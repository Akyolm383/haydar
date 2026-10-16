import math
import os
import random
import sys
from typing import List, Optional

from PyQt6.QtCore import (
    QEasingCurve,
    QObject,
    QPoint,
    QPropertyAnimation,
    QRect,
    QRectF,
    QSize,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QAction,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMenu,
    QSystemTrayIcon,
    QWidget,
)


class IslandSignals(QObject):
    sig_speech_start = pyqtSignal()
    sig_audio_level = pyqtSignal(float)
    sig_transcribed = pyqtSignal(str)
    sig_waiting_command = pyqtSignal()
    sig_executed = pyqtSignal(str, list, float)  # desc, keys, score
    sig_ai_answer = pyqtSignal(str, str)         # prompt, answer
    sig_unmatched = pyqtSignal(str, float)       # text, score
    sig_exit = pyqtSignal()


class AudioWaveVisualizer(QWidget):
    """
    Real-time 4-bar animated audio visualizer widget for Dynamic Island.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 22)
        self.num_bars = 4
        self.current_heights = [4.0, 4.0, 4.0, 4.0]
        self.target_heights = [4.0, 4.0, 4.0, 4.0]
        self.active_color = QColor(16, 185, 129)  # Emerald green

        # 30 FPS smooth physics decay timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_physics)
        self.timer.start(33)

    def set_level(self, level: float):
        """Called when new audio amplitude arrives (0.0 to 1.0)."""
        max_h = 20.0
        min_h = 4.0
        # Multipliers for natural wave variation across the 4 bars
        multipliers = [0.8, 1.2, 1.0, 0.7]
        for i in range(self.num_bars):
            val = min_h + (max_h - min_h) * min(1.0, level * multipliers[i])
            self.target_heights[i] = val

    def set_color(self, color: QColor):
        self.active_color = color
        self.update()

    def _update_physics(self):
        changed = False
        for i in range(self.num_bars):
            # Smooth approach to target height
            diff = self.target_heights[i] - self.current_heights[i]
            if abs(diff) > 0.3:
                self.current_heights[i] += diff * 0.4
                changed = True
            # Decay target height towards minimum
            self.target_heights[i] = max(4.0, self.target_heights[i] * 0.88)

        if changed or any(h > 4.5 for h in self.current_heights):
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bar_width = 3.5
        spacing = 3.5
        start_x = 2.0
        mid_y = self.height() / 2.0

        painter.setBrush(self.active_color)
        painter.setPen(Qt.PenStyle.NoPen)

        for i in range(self.num_bars):
            h = self.current_heights[i]
            x = start_x + i * (bar_width + spacing)
            y = mid_y - (h / 2.0)
            painter.drawRoundedRect(QRectF(x, y, bar_width, h), 1.75, 1.75)


class DynamicIsland(QWidget):
    def __init__(self):
        super().__init__()

        # Frameless, Always on Top, Tool window (no taskbar item), Does Not Steal Focus
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # Island dimensions
        self.island_height = 42
        self.current_width = 240
        self.target_y = 12
        self.hidden_y = -75

        # Visual styling
        self.bg_color = QColor(15, 17, 23, 245)
        self.border_color = QColor(255, 255, 255, 35)
        self.border_width = 1.0

        # Screen geometry
        self.screen_geo = QApplication.primaryScreen().geometry()
        init_x = (self.screen_geo.width() - self.current_width) // 2

        # Start hidden above top bezel
        self.setGeometry(init_x, self.hidden_y, self.current_width, self.island_height)

        # UI elements layout
        self._init_layout()

        # Animations
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(260)

        # Auto-hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.slide_up)

        # Tray icon
        self._init_tray_icon()

        self.is_visible_on_screen = False

    def _init_layout(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        # Live audio visualizer
        self.visualizer = AudioWaveVisualizer(self)
        layout.addWidget(self.visualizer)

        # Status icon / dot
        self.icon_label = QLabel("🎙️")
        self.icon_label.setFont(QFont("Segoe UI Emoji", 11))
        self.icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.icon_label)

        # Main text
        self.text_label = QLabel("Dinleniyor...")
        self.text_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.text_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        layout.addWidget(self.text_label, stretch=1)

        # Shortcut badge (e.g. [ Win + D ])
        self.badge_label = QLabel("")
        self.badge_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.badge_label.setStyleSheet(
            "background: rgba(255, 255, 255, 0.12); color: #10B981; border-radius: 6px; padding: 3px 8px;"
        )
        self.badge_label.hide()
        layout.addWidget(self.badge_label)

    def _init_tray_icon(self):
        self.tray = QSystemTrayIcon(self)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(16, 185, 129))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()

        self.tray.setIcon(QIcon(pixmap))
        self.tray.setToolTip("Haydar - Sesli Asistan")

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a1d26;
                color: #FFFFFF;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                padding: 6px;
                font-family: 'Segoe UI';
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #2b3040;
            }
        """)

        title_action = QAction("🎙️ Haydar Aktif (Dinliyor)", self)
        title_action.setEnabled(False)
        menu.addAction(title_action)
        menu.addSeparator()

        edit_action = QAction("⚙️ Komutları Düzenle (commands.json)", self)
        edit_action.triggered.connect(self._open_commands_json)
        menu.addAction(edit_action)

        exit_action = QAction("❌ Haydar'dan Çıkış", self)
        exit_action.triggered.connect(self.close_and_exit)
        menu.addAction(exit_action)

        self.tray.setContextMenu(menu)
        self.tray.show()

    def _open_commands_json(self):
        config_path = os.path.abspath("config/commands.json")
        try:
            os.startfile(config_path)
        except Exception:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        rect = self.rect().adjusted(1, 1, -1, -1)
        radius = rect.height() / 2.0
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)

        # Fill background
        painter.fillPath(path, self.bg_color)

        # Draw border
        pen = QPen(self.border_color, self.border_width)
        painter.setPen(pen)
        painter.drawPath(path)

    def _update_geometry(self, width: int):
        self.current_width = width
        cx = (self.screen_geo.width() - width) // 2
        cy = self.y()
        self.setGeometry(cx, cy, width, self.island_height)

    def slide_down(self):
        """Slides the island down from top bezel into view."""
        self.hide_timer.stop()
        cx = (self.screen_geo.width() - self.current_width) // 2

        self.pos_anim.stop()
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(QPoint(cx, self.target_y))
        self.show()
        self.pos_anim.start()
        self.is_visible_on_screen = True

    def slide_up(self):
        """Slides the island back up into the bezel and hides."""
        self.hide_timer.stop()
        cx = (self.screen_geo.width() - self.current_width) // 2

        self.pos_anim.stop()
        self.pos_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(QPoint(cx, self.hidden_y))
        self.pos_anim.start()
        self.is_visible_on_screen = False

    def handle_audio_level(self, level: float):
        """Updates the live audio waveform."""
        if self.is_visible_on_screen:
            self.visualizer.set_level(level)

    # ---------------- State handlers ----------------

    def show_listening(self):
        """Triggered when speech starts or waiting for speech."""
        self.bg_color = QColor(15, 17, 23, 245)
        self.border_color = QColor(56, 189, 248, 140)  # Light cyan accent
        self.border_width = 1.5
        self.visualizer.set_color(QColor(56, 189, 248))

        self.icon_label.setText("🎙️")
        self.text_label.setText("Dinleniyor...")
        self.badge_label.hide()

        self._update_geometry(260)
        self.slide_down()
        self.update()

    def show_waiting_for_command(self):
        """Triggered when user says just 'Haydar' and system is waiting for follow-up command."""
        self.bg_color = QColor(15, 23, 42, 250)
        self.border_color = QColor(56, 189, 248, 200)  # Cyan glow
        self.border_width = 1.8
        self.visualizer.set_color(QColor(56, 189, 248))

        self.icon_label.setText("👋")
        self.text_label.setText("Efendim? Dinliyorum...")
        self.badge_label.hide()

        self._update_geometry(280)
        if not self.is_visible_on_screen:
            self.slide_down()
        self.update()

        # Generous 6-second window to wait for the command before auto-retracting
        self.hide_timer.start(6000)

    def show_transcribing(self, raw_text: str):
        """Triggered when Google Speech returns recognized text."""
        self.bg_color = QColor(15, 17, 23, 245)
        self.border_color = QColor(168, 85, 247, 140)  # Purple accent
        self.border_width = 1.5
        self.visualizer.set_color(QColor(168, 85, 247))

        self.icon_label.setText("💬")
        display_text = f'"{raw_text}"'
        self.text_label.setText(display_text)
        self.badge_label.hide()

        needed_width = max(280, min(540, len(display_text) * 11 + 100))
        self._update_geometry(needed_width)
        if not self.is_visible_on_screen:
            self.slide_down()
        self.update()

    def show_executed(self, desc: str, keys: List[str], score: float):
        """Triggered when command matched and executed."""
        self.bg_color = QColor(10, 26, 20, 250)
        self.border_color = QColor(16, 185, 129, 220)  # Green glow
        self.border_width = 2.0
        self.visualizer.set_color(QColor(16, 185, 129))

        self.icon_label.setText("✔")
        self.text_label.setText(desc)

        if keys:
            keys_text = " + ".join(keys)
            self.badge_label.setText(f"[ {keys_text} ]")
            self.badge_label.setStyleSheet(
                "background: rgba(16, 185, 129, 0.2); color: #34D399; font-weight: bold; border-radius: 6px; padding: 3px 8px;"
            )
            self.badge_label.show()
            needed_width = max(380, min(580, len(desc) * 9 + len(keys_text) * 12 + 120))
        else:
            self.badge_label.hide()
            needed_width = max(320, min(500, len(desc) * 10 + 100))

        self._update_geometry(needed_width)
        if not self.is_visible_on_screen:
            self.slide_down()
        self.update()

        # Disappear after 1.8 seconds of glory
        self.hide_timer.start(1800)

    def show_ai_answer(self, prompt: str, answer: str):
        """Triggered when Gemini AI provides an answer."""
        self.bg_color = QColor(24, 18, 43, 252)
        self.border_color = QColor(168, 85, 247, 240)  # Purple/Cyan AI glow
        self.border_width = 2.0
        self.visualizer.set_color(QColor(168, 85, 247))

        self.icon_label.setText("🤖")
        self.text_label.setText(answer)
        self.badge_label.setText("Gemini AI")
        self.badge_label.setStyleSheet(
            "background: rgba(168, 85, 247, 0.25); color: #C084FC; font-weight: bold; border-radius: 6px; padding: 3px 8px;"
        )
        self.badge_label.show()

        needed_width = max(380, min(620, len(answer) * 8 + 140))
        self._update_geometry(needed_width)
        if not self.is_visible_on_screen:
            self.slide_down()
        self.update()

        # Generous 5-second timer so user can read the response comfortably
        self.hide_timer.start(5000)

    def show_unmatched(self, raw_text: str, score: float):
        """Triggered when speech was heard but below threshold."""
        self.bg_color = QColor(25, 18, 18, 245)
        self.border_color = QColor(239, 68, 68, 120)  # Red accent
        self.border_width = 1.5
        self.visualizer.set_color(QColor(239, 68, 68))

        self.icon_label.setText("✖")
        self.text_label.setText(f'"{raw_text}" (Anlaşılamadı)')
        self.badge_label.hide()

        self._update_geometry(340)
        if not self.is_visible_on_screen:
            self.slide_down()
        self.update()

        # Disappear after 1.5 seconds
        self.hide_timer.start(1500)

    def show_exit(self):
        """Show goodbye and quit."""
        self.bg_color = QColor(15, 17, 23, 250)
        self.border_color = QColor(245, 158, 11, 200)
        self.visualizer.set_color(QColor(245, 158, 11))
        self.icon_label.setText("👋")
        self.text_label.setText("Görüşmek üzere...")
        self.badge_label.hide()
        self._update_geometry(260)
        self.slide_down()
        self.update()
        QTimer.singleShot(900, self.close_and_exit)

    def close_and_exit(self):
        self.tray.hide()
        QApplication.quit()
