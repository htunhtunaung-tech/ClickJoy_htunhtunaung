import math

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QFrame,
                               QLabel, QApplication)
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, Signal
from PySide6.QtGui import (QPainter, QPainterPath, QColor, QPen, QBrush, QRadialGradient)

from theme_and_animation import (F, FM, _make_back_btn, apply_theme, _build_stylesheet,
                                  _DARK_PALETTE, _LIGHT_PALETTE,
                                  TEXT, DIM, GHOST, EDGE, PANEL)


class _ThemeToggle(QWidget):
    toggled = Signal(bool)  # emits True = dark, False = light

    TW = 160; TH = 44; TD = 36

    def __init__(self, is_dark=True, parent=None):
        super().__init__(parent)
        self.setFixedSize(64, 32)
        self.setCursor(Qt.PointingHandCursor)
        self._dark = is_dark
        self._pos = 1.0 if is_dark else 0.0
        self._anim = QTimer(self)
        self._anim.setInterval(12)
        self._anim.timeout.connect(self._step)

    def _step(self):
        target = 1.0 if self._dark else 0.0
        diff = target - self._pos
        if abs(diff) < 0.04:
            self._pos = target
            self._anim.stop()
        else:
            self._pos += diff * 0.22
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._dark = not self._dark
            self._anim.start()
            self.toggled.emit(self._dark)

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); r = h / 2
        t = self._pos
        dark_c  = QColor("#1e2235")
        light_c = QColor("#e0e8ff")
        track_c = QColor(
            int(dark_c.red()   * t + light_c.red()   * (1-t)),
            int(dark_c.green() * t + light_c.green() * (1-t)),
            int(dark_c.blue()  * t + light_c.blue()  * (1-t)),
        )
        track_path = QPainterPath()
        track_path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        pa.fillPath(track_path, track_c)
        border_c = QColor("#3b82f6") if self._dark else QColor("#f59e0b")
        pa.strokePath(track_path, QPen(border_c, 1.5))
        pa.setFont(F(9, 400))
        pa.setPen(QColor(255, 255, 255, 100))
        pa.drawText(QRectF(4, 0, 20, h).toRect(), Qt.AlignCenter, "🌙")
        pa.drawText(QRectF(w-24, 0, 20, h).toRect(), Qt.AlignCenter, "☀")
        margin = 3
        travel = w - h
        cx = margin + r - margin + travel * self._pos
        cy = h / 2
        thumb_r = r - margin
        thumb_c = QColor("#3b82f6") if self._dark else QColor("#f59e0b")
        grd = QRadialGradient(cx, cy - thumb_r*0.3, thumb_r * 1.4)
        grd.setColorAt(0, thumb_c.lighter(130))
        grd.setColorAt(1, thumb_c)
        pa.setBrush(QBrush(grd))
        pa.setPen(Qt.NoPen)
        pa.drawEllipse(QPointF(cx, cy), thumb_r, thumb_r)
        glow_pen = QPen(QColor(thumb_c.red(), thumb_c.green(), thumb_c.blue(), 80), 5)
        pa.setPen(glow_pen); pa.setBrush(Qt.NoBrush)
        pa.drawEllipse(QPointF(cx, cy), thumb_r + 2, thumb_r + 2)
        pa.end()


class SettingPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self._main_window = main_window
        self._is_dark = True

        layout = QVBoxLayout(self); layout.setContentsMargins(16,16,16,16)
        layout.setSpacing(12)

        _hrow = QHBoxLayout(); _hrow.setSpacing(10); _hrow.setContentsMargins(0,0,0,0)
        _hrow.addWidget(_make_back_btn(lambda: main_window.go_to(1)), 0, Qt.AlignVCenter)
        self._htitle = QLabel("⚙️  Settings"); self._htitle.setFont(F(16, 700))
        self._htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        _hrow.addWidget(self._htitle, 1, Qt.AlignVCenter)
        layout.addLayout(_hrow)

        layout.addSpacing(24)

        self._theme_card = QFrame()
        self._theme_card.setStyleSheet(f"""
            QFrame {{
                background: {PANEL};
                border: 1px solid {EDGE};
                border-radius: 14px;
            }}
        """)
        card_lay = QHBoxLayout(self._theme_card)
        card_lay.setContentsMargins(20, 16, 20, 16)
        card_lay.setSpacing(14)

        theme_icon = QLabel("🎨"); theme_icon.setFont(F(22))
        theme_icon.setStyleSheet("background:transparent;")
        card_lay.addWidget(theme_icon, 0, Qt.AlignVCenter)

        text_col = QVBoxLayout(); text_col.setSpacing(2)
        self._theme_lbl = QLabel("Appearance"); self._theme_lbl.setFont(F(13, 600))
        self._theme_lbl.setStyleSheet(f"color:{TEXT};background:transparent;")
        self._theme_sub = QLabel("Dark mode"); self._theme_sub.setFont(F(10, 400))
        self._theme_sub.setStyleSheet(f"color:{DIM};background:transparent;")
        text_col.addWidget(self._theme_lbl)
        text_col.addWidget(self._theme_sub)
        card_lay.addLayout(text_col, 1)

        self._toggle = _ThemeToggle(is_dark=True)
        self._toggle.toggled.connect(self._on_theme_toggled)
        card_lay.addWidget(self._toggle, 0, Qt.AlignVCenter)

        layout.addWidget(self._theme_card)
        layout.addStretch()

    def _on_theme_toggled(self, is_dark: bool):
        self._is_dark = is_dark
        apply_theme(is_dark)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(
                _build_stylesheet(_DARK_PALETTE if is_dark else _LIGHT_PALETTE)
            )
        self._main_window.refresh_theme()
        self._theme_sub.setText("Dark mode" if is_dark else "Light mode")
        self._htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        self._theme_lbl.setStyleSheet(f"color:{TEXT};background:transparent;")
        self._theme_sub.setStyleSheet(f"color:{DIM};background:transparent;")
        self._theme_card.setStyleSheet(f"""
            QFrame {{
                background: {PANEL};
                border: 1px solid {EDGE};
                border-radius: 14px;
            }}
        """)
        self.update()