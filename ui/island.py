import math
import os
import random
import sys
from typing import List, Optional

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    try:
        user32 = ctypes.windll.user32
        user32.SetWindowPos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint,
        ]
        user32.SetWindowPos.restype = wintypes.BOOL
    except Exception:
        user32 = None
else:
    user32 = None

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
    QVariantAnimation,
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


def lerp_color(c1: QColor, c2: QColor, t: float) -> QColor:
    """Linearly interpolates between two QColor instances."""
    r = int(c1.red() + (c2.red() - c1.red()) * t)
    g = int(c1.green() + (c2.green() - c1.green()) * t)
    b = int(c1.blue() + (c2.blue() - c1.blue()) * t)
    a = int(c1.alpha() + (c2.alpha() - c1.alpha()) * t)
    return QColor(
        max(0, min(255, r)),
        max(0, min(255, g)),
        max(0, min(255, b)),
        max(0, min(255, a)),
    )


class IslandSignals(QObject):
    sig_speech_start = pyqtSignal()
    sig_audio_level = pyqtSignal(float)
    sig_transcribed = pyqtSignal(str)
    sig_waiting_command = pyqtSignal()
    sig_window_switch_mode = pyqtSignal()
    sig_executed = pyqtSignal(str, list, float)  # desc, keys, score
    sig_unmatched = pyqtSignal(str, float)       # text, score
    sig_exit = pyqtSignal()
    sig_continuous_toggled = pyqtSignal(bool)   # True = continuous ON, False = continuous OFF


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
        self.active_color = QColor(235, 240, 248, 220)  # Pure cool white/silver default

        # 30 FPS smooth physics decay timer (started only when island is visible)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_physics)

    def start_anim(self):
        if not self.timer.isActive():
            self.timer.start(33)

    def stop_anim(self):
        if self.timer.isActive():
            self.timer.stop()
        self.current_heights = [4.0, 4.0, 4.0, 4.0]
        self.target_heights = [4.0, 4.0, 4.0, 4.0]

    def set_level(self, level: float):
        """Called when new audio amplitude arrives (0.0 to 1.0)."""
        max_h = 20.0
        min_h = 4.0
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
            diff = self.target_heights[i] - self.current_heights[i]
            if abs(diff) > 0.3:
                self.current_heights[i] += diff * 0.4
                changed = True
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
    # Predefined Theme Archetypes
    THEME_DEFAULT_BG = QColor(10, 11, 14, 252)         # Pitch-black obsidian matte glass
    THEME_DEFAULT_BORDER = QColor(255, 255, 255, 28)    # Frosted platinum edge
    THEME_DEFAULT_VIS = QColor(235, 240, 248, 220)      # Clean monochrome silver-white

    THEME_SUCCESS_BG = QColor(6, 26, 18, 252)           # Emerald dark glass
    THEME_SUCCESS_BORDER = QColor(16, 185, 129, 240)    # Glowing emerald green border
    THEME_SUCCESS_VIS = QColor(52, 211, 153)            # Cyber emerald visualizer

    THEME_ERROR_BG = QColor(28, 10, 14, 252)            # Crimson dark glass
    THEME_ERROR_BORDER = QColor(239, 68, 68, 230)       # Glowing ruby red border
    THEME_ERROR_VIS = QColor(248, 113, 113)             # Fiery warning red visualizer

    THEME_CONTINUOUS_BG = QColor(26, 12, 44, 252)        # Obsidian violet dark glass
    THEME_CONTINUOUS_BORDER = QColor(168, 85, 247, 240)  # Glowing electric violet border
    THEME_CONTINUOUS_VIS = QColor(192, 132, 252)         # Radiant neon violet visualizer

    def __init__(self):
        super().__init__()

        # Frameless, Always on Top, Tool window, Does Not Steal Focus
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)

        # Continuous listening toggle state
        self.is_continuous_mode = False

        # Island dimensions & relative offsets
        self.island_height = 44
        self.current_width = 280
        self.target_y_offset = 12
        self.hidden_y_offset = -85

        # Visual styling
        self.bg_color = QColor(self.THEME_DEFAULT_BG)
        self.border_color = QColor(self.THEME_DEFAULT_BORDER)
        self.border_width = 1.2

        # Morph Animation Engines
        self.morph_anim = QVariantAnimation(self)
        self.morph_anim.setDuration(260)
        self.morph_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.morph_anim.valueChanged.connect(self._on_morph_step)

        self._start_bg = self.bg_color
        self._target_bg = self.bg_color
        self._start_border = self.border_color
        self._target_border = self.border_color
        self._start_vis_color = self.THEME_DEFAULT_VIS
        self._target_vis_color = self.THEME_DEFAULT_VIS

        # Width Animation Engine (Liquid Pill Stretching)
        self.width_anim = QVariantAnimation(self)
        self.width_anim.setDuration(240)
        self.width_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.width_anim.valueChanged.connect(self._on_width_step)

        # Screen geometry (dynamically adapts to active monitor where cursor is)
        self.screen_geo = self.get_target_screen_geometry()
        init_x = self.screen_geo.x() + (self.screen_geo.width() - self.current_width) // 2
        init_y = self.screen_geo.y() + self.hidden_y_offset

        # Start hidden above top bezel
        self.setGeometry(init_x, init_y, self.current_width, self.island_height)

        # UI elements layout
        self._init_layout()

        # Position slide animation
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(280)
        self.pos_anim.finished.connect(self.force_on_top)

        # Auto-hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.slide_up)

        # Periodic topmost watchdog timer (active only when island is visible on screen)
        self.topmost_watchdog = QTimer(self)
        self.topmost_watchdog.setInterval(500)
        self.topmost_watchdog.timeout.connect(self._enforce_topmost_if_visible)

        # Tray icon
        self._init_tray_icon()

        self.is_visible_on_screen = False

    def _init_layout(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
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
        self.text_label.setStyleSheet("color: #F3F4F6; background: transparent;")
        layout.addWidget(self.text_label, stretch=1)

        # Shortcut badge (e.g. [ Win + D ])
        self.badge_label = QLabel("")
        self.badge_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.badge_label.setStyleSheet(
            "background: rgba(16, 185, 129, 0.18); color: #34D399; font-weight: bold; border-radius: 6px; padding: 3px 8px; border: 1px solid rgba(16, 185, 129, 0.35);"
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
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, "config", "commands.json")
        try:
            os.startfile(config_path)
        except Exception:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        radius = rect.height() / 2.0

        # Multi-layer subtle dark ambient shadow
        for offset, alpha in [(3, 10), (2, 22), (1, 38)]:
            g_rect = rect.adjusted(-offset, -offset, offset, offset)
            g_rad = g_rect.height() / 2.0
            g_path = QPainterPath()
            g_path.addRoundedRect(g_rect.x(), g_rect.y(), g_rect.width(), g_rect.height(), g_rad, g_rad)
            painter.fillPath(g_path, QColor(0, 0, 0, alpha))

        # Main Capsule Pill
        path = QPainterPath()
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)

        # Background fill
        painter.fillPath(path, self.bg_color)

        # Subtle top inner highlight line for hardware glass depth
        highlight_path = QPainterPath()
        highlight_rect = rect.adjusted(1, 1, -1, -1)
        highlight_rad = highlight_rect.height() / 2.0
        highlight_path.addRoundedRect(highlight_rect.x(), highlight_rect.y(), highlight_rect.width(), highlight_rect.height(), highlight_rad, highlight_rad)
        painter.setPen(QPen(QColor(255, 255, 255, 16), 1.0))
        painter.drawPath(highlight_path)

        # Outer animated colored border
        pen = QPen(self.border_color, self.border_width)
        painter.setPen(pen)
        painter.drawPath(path)

    def morph_theme(
        self,
        target_bg: QColor,
        target_border: QColor,
        target_vis: QColor,
        border_width: float = 1.6,
        duration: int = 260,
    ):
        """Smoothly interpolates background, border, and visualizer colors."""
        self.morph_anim.stop()
        self._start_bg = QColor(self.bg_color)
        self._target_bg = QColor(target_bg)
        self._start_border = QColor(self.border_color)
        self._target_border = QColor(target_border)
        self._start_vis_color = QColor(self.visualizer.active_color)
        self._target_vis_color = QColor(target_vis)
        self.border_width = border_width

        self.morph_anim.setDuration(duration)
        self.morph_anim.setStartValue(0.0)
        self.morph_anim.setEndValue(1.0)
        self.morph_anim.start()

    def _on_morph_step(self, val):
        t = float(val)
        self.bg_color = lerp_color(self._start_bg, self._target_bg, t)
        self.border_color = lerp_color(self._start_border, self._target_border, t)
        vis_color = lerp_color(self._start_vis_color, self._target_vis_color, t)
        self.visualizer.set_color(vis_color)
        self.update()

    def morph_width(self, target_width: int, duration: int = 240):
        """Smoothly morphs the island width with easing curve."""
        if target_width == self.current_width:
            return
        self.width_anim.stop()
        self.width_anim.setDuration(duration)
        self.width_anim.setStartValue(float(self.current_width))
        self.width_anim.setEndValue(float(target_width))
        self.width_anim.start()

    @property
    def target_y(self) -> int:
        return self.screen_geo.y() + self.target_y_offset

    @property
    def hidden_y(self) -> int:
        return self.screen_geo.y() + self.hidden_y_offset

    def get_target_screen_geometry(self) -> QRect:
        """
        Returns geometry of active screen (where mouse cursor is located),
        or primary screen as fallback.
        """
        try:
            from PyQt6.QtGui import QCursor
            cursor_pos = QCursor.pos()
            screen = QApplication.screenAt(cursor_pos)
            if screen:
                return screen.geometry()
        except Exception:
            pass
        primary = QApplication.primaryScreen()
        return primary.geometry() if primary else QRect(0, 0, 1920, 1080)

    def force_on_top(self):
        """Forces the window to the very top of Windows Z-order above fullscreen apps."""
        if sys.platform == "win32" and user32 is not None:
            try:
                hwnd = wintypes.HWND(int(self.winId()))
                HWND_TOPMOST = wintypes.HWND(-1)
                SWP_NOSIZE = 0x0001
                SWP_NOMOVE = 0x0002
                SWP_NOACTIVATE = 0x0010
                SWP_SHOWWINDOW = 0x0040

                user32.SetWindowPos(
                    hwnd,
                    HWND_TOPMOST,
                    0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
                )
            except Exception:
                pass

        self.raise_()

    def _enforce_topmost_if_visible(self):
        if self.is_visible_on_screen:
            self.force_on_top()

    def _on_width_step(self, val):
        self.current_width = int(val)
        cx = self.screen_geo.x() + (self.screen_geo.width() - self.current_width) // 2
        self.setGeometry(cx, self.y(), self.current_width, self.island_height)
        self.update()

    def slide_down(self):
        """Slides the island down from top bezel into view with subtle tactile bounce."""
        self.hide_timer.stop()
        geo = self.get_target_screen_geometry()
        self.screen_geo = geo
        cx = geo.x() + (geo.width() - self.current_width) // 2
        target_y = geo.y() + self.target_y_offset

        self.pos_anim.stop()
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(QPoint(cx, target_y))
        self.show()
        self.force_on_top()
        self.pos_anim.start()
        self.is_visible_on_screen = True
        self.visualizer.start_anim()
        if not self.topmost_watchdog.isActive():
            self.topmost_watchdog.start()

    def slide_up(self):
        """Slides the island back up into the bezel, or transitions to continuous standby if toggle is active."""
        self.hide_timer.stop()
        if self.is_continuous_mode:
            self.show_continuous_standby()
            return

        cx = self.screen_geo.x() + (self.screen_geo.width() - self.current_width) // 2
        hidden_y = self.screen_geo.y() + self.hidden_y_offset

        self.pos_anim.stop()
        self.pos_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(QPoint(cx, hidden_y))
        self.pos_anim.start()
        self.is_visible_on_screen = False
        self.visualizer.stop_anim()
        self.topmost_watchdog.stop()

        # Reset stealth black theme for next invocation
        self.bg_color = QColor(self.THEME_DEFAULT_BG)
        self.border_color = QColor(self.THEME_DEFAULT_BORDER)
        self.visualizer.set_color(QColor(self.THEME_DEFAULT_VIS))
        self.border_width = 1.2

    def handle_audio_level(self, level: float):
        """Updates the live audio waveform."""
        if self.is_visible_on_screen:
            self.visualizer.set_level(level)

    # ---------------- State handlers ----------------

    def show_continuous_standby(self):
        """Persistent sleek standby capsule when continuous listening mode is active."""
        if not self.is_continuous_mode:
            return
        self.morph_theme(
            self.THEME_CONTINUOUS_BG,
            self.THEME_CONTINUOUS_BORDER,
            self.THEME_CONTINUOUS_VIS,
            border_width=1.5,
            duration=260,
        )
        self.icon_label.setText("⚡")
        self.text_label.setText("Sürekli Dinleniyor...")
        self.text_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self.badge_label.setText("[ Sürekli ]")
        self.badge_label.setStyleSheet(
            "background: rgba(168, 85, 247, 0.25); color: #C084FC; font-weight: bold; border-radius: 6px; padding: 3px 8px; border: 1px solid rgba(168, 85, 247, 0.4);"
        )
        self.badge_label.show()
        self.morph_width(295)
        self.slide_down()
        self.update()

    def show_continuous_mode(self, enabled: bool):
        """Triggered when continuous listening toggle is switched ON or OFF."""
        self.is_continuous_mode = enabled
        if enabled:
            self.morph_theme(
                self.THEME_CONTINUOUS_BG,
                self.THEME_CONTINUOUS_BORDER,
                self.THEME_CONTINUOUS_VIS,
                border_width=1.8,
                duration=280,
            )
            self.icon_label.setText("⚡")
            self.text_label.setText("Sürekli dinleme aktif")
            self.text_label.setStyleSheet("color: #FFFFFF; background: transparent;")
            self.badge_label.setText("[ Sürekli Dinleme ]")
            self.badge_label.setStyleSheet(
                "background: rgba(168, 85, 247, 0.25); color: #C084FC; font-weight: bold; border-radius: 6px; padding: 3px 8px; border: 1px solid rgba(168, 85, 247, 0.4);"
            )
            self.badge_label.show()
            self.morph_width(340)
            self.slide_down()
            self.update()
            # After 2.2s notification, settle smoothly into continuous listening standby capsule
            self.hide_timer.start(2200)
        else:
            self.morph_theme(
                QColor(15, 17, 23, 252),
                QColor(245, 158, 11, 230),
                QColor(245, 158, 11),
                border_width=1.6,
                duration=260,
            )
            self.icon_label.setText("🔒")
            self.text_label.setText("Sürekli dinleme kapatıldı")
            self.text_label.setStyleSheet("color: #FFFFFF; background: transparent;")
            self.badge_label.setText("[ Wake Word: Haydar ]")
            self.badge_label.setStyleSheet(
                "background: rgba(245, 158, 11, 0.2); color: #FBBF24; font-weight: bold; border-radius: 6px; padding: 3px 8px; border: 1px solid rgba(245, 158, 11, 0.35);"
            )
            self.badge_label.show()
            self.morph_width(370)
            self.slide_down()
            self.update()
            # Auto-retract back into bezel after 2.0s
            self.hide_timer.start(2000)

    def show_listening(self):
        """Triggered when speech starts or waiting for speech in standby."""
        if self.is_continuous_mode:
            self.bg_color = QColor(self.THEME_CONTINUOUS_BG)
            self.border_color = QColor(self.THEME_CONTINUOUS_BORDER)
            self.border_width = 1.4
            self.visualizer.set_color(QColor(self.THEME_CONTINUOUS_VIS))
            self.icon_label.setText("⚡")
            self.text_label.setText("Dinleniyor...")
            self.text_label.setStyleSheet("color: #F3F4F6; background: transparent;")
            self.badge_label.setText("[ Sürekli ]")
            self.badge_label.setStyleSheet(
                "background: rgba(168, 85, 247, 0.25); color: #C084FC; font-weight: bold; border-radius: 6px; padding: 3px 8px; border: 1px solid rgba(168, 85, 247, 0.4);"
            )
            self.badge_label.show()
            self.morph_width(290)
            self.slide_down()
            self.update()
        else:
            self.bg_color = QColor(self.THEME_DEFAULT_BG)
            self.border_color = QColor(self.THEME_DEFAULT_BORDER)
            self.border_width = 1.2
            self.visualizer.set_color(QColor(self.THEME_DEFAULT_VIS))
            self.icon_label.setText("🎙️")
            self.text_label.setText("Dinleniyor...")
            self.text_label.setStyleSheet("color: #F3F4F6; background: transparent;")
            self.badge_label.hide()
            self.morph_width(260)
            self.slide_down()
            self.update()

    def show_waiting_for_command(self):
        """Triggered when user says just 'Haydar' - enters matte stealth obsidian black!"""
        self.bg_color = QColor(self.THEME_DEFAULT_BG)
        self.border_color = QColor(255, 255, 255, 38)
        self.border_width = 1.3
        self.visualizer.set_color(QColor(self.THEME_DEFAULT_VIS))

        self.icon_label.setText("👋")
        self.text_label.setText("Efendim? Dinliyorum...")
        self.text_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self.badge_label.hide()

        self.morph_width(280)
        if not self.is_visible_on_screen:
            self.slide_down()
        else:
            self.force_on_top()
        self.update()

        # Generous 6-second window before auto-retracting
        self.hide_timer.start(6000)

    def show_window_switch_mode(self):
        """Triggered when Alt+Tab window switcher opens and assistant awaits window selection."""
        self.bg_color = QColor(self.THEME_DEFAULT_BG)
        self.border_color = QColor(59, 130, 246, 230)  # Azure blue border
        self.border_width = 1.6
        self.visualizer.set_color(QColor(96, 165, 250))  # Sky blue visualizer

        self.icon_label.setText("🪟")
        self.text_label.setText("Pencereler açıldı... Kaçıncı pencere?")
        self.text_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self.badge_label.setText("[ Alt + Tab ]")
        self.badge_label.setStyleSheet(
            "background: rgba(59, 130, 246, 0.22); color: #60A5FA; font-weight: bold; border-radius: 6px; padding: 3px 8px; border: 1px solid rgba(59, 130, 246, 0.35);"
        )
        self.badge_label.show()

        self.morph_width(380)
        if not self.is_visible_on_screen:
            self.slide_down()
        else:
            self.force_on_top()
        self.update()

        # Generous 8-second window for user to look at windows and say number
        self.hide_timer.start(8000)

    def show_transcribing(self, raw_text: str):
        """Triggered when speech is transcribed."""
        if self.is_continuous_mode:
            self.bg_color = QColor(self.THEME_CONTINUOUS_BG)
            self.border_color = QColor(self.THEME_CONTINUOUS_BORDER)
            self.visualizer.set_color(QColor(self.THEME_CONTINUOUS_VIS))

        self.icon_label.setText("💬")
        display_text = f'"{raw_text}"'
        self.text_label.setText(display_text)
        self.text_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self.badge_label.hide()

        needed_width = max(280, min(560, len(display_text) * 11 + 100))
        self.morph_width(needed_width)
        if not self.is_visible_on_screen:
            self.slide_down()
        else:
            self.force_on_top()
        self.update()

        # Safety auto-retract if processing hangs or takes too long
        self.hide_timer.start(5000)

    def show_executed(self, desc: str, keys: List[str], score: float):
        """Triggered when command matched and executed - morphs to radiant cyber emerald!"""
        self.morph_theme(
            self.THEME_SUCCESS_BG,
            self.THEME_SUCCESS_BORDER,
            self.THEME_SUCCESS_VIS,
            border_width=1.8,
            duration=280,
        )

        self.icon_label.setText("✔")
        self.text_label.setText(desc)
        self.text_label.setStyleSheet("color: #FFFFFF; background: transparent;")

        if keys:
            friendly_map = {
                "playpause": "⏯️ Oynat/Durdur",
                "nexttrack": "⏭️ Sonraki Şarkı",
                "prevtrack": "⏮️ Önceki Şarkı",
                "volumeup": "Ses +",
                "volumedown": "Ses -",
                "volumemute": "Sessiz",
                "win": "Win",
                "ctrl": "Ctrl",
                "alt": "Alt",
                "shift": "Shift",
                "space": "Boşluk",
                "escape": "ESC",
                "esc": "ESC",
                "f": "F",
                "f5": "F5",
                "f11": "F11",
                "tab": "Tab",
                "right": "Sağ Ok",
                "left": "Sol Ok",
                "up": "Yukarı Ok",
                "down": "Aşağı Ok",
                "m": "M",
                "d": "D",
                "pause": "Pause",
                "scrolllock": "Scroll Lock",
            }
            keys_text = " + ".join(friendly_map.get(k.lower(), k.upper()) for k in keys)
            self.badge_label.setText(f"[ {keys_text} ]")
            self.badge_label.setStyleSheet(
                "background: rgba(16, 185, 129, 0.2); color: #34D399; font-weight: bold; border-radius: 6px; padding: 3px 8px; border: 1px solid rgba(16, 185, 129, 0.35);"
            )
            self.badge_label.show()
            needed_width = max(380, min(600, len(desc) * 9 + len(keys_text) * 12 + 120))
        else:
            self.badge_label.hide()
            needed_width = max(320, min(520, len(desc) * 10 + 100))

        self.morph_width(needed_width)
        if not self.is_visible_on_screen:
            self.slide_down()
        else:
            self.force_on_top()

        # Disappear after 1.8 seconds of glory
        self.hide_timer.start(1800)

    def enterEvent(self, event):
        """When user hovers mouse over island, pause auto-hide timer to allow reading."""
        self.hide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """When user moves mouse away, resume hide timer with a short delay."""
        if self.is_visible_on_screen:
            self.hide_timer.start(3500)
        super().leaveEvent(event)

    def show_unmatched(self, raw_text: str, score: float):
        """Triggered when speech was heard but below threshold - morphs to fiery crimson red!"""
        self.morph_theme(
            self.THEME_ERROR_BG,
            self.THEME_ERROR_BORDER,
            self.THEME_ERROR_VIS,
            border_width=1.8,
            duration=240,
        )

        self.icon_label.setText("✕")
        if any(term in raw_text.lower() for term in ["bulunamadı", "bağlı değil", "iptal", "hata", "zaman aşımı", "yanıt vermedi"]):
            display_str = raw_text
        else:
            display_str = f'"{raw_text}" (Anlaşılamadı)'
        self.text_label.setText(display_str)
        self.text_label.setStyleSheet("color: #FCA5A5; background: transparent;")
        self.badge_label.hide()

        needed_width = max(340, min(540, len(raw_text) * 10 + 150))
        self.morph_width(needed_width)
        if not self.is_visible_on_screen:
            self.slide_down()
        else:
            self.force_on_top()

        # Disappear after 1.6 seconds
        self.hide_timer.start(1600)

    def show_exit(self):
        """Show goodbye and quit."""
        self.morph_theme(
            QColor(15, 17, 23, 252),
            QColor(245, 158, 11, 220),
            QColor(245, 158, 11),
            border_width=1.8,
            duration=200,
        )
        self.icon_label.setText("👋")
        self.text_label.setText("Görüşmek üzere...")
        self.text_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self.badge_label.hide()
        self.morph_width(260)
        self.slide_down()
        QTimer.singleShot(900, self.close_and_exit)

    def close_and_exit(self):
        self.tray.hide()
        QApplication.quit()
