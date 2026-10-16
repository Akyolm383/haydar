import os
import sys
from typing import List, Optional

from PyQt6.QtCore import (
    QEasingCurve,
    QObject,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
    QTimer,
    pyqtSignal,
    pyqtProperty,
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
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMenu,
    QSystemTrayIcon,
    QWidget,
)


class IslandSignals(QObject):
    sig_speech_start = pyqtSignal()
    sig_transcribed = pyqtSignal(str)
    sig_executed = pyqtSignal(str, list, float)  # desc, keys, score
    sig_unmatched = pyqtSignal(str, float)       # text, score
    sig_exit = pyqtSignal()


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
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        # Status icon / dot
        self.icon_label = QLabel("🎙️")
        self.icon_label.setFont(QFont("Segoe UI Emoji", 12))
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
        # Create a simple clean icon for tray
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

    # ---------------- State handlers ----------------

    def show_listening(self):
        """Triggered immediately when user starts speaking."""
        self.bg_color = QColor(15, 17, 23, 245)
        self.border_color = QColor(56, 189, 248, 120)  # Light cyan accent
        self.border_width = 1.5

        self.icon_label.setText("🎙️")
        self.text_label.setText("Dinleniyor...")
        self.badge_label.hide()

        self._update_geometry(240)
        self.slide_down()
        self.update()

    def show_transcribing(self, raw_text: str):
        """Triggered when Google Speech returns recognized text."""
        self.bg_color = QColor(15, 17, 23, 245)
        self.border_color = QColor(168, 85, 247, 120)  # Purple accent
        self.border_width = 1.5

        self.icon_label.setText("💬")
        display_text = f'"{raw_text}"'
        self.text_label.setText(display_text)
        self.badge_label.hide()

        # Dynamic width based on text length
        needed_width = max(280, min(520, len(display_text) * 11 + 90))
        self._update_geometry(needed_width)
        if not self.is_visible_on_screen:
            self.slide_down()
        self.update()

    def show_executed(self, desc: str, keys: List[str], score: float):
        """Triggered when command matched and executed."""
        self.bg_color = QColor(10, 26, 20, 250)
        self.border_color = QColor(16, 185, 129, 220)  # Green glow
        self.border_width = 2.0

        self.icon_label.setText("✔")
        self.text_label.setText(desc)

        keys_text = " + ".join(keys)
        self.badge_label.setText(f"[ {keys_text} ]")
        self.badge_label.setStyleSheet(
            "background: rgba(16, 185, 129, 0.2); color: #34D399; font-weight: bold; border-radius: 6px; padding: 3px 8px;"
        )
        self.badge_label.show()

        needed_width = max(380, min(560, len(desc) * 9 + len(keys_text) * 12 + 100))
        self._update_geometry(needed_width)
        if not self.is_visible_on_screen:
            self.slide_down()
        self.update()

        # Disappear after 1.8 seconds of glory!
        self.hide_timer.start(1800)

    def show_unmatched(self, raw_text: str, score: float):
        """Triggered when speech was heard but below threshold."""
        self.bg_color = QColor(25, 18, 18, 245)
        self.border_color = QColor(239, 68, 68, 120)  # Red accent
        self.border_width = 1.5

        self.icon_label.setText("✖")
        self.text_label.setText(f'"{raw_text}" (Anlaşılamadı)')
        self.badge_label.hide()

        self._update_geometry(320)
        if not self.is_visible_on_screen:
            self.slide_down()
        self.update()

        # Disappear after 1.5 seconds
        self.hide_timer.start(1500)

    def show_exit(self):
        """Show goodbye and quit."""
        self.bg_color = QColor(15, 17, 23, 250)
        self.border_color = QColor(245, 158, 11, 200)
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
