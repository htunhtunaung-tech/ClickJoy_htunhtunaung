import sys, random, math
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSizePolicy, QScrollArea, QLineEdit, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import (
    Qt, QTimer, QElapsedTimer, QPoint, QPointF, QRect, QRectF, QSize, Signal
)
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QLinearGradient,
    QRadialGradient, QPainterPath, QPalette, QConicalGradient,
    QPolygonF
)
BG       = "#0e0f14"      # deep charcoal — not void black
SURFACE  = "#13151c"      # lifted surface
PANEL    = "#181b25"      # card background
EDGE     = "#22263a"      # structural edge lines
TEXT     = "#e8ecff"      # ice white
DIM      = "#5a637a"      # muted text
GHOST    = "#2a2e40"      # disabled / ghost

# Per-game neon palette: (neon, glow_dark, accent2, bg_tint)
NEON = {
    "normal": ("#3b82f6", "#1a3a7a", "#60a5fa", "#060c1a"),
    "flip":   ("#f59e0b", "#7a4a00", "#fcd34d", "#1a0f00"),
    "switch": ("#10b981", "#065a3a", "#34d399", "#001a0e"),
    "swap":   ("#ec4899", "#7a1040", "#f472b6", "#1a0010"),
    "cpt":    ("#8b5cf6", "#3d1a7a", "#a78bfa", "#0d0020"),
    "swc":    ("#06b6d4", "#034a60", "#67e8f9", "#001a20"),
    "popit":  ("#f97316", "#7c2d00", "#fb923c", "#1a0800"),
    "focus":  ("#e879f9", "#6b0080", "#f0abfc", "#1a0020"),
    "chaos":  ("#ff4d4d", "#7a0000", "#ff8080", "#1a0000"),
    "memory": ("#00e5ff", "#004a60", "#80f0ff", "#001a20"),
    "dopa":   ("#39ff14", "#0a4000", "#80ff60", "#001200"),
    "rcs":    ("#2EB62C", "#303050", "#c0d0ff", "#080810"),
}

SUBTITLES = {
    "normal": "tap as fast as you can",
    "flip":   "heads or tails?",
    "switch": "toggle the switch",
    "swap":   "chase the target",
    "cpt":    "race the clock",
    "swc":    "hit the exact time",
    "popit":  "pop every bubble fast!",
    "focus":  "click only the right shape",
    "chaos":  "find the real button!",
    "memory": "remember the pattern",
    "dopa":   "stay controlled, fill the meter",
    "rcs":    "match the color — react fast!",
}

# Geometric symbol icons (render as text)
ICONS = {
    "normal": "⬡", "flip": "◆", "switch": "▣",
    "swap":   "◎", "cpt":  "◷", "swc":    "◉", "popit": "⬤",
    "focus": "◈",
    "chaos": "⚡",
    "memory": "◫",
    "dopa":   "◑",
    "rcs":    "◐",
}

NAMES = {
    "normal": "Normal Click",
    "flip":   "Flip Coin",
    "switch": "Switch",
    "swap":   "Swap Click",
    "cpt":    "Click per Time",
    "swc":    "Stopwatch Callout",
    "popit":  "Pop It",
    "focus":  "Focus Burst",
    "chaos":  "Chaos Control",
    "memory": "Memory Flash",
    "dopa":   "Dopamine Meter",
    "rcs":    "Color Shift",
}


# ══════════════════════════════════════════════════════════════
#  FONT SYSTEM  — mono for numbers, geometric for labels
# ══════════════════════════════════════════════════════════════
def F(size=14, weight=400):
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
    """Monospaced — for numbers and timers"""
    f = QFont()
    for name in ("Consolas", "Courier New", "monospace"):
        f.setFamily(name); break
    f.setPointSize(size)
    f.setBold(bold)
    return f


# ══════════════════════════════════════════════════════════════
#  SHARED STATE
# ══════════════════════════════════════════════════════════════
class G:
    normal = 0; flip = 0; switch = 0; swap = 0; popit = 0
    cpt_cps = 0.0; swc_best = float("inf")
    flip_streak = 0; flip_side = ""
    flip_best_h = 0; flip_best_t = 0
    switch_on = False
    focus_best = 0
    chaos_best = 0
    memory_best = 0
    dopa_best   = 0
    rcs_best    = 0


# ══════════════════════════════════════════════════════════════
#  BACKGROUND: GRID + SCANLINES + NEON ORBS
# ══════════════════════════════════════════════════════════════
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

        # ── Base fill ─────────────────────────────────────────
        pa.fillRect(0, 0, w, h, QColor(BG))

        # ── Dot grid ──────────────────────────────────────────
        dot_c = QColor(255, 255, 255, 10)
        step = 28
        pa.setPen(Qt.NoPen)
        pa.setBrush(dot_c)
        for gx in range(0, w + step, step):
            for gy in range(0, h + step, step):
                pa.drawEllipse(gx - 1, gy - 1, 2, 2)

        # ── Animated neon orb ──────────────────────────────────
        nc = QColor(gd)
        ox = int(w * (0.65 + 0.18 * math.sin(self._phase * 0.6)))
        oy = int(h * (0.30 + 0.14 * math.cos(self._phase * 0.4)))
        orb_r = int(min(w, h) * 0.55)
        orb = QRadialGradient(ox, oy, orb_r)
        orb.setColorAt(0.0, QColor(nc.red(), nc.green(), nc.blue(), 90))
        orb.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.setBrush(QBrush(orb)); pa.setPen(Qt.NoPen)
        pa.drawEllipse(ox - orb_r, oy - orb_r, orb_r * 2, orb_r * 2)

        # Second smaller orb (bottom left, counter-phase)
        nc2 = QColor(neon)
        ox2 = int(w * (0.20 + 0.10 * math.cos(self._phase * 0.7 + 1.0)))
        oy2 = int(h * (0.75 + 0.12 * math.sin(self._phase * 0.5 + 0.5)))
        r2 = int(min(w, h) * 0.35)
        orb2 = QRadialGradient(ox2, oy2, r2)
        orb2.setColorAt(0.0, QColor(nc2.red(), nc2.green(), nc2.blue(), 50))
        orb2.setColorAt(1.0, QColor(nc2.red(), nc2.green(), nc2.blue(), 0))
        pa.setBrush(QBrush(orb2))
        pa.drawEllipse(ox2 - r2, oy2 - r2, r2 * 2, r2 * 2)

        # ── Scanline overlay ───────────────────────────────────
        sl = QColor(0, 0, 0, 18)
        for y in range(0, h, 3):
            pa.fillRect(0, y, w, 1, sl)

        pa.end()


# ══════════════════════════════════════════════════════════════
#  NEON PANEL CARD  (sharp left edge, rounded right)
# ══════════════════════════════════════════════════════════════
class NeonPanel(QWidget):
    """Card with left neon accent bar + frosted dark body."""
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

        # Main body — full rounded rect
        body = QPainterPath()
        body.addRoundedRect(QRectF(bar, 0, w - bar, h), self._r, self._r)
        pa.fillPath(body, QColor(24, 27, 37, 230))

        # Top-edge highlight
        hi = QLinearGradient(0, 0, 0, 20)
        hi.setColorAt(0, QColor(255, 255, 255, 22))
        hi.setColorAt(1, QColor(255, 255, 255, 0))
        pa.strokePath(body, QPen(QBrush(hi), 1))

        # Left neon accent bar
        nc = QColor(self._neon)
        bar_path = QPainterPath()
        bar_path.addRoundedRect(QRectF(0, h * 0.15, bar, h * 0.70), bar // 2, bar // 2)
        pa.fillPath(bar_path, nc)

        # Bar glow
        glow = QRadialGradient(bar // 2, h // 2, h * 0.4)
        glow.setColorAt(0.0, QColor(nc.red(), nc.green(), nc.blue(), 55))
        glow.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.setBrush(QBrush(glow)); pa.setPen(Qt.NoPen)
        pa.drawRect(0, 0, 60, h)

        pa.end()


# ══════════════════════════════════════════════════════════════
#  ANIMATED CORNER BRACKET  (decorative HUD element)
# ══════════════════════════════════════════════════════════════
class CornerBrackets(QWidget):
    """Draws animated corner brackets that pulse with neon color."""
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

        # Top-left
        pa.drawLine(0, sz, 0, 0); pa.drawLine(0, 0, sz, 0)
        # Top-right
        pa.drawLine(w - sz, 0, w, 0); pa.drawLine(w, 0, w, sz)
        # Bottom-left
        pa.drawLine(0, h - sz, 0, h); pa.drawLine(0, h, sz, h)
        # Bottom-right
        pa.drawLine(w - sz, h, w, h); pa.drawLine(w, h, w, h - sz)
        pa.end()


# ══════════════════════════════════════════════════════════════
#  NEON SCORE LABEL  (big engraved-looking number)
# ══════════════════════════════════════════════════════════════
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

        # Shadow layer (offset = depth illusion)
        pa.setPen(QColor(0, 0, 0, 120))
        pa.setFont(FM(self._size, True))
        pa.drawText(QRect(3, 3, w, h), Qt.AlignCenter, self._text)

        # Glow layer
        glow_eff = QGraphicsDropShadowEffect()
        # (can't do per-paint glow, so we draw a blurred copy manually)
        nc_soft = QColor(nc.red(), nc.green(), nc.blue(), 60)
        pa.setPen(nc_soft)
        for offset in [(-2,0),(2,0),(0,-2),(0,2),(-1,-1),(1,1)]:
            pa.drawText(QRect(offset[0], offset[1], w, h), Qt.AlignCenter, self._text)

        # Main text
        pa.setPen(nc)
        pa.setFont(FM(self._size, True))
        pa.drawText(QRect(0, 0, w, h), Qt.AlignCenter, self._text)
        pa.end()


# ══════════════════════════════════════════════════════════════
#  GLOW LABEL  (for section caps / headers)
# ══════════════════════════════════════════════════════════════
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


# ══════════════════════════════════════════════════════════════
#  STAT CHIP  (HUD data display)
# ══════════════════════════════════════════════════════════════
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
        # Dark fill
        path = QPainterPath()
        path.addRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 10, 10)
        pa.fillPath(path, QColor(18, 20, 30, 220))
        # Neon border
        pa.strokePath(path, QPen(QColor(nc.red(), nc.green(), nc.blue(), 80), 1))
        # Top highlight
        hi = QLinearGradient(0, 0, 0, 10)
        hi.setColorAt(0, QColor(nc.red(), nc.green(), nc.blue(), 40))
        hi.setColorAt(1, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.fillPath(path, QBrush(hi))
        pa.end()


# ══════════════════════════════════════════════════════════════
#  THE BIG TAP BUTTON
# ══════════════════════════════════════════════════════════════
class NeonTapButton(QWidget):
    clicked = None

    def __init__(self, label, neon, accent, size=200, parent=None):
        super().__init__(parent)
        self.label = label; self.neon = neon; self.accent = accent
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self._press  = 0.0
        self._ripple = 0.0
        self._pulse  = 0.0   # idle breathing
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
        br = w // 2 - 6   # button radius

        # ── Outer pulse halo ─────────────────────────────────
        pulse_alpha = int(30 + 25 * math.sin(self._pulse)) + (20 if self._hover else 0)
        halo = QRadialGradient(cx, cy, br + 30)
        halo.setColorAt(0.6, QColor(nc.red(), nc.green(), nc.blue(), 0))
        halo.setColorAt(0.80, QColor(nc.red(), nc.green(), nc.blue(), pulse_alpha))
        halo.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.setBrush(QBrush(halo)); pa.setPen(Qt.NoPen)
        pa.drawEllipse(cx - br - 30, cy - br - 30, (br + 30) * 2, (br + 30) * 2)

        # ── Expanding ripple ring ────────────────────────────
        if self._ripple > 0:
            rr = int(br + (1 - self._ripple) * 55)
            rpen_c = QColor(nc.red(), nc.green(), nc.blue(), int(self._ripple * 180))
            pa.setPen(QPen(rpen_c, 2)); pa.setBrush(Qt.NoBrush)
            pa.drawEllipse(cx - rr, cy - rr, rr * 2, rr * 2)
            rr2 = int(br + (1 - self._ripple) * 80)
            rpen_c2 = QColor(nc.red(), nc.green(), nc.blue(), int(self._ripple * 80))
            pa.setPen(QPen(rpen_c2, 1))
            pa.drawEllipse(cx - rr2, cy - rr2, rr2 * 2, rr2 * 2)

        # ── Button disc ──────────────────────────────────────
        pressed_r = int(br - self._press * 10)
        disc = QPainterPath()
        disc.addEllipse(QPointF(cx, cy), float(pressed_r), float(pressed_r))

        # Dark base
        pa.fillPath(disc, QColor(14, 16, 24, 245))

        # Neon ring border (double — main + glow)
        pa.strokePath(disc, QPen(QColor(nc.red(), nc.green(), nc.blue(), 40), 12))
        pa.strokePath(disc, QPen(nc, 2))

        # Inner radial — subtle colored center
        inner = QRadialGradient(cx, cy - pressed_r // 4, pressed_r // 2)
        inner.setColorAt(0.0, QColor(nc.red(), nc.green(), nc.blue(), 30 + int(20 * self._press)))
        inner.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.fillPath(disc, QBrush(inner))

        # ── Label ─────────────────────────────────────────────
        # Shadow
        pa.setPen(QColor(0, 0, 0, 160))
        pa.setFont(F(w // 5, 700))
        pa.drawText(QRect(2, 2, w, w), Qt.AlignCenter, self.label)
        # Main
        pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), 240))
        pa.drawText(QRect(0, 0, w, w), Qt.AlignCenter, self.label)

        pa.end()


# ══════════════════════════════════════════════════════════════
#  PARTICLE SYSTEM
# ══════════════════════════════════════════════════════════════
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
            else:  # diamond
                pts = QPolygonF([
                    QPointF(s.x, s.y - sz), QPointF(s.x + sz, s.y),
                    QPointF(s.x, s.y + sz), QPointF(s.x - sz, s.y)
                ])
                pa.drawPolygon(pts)
        pa.end()


# ══════════════════════════════════════════════════════════════
#  NEON TOGGLE  (inspired by industrial switches)
# ══════════════════════════════════════════════════════════════
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

        # Track dark fill
        track = QPainterPath()
        track.addRoundedRect(QRectF(0, ty, tw, th), tr, tr)
        pa.fillPath(track, QColor(12, 14, 20, 240))

        # Track neon fill when ON
        if self._pos > 0:
            nf = QPainterPath()
            filled_w = tr + (tw - tr * 2) * self._pos
            nf.addRoundedRect(QRectF(0, ty, filled_w + tr, th), tr, tr)
            fill_c = QColor(nc.red(), nc.green(), nc.blue(), int(160 * self._pos))
            pa.fillPath(nf, fill_c)

        # Track border
        pa.strokePath(track, QPen(QColor(nc.red(), nc.green(), nc.blue(),
                                         int(60 + 120 * self._pos)), 1.5))

        # Tick marks
        pa.setPen(QPen(QColor(255, 255, 255, 25), 1))
        for tx in range(tr + 10, tw - tr - 10, 12):
            pa.drawLine(tx, ty + 8, tx, ty + th - 8)

        # Thumb
        left_cx = float(tr); right_cx = float(tw - tr)
        cx = left_cx + self._pos * (right_cx - left_cx)
        cy = float(h // 2)
        thr = self.TD // 2

        # Thumb shadow
        pa.setPen(Qt.NoPen)
        pa.setBrush(QColor(0, 0, 0, 80))
        pa.drawEllipse(QPointF(cx + 1, cy + 2), float(thr), float(thr))

        # Thumb body
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

        # Thumb neon glow ring when ON
        if self._pos > 0.4:
            glow_a = int(140 * self._pos)
            pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), glow_a), 3))
            pa.setBrush(Qt.NoBrush)
            pa.drawEllipse(QPointF(cx, cy), float(thr + 4), float(thr + 4))

        pa.strokePath(thumb, QPen(QColor(255, 255, 255, 80), 1))
        pa.end()


# ══════════════════════════════════════════════════════════════
#  NEON RING  (countdown / progress)
# ══════════════════════════════════════════════════════════════
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

        # Outer decorative ring (static tick marks)
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

        # Track
        pa.setPen(QPen(QColor(255, 255, 255, 14), pw, Qt.SolidLine, Qt.RoundCap))
        pa.drawArc(rect, 0, 360 * 16)

        # Active arc
        span = int(-360 * 16 * self._progress)
        if span != 0:
            # Glow pass
            pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), 40), pw + 14, Qt.SolidLine, Qt.RoundCap))
            pa.drawArc(rect, 90 * 16, span)
            # Main arc
            pa.setPen(QPen(nc, pw, Qt.SolidLine, Qt.RoundCap))
            pa.drawArc(rect, 90 * 16, span)
            # Bright tip at arc end
            tip_angle = math.radians(90 - 360 * self._progress)
            tip_r = s // 2 - m + pw // 2
            tx = cx + tip_r * math.cos(tip_angle)
            ty_ = cy - tip_r * math.sin(tip_angle)
            tip_grd = QRadialGradient(tx, ty_, pw)
            tip_grd.setColorAt(0, QColor(min(nc.red()+80,255), min(nc.green()+80,255), min(nc.blue()+80,255), 220))
            tip_grd.setColorAt(1, QColor(nc.red(), nc.green(), nc.blue(), 0))
            pa.setPen(Qt.NoPen); pa.setBrush(QBrush(tip_grd))
            pa.drawEllipse(QPointF(tx, ty_), float(pw), float(pw))

        # Inner dark disc
        inner_r = s // 2 - m - pw // 2 - 6
        inner = QPainterPath()
        inner.addEllipse(QPointF(cx, cy), inner_r, inner_r)
        pa.fillPath(inner, QColor(10, 12, 18, 200))
        pa.strokePath(inner, QPen(QColor(nc.red(), nc.green(), nc.blue(), 25), 1))

        # Center text
        pa.setPen(QColor(TEXT))
        pa.setFont(FM(20, True))
        pa.drawText(QRect(0, 0, s, s), Qt.AlignCenter, self._text)
        pa.end()


# ══════════════════════════════════════════════════════════════
#  COIN DISC
# ══════════════════════════════════════════════════════════════
class CoinParticle:
    """Single particle for the burst effect on reveal."""
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
        self.vy += 0.35          # gravity
        self.vx *= 0.94          # drag
        self.life -= 1

    def alive(self): return self.life > 0

    def alpha(self): return int(255 * (self.life / self.max_life))


class CoinDisc(QWidget):
    # Signals for screen-shake: emit when result lands
    result_landed = Signal()

    # Phase constants
    _IDLE   = "idle"
    _SPIN   = "spin"
    _REVEAL = "reveal"
    _GLOW   = "glow"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self._side   = "?"
        self._neon   = GHOST
        self._accent = GHOST

        # Spin state
        self._phase       = self._IDLE
        self._spin_angle  = 0.0      # current visual rotation (degrees)
        self._spin_speed  = 0.0      # deg/frame – chaotically varying
        self._spin_frames = 0        # frames left in spin
        self._squash      = 1.0      # x-scale for squash/stretch
        self._squash_v    = 0.0

        # Reveal burst
        self._reveal_scale = 0.0     # punches from 0→1.4→1.0
        self._reveal_frame = 0

        # Idle hypnotic float
        self._idle_t = 0.0
        self._idle_drift_x = 0.0
        self._idle_drift_y = 0.0

        # Particles
        self._particles: list[CoinParticle] = []

        # Glow pulse after reveal
        self._glow_t = 0.0

        self._t = QTimer(self)
        self._t.setInterval(14)
        self._t.timeout.connect(self._step)
        self._t.start()              # always running for idle

    def flip_to(self, side):
        self._side   = side
        key          = "flip" if side == "H" else "swap"
        self._neon   = NEON[key][0]
        self._accent = NEON[key][2]
        # Chaotic spin: random duration (25-45 frames) and speed bursts
        self._phase       = self._SPIN
        self._spin_frames = random.randint(22, 42)
        self._spin_speed  = random.uniform(28, 55)   # fast kick
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
            # Chaotic speed: randomly jitter mid-spin
            if random.random() < 0.18:
                self._spin_speed = random.uniform(18, 60)
            self._spin_angle  = (self._spin_angle + self._spin_speed) % 360
            self._spin_frames -= 1
            # Squash oscillation
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
            # Punch scale: 0 → 1.55 → 1.0 over ~18 frames
            t = self._reveal_frame / 18.0
            if t < 0.5:
                self._reveal_scale = t * 2 * 1.55
            else:
                self._reveal_scale = 1.55 - (t - 0.5) * 2 * 0.55
            self._reveal_scale = max(0.05, min(2.0, self._reveal_scale))
            if self._reveal_frame >= 18:
                self._reveal_scale = 1.0
                self._phase        = self._GLOW
                self._glow_t       = 0.0

        elif self._phase == self._GLOW:
            self._glow_t += 0.07
            # Hypnotic pulse – never stops

        else:  # IDLE
            self._idle_t += 0.04
            self._idle_drift_x = math.sin(self._idle_t * 1.3) * 4
            self._idle_drift_y = math.sin(self._idle_t * 0.9) * 3

        # Particles always tick
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

        # ── Particles (drawn first, behind coin) ──────────────────
        for p in self._particles:
            a   = p.alpha()
            col = QColor(p.color.red(), p.color.green(), p.color.blue(), a)
            pa.setPen(Qt.NoPen)
            pa.setBrush(col)
            px, py, ps = int(p.x), int(p.y), p.size
            if p.shape == "circle":
                pa.drawEllipse(QPointF(px, py), ps * 0.5, ps * 0.5)
            elif p.shape == "star":
                # Simple 4-point star
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
            else:  # spark – thin line
                pa.save()
                pa.translate(px, py)
                pa.rotate(math.degrees(math.atan2(p.vy, p.vx)))
                pen = QPen(col, 1.5)
                pa.setPen(pen); pa.setBrush(Qt.NoBrush)
                pa.drawLine(0, 0, int(ps * 2.5), 0)
                pa.restore()

        # ── Determine transform ────────────────────────────────────
        pa.save()
        pa.translate(cx, cy)

        if self._phase == self._SPIN:
            # Chaotic wobble: horizontal squeeze simulates tumbling
            sx = abs(math.cos(math.radians(self._spin_angle))) * self._squash
            if sx < 0.05: sx = 0.05
            pa.scale(sx, self._squash * 0.98 + 0.02)
        elif self._phase == self._REVEAL:
            sc = self._reveal_scale
            pa.scale(sc, sc)
        elif self._phase == self._GLOW:
            # Subtle hypnotic breathe
            breathe = 1.0 + math.sin(self._glow_t) * 0.025
            pa.scale(breathe, breathe)
        else:  # IDLE float
            pa.translate(self._idle_drift_x, self._idle_drift_y)

        pa.translate(-cx, -cy)

        # ── Outer glow halo ───────────────────────────────────────
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

        # ── Disc fill ─────────────────────────────────────────────
        disc = QPainterPath()
        disc.addEllipse(QPointF(cx, cy), float(r), float(r))
        pa.fillPath(disc, QColor(10, 12, 18, 250))

        # ── Inner rings ───────────────────────────────────────────
        ring_a = 70 if self._phase in (self._GLOW, self._REVEAL) else 35
        for rr, a in [(r - 7, ring_a), (r - 16, ring_a // 2)]:
            ring = QPainterPath()
            ring.addEllipse(QPointF(cx, cy), float(rr), float(rr))
            pa.strokePath(ring, QPen(QColor(nr, ng, nb, a), 1))

        # ── Neon border ───────────────────────────────────────────
        border_w = 3.0 if self._phase == self._GLOW else 2.0
        pa.strokePath(disc, QPen(nc, border_w))
        pa.strokePath(disc, QPen(QColor(nr, ng, nb, 50), 12))

        # ── Sheen ─────────────────────────────────────────────────
        sheen = QRadialGradient(cx, cy - r // 3, r // 2)
        sheen.setColorAt(0, QColor(255, 255, 255, 40))
        sheen.setColorAt(1, QColor(255, 255, 255, 0))
        pa.fillPath(disc, QBrush(sheen))

        # ── Label (H / T / ?) ────────────────────────────────────
        if self._phase == self._SPIN:
            # During spin show rapid random flicker
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


# ══════════════════════════════════════════════════════════════
#  PAGE HEADER
# ══════════════════════════════════════════════════════════════
class PageHeader(QWidget):
    def __init__(self, key, nav, parent=None):
        super().__init__(parent)
        self.setFixedHeight(62)
        neon = NEON[key][0]
        row = QHBoxLayout(self); row.setContentsMargins(0, 0, 0, 0); row.setSpacing(0)

        back = QPushButton("‹")
        back.setFont(F(26, 700)); back.setFixedSize(48, 48); back.setCursor(Qt.PointingHandCursor)
        back.setStyleSheet(f"""
            QPushButton {{
                background: {PANEL};
                color: {neon};
                border: 1px solid {EDGE};
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background: {SURFACE};
                border-color: {neon};
            }}
        """)
        back.clicked.connect(lambda: nav.go("home")); row.addWidget(back); row.addSpacing(14)

        # Icon badge
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
        row.addWidget(badge); row.addSpacing(12)

        title = QLabel(NAMES[key])
        title.setFont(F(20, 700))
        title.setStyleSheet(f"color:{TEXT};background:transparent;")
        row.addWidget(title, 1)

        # Neon line at bottom
        self._neon = neon

    def paintEvent(self, ev):
        super().paintEvent(ev)
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        nc = QColor(self._neon)
        # Bottom separator line with fade
        grd = QLinearGradient(0, 0, self.width(), 0)
        grd.setColorAt(0.0, QColor(nc.red(), nc.green(), nc.blue(), 100))
        grd.setColorAt(0.5, QColor(nc.red(), nc.green(), nc.blue(), 40))
        grd.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.setPen(QPen(QBrush(grd), 1))
        pa.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        pa.end()


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


# ══════════════════════════════════════════════════════════════
#  HOME PAGE
# ══════════════════════════════════════════════════════════════
class HomeCard(QWidget):
    def __init__(self, key, nav, parent=None):
        super().__init__(parent)
        self.key = key; self.nav = nav
        self._neon = NEON[key][0]; self._acc = NEON[key][2]
        self.setFixedHeight(80); self.setCursor(Qt.PointingHandCursor)
        self._hover = 0.0
        self._ht = QTimer(self); self._ht.setInterval(16); self._ht.timeout.connect(self._hanim)
        self._target = 0.0

        row = QHBoxLayout(self); row.setContentsMargins(16, 0, 16, 0); row.setSpacing(0)

        # Left: neon icon box
        icon_box = QFrame(); icon_box.setFixedSize(44, 44)
        icon_box.setStyleSheet(f"""
            QFrame {{
                background: {NEON[key][3]};
                border: 1px solid {NEON[key][0]};
                border-radius: 10px;
            }}
        """)
        il = QHBoxLayout(icon_box); il.setContentsMargins(0,0,0,0)
        ic = QLabel(ICONS[key]); ic.setFont(F(20, 700)); ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet(f"color:{self._neon};background:transparent;")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(18)
        eff.setColor(QColor(self._neon)); eff.setOffset(0, 0); ic.setGraphicsEffect(eff)
        il.addWidget(ic); row.addWidget(icon_box); row.addSpacing(14)

        col = QVBoxLayout(); col.setSpacing(2)
        nm = QLabel(NAMES[key]); nm.setFont(F(14, 700))
        nm.setStyleSheet(f"color:{TEXT};background:transparent;")
        sb = QLabel(SUBTITLES[key]); sb.setFont(F(10, 400))
        sb.setStyleSheet(f"color:{DIM};background:transparent;")
        col.addWidget(nm); col.addWidget(sb); row.addLayout(col, 1)

        self._arr = QLabel("›"); self._arr.setFont(F(22, 700))
        self._arr.setStyleSheet(f"color:{self._neon};background:transparent;")
        row.addWidget(self._arr)

    def enterEvent(self, e): self._target = 1.0; self._ht.start()
    def leaveEvent(self, e): self._target = 0.0; self._ht.start()
    def _hanim(self):
        self._hover += (self._target - self._hover) * 0.25
        if abs(self._hover - self._target) < 0.01: self._hover = self._target; self._ht.stop()
        self.update()
    def mousePressEvent(self, e): self.nav.go(self.key)

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        nc = QColor(self._neon)
        bar = 4

        # Body
        body = QPainterPath()
        body.addRoundedRect(QRectF(bar, 1, w - bar - 1, h - 2), 12, 12)
        base_a = int(180 + 40 * self._hover)
        pa.fillPath(body, QColor(20, 23, 34, base_a))

        # Hover color wash from left
        if self._hover > 0.01:
            wash = QLinearGradient(bar, 0, w * 0.55, 0)
            wash.setColorAt(0, QColor(nc.red(), nc.green(), nc.blue(), int(35 * self._hover)))
            wash.setColorAt(1, QColor(nc.red(), nc.green(), nc.blue(), 0))
            pa.fillPath(body, QBrush(wash))

        # Border
        border_a = int(40 + 120 * self._hover)
        pa.strokePath(body, QPen(QColor(nc.red(), nc.green(), nc.blue(), border_a), 1))

        # Left neon bar
        bar_path = QPainterPath()
        bar_path.addRoundedRect(QRectF(0, h * 0.2, bar, h * 0.6), 2, 2)
        bar_nc = QColor(nc.red(), nc.green(), nc.blue(), int(100 + 155 * self._hover))
        pa.fillPath(bar_path, bar_nc)
        pa.end()
        super().paintEvent(ev)


class HomePage(QWidget):
    def __init__(self, nav):
        super().__init__(); self.nav = nav; self._build()

    def _build(self):
        self.bg = NeonBackground("normal", self)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 40, 22, 24); root.setSpacing(0)

        # ── Brand header ─────────────────────────────────────
        hdr = QHBoxLayout()
        brand_col = QVBoxLayout(); brand_col.setSpacing(0)
        brand = QLabel("CLICKJOY")
        brand.setFont(F(30, 900))
        brand.setStyleSheet(f"color:{TEXT};background:transparent;letter-spacing:5px;")
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(20); eff.setColor(QColor(NEON["normal"][0])); eff.setOffset(0, 0)
        brand.setGraphicsEffect(eff)
        tagline = QLabel("▸  beat your record")
        tagline.setFont(F(10, 500))
        tagline.setStyleSheet(f"color:{NEON['normal'][0]};background:transparent;letter-spacing:2px;")
        brand_col.addWidget(brand); brand_col.addWidget(tagline)
        hdr.addLayout(brand_col, 1)

        rb = QPushButton("🏆"); rb.setFont(F(18)); rb.setFixedSize(50, 50)
        rb.setCursor(Qt.PointingHandCursor)
        rb.setStyleSheet(f"""
            QPushButton {{
                background:{PANEL}; border:1px solid {EDGE};
                border-radius:14px; color:white;
            }}
            QPushButton:hover {{
                background:{SURFACE}; border-color:{NEON["flip"][0]};
            }}
        """)
        rb.clicked.connect(lambda: self.nav.go("ranking")); hdr.addWidget(rb)
        root.addLayout(hdr); root.addSpacing(22)

        # ── Stats banner ─────────────────────────────────────
        banner = QWidget(); banner.setFixedHeight(90)
        banner.setAttribute(Qt.WA_TranslucentBackground)
        bl = QHBoxLayout(banner); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(12)

        self.total_chip = self._stat_banner_chip("TOTAL CLICKS", "0", NEON["normal"][0])
        self.cps_chip   = self._stat_banner_chip("BEST CPS",     "—", NEON["cpt"][0])
        bl.addWidget(self.total_chip); bl.addWidget(self.cps_chip)
        root.addWidget(banner); root.addSpacing(18)

        # ── Game grid ────────────────────────────────────────
        keys = list(NAMES.keys())
        for i in range(0, len(keys), 2):
            row = QHBoxLayout(); row.setSpacing(12)
            for j in range(2):
                if i + j < len(keys):
                    row.addWidget(HomeCard(keys[i + j], self.nav))
                else:
                    row.addStretch()
            root.addLayout(row); root.addSpacing(10)

        root.addStretch()

    def _stat_banner_chip(self, label, value, neon):
        """Large stat banner card."""
        w = QWidget(); w.setAttribute(Qt.WA_TranslucentBackground)
        w._neon = neon
        lay = QVBoxLayout(w); lay.setContentsMargins(18, 14, 18, 14); lay.setSpacing(2)
        cap = QLabel(label); cap.setFont(F(9, 500))
        cap.setStyleSheet(f"color:{DIM};background:transparent;letter-spacing:2px;")
        val = QLabel(value); val.setFont(FM(28, True))
        val.setStyleSheet(f"color:{neon};background:transparent;")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(22)
        eff.setColor(QColor(neon)); eff.setOffset(0, 0); val.setGraphicsEffect(eff)
        lay.addWidget(cap); lay.addWidget(val)
        w._val_lbl = val

        # Custom paint
        def paint(ev, widget=w):
            pa = QPainter(widget); pa.setRenderHint(QPainter.Antialiasing)
            nc = QColor(widget._neon)
            ww, wh = widget.width(), widget.height()
            path = QPainterPath()
            path.addRoundedRect(QRectF(0.5, 0.5, ww - 1, wh - 1), 14, 14)
            pa.fillPath(path, QColor(18, 21, 32, 220))
            pa.strokePath(path, QPen(QColor(nc.red(), nc.green(), nc.blue(), 70), 1))
            hi = QLinearGradient(0, 0, 0, 20)
            hi.setColorAt(0, QColor(nc.red(), nc.green(), nc.blue(), 35))
            hi.setColorAt(1, QColor(nc.red(), nc.green(), nc.blue(), 0))
            pa.fillPath(path, QBrush(hi))
            pa.end()
        w.paintEvent = paint
        return w

    def resizeEvent(self, e):
        self.bg.setGeometry(0, 0, self.width(), self.height()); super().resizeEvent(e)

    def showEvent(self, e):
        total = G.normal + G.flip + G.switch + G.swap
        self.total_chip._val_lbl.setText(f"{total:,}")
        self.cps_chip._val_lbl.setText(f"{G.cpt_cps:.2f}" if G.cpt_cps > 0 else "—")
        super().showEvent(e)


# ══════════════════════════════════════════════════════════════
#  BASE PAGE
# ══════════════════════════════════════════════════════════════
class BasePage(QWidget):
    KEY = "normal"
    def __init__(self, nav):
        super().__init__(); self.nav = nav
        self.neon   = NEON[self.KEY][0]
        self.accent = NEON[self.KEY][2]
        self._setup()

    def _setup(self):
        self.bg = NeonBackground(self.KEY, self)
        self.bg.setGeometry(0, 0, 500, 900)
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(22, 16, 22, 22); self.root.setSpacing(0)
        self.root.addWidget(PageHeader(self.KEY, self.nav))
        self.root.addSpacing(18)
        self._build_content()

    def _build_content(self): pass

    def resizeEvent(self, e):
        self.bg.setGeometry(0, 0, self.width(), self.height()); super().resizeEvent(e)

    def _ghost_btn(self, txt):
        b = QPushButton(txt); b.setFont(F(11, 500)); b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton {{
                background:{PANEL}; color:{DIM};
                border:1px solid {EDGE}; border-radius:10px; padding:8px 30px;
            }}
            QPushButton:hover {{
                color:{TEXT}; background:{SURFACE}; border-color:{self.neon};
            }}
        """); return b


# ══════════════════════════════════════════════════════════════
#  CAP LABEL  (section header)
# ══════════════════════════════════════════════════════════════
def cap_lbl(text, neon=None):
    l = QLabel(text.upper()); l.setFont(F(8, 500))
    l.setAlignment(Qt.AlignCenter)
    color = neon if neon else DIM
    l.setStyleSheet(f"color:{color};background:transparent;letter-spacing:3px;")
    return l


# ══════════════════════════════════════════════════════════════
#  NORMAL CLICK
# ══════════════════════════════════════════════════════════════
class NormalClickPage(BasePage):
    KEY = "normal"
    def _build_content(self):
        self._session = 0
        root = self.root

        self.score = GlowLabel("0", self.neon, 68, mono=True)
        root.addWidget(self.score, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("total clicks", self.neon))
        root.addSpacing(32)

        ctr = QWidget(); ctr.setFixedSize(260, 260); ctr.setStyleSheet("background:transparent;")
        self.btn = NeonTapButton("TAP", self.neon, self.accent, 230, ctr)
        self.btn.move(15, 15); self.btn.clicked = self._tap
        self.parts = Particles(ctr); self.parts.setGeometry(0, 0, 260, 260)
        # Corner brackets overlay
        self.brackets = CornerBrackets(self.neon, 20, 2, ctr)
        self.brackets.setGeometry(0, 0, 260, 260)
        root.addWidget(ctr, 0, Qt.AlignCenter)
        root.addStretch()

        row = QHBoxLayout(); row.setSpacing(12)
        self.sess_c = StatChip("session", "0",  self.neon)
        self.best_c = StatChip("all time", f"{G.normal:,}", self.neon)
        row.addWidget(self.sess_c); row.addWidget(self.best_c)
        root.addLayout(row)

    def _tap(self):
        G.normal += 1; self._session += 1
        self.score.set(f"{G.normal:,}")
        self.sess_c.set(f"{self._session:,}")
        self.best_c.set(f"{G.normal:,}")
        self.parts.burst(130, 130, self.neon, 18)

    def showEvent(self, e):
        self.score.set(f"{G.normal:,}"); self.best_c.set(f"{G.normal:,}"); super().showEvent(e)


# ══════════════════════════════════════════════════════════════
#  FLIP COIN
# ══════════════════════════════════════════════════════════════
class ResultBanner(QWidget):
    """Big flashy result label that punches in and fades."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._text  = ""
        self._color = QColor(GHOST)
        self._alpha = 0.0
        self._scale = 1.0
        self._frame = 0
        self._active = False
        self._t = QTimer(self); self._t.setInterval(14); self._t.timeout.connect(self._step)

    def show_result(self, text, color):
        self._text   = text
        self._color  = QColor(color)
        self._frame  = 0
        self._active = True
        self._t.start()

    def _step(self):
        self._frame += 1
        t = self._frame
        if t < 12:                       # punch in
            self._scale = 0.5 + (t / 12) * 0.9
            self._alpha = t / 12
        elif t < 38:                     # hold
            self._scale = 1.0 + math.sin((t - 12) / 26 * math.pi) * 0.06
            self._alpha = 1.0
        elif t < 55:                     # fade out
            self._alpha = 1.0 - (t - 38) / 17
            self._scale = 1.0
        else:
            self._active = False
            self._alpha  = 0.0
            self._t.stop()
        self.update()

    def paintEvent(self, ev):
        if self._alpha <= 0: return
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        nc = self._color; a = int(self._alpha * 255)
        pa.save()
        pa.translate(cx, cy); pa.scale(self._scale, self._scale); pa.translate(-cx, -cy)
        # Dynamic font & pill size: shrink when streak text is long
        has_streak = "×" in self._text
        font_size  = 22 if has_streak else 42
        pill_w     = 210 if has_streak else 180
        pill_h     = 52  if has_streak else 64
        # Glow bg pill
        pill = QPainterPath()
        pill.addRoundedRect(QRectF(cx - pill_w // 2, cy - pill_h // 2, pill_w, pill_h), 18, 18)
        pa.fillPath(pill, QColor(nc.red(), nc.green(), nc.blue(), int(a * 0.22)))
        pa.strokePath(pill, QPen(QColor(nc.red(), nc.green(), nc.blue(), int(a * 0.7)), 2))
        # Main text
        pa.setFont(FM(font_size, True))
        pa.setPen(QColor(0, 0, 0, int(a * 0.5)))
        pa.drawText(QRect(2, 2, w, h), Qt.AlignCenter, self._text)
        pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), a))
        pa.drawText(QRect(0, 0, w, h), Qt.AlignCenter, self._text)
        pa.restore(); pa.end()


class StreakBadge(QWidget):
    """Animated streak counter that pulses on combos."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(110, 70)
        self._streak = 0
        self._pulse  = 0.0
        self._t = QTimer(self); self._t.setInterval(14); self._t.timeout.connect(self._step)
        self._t.start()

    def set_streak(self, n, color):
        self._streak = n
        self._neon   = QColor(color)
        self._pulse  = 1.4 if n > 1 else 0.0
        self.update()

    def _step(self):
        if self._pulse > 0:
            self._pulse = max(0.0, self._pulse - 0.06)
            self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        if not hasattr(self, "_neon"): self._neon = QColor(GHOST)
        nc = self._neon; w, h = self.width(), self.height()
        sc = 1.0 + self._pulse * 0.12
        cx, cy = w // 2, h // 2
        pa.translate(cx, cy); pa.scale(sc, sc); pa.translate(-cx, -cy)
        path = QPainterPath(); path.addRoundedRect(QRectF(1, 1, w - 2, h - 2), 12, 12)
        pa.fillPath(path, QColor(nc.red(), nc.green(), nc.blue(), 28))
        pa.strokePath(path, QPen(QColor(nc.red(), nc.green(), nc.blue(), 120), 1.5))
        pa.setFont(FM(22, True)); pa.setPen(nc)
        pa.drawText(QRect(0, 0, w, h - 18), Qt.AlignCenter, f"×{self._streak}")
        pa.setFont(F(8, 500)); pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), 160))
        pa.drawText(QRect(0, h - 22, w, 20), Qt.AlignCenter, "STREAK")
        pa.end()


class FlipCoinPage(BasePage):
    KEY = "flip"

    def _build_content(self):
        root = self.root

        # ── Top stat row ─────────────────────────────────────────
        top = QHBoxLayout(); top.setSpacing(10)
        self.flips_c = StatChip("flips", "0", self.neon)
        self.side_c  = StatChip("last",  "—", self.neon)
        top.addWidget(self.flips_c); top.addWidget(self.side_c)
        root.addLayout(top); root.addSpacing(18)

        # ── Coin + overlaid banner in a stacked container ────────
        coin_wrap = QWidget(); coin_wrap.setFixedSize(220, 220)
        coin_wrap.setStyleSheet("background:transparent;")
        self.coin = CoinDisc(coin_wrap)
        self.coin.result_landed.connect(self._on_landed)
        self.banner = ResultBanner(coin_wrap)
        self.banner.setGeometry(0, 0, 220, 220)
        root.addWidget(coin_wrap, 0, Qt.AlignCenter); root.addSpacing(10)

        # ── Streak badge ─────────────────────────────────────────
        self.streak_badge = StreakBadge()
        self.streak_badge.set_streak(0, self.neon)
        root.addWidget(self.streak_badge, 0, Qt.AlignCenter)
        root.addSpacing(14)

        # ── FLIP button ──────────────────────────────────────────
        nc = QColor(self.neon); r, g, b = nc.red(), nc.green(), nc.blue()
        nc2 = QColor(self.accent)
        self.fbtn = QPushButton("◆  FLIP"); self.fbtn.setFont(F(17, 700))
        self.fbtn.setFixedWidth(240); self.fbtn.setFixedHeight(58)
        self.fbtn.setCursor(Qt.PointingHandCursor)
        self.fbtn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 rgba({r},{g},{b},200),
                    stop:1 rgba({nc2.red()},{nc2.green()},{nc2.blue()},200));
                color:{TEXT}; border:none; border-radius:16px; letter-spacing:3px;
            }}
            QPushButton:hover  {{ background:rgba({r},{g},{b},255); }}
            QPushButton:pressed {{ background:rgba({r//2},{g//2},{b//2},240);
                                   padding-top:3px; }}
        """)
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(32)
        eff.setColor(QColor(self.neon)); eff.setOffset(0, 5)
        self.fbtn.setGraphicsEffect(eff)
        self.fbtn.clicked.connect(self._flip)
        root.addWidget(self.fbtn, 0, Qt.AlignCenter); root.addStretch()

        # ── Best scores ──────────────────────────────────────────
        bot = QHBoxLayout(); bot.setSpacing(10)
        self.bh = StatChip("best H streak", "0", NEON["flip"][0])
        self.bt = StatChip("best T streak", "0", NEON["swap"][0])
        bot.addWidget(self.bh); bot.addWidget(self.bt)
        root.addLayout(bot)

        # ── Screen-shake state ───────────────────────────────────
        self._shake_frames = 0
        self._shake_t = QTimer(self)
        self._shake_t.setInterval(14)
        self._shake_t.timeout.connect(self._do_shake)

        self._last_result = None

    def _flip(self):
        result = random.choice(["H", "T"]); G.flip += 1
        if result == G.flip_side: G.flip_streak += 1
        else: G.flip_streak = 1; G.flip_side = result
        if result == "H": G.flip_best_h = max(G.flip_best_h, G.flip_streak)
        else:             G.flip_best_t = max(G.flip_best_t, G.flip_streak)
        self._last_result = result
        self.coin.flip_to(result)
        self.flips_c.set(G.flip); self.side_c.set(result)
        self.bh.set(G.flip_best_h); self.bt.set(G.flip_best_t)

    def _on_landed(self):
        """Called when coin reveal punch hits — show banner, shake, update streak."""
        result = self._last_result
        if result is None: return
        color  = NEON["flip"][0] if result == "H" else NEON["swap"][0]
        label  = "HEADS!" if result == "H" else "TAILS!"
        if G.flip_streak >= 3:
            label = f"{label}  🔥×{G.flip_streak}"
        self.banner.show_result(label, color)
        self.streak_badge.set_streak(G.flip_streak, color)
        # Shake intensity scales with streak
        self._shake_frames = min(6 + G.flip_streak * 2, 18)
        self._shake_t.start()

    def _do_shake(self):
        if self._shake_frames <= 0:
            self._shake_t.stop()
            # Restore position
            self.move(self.x() - self.x() % 1, self.y() - self.y() % 1)
            return
        intensity = min(self._shake_frames, 8)
        dx = random.randint(-intensity, intensity)
        dy = random.randint(-intensity // 2, intensity // 2)
        self.move(self.x() + dx, self.y() + dy)
        self._shake_frames -= 1


# ══════════════════════════════════════════════════════════════
#  SWITCH
# ══════════════════════════════════════════════════════════════
class SwitchPage(BasePage):
    KEY = "switch"
    def _build_content(self):
        self._on_ct = 0; self._off_ct = 0
        root = self.root
        self.score = GlowLabel("0", self.neon, 58, mono=True)
        root.addWidget(self.score, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("toggles", self.neon))
        root.addStretch()

        # Toggle + brackets
        tog_ctr = QWidget(); tog_ctr.setFixedSize(200, 90)
        tog_ctr.setStyleSheet("background:transparent;")
        self.toggle = NeonToggle(self.neon, self.accent, tog_ctr)
        self.toggle.move(20, 16); self.toggle.toggled = self._toggled
        brk = CornerBrackets(self.neon, 16, 2, tog_ctr)
        brk.setGeometry(0, 0, 200, 90)
        root.addWidget(tog_ctr, 0, Qt.AlignCenter); root.addSpacing(20)

        self.state_lbl = GlowLabel("OFF", GHOST, 46, mono=True)
        root.addWidget(self.state_lbl)
        root.addStretch()

        bot = QHBoxLayout(); bot.setSpacing(10)
        self.on_c  = StatChip("times on",  "0", self.neon)
        self.off_c = StatChip("times off", "0", DIM)
        bot.addWidget(self.on_c); bot.addWidget(self.off_c); root.addLayout(bot)

    def _toggled(self):
        G.switch_on = self.toggle._on; G.switch += 1
        if G.switch_on: self._on_ct += 1; self.on_c.set(self._on_ct)
        else:           self._off_ct += 1; self.off_c.set(self._off_ct)
        self.score.set(f"{G.switch:,}")
        if G.switch_on:
            self.state_lbl.setText("ON")
            self.state_lbl.setStyleSheet(f"color:{self.neon};background:transparent;")
            eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(35)
            eff.setColor(QColor(self.neon)); eff.setOffset(0, 0); self.state_lbl.setGraphicsEffect(eff)
        else:
            self.state_lbl.setText("OFF")
            self.state_lbl.setStyleSheet(f"color:{GHOST};background:transparent;")
            self.state_lbl.setGraphicsEffect(None)

    def showEvent(self, e):
        self.score.set(f"{G.switch:,}"); self.toggle.set_state(G.switch_on)
        if G.switch_on:
            self.state_lbl.setText("ON")
            self.state_lbl.setStyleSheet(f"color:{self.neon};background:transparent;")
        else:
            self.state_lbl.setText("OFF")
            self.state_lbl.setStyleSheet(f"color:{GHOST};background:transparent;")
        super().showEvent(e)


# ══════════════════════════════════════════════════════════════
#  SWAP CLICK
# ══════════════════════════════════════════════════════════════
class SwapClickPage(BasePage):
    KEY = "swap"
    def _build_content(self):
        root = self.root
        self.score = GlowLabel("0", self.neon, 52, mono=True)
        root.addWidget(self.score, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("hits", self.neon)); root.addSpacing(8)

        self.zone = QWidget(); self.zone.setMinimumHeight(360)
        self.zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.zone.setStyleSheet("background:transparent;")
        self.parts   = Particles(self.zone); self.parts.setGeometry(0, 0, 600, 600)
        self.swap_btn = NeonTapButton("◎", self.neon, self.accent, 74, self.zone)
        self.swap_btn.move(140, 150); self.swap_btn.clicked = self._hit

        # Zone HUD border
        self._zone_neon = self.neon
        self.zone.paintEvent = self._zone_paint
        root.addWidget(self.zone, 1); root.addSpacing(8)

        hint = QLabel("◈  chase the target before it escapes")
        hint.setFont(F(10, 500)); hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"color:{DIM};background:transparent;letter-spacing:1px;")
        root.addWidget(hint)

    def _zone_paint(self, ev):
        pa = QPainter(self.zone); pa.setRenderHint(QPainter.Antialiasing)
        nc = QColor(self._zone_neon)
        w, h = self.zone.width(), self.zone.height()
        path = QPainterPath()
        path.addRoundedRect(QRectF(1, 1, w - 2, h - 2), 16, 16)
        pa.fillPath(path, QColor(10, 12, 18, 80))
        pa.strokePath(path, QPen(QColor(nc.red(), nc.green(), nc.blue(), 35), 1))
        # corner accents
        sz = 16
        pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), 80), 2))
        pa.drawLine(2, sz, 2, 2); pa.drawLine(2, 2, sz, 2)
        pa.drawLine(w - sz, 2, w - 2, 2); pa.drawLine(w - 2, 2, w - 2, sz)
        pa.drawLine(2, h - sz, 2, h - 2); pa.drawLine(2, h - 2, sz, h - 2)
        pa.drawLine(w - sz, h - 2, w - 2, h - 2); pa.drawLine(w - 2, h - sz, w - 2, h - 2)
        pa.end()

    def _hit(self):
        G.swap += 1; self.score.set(f"{G.swap:,}")
        w = max(20, self.zone.width() - 84); h = max(20, self.zone.height() - 84)
        ox = self.swap_btn.x() + 37; oy = self.swap_btn.y() + 37
        self.parts.setGeometry(0, 0, self.zone.width(), self.zone.height())
        self.parts.burst(ox, oy, self.neon, 20)
        self.swap_btn.move(random.randint(8, w), random.randint(8, h))

    def showEvent(self, e): self.score.set(f"{G.swap:,}"); super().showEvent(e)


# ══════════════════════════════════════════════════════════════
#  CLICK PER TIME
# ══════════════════════════════════════════════════════════════
class ClickPerTimePage(BasePage):
    KEY = "cpt"
    def _build_content(self):
        self._clicks = 0; self._running = False; self._finished = False
        self._elapsed = QElapsedTimer()
        self._ticker  = QTimer(self); self._ticker.setInterval(16)
        self._ticker.timeout.connect(self._tick)
        root = self.root

        dur_row = QHBoxLayout()
        dl = QLabel("Duration"); dl.setFont(F(12, 500))
        dl.setStyleSheet(f"color:{DIM};background:transparent;")
        dur_row.addWidget(dl); dur_row.addStretch()
        self.t_input = StyledInput("60", self.neon); self.t_input.setFixedWidth(88)
        self.t_input.textChanged.connect(self._sync_ring)
        dur_row.addWidget(self.t_input)
        sl = QLabel("s"); sl.setFont(F(12, 400))
        sl.setStyleSheet(f"color:{DIM};background:transparent;")
        dur_row.addSpacing(6); dur_row.addWidget(sl)
        root.addLayout(dur_row); root.addSpacing(14)

        self.ring = NeonRing(self.neon, self.accent, 190)
        root.addWidget(self.ring, 0, Qt.AlignCenter); self._sync_ring()
        root.addSpacing(4)

        self.clicks_lbl = GlowLabel("0", self.neon, 40, mono=True)
        root.addWidget(self.clicks_lbl, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("clicks", self.neon))
        root.addSpacing(14)

        ctr = QWidget(); ctr.setFixedSize(160, 160); ctr.setStyleSheet("background:transparent;")
        self.tap_btn = NeonTapButton("TAP", self.neon, self.accent, 140, ctr)
        self.tap_btn.move(10, 10); self.tap_btn.clicked = self._on_click
        self.parts = Particles(ctr); self.parts.setGeometry(0, 0, 160, 160)
        root.addWidget(ctr, 0, Qt.AlignCenter); root.addStretch()

        stats = QHBoxLayout(); stats.setSpacing(10)
        self.cps_c  = StatChip("cps",      "—",   self.neon)
        self.best_c = StatChip("best cps", f"{G.cpt_cps:.2f}", self.neon)
        stats.addWidget(self.cps_c); stats.addWidget(self.best_c)
        root.addLayout(stats); root.addSpacing(10)
        rst = self._ghost_btn("◀  RESET"); rst.clicked.connect(self._reset)
        root.addWidget(rst, 0, Qt.AlignCenter)

    def _target(self):
        try: return max(1.0, float(self.t_input.text()))
        except: return 60.0

    def _sync_ring(self):
        if not self._running and not self._finished:
            self.ring.set(1.0, f"{self._target():.0f}s")

    def _on_click(self):
        if self._finished: return
        if not self._running:
            self._running = True; self._clicks = 0; self._elapsed.start()
            self._ticker.start(); self.t_input.setEnabled(False)
        self._clicks += 1; self.clicks_lbl.set(str(self._clicks))
        self.parts.burst(80, 80, self.neon, 12)

    def _tick(self):
        t = self._target(); el = self._elapsed.elapsed() / 1000.0
        rem = max(0.0, t - el); self.ring.set(rem / t, f"{rem:.2f}")
        if rem <= 0: self._finish(el)

    def _finish(self, el):
        self._ticker.stop(); self._running = False; self._finished = True
        self.ring.set(0.0, "DONE"); self.tap_btn.setEnabled(False)
        cps = self._clicks / el if el > 0 else 0.0
        self.cps_c.set(f"{cps:.2f}")
        if cps > G.cpt_cps: G.cpt_cps = cps; self.best_c.set(f"{cps:.2f}")

    def _reset(self):
        self._ticker.stop(); self._running = self._finished = False
        self._clicks = 0; self.clicks_lbl.set("0"); self.cps_c.set("—")
        self.tap_btn.setEnabled(True); self.t_input.setEnabled(True); self._sync_ring()

    def showEvent(self, e):
        if not self._running and not self._finished: self._sync_ring()
        self.best_c.set(f"{G.cpt_cps:.2f}"); super().showEvent(e)


# ══════════════════════════════════════════════════════════════
#  STOPWATCH CALLOUT
# ══════════════════════════════════════════════════════════════
class StopwatchCalloutPage(BasePage):
    KEY = "swc"
    def _build_content(self):
        self._running = False; self._elapsed = QElapsedTimer()
        self._ticker = QTimer(self); self._ticker.setInterval(16)
        self._ticker.timeout.connect(self._tick)
        root = self.root

        tr_row = QHBoxLayout()
        tl = QLabel("Target time"); tl.setFont(F(12, 500))
        tl.setStyleSheet(f"color:{DIM};background:transparent;")
        tr_row.addWidget(tl); tr_row.addStretch()
        self.t_input = StyledInput("3", self.neon); self.t_input.setFixedWidth(88)
        tr_row.addWidget(self.t_input)
        sl = QLabel("s"); sl.setFont(F(12, 400))
        sl.setStyleSheet(f"color:{DIM};background:transparent;")
        tr_row.addSpacing(6); tr_row.addWidget(sl)
        root.addLayout(tr_row); root.addSpacing(28)

        self.live_lbl = GlowLabel("0.00", self.neon, 70, mono=True)
        root.addWidget(self.live_lbl, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("seconds", self.neon)); root.addSpacing(28)

        self.ss_btn = QPushButton("▶  START"); self.ss_btn.setFont(F(16, 700))
        self.ss_btn.setFixedWidth(240); self.ss_btn.setFixedHeight(56)
        self.ss_btn.setCursor(Qt.PointingHandCursor); self.ss_btn.clicked.connect(self._toggle)
        self._style_ss(False); root.addWidget(self.ss_btn, 0, Qt.AlignCenter); root.addSpacing(28)

        self.excess_lbl = GlowLabel("—", DIM, 42, mono=True)
        root.addWidget(self.excess_lbl, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("excess time")); root.addStretch()

        bot = QHBoxLayout(); bot.setSpacing(10)
        self.tgt_c  = StatChip("target", "3.0 s", DIM)
        self.best_c = StatChip("best",   "—",     self.neon)
        bot.addWidget(self.tgt_c); bot.addWidget(self.best_c); root.addLayout(bot)
        root.addSpacing(10)
        rst = self._ghost_btn("◀  RESET"); rst.clicked.connect(self._reset)
        root.addWidget(rst, 0, Qt.AlignCenter)

    def _style_ss(self, running):
        nc = QColor(self.neon); r, g, b = nc.red(), nc.green(), nc.blue()
        nc2 = QColor(self.accent); r2, g2, b2 = nc2.red(), nc2.green(), nc2.blue()
        self.ss_btn.setText("■  STOP" if running else "▶  START")
        if running:
            self.ss_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba({r//2},{g//2},{b//2},220);
                    color:{TEXT}; border:1px solid rgba({r},{g},{b},120); border-radius:14px;
                }}
                QPushButton:hover {{ background: rgba({r},{g},{b},200); }}
            """)
        else:
            self.ss_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 rgba({r},{g},{b},200), stop:1 rgba({r2},{g2},{b2},200));
                    color:{TEXT}; border:none; border-radius:14px;
                }}
                QPushButton:hover {{ background:rgba({r},{g},{b},255); }}
                QPushButton:pressed {{ background:rgba({r//2},{g//2},{b//2},255); }}
            """)
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(24 if not running else 8)
        eff.setColor(QColor(self.neon)); eff.setOffset(0, 3); self.ss_btn.setGraphicsEffect(eff)

    def _target(self):
        try: return max(0.1, float(self.t_input.text()))
        except: return 3.0

    def _toggle(self):
        if not self._running:
            self._running = True; self._elapsed.start(); self._ticker.start()
            self._style_ss(True); self.t_input.setEnabled(False)
            self.excess_lbl.setText("—")
            self.excess_lbl.setStyleSheet(f"color:{DIM};background:transparent;")
            self.excess_lbl.setGraphicsEffect(None)
        else:
            el = self._elapsed.elapsed() / 1000.0; self._ticker.stop()
            self._running = False; self._style_ss(False)
            self.live_lbl.set(f"{el:.2f}"); self.t_input.setEnabled(True)
            target = self._target(); excess = el - target; ae = abs(excess)
            sign = "+" if excess >= 0 else "-"
            if   ae <= 0.15: color = NEON["swc"][0]
            elif ae <= 0.60: color = NEON["cpt"][0]
            elif ae <= 1.50: color = NEON["flip"][0]
            else:            color = NEON["swap"][0]
            self.excess_lbl.setText(f"{sign}{ae:.2f}s")
            self.excess_lbl.setStyleSheet(f"color:{color};background:transparent;")
            eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(28)
            eff.setColor(QColor(color)); eff.setOffset(0, 0); self.excess_lbl.setGraphicsEffect(eff)
            if ae < abs(G.swc_best): G.swc_best = excess
            be = G.swc_best; bs = "+" if be >= 0 else "-"
            self.best_c.set(f"{bs}{abs(be):.2f}s"); self.tgt_c.set(f"{target:.1f} s")

    def _tick(self):
        self.live_lbl.set(f"{self._elapsed.elapsed() / 1000.0:.2f}")

    def _reset(self):
        self._ticker.stop(); self._running = False; self._style_ss(False)
        self.live_lbl.set("0.00"); self.excess_lbl.setText("—")
        self.excess_lbl.setStyleSheet(f"color:{DIM};background:transparent;")
        self.excess_lbl.setGraphicsEffect(None); self.t_input.setEnabled(True)


# ══════════════════════════════════════════════════════════════
#  RANKING PAGE
# ══════════════════════════════════════════════════════════════
class RankingPage(QWidget):
    def __init__(self, nav):
        super().__init__(); self.nav = nav
        self.bg = NeonBackground("flip", self); self._build()

    def resizeEvent(self, e):
        self.bg.setGeometry(0, 0, self.width(), self.height()); super().resizeEvent(e)

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(22, 26, 22, 22); root.setSpacing(0)
        hdr = QHBoxLayout()
        back = QPushButton("‹"); back.setFont(F(26, 700))
        back.setFixedSize(48, 48); back.setCursor(Qt.PointingHandCursor)
        back.setStyleSheet(f"""
            QPushButton {{
                background:{PANEL}; color:{TEXT};
                border:1px solid {EDGE}; border-radius:12px;
            }}
            QPushButton:hover {{
                background:{SURFACE}; border-color:{NEON["flip"][0]};
            }}
        """)
        back.clicked.connect(lambda: self.nav.go("home")); hdr.addWidget(back); hdr.addSpacing(14)
        tl = QLabel("RANKINGS"); tl.setFont(F(20, 900))
        tl.setStyleSheet(f"color:{TEXT};background:transparent;letter-spacing:4px;")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(18)
        eff.setColor(QColor(NEON["flip"][0])); eff.setOffset(0, 0); tl.setGraphicsEffect(eff)
        hdr.addWidget(tl, 1)
        root.addLayout(hdr); root.addSpacing(20)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.inner = QWidget(); self.inner.setStyleSheet("background:transparent;")
        self.il = QVBoxLayout(self.inner)
        self.il.setContentsMargins(0, 0, 0, 0); self.il.setSpacing(10)
        scroll.setWidget(self.inner); root.addWidget(scroll, 1)

    def _entries(self):
        def info(k):
            if k == "cpt":
                return f"{G.cpt_cps:.2f} CPS", G.cpt_cps
            if k == "swc":
                if G.swc_best == float("inf"):
                    return "No attempt", 0.0
                s = "+" if G.swc_best >= 0 else "-"
                return f"{s}{abs(G.swc_best):.2f}s", abs(G.swc_best)
            if k == "focus":
                return f"Best {G.focus_best} combo", float(G.focus_best)
            if k == "chaos":
                return f"Best {G.chaos_best} hits", float(G.chaos_best)
            if k == "memory":
                return f"Best {G.memory_best} rounds", float(G.memory_best)
            if k == "dopa":
                return f"Peak {G.dopa_best}%", float(G.dopa_best)
            if k == "rcs":
                return f"Best {G.rcs_best} pts", float(G.rcs_best)
            v = {
                "normal": G.normal,
                "flip":   G.flip,
                "switch": G.switch,
                "swap":   G.swap,
                "popit":  G.popit,
            }[k]
            return f"{v:,}", float(v)

        rows = [(k, *info(k)) for k in NAMES]
        rows.sort(key=lambda x: x[2], reverse=True)
        return rows

    def _refresh(self):
        while self.il.count():
            it = self.il.takeAt(0)
            if it.widget(): it.widget().deleteLater()

        medals = ["🥇", "🥈", "🥉"]
        for i, (key, display, _) in enumerate(self._entries()):
            neon = NEON[key][0]; accent = NEON[key][2]
            nc = QColor(neon); r, g, b = nc.red(), nc.green(), nc.blue()

            card = NeonPanel(neon, radius=12, bar=4)
            card.setFixedHeight(74)
            if i < 3:
                eff = QGraphicsDropShadowEffect()
                eff.setBlurRadius(18); eff.setColor(QColor(neon)); eff.setOffset(0, 2)
                card.setGraphicsEffect(eff)

            row = QHBoxLayout(card); row.setContentsMargins(20, 0, 16, 0); row.setSpacing(0)

            # Rank
            if i < 3:
                rl = QLabel(medals[i]); rl.setFont(F(24, 700))
            else:
                rl = QLabel(f"#{i+1}"); rl.setFont(FM(14, True))
                rl.setStyleSheet(f"color:{neon};background:transparent;")
            rl.setFixedWidth(50); rl.setAlignment(Qt.AlignCenter)
            rl.setStyleSheet(f"color:{neon};background:transparent;")
            row.addWidget(rl); row.addSpacing(8)

            # Icon badge
            badge = QFrame(); badge.setFixedSize(38, 38)
            badge.setStyleSheet(f"""
                QFrame {{
                    background: {NEON[key][3]};
                    border: 1px solid rgba({r},{g},{b},100);
                    border-radius: 9px;
                }}
            """)
            bl = QHBoxLayout(badge); bl.setContentsMargins(0, 0, 0, 0)
            ic = QLabel(ICONS[key]); ic.setFont(F(16, 700)); ic.setAlignment(Qt.AlignCenter)
            ic.setStyleSheet(f"color:{neon};background:transparent;")
            ie = QGraphicsDropShadowEffect(); ie.setBlurRadius(12)
            ie.setColor(QColor(neon)); ie.setOffset(0, 0); ic.setGraphicsEffect(ie)
            bl.addWidget(ic); row.addWidget(badge); row.addSpacing(12)

            # Name + score
            col = QVBoxLayout(); col.setSpacing(2)
            nm = QLabel(NAMES[key]); nm.setFont(F(14, 700))
            nm.setStyleSheet(f"color:{TEXT};background:transparent;")
            sc = QLabel(display); sc.setFont(FM(11, True))
            sc.setStyleSheet(f"color:{neon};background:transparent;")
            col.addWidget(nm); col.addWidget(sc); row.addLayout(col, 1)

            # Go button
            go = QPushButton("›"); go.setFont(F(20, 700))
            go.setFixedSize(34, 34); go.setCursor(Qt.PointingHandCursor)
            go.setStyleSheet(f"""
                QPushButton {{
                    background: rgba({r},{g},{b},28);
                    color:{neon}; border:1px solid rgba({r},{g},{b},60);
                    border-radius: 9px;
                }}
                QPushButton:hover {{ background: rgba({r},{g},{b},70); }}
            """)
            go.clicked.connect(lambda _, k=key: self.nav.go(k)); row.addWidget(go)
            self.il.addWidget(card)

        self.il.addStretch()

    def showEvent(self, e): self._refresh(); super().showEvent(e)



# ══════════════════════════════════════════════════════════════
#  POP IT
# ══════════════════════════════════════════════════════════════
class BubbleWidget(QWidget):
    """A single pop-it bubble — custom painted, animates on pop."""
    def __init__(self, row, col, neon, accent, parent=None):
        super().__init__(parent)
        self.row = row; self.col = col
        self.neon = neon; self.accent = accent
        self.setFixedSize(58, 58)
        self.setCursor(Qt.PointingHandCursor)
        self._popped  = False
        self._pop_anim = 0.0   # 0→1 pop squish animation
        self._hover   = False
        self._t = QTimer(self); self._t.setInterval(16)
        self._t.timeout.connect(self._tick)
        self.on_popped = None  # callback

    def reset(self):
        self._popped = False; self._pop_anim = 0.0
        self._t.stop(); self.update()

    def _tick(self):
        self._pop_anim = min(1.0, self._pop_anim + 0.10)
        self.update()
        if self._pop_anim >= 1.0: self._t.stop()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and not self._popped:
            self._popped = True; self._pop_anim = 0.0; self._t.start()
            if self.on_popped: self.on_popped()

    def enterEvent(self, e): self._hover = True;  self.update()
    def leaveEvent(self, e): self._hover = False; self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w = h = self.width(); cx = cy = w // 2
        nc = QColor(self.neon); ac = QColor(self.accent)

        if self._popped:
            # Sunken flat disc
            t = self._pop_anim
            radius = int(20 - 6 * t)
            depth  = int(4 * t)
            # Outer ring
            pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), int(160 - 100*t)), 2))
            pa.setBrush(QColor(10, 12, 20, 180))
            pa.drawEllipse(cx - 22, cy - 22, 44, 44)
            # Inner sunken circle
            inner = QPainterPath()
            inner.addEllipse(QPointF(cx, cy + depth), float(radius), float(radius))
            pa.fillPath(inner, QColor(6, 8, 14, 220))
            pa.strokePath(inner, QPen(QColor(nc.red(), nc.green(), nc.blue(),
                                             int(80 - 50*t)), 1))
            # Center dot
            pa.setPen(Qt.NoPen)
            pa.setBrush(QColor(nc.red(), nc.green(), nc.blue(), int(60 - 40*t)))
            pa.drawEllipse(QPointF(cx, cy + depth + 1), 4.0, 4.0)
        else:
            # Raised bubble
            hover_boost = 8 if self._hover else 0
            outer_r = 24 + hover_boost // 3

            # Outer glow ring
            if self._hover:
                glow = QRadialGradient(cx, cy, outer_r + 12)
                glow.setColorAt(0.6, QColor(nc.red(), nc.green(), nc.blue(), 0))
                glow.setColorAt(0.85, QColor(nc.red(), nc.green(), nc.blue(), 55))
                glow.setColorAt(1.0,  QColor(nc.red(), nc.green(), nc.blue(), 0))
                pa.setBrush(QBrush(glow)); pa.setPen(Qt.NoPen)
                pa.drawEllipse(cx - outer_r - 12, cy - outer_r - 12,
                               (outer_r + 12)*2, (outer_r + 12)*2)

            # Bubble body
            bubble = QPainterPath()
            bubble.addEllipse(QPointF(cx, cy), float(outer_r), float(outer_r))

            # Base fill (dark + tinted)
            tint_bg = QColor(nc.red()//6, nc.green()//6, nc.blue()//6, 200)
            pa.fillPath(bubble, tint_bg)

            # Neon color fill layer
            fill_grd = QRadialGradient(cx, cy + outer_r * 0.3, outer_r * 1.1)
            fill_grd.setColorAt(0.0, QColor(nc.red(), nc.green(), nc.blue(), 70))
            fill_grd.setColorAt(0.6, QColor(nc.red(), nc.green(), nc.blue(), 45))
            fill_grd.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 20))
            pa.fillPath(bubble, QBrush(fill_grd))

            # Neon border
            border_a = 200 if self._hover else 140
            pa.strokePath(bubble, QPen(QColor(nc.red(), nc.green(), nc.blue(), border_a),
                                       2.0 if self._hover else 1.5))

            # Specular highlight (top-left dome shine)
            shine = QRadialGradient(cx - outer_r * 0.28, cy - outer_r * 0.32, outer_r * 0.45)
            shine.setColorAt(0.0, QColor(255, 255, 255, 90 if not self._hover else 120))
            shine.setColorAt(1.0, QColor(255, 255, 255, 0))
            pa.fillPath(bubble, QBrush(shine))

            # Bottom rim shadow
            rim = QRadialGradient(cx, cy + outer_r * 0.5, outer_r * 0.7)
            rim.setColorAt(0.0, QColor(0, 0, 0, 0))
            rim.setColorAt(1.0, QColor(0, 0, 0, 60))
            pa.fillPath(bubble, QBrush(rim))
        pa.end()


class PopItPage(BasePage):
    KEY = "popit"
    ROWS = 4
    COLS = 5

    def _build_content(self):
        self._total_popped = 0
        self._round_popped = 0
        self._round = 1
        self._total_bubbles = self.ROWS * self.COLS
        self._start_time = None
        self._best_time = None
        root = self.root

        # Score row
        top = QHBoxLayout(); top.setSpacing(10)
        self.score_c = StatChip("total pops",  "0",  self.neon)
        self.round_c = StatChip("round",       "1",  self.neon)
        self.best_c  = StatChip("best time",   "-",  self.neon)
        top.addWidget(self.score_c)
        top.addWidget(self.round_c)
        top.addWidget(self.best_c)
        root.addLayout(top)
        root.addSpacing(14)

        # Live timer label
        self.timer_lbl = GlowLabel("0.00", self.neon, 30, mono=True)
        root.addWidget(self.timer_lbl, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("seconds this round", self.neon))
        root.addSpacing(10)

        # Bubble grid container
        grid_w = QWidget(); grid_w.setStyleSheet("background:transparent;")
        grid_w.setAttribute(Qt.WA_TranslucentBackground)
        grid_layout = QVBoxLayout(grid_w)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(8)

        self._bubbles = []
        for r in range(self.ROWS):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)
            row_layout.addStretch()
            row_widgets = []
            for c in range(self.COLS):
                # Alternate between two neon colors for variety
                use_neon   = self.neon   if (r + c) % 2 == 0 else self.accent
                use_accent = self.accent if (r + c) % 2 == 0 else self.neon
                b = BubbleWidget(r, c, use_neon, use_accent, grid_w)
                b.on_popped = self._bubble_popped
                row_layout.addWidget(b)
                row_widgets.append(b)
            row_layout.addStretch()
            self._bubbles.append(row_widgets)
            grid_layout.addLayout(row_layout)

        root.addWidget(grid_w, 0, Qt.AlignCenter)
        root.addStretch()

        # Reset button
        rst = self._ghost_btn("◀  NEW ROUND")
        rst.clicked.connect(self._new_round)
        root.addWidget(rst, 0, Qt.AlignCenter)

        # Live timer
        self._timer_elapsed = QElapsedTimer()
        self._ticker = QTimer(self); self._ticker.setInterval(30)
        self._ticker.timeout.connect(self._tick_timer)

    def _bubble_popped(self):
        self._total_popped += 1
        self._round_popped += 1
        G.popit += 1
        self.score_c.set(str(G.popit))

        # Start round timer on first pop
        if self._round_popped == 1:
            self._timer_elapsed.start()
            self._ticker.start()

        # Check if all bubbles are popped
        if self._round_popped >= self._total_bubbles:
            elapsed = self._timer_elapsed.elapsed() / 1000.0
            self._ticker.stop()
            self.timer_lbl.set(f"{elapsed:.2f}")

            # Update best time
            if self._best_time is None or elapsed < self._best_time:
                self._best_time = elapsed
                self.best_c.set(f"{elapsed:.2f}s")

            # Flash all bubbles then auto-reset after delay
            QTimer.singleShot(700, self._new_round)

    def _tick_timer(self):
        elapsed = self._timer_elapsed.elapsed() / 1000.0
        self.timer_lbl.set(f"{elapsed:.2f}")

    def _new_round(self):
        self._ticker.stop()
        self._round += 1
        self._round_popped = 0
        self.round_c.set(str(self._round))
        self.timer_lbl.set("0.00")
        for row in self._bubbles:
            for b in row:
                b.reset()

    def showEvent(self, e):
        self.score_c.set(str(G.popit)); super().showEvent(e)
        
# ══════════════════════════════════════════════════════════════
#  FOCUS BURST
# ══════════════════════════════════════════════════════════════
class _FocusShape:
    SHAPES = ["circle", "square", "triangle", "diamond", "star"]
    def __init__(self, zone_w, zone_h):
        self.zone_w = zone_w; self.zone_h = zone_h
        self.shape = random.choice(self.SHAPES)
        color_keys = list(NEON.keys())
        self.color_key = random.choice(color_keys)
        self.color = NEON[self.color_key][0]
        self.size = random.randint(22, 36)
        self.x = random.uniform(self.size, zone_w - self.size)
        self.y = random.uniform(self.size, zone_h - self.size)
        speed = random.uniform(0.6, 1.4); angle = random.uniform(0, math.pi*2)
        self.vx = math.cos(angle)*speed; self.vy = math.sin(angle)*speed

    def step(self, speed_mult=1.0):
        self.x += self.vx * speed_mult; self.y += self.vy * speed_mult
        if self.x - self.size < 0:   self.x = self.size;           self.vx = abs(self.vx)
        if self.x + self.size > self.zone_w: self.x = self.zone_w - self.size; self.vx = -abs(self.vx)
        if self.y - self.size < 0:   self.y = self.size;           self.vy = abs(self.vy)
        if self.y + self.size > self.zone_h: self.y = self.zone_h - self.size; self.vy = -abs(self.vy)

    def draw(self, pa, highlight=False, flash_wrong=False):
        nc = QColor("#ef4444" if flash_wrong else self.color)
        sz = self.size; cx = int(self.x); cy = int(self.y)
        grd = QRadialGradient(cx, cy, sz+10)
        grd.setColorAt(0.4, QColor(nc.red(), nc.green(), nc.blue(), 130 if highlight else 60))
        grd.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.setBrush(QBrush(grd)); pa.setPen(Qt.NoPen)
        pa.drawEllipse(cx-sz-10, cy-sz-10, (sz+10)*2, (sz+10)*2)
        pa.setBrush(QColor(nc.red(), nc.green(), nc.blue(), 160 if highlight else 100))
        pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), 255 if highlight else 180), 2.5 if highlight else 1.5))
        if self.shape == "circle":
            pa.drawEllipse(QPointF(cx, cy), float(sz), float(sz))
        elif self.shape == "square":
            pa.drawRoundedRect(QRectF(cx-sz, cy-sz, sz*2, sz*2), 5, 5)
        elif self.shape == "triangle":
            pa.drawPolygon(QPolygonF([QPointF(cx, cy-sz), QPointF(cx+sz, cy+sz), QPointF(cx-sz, cy+sz)]))
        elif self.shape == "diamond":
            pa.drawPolygon(QPolygonF([QPointF(cx, cy-sz), QPointF(cx+sz, cy), QPointF(cx, cy+sz), QPointF(cx-sz, cy)]))
        elif self.shape == "star":
            pts = [QPointF(cx + (sz if i%2==0 else sz*0.42)*math.cos(math.radians(i*36-90)),
                           cy + (sz if i%2==0 else sz*0.42)*math.sin(math.radians(i*36-90))) for i in range(10)]
            pa.drawPolygon(QPolygonF(pts))
        if highlight:
            sheen = QRadialGradient(cx - sz*0.3, cy - sz*0.3, sz*0.5)
            sheen.setColorAt(0, QColor(255,255,255,80)); sheen.setColorAt(1, QColor(255,255,255,0))
            pa.setBrush(QBrush(sheen)); pa.setPen(Qt.NoPen)
            pa.drawEllipse(QPointF(cx, cy), float(sz), float(sz))


class _TargetHintWidget(QWidget):
    def __init__(self, neon, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._shape = "circle"; self._color = neon; self._neon = neon
        self._phase = 0.0
        self._t = QTimer(self); self._t.setInterval(30); self._t.timeout.connect(self._step); self._t.start()
    def set_target(self, shape, color): self._shape = shape; self._color = color; self.update()
    def _step(self): self._phase = (self._phase + 0.06) % (math.pi*2); self.update()
    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); cx = w//2; cy = h//2
        nc = QColor(self._color); sz = min(w,h)//2 - 6
        pulse = 0.5 + 0.5*math.sin(self._phase)
        pa.setBrush(QColor(nc.red(), nc.green(), nc.blue(), int(25+20*pulse)))
        pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), int(100+80*pulse)), 1.5))
        pa.drawEllipse(QPointF(cx, cy), float(sz+5), float(sz+5))
        s = _FocusShape.__new__(_FocusShape)
        s.shape = self._shape; s.x = cx; s.y = cy; s.color = self._color
        s.color_key = ""; s.size = sz; s.zone_w = w; s.zone_h = h
        s.draw(pa, highlight=True); pa.end()


class _TimeBar(QWidget):
    def __init__(self, neon, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._neon = neon; self._progress = 1.0
    def set(self, v): self._progress = max(0.0, min(1.0, v)); self.update()
    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); r = h//2
        pa.setBrush(QColor(255,255,255,18)); pa.setPen(Qt.NoPen)
        pa.drawRoundedRect(0, 0, w, h, r, r)
        fill_w = int(w * self._progress)
        if fill_w > 0:
            nc = QColor(self._neon); t = 1.0 - self._progress
            rc = min(255, int(nc.red() + (255-nc.red()) * min(1,t*2)))
            gc = max(0,   int(nc.green() * (1 - min(1,t*2))))
            bc = max(0,   int(nc.blue()  * (1 - min(1,t*2))))
            grd = QLinearGradient(0, 0, fill_w, 0)
            grd.setColorAt(0.0, QColor(nc.red(), nc.green(), nc.blue(), 220))
            grd.setColorAt(1.0, QColor(rc, gc, bc, 240))
            pa.setBrush(QBrush(grd))
            pa.drawRoundedRect(0, 0, fill_w, h, r, r)
        pa.end()


class FocusZone(QWidget):
    def __init__(self, neon, on_correct, on_wrong, parent=None):
        super().__init__(parent)
        self.neon = neon; self.on_correct = on_correct; self.on_wrong = on_wrong
        self.setCursor(Qt.CrossCursor); self.setAttribute(Qt.WA_TranslucentBackground)
        self._shapes = []; self._target = None; self._speed_mult = 1.0
        self._wrong_id = None; self._wrong_timer = 0; self._running = False
        self._tick_t = QTimer(self); self._tick_t.setInterval(16); self._tick_t.timeout.connect(self._step)

    def start(self):
        self._speed_mult = 1.0; self._running = True; self._wrong_id = None; self._wrong_timer = 0
        w = max(self.width(), 300); h = max(self.height(), 200)
        self._shapes = [_FocusShape(w, h) for _ in range(12)]
        self._new_target(); self._tick_t.start()

    def stop(self): self._running = False; self._tick_t.stop(); self.update()
    def _new_target(self):
        if self._shapes:
            c = random.choice(self._shapes); self._target = (c.shape, c.color_key, c.color)
    def get_target(self): return self._target
    def boost_speed(self): self._speed_mult = min(self._speed_mult + 0.12, 2.2)
    def reset_speed(self):  self._speed_mult = max(1.0, self._speed_mult - 0.15)
    def change_target(self): self._new_target()

    def _step(self):
        for s in self._shapes: s.step(self._speed_mult)
        if self._wrong_timer > 0:
            self._wrong_timer -= 1
            if self._wrong_timer == 0: self._wrong_id = None
        self.update()

    def mousePressEvent(self, ev):
        if not self._running or ev.button() != Qt.LeftButton: return
        try:    px, py = ev.position().x(), ev.position().y()
        except: px, py = float(ev.x()), float(ev.y())
        for i in range(len(self._shapes)-1, -1, -1):
            s = self._shapes[i]
            if math.hypot(px-s.x, py-s.y) <= s.size + 4:
                t_shape, t_ckey, _ = self._target
                if s.shape == t_shape and s.color_key == t_ckey:
                    self.on_correct(s)
                else:
                    self._wrong_id = i; self._wrong_timer = 18; self.on_wrong()
                return

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); nc = QColor(self.neon)
        bg = QPainterPath(); bg.addRoundedRect(QRectF(1,1,w-2,h-2), 16, 16)
        pa.fillPath(bg, QColor(10,11,18,140))
        pa.strokePath(bg, QPen(QColor(nc.red(),nc.green(),nc.blue(),40), 1))
        sz = 14; pa.setPen(QPen(QColor(nc.red(),nc.green(),nc.blue(),70), 2))
        pa.drawLine(2,sz,2,2); pa.drawLine(2,2,sz,2)
        pa.drawLine(w-sz,2,w-2,2); pa.drawLine(w-2,2,w-2,sz)
        pa.drawLine(2,h-sz,2,h-2); pa.drawLine(2,h-2,sz,h-2)
        pa.drawLine(w-sz,h-2,w-2,h-2); pa.drawLine(w-2,h-sz,w-2,h-2)
        if not self._running:
            pa.setPen(QColor(nc.red(),nc.green(),nc.blue(),100)); pa.setFont(F(14,500))
            pa.drawText(QRect(0,0,w,h), Qt.AlignCenter, "Press START to begin")
            pa.end(); return
        for i, s in enumerate(self._shapes):
            t_shape, t_ckey, _ = self._target
            s.draw(pa, highlight=(s.shape==t_shape and s.color_key==t_ckey), flash_wrong=(i==self._wrong_id))
        pa.end()


class FocusBurstPage(BasePage):
    KEY = "focus"
    DURATION = 30

    def _build_content(self):
        self._combo = 0; self._correct = 0; self._running = False
        self._elapsed = QElapsedTimer()
        self._ticker = QTimer(self); self._ticker.setInterval(80); self._ticker.timeout.connect(self._tick_round)
        self._next_change = 8
        root = self.root

        # Target hint
        hint_row = QHBoxLayout(); hint_row.addStretch()
        hint_row.addWidget(QLabel("TARGET →", styleSheet=f"color:{DIM};background:transparent;font-size:10px;letter-spacing:2px;"))
        hint_row.addSpacing(8)
        self.target_hint = _TargetHintWidget(self.neon); self.target_hint.setFixedSize(52, 52)
        hint_row.addWidget(self.target_hint); hint_row.addStretch()
        root.addLayout(hint_row); root.addSpacing(6)

        # Time bar
        self.time_bar = _TimeBar(self.neon); self.time_bar.setFixedHeight(8)
        root.addWidget(self.time_bar); root.addSpacing(10)

        # Play zone
        self.zone = FocusZone(self.neon, self._on_correct, self._on_wrong)
        self.zone.setMinimumHeight(280)
        self.zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.zone, 1); root.addSpacing(10)

        # Stats
        stats = QHBoxLayout(); stats.setSpacing(10)
        self.combo_c   = StatChip("combo",      "0",              self.neon)
        self.correct_c = StatChip("hits",        "0",              self.neon)
        self.best_c    = StatChip("best combo",  str(G.focus_best), self.neon)
        stats.addWidget(self.combo_c); stats.addWidget(self.correct_c); stats.addWidget(self.best_c)
        root.addLayout(stats); root.addSpacing(10)

        # Start/Stop
        self.ss_btn = QPushButton("▶  START"); self.ss_btn.setFont(F(15,700))
        self.ss_btn.setFixedWidth(200); self.ss_btn.setFixedHeight(48)
        self.ss_btn.setCursor(Qt.PointingHandCursor); self.ss_btn.clicked.connect(self._toggle)
        self._style_btn(False); root.addWidget(self.ss_btn, 0, Qt.AlignCenter)

    def _style_btn(self, running):
        nc = QColor(self.neon); ac = QColor(self.accent)
        r,g,b = nc.red(),nc.green(),nc.blue(); r2,g2,b2 = ac.red(),ac.green(),ac.blue()
        self.ss_btn.setText("■  STOP" if running else "▶  START")
        if running:
            self.ss_btn.setStyleSheet(f"QPushButton{{background:rgba({r//2},{g//2},{b//2},220);color:{TEXT};border:1px solid rgba({r},{g},{b},120);border-radius:12px;}}QPushButton:hover{{background:rgba({r},{g},{b},200);}}")
        else:
            self.ss_btn.setStyleSheet(f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 rgba({r},{g},{b},200),stop:1 rgba({r2},{g2},{b2},200));color:{TEXT};border:none;border-radius:12px;}}QPushButton:hover{{background:rgba({r},{g},{b},255);}}")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(22 if not running else 8)
        eff.setColor(QColor(self.neon)); eff.setOffset(0,3); self.ss_btn.setGraphicsEffect(eff)

    def _update_hint(self):
        t = self.zone.get_target()
        if t: self.target_hint.set_target(t[0], t[2])

    def _toggle(self):
        if not self._running:
            self._running = True; self._combo = 0; self._correct = 0; self._next_change = 8
            self.combo_c.set("0"); self.correct_c.set("0")
            self._elapsed.start(); self.time_bar.set(1.0); self._style_btn(True)
            self.zone.start(); self._update_hint(); self._ticker.start()
        else:
            self._end_round()

    def _on_correct(self, shape_obj):
        self._combo += 1; self._correct += 1
        self.combo_c.set(str(self._combo)); self.correct_c.set(str(self._correct))
        if self._combo > G.focus_best:
            G.focus_best = self._combo; self.best_c.set(str(G.focus_best))
        self.zone.boost_speed()
        if self._correct % self._next_change == 0:
            self.zone.change_target(); self._update_hint()
            self._next_change = max(4, self._next_change - 1)

    def _on_wrong(self):
        self._combo = 0; self.combo_c.set("0"); self.zone.reset_speed()

    def _tick_round(self):
        remaining = max(0.0, self.DURATION - self._elapsed.elapsed()/1000.0)
        self.time_bar.set(remaining / self.DURATION)
        if remaining <= 0: self._end_round()

    def _end_round(self):
        self._ticker.stop(); self._running = False; self.zone.stop()
        self._style_btn(False); self.time_bar.set(0.0)

    def showEvent(self, e): self.best_c.set(str(G.focus_best)); super().showEvent(e)

# ══════════════════════════════════════════════════════════════
#  CHAOS CONTROL
# ══════════════════════════════════════════════════════════════
class ChaosZone(QWidget):
    """Play area filled with fake decoy buttons + one real target."""

    GOAL = 15
    DURATION = 30

    def __init__(self, neon, on_correct, on_wrong, parent=None):
        super().__init__(parent)
        self.neon = neon
        self.on_correct = on_correct
        self.on_wrong   = on_wrong
        self._running   = False
        self._hits      = 0
        self._target_id = -1
        self._buttons   : list[dict] = []   # {x,y,w,h,label,is_target,wobble_phase}
        self._wobble     = 0.0
        self._flash_wrong_id = -1
        self._flash_timer    = 0
        self._move_timer = QTimer(self); self._move_timer.setInterval(50)
        self._move_timer.timeout.connect(self._step)

    # ── public API ────────────────────────────────────────────
    def start(self):
        self._running = True; self._hits = 0
        self._spawn_buttons(); self._move_timer.start()

    def stop(self):
        self._running = False; self._move_timer.stop(); self._buttons.clear()
        self._target_id = -1; self.update()

    def get_hits(self): return self._hits

    # ── internals ─────────────────────────────────────────────
    _FAKE_LABELS = [
        "CLICK", "PRESS", "GO!", "TAP", "HIT", "OK", "YES",
        "★", "◆", "▶", "NOW", "→", "DO IT", "FREE",
        "WIN", "BONUS", "×2", "⚡", "◉", "▣",
    ]

    def _spawn_buttons(self):
        self._buttons.clear()
        w, h = max(self.width(), 300), max(self.height(), 300)
        count = 18   # total buttons including 1 real
        placed = []

        def overlaps(x, y, bw, bh):
            for p in placed:
                if (abs(x - p[0]) < bw + 8 and abs(y - p[1]) < bh + 8):
                    return True
            return False

        # Real target — place first at a random spot
        tw, th = 88, 38
        for _ in range(200):
            tx = random.randint(4, w - tw - 4)
            ty = random.randint(4, h - th - 4)
            if not overlaps(tx, ty, tw, th): break
        placed.append((tx, ty, tw, th))
        self._target_id = 0
        self._buttons.append({
            "x": tx, "y": ty, "w": tw, "h": th,
            "label": "CLICK ME",
            "is_target": True,
            "wobble_phase": random.uniform(0, math.pi * 2),
            "vx": random.choice([-1, 1]) * random.uniform(0.6, 1.4),
            "vy": random.choice([-1, 1]) * random.uniform(0.6, 1.4),
        })

        # Fake decoys
        for i in range(1, count):
            bw = random.randint(48, 90); bh = random.randint(26, 40)
            for _ in range(200):
                bx = random.randint(4, w - bw - 4)
                by_ = random.randint(4, h - bh - 4)
                if not overlaps(bx, by_, bw, bh): break
            placed.append((bx, by_, bw, bh))
            self._buttons.append({
                "x": bx, "y": by_, "w": bw, "h": bh,
                "label": random.choice(self._FAKE_LABELS),
                "is_target": False,
                "wobble_phase": random.uniform(0, math.pi * 2),
                "vx": random.choice([-1, 1]) * random.uniform(0.3, 1.8),
                "vy": random.choice([-1, 1]) * random.uniform(0.3, 1.8),
            })

    def _step(self):
        if not self._running: return
        self._wobble += 0.07
        w, h = self.width(), self.height()
        for b in self._buttons:
            b["wobble_phase"] += 0.04
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            # Bounce off walls
            if b["x"] < 0:           b["x"] = 0;          b["vx"] =  abs(b["vx"])
            if b["x"] + b["w"] > w:  b["x"] = w - b["w"]; b["vx"] = -abs(b["vx"])
            if b["y"] < 0:           b["y"] = 0;          b["vy"] =  abs(b["vy"])
            if b["y"] + b["h"] > h:  b["y"] = h - b["h"]; b["vy"] = -abs(b["vy"])
        if self._flash_timer > 0:
            self._flash_timer -= 1
            if self._flash_timer == 0: self._flash_wrong_id = -1
        self.update()

    def _relocate_target(self):
        """After a correct hit, jump the target to a new random position."""
        w, h = max(self.width(), 300), max(self.height(), 300)
        b = self._buttons[self._target_id]
        for _ in range(100):
            nx = random.randint(4, w - b["w"] - 4)
            ny = random.randint(4, h - b["h"] - 4)
            # avoid overlap with current positions
            ok = True
            for ob in self._buttons:
                if ob is b: continue
                if abs(nx - ob["x"]) < b["w"] + 6 and abs(ny - ob["y"]) < b["h"] + 6:
                    ok = False; break
            if ok: break
        b["x"], b["y"] = float(nx), float(ny)
        b["vx"] = random.choice([-1, 1]) * random.uniform(0.8, 1.8)
        b["vy"] = random.choice([-1, 1]) * random.uniform(0.8, 1.8)
        # Shuffle decoy labels so the screen feels fresh
        for ob in self._buttons:
            if not ob["is_target"]:
                ob["label"] = random.choice(self._FAKE_LABELS)

    def mousePressEvent(self, ev):
        if not self._running or ev.button() != Qt.LeftButton: return
        try:    px, py = ev.position().x(), ev.position().y()
        except: px, py = float(ev.x()), float(ev.y())
        # Check back-to-front
        for i in range(len(self._buttons) - 1, -1, -1):
            b = self._buttons[i]
            if b["x"] <= px <= b["x"] + b["w"] and b["y"] <= py <= b["y"] + b["h"]:
                if b["is_target"]:
                    self._hits += 1
                    self._relocate_target()
                    self.on_correct(self._hits)
                else:
                    self._flash_wrong_id = i
                    self._flash_timer = 14
                    self.on_wrong()
                return

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        nc = QColor(self.neon)

        # Background
        bg = QPainterPath(); bg.addRoundedRect(QRectF(1, 1, w - 2, h - 2), 16, 16)
        pa.fillPath(bg, QColor(10, 11, 18, 140))
        pa.strokePath(bg, QPen(QColor(nc.red(), nc.green(), nc.blue(), 40), 1))

        if not self._running:
            pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), 100)); pa.setFont(F(14, 500))
            pa.drawText(QRect(0, 0, w, h), Qt.AlignCenter, "Press START to begin")
            pa.end(); return

        for i, b in enumerate(self._buttons):
            bx, by_ = int(b["x"]), int(b["y"])
            bw, bh   = b["w"], b["h"]
            is_tgt   = b["is_target"]
            wobble   = math.sin(b["wobble_phase"]) * 2.5

            # slight wobble offset for decoys
            draw_x = bx + (0 if is_tgt else int(wobble))
            draw_y = by_

            rect = QRectF(draw_x, draw_y, bw, bh)
            path = QPainterPath(); path.addRoundedRect(rect, 8, 8)

            if is_tgt:
                # Glowing real button
                pulse = 0.6 + 0.4 * math.sin(self._wobble * 1.8)
                fill_a = int(180 + 60 * pulse)
                pa.fillPath(path, QColor(nc.red(), nc.green(), nc.blue(), fill_a))
                # Glow halo
                glow_pen = QPen(QColor(nc.red(), nc.green(), nc.blue(), int(120 * pulse)), 3)
                pa.strokePath(path, glow_pen)
                # Label
                pa.setPen(QColor(255, 255, 255, 255)); pa.setFont(F(10, 700))
                pa.drawText(QRect(draw_x, draw_y, bw, bh), Qt.AlignCenter, b["label"])
            else:
                # Decoy buttons — muted / confusing
                flash = (i == self._flash_wrong_id)
                if flash:
                    pa.fillPath(path, QColor(220, 30, 30, 200))
                    pa.strokePath(path, QPen(QColor(255, 80, 80, 200), 2))
                else:
                    # vary decoy appearance
                    shade = (i * 37) % 60
                    pa.fillPath(path, QColor(30 + shade, 32 + shade, 48 + shade, 160))
                    pa.strokePath(path, QPen(QColor(80, 90, 120, 100), 1))
                txt_col = QColor(220, 80, 80, 200) if flash else QColor(180, 185, 210, 180)
                pa.setPen(txt_col); pa.setFont(F(9, 500))
                pa.drawText(QRect(draw_x, draw_y, bw, bh), Qt.AlignCenter, b["label"])

        pa.end()


class ChaosControlPage(BasePage):
    KEY = "chaos"
    GOAL = 15
    DURATION = 30

    def _build_content(self):
        self._hits    = 0
        self._running = False
        self._elapsed = QElapsedTimer()
        self._ticker  = QTimer(self); self._ticker.setInterval(80)
        self._ticker.timeout.connect(self._tick)
        root = self.root

        # Time bar
        self.time_bar = _TimeBar(self.neon); self.time_bar.setFixedHeight(8)
        root.addWidget(self.time_bar); root.addSpacing(8)

        # Goal label
        self.goal_lbl = QLabel(f"HIT THE REAL BUTTON  {self._hits} / {self.GOAL}")
        self.goal_lbl.setFont(F(10, 600))
        self.goal_lbl.setAlignment(Qt.AlignCenter)
        self.goal_lbl.setStyleSheet(f"color:{self.neon};background:transparent;letter-spacing:2px;")
        root.addWidget(self.goal_lbl); root.addSpacing(6)

        # Play zone
        self.zone = ChaosZone(self.neon, self._on_correct, self._on_wrong)
        self.zone.setMinimumHeight(300)
        self.zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.zone, 1); root.addSpacing(10)

        # Stats row
        stats = QHBoxLayout(); stats.setSpacing(10)
        self.hits_c  = StatChip("hits",      "0",              self.neon)
        self.miss_c  = StatChip("misses",    "0",              self.neon)
        self.best_c  = StatChip("best hits", str(G.chaos_best), self.neon)
        stats.addWidget(self.hits_c); stats.addWidget(self.miss_c); stats.addWidget(self.best_c)
        root.addLayout(stats); root.addSpacing(10)

        # Start/Stop button
        self.ss_btn = QPushButton("▶  START"); self.ss_btn.setFont(F(15, 700))
        self.ss_btn.setFixedWidth(200); self.ss_btn.setFixedHeight(48)
        self.ss_btn.setCursor(Qt.PointingHandCursor)
        self.ss_btn.clicked.connect(self._toggle)
        self._style_btn(False); root.addWidget(self.ss_btn, 0, Qt.AlignCenter)
        self._misses = 0

    def _style_btn(self, running):
        nc = QColor(self.neon); ac = QColor(self.accent)
        r,g,b = nc.red(),nc.green(),nc.blue(); r2,g2,b2 = ac.red(),ac.green(),ac.blue()
        self.ss_btn.setText("■  STOP" if running else "▶  START")
        if running:
            self.ss_btn.setStyleSheet(f"QPushButton{{background:rgba({r//2},{g//2},{b//2},220);color:{TEXT};border:1px solid rgba({r},{g},{b},120);border-radius:12px;}}QPushButton:hover{{background:rgba({r},{g},{b},200);}}")
        else:
            self.ss_btn.setStyleSheet(f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 rgba({r},{g},{b},200),stop:1 rgba({r2},{g2},{b2},200));color:{TEXT};border:none;border-radius:12px;}}QPushButton:hover{{background:rgba({r},{g},{b},255);}}")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(22 if not running else 8)
        eff.setColor(QColor(self.neon)); eff.setOffset(0, 3); self.ss_btn.setGraphicsEffect(eff)

    def _toggle(self):
        if not self._running:
            self._running = True; self._hits = 0; self._misses = 0
            self.hits_c.set("0"); self.miss_c.set("0")
            self._update_goal_lbl()
            self._elapsed.start(); self.time_bar.set(1.0)
            self._style_btn(True); self.zone.start(); self._ticker.start()
        else:
            self._end_round()

    def _on_correct(self, total_hits):
        self._hits = total_hits
        self.hits_c.set(str(self._hits))
        self._update_goal_lbl()
        if self._hits >= self.GOAL:
            self._end_round()

    def _on_wrong(self):
        self._misses += 1; self.miss_c.set(str(self._misses))

    def _update_goal_lbl(self):
        self.goal_lbl.setText(f"HIT THE REAL BUTTON  {self._hits} / {self.GOAL}")

    def _tick(self):
        remaining = max(0.0, self.DURATION - self._elapsed.elapsed() / 1000.0)
        self.time_bar.set(remaining / self.DURATION)
        if remaining <= 0:
            self._end_round()

    def _end_round(self):
        self._ticker.stop(); self._running = False; self.zone.stop()
        self._style_btn(False); self.time_bar.set(0.0)
        if self._hits > G.chaos_best:
            G.chaos_best = self._hits; self.best_c.set(str(G.chaos_best))

    def showEvent(self, e):
        self.best_c.set(str(G.chaos_best)); super().showEvent(e)


# ══════════════════════════════════════════════════════════════
#  MEMORY FLASH
# ══════════════════════════════════════════════════════════════
class MemoryGrid(QWidget):
    """
    Draws a grid of N tiles.
    Phases:
      'idle'   – all dark, waiting
      'show'   – tiles in sequence light up one by one
      'input'  – player taps tiles; correct = neon, wrong = red flash
      'result' – brief full-grid flash (green=win / red=fail)
    """
    COLS = 4

    def __init__(self, neon, accent, on_input, parent=None):
        super().__init__(parent)
        self.neon   = neon
        self.accent = accent
        self.on_input = on_input          # callback(index, is_correct)
        self._n_tiles  = 8
        self._pattern  : list[int] = []
        self._revealed : list[int] = []   # tiles correctly tapped so far
        self._lit_show  = -1              # tile currently lit during show phase
        self._wrong_id  = -1
        self._wrong_timer = 0
        self._result_flash = 0            # >0 = result phase frames remaining
        self._result_win   = False
        self._phase = "idle"              # idle | show | input | result
        self._pulse = 0.0
        self._anim_t = QTimer(self); self._anim_t.setInterval(16)
        self._anim_t.timeout.connect(self._anim_step); self._anim_t.start()

    # ── tile geometry ──────────────────────────────────────────
    def _rows(self): return math.ceil(self._n_tiles / self.COLS)
    def _tile_rect(self, idx):
        cols = self.COLS; rows = self._rows()
        w, h = self.width(), self.height()
        pad = 10; gap = 8
        tw = (w - pad*2 - gap*(cols-1)) / cols
        th = (h - pad*2 - gap*(rows-1)) / rows
        c = idx % cols; r = idx // cols
        x = pad + c*(tw+gap); y = pad + r*(th+gap)
        return QRectF(x, y, tw, th)

    # ── public API ─────────────────────────────────────────────
    def setup(self, n_tiles, pattern):
        self._n_tiles = n_tiles
        self._pattern = list(pattern)
        self._revealed.clear()
        self._lit_show = -1; self._wrong_id = -1; self._wrong_timer = 0
        self._result_flash = 0; self._phase = "idle"
        self.update()

    def play_show(self, lit_index):
        """Light up a specific tile index (called externally by sequencer)."""
        self._lit_show = lit_index; self._phase = "show"; self.update()

    def hide_show(self):
        self._lit_show = -1; self.update()

    def set_phase(self, phase):
        self._phase = phase
        if phase == "idle": self._lit_show = -1; self._revealed.clear()
        self.update()

    def flash_result(self, win):
        self._result_win = win; self._result_flash = 28; self._phase = "result"
        self.update()

    # ── input handling ─────────────────────────────────────────
    def mousePressEvent(self, ev):
        if self._phase != "input" or ev.button() != Qt.LeftButton: return
        try:    px, py = ev.position().x(), ev.position().y()
        except: px, py = float(ev.x()), float(ev.y())
        for i in range(self._n_tiles):
            r = self._tile_rect(i)
            if r.contains(px, py):
                if i in self._revealed: return        # already tapped
                expected = self._pattern[len(self._revealed)]
                correct  = (i == expected)
                if correct:
                    self._revealed.append(i)
                else:
                    self._wrong_id = i; self._wrong_timer = 18
                self.on_input(i, correct)
                self.update()
                return

    # ── animation ──────────────────────────────────────────────
    def _anim_step(self):
        self._pulse = (self._pulse + 0.04) % (math.pi * 2)
        if self._wrong_timer > 0:
            self._wrong_timer -= 1
            if self._wrong_timer == 0: self._wrong_id = -1
        if self._result_flash > 0:
            self._result_flash -= 1
        self.update()

    # ── paint ──────────────────────────────────────────────────
    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        nc  = QColor(self.neon)
        ac  = QColor(self.accent)
        pulse = 0.5 + 0.5 * math.sin(self._pulse)

        # Result overlay
        if self._phase == "result" and self._result_flash > 0:
            alpha = int(self._result_flash / 28 * 180)
            col = QColor(60, 220, 100, alpha) if self._result_win else QColor(220, 50, 50, alpha)
            pa.fillRect(0, 0, self.width(), self.height(), col)

        for i in range(self._n_tiles):
            rect  = self._tile_rect(i)
            path  = QPainterPath(); path.addRoundedRect(rect, 10, 10)
            is_lit    = (i == self._lit_show)
            is_done   = (i in self._revealed)
            is_wrong  = (i == self._wrong_id)
            is_next   = (self._phase == "input" and
                         len(self._revealed) < len(self._pattern) and
                         i == self._pattern[len(self._revealed)])

            if is_lit:
                # Show-phase flash — bright neon fill
                glow_a = int(200 + 55 * pulse)
                pa.fillPath(path, QColor(nc.red(), nc.green(), nc.blue(), glow_a))
                pa.strokePath(path, QPen(QColor(255, 255, 255, 200), 2))
                # Inner white hotspot
                inner = QPainterPath(); inner.addRoundedRect(rect.adjusted(6,6,-6,-6), 6, 6)
                pa.fillPath(inner, QColor(255, 255, 255, 90))
            elif is_done:
                # Correctly tapped — solid neon
                pa.fillPath(path, QColor(nc.red(), nc.green(), nc.blue(), 200))
                pa.strokePath(path, QPen(QColor(255,255,255,120), 1.5))
            elif is_wrong:
                # Wrong tap — red
                pa.fillPath(path, QColor(220, 50, 50, 220))
                pa.strokePath(path, QPen(QColor(255, 80, 80, 200), 2))
            else:
                # Default dark tile
                shade = 22 + (i % 3) * 5
                pa.fillPath(path, QColor(shade, shade+2, shade+12, 210))
                border_a = int(50 + 30 * pulse) if (self._phase == "input" and is_next) else 45
                pa.strokePath(path, QPen(QColor(nc.red(), nc.green(), nc.blue(), border_a), 1))

            # Tile index number (subtle)
            if self._phase in ("idle", "show"):
                pa.setPen(QColor(255, 255, 255, 25 if not is_lit else 0))
                pa.setFont(F(9, 400))
                pa.drawText(rect.toRect(), Qt.AlignCenter, str(i + 1))

        pa.end()


class MemoryFlashPage(BasePage):
    KEY = "memory"

    # Show-phase: each tile stays lit for flash_ms, then off for gap_ms
    _BASE_FLASH_MS = 600
    _BASE_GAP_MS   = 200
    _MIN_FLASH_MS  = 180
    _MIN_GAP_MS    = 80

    def _build_content(self):
        self._round       = 0
        self._score       = 0           # rounds passed
        self._running     = False
        self._phase       = "idle"      # idle | showing | waiting | input | feedback
        self._pattern     : list[int] = []
        self._show_idx    = 0           # which step in the show sequence we're on
        self._show_timer  = QTimer(self); self._show_timer.setSingleShot(True)
        self._show_timer.timeout.connect(self._show_next_step)
        self._feedback_timer = QTimer(self); self._feedback_timer.setSingleShot(True)
        self._feedback_timer.timeout.connect(self._next_round)
        self._input_ok    = 0           # correct taps in current input phase

        root = self.root

        # ── Status label ──────────────────────────────────────
        self.status_lbl = QLabel("Press START")
        self.status_lbl.setFont(F(13, 600))
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet(f"color:{self.neon};background:transparent;letter-spacing:1px;")
        root.addWidget(self.status_lbl); root.addSpacing(6)

        # ── Round / speed bar ─────────────────────────────────
        bar_row = QHBoxLayout(); bar_row.setSpacing(8)
        self.round_lbl = QLabel("ROUND 0")
        self.round_lbl.setFont(F(9, 500))
        self.round_lbl.setStyleSheet(f"color:{DIM};background:transparent;letter-spacing:2px;")
        bar_row.addWidget(self.round_lbl)
        bar_row.addStretch()
        self.speed_lbl = QLabel("SPEED ×1.0")
        self.speed_lbl.setFont(F(9, 500))
        self.speed_lbl.setStyleSheet(f"color:{DIM};background:transparent;letter-spacing:2px;")
        bar_row.addWidget(self.speed_lbl)
        root.addLayout(bar_row); root.addSpacing(4)

        # ── Memory grid ───────────────────────────────────────
        self.grid = MemoryGrid(self.neon, self.accent, self._on_tile_input)
        self.grid.setMinimumHeight(260)
        self.grid.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.grid, 1); root.addSpacing(10)

        # ── Stat chips ────────────────────────────────────────
        chips = QHBoxLayout(); chips.setSpacing(10)
        self.score_c  = StatChip("score",      "0",                self.neon)
        self.round_c  = StatChip("round",      "0",                self.neon)
        self.best_c   = StatChip("best score", str(G.memory_best), self.neon)
        chips.addWidget(self.score_c); chips.addWidget(self.round_c); chips.addWidget(self.best_c)
        root.addLayout(chips); root.addSpacing(10)

        # ── Start button ──────────────────────────────────────
        self.ss_btn = QPushButton("▶  START"); self.ss_btn.setFont(F(15, 700))
        self.ss_btn.setFixedWidth(200); self.ss_btn.setFixedHeight(48)
        self.ss_btn.setCursor(Qt.PointingHandCursor)
        self.ss_btn.clicked.connect(self._toggle)
        self._style_btn(False)
        root.addWidget(self.ss_btn, 0, Qt.AlignCenter)

    # ── helpers ───────────────────────────────────────────────
    def _style_btn(self, running):
        nc = QColor(self.neon); ac = QColor(self.accent)
        r, g, b = nc.red(), nc.green(), nc.blue()
        r2, g2, b2 = ac.red(), ac.green(), ac.blue()
        self.ss_btn.setText("■  STOP" if running else "▶  START")
        if running:
            self.ss_btn.setStyleSheet(
                f"QPushButton{{background:rgba({r//2},{g//2},{b//2},220);color:{TEXT};"
                f"border:1px solid rgba({r},{g},{b},120);border-radius:12px;}}"
                f"QPushButton:hover{{background:rgba({r},{g},{b},200);}}")
        else:
            self.ss_btn.setStyleSheet(
                f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 rgba({r},{g},{b},200),stop:1 rgba({r2},{g2},{b2},200));"
                f"color:{TEXT};border:none;border-radius:12px;}}"
                f"QPushButton:hover{{background:rgba({r},{g},{b},255);}}")
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(22 if not running else 8)
        eff.setColor(QColor(self.neon)); eff.setOffset(0, 3)
        self.ss_btn.setGraphicsEffect(eff)

    def _flash_ms(self):
        speed = 1.0 + (self._round - 1) * 0.15
        return max(self._MIN_FLASH_MS, int(self._BASE_FLASH_MS / speed))

    def _gap_ms(self):
        speed = 1.0 + (self._round - 1) * 0.15
        return max(self._MIN_GAP_MS, int(self._BASE_GAP_MS / speed))

    def _speed_mult(self):
        return 1.0 + (self._round - 1) * 0.15

    def _n_tiles(self):
        """5 tiles rounds 1-2, 6 tiles rounds 3-4, 7 rounds 5-6, 8 rounds 7+"""
        return min(8, 5 + (self._round - 1) // 2)

    def _pattern_len(self):
        """Pattern length grows with round: 3 + round//2, capped at n_tiles."""
        return min(self._n_tiles(), 3 + self._round // 2)

    # ── game flow ─────────────────────────────────────────────
    def _toggle(self):
        if not self._running:
            self._running = True; self._round = 0; self._score = 0
            self.score_c.set("0"); self.round_c.set("0")
            self._style_btn(True)
            self._next_round()
        else:
            self._stop_game()

    def _stop_game(self):
        self._running = False
        self._show_timer.stop(); self._feedback_timer.stop()
        self.grid.set_phase("idle")
        self._style_btn(False)
        self.status_lbl.setText("Stopped")
        if self._score > G.memory_best:
            G.memory_best = self._score; self.best_c.set(str(G.memory_best))

    def _next_round(self):
        if not self._running: return
        self._round += 1
        n  = self._n_tiles()
        pl = self._pattern_len()
        self._pattern = random.sample(range(n), pl)
        self._input_ok = 0
        self.round_lbl.setText(f"ROUND {self._round}")
        self.round_c.set(str(self._round))
        sp = self._speed_mult()
        self.speed_lbl.setText(f"SPEED ×{sp:.1f}")
        self.grid.setup(n, self._pattern)
        self.status_lbl.setText("Watch the pattern…")
        # Brief pause before showing pattern
        self._show_idx = 0
        self._show_timer.start(400)

    def _show_next_step(self):
        if not self._running: return
        if self._show_idx < len(self._pattern):
            tile = self._pattern[self._show_idx]
            self.grid.play_show(tile)
            # After flash_ms turn tile off and schedule next
            QTimer.singleShot(self._flash_ms(), self._after_flash)
        else:
            # All tiles shown → input phase
            self.grid.hide_show()
            self.grid.set_phase("input")
            self.status_lbl.setText(f"Repeat the pattern!  (0 / {len(self._pattern)})")

    def _after_flash(self):
        if not self._running: return
        self.grid.hide_show()
        self._show_idx += 1
        # Gap between tiles
        self._show_timer.start(self._gap_ms())

    def _on_tile_input(self, tile_idx, correct):
        if not self._running: return
        if correct:
            self._input_ok += 1
            done = self._input_ok
            total = len(self._pattern)
            self.status_lbl.setText(f"Repeat the pattern!  ({done} / {total})")
            # Play a short beep-like visual pulse via QTimer
            if done == total:
                # Round complete!
                self._score += 1
                self.score_c.set(str(self._score))
                if self._score > G.memory_best:
                    G.memory_best = self._score
                    self.best_c.set(str(G.memory_best))
                self.grid.flash_result(True)
                self.status_lbl.setText("✓  Pattern matched!")
                self._feedback_timer.start(700)
        else:
            # Wrong tile — round failed
            self.grid.flash_result(False)
            self.status_lbl.setText("✗  Wrong tile!  Game over.")
            self._feedback_timer.stop()
            QTimer.singleShot(900, self._stop_game)

    def showEvent(self, e):
        self.best_c.set(str(G.memory_best)); super().showEvent(e)


# ══════════════════════════════════════════════════════════════
#  DOPAMINE METER
# ══════════════════════════════════════════════════════════════
class _EnergyBar(QWidget):
    """Vertical glowing energy bar — fills bottom-to-top."""
    def __init__(self, neon, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._neon     = neon
        self._fill     = 0.0   # 0.0 – 1.0
        self._target   = 0.0
        self._phase    = 0.0
        self._anim_t   = QTimer(self); self._anim_t.setInterval(16)
        self._anim_t.timeout.connect(self._step); self._anim_t.start()

    def set_fill(self, v):
        self._target = max(0.0, min(1.0, v))

    def _step(self):
        self._fill += (self._target - self._fill) * 0.12
        self._phase = (self._phase + 0.05) % (math.pi * 2)
        self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        nc   = QColor(self._neon)
        r, g, b = nc.red(), nc.green(), nc.blue()

        # Track background
        track = QPainterPath()
        track.addRoundedRect(QRectF(0, 0, w, h), w // 2, w // 2)
        pa.fillPath(track, QColor(18, 22, 32, 220))
        pa.strokePath(track, QPen(QColor(r, g, b, 55), 1.5))

        # Segment tick marks
        segs = 10
        pa.setPen(QPen(QColor(255, 255, 255, 18), 1))
        for i in range(1, segs):
            y = int(h * i / segs)
            pa.drawLine(2, y, w - 2, y)

        # Filled portion (bottom-to-top)
        fill_h = int(h * self._fill)
        if fill_h > 1:
            fill_y = h - fill_h
            fill_path = QPainterPath()
            fill_path.addRoundedRect(QRectF(0, fill_y, w, fill_h), w // 2, w // 2)

            # Colour shifts: green → yellow → red as overfill
            t = self._fill
            if t < 0.6:
                cr, cg, cb = r, g, b
            elif t < 0.85:
                # blend to yellow
                ratio = (t - 0.6) / 0.25
                cr = int(r + (255 - r) * ratio)
                cg = int(g + (200 - g) * ratio)
                cb = int(b * (1 - ratio))
            else:
                # blend to red (overload)
                ratio = (t - 0.85) / 0.15
                cr = 255
                cg = int(200 * (1 - ratio))
                cb = 0

            pulse = 0.75 + 0.25 * math.sin(self._phase)
            grd = QLinearGradient(0, fill_y + fill_h, 0, fill_y)
            grd.setColorAt(0.0, QColor(cr, cg, cb, int(200 * pulse)))
            grd.setColorAt(0.5, QColor(min(cr+40,255), min(cg+40,255), min(cb+40,255), int(230 * pulse)))
            grd.setColorAt(1.0, QColor(255, 255, 255, int(180 * pulse)))
            pa.fillPath(fill_path, QBrush(grd))

            # Glow halo
            halo_a = int(60 * pulse)
            pa.strokePath(fill_path, QPen(QColor(cr, cg, cb, halo_a), 6))

        # Top cap label
        pa.setPen(QColor(r, g, b, 160)); pa.setFont(F(7, 600))
        pa.drawText(QRect(0, 0, w, 18), Qt.AlignCenter, "E")
        pa.end()


class _ZoneWindow(QWidget):
    """
    The click zone: shows a pulsing ring target.
    Player must click INSIDE the ring (controlled) → energy +.
    Clicking outside or too fast (< min_interval ms) → energy -.
    The ring slowly shrinks over time to increase difficulty.
    """
    def __init__(self, neon, on_click, parent=None):
        super().__init__(parent)
        self.neon      = neon
        self.on_click  = on_click   # callback(is_controlled: bool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self._running       = False
        self._ring_r        = 80.0   # current ring radius
        self._target_r      = 80.0
        self._phase         = 0.0
        self._last_click_ms = 0
        self._miss_flash    = 0
        self._hit_flash     = 0
        self._anim_t = QTimer(self); self._anim_t.setInterval(16)
        self._anim_t.timeout.connect(self._step)

    def start(self):
        self._running = True; self._ring_r = 80.0; self._target_r = 80.0
        self._last_click_ms = 0; self._miss_flash = 0; self._hit_flash = 0
        self._anim_t.start()

    def stop(self):
        self._running = False; self._anim_t.stop(); self.update()

    def shrink(self):
        """Called each second to slowly shrink the target ring."""
        self._target_r = max(28.0, self._target_r - 2.5)

    def reset_ring(self):
        self._target_r = 80.0

    def _step(self):
        self._phase = (self._phase + 0.035) % (math.pi * 2)
        self._ring_r += (self._target_r - self._ring_r) * 0.08
        if self._miss_flash > 0: self._miss_flash -= 1
        if self._hit_flash  > 0: self._hit_flash  -= 1
        self.update()

    def mousePressEvent(self, ev):
        if not self._running or ev.button() != Qt.LeftButton: return
        try:    px, py = ev.position().x(), ev.position().y()
        except: px, py = float(ev.x()), float(ev.y())
        cx, cy = self.width() / 2, self.height() / 2
        dist   = math.hypot(px - cx, py - cy)

        # Measure interval since last click
        now_ms = ev.timestamp() if hasattr(ev, 'timestamp') else 0
        # Use QElapsedTimer trick: just check ring distance
        inside = dist <= self._ring_r + 6

        if inside:
            self._hit_flash = 14
            self.on_click(True)
        else:
            self._miss_flash = 14
            self.on_click(False)

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        nc = QColor(self.neon)
        r, g, b = nc.red(), nc.green(), nc.blue()

        # Dark zone background
        bg = QPainterPath(); bg.addRoundedRect(QRectF(1, 1, w-2, h-2), 16, 16)
        pa.fillPath(bg, QColor(10, 12, 18, 160))

        if not self._running:
            pa.setPen(QColor(r, g, b, 80)); pa.setFont(F(13, 500))
            pa.drawText(QRect(0, 0, w, h), Qt.AlignCenter, "Press START to begin")
            pa.end(); return

        pulse = 0.5 + 0.5 * math.sin(self._phase)

        # Miss flash overlay
        if self._miss_flash > 0:
            alpha = int(self._miss_flash / 14 * 70)
            pa.fillPath(bg, QColor(220, 40, 40, alpha))

        # Hit flash overlay
        if self._hit_flash > 0:
            alpha = int(self._hit_flash / 14 * 60)
            pa.fillPath(bg, QColor(r, g, b, alpha))

        # Outer guidance ring (faint)
        pa.setPen(QPen(QColor(r, g, b, 25), 1))
        pa.setBrush(Qt.NoBrush)
        pa.drawEllipse(QPointF(cx, cy), self._ring_r + 22, self._ring_r + 22)

        # Main target ring — glow
        glow_a = int(40 + 30 * pulse)
        pa.setPen(QPen(QColor(r, g, b, glow_a), 18))
        pa.drawEllipse(QPointF(cx, cy), float(self._ring_r), float(self._ring_r))

        # Main target ring — solid
        ring_a = int(160 + 80 * pulse)
        pa.setPen(QPen(QColor(r, g, b, ring_a), 3))
        pa.drawEllipse(QPointF(cx, cy), float(self._ring_r), float(self._ring_r))

        # Crosshair centre
        cross_len = 10
        pa.setPen(QPen(QColor(r, g, b, 120), 1))
        pa.drawLine(QPointF(cx - cross_len, cy), QPointF(cx + cross_len, cy))
        pa.drawLine(QPointF(cx, cy - cross_len), QPointF(cx, cy + cross_len))

        # Tick marks on ring
        pa.setPen(QPen(QColor(255, 255, 255, 40), 1))
        for deg in range(0, 360, 30):
            rad = math.radians(deg + self._phase * 10)
            x1  = cx + (self._ring_r - 5) * math.cos(rad)
            y1  = cy + (self._ring_r - 5) * math.sin(rad)
            x2  = cx + (self._ring_r + 5) * math.cos(rad)
            y2  = cy + (self._ring_r + 5) * math.sin(rad)
            pa.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Instruction text
        pa.setPen(QColor(255, 255, 255, 50)); pa.setFont(F(9, 400))
        pa.drawText(QRect(0, h - 28, w, 24), Qt.AlignCenter, "Click INSIDE the Ring  •  Stay Calm")

        pa.end()


class DopamineMeterPage(BasePage):
    KEY      = "dopa"
    DURATION = 60        # seconds per session

    # Energy constants
    _E_HIT_FAST   = +8.0   # inside ring — good
    _E_MISS       = -15.0  # outside ring — impulsive
    _E_DECAY      = -0.04  # per tick (passive drain — must keep clicking)
    _E_MAX        = 100.0

    # Click-rate impulse penalty: if > MAX_CPS clicks/sec → penalty
    _MAX_CPS      = 3.5
    _IMPULSE_PEN  = -12.0

    def _build_content(self):
        self._running   = False
        self._energy    = 0.0
        self._score     = 0       # peak energy integer reached this session
        self._clicks_this_sec = 0
        self._elapsed   = QElapsedTimer()
        self._last_sec  = 0

        self._ticker = QTimer(self); self._ticker.setInterval(50)
        self._ticker.timeout.connect(self._tick)
        self._sec_t  = QTimer(self); self._sec_t.setInterval(1000)
        self._sec_t.timeout.connect(self._on_second)

        root = self.root

        # ── Top row: time bar + energy bar side by side ────────
        top_row = QHBoxLayout(); top_row.setSpacing(12)

        # Left: vertical energy bar
        self.ebar = _EnergyBar(self.neon)
        self.ebar.setFixedWidth(28)
        self.ebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        top_row.addWidget(self.ebar)

        # Right column: time bar + zone
        right_col = QVBoxLayout(); right_col.setSpacing(8)

        # Time bar
        self.time_bar = _TimeBar(self.neon); self.time_bar.setFixedHeight(8)
        right_col.addWidget(self.time_bar)

        # Status label
        self.status_lbl = QLabel("Stay controlled — click inside the ring")
        self.status_lbl.setFont(F(10, 500))
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet(f"color:{self.neon};background:transparent;letter-spacing:1px;")
        right_col.addWidget(self.status_lbl)

        # Click zone
        self.zone = _ZoneWindow(self.neon, self._on_click)
        self.zone.setMinimumHeight(240)
        self.zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_col.addWidget(self.zone, 1)

        top_row.addLayout(right_col, 1)
        root.addLayout(top_row, 1); root.addSpacing(10)

        # ── Energy % label ────────────────────────────────────
        self.energy_lbl = GlowLabel("0%", self.neon, 42, mono=True)
        root.addWidget(self.energy_lbl, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("focus energy", self.neon))
        root.addSpacing(8)

        # ── Stat chips ────────────────────────────────────────
        chips = QHBoxLayout(); chips.setSpacing(10)
        self.peak_c  = StatChip("peak",      "0%",               self.neon)
        self.hits_c  = StatChip("controlled","0",                self.neon)
        self.miss_c  = StatChip("impulsive", "0",                self.neon)
        self.best_c  = StatChip("best peak", f"{G.dopa_best}%",  self.neon)
        chips.addWidget(self.peak_c)
        chips.addWidget(self.hits_c)
        chips.addWidget(self.miss_c)
        chips.addWidget(self.best_c)
        root.addLayout(chips); root.addSpacing(10)

        # ── Start / Stop button ───────────────────────────────
        self.ss_btn = QPushButton("▶  START"); self.ss_btn.setFont(F(15, 700))
        self.ss_btn.setFixedWidth(200); self.ss_btn.setFixedHeight(48)
        self.ss_btn.setCursor(Qt.PointingHandCursor)
        self.ss_btn.clicked.connect(self._toggle)
        self._style_btn(False)
        root.addWidget(self.ss_btn, 0, Qt.AlignCenter)

        self._hits = 0; self._misses = 0; self._peak = 0

    # ── helpers ───────────────────────────────────────────────
    def _style_btn(self, running):
        nc = QColor(self.neon); ac = QColor(self.accent)
        r, g, b = nc.red(), nc.green(), nc.blue()
        r2, g2, b2 = ac.red(), ac.green(), ac.blue()
        self.ss_btn.setText("■  STOP" if running else "▶  START")
        if running:
            self.ss_btn.setStyleSheet(
                f"QPushButton{{background:rgba({r//2},{g//2},{b//2},220);color:{TEXT};"
                f"border:1px solid rgba({r},{g},{b},120);border-radius:12px;}}"
                f"QPushButton:hover{{background:rgba({r},{g},{b},200);}}")
        else:
            self.ss_btn.setStyleSheet(
                f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 rgba({r},{g},{b},200),stop:1 rgba({r2},{g2},{b2},200));"
                f"color:{TEXT};border:none;border-radius:12px;}}"
                f"QPushButton:hover{{background:rgba({r},{g},{b},255);}}")
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(22 if not running else 8)
        eff.setColor(QColor(self.neon)); eff.setOffset(0, 3)
        self.ss_btn.setGraphicsEffect(eff)

    def _set_energy(self, v):
        self._energy = max(0.0, min(self._E_MAX, v))
        pct = int(self._energy)
        self.energy_lbl.set(f"{pct}%")
        self.ebar.set_fill(self._energy / self._E_MAX)
        if pct > self._peak:
            self._peak = pct
            self.peak_c.set(f"{self._peak}%")

    def _status_for_energy(self):
        e = self._energy
        if e >= 80:  return "🔥  MAX FOCUS — incredible control!"
        if e >= 60:  return "⚡  High energy — keep it steady"
        if e >= 40:  return "✓  Good rhythm — stay calm"
        if e >= 20:  return "↓  Losing focus — slow down"
        return "✗  Too impulsive — breathe and aim"

    # ── game flow ─────────────────────────────────────────────
    def _toggle(self):
        if not self._running:
            self._running = True
            self._energy  = 30.0   # start at 30% — not zero
            self._hits    = 0; self._misses = 0; self._peak = 0
            self._clicks_this_sec = 0
            self.hits_c.set("0"); self.miss_c.set("0"); self.peak_c.set("0%")
            self._set_energy(30.0)
            self._elapsed.start()
            self.time_bar.set(1.0)
            self._style_btn(True)
            self.zone.start()
            self._ticker.start(); self._sec_t.start()
        else:
            self._end_session()

    def _on_click(self, controlled: bool):
        if not self._running: return
        self._clicks_this_sec += 1
        if controlled:
            self._hits += 1
            self.hits_c.set(str(self._hits))
            self._set_energy(self._energy + self._E_HIT_FAST)
            self.status_lbl.setText(self._status_for_energy())
        else:
            self._misses += 1
            self.miss_c.set(str(self._misses))
            self._set_energy(self._energy + self._E_MISS)
            self.status_lbl.setText("✗  Outside ring — aim carefully!")

    def _on_second(self):
        if not self._running: return
        # Impulse check: too many clicks per second?
        if self._clicks_this_sec > self._MAX_CPS:
            self._set_energy(self._energy + self._IMPULSE_PEN)
            self.status_lbl.setText("⚠  Slow down! Too rapid clicking.")
        self._clicks_this_sec = 0
        # Shrink the ring a bit each second
        self.zone.shrink()

    def _tick(self):
        if not self._running: return
        elapsed_s = self._elapsed.elapsed() / 1000.0
        remaining = max(0.0, self.DURATION - elapsed_s)
        self.time_bar.set(remaining / self.DURATION)
        # Passive energy decay
        self._set_energy(self._energy + self._E_DECAY)
        if remaining <= 0:
            self._end_session()

    def _end_session(self):
        self._ticker.stop(); self._sec_t.stop()
        self._running = False
        self.zone.stop(); self.zone.reset_ring()
        self._style_btn(False)
        self.time_bar.set(0.0)
        if self._peak > G.dopa_best:
            G.dopa_best = self._peak
            self.best_c.set(f"{G.dopa_best}%")
        self.status_lbl.setText(f"Session done!  Peak energy: {self._peak}%")

    def showEvent(self, e):
        self.best_c.set(f"{G.dopa_best}%"); super().showEvent(e)



# ══════════════════════════════════════════════════════════════
#  REACTION COLOR SHIFT
# ══════════════════════════════════════════════════════════════

# The six challenge colors: (key, display_name, neon_hex, bg_hex, dark_text)
_RCS_COLORS = [
    ("blue",   "BLUE",   "#3b82f6", "#0a1a40", False),
    ("red",    "RED",    "#ff4d4d", "#3a0000", False),
    ("green",  "GREEN",  "#10b981", "#001a10", False),
    ("purple", "PURPLE", "#8b5cf6", "#1a0040", False),
    ("orange", "ORANGE", "#f97316", "#3a1000", False),
    ("cyan",   "CYAN",   "#06b6d4", "#001a25", False),
]

class _ColorFlashZone(QWidget):
    """Full-area background that transitions to the target color."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._cur_color  = QColor(10, 11, 18)
        self._tgt_color  = QColor(10, 11, 18)
        self._lerp       = 1.0
        self._phase      = 0.0
        self._anim_t = QTimer(self); self._anim_t.setInterval(16)
        self._anim_t.timeout.connect(self._step); self._anim_t.start()

    def flash(self, hex_color):
        self._tgt_color = QColor(hex_color); self._lerp = 0.0

    def reset(self):
        self._tgt_color = QColor(10, 11, 18); self._lerp = 0.0

    def _lerp_color(self, a, b, t):
        return QColor(
            int(a.red()   + (b.red()   - a.red())   * t),
            int(a.green() + (b.green() - a.green()) * t),
            int(a.blue()  + (b.blue()  - a.blue())  * t),
        )

    def _step(self):
        self._lerp = min(1.0, self._lerp + 0.08)
        self._cur_color = self._lerp_color(self._cur_color, self._tgt_color, 0.15)
        self._phase = (self._phase + 0.025) % (math.pi * 2)
        self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        c = self._cur_color
        # Radial gradient for dramatic feel
        grd = QRadialGradient(w/2, h/2, max(w, h)*0.7)
        pulse = 0.85 + 0.15 * math.sin(self._phase)
        bright = QColor(min(255, int(c.red()*1.4*pulse)),
                        min(255, int(c.green()*1.4*pulse)),
                        min(255, int(c.blue()*1.4*pulse)))
        dark   = QColor(max(0, int(c.red()*0.25)),
                        max(0, int(c.green()*0.25)),
                        max(0, int(c.blue()*0.25)))
        grd.setColorAt(0.0, bright)
        grd.setColorAt(1.0, dark)
        pa.fillRect(0, 0, w, h, QBrush(grd))
        pa.end()


class _ColorButton(QWidget):
    """Single color choice button with neon glow."""
    def __init__(self, key, label, neon_hex, bg_hex, on_press, parent=None):
        super().__init__(parent)
        self.key      = key
        self._neon    = neon_hex
        self._bg      = bg_hex
        self._label   = label
        self._on_press = on_press
        self._hover   = False
        self._flash   = 0        # >0 = result flash (green or red)
        self._flash_ok = True
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(56)
        self._anim_t = QTimer(self); self._anim_t.setInterval(16)
        self._anim_t.timeout.connect(self._step)

    def do_flash(self, correct: bool):
        self._flash = 22; self._flash_ok = correct; self._anim_t.start()

    def _step(self):
        if self._flash > 0: self._flash -= 1
        else: self._anim_t.stop()
        self.update()

    def enterEvent(self, e): self._hover = True;  self.update()
    def leaveEvent(self, e): self._hover = False; self.update()
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton: self._on_press(self.key)

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        nc = QColor(self._neon); bg = QColor(self._bg)
        r, g, b = nc.red(), nc.green(), nc.blue()
        path = QPainterPath(); path.addRoundedRect(QRectF(0,0,w,h), 14, 14)

        # Background fill
        if self._flash > 0:
            t = self._flash / 22
            if self._flash_ok:
                fc = QColor(int(r*0.4+40*t), int(g*0.4+180*t), int(b*0.4+40*t), 240)
            else:
                fc = QColor(200, int(30*t), int(30*t), 240)
            pa.fillPath(path, fc)
        elif self._hover:
            grd = QLinearGradient(0, 0, w, 0)
            grd.setColorAt(0, QColor(r, g, b, 120))
            grd.setColorAt(1, QColor(r, g, b, 60))
            pa.fillPath(path, QBrush(grd))
        else:
            pa.fillPath(path, QColor(bg.red(), bg.green(), bg.blue(), 200))

        # Neon border
        border_a = 200 if self._hover else 100
        pa.strokePath(path, QPen(QColor(r, g, b, border_a), 2))

        # Left accent bar
        bar = QPainterPath()
        bar.addRoundedRect(QRectF(0, h*0.2, 4, h*0.6), 2, 2)
        pa.fillPath(bar, nc)

        # Label
        pa.setPen(QColor(255, 255, 255, 230)); pa.setFont(F(15, 700))
        pa.drawText(QRect(0, 0, w, h), Qt.AlignCenter, self._label)
        pa.end()


class _ReactionTimerBar(QWidget):
    """Thin bar that drains from full to empty in `window_ms` ms."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._progress = 0.0   # 0 = empty, 1 = full
        self._neon     = "#ffffff"
        self._danger   = False

    def start_drain(self, neon): self._neon = neon; self._progress = 1.0; self._danger = False
    def set(self, v):
        self._progress = max(0.0, min(1.0, v))
        self._danger   = v < 0.25
        self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); r = h//2
        pa.setBrush(QColor(255,255,255,15)); pa.setPen(Qt.NoPen)
        pa.drawRoundedRect(0, 0, w, h, r, r)
        fw = int(w * self._progress)
        if fw > 0:
            nc = QColor("#ff4444" if self._danger else self._neon)
            grd = QLinearGradient(0, 0, fw, 0)
            grd.setColorAt(0, QColor(nc.red(), nc.green(), nc.blue(), 220))
            grd.setColorAt(1, QColor(nc.red(), nc.green(), nc.blue(), 255))
            pa.setBrush(QBrush(grd)); pa.drawRoundedRect(0, 0, fw, h, r, r)
        pa.end()


class ColorShiftPage(BasePage):
    KEY      = "rcs"
    ROUNDS   = 15          # rounds per session
    WINDOW_MS = 2000       # reaction window in ms (shrinks)
    MIN_WIN_MS = 800

    def _build_content(self):
        self._running     = False
        self._round       = 0
        self._score       = 0
        self._streak      = 0
        self._target_key  = ""
        self._window_ms   = self.WINDOW_MS
        self._elapsed_r   = QElapsedTimer()   # per-round timer
        self._waiting     = False             # between rounds

        self._drain_t = QTimer(self); self._drain_t.setInterval(16)
        self._drain_t.timeout.connect(self._drain_tick)
        self._next_t  = QTimer(self); self._next_t.setSingleShot(True)
        self._next_t.timeout.connect(self._next_round)

        root = self.root

        # ── Flash zone (fills page area above buttons) ────────
        self.flash_zone = _ColorFlashZone()
        self.flash_zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.flash_zone.setMinimumHeight(160)

        # ── Overlay widgets on flash zone ─────────────────────
        flash_container = QWidget()
        flash_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        flash_container.setMinimumHeight(160)
        flash_layout = QVBoxLayout(flash_container)
        flash_layout.setContentsMargins(0, 0, 0, 0)

        # Stack flash_zone behind overlay labels
        self.flash_zone.setParent(flash_container)
        self.flash_zone.lower()

        # Round / status label
        self.round_lbl = QLabel("Press START")
        self.round_lbl.setFont(F(11, 600)); self.round_lbl.setAlignment(Qt.AlignCenter)
        self.round_lbl.setStyleSheet("color:rgba(255,255,255,200);background:transparent;")
        flash_layout.addStretch()
        flash_layout.addWidget(self.round_lbl)

        # Big color name label
        self.color_lbl = QLabel("")
        self.color_lbl.setFont(F(38, 900)); self.color_lbl.setAlignment(Qt.AlignCenter)
        self.color_lbl.setStyleSheet("color:white;background:transparent;")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(40)
        eff.setColor(QColor("white")); eff.setOffset(0,0)
        self.color_lbl.setGraphicsEffect(eff)
        flash_layout.addWidget(self.color_lbl)

        # Reaction time label
        self.react_lbl = QLabel("")
        self.react_lbl.setFont(FM(13, True)); self.react_lbl.setAlignment(Qt.AlignCenter)
        self.react_lbl.setStyleSheet("color:rgba(255,255,255,180);background:transparent;")
        flash_layout.addWidget(self.react_lbl)
        flash_layout.addStretch()

        root.addWidget(flash_container, 1)

        # ── Reaction timer bar ────────────────────────────────
        self.react_bar = _ReactionTimerBar(); self.react_bar.setFixedHeight(10)
        root.addWidget(self.react_bar); root.addSpacing(8)

        # ── Color buttons (2 rows × 3) ────────────────────────
        self._btns: dict[str, _ColorButton] = {}
        for row_i in range(2):
            row = QHBoxLayout(); row.setSpacing(8)
            for col_j in range(3):
                idx = row_i * 3 + col_j
                key, label, neon, bg, _ = _RCS_COLORS[idx]
                btn = _ColorButton(key, label, neon, bg, self._on_btn_press)
                self._btns[key] = btn
                row.addWidget(btn)
            root.addLayout(row); root.addSpacing(6)

        root.addSpacing(4)

        # ── Stat chips ────────────────────────────────────────
        chips = QHBoxLayout(); chips.setSpacing(10)
        self.score_c  = StatChip("score",   "0",               self.neon)
        self.streak_c = StatChip("streak",  "0",               self.neon)
        self.best_c   = StatChip("best",    str(G.rcs_best),   self.neon)
        for c in (self.score_c, self.streak_c, self.best_c): chips.addWidget(c)
        root.addLayout(chips); root.addSpacing(10)

        # ── Start button ──────────────────────────────────────
        self.ss_btn = QPushButton("▶  START"); self.ss_btn.setFont(F(15, 700))
        self.ss_btn.setFixedWidth(200); self.ss_btn.setFixedHeight(48)
        self.ss_btn.setCursor(Qt.PointingHandCursor)
        self.ss_btn.clicked.connect(self._toggle); self._style_btn(False)
        root.addWidget(self.ss_btn, 0, Qt.AlignCenter)

    def resizeEvent(self, e):
        # Keep flash_zone filling its parent container
        p = self.flash_zone.parent()
        if p: self.flash_zone.setGeometry(0, 0, p.width(), p.height())
        super().resizeEvent(e)

    def _style_btn(self, running):
        nc=QColor(self.neon); ac=QColor(self.accent)
        r,g,b=nc.red(),nc.green(),nc.blue(); r2,g2,b2=ac.red(),ac.green(),ac.blue()
        self.ss_btn.setText("■  STOP" if running else "▶  START")
        if running:
            self.ss_btn.setStyleSheet(f"QPushButton{{background:rgba({r//2},{g//2},{b//2},220);color:{TEXT};border:1px solid rgba({r},{g},{b},120);border-radius:12px;}}QPushButton:hover{{background:rgba({r},{g},{b},200);}}")
        else:
            self.ss_btn.setStyleSheet(f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 rgba({r},{g},{b},200),stop:1 rgba({r2},{g2},{b2},200));color:{TEXT};border:none;border-radius:12px;}}QPushButton:hover{{background:rgba({r},{g},{b},255);}}")
        eff=QGraphicsDropShadowEffect(); eff.setBlurRadius(22 if not running else 8)
        eff.setColor(QColor(self.neon)); eff.setOffset(0,3); self.ss_btn.setGraphicsEffect(eff)

    # ── game flow ─────────────────────────────────────────────
    def _toggle(self):
        if not self._running:
            self._running=True; self._round=0; self._score=0; self._streak=0
            self._window_ms=self.WINDOW_MS
            self.score_c.set("0"); self.streak_c.set("0")
            self._style_btn(True)
            self._next_round()
        else:
            self._end_session(aborted=True)

    def _next_round(self):
        if not self._running: return
        self._round += 1
        if self._round > self.ROUNDS:
            self._end_session(aborted=False); return

        # Pick a random color (different from last)
        choices = [c for c in _RCS_COLORS if c[0] != self._target_key]
        entry   = random.choice(choices)
        self._target_key = entry[0]
        _, label, neon, bg, _ = entry

        self.round_lbl.setText(f"ROUND {self._round} / {self.ROUNDS}")
        self.color_lbl.setText(label)
        self.react_lbl.setText("")

        # Style color name with matching color
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(50)
        eff.setColor(QColor(neon)); eff.setOffset(0,0)
        self.color_lbl.setGraphicsEffect(eff)
        self.color_lbl.setStyleSheet(f"color:{neon};background:transparent;")

        self.flash_zone.flash(bg)
        self.react_bar.start_drain(neon)

        self._waiting = False
        self._elapsed_r.start()
        self._drain_t.start()

    def _drain_tick(self):
        if not self._running: return
        elapsed = self._elapsed_r.elapsed()
        remaining = max(0.0, self._window_ms - elapsed)
        self.react_bar.set(remaining / self._window_ms)
        if remaining <= 0:
            self._drain_t.stop()
            self._on_timeout()

    def _on_timeout(self):
        self._streak = 0
        self.streak_c.set("0")
        self.react_lbl.setText("✗  Too slow!")
        self.color_lbl.setText("")
        self.flash_zone.reset()
        for btn in self._btns.values(): btn.do_flash(False)
        self._waiting = True
        self._next_t.start(900)

    def _on_btn_press(self, key):
        if not self._running or self._waiting: return
        self._drain_t.stop()
        react_ms = self._elapsed_r.elapsed()
        correct  = (key == self._target_key)

        self._btns[key].do_flash(correct)

        if correct:
            self._streak += 1
            # Score = base 100, bonus for speed, bonus for streak
            speed_bonus = max(0, int((self._window_ms - react_ms) / self._window_ms * 50))
            streak_bonus = (self._streak - 1) * 10
            pts = 100 + speed_bonus + streak_bonus
            self._score += pts
            self.score_c.set(str(self._score))
            self.streak_c.set(str(self._streak))
            self.react_lbl.setText(f"✓  {react_ms} ms  +{pts} pts")
            # Speed up window slightly
            self._window_ms = max(self.MIN_WIN_MS, self._window_ms - 30)
        else:
            self._streak = 0; self.streak_c.set("0")
            self.react_lbl.setText(f"✗  Wrong color!")
            self.flash_zone.reset()

        self.color_lbl.setText("")
        self._waiting = True
        self._next_t.start(700 if correct else 1000)

    def _end_session(self, aborted=False):
        self._drain_t.stop(); self._next_t.stop()
        self._running = False
        self.flash_zone.reset()
        self._style_btn(False)
        self.react_bar.set(0.0)
        self.color_lbl.setText("")
        if self._score > G.rcs_best:
            G.rcs_best = self._score; self.best_c.set(str(G.rcs_best))
        if aborted:
            self.round_lbl.setText("Stopped")
        else:
            self.round_lbl.setText(f"Done!  Score: {self._score}  •  Best: {G.rcs_best}")
        self.react_lbl.setText("")

    def showEvent(self, e):
        self.best_c.set(str(G.rcs_best)); super().showEvent(e)


# ══════════════════════════════════════════════════════════════
#  NAV + MAIN
# ══════════════════════════════════════════════════════════════
class Nav:
    def __init__(self, stack, pages): self.stack = stack; self.pages = pages
    def go(self, name):
        if name in self.pages: self.stack.setCurrentWidget(self.pages[name])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CLICKJOY ✦")
        self.setMinimumSize(400, 680); self.resize(460, 840)
        stack = QStackedWidget(); self.setCentralWidget(stack)
        nav = Nav(stack, {})
        pages = {
            "home":    HomePage(nav),
            "ranking": RankingPage(nav),
            "normal":  NormalClickPage(nav),
            "flip":    FlipCoinPage(nav),
            "switch":  SwitchPage(nav),
            "swap":    SwapClickPage(nav),
            "cpt":     ClickPerTimePage(nav),
            "swc":     StopwatchCalloutPage(nav),
            "popit":   PopItPage(nav),
            "focus":   FocusBurstPage(nav),
            "chaos":   ChaosControlPage(nav),
            "memory":  MemoryFlashPage(nav),
            "dopa":    DopamineMeterPage(nav),
            "rcs":     ColorShiftPage(nav),
        }
        nav.pages = pages
        for p in pages.values(): stack.addWidget(p)
        stack.setCurrentWidget(pages["home"])


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window,     QColor(BG))
    pal.setColor(QPalette.WindowText, QColor(TEXT))
    pal.setColor(QPalette.Base,       QColor(SURFACE))
    pal.setColor(QPalette.Text,       QColor(TEXT))
    pal.setColor(QPalette.Button,     QColor(PANEL))
    pal.setColor(QPalette.ButtonText, QColor(TEXT))
    app.setPalette(pal)
    win = MainWindow(); win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()