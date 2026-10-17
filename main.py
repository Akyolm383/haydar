import argparse
import json
import os
import sys
import threading
import time

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QApplication

from core.executor import ActionExecutor
from core.listener import VoiceListener
from core.matcher import (
    CommandMatcher,
    extract_browser_click_target,
    extract_window_number,
    normalize_turkish,
)
from core.web_bridge import web_bridge
from ui.island import DynamicIsland, IslandSignals
from utils.sound import SoundFeedback
from utils.ui import HaydarUI, console


def load_config(config_path: str = "config/commands.json") -> dict:
    if not os.path.isabs(config_path):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, config_path)

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class VoiceWorkerThread(QThread):
    def __init__(
        self,
        listener: VoiceListener,
        matcher: CommandMatcher,
        executor: ActionExecutor,
        signals: IslandSignals,
    ):
        super().__init__()
        self.listener = listener
        self.matcher = matcher
        self.executor = executor
        self.signals = signals
        self.running = True

        # Continuous active listening toggle state
        self.default_wake_word_enabled = matcher.wake_word_enabled
        self.continuous_listening = False

        # Two-stage wake state for Haydar ("Haydar" -> "Efendim? Dinliyorum...")
        self.is_haydar_awake = False
        self.haydar_awake_timestamp = 0.0
        self.wake_window_seconds = 7.0

        # Window switcher state ("Haydar pencere değiştir" -> Alt+Tab açıldı -> "5. pencere")
        self.is_window_switch_active = False
        self.window_switch_timestamp = 0.0
        self.window_switch_timeout = 8.0

    def run(self):
        while self.running:
            now = time.time()
            if self.is_haydar_awake and (now - self.haydar_awake_timestamp) > self.wake_window_seconds:
                self.is_haydar_awake = False

            if self.is_window_switch_active and (now - self.window_switch_timestamp) > self.window_switch_timeout:
                self.is_window_switch_active = False
                self.executor.close_window_switcher()

            try:
                raw_text = self.listener.listen_once()
            except RuntimeError:
                time.sleep(0.5)
                continue

            if not self.running:
                break

            if raw_text is None or not raw_text.strip():
                continue

            now = time.time()

            # --- CASE 0: Assistant is waiting for window selection following "Pencere değiştir" ---
            if self.is_window_switch_active and (now - self.window_switch_timestamp) <= self.window_switch_timeout:
                self.is_window_switch_active = False
                self.signals.sig_transcribed.emit(raw_text)

                norm_text = normalize_turkish(raw_text)
                if any(w in norm_text for w in ["iptal", "vazgec", "vazgeç", "kapat", "cik", "çık"]):
                    self.executor.close_window_switcher()
                    self.signals.sig_unmatched.emit("İptal edildi", 100.0)
                    continue

                target_num = extract_window_number(raw_text)
                if target_num is not None and 1 <= target_num <= 30:
                    success = self.executor.switch_to_nth_window(target_num)
                    if success:
                        self.signals.sig_executed.emit(
                            f"{target_num}. pencere açıldı",
                            ["alt", f"tab x{target_num}"],
                            100.0,
                        )
                else:
                    self.executor.close_window_switcher()
                    self.signals.sig_unmatched.emit(raw_text, 0.0)
                continue

            # --- CASE 1: Assistant is waiting for command following "Haydar" ---
            if self.is_haydar_awake and (now - self.haydar_awake_timestamp) <= self.wake_window_seconds:
                self.is_haydar_awake = False
                self.signals.sig_transcribed.emit(raw_text)

                # Check dynamic click command first: e.g. "tıkla abone ol", "abone ol butonuna bas"
                click_target = extract_browser_click_target(raw_text)
                if click_target:
                    resp = self.executor.browser_click_custom(click_target)
                    status = resp.get("status")
                    if status in ("success", "timeout"):
                        elem_text = resp.get("element", click_target)
                        self.signals.sig_executed.emit(
                            f"'{elem_text}' tıklandı",
                            ["Web Extension"],
                            100.0,
                        )
                    elif status == "no_extension":
                        self.signals.sig_unmatched.emit("Tarayıcı eklentisi bağlı değil", 0.0)
                    else:
                        self.signals.sig_unmatched.emit(f"'{click_target}' bulunamadı", 0.0)
                    continue

                orig_wake_setting = self.matcher.wake_word_enabled
                self.matcher.wake_word_enabled = False
                match_res = self.matcher.find_match(raw_text)
                self.matcher.wake_word_enabled = orig_wake_setting

                if match_res.matched and match_res.command:
                    cmd = match_res.command

                    if cmd.get("action_type") == "toggle_listen_on":
                        self.continuous_listening = True
                        self.matcher.wake_word_enabled = False
                        self.signals.sig_continuous_toggled.emit(True)
                        continue

                    if cmd.get("action_type") == "toggle_listen_off":
                        self.continuous_listening = False
                        self.matcher.wake_word_enabled = self.default_wake_word_enabled
                        self.signals.sig_continuous_toggled.emit(False)
                        continue

                    if cmd.get("id") == "switch_window_mode":
                        self.is_window_switch_active = True
                        self.window_switch_timestamp = time.time()
                        self.executor.open_window_switcher()
                        self.signals.sig_window_switch_mode.emit()
                        continue

                    if cmd.get("action_type") == "exit":
                        self.signals.sig_exit.emit()
                        self.running = False
                        break

                    if cmd.get("action_type") == "browser":
                        browser_res = self.executor.execute_browser_action(cmd)
                        status = browser_res.get("status")
                        if status in ("success", "timeout"):
                            elem_text = browser_res.get("element") or cmd.get("description", "")
                            if cmd.get("browser_action") == "play_video":
                                disp_msg = f"{elem_text} başlatıldı"
                            elif cmd.get("browser_action") == "click_button":
                                disp_msg = f"'{elem_text}' tıklandı"
                            else:
                                disp_msg = elem_text
                            self.signals.sig_executed.emit(
                                disp_msg,
                                ["Web Extension"],
                                match_res.score or 100.0,
                            )
                        elif status == "no_extension":
                            self.signals.sig_unmatched.emit("Tarayıcı eklentisi bağlı değil", 0.0)
                        else:
                            fallback_name = "Video Oynatıcı" if cmd.get("browser_action") == "play_video" else "Buton"
                            target_name = cmd.get("target") or fallback_name
                            self.signals.sig_unmatched.emit(f"'{target_name}' bulunamadı", 0.0)
                        continue

                    executed = self.executor.execute(cmd)
                    if executed:
                        self.signals.sig_executed.emit(
                            cmd.get("description", ""),
                            cmd.get("keys", []),
                            match_res.score,
                        )
                else:
                    self.signals.sig_unmatched.emit(raw_text, match_res.score)
                continue

            # --- CASE 2: Standby mode ("Haydar ..." or "Haydar") ---
            match_result = self.matcher.find_match(raw_text)
            processed_text, wake_detected = self.matcher.extract_command_text(raw_text)

            # Direct video browser commands (works with 'Haydar ...' or simply without 'Haydar'):
            norm_raw = normalize_turkish(raw_text)
            direct_video_prefixes = (
                "sonraki bölüm", "sonraki bolum", "önceki bölüm", "onceki bolum",
                "tıkla sonraki bölüm", "tıkla sonraki bolum", "tıkla sıradaki bölüm", "tıkla sonraki",
                "tıkla önceki bölüm", "tıkla onceki bolum", "tıkla önceki",
                "introyu atla", "reklamı geç", "reklamı atla",
                "videoyu aç", "videoyu ac", "video aç", "video ac",
                "videoyu başlat", "videoyu baslat", "video başlat", "video baslat",
                "videoyu oynat", "video oynat",
                "filmi başlat", "filmi baslat", "film başlat", "film baslat",
                "filmi aç", "filmi ac", "film aç", "film ac",
                "filmi oynat", "film oynat",
                "diziyi başlat", "diziyi baslat", "dizi başlat", "dizi baslat",
                "diziyi aç", "diziyi ac", "dizi aç", "dizi ac",
                "diziyi oynat", "dizi oynat",
                "videoyu bul", "video bul",
                "playerı aç", "playeri ac", "player aç", "player ac",
                "oynatıcıyı aç", "oynatıcı aç", "oynatici ac"
            )
            if any(norm_raw.startswith(k) for k in direct_video_prefixes):
                orig_wake_setting = self.matcher.wake_word_enabled
                self.matcher.wake_word_enabled = False
                direct_match = self.matcher.find_match(raw_text)
                self.matcher.wake_word_enabled = orig_wake_setting
                if direct_match.matched and direct_match.command and direct_match.command.get("action_type") == "browser":
                    self.signals.sig_transcribed.emit(raw_text)
                    b_res = self.executor.execute_browser_action(direct_match.command)
                    status = b_res.get("status")
                    if status in ("success", "timeout"):
                        elem = b_res.get("element") or direct_match.command.get("description", "")
                        if direct_match.command.get("browser_action") == "play_video":
                            disp = f"{elem} başlatıldı"
                        elif direct_match.command.get("browser_action") == "click_button":
                            disp = f"'{elem}' tıklandı"
                        else:
                            disp = elem
                        self.signals.sig_executed.emit(
                            disp,
                            ["Web Extension"],
                            100.0,
                        )
                    elif status == "no_extension":
                        self.signals.sig_unmatched.emit("Tarayıcı eklentisi bağlı değil", 0.0)
                    else:
                        target_name = direct_match.command.get("target") or "Video Oynatıcı"
                        self.signals.sig_unmatched.emit(f"'{target_name}' bulunamadı", 0.0)
                    continue

            # Direct single-shot window command: e.g. "haydar 5. pencere", "haydar 3. pencereye geç"
            if (wake_detected or not self.matcher.wake_word_enabled) and "pencere" in processed_text:
                direct_num = extract_window_number(processed_text)
                if direct_num is not None and 1 <= direct_num <= 30:
                    self.signals.sig_transcribed.emit(raw_text)
                    success = self.executor.switch_to_nth_window(direct_num)
                    if success:
                        self.signals.sig_executed.emit(
                            f"{direct_num}. pencere açıldı",
                            ["alt", f"tab x{direct_num}"],
                            100.0,
                        )
                    continue

            # Direct single-shot browser click: e.g. "haydar tıkla abone ol", "haydar sepete ekle butonuna bas", "tıkla abone ol"
            if wake_detected or not self.matcher.wake_word_enabled:
                click_target = extract_browser_click_target(processed_text) or extract_browser_click_target(raw_text)
                if click_target:
                    self.signals.sig_transcribed.emit(raw_text)
                    resp = self.executor.browser_click_custom(click_target)
                    status = resp.get("status")
                    if status in ("success", "timeout"):
                        elem_text = resp.get("element", click_target)
                        self.signals.sig_executed.emit(
                            f"'{elem_text}' tıklandı",
                            ["Web Extension"],
                            100.0,
                        )
                    elif status == "no_extension":
                        self.signals.sig_unmatched.emit("Tarayıcı eklentisi bağlı değil", 0.0)
                    else:
                        self.signals.sig_unmatched.emit(f"'{click_target}' bulunamadı", 0.0)
                    continue

            if match_result.matched and match_result.command:
                cmd = match_result.command

                if cmd.get("action_type") == "toggle_listen_on":
                    self.continuous_listening = True
                    self.matcher.wake_word_enabled = False
                    self.signals.sig_continuous_toggled.emit(True)
                    continue

                if cmd.get("action_type") == "toggle_listen_off":
                    self.continuous_listening = False
                    self.matcher.wake_word_enabled = self.default_wake_word_enabled
                    self.signals.sig_continuous_toggled.emit(False)
                    continue

                # User said just "Haydar" -> Enter command listening mode
                if cmd.get("id") == "wake_greeting":
                    self.is_haydar_awake = True
                    self.haydar_awake_timestamp = time.time()
                    self.signals.sig_waiting_command.emit()
                    continue

                # User said "Haydar pencere değiştir"
                if cmd.get("id") == "switch_window_mode":
                    self.is_window_switch_active = True
                    self.window_switch_timestamp = time.time()
                    self.signals.sig_transcribed.emit(raw_text)
                    self.executor.open_window_switcher()
                    self.signals.sig_window_switch_mode.emit()
                    continue

                # Browser extension command
                if cmd.get("action_type") == "browser":
                    self.signals.sig_transcribed.emit(raw_text)
                    browser_res = self.executor.execute_browser_action(cmd)
                    status = browser_res.get("status")
                    if status in ("success", "timeout"):
                        elem_text = browser_res.get("element") or cmd.get("description", "")
                        if cmd.get("browser_action") == "play_video":
                            disp_msg = f"{elem_text} başlatıldı"
                        elif cmd.get("browser_action") == "click_button":
                            disp_msg = f"'{elem_text}' tıklandı"
                        else:
                            disp_msg = elem_text
                        self.signals.sig_executed.emit(
                            disp_msg,
                            ["Web Extension"],
                            match_result.score or 100.0,
                        )
                    elif status == "no_extension":
                        self.signals.sig_unmatched.emit("Tarayıcı eklentisi bağlı değil", 0.0)
                    else:
                        target_name = cmd.get("target") or "Video Oynatıcı"
                        self.signals.sig_unmatched.emit(f"'{target_name}' bulunamadı", 0.0)
                    continue

                # User said standard command in one breath
                self.signals.sig_transcribed.emit(raw_text)
                if cmd.get("action_type") == "exit":
                    self.signals.sig_exit.emit()
                    self.running = False
                    break

                executed = self.executor.execute(cmd)
                if executed:
                    self.signals.sig_executed.emit(
                        cmd.get("description", ""),
                        cmd.get("keys", []),
                        match_result.score,
                    )
            elif wake_detected and processed_text:
                self.signals.sig_transcribed.emit(raw_text)
                self.signals.sig_unmatched.emit(processed_text, match_result.score)
            elif not self.matcher.wake_word_enabled:
                self.signals.sig_transcribed.emit(raw_text)
                self.signals.sig_unmatched.emit(raw_text, match_result.score)

    def stop(self):
        self.running = False


def run_interactive_simulation(matcher: CommandMatcher, executor: ActionExecutor, ui: HaydarUI, sound: SoundFeedback):
    """Allows testing commands via terminal text input without using a microphone."""
    console.print("\n[bold yellow]⌨️ Simülasyon Modu Aktif![/] İstediğiniz komut metnini yazıp Enter'a basın (Çıkmak için 'q'):\n")
    while True:
        try:
            text = input("Haydar > ").strip()
            if not text:
                continue
            if text.lower() in ["q", "exit", "quit", "çıkış"]:
                console.print("[cyan]Simülasyon modundan çıkıldı.[/cyan]")
                break

            ui.log_processing(text)
            result = matcher.find_match(text)
            if result.matched and result.command:
                cmd = result.command
                if cmd.get("action_type") == "toggle_listen_on":
                    matcher.wake_word_enabled = False
                    console.print("[bold magenta]⚡ Sürekli dinleme modu açıldı (Wake word devre dışı)![/]")
                elif cmd.get("action_type") == "toggle_listen_off":
                    matcher.wake_word_enabled = True
                    console.print("[bold yellow]🔒 Sürekli dinleme modu kapatıldı (Wake word: Haydar)![/]")

                executor.execute(cmd)
                ui.log_success(
                    cmd_id=cmd.get("id", ""),
                    desc=cmd.get("description", ""),
                    trigger=result.matched_trigger,
                    score=result.score,
                    keys=cmd.get("keys", []),
                )
            else:
                ui.log_unmatched(
                    raw_text=text,
                    score=result.score,
                    threshold=result.command.get("threshold", matcher.default_threshold) if result.command else matcher.default_threshold,
                    reason=result.reason,
                )
        except (KeyboardInterrupt, EOFError):
            break


def main():
    parser = argparse.ArgumentParser(description="Haydar - Sesli Komut ve Dinamik Ada Asistanı")
    parser.add_argument("--cli", action="store_true", help="Mikrofon yerine terminalden metin girerek test edin")
    parser.add_argument("--simulate", type=str, help="Tek bir komut metnini doğrudan çalıştırıp test edin")
    parser.add_argument("--config", type=str, default="config/commands.json", help="Özel komut dosyası yolu")
    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        console.print(f"[bold red]Konfigürasyon yükleme hatası:[/] {e}")
        sys.exit(1)

    settings = config.get("settings", {})
    commands = config.get("commands", [])

    sound = SoundFeedback(enabled=False)
    matcher = CommandMatcher(config)
    executor = ActionExecutor(cooldown_seconds=float(settings.get("cooldown_seconds", 0.8)))
    ui = HaydarUI(settings=settings, commands=commands)

    # CLI simulation mode
    if args.cli:
        ui.print_banner()
        ui.print_status()
        ui.print_commands_summary()
        run_interactive_simulation(matcher, executor, ui, sound)
        sys.exit(0)

    # Single simulation command
    if args.simulate:
        result = matcher.find_match(args.simulate)
        if result.matched and result.command:
            executor.execute(result.command)
            ui.log_success(
                cmd_id=result.command.get("id", ""),
                desc=result.command.get("description", ""),
                trigger=result.matched_trigger,
                score=result.score,
                keys=result.command.get("keys", []),
            )
            sys.exit(0)
        else:
            ui.log_unmatched(
                raw_text=args.simulate,
                score=result.score,
                threshold=result.command.get("threshold", matcher.default_threshold) if result.command else matcher.default_threshold,
                reason=result.reason,
            )
            sys.exit(1)

    # Launch PyQt Application with Auto-Hiding Dynamic Island
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    island_signals = IslandSignals()
    island = DynamicIsland()

    # Connect signals to Dynamic Island methods
    island_signals.sig_speech_start.connect(island.show_listening)
    island_signals.sig_audio_level.connect(island.handle_audio_level)
    island_signals.sig_transcribed.connect(island.show_transcribing)
    island_signals.sig_waiting_command.connect(island.show_waiting_for_command)
    island_signals.sig_window_switch_mode.connect(island.show_window_switch_mode)
    island_signals.sig_executed.connect(island.show_executed)
    island_signals.sig_unmatched.connect(island.show_unmatched)
    island_signals.sig_exit.connect(island.show_exit)
    island_signals.sig_continuous_toggled.connect(island.show_continuous_mode)

    # Initialize microphone listener with amplitude monitoring
    try:
        listener = VoiceListener(
            language=settings.get("language", "tr-TR"),
            energy_threshold_adjustment=settings.get("energy_threshold_adjustment", True),
            on_speech_start=lambda: island_signals.sig_speech_start.emit() if not matcher.wake_word_enabled else None,
            on_audio_level=lambda lvl: island_signals.sig_audio_level.emit(lvl),
        )

        if settings.get("energy_threshold_adjustment", True):
            listener.calibrate(duration=0.8)

    except Exception as e:
        console.print(f"[bold red]Mikrofon başlatılamadı:[/] {e}")
        sys.exit(1)

    # Start local Web Bridge for browser extension
    web_bridge.start()

    # Start background voice thread
    voice_thread = VoiceWorkerThread(listener, matcher, executor, island_signals)
    voice_thread.start()

    # Handle clean exit
    def cleanup():
        web_bridge.stop()
        voice_thread.stop()
        voice_thread.wait(1000)

    app.aboutToQuit.connect(cleanup)

    # Run PyQt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
