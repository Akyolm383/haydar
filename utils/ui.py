import sys
from typing import Any, Dict, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(legacy_windows=False)


class HaydarUI:
    def __init__(self, settings: Dict[str, Any], commands: List[Dict[str, Any]]):
        self.settings = settings
        self.commands = commands

    def print_banner(self):
        banner_text = Text()
        banner_text.append("🎙️  H A Y D A R  🎙️\n", style="bold cyan")
        banner_text.append("Akıllı Türkçe Sesli Komut ve Masaüstü Otomasyon Asistanı\n", style="italic white")
        banner_text.append("Google Speech API + RapidFuzz (Bulanık Arama) + Windows Otomasyonu", style="dim green")
        console.print(Panel(banner_text, border_style="cyan", expand=False))

    def print_status(self):
        table = Table(title="Sistem Ayarları", border_style="blue", show_header=True)
        table.add_column("Ayar", style="bold white")
        table.add_column("Değer", style="yellow")
        table.add_column("Açıklama", style="dim")

        wake_word_status = (
            f"[green]Aktif[/green] ('{self.settings.get('wake_word', 'haydar')}')"
            if self.settings.get("wake_word_enabled", False)
            else "[yellow]Devre Dışı[/yellow] (Sürekli Dinleme)"
        )

        table.add_row("Eşik Skoru (Fuzzy)", f"%{self.settings.get('default_threshold', 70)}", "En az benzerlik oranı")
        table.add_row("Çalışma Modu", wake_word_status, "Komut tetikleme yöntemi")
        table.add_row("Dil", str(self.settings.get("language", "tr-TR")), "Ses tanıma dili")
        table.add_row("Toplam Komut", str(len(self.commands)), "Yüklü komut sayısı")

        console.print(table)

    def print_commands_summary(self):
        table = Table(title="Kayıtlı Komutlar ve Tetikleyiciler", border_style="magenta", show_header=True)
        table.add_column("Komut ID", style="cyan")
        table.add_column("Açıklama", style="white")
        table.add_column("Örnek Tetikleyiciler", style="green")
        table.add_column("Tuşlar", style="yellow")

        for cmd in self.commands:
            triggers_str = ", ".join(f"'{t}'" for t in cmd.get("triggers", [])[:3])
            if len(cmd.get("triggers", [])) > 3:
                triggers_str += "..."
            keys_str = " + ".join(cmd.get("keys", []))
            table.add_row(cmd.get("id", ""), cmd.get("description", ""), triggers_str, keys_str)

        console.print(table)

    def log_listening(self):
        console.print("[dim cyan]● Dinleniyor... Konuşun (Çıkmak için Ctrl+C)[/dim cyan]", end="\r")

    def log_processing(self, raw_text: str):
        console.print(f"\n[bold magenta]► Algılanan Ses:[/] \"[white]{raw_text}[/]\"")

    def log_success(self, cmd_id: str, desc: str, trigger: str, score: float, keys: List[str]):
        keys_display = " + ".join(keys)
        panel_content = (
            f"[bold green]✔ Eşleşme Başarılı![/] [yellow](Skor: %{score:.1f})[/yellow]\n"
            f"[bold white]Komut:[/] {desc} ([cyan]{cmd_id}[/cyan])\n"
            f"[bold white]Eşleşen Kalıp:[/] \"{trigger}\"\n"
            f"[bold white]Tetiklenen Eylem:[/] [bold yellow][ {keys_display} ][/bold yellow]"
        )
        console.print(Panel(panel_content, border_style="green", expand=False))

    def log_unmatched(self, raw_text: str, score: float, threshold: float, reason: str):
        panel_content = (
            f"[bold red]✖ Komut Yürütülmedi[/bold red]\n"
            f"[bold white]Metin:[/] \"{raw_text}\"\n"
            f"[bold white]En Yüksek Skor:[/] [yellow]%{score:.1f}[/yellow] (Gerekli: %{threshold})\n"
            f"[bold white]Neden:[/] [dim]{reason}[/dim]"
        )
        console.print(Panel(panel_content, border_style="red", expand=False))

    def log_warning(self, message: str):
        console.print(f"[bold yellow]⚠ {message}[/bold yellow]")

    def log_error(self, message: str):
        console.print(f"[bold red]❌ {message}[/bold red]")
