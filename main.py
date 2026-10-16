import argparse
import json
import os
import sys
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
from core.matcher import CommandMatcher
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
    def __init__(self, listener: VoiceListener, matcher: CommandMatcher, executor: ActionExecutor, signals: IslandSignals):
        super().__init__()
        self.listener = listener
        self.matcher = matcher
        self.executor = executor
        self.signals = signals
        self.running = True

    def run(self):
        while self.running:
            try:
                raw_text = self.listener.listen_once()
            except RuntimeError:
                time.sleep(1.0)
                continue

            if not self.running:
                break

            if raw_text is None or not raw_text.strip():
                continue

            match_result = self.matcher.find_match(raw_text)
            if match_result.matched and match_result.command:
                # Wake word matched! Show transcribed text and execute
                self.signals.sig_transcribed.emit(raw_text)
                cmd = match_result.command

                # Check if voice command is to exit
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
            elif not self.matcher.wake_word_enabled:
                # Only show unmatched popup if wake word is disabled (continuous mode)
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
                executor.execute(result.command)
                ui.log_success(
                    cmd_id=result.command.get("id", ""),
                    desc=result.command.get("description", ""),
                    trigger=result.matched_trigger,
                    score=result.score,
                    keys=result.command.get("keys", []),
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
    parser.add_argument("--no-gui", action="store_true", help="Dinamik Ada arayüzü olmadan sadece konsolda çalıştırın")
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

    sound = SoundFeedback(enabled=False)  # Completely silent per user request
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
    island_signals.sig_transcribed.connect(island.show_transcribing)
    island_signals.sig_executed.connect(island.show_executed)
    island_signals.sig_unmatched.connect(island.show_unmatched)
    island_signals.sig_exit.connect(island.show_exit)

    # Initialize microphone listener
    try:
        wake_enabled = settings.get("wake_word_enabled", True)
        listener = VoiceListener(
            language=settings.get("language", "tr-TR"),
            energy_threshold_adjustment=settings.get("energy_threshold_adjustment", True),
            on_speech_start=lambda: island_signals.sig_speech_start.emit() if not wake_enabled else None,
        )

        if settings.get("energy_threshold_adjustment", True):
            listener.calibrate(duration=0.8)

    except Exception as e:
        console.print(f"[bold red]Mikrofon başlatılamadı:[/] {e}")
        sys.exit(1)

    # Start background voice thread
    voice_thread = VoiceWorkerThread(listener, matcher, executor, island_signals)
    voice_thread.start()

    # Handle clean exit
    def cleanup():
        voice_thread.stop()
        voice_thread.wait(1000)

    app.aboutToQuit.connect(cleanup)

    # Run PyQt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
