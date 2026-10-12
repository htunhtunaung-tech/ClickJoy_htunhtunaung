import sys
import math
import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QGraphicsDropShadowEffect, QFrame)
from PySide6.QtCore import Qt, QTimer, QRect, QRectF, QPointF
from PySide6.QtGui import (QFont, QColor, QPainter, QPainterPath, QPen,
                            QBrush, QRadialGradient, QLinearGradient, QPolygonF)
from game_data import ICONS, NAMES

# ==================== Theme Palettes ====================
_DARK_PALETTE = dict(
    BG      = "#0e0f14",
    SURFACE = "#13151c",
    PANEL   = "#181b25",
    EDGE    = "#22263a",
    TEXT    = "#e8ecff",
    DIM     = "#5a637a",
    GHOST   = "#2a2e40",
)

_LIGHT_PALETTE = dict(
    BG      = "#f0f2f8",
    SURFACE = "#e4e8f4",
    PANEL   = "#dce1f0",
    EDGE    = "#c2c8dc",
    TEXT    = "#1a1d2e",
    DIM     = "#6b7599",
    GHOST   = "#ccd1e4",
)

BG      = _DARK_PALETTE["BG"]
SURFACE = _DARK_PALETTE["SURFACE"]
PANEL   = _DARK_PALETTE["PANEL"]
EDGE    = _DARK_PALETTE["EDGE"]
TEXT    = _DARK_PALETTE["TEXT"]
DIM     = _DARK_PALETTE["DIM"]
GHOST   = _DARK_PALETTE["GHOST"]

_DARK_NEON = {
    "normal": ("#3b82f6", "#0f2a5c", "#60a5fa", "#060c1a"),
    "flip":   ("#f59e0b", "#5a3600", "#fcd34d", "#1a0f00"),
    "switch": ("#10b981", "#043d28", "#34d399", "#001a0e"),
    "swap":   ("#ec4899", "#5a0c30", "#f472b6", "#1a0010"),
    "cpm":    ("#8b5cf6", "#2d0f5c", "#a78bfa", "#0d0020"),
    "stop":   ("#06b6d4", "#023648", "#67e8f9", "#001a20"),
    "pop":    ("#f97316", "#5c1f00", "#fb923c", "#1a0800"),
    "focus":  ("#e879f9", "#4d0060", "#f0abfc", "#1a0020"),
    "chaos":  ("#ff4d4d", "#5a0000", "#ff8080", "#1a0000"),
    "memory": ("#00e5ff", "#003648", "#80f0ff", "#001a20"),
    "dopa":   ("#39ff14", "#073a00", "#80ff60", "#001200"),
    "rcs":    ("#a3e635", "#2e4a00", "#c0d0ff", "#080810"),
}
ACCENT = "#3b82f6"

ACCENT_PRESETS = [
    ("#3b82f6", "Blue"),
    ("#8b5cf6", "Purple"),
    ("#ec4899", "Pink"),
    ("#10b981", "Emerald"),
    ("#f59e0b", "Amber"),
    ("#06b6d4", "Cyan"),
    ("#f97316", "Orange"),
    ("#ff4d4d", "Red"),
    ("#39ff14", "Lime"),
    ("#e879f9", "Fuchsia"),
]

_LIGHT_NEON = {
    "normal": ("#2563eb", "#bfdbfe", "#1d4ed8", "#dbeafe"),
    "flip":   ("#d97706", "#fde68a", "#b45309", "#fef3c7"),
    "switch": ("#059669", "#a7f3d0", "#047857", "#d1fae5"),
    "swap":   ("#db2777", "#fbcfe8", "#be185d", "#fce7f3"),
    "cpm":    ("#7c3aed", "#ddd6fe", "#6d28d9", "#ede9fe"),
    "stop":   ("#0891b2", "#a5f3fc", "#0e7490", "#cffafe"),
    "pop":    ("#ea580c", "#fed7aa", "#c2410c", "#ffedd5"),
    "focus":  ("#c026d3", "#f5d0fe", "#a21caf", "#fae8ff"),
    "chaos":  ("#dc2626", "#fecaca", "#b91c1c", "#fee2e2"),
    "memory": ("#0284c7", "#bae6fd", "#0369a1", "#e0f2fe"),
    "dopa":   ("#16a34a", "#bbf7d0", "#15803d", "#dcfce7"),
    "rcs":    ("#65a30d", "#d9f99d", "#4d7c0f", "#ecfccb"),
}

NEON = dict(_DARK_NEON)


def apply_theme(is_dark: bool) -> None:
    import sys as _sys
    _mod = _sys.modules[__name__]
    src = _DARK_PALETTE if is_dark else _LIGHT_PALETTE
    for _k, _v in src.items():
        globals()[_k] = _v
        setattr(_mod, _k, _v)
    neon_src = _DARK_NEON if is_dark else _LIGHT_NEON
    NEON.clear()
    NEON.update(neon_src)


def F(size=14, weight=400):
    size = max(1, int(size))
    f = QFont()
    f.setFamily("Segoe UI")
    f.setPointSize(size)
    _W = {
        400: QFont.Weight.Normal, 500: QFont.Weight.Medium,
        600: QFont.Weight.DemiBold, 700: QFont.Weight.Bold,
        800: QFont.Weight.ExtraBold, 900: QFont.Weight.Black,
    }
    f.setWeight(_W.get(weight, QFont.Weight.Normal))
    return f


def FM(size=14, bold=False):
    size = max(1, int(size))
    f = QFont()
    for name in ("Consolas", "Courier New", "monospace"):
        f.setFamily(name); break
    f.setPointSize(size)
    f.setBold(bold)
    return f


def _make_back_btn(on_click):
    class _B(QWidget):
        def __init__(self):
            super().__init__()
            self.setFixedSize(44, 44); self.setCursor(Qt.PointingHandCursor)
            self._hover = False
        def enterEvent(self, e): self._hover = True;  self.update()
        def leaveEvent(self, e): self._hover = False; self.update()
        def mousePressEvent(self, e):
            if e.button() == Qt.LeftButton: on_click()
        def paintEvent(self, ev):
            pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
            nc = QColor(TEXT)
            path = QPainterPath(); path.addRoundedRect(QRectF(1,1,42,42), 11, 11)
            pa.fillPath(path, QColor(PANEL))
            pa.strokePath(path, QPen(QColor(nc.red(),nc.green(),nc.blue(), 160 if self._hover else 60), 1.5))
            pa.setPen(QPen(QColor(DIM if not self._hover else TEXT), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            cx, cy = 19, 22; s = 7
            pa.drawPolyline(QPolygonF([QPointF(cx+s*0.6, cy-s), QPointF(cx-s*0.4, cy), QPointF(cx+s*0.6, cy+s)]))
            pa.end()
    return _B()


class Toast(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._alpha = 0; self._phase = "in"; self._hold = 0
        self._text = ""; self._color = "#3b82f6"
        self._t = QTimer(self); self._t.setInterval(16)
        self._t.timeout.connect(self._step)
        self.setFixedHeight(44); self.hide()

    def show_msg(self, text, color="#3b82f6", hold_ms=1800):
        self._text = text; self._color = color
        self._alpha = 0; self._phase = "in"
        self._hold_target = hold_ms // 16
        self._hold = 0
        self._reposition()
        self.show(); self._t.start()

    def _reposition(self):
        p = self.parent()
        if p:
            w = min(p.width() - 40, 400)
            self.setFixedWidth(w)
            self.move((p.width() - w) // 2, p.height() - 70)

    def resizeEvent(self, e): self._reposition()

    def _step(self):
        if self._phase == "in":
            self._alpha = min(255, self._alpha + 18)
            if self._alpha >= 255: self._phase = "hold"
        elif self._phase == "hold":
            self._hold += 1
            if self._hold >= self._hold_target: self._phase = "out"
        else:
            self._alpha = max(0, self._alpha - 12)
            if self._alpha == 0:
                self._t.stop(); self.hide(); return
        self.update()

    def paintEvent(self, ev):
        if not self._text: return
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        nc = QColor(self._color); a = self._alpha
        bg = QPainterPath(); bg.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 12, 12)
        pa.fillPath(bg, QColor(22, 26, 38, int(a * 0.92)))
        pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), a), 1.5))
        pa.setBrush(Qt.NoBrush); pa.drawRoundedRect(QRectF(1, 1, self.width()-2, self.height()-2), 12, 12)
        pa.setFont(F(10, 600)); pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), a))
        pa.drawText(QRect(0, 0, self.width(), self.height()), Qt.AlignCenter, self._text)
        pa.end()


_toast_instance = None

def show_toast(parent_window, text, color="#3b82f6", hold_ms=1800):
    global _toast_instance
    root = parent_window
    while root.parent(): root = root.parent()
    if _toast_instance is None or _toast_instance.parent() is not root:
        _toast_instance = Toast(root)
    _toast_instance._reposition = lambda: (
        _toast_instance.setFixedWidth(min(root.width() - 40, 400)),
        _toast_instance.move((root.width() - _toast_instance.width()) // 2, root.height() - 80)
    )
    _toast_instance.show_msg(text, color, hold_ms)


class NeonBackground(QWidget):
    def __init__(self, key, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.key = key
        self._phase = random.uniform(0, math.pi * 2)
        self._t = QTimer(self); self._t.setInterval(40); self._t.timeout.connect(self._step)
        self._t.start()

    def _step(self):
        self._phase += 0.012
        self.update()

    def paintEvent(self, ev):
        if self.key not in NEON: return
        neon, gd, a2, bg_tint = NEON[self.key]
        pa = QPainter(self)
        pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        pa.fillRect(0, 0, w, h, QColor(BG))
        dot_c = QColor(255, 255, 255, 10)
        step = 28
        pa.setPen(Qt.NoPen)
        pa.setBrush(dot_c)
        for gx in range(0, w + step, step):
            for gy in range(0, h + step, step):
                pa.drawEllipse(gx - 1, gy - 1, 2, 2)
        nc = QColor(gd)
        ox = int(w * (0.65 + 0.18 * math.sin(self._phase * 0.6)))
        oy = int(h * (0.30 + 0.14 * math.cos(self._phase * 0.4)))
        orb_r = int(min(w, h) * 0.55)
        orb = QRadialGradient(ox, oy, orb_r)
        orb.setColorAt(0.0, QColor(nc.red(), nc.green(), nc.blue(), 90))
        orb.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.setBrush(QBrush(orb)); pa.setPen(Qt.NoPen)
        pa.drawEllipse(ox - orb_r, oy - orb_r, orb_r * 2, orb_r * 2)
        nc2 = QColor(neon)
        ox2 = int(w * (0.20 + 0.10 * math.cos(self._phase * 0.7 + 1.0)))
        oy2 = int(h * (0.75 + 0.12 * math.sin(self._phase * 0.5 + 0.5)))
        r2 = int(min(w, h) * 0.35)
        orb2 = QRadialGradient(ox2, oy2, r2)
        orb2.setColorAt(0.0, QColor(nc2.red(), nc2.green(), nc2.blue(), 50))
        orb2.setColorAt(1.0, QColor(nc2.red(), nc2.green(), nc2.blue(), 0))
        pa.setBrush(QBrush(orb2))
        pa.drawEllipse(ox2 - r2, oy2 - r2, r2 * 2, r2 * 2)
        sl = QColor(0, 0, 0, 18)
        for y in range(0, h, 3):
            pa.fillRect(0, y, w, 1, sl)
        pa.end()


class NeonPanel(QWidget):
    def __init__(self, neon_color, radius=14, bar=4, parent=None):
        super().__init__(parent)
        self._neon  = neon_color
        self._r     = radius
        self._bar   = bar
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, ev):
        pa = QPainter(self)
        pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        bar = self._bar
        body = QPainterPath()
        body.addRoundedRect(QRectF(bar, 0, w - bar, h), self._r, self._r)
        pa.fillPath(body, QColor(24, 27, 37, 230))
        hi = QLinearGradient(0, 0, 0, 20)
        hi.setColorAt(0, QColor(255, 255, 255, 22))
        hi.setColorAt(1, QColor(255, 255, 255, 0))
        pa.strokePath(body, QPen(QBrush(hi), 1))
        nc = QColor(self._neon)
        bar_path = QPainterPath()
        bar_path.addRoundedRect(QRectF(0, h * 0.15, bar, h * 0.70), bar // 2, bar // 2)
        pa.fillPath(bar_path, nc)
        glow = QRadialGradient(bar // 2, h // 2, h * 0.4)
        glow.setColorAt(0.0, QColor(nc.red(), nc.green(), nc.blue(), 55))
        glow.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.setBrush(QBrush(glow)); pa.setPen(Qt.NoPen)
        pa.drawRect(0, 0, 60, h)
        pa.end()


class CornerBrackets(QWidget):
    def __init__(self, neon_color, size=24, thickness=2, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._neon  = neon_color
        self._sz    = size
        self._th    = thickness
        self._phase = 0.0
        self._t = QTimer(self); self._t.setInterval(40)
        self._t.timeout.connect(self._step); self._t.start()

    def _step(self):
        self._phase = (self._phase + 0.04) % (math.pi * 2)
        self.update()

    def paintEvent(self, ev):
        pa = QPainter(self)
        pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        sz = self._sz
        pulse = 0.55 + 0.45 * math.sin(self._phase)
        nc = QColor(self._neon)
        alpha = int(120 + 135 * pulse)
        pen = QPen(QColor(nc.red(), nc.green(), nc.blue(), alpha), self._th)
        pen.setCapStyle(Qt.RoundCap)
        pa.setPen(pen); pa.setBrush(Qt.NoBrush)
        pa.drawLine(0, sz, 0, 0); pa.drawLine(0, 0, sz, 0)
        pa.drawLine(w - sz, 0, w, 0); pa.drawLine(w, 0, w, sz)
        pa.drawLine(0, h - sz, 0, h); pa.drawLine(0, h, sz, h)
        pa.drawLine(w - sz, h, w, h); pa.drawLine(w, h, w, h - sz)
        pa.end()


class NeonScore(QWidget):
    def __init__(self, neon, size=72, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._neon = neon
        self._size = size
        self._text = "0"
        self.setMinimumHeight(size + 20)

    def set(self, text): self._text = str(text); self.update()

    def paintEvent(self, ev):
        pa = QPainter(self)
        pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        nc = QColor(self._neon)
        pa.setPen(QColor(0, 0, 0, 120))
        pa.setFont(FM(self._size, True))
        pa.drawText(QRect(3, 3, w, h), Qt.AlignCenter, self._text)
        nc_soft = QColor(nc.red(), nc.green(), nc.blue(), 60)
        pa.setPen(nc_soft)
        for offset in [(-2,0),(2,0),(0,-2),(0,2),(-1,-1),(1,1)]:
            pa.drawText(QRect(offset[0], offset[1], w, h), Qt.AlignCenter, self._text)
        pa.setPen(nc)
        pa.setFont(FM(self._size, True))
        pa.drawText(QRect(0, 0, w, h), Qt.AlignCenter, self._text)
        pa.end()


class GlowLabel(QLabel):
    def __init__(self, text, color, size=52, mono=False, parent=None):
        super().__init__(text, parent)
        self.setFont(FM(size, True) if mono else F(size, 700))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"color:{color};background:transparent;")
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(35); eff.setColor(QColor(color)); eff.setOffset(0, 0)
        self.setGraphicsEffect(eff)

    def set(self, t): self.setText(str(t))


class StatChip(QWidget):
    def __init__(self, label, value, neon, parent=None):
        super().__init__(parent)
        self._neon = neon
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(3)
        self._val = QLabel(str(value))
        self._val.setFont(FM(18, True))
        self._val.setAlignment(Qt.AlignCenter)
        self._val.setStyleSheet(f"color:{neon};background:transparent;")
        cap = QLabel(label.upper())
        cap.setFont(F(8, 500))
        cap.setAlignment(Qt.AlignCenter)
        cap.setStyleSheet(f"color:{DIM};background:transparent;letter-spacing:2px;")
        lay.addWidget(self._val); lay.addWidget(cap)

    def set(self, v): self._val.setText(str(v))

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        nc = QColor(self._neon)
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 10, 10)
        pa.fillPath(path, QColor(18, 20, 30, 220))
        pa.strokePath(path, QPen(QColor(nc.red(), nc.green(), nc.blue(), 80), 1))
        hi = QLinearGradient(0, 0, 0, 10)
        hi.setColorAt(0, QColor(nc.red(), nc.green(), nc.blue(), 40))
        hi.setColorAt(1, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.fillPath(path, QBrush(hi))
        pa.end()


class NeonTapButton(QWidget):
    clicked = None

    def __init__(self, label, neon, accent, size=200, parent=None):
        super().__init__(parent)
        self.label = label; self.neon = neon; self.accent = accent
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self._press  = 0.0
        self._ripple = 0.0
        self._pulse  = 0.0
        self._hover  = False
        self._t = QTimer(self); self._t.setInterval(16); self._t.timeout.connect(self._tick)
        self._t.start()

    def _tick(self):
        if self._press  > 0: self._press  = max(0, self._press  - 0.07)
        if self._ripple > 0: self._ripple = max(0, self._ripple - 0.035)
        self._pulse = (self._pulse + 0.025) % (math.pi * 2)
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._press = 1.0; self._ripple = 1.0
            if self.clicked: self.clicked()

    def enterEvent(self, e): self._hover = True
    def leaveEvent(self, e): self._hover = False

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w = self.width(); cx = cy = w // 2
        nc = QColor(self.neon); ac = QColor(self.accent)
        br = w // 2 - 6
        pulse_alpha = int(30 + 25 * math.sin(self._pulse)) + (20 if self._hover else 0)
        halo = QRadialGradient(cx, cy, br + 30)
        halo.setColorAt(0.6, QColor(nc.red(), nc.green(), nc.blue(), 0))
        halo.setColorAt(0.80, QColor(nc.red(), nc.green(), nc.blue(), pulse_alpha))
        halo.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.setBrush(QBrush(halo)); pa.setPen(Qt.NoPen)
        pa.drawEllipse(cx - br - 30, cy - br - 30, (br + 30) * 2, (br + 30) * 2)
        if self._ripple > 0:
            rr = int(br + (1 - self._ripple) * 55)
            rpen_c = QColor(nc.red(), nc.green(), nc.blue(), int(self._ripple * 180))
            pa.setPen(QPen(rpen_c, 2)); pa.setBrush(Qt.NoBrush)
            pa.drawEllipse(cx - rr, cy - rr, rr * 2, rr * 2)
            rr2 = int(br + (1 - self._ripple) * 80)
            rpen_c2 = QColor(nc.red(), nc.green(), nc.blue(), int(self._ripple * 80))
            pa.setPen(QPen(rpen_c2, 1))
            pa.drawEllipse(cx - rr2, cy - rr2, rr2 * 2, rr2 * 2)
        pressed_r = int(br - self._press * 10)
        disc = QPainterPath()
        disc.addEllipse(QPointF(cx, cy), float(pressed_r), float(pressed_r))
        pa.fillPath(disc, QColor(14, 16, 24, 245))
        pa.strokePath(disc, QPen(QColor(nc.red(), nc.green(), nc.blue(), 40), 12))
        pa.strokePath(disc, QPen(nc, 2))
        inner = QRadialGradient(cx, cy - pressed_r // 4, pressed_r // 2)
        inner.setColorAt(0.0, QColor(nc.red(), nc.green(), nc.blue(), 30 + int(20 * self._press)))
        inner.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.fillPath(disc, QBrush(inner))
        pa.setPen(QColor(0, 0, 0, 160))
        pa.setFont(F(w // 5, 700))
        pa.drawText(QRect(2, 2, w, w), Qt.AlignCenter, self.label)
        pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), 240))
        pa.drawText(QRect(0, 0, w, w), Qt.AlignCenter, self.label)
        pa.end()


class _Spark:
    __slots__ = ('x','y','vx','vy','life','decay','size','r','g','b','shape')
    def __init__(self, x, y, color):
        a = random.uniform(0, math.pi * 2)
        s = random.uniform(2, 8)
        self.x = float(x); self.y = float(y)
        self.vx = math.cos(a) * s; self.vy = math.sin(a) * s - random.uniform(0.5, 2.5)
        self.life = 1.0; self.decay = random.uniform(0.025, 0.07)
        self.size = random.uniform(2, 7)
        c = QColor(color); self.r = c.red(); self.g = c.green(); self.b = c.blue()
        self.shape = random.choice(['circle', 'square', 'diamond'])


class Particles(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._sparks = []
        self._t = QTimer(self); self._t.setInterval(16); self._t.timeout.connect(self._step)

    def burst(self, x, y, color, n=24):
        self._sparks += [_Spark(x, y, color) for _ in range(n)]
        self._t.start()

    def _step(self):
        live = []
        for s in self._sparks:
            s.x += s.vx; s.y += s.vy; s.vy += 0.22; s.vx *= 0.97; s.life -= s.decay
            if s.life > 0: live.append(s)
        self._sparks = live
        if not live: self._t.stop()
        self.update()

    def paintEvent(self, ev):
        if not self._sparks: return
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        pa.setPen(Qt.NoPen)
        for s in self._sparks:
            alpha = int(max(0, s.life) * 230)
            pa.setBrush(QColor(s.r, s.g, s.b, alpha))
            sz = s.size * s.life
            if s.shape == 'circle':
                pa.drawEllipse(QRectF(s.x - sz/2, s.y - sz/2, sz, sz))
            elif s.shape == 'square':
                pa.drawRect(QRectF(s.x - sz/2, s.y - sz/2, sz, sz))
            else:
                pts = QPolygonF([
                    QPointF(s.x, s.y - sz), QPointF(s.x + sz, s.y),
                    QPointF(s.x, s.y + sz), QPointF(s.x - sz, s.y)
                ])
                pa.drawPolygon(pts)
        pa.end()


class NeonToggle(QWidget):
    TW = 160; TH = 44; TD = 36

    def __init__(self, neon, accent, parent=None):
        super().__init__(parent)
        self.neon = neon; self.accent = accent
        self.setFixedSize(self.TW, self.TH + 24)
        self.setCursor(Qt.PointingHandCursor)
        self._on = False; self._pos = 0.0
        self._t = QTimer(self); self._t.setInterval(12); self._t.timeout.connect(self._anim)
        self.toggled = None

    def set_state(self, on):
        self._on = on; self._pos = 1.0 if on else 0.0; self.update()

    def _anim(self):
        target = 1.0 if self._on else 0.0
        self._pos += (target - self._pos) * 0.22
        if abs(self._pos - target) < 0.004: self._pos = target; self._t.stop()
        self.update()

    def mousePressEvent(self, e):
        self._on = not self._on; self._t.start()
        if self.toggled: self.toggled()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        tw = self.TW; th = self.TH; ty = (h - th) // 2
        tr = th // 2
        nc = QColor(self.neon)
        track = QPainterPath()
        track.addRoundedRect(QRectF(0, ty, tw, th), tr, tr)
        pa.fillPath(track, QColor(12, 14, 20, 240))
        if self._pos > 0:
            nf = QPainterPath()
            filled_w = tr + (tw - tr * 2) * self._pos
            nf.addRoundedRect(QRectF(0, ty, filled_w + tr, th), tr, tr)
            fill_c = QColor(nc.red(), nc.green(), nc.blue(), int(160 * self._pos))
            pa.fillPath(nf, fill_c)
        pa.strokePath(track, QPen(QColor(nc.red(), nc.green(), nc.blue(),
                                         int(60 + 120 * self._pos)), 1.5))
        pa.setPen(QPen(QColor(255, 255, 255, 25), 1))
        for tx in range(tr + 10, tw - tr - 10, 12):
            pa.drawLine(tx, ty + 8, tx, ty + th - 8)
        left_cx = float(tr); right_cx = float(tw - tr)
        cx = left_cx + self._pos * (right_cx - left_cx)
        cy = float(h // 2)
        thr = self.TD // 2
        pa.setPen(Qt.NoPen)
        pa.setBrush(QColor(0, 0, 0, 80))
        pa.drawEllipse(QPointF(cx + 1, cy + 2), float(thr), float(thr))
        thumb = QPainterPath()
        thumb.addEllipse(QPointF(cx, cy), float(thr), float(thr))
        if self._pos > 0.5:
            tgrd = QRadialGradient(cx - thr * 0.3, cy - thr * 0.3, thr * 1.2)
            tgrd.setColorAt(0, QColor(min(nc.red() + 80, 255), min(nc.green() + 80, 255), min(nc.blue() + 80, 255)))
            tgrd.setColorAt(1, nc)
            pa.fillPath(thumb, QBrush(tgrd))
        else:
            tgrd2 = QRadialGradient(cx - thr * 0.3, cy - thr * 0.3, thr)
            tgrd2.setColorAt(0, QColor(80, 85, 105)); tgrd2.setColorAt(1, QColor(40, 44, 60))
            pa.fillPath(thumb, QBrush(tgrd2))
        if self._pos > 0.4:
            glow_a = int(140 * self._pos)
            pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), glow_a), 3))
            pa.setBrush(Qt.NoBrush)
            pa.drawEllipse(QPointF(cx, cy), float(thr + 4), float(thr + 4))
        pa.strokePath(thumb, QPen(QColor(255, 255, 255, 80), 1))
        pa.end()


class NeonRing(QWidget):
    def __init__(self, neon, accent, size=200, parent=None):
        super().__init__(parent)
        self.neon = neon; self.accent = accent
        self.setFixedSize(size, size)
        self._progress = 1.0; self._text = "—"
        self._phase = 0.0
        self._t = QTimer(self); self._t.setInterval(40); self._t.timeout.connect(self._tick)
        self._t.start()

    def _tick(self): self._phase = (self._phase + 0.03) % (math.pi * 2); self.update()

    def set(self, progress, text):
        self._progress = max(0.0, min(1.0, progress)); self._text = text; self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        s = self.width(); pw = 12; m = pw + 10
        cx = cy = s // 2
        rect = QRect(m, m, s - m * 2, s - m * 2)
        nc = QColor(self.neon)
        pa.setPen(QPen(QColor(255, 255, 255, 12), 1))
        for deg in range(0, 360, 6):
            rad = math.radians(deg)
            r_out = s // 2 - 4; r_in = s // 2 - (10 if deg % 30 == 0 else 7)
            x1 = cx + r_out * math.cos(rad); y1 = cy - r_out * math.sin(rad)
            x2 = cx + r_in  * math.cos(rad); y2 = cy - r_in  * math.sin(rad)
            if deg % 30 == 0:
                pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), 40), 1))
            else:
                pa.setPen(QPen(QColor(255, 255, 255, 12), 1))
            pa.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        pa.setPen(QPen(QColor(255, 255, 255, 14), pw, Qt.SolidLine, Qt.RoundCap))
        pa.drawArc(rect, 0, 360 * 16)
        span = int(-360 * 16 * self._progress)
        if span != 0:
            pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), 40), pw + 14, Qt.SolidLine, Qt.RoundCap))
            pa.drawArc(rect, 90 * 16, span)
            pa.setPen(QPen(nc, pw, Qt.SolidLine, Qt.RoundCap))
            pa.drawArc(rect, 90 * 16, span)
            tip_angle = math.radians(90 - 360 * self._progress)
            tip_r = s // 2 - m + pw // 2
            tx = cx + tip_r * math.cos(tip_angle)
            ty_ = cy - tip_r * math.sin(tip_angle)
            tip_grd = QRadialGradient(tx, ty_, pw)
            tip_grd.setColorAt(0, QColor(min(nc.red()+80,255), min(nc.green()+80,255), min(nc.blue()+80,255), 220))
            tip_grd.setColorAt(1, QColor(nc.red(), nc.green(), nc.blue(), 0))
            pa.setPen(Qt.NoPen); pa.setBrush(QBrush(tip_grd))
            pa.drawEllipse(QPointF(tx, ty_), float(pw), float(pw))
        inner_r = s // 2 - m - pw // 2 - 6
        inner = QPainterPath()
        inner.addEllipse(QPointF(cx, cy), inner_r, inner_r)
        pa.fillPath(inner, QColor(10, 12, 18, 200))
        pa.strokePath(inner, QPen(QColor(nc.red(), nc.green(), nc.blue(), 25), 1))
        pa.setPen(QColor(TEXT))
        pa.setFont(FM(20, True))
        pa.drawText(QRect(0, 0, s, s), Qt.AlignCenter, self._text)
        pa.end()


class CoinParticle:
    def __init__(self, cx, cy, color):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(3.5, 9.0)
        self.x = float(cx); self.y = float(cy)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(18, 32)
        self.max_life = self.life
        self.size = random.uniform(3, 7)
        self.color = color
        self.shape = random.choice(["circle", "star", "spark"])

    def step(self):
        self.x += self.vx; self.y += self.vy
        self.vy += 0.35; self.vx *= 0.94
        self.life -= 1

    def alive(self): return self.life > 0
    def alpha(self): return int(255 * (self.life / self.max_life))


from PySide6.QtCore import Signal

class CoinDisc(QWidget):
    result_landed = Signal()
    _IDLE   = "idle"; _SPIN   = "spin"; _REVEAL = "reveal"; _GLOW   = "glow"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self._side   = "?"
        self._neon   = GHOST
        self._accent = GHOST
        self._phase       = self._IDLE
        self._spin_angle  = 0.0
        self._spin_speed  = 0.0
        self._spin_frames = 0
        self._squash      = 1.0
        self._squash_v    = 0.0
        self._reveal_scale = 0.0
        self._reveal_frame = 0
        self._idle_t = 0.0
        self._idle_drift_x = 0.0
        self._idle_drift_y = 0.0
        self._particles: list = []
        self._glow_t = 0.0
        self._t = QTimer(self)
        self._t.setInterval(14)
        self._t.timeout.connect(self._step)
        self._t.start()

    def flip_to(self, side):
        self._side   = side
        key          = "flip" if side == "H" else "swap"
        self._neon   = NEON[key][0]
        self._accent = NEON[key][2]
        self._phase       = self._SPIN
        self._spin_frames = random.randint(6, 10)
        self._spin_speed  = random.uniform(80, 130)
        self._squash      = 1.0
        self._squash_v    = 0.0
        self._particles   = []
        self._reveal_frame = 0

    def _burst_particles(self):
        cx = self.width() // 2; cy = self.height() // 2
        nc = QColor(self._neon); ac = QColor(self._accent)
        for _ in range(28):
            c = nc if random.random() > 0.4 else ac
            self._particles.append(CoinParticle(cx, cy, c))

    def _step(self):
        if self._phase == self._SPIN:
            if random.random() < 0.18:
                self._spin_speed = random.uniform(18, 60)
            self._spin_angle  = (self._spin_angle + self._spin_speed) % 360
            self._spin_frames -= 1
            self._squash_v += (1.0 - self._squash) * 0.35
            self._squash_v *= 0.6
            self._squash += self._squash_v
            if self._spin_frames <= 0:
                self._phase        = self._REVEAL
                self._reveal_frame = 0
                self._spin_angle   = 0.0
                self._squash       = 1.0
                self._burst_particles()
                self.result_landed.emit()
        elif self._phase == self._REVEAL:
            self._reveal_frame += 1
            t = self._reveal_frame / 6.0
            if t < 0.5:
                self._reveal_scale = t * 2 * 1.55
            else:
                self._reveal_scale = 1.55 - (t - 0.5) * 2 * 0.55
            self._reveal_scale = max(0.05, min(2.0, self._reveal_scale))
            if self._reveal_frame >= 6:
                self._reveal_scale = 1.0
                self._phase        = self._GLOW
                self._glow_t       = 0.0
        elif self._phase == self._GLOW:
            self._glow_t += 0.07
        else:
            self._idle_t += 0.04
            self._idle_drift_x = math.sin(self._idle_t * 1.3) * 4
            self._idle_drift_y = math.sin(self._idle_t * 0.9) * 3
        self._particles = [p for p in self._particles if p.alive()]
        for p in self._particles:
            p.step()
        self.update()

    def paintEvent(self, ev):
        pa = QPainter(self)
        pa.setRenderHint(QPainter.Antialiasing)
        s  = self.width()
        cx = cy = s // 2
        r  = s // 2 - 14
        nc = QColor(self._neon)
        nr, ng, nb = nc.red(), nc.green(), nc.blue()
        for p in self._particles:
            a   = p.alpha()
            col = QColor(p.color.red(), p.color.green(), p.color.blue(), a)
            pa.setPen(Qt.NoPen)
            pa.setBrush(col)
            px, py, ps = int(p.x), int(p.y), p.size
            if p.shape == "circle":
                pa.drawEllipse(QPointF(px, py), ps * 0.5, ps * 0.5)
            elif p.shape == "star":
                pa.save()
                pa.translate(px, py)
                pa.rotate(p.life * 12)
                path = QPainterPath()
                for i in range(4):
                    ang = math.radians(i * 90)
                    path.lineTo(math.cos(ang) * ps, math.sin(ang) * ps)
                    ang2 = math.radians(i * 90 + 45)
                    path.lineTo(math.cos(ang2) * ps * 0.4, math.sin(ang2) * ps * 0.4)
                path.closeSubpath()
                pa.fillPath(path, col)
                pa.restore()
            else:
                pa.save()
                pa.translate(px, py)
                pa.rotate(math.degrees(math.atan2(p.vy, p.vx)))
                pen = QPen(col, 1.5)
                pa.setPen(pen); pa.setBrush(Qt.NoBrush)
                pa.drawLine(0, 0, int(ps * 2.5), 0)
                pa.restore()
        pa.save()
        pa.translate(cx, cy)
        if self._phase == self._SPIN:
            sx = abs(math.cos(math.radians(self._spin_angle))) * self._squash
            if sx < 0.05: sx = 0.05
            pa.scale(sx, self._squash * 0.98 + 0.02)
        elif self._phase == self._REVEAL:
            sc = self._reveal_scale
            pa.scale(sc, sc)
        elif self._phase == self._GLOW:
            breathe = 1.0 + math.sin(self._glow_t) * 0.025
            pa.scale(breathe, breathe)
        else:
            pa.translate(self._idle_drift_x, self._idle_drift_y)
        pa.translate(-cx, -cy)
        glow_r = r + 28
        if self._phase == self._GLOW:
            pulse = 0.5 + 0.5 * math.sin(self._glow_t * 1.8)
            glow_a = int(50 + pulse * 80)
        elif self._phase == self._REVEAL:
            glow_a = int(self._reveal_scale * 120)
        else:
            glow_a = 30
        halo = QRadialGradient(cx, cy, glow_r)
        halo.setColorAt(0.0, QColor(nr, ng, nb, 0))
        halo.setColorAt(0.55, QColor(nr, ng, nb, 0))
        halo.setColorAt(0.78, QColor(nr, ng, nb, glow_a))
        halo.setColorAt(1.0,  QColor(nr, ng, nb, 0))
        pa.setBrush(QBrush(halo)); pa.setPen(Qt.NoPen)
        pa.drawEllipse(cx - glow_r, cy - glow_r, glow_r * 2, glow_r * 2)
        disc = QPainterPath()
        disc.addEllipse(QPointF(cx, cy), float(r), float(r))
        pa.fillPath(disc, QColor(10, 12, 18, 250))
        ring_a = 70 if self._phase in (self._GLOW, self._REVEAL) else 35
        for rr, a in [(r - 7, ring_a), (r - 16, ring_a // 2)]:
            ring = QPainterPath()
            ring.addEllipse(QPointF(cx, cy), float(rr), float(rr))
            pa.strokePath(ring, QPen(QColor(nr, ng, nb, a), 1))
        border_w = 3.0 if self._phase == self._GLOW else 2.0
        pa.strokePath(disc, QPen(nc, border_w))
        pa.strokePath(disc, QPen(QColor(nr, ng, nb, 50), 12))
        sheen = QRadialGradient(cx, cy - r // 3, r // 2)
        sheen.setColorAt(0, QColor(255, 255, 255, 40))
        sheen.setColorAt(1, QColor(255, 255, 255, 0))
        pa.fillPath(disc, QBrush(sheen))
        if self._phase == self._SPIN:
            show = random.choice(["H", "T", "?", "?"])
            label_alpha = random.randint(80, 200)
        else:
            show = self._side
            label_alpha = 255
        lc = QColor(nr, ng, nb, label_alpha)
        pa.setFont(FM(68, True))
        pa.setPen(QColor(0, 0, 0, 130))
        pa.drawText(QRect(2, 2, s, s), Qt.AlignCenter, show)
        pa.setPen(lc)
        pa.drawText(QRect(0, 0, s, s), Qt.AlignCenter, show)
        pa.restore()
        pa.end()


class PageHeader(QWidget):
    def __init__(self, key, nav, parent=None):
        super().__init__(parent)
        self.setFixedHeight(62)
        neon = NEON[key][0]
        row = QHBoxLayout(self); row.setContentsMargins(10, 0, 0, 0); row.setSpacing(0)
        row.setAlignment(Qt.AlignVCenter)

        class _BackBtn(QWidget):
            def __init__(self, neon, nav_fn, parent=None):
                super().__init__(parent)
                self.setFixedSize(44, 44); self.setCursor(Qt.PointingHandCursor)
                self._neon = neon; self._nav = nav_fn; self._hover = False
            def enterEvent(self, e): self._hover = True;  self.update()
            def leaveEvent(self, e): self._hover = False; self.update()
            def mousePressEvent(self, e):
                if e.button() == Qt.LeftButton: self._nav()
            def paintEvent(self, ev):
                pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
                nc = QColor(self._neon)
                path = QPainterPath(); path.addRoundedRect(QRectF(1,1,42,42), 11, 11)
                pa.fillPath(path, QColor(nc.red(),nc.green(),nc.blue(), 30 if self._hover else 0))
                pa.fillPath(path, QColor(PANEL))
                pa.strokePath(path, QPen(QColor(nc.red(),nc.green(),nc.blue(), 200 if self._hover else 90), 1.5))
                pa.setPen(QPen(nc, 3.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                pa.setBrush(Qt.NoBrush)
                cx, cy = 19, 22; s = 7
                arrow = QPolygonF([QPointF(cx+s*0.6, cy-s), QPointF(cx-s*0.4, cy), QPointF(cx+s*0.6, cy+s)])
                pa.drawPolyline(arrow)
                pa.end()

        back = _BackBtn(neon, lambda: nav.go("home"))
        row.addWidget(back, 0, Qt.AlignVCenter); row.addSpacing(14)

        badge = QFrame(); badge.setFixedSize(42, 42)
        badge.setStyleSheet(f"""
            QFrame {{
                background: {NEON[key][3]};
                border: 1px solid {neon};
                border-radius: 10px;
            }}
        """)
        bl = QHBoxLayout(badge); bl.setContentsMargins(0, 0, 0, 0)
        ic = QLabel(ICONS[key]); ic.setFont(F(18, 700)); ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet(f"color:{neon};background:transparent;")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(16); eff.setColor(QColor(neon)); eff.setOffset(0,0)
        ic.setGraphicsEffect(eff); bl.addWidget(ic)
        row.addWidget(badge, 0, Qt.AlignVCenter); row.addSpacing(12)

        title = QLabel(NAMES[key])
        title.setFont(F(20, 700))
        title.setStyleSheet(f"color:{TEXT};background:transparent;")
        row.addWidget(title, 1, Qt.AlignVCenter)

        self._neon = neon

    def paintEvent(self, ev):
        super().paintEvent(ev)
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        nc = QColor(self._neon)
        grd = QLinearGradient(0, 0, self.width(), 0)
        grd.setColorAt(0.0, QColor(nc.red(), nc.green(), nc.blue(), 100))
        grd.setColorAt(0.5, QColor(nc.red(), nc.green(), nc.blue(), 40))
        grd.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.setPen(QPen(QBrush(grd), 1))
        pa.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        pa.end()


from PySide6.QtWidgets import QLineEdit

class StyledInput(QLineEdit):
    def __init__(self, text, neon):
        super().__init__(text)
        self.setFont(FM(17, True)); self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {PANEL};
                color: {TEXT};
                border: 1px solid {EDGE};
                border-radius: 10px;
                padding: 8px 12px;
            }}
            QLineEdit:focus {{ border: 1px solid {neon}; }}
        """)


def _build_stylesheet(p: dict) -> str:
    return f"""
* {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 11pt; }}
QWidget {{ background-color: {p['BG']}; color: {p['TEXT']}; }}
QMainWindow {{ background-color: {p['BG']}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{
    background: {p['SURFACE']}; width: 6px; border-radius: 3px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {p['EDGE']}; border-radius: 3px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
QTableWidget {{
    background: {p['SURFACE']}; gridline-color: {p['EDGE']};
    border: 1px solid {p['EDGE']}; border-radius: 8px; outline: none;
}}
QHeaderView::section {{
    background: {p['PANEL']}; color: {p['DIM']};
    border: none; border-bottom: 1px solid {p['EDGE']};
    padding: 6px; font-weight: bold; font-size: 9pt;
}}
QTableWidget::item {{ padding: 4px; border: none; }}
QTableWidget::item:selected {{ background: {p['EDGE']}; color: {p['TEXT']}; }}
QLineEdit {{
    background: {p['SURFACE']}; color: {p['TEXT']};
    border: 1px solid {p['EDGE']}; border-radius: 8px; padding: 0 10px;
}}
QLineEdit:focus {{ border: 1px solid #3b82f6; }}
QProgressBar {{
    border: 1px solid {p['EDGE']}; border-radius: 6px;
    background: {p['SURFACE']}; color: {p['TEXT']}; text-align: center;
}}
QProgressBar::chunk {{ border-radius: 5px; }}
"""

GLOBAL_STYLE = _build_stylesheet(_DARK_PALETTE)
DARK_STYLE   = GLOBAL_STYLE
LIGHT_STYLE  = _build_stylesheet(_LIGHT_PALETTE)


class _TimeBar(QWidget):
    def __init__(self, neon, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._neon = neon; self._progress = 1.0

    def set(self, v): self._progress = max(0.0, min(1.0, v)); self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); r = h // 2
        pa.setBrush(QColor(255, 255, 255, 18)); pa.setPen(Qt.NoPen)
        pa.drawRoundedRect(0, 0, w, h, r, r)
        fill_w = int(w * self._progress)
        if fill_w > 0:
            nc = QColor(self._neon); t = 1.0 - self._progress
            rc = min(255, int(nc.red()   + (255 - nc.red())   * min(1, t*2)))
            gc = max(0,   int(nc.green() * (1 - min(1, t*2))))
            bc = max(0,   int(nc.blue()  * (1 - min(1, t*2))))
            grd = QLinearGradient(0, 0, fill_w, 0)
            grd.setColorAt(0.0, QColor(nc.red(), nc.green(), nc.blue(), 220))
            grd.setColorAt(1.0, QColor(rc, gc, bc, 240))
            pa.setBrush(QBrush(grd))
            pa.drawRoundedRect(0, 0, fill_w, h, r, r)
        pa.end()


class _StatsBarChart(QWidget):
    ROW_H  = 50
    BAR_H  = 18
    PAD_L  = 82
    PAD_R  = 72
    PAD_T  = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list = []
        self._fills: list = []
        self._glow_t = 0.0
        self._t = QTimer(self); self._t.setInterval(14)
        self._t.timeout.connect(self._step)
        self.setMinimumHeight(40)

    def set_data(self, data):
        self._data  = data
        self._fills = [0.0] * len(data)
        self.setMinimumHeight(self.PAD_T + len(data) * self.ROW_H + 16)
        self._t.start()

    def _step(self):
        changed = False
        mx = max(v for _, v, _ in self._data) if self._data else 1
        for i, (_, v, _) in enumerate(self._data):
            target = (v / mx) if mx else 0
            diff = target - self._fills[i]
            if abs(diff) > 0.001:
                self._fills[i] += diff * 0.10
                changed = True
        self._glow_t += 0.05
        self.update()
        if not changed: self._t.stop()

    def paintEvent(self, ev):
        if not self._data: return
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        W  = self.width()
        bar_area = W - self.PAD_L - self.PAD_R
        mx_val = max(v for _, v, _ in self._data) or 1
        top_i = max(range(len(self._data)), key=lambda i: self._data[i][1])
        pulse = 0.5 + 0.5 * math.sin(self._glow_t)

        for i, (label, val, color) in enumerate(self._data):
            y  = self.PAD_T + i * self.ROW_H
            cy = y + self.ROW_H // 2
            by = cy - self.BAR_H // 2
            nc = QColor(color); r, g, b = nc.red(), nc.green(), nc.blue()
            is_top = (i == top_i and val > 0)

            lbl_color = QColor(TEXT) if is_top else QColor(DIM)
            pa.setFont(F(9, 700 if is_top else 400))
            pa.setPen(lbl_color)
            pa.drawText(QRect(0, by, self.PAD_L - 8, self.BAR_H),
                        Qt.AlignRight | Qt.AlignVCenter, label)

            track = QPainterPath()
            track.addRoundedRect(QRectF(self.PAD_L, by, bar_area, self.BAR_H), 5, 5)
            pa.fillPath(track, QColor(GHOST))

            fw = self._fills[i] * bar_area
            if fw > 2:
                fill = QPainterPath()
                fill.addRoundedRect(QRectF(self.PAD_L, by, fw, self.BAR_H), 5, 5)
                grad = QLinearGradient(self.PAD_L, 0, self.PAD_L + fw, 0)
                grad.setColorAt(0.0, QColor(r, g, b, 100))
                grad.setColorAt(0.6, QColor(r, g, b, 200))
                grad.setColorAt(1.0, QColor(r, g, b, 255))
                pa.fillPath(fill, QBrush(grad))
                pa.setPen(QPen(QColor(255,255,255,35), 1))
                pa.drawLine(QPointF(self.PAD_L + 4, by + 3),
                            QPointF(self.PAD_L + fw - 4, by + 3))
                glow_alpha = int(80 + 60 * pulse) if is_top else 55
                cap_x = self.PAD_L + fw
                for radius, alpha_mult in ((14, 0.6), (8, 1.0)):
                    grd = QRadialGradient(cap_x, cy, radius)
                    grd.setColorAt(0, QColor(r, g, b, int(glow_alpha * alpha_mult)))
                    grd.setColorAt(1, QColor(r, g, b, 0))
                    pa.fillRect(QRectF(cap_x - radius, cy - radius, radius*2, radius*2),
                                QBrush(grd))
                if is_top:
                    outer = QPen(QColor(r, g, b, int(60 + 50 * pulse)), 3)
                    pa.setPen(outer); pa.setBrush(Qt.NoBrush)
                    pa.drawRoundedRect(QRectF(self.PAD_L - 1, by - 1, fw + 2, self.BAR_H + 2), 6, 6)

            pa.setFont(FM(9, bold=True))
            alpha_val = 230 if val > 0 else 60
            pa.setPen(QColor(r, g, b, alpha_val))
            pa.drawText(QRect(int(self.PAD_L + bar_area + 6), by, self.PAD_R - 6, self.BAR_H),
                        Qt.AlignLeft | Qt.AlignVCenter, f"{val:,}")

            if is_top and val > 0:
                pa.setFont(F(10)); pa.setPen(QColor(255, 215, 0, int(180 + 60 * pulse)))
                pa.drawText(QRect(int(self.PAD_L + bar_area + 44), by - 2, 20, self.BAR_H + 4),
                            Qt.AlignCenter, "👑")
        pa.end()


def cap_lbl(text, color):
    lbl = QLabel(text.upper())
    lbl.setFont(F(8, 500))
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(f"color:{color};background:transparent;letter-spacing:2px;")
    return lbl
