import sys
import os
import math
import random
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message="Failed to disconnect")

# Suppress Qt internal font warnings (point size -1 from stylesheet px->pt conversion)
try:
    from PySide6.QtCore import qInstallMessageHandler
    def _qt_msg_handler(msg_type, context, message):
        if "Point size <= 0" in message or "setPointSize" in message:
            return  # suppress
        # print all other Qt messages normally
        print(message, file=sys.stderr)
    qInstallMessageHandler(_qt_msg_handler)
except Exception:
    pass
from PySide6.QtWidgets import (QApplication, QMainWindow,
                             QVBoxLayout, QWidget, QHBoxLayout,
                             QGridLayout, QLineEdit,
                             QPushButton, QLabel,
                             QStackedWidget, QFrame,
                             QTableWidget, QTableWidgetItem,
                             QScrollArea, QProgressBar,
                             QHeaderView, QSizePolicy,
                             QGraphicsDropShadowEffect,
                             QDialog, QFileDialog, QTextEdit)
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QTimer, QRectF, Signal, QElapsedTimer, QPointF, QRectF
from PySide6.QtGui import (QFont, QAction, QColor, QPainter, QPainterPath,
                            QPen, QBrush, QRadialGradient, QLinearGradient,
                            QPolygonF)

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

# Module-level globals — mutated by apply_theme() at runtime
BG      = _DARK_PALETTE["BG"]
SURFACE = _DARK_PALETTE["SURFACE"]
PANEL   = _DARK_PALETTE["PANEL"]
EDGE    = _DARK_PALETTE["EDGE"]
TEXT    = _DARK_PALETTE["TEXT"]
DIM     = _DARK_PALETTE["DIM"]
GHOST   = _DARK_PALETTE["GHOST"]

# Dark neon accent colours (vivid, for dark backgrounds)
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
ACCENT = "#3b82f6"          # default: blue

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

# Light neon accent colours (slightly deeper for readability on light bg)
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

NEON = dict(_DARK_NEON)  # mutable copy — updated by apply_theme()


def apply_theme(is_dark: bool) -> None:
    """Mutate all module-level palette globals for dark or light mode.

    Called at runtime when the user flips the theme toggle.  All widgets
    that read these globals in their paintEvent() will automatically pick
    up the new colours on the next repaint.  Widgets that baked the
    palette into a setStyleSheet() call at construction time must call
    their own refresh_theme() method separately.

    Args:
        is_dark (bool): True -> dark neon palette; False -> light palette.
    """
    import sys as _sys
    _mod = _sys.modules[__name__]
    src = _DARK_PALETTE if is_dark else _LIGHT_PALETTE
    for _k, _v in src.items():
        globals()[_k] = _v
        setattr(_mod, _k, _v)
    neon_src = _DARK_NEON if is_dark else _LIGHT_NEON
    NEON.clear()
    NEON.update(neon_src)

# ══════════════════════════════════════════════════════════════
#  FONT SYSTEM  — mono for numbers, geometric for labels
# ══════════════════════════════════════════════════════════════
def F(size=14, weight=400):
    size = max(1, int(size))  # guard: point size must be > 0
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
    size = max(1, int(size))  # guard: point size must be > 0
    f = QFont()
    for name in ("Consolas", "Courier New", "monospace"):
        f.setFamily(name); break
    f.setPointSize(size)
    f.setBold(bold)
    return f


def _make_back_btn(on_click):
    """Small square back button matching PageHeader style."""
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

# ══════════════════════════════════════════════════════════════
#  TOAST NOTIFICATION
# ══════════════════════════════════════════════════════════════
class Toast(QWidget):
    """Floating neon toast that fades in, holds, then fades out."""
    def __init__(self, parent):
        """Initialise the instance.

        Args:
            parent (QWidget): Parent widget that owns this toast.
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._alpha = 0; self._phase = "in"; self._hold = 0
        self._text = ""; self._color = "#3b82f6"
        self._t = QTimer(self); self._t.setInterval(16)
        self._t.timeout.connect(self._step)
        self.setFixedHeight(44); self.hide()

    def show_msg(self, text, color="#3b82f6", hold_ms=1800):
        """Execute show msg.

        Args:
            text (str): Message string to display.
                    color (str): Neon hex accent colour for border and text.
                    hold_ms (int): Milliseconds to hold before fading out.

        Raises:
            None

        Examples:
            >>> toast.show_msg('✓ Saved', '#3b82f6', 1500)
        """
        self._text = text; self._color = color
        self._alpha = 0; self._phase = "in"
        self._hold_target = hold_ms // 16
        self._hold = 0
        self._reposition()
        self.show(); self._t.start()

    def _reposition(self):
        """Re-centre the toast over the parent window.
        """
        p = self.parent()
        if p:
            w = min(p.width() - 40, 400)
            self.setFixedWidth(w)
            self.move((p.width() - w) // 2, p.height() - 70)

    def resizeEvent(self, e): self._reposition()

    def _step(self):
        """Advance internal state by one timer tick.
        """
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
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
        if not self._text: return
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        nc = QColor(self._color); a = self._alpha
        # Background
        bg = QPainterPath(); bg.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 12, 12)
        pa.fillPath(bg, QColor(22, 26, 38, int(a * 0.92)))
        # Border
        pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), a), 1.5))
        pa.setBrush(Qt.NoBrush); pa.drawRoundedRect(QRectF(1, 1, self.width()-2, self.height()-2), 12, 12)
        # Text
        pa.setFont(F(10, 600)); pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), a))
        pa.drawText(QRect(0, 0, self.width(), self.height()), Qt.AlignCenter, self._text)
        pa.end()


_toast_instance: "Toast | None" = None

def show_toast(parent_window, text, color="#3b82f6", hold_ms=1800):
    """Display a floating toast notification on the root window.

    Args:
        parent_window (QWidget): Any widget in the hierarchy; the toast
            is parented to the top-level window automatically.
        text (str): Message to display inside the toast.
        color (str): Hex neon accent colour for border and text.
        hold_ms (int): Milliseconds to hold the toast before fading out.

    Returns:
        None

    Examples:
        >>> show_toast(self, "✓  Saved", "#3b82f6", 1500)
    """
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


# ══════════════════════════════════════════════════════════════
#  BACKGROUND: GRID + SCANLINES + NEON ORBS
# ══════════════════════════════════════════════════════════════
class NeonBackground(QWidget):
    """Animated background widget: dot-grid, two pulsing neon orbs, and scanlines.

    Colour scheme driven by a NEON palette key.
    """
    def __init__(self, key, parent=None):
        """Initialise the instance.

        Args:
            key (str): NEON palette key for orb/grid colour.
                    parent (QWidget | None): Optional parent widget.
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.key = key
        self._phase = random.uniform(0, math.pi * 2)
        self._t = QTimer(self); self._t.setInterval(40); self._t.timeout.connect(self._step)
        self._t.start()

    def _step(self):
        """Advance internal state by one timer tick.
        """
        self._phase += 0.012
        self.update()

    def paintEvent(self, ev):
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
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
        """Initialise the instance.

        Args:
            neon (str): Hex accent colour for the left-edge bar.
                    parent (QWidget | None): Optional parent widget.
        """
        super().__init__(parent)
        self._neon  = neon_color
        self._r     = radius
        self._bar   = bar
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, ev):
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
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
        """Initialise the instance.

        Args:
            neon_color (str): Hex colour of the brackets.
                    radius (int): Corner radius in pixels.
                    bar (int): Bracket arm thickness.
                    parent (QWidget | None): Optional parent widget.
        """
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
        """Advance internal state by one timer tick.
        """
        self._phase = (self._phase + 0.04) % (math.pi * 2)
        self.update()

    def paintEvent(self, ev):
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
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
    """Large engraved numeric display with neon drop-shadow.

    Renders via QPainter for a custom glowing text effect.
    """
    def __init__(self, neon, size=72, parent=None):
        """Initialise the instance.

        Args:
            neon (str): Hex accent/glow colour.
                    size (int): Font size in points.
                    parent (QWidget | None): Optional parent widget.
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._neon = neon
        self._size = size
        self._text = "0"
        self.setMinimumHeight(size + 20)

    def set(self, text): self._text = str(text); self.update()
    def paintEvent(self, ev):
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
        pa = QPainter(self)
        pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        nc = QColor(self._neon)

        # Shadow layer (offset = depth illusion)
        pa.setPen(QColor(0, 0, 0, 120))
        pa.setFont(FM(self._size, True))
        pa.drawText(QRect(3, 3, w, h), Qt.AlignCenter, self._text)

        # Glow layer (soft multi-offset copy)
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
    """QLabel subclass that applies a QGraphicsDropShadowEffect for a neon glow.

    Call set(text) to update the label text at runtime.
    """
    def __init__(self, text, color, size=52, mono=False, parent=None):
        """Initialise the instance.

        Args:
            text (str): Initial label text.
                    color (str): Neon hex glow colour.
                    size (int): Font size in points.
                    mono (bool): Use monospace font if True.
                    parent (QWidget | None): Optional parent widget.
        """
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
    """Small rounded chip showing a label and a numeric value in neon colour.

    Call set(value) to update the displayed value.
    """
    def __init__(self, label, value, neon, parent=None):
        """Initialise the instance.

        Args:
            label (str): Chip label text shown in dim colour.
                    value (int | str): Initial numeric value.
                    neon (str): Hex accent colour.
                    parent (QWidget | None): Optional parent widget.
        """
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
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
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


# ══════════════════════════════════════════════════════════════
#  THE BIG TAP BUTTON
# ══════════════════════════════════════════════════════════════
class NeonTapButton(QWidget):
    """Large circular tap/click button with press, ripple, and pulse animations.

    Callers pass a callback via the constructor.
    """
    clicked = None

    def __init__(self, label, neon, accent, size=200, parent=None):
        """Initialise the instance.

        Args:
            label (str): Text drawn inside the button.
                    neon (str): Hex ring/glow colour.
                    accent (str): Hex fill colour on press.
                    size (int): Diameter of the circular button.
                    parent (QWidget | None): Optional parent widget.
        """
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
        """Advance the animation by one timer step.
        """
        if self._press  > 0: self._press  = max(0, self._press  - 0.07)
        if self._ripple > 0: self._ripple = max(0, self._ripple - 0.035)
        self._pulse = (self._pulse + 0.025) % (math.pi * 2)
        self.update()

    def mousePressEvent(self, e):
        """Handle mouse press.

        Args:
            e (QMouseEvent): Mouse event from Qt.
        """
        if e.button() == Qt.LeftButton:
            self._press = 1.0; self._ripple = 1.0
            if self.clicked: self.clicked()

    def enterEvent(self, e): self._hover = True
    def leaveEvent(self, e): self._hover = False
    def paintEvent(self, ev):
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w = self.width(); cx = cy = w // 2
        nc = QColor(self.neon); ac = QColor(self.accent)
        br = w // 2 - 6

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
        pa.fillPath(disc, QColor(14, 16, 24, 245))
        pa.strokePath(disc, QPen(QColor(nc.red(), nc.green(), nc.blue(), 40), 12))
        pa.strokePath(disc, QPen(nc, 2))
        inner = QRadialGradient(cx, cy - pressed_r // 4, pressed_r // 2)
        inner.setColorAt(0.0, QColor(nc.red(), nc.green(), nc.blue(), 30 + int(20 * self._press)))
        inner.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.fillPath(disc, QBrush(inner))

        # ── Label ─────────────────────────────────────────────
        pa.setPen(QColor(0, 0, 0, 160))
        pa.setFont(F(w // 5, 700))
        pa.drawText(QRect(2, 2, w, w), Qt.AlignCenter, self.label)
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
    """Particle burst overlay widget.

    Call burst(x, y, color, n) to spawn n sparks at position (x, y).
    Each _Spark instance is stepped every frame until its lifetime expires.
    """
    def __init__(self, parent=None):
        """Initialise the instance.

        Args:
            parent (QWidget | None): Optional parent widget.
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._sparks = []
        self._t = QTimer(self); self._t.setInterval(16); self._t.timeout.connect(self._step)

    def burst(self, x, y, color, n=24):
        """Execute burst.

        Args:
            x (int): X position for the burst origin.
                    y (int): Y position for the burst origin.
                    color (str): Hex colour of the sparks.
                    n (int): Number of sparks to spawn.

        Examples:
            >>> particles.burst(100, 200, '#f59e0b', 24)
        """
        self._sparks += [_Spark(x, y, color) for _ in range(n)]
        self._t.start()

    def _step(self):
        """Advance internal state by one timer tick.
        """
        live = []
        for s in self._sparks:
            s.x += s.vx; s.y += s.vy; s.vy += 0.22; s.vx *= 0.97; s.life -= s.decay
            if s.life > 0: live.append(s)
        self._sparks = live
        if not live: self._t.stop()
        self.update()

    def paintEvent(self, ev):
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
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


# ══════════════════════════════════════════════════════════════
#  NEON TOGGLE  (inspired by industrial switches)
# ══════════════════════════════════════════════════════════════
class NeonToggle(QWidget):
    """Industrial-style on/off toggle switch drawn with QPainter.

    Fires the toggled(bool) callback on state change.
    """
    TW = 160; TH = 44; TD = 36

    def __init__(self, neon, accent, parent=None):
        """Initialise the instance.

        Args:
            neon (str): Hex colour of the ON state.
                    accent (str): Hex colour of the knob.
                    parent (QWidget | None): Optional parent widget.
        """
        super().__init__(parent)
        self.neon = neon; self.accent = accent
        self.setFixedSize(self.TW, self.TH + 24)
        self.setCursor(Qt.PointingHandCursor)
        self._on = False; self._pos = 0.0
        self._t = QTimer(self); self._t.setInterval(12); self._t.timeout.connect(self._anim)
        self.toggled = None

    def set_state(self, on):
        """Execute set state.

        Args:
            on (bool): True to turn the toggle ON, False for OFF.

        Examples:
            >>> toggle.set_state(True)
        """
        self._on = on; self._pos = 1.0 if on else 0.0; self.update()

    def _anim(self):
        """Drive the toggle slide animation.
        """
        target = 1.0 if self._on else 0.0
        self._pos += (target - self._pos) * 0.22
        if abs(self._pos - target) < 0.004: self._pos = target; self._t.stop()
        self.update()

    def mousePressEvent(self, e):
        """Handle mouse press.

        Args:
            e (QMouseEvent): Mouse event from Qt.
        """
        self._on = not self._on; self._t.start()
        if self.toggled: self.toggled()

    def paintEvent(self, ev):
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
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


# ══════════════════════════════════════════════════════════════
#  NEON RING  (countdown / progress)
# ══════════════════════════════════════════════════════════════
class NeonRing(QWidget):
    """Circular countdown / progress ring drawn with QPainter.

    Call set(progress, text) where progress is 0.0 to 1.0.
    """
    def __init__(self, neon, accent, size=200, parent=None):
        """Initialise the instance.

        Args:
            neon (str): Hex colour of the ring arc.
                    accent (str): Hex colour for the tip glow.
                    size (int): Diameter of the ring widget.
                    parent (QWidget | None): Optional parent widget.
        """
        super().__init__(parent)
        self.neon = neon; self.accent = accent
        self.setFixedSize(size, size)
        self._progress = 1.0; self._text = "—"
        self._phase = 0.0
        self._t = QTimer(self); self._t.setInterval(40); self._t.timeout.connect(self._tick)
        self._t.start()

    def _tick(self): self._phase = (self._phase + 0.03) % (math.pi * 2); self.update()
    def set(self, progress, text):
        """Update the ring's fill fraction and centre label.

        Args:
            progress (float): Fill level from 0.0 (empty) to 1.0 (full).
                Values are clamped automatically.
            text (str): Text drawn in the centre of the ring.

        Returns:
            None

        Examples:
            >>> ring.set(0.75, "15s")
        """
        self._progress = max(0.0, min(1.0, progress)); self._text = text; self.update()

    def paintEvent(self, ev):
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
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


# ══════════════════════════════════════════════════════════════
#  COIN DISC
# ══════════════════════════════════════════════════════════════
class CoinParticle:
    def __init__(self, cx, cy, color):
        """Initialise the instance.

        Args:
            cx (int): X origin of the burst.
                    cy (int): Y origin of the burst.
                    color (str): Hex particle colour.
        """
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
        """Execute step.

        Returns:
            bool: True while the particle is still alive.
        """
        self.x += self.vx; self.y += self.vy
        self.vy += 0.35; self.vx *= 0.94
        self.life -= 1

    def alive(self): return self.life > 0
    def alpha(self): return int(255 * (self.life / self.max_life))
class CoinDisc(QWidget):
    """Animated coin widget cycling through SPIN, REVEAL, and GLOW phases.

    Call flip_to(side) where side is 'H' or 'T'.
    Emits result_landed Signal when the flip completes.
    """
    result_landed = Signal()

    _IDLE   = "idle"
    _SPIN   = "spin"
    _REVEAL = "reveal"
    _GLOW   = "glow"

    def __init__(self, parent=None):
        """Initialise the instance.

        Args:
            parent (QWidget | None): Optional parent widget.
        """
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
        """Start the coin-flip animation toward the given side.

        Transitions the widget through SPIN -> REVEAL -> GLOW phases.
        Emits ``result_landed`` Signal when the SPIN phase ends.

        Args:
            side (str): "H" for Heads or "T" for Tails.

        Returns:
            None

        Examples:
            >>> coin.flip_to("H")
        """
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
        """Execute burst particles.
        """
        cx = self.width() // 2; cy = self.height() // 2
        nc = QColor(self._neon); ac = QColor(self._accent)
        for _ in range(28):
            c = nc if random.random() > 0.4 else ac
            self._particles.append(CoinParticle(cx, cy, c))

    def _step(self):
        """Advance internal state by one timer tick.
        """
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
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
        pa = QPainter(self)
        pa.setRenderHint(QPainter.Antialiasing)
        s  = self.width()
        cx = cy = s // 2
        r  = s // 2 - 14
        nc = QColor(self._neon)
        nr, ng, nb = nc.red(), nc.green(), nc.blue()

        # ── Particles ─────────────────────────────────────────────
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

        # ── Transform ─────────────────────────────────────────────
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


# ══════════════════════════════════════════════════════════════
#  PAGE HEADER
# ══════════════════════════════════════════════════════════════
class PageHeader(QWidget):
    """Reusable page header: back button, neon badge icon, and page title.

    The back button calls nav.go('home') on click.
    Used by all 12 game pages for consistent navigation.
    """
    def __init__(self, key, nav, parent=None):
        """Initialise the instance.

        Args:
            key (str): NEON palette key for the accent colour.
                    nav (object): Navigation object with a go() method.
                    parent (QWidget | None): Optional parent widget.
        """
        super().__init__(parent)
        self.setFixedHeight(62)
        neon = NEON[key][0]
        row = QHBoxLayout(self); row.setContentsMargins(10, 0, 0, 0); row.setSpacing(0)
        row.setAlignment(Qt.AlignVCenter)

        # Custom painted back button — arrow always perfectly centered
        class _BackBtn(QWidget):
            def __init__(self, neon, nav_fn, parent=None):
                """Initialise the instance.

                Args:
                    key (str): NEON palette key for the accent colour.
                            nav (object): Navigation object with a go() method.
                            parent (QWidget | None): Optional parent widget.
                """
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
                # Box
                path = QPainterPath(); path.addRoundedRect(QRectF(1,1,42,42), 11, 11)
                pa.fillPath(path, QColor(nc.red(),nc.green(),nc.blue(), 30 if self._hover else 0))
                pa.fillPath(path, QColor(PANEL))
                pa.strokePath(path, QPen(QColor(nc.red(),nc.green(),nc.blue(), 200 if self._hover else 90), 1.5))
                # Arrow <
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


class StyledInput(QLineEdit):
    """QLineEdit subclass styled with a neon focus border.

    Inherits all QLineEdit behaviour; appearance is driven by the neon colour.
    """
    def __init__(self, text, neon):
        """Initialise the instance.

        Args:
            neon (str): Hex accent colour for the focus border.
                    parent (QWidget | None): Optional parent widget.
        """
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
    """Build the global Qt stylesheet from a palette dict."""
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

# ==================== Data ====================
DATA_FILE = "data.csv"
ALL_DB_FIELDS = ["normal","flip","switch","pop","swap","cpm","stop",
                 "focus","chaos","memory","dopa","rcs"]

GAME_LIST = [
    ("normal", "Normal Click",   "⬡", "tap as fast as you can"),
    ("flip",   "Flip Coin",      "◆", "heads or tails?"),
    ("switch", "Switch",         "▣", "toggle the switch"),
    ("swap",   "Swap Click",     "◎", "chase the target"),
    ("cpm",    "Click per Time", "◷", "race the clock"),
    ("stop",   "Stopwatch",      "◉", "hit the exact time"),
    ("pop",    "Pop It",         "⬤", "pop every bubble fast!"),
    ("focus",  "Focus Burst",    "◈", "click only the right shape"),
    ("chaos",  "Chaos Control",  "⚡", "find the real button!"),
    ("memory", "Memory Flash",   "◫", "remember the pattern"),
    ("dopa",   "Dopamine Meter", "◑", "stay controlled, fill meter"),
    ("rcs",    "Color Shift",    "◐", "match the color — react fast"),
]

ICONS = {g[0]: g[2] for g in GAME_LIST}
NAMES = {g[0]: g[1] for g in GAME_LIST}

# ==================== DataManager ====================
CSV_FIELDS = ["user","password","uid","total","normal","flip","switch","pop",
              "swap","cpm","stop","focus","chaos","memory","dopa","rcs","reward","bio","avatar"]
INT_FIELDS = {"total","normal","flip","switch","pop","swap","cpm","stop",
              "focus","chaos","memory","dopa","rcs"}

class DataManager:
    """Persistent data layer backed by a CSV file (data.csv).

    Provides CRUD operations for user accounts, scores, bio, avatar,
    and rewards.  All methods read/write the CSV via the standard csv module.

    Attributes:
        CSV_FIELDS (list): Ordered column names written to the CSV header.
        INT_FIELDS (set): Fields that are parsed as integers on read.

    Examples:
        >>> db = DataManager()
        >>> db.register("alice", "pass123")
        True
        >>> db.login("alice", "pass123")["user"]
        'alice'
    """
    def __init__(self):
        """Initialise the instance.
        """
        import csv as _csv
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
                _csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()

    def _read_all(self):
        """Execute read all.

        Returns:
            list[dict]: All user records as dicts with typed fields.

        Examples:
            >>> db._read_all()
                    [{'user': 'alice', 'uid': '00000001', ...}]
        """
        import csv as _csv
        rows = []
        try:
            with open(DATA_FILE, "r", newline="", encoding="utf-8") as f:
                reader = _csv.DictReader(f)
                for row in reader:
                    r = dict(row)
                    for k in INT_FIELDS:
                        try: r[k] = int(r.get(k) or 0)
                        except ValueError: r[k] = 0
                    rw = r.get("reward", "")
                    r["reward"] = [x for x in rw.split("|") if x] if rw else []
                    r.setdefault("bio", "")
                    r.setdefault("avatar", "")
                    rows.append(r)
        except Exception:
            pass
        return rows

    def _write_all(self, rows):
        """Execute write all.

        Args:
            rows (list[dict]): Sequence of user record dicts to persist.

        Raises:
            OSError: If the CSV file cannot be opened for writing.
        """
        import csv as _csv
        with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
            writer = _csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
            writer.writeheader()
            for r in rows:
                out = dict(r)
                out["reward"] = "|".join(r.get("reward", []))
                writer.writerow(out)

    def _next_uid(self, rows):
        """Execute next uid.

        Args:
            rows (list[dict]): Current list of user records.

        Returns:
            str: Zero-padded 8-digit UID string.

        Examples:
            >>> db._next_uid([])
                    '00000001'
        """
        if not rows: return "00000001"
        return str(max(int(r["uid"]) for r in rows) + 1).zfill(8)

    def register(self, username, password):
        """Register a new user account.

        Args:
            username (str): Desired username (must be unique).
            password (str): Plain-text password.

        Returns:
            bool: True if registration succeeded, False if username already exists.

        Examples:
            >>> db.register("bob", "secret")
            True
            >>> db.register("bob", "secret")
            False
        """
        rows = self._read_all()
        if any(r["user"] == username for r in rows): return False
        rows.append({
            "user": username, "password": password, "uid": self._next_uid(rows),
            "total": 0, "normal": 0, "flip": 0, "switch": 0, "pop": 0, "swap": 0,
            "cpm": 0, "stop": 0, "focus": 0, "chaos": 0, "memory": 0,
            "dopa": 0, "rcs": 0, "reward": [], "bio": "", "avatar": ""
        })
        self._write_all(rows); return True

    def login(self, username, password):
        """Authenticate a user with username and password.

        Args:
            username (str): The account username.
            password (str): The account password.

        Returns:
            dict | None: User record dict on success, None if credentials are wrong.

        Examples:
            >>> db.login("alice", "pass123")["uid"]
            '00000001'
            >>> db.login("alice", "wrong") is None
            True
        """
        for r in self._read_all():
            if r["user"] == username and r["password"] == password: return r
        return None

    def get_user(self, username):
        for r in self._read_all():
            if r["user"] == username: return r
        return None

    def update_score(self, username, field, value):
        """Update a numeric score field for a user and recalculate total.

        Args:
            username (str): The target user.
            field (str): Score field name (e.g. "normal", "flip").
            value (int): New score value.

        Returns:
            None

        Raises:
            KeyError: If field is not a valid score column.

        Examples:
            >>> db.update_score("alice", "normal", 150)
        """
        rows = self._read_all()
        for r in rows:
            if r["user"] == username:
                r[field] = value
                r["total"] = sum(r.get(f, 0) for f in ALL_DB_FIELDS)
                break
        self._write_all(rows)

    def update_bio(self, username, bio):
        """Save a user's bio text to the CSV.

        Args:
            username (str): The target user.
            bio (str): New bio text (commas are preserved via CSV quoting).

        Returns:
            None

        Examples:
            >>> db.update_bio("alice", "I love clicking things!")
        """
        rows = self._read_all()
        for r in rows:
            if r["user"] == username:
                r["bio"] = bio; break
        self._write_all(rows)

    def update_avatar(self, username, avatar_path):
        """Save the file path of a user's profile picture to the CSV.

        Args:
            username (str): The target user.
            avatar_path (str): Absolute or relative path to the image file.

        Returns:
            None

        Examples:
            >>> db.update_avatar("alice", "C:/photos/me.png")
        """
        rows = self._read_all()
        for r in rows:
            if r["user"] == username:
                r["avatar"] = avatar_path; break
        self._write_all(rows)

    def add_reward(self, username, reward_id):
        """Add a reward ID to a user's reward list (no duplicates).

        Args:
            username (str): The target user.
            reward_id (str): Unique reward identifier (e.g. "200flip").

        Returns:
            None

        Examples:
            >>> db.add_reward("alice", "200flip")
            >>> db.has_reward("alice", "200flip")
            True
        """
        rows = self._read_all()
        for r in rows:
            if r["user"] == username:
                if reward_id not in r["reward"]: r["reward"].append(reward_id)
                break
        self._write_all(rows)

    def has_reward(self, username, reward_id):
        """Execute has reward.

        Args:
            username (str): The target user.
                    reward_id (str): Reward identifier to check.

        Returns:
            bool: True if the user owns the reward, False otherwise.

        Examples:
            >>> db.has_reward('alice', '200flip')
                    True
        """
        u = self.get_user(username)
        return bool(u) and reward_id in u["reward"]

    def get_all_scores(self, field):
        """Return all users sorted by a score field descending.

        Args:
            field (str): Score field to sort by (e.g. "total", "flip").

        Returns:
            list[tuple[str, int]]: List of (username, score) pairs,
            highest score first.

        Examples:
            >>> db.get_all_scores("flip")
            [("alice", 206), ("bob", 50)]
        """
        rows = self._read_all()
        result = [(r["user"], r.get(field, 0)) for r in rows]
        result.sort(key=lambda x: x[1], reverse=True)
        return result

    def get_reward_percent(self, reward_id):
        """Execute get reward percent.

        Args:
            reward_id (str): Reward identifier to measure.

        Returns:
            float: Percentage (0–100) of users who own the reward.

        Examples:
            >>> db.get_reward_percent('200flip')
                    33.33
        """
        rows = self._read_all()
        if not rows: return 0.0
        return sum(1 for r in rows if reward_id in r["reward"]) / len(rows) * 100.0


# ==================== GameCard ====================
class GameCard(QFrame):
    """Horizontal list-row game card for the scrollable game select list.

    Shows neon icon box, game name, subtitle, and a chevron arrow.
    Fires on_click(field) when clicked.
    """
    def __init__(self, field, name, icon, subtitle, on_click, parent=None):
        """Initialise the instance."""
        super().__init__(parent)
        self.field = field
        self.on_click = on_click
        self._selected = False
        neon, glow, *_ = NEON.get(field, ("#3b82f6","#0f2a5c","",""))
        self._neon = neon; self._glow = glow
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("GameCard")

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 10, 14, 10); row.setSpacing(14)

        # Neon icon box
        self.icon_box = QLabel(icon)
        self.icon_box.setFixedSize(52, 52)
        self.icon_box.setAlignment(Qt.AlignCenter)
        self.icon_box.setFont(F(22))
        self.icon_box.setStyleSheet(f"""
            QLabel {{
                background: {glow};
                border: 2px solid {neon};
                border-radius: 12px;
                color: {neon};
            }}
        """)
        row.addWidget(self.icon_box)

        # Text
        txt = QVBoxLayout(); txt.setSpacing(2)
        self.name_lbl = QLabel(name)
        self.name_lbl.setFont(F(13, 700))
        self.name_lbl.setStyleSheet("background:transparent;border:none;")
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setFont(F(9))
        self.sub_lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;")
        txt.addWidget(self.name_lbl); txt.addWidget(self.sub_lbl)
        row.addLayout(txt, stretch=1)

        # Chevron
        self.chevron = QLabel("›")
        self.chevron.setFont(F(18, 700))
        self.chevron.setStyleSheet(f"color:{neon};background:transparent;border:none;")
        row.addWidget(self.chevron)

        self._set_style(False)

    def _set_style(self, active):
        neon, glow = self._neon, self._glow
        # Parse neon hex → rgba for dimmed subtitle
        r = int(neon[1:3],16); g = int(neon[3:5],16); b = int(neon[5:7],16)
        neon_dim = f"rgba({r},{g},{b},160)"
        if active:
            self.setStyleSheet(f"#GameCard{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {glow},stop:1 {PANEL});border:2px solid {neon};border-radius:12px;}}")
            self.name_lbl.setStyleSheet(f"color:#ffffff;background:transparent;border:none;")
            self.sub_lbl.setStyleSheet(f"color:{neon_dim};background:transparent;border:none;")
            self.chevron.setStyleSheet(f"color:{neon};background:transparent;border:none;")
        else:
            self.setStyleSheet(f"#GameCard{{background:{PANEL};border:1px solid {EDGE};border-radius:12px;}}")
            self.name_lbl.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
            self.sub_lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;")
            self.chevron.setStyleSheet(f"color:{neon};background:transparent;border:none;")

    def set_selected(self, val):
        """Set the card's selected/highlighted state."""
        self._selected = val; self._set_style(val)

    def enterEvent(self, e): self._set_style(True)
    def leaveEvent(self, e): self._set_style(self._selected)
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self.on_click(self.field)

    def paintEvent(self, ev):
        """Draw neon left bar + glow on top of base stylesheet."""
        super().paintEvent(ev)
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        nc = QColor(self._neon); r, g, b = nc.red(), nc.green(), nc.blue()
        w, h = self.width(), self.height()
        bar_w = 4; bar_r = 2
        bar_x = 0; bar_y = int(h * 0.15); bar_h = int(h * 0.70)

        # Glow spread (radial from bar)
        glow = QRadialGradient(bar_w, h // 2, 80)
        glow.setColorAt(0.0, QColor(r, g, b, 55))
        glow.setColorAt(1.0, QColor(r, g, b, 0))
        pa.setBrush(QBrush(glow)); pa.setPen(Qt.NoPen)
        pa.drawRect(0, 0, 90, h)

        # Neon bar
        bar_path = QPainterPath()
        bar_path.addRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), bar_r, bar_r)
        pa.fillPath(bar_path, nc)
        pa.end()


# ==================== DetailPanel ====================
class DetailPanel(QFrame):
    """Right-hand detail panel in the main menu.

    Shows the selected game description, the current user score,
    and a PLAY button that navigates to the corresponding game page.
    """
    def __init__(self, main_window, parent=None):
        """Initialise the instance.

        Args:
            main_window (MainWindow): Root window for navigation and DB access.
        """
        super().__init__(parent)
        self.main_window = main_window
        self._current_field = "normal"
        self.setFixedWidth(240)
        self.setObjectName("DetailPanel")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18,18,18,18); lay.setSpacing(10)

        self.icon_lbl = QLabel("⬡")
        self.icon_lbl.setFont(F(40))
        self.icon_lbl.setAlignment(Qt.AlignLeft)
        self.icon_lbl.setStyleSheet("background:transparent;border:none;")
        lay.addWidget(self.icon_lbl)

        self.name_lbl = QLabel("NORMAL CLICK")
        self.name_lbl.setFont(FM(13, bold=True))
        self.name_lbl.setWordWrap(True)
        self.name_lbl.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        lay.addWidget(self.name_lbl)

        self.sub_lbl = QLabel("tap as fast as you can")
        self.sub_lbl.setFont(F(8))
        self.sub_lbl.setWordWrap(True)
        self.sub_lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;")
        lay.addWidget(self.sub_lbl)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{EDGE};border:none;"); lay.addWidget(sep)

        score_row = QHBoxLayout()
        sk = QLabel("My Score"); sk.setFont(F(8))
        sk.setStyleSheet(f"color:{DIM};background:transparent;border:none;")
        self.score_val = QLabel("—")
        self.score_val.setFont(FM(12, bold=True))
        self.score_val.setAlignment(Qt.AlignRight)
        self.score_val.setStyleSheet(f"color:{GHOST};background:transparent;border:none;")
        score_row.addWidget(sk); score_row.addStretch(); score_row.addWidget(self.score_val)
        lay.addLayout(score_row)
        lay.addStretch()

        self.play_btn = QPushButton("▶   PLAY")
        self.play_btn.setFixedHeight(40)
        self.play_btn.setFont(FM(10, bold=True))
        self.play_btn.setCursor(Qt.PointingHandCursor)
        lay.addWidget(self.play_btn)
        self.update_game("normal","Normal Click","⬡","tap as fast as you can")

    def update_game(self, field, name, icon, subtitle):
        self._current_field = field
        neon, glow, *_ = NEON.get(field, ("#3b82f6","#0f2a5c","",""))
        self.setStyleSheet(f"#DetailPanel{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {glow},stop:0.6 {SURFACE},stop:1 {PANEL});border:1px solid {neon}55;border-radius:14px;}}")
        self.icon_lbl.setText(icon)
        self.icon_lbl.setStyleSheet(f"color:{neon};background:transparent;border:none;")
        self.name_lbl.setText(name.upper())
        self.name_lbl.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        self.sub_lbl.setText(subtitle)
        self.sub_lbl.setStyleSheet(f"color:{neon}99;background:transparent;border:none;")
        self.play_btn.setStyleSheet(f"""
            QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {glow},stop:1 {neon}44);
            border:1px solid {neon};border-radius:9px;color:{neon};letter-spacing:2px;}}
            QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {glow},stop:1 {neon}77);}}
            QPushButton:pressed{{background:{neon}33;}}
        """)
        try: self.play_btn.clicked.disconnect()
        except (RuntimeError, TypeError): pass
        self.play_btn.clicked.connect(self._play)
        self.refresh_score()

    def refresh_score(self):
        username = self.main_window.current_user
        if not username:
            self.score_val.setText("—"); return
        u = self.main_window.db.get_user(username)
        if u:
            val = u.get(self._current_field, 0)
            neon, *_ = NEON.get(self._current_field, ("#3b82f6","#0f2a5c","",""))
            self.score_val.setText(f"{val:,}")
            self.score_val.setStyleSheet(f"color:{neon};background:transparent;border:none;")

    def _play(self):
        username = self.main_window.current_user
        if not username: return
        self.main_window.go_game(self._current_field)


# ==================== MainWindow ====================
class MainWindow(QMainWindow):
    """Top-level application window.

    Owns a QStackedWidget with all pages (login, menus, 12 games),
    a HamburgerMenuPage overlay, a QToolBar, and a QStatusBar.
    Central routing is done via go_to(index) and go_game(key).
    """
    def __init__(self):
        """Initialise the instance.
        """
        super().__init__()
        self.setWindowTitle("Clickjoy")
        self.resize(920, 700)
        self.db = DataManager()
        self.current_user = None
        self.container = QWidget()
        self.setCentralWidget(self.container)
        self.container.setFixedSize(920, 700)
        self.stack = QStackedWidget(self.container)
        self.stack.setGeometry(0,0,920,700)

        self.login_page   = LoginPage(self)
        self.main_menu    = MainMenuPage(self)
        self.ranking_page = RankingPage(self)
        self.task_page    = TaskPage(self)
        self.reward_page  = RewardPage(self)
        self.setting_page = SettingPage(self)
        self.profile_page = ProfilePage(self)

        for p in [self.login_page,self.main_menu,self.ranking_page,
                  self.task_page,self.reward_page,self.setting_page,self.profile_page]:
            self.stack.addWidget(p)

        self.ham_menu = HamburgerMenuPage(self.container, self)
        self.ham_menu.setGeometry(-280,0,280,700)
        self.ham_open = False

        # Game pages (index 7+)
        _game_classes = [
            NormalClickPage, FlipCoinPage,    SwitchPage,       SwapClickPage,
            ClickPerTimePage, StopwatchPage,  PopItPage,        FocusBurstPage,
            ChaosControlPage, MemoryFlashPage, DopamineMeterPage, ColorShiftPage,
        ]
        self._game_pages = {}
        for cls in _game_classes:
            page = cls(self)
            self.stack.addWidget(page)
            self._game_pages[cls.KEY] = page

        self.stack.setCurrentIndex(0)

        # ── Toolbar ──────────────────────────────────────────
        from PySide6.QtWidgets import QToolBar
        self._tb = QToolBar("Quick Access"); self._tb.setMovable(False)
        self._tb.setStyleSheet(f"""
            QToolBar {{ background:{PANEL}; border-bottom:1px solid {EDGE}; spacing:4px; padding:2px 6px; }}
            QToolButton {{ background:transparent; color:{DIM}; border:none; border-radius:6px;
                           padding:4px 10px; font-size: 9pt; }}
            QToolButton:hover {{ background:{GHOST}; color:{TEXT}; }}
        """)
        for icon, label, idx in [("🏆","Ranking",2),("📋","Task",3),("⭐","Reward",4),("⚙️","Settings",5),("👤","Profile",6)]:
            a = QAction(f"{icon}  {label}", self)
            a.triggered.connect(lambda _, i=idx: self.go_to(i))
            self._tb.addAction(a)
        self._tb.addSeparator()
        fb_action = QAction("💬  Feedback", self)
        fb_action.triggered.connect(lambda: _FeedbackDialog(self).exec())
        self._tb.addAction(fb_action)
        self.addToolBar(self._tb)

        # ── Status bar ───────────────────────────────────────
        self._status_bar = self.statusBar()
        self._status_bar.setStyleSheet(f"""
            QStatusBar {{ background:{PANEL}; color:{DIM}; border-top:1px solid {EDGE};
                          font-size: 8pt; padding:0 8px; }}
            QStatusBar::item {{ border:none; }}
        """)
        self._status_bar.showMessage("Welcome to Clickjoy  •  Select a game to start")

        # ── Hide toolbar & menubar on login screen ────────────
        self._tb.setVisible(False)
        self.menuBar().setVisible(False)

    _PAGE_NAMES = {0:"Login", 1:"Game Select", 2:"Ranking", 3:"Task",
                   4:"Reward", 5:"Settings", 6:"Profile"}

    def go_to(self, index):
        """Navigate to a page by stack index and update the status bar.

        Args:
            index (int): Stack index (0=Login, 1=GameSelect, 2=Ranking,
                3=Task, 4=Reward, 5=Settings, 6=Profile, 7+=Games).

        Returns:
            None

        Examples:
            >>> self.go_to(2)  # open Ranking page
        """
        self.stack.setCurrentIndex(index)
        name = self._PAGE_NAMES.get(index, "")
        user = self.current_user or "Guest"
        msg = f"📍 {name}  •  Logged in as {user}" if self.current_user else f"📍 {name}"
        if hasattr(self, '_status_bar'): self._status_bar.showMessage(msg)

    def go_game(self, key):
        """Navigate to a game page by its string key.

        Args:
            key (str): Game key matching GAME_LIST (e.g. "flip", "normal").

        Returns:
            None

        Raises:
            None: Silently ignored if key is not found.

        Examples:
            >>> self.go_game("flip")
        """
        page = self._game_pages.get(key)
        if page:
            self.stack.setCurrentWidget(page)
            if hasattr(self, '_status_bar'):
                self._status_bar.showMessage(f"🎮 {NAMES.get(key, key)}  •  {self.current_user or 'Guest'}")

    def on_login_success(self, username):
        """Execute on login success.

        Args:
            username (str): Authenticated username.

        Examples:
            >>> window.on_login_success('alice')
        """
        self.current_user = username
        self.main_menu.update_user_label()
        self.ham_menu.update_user_label()
        self.ranking_page.refresh(); self.task_page.refresh()
        self.reward_page.refresh(); self.profile_page.refresh()
        # Show toolbar and menubar now that user is logged in
        self._tb.setVisible(True)
        self.menuBar().setVisible(True)
        self.go_to(1)
        if hasattr(self, '_status_bar'):
            self._status_bar.showMessage(f"✅ Logged in as {username}  •  Select a game to start")

    def toggle_hamburger(self):
        """Execute toggle hamburger.
        """
        self.ham_menu.raise_()
        w, h = 280, 700
        anim = QPropertyAnimation(self.ham_menu, b"geometry")
        anim.setDuration(300); anim.setEasingCurve(QEasingCurve.OutCubic)
        if not self.ham_open:
            anim.setStartValue(QRect(-w,0,w,h)); anim.setEndValue(QRect(0,0,w,h))
            self.ham_open = True
        else:
            anim.setStartValue(QRect(0,0,w,h)); anim.setEndValue(QRect(-w,0,w,h))
            self.ham_open = False
        anim.start(); self._anim = anim

    def refresh_theme(self):
        """Rebuild toolbar & status-bar stylesheets after a theme change,
        then delegate to each sub-page that has baked palette colours.
        """
        self._tb.setStyleSheet(f"""
            QToolBar {{ background:{PANEL}; border-bottom:1px solid {EDGE}; spacing:4px; padding:2px 6px; }}
            QToolButton {{ background:transparent; color:{DIM}; border:none; border-radius:6px;
                           padding:4px 10px; font-size: 9pt; }}
            QToolButton:hover {{ background:{GHOST}; color:{TEXT}; }}
        """)
        self._status_bar.setStyleSheet(f"""
            QStatusBar {{ background:{PANEL}; color:{DIM}; border-top:1px solid {EDGE};
                          font-size: 8pt; padding:0 8px; }}
            QStatusBar::item {{ border:none; }}
        """)
        # Propagate to pages that have inline stylesheets
        self.main_menu.refresh_theme()
        self.ham_menu.refresh_theme()
        self.ranking_page.refresh_theme()
        self.profile_page.refresh_theme()
        # Rebuild task & reward cards (they bake palette colours at card-build time)
        self.task_page.refresh()
        self.reward_page.refresh()
        # Force full repaint of the whole widget tree
        self.container.update()
        for i in range(self.stack.count()):
            w = self.stack.widget(i)
            if w: w.update()


# ==================== LoginPage ====================
class LoginPage(QWidget):
    """Login and registration form with card layout, show/hide password,
    forgot-password flow, and inline validation feedback.

    Modes: 'login' (default) and 'register'.
    On login success calls main_window.on_login_success(username).
    """

    # ── shared card colours ─────────────────────────────────────────────
    _BLUE      = "#1a6fcf"
    _DARK_BLUE = "#0d4fa0"
    _BG        = "#f5f5e8"
    _RED       = "#e53935"

    def __init__(self, main_window):
        """Initialise the instance.

        Args:
            main_window (MainWindow): Root window reference.
        """
        super().__init__()
        self.main_window = main_window
        self.db          = main_window.db
        self._mode       = "login"

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        # ── stacked card (login / register / forgot share the same area) ──
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_login_card())    # 0
        self._stack.addWidget(self._build_register_card()) # 1
        self._stack.addWidget(self._build_forgot_card())   # 2
        self._stack.setCurrentIndex(0)

        outer.addWidget(self._stack)

    # ──────────────────────────────────────────────────────────────────────
    # Card builders
    # ──────────────────────────────────────────────────────────────────────
    def _build_login_card(self):
        """Build and return the login card widget."""
        W = QWidget(); W.setStyleSheet("background:transparent;")
        outer = QVBoxLayout(W); outer.setAlignment(Qt.AlignCenter)

        card = QFrame(); card.setFixedWidth(380)
        card.setStyleSheet(f"""
            QFrame {{
                border: 3px solid {self._BLUE};
                border-radius: 18px;
                background: {self._BG};
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setSpacing(14); lay.setContentsMargins(36, 32, 36, 32)

        # Avatar
        av = QLabel("👤"); av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet("font-size: 44pt; border: none; background: transparent;")
        lay.addWidget(av)

        # Title
        title = QLabel("🖱️  Clickjoy"); title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 20pt; font-weight: bold; font-style: italic;"
                            f"color: {self._BLUE}; border: none; background: transparent;")
        lay.addWidget(title)
        lay.addSpacing(4)

        # Username
        self._login_user = self._input("Username")
        lay.addWidget(self._login_user)

        # Password with show/hide
        pw_row, self._login_pass = self._password_row("Password")
        lay.addWidget(pw_row)

        # Error
        self._login_err = self._err_lbl("⚠  Username หรือ Password ไม่ถูกต้อง")
        lay.addWidget(self._login_err)

        # Sign in button
        signin = self._primary_btn("Sign in")
        signin.clicked.connect(self._on_login)
        lay.addWidget(signin)

        # Forgot password link
        fp = self._link_btn("Forgot password?")
        fp.clicked.connect(lambda: self._stack.setCurrentIndex(2))
        lay.addWidget(fp, alignment=Qt.AlignCenter)

        lay.addSpacing(2)

        # Create account link
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self._dim_lbl("ยังไม่มีบัญชี?"))
        ca = self._link_btn("Create account")
        ca.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        row.addWidget(ca)
        row.addStretch()
        lay.addLayout(row)

        outer.addWidget(card, alignment=Qt.AlignCenter)
        return W

    def _build_register_card(self):
        """Build and return the register card widget."""
        W = QWidget(); W.setStyleSheet("background:transparent;")
        outer = QVBoxLayout(W); outer.setAlignment(Qt.AlignCenter)

        card = QFrame(); card.setFixedWidth(400)
        card.setStyleSheet(f"""
            QFrame {{
                border: 3px solid {self._BLUE};
                border-radius: 18px;
                background: {self._BG};
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setSpacing(10); lay.setContentsMargins(36, 28, 36, 28)

        # Back button
        back_row = QHBoxLayout()
        back = QPushButton("← Back")
        back.setFlat(True); back.setCursor(Qt.PointingHandCursor)
        back.setStyleSheet(f"QPushButton{{color:{self._BLUE};font-size: 10pt;font-weight:bold;"
                           f"border:none;background:transparent;text-align:left;}}"
                           f"QPushButton:hover{{color:{self._DARK_BLUE};}}")
        back.clicked.connect(lambda: (self._stack.setCurrentIndex(0), self._clear_register()))
        back_row.addWidget(back); back_row.addStretch()
        lay.addLayout(back_row)

        title = QLabel("Create Account"); title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 17pt; font-weight: bold; font-style: italic; color: {self._BLUE}; border: none; background: transparent;")
        lay.addWidget(title)
        lay.addSpacing(4)

        # Username
        lay.addWidget(self._field_lbl("Username:"))
        self._reg_user = self._input("Username")
        lay.addWidget(self._reg_user)
        self._reg_user_err = self._err_lbl("⚠  Username นี้มีอยู่แล้ว")
        lay.addWidget(self._reg_user_err)

        # Password
        lay.addWidget(self._field_lbl("Password:"))
        pw_row, self._reg_pass = self._password_row("Password")
        lay.addWidget(pw_row)

        # Confirm Password
        lay.addWidget(self._field_lbl("Confirm Password:"))
        cp_row, self._reg_confirm = self._password_row("Confirm Password")
        lay.addWidget(cp_row)
        self._reg_pw_err = self._err_lbl("⚠  Password ไม่ตรงกัน")
        lay.addWidget(self._reg_pw_err)

        create = self._primary_btn("Create Account")
        create.clicked.connect(self._on_register)
        lay.addWidget(create)

        self._reg_ok = QLabel("✅  สมัครสำเร็จ! กรุณา Sign in")
        self._reg_ok.setAlignment(Qt.AlignCenter)
        self._reg_ok.setStyleSheet("color:#16a34a;font-size: 10pt;border:none;background:transparent;")
        self._reg_ok.setVisible(False)
        lay.addWidget(self._reg_ok)

        outer.addWidget(card, alignment=Qt.AlignCenter)
        return W

    # ──────────────────────────────────────────────────────────────────────
    # Forgot-password inline flow  (overlay via QDialog-style QFrame)
    # ──────────────────────────────────────────────────────────────────────
    def _build_forgot_card(self):
        """Build and return the forgot-password page widget."""
        W = QWidget(); W.setStyleSheet("background:transparent;")
        outer = QVBoxLayout(W); outer.setAlignment(Qt.AlignCenter)

        card = QFrame(); card.setFixedWidth(400)
        card.setStyleSheet(f"""
            QFrame {{
                border: 3px solid {self._BLUE};
                border-radius: 18px;
                background: {self._BG};
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setSpacing(12); lay.setContentsMargins(36, 28, 36, 28)

        # Back button
        back_row = QHBoxLayout()
        back = QPushButton("← Back")
        back.setFlat(True); back.setCursor(Qt.PointingHandCursor)
        back.setStyleSheet(f"QPushButton{{color:{self._BLUE};font-size:11pt;font-weight:bold;"
                           f"border:none;background:transparent;text-align:left;}}"
                           f"QPushButton:hover{{color:{self._DARK_BLUE};}}")
        back.clicked.connect(lambda: (self._stack.setCurrentIndex(0), self._clear_forgot()))
        back_row.addWidget(back); back_row.addStretch()
        lay.addLayout(back_row)

        title = QLabel("Forgot password?")
        title.setStyleSheet(f"font-size: 20pt; font-weight: bold; font-style: italic;"
                            f"color: {self._BLUE}; border: none; background: transparent;")
        lay.addWidget(title)

        sub = QLabel("กรอก Username ของคุณ")
        sub.setStyleSheet(f"font-size: 11pt; color: #555; border: none; background: transparent;")
        lay.addWidget(sub)
        lay.addSpacing(4)

        self._fp_user = self._input("Username")
        lay.addWidget(self._fp_user)
        self._fp_user_err = self._err_lbl("⚠  ไม่พบ Username นี้")
        lay.addWidget(self._fp_user_err)

        # Step 2 — reset fields (hidden initially)
        self._fp_step2 = QWidget(); self._fp_step2.setStyleSheet("background:transparent;")
        s2 = QVBoxLayout(self._fp_step2); s2.setContentsMargins(0,4,0,0); s2.setSpacing(8)
        s2.addWidget(self._field_lbl("New Password:"))
        pw_row, self._fp_new_pw = self._password_row("New Password")
        s2.addWidget(pw_row)
        s2.addWidget(self._field_lbl("Confirm New Password:"))
        cp_row, self._fp_confirm = self._password_row("Confirm Password")
        s2.addWidget(cp_row)
        self._fp_pw_err = self._err_lbl("⚠  Password ไม่ตรงกัน")
        s2.addWidget(self._fp_pw_err)
        self._fp_step2.setVisible(False)
        lay.addWidget(self._fp_step2)

        self._fp_btn = self._primary_btn("Next")
        self._fp_btn.clicked.connect(self._on_forgot_next)
        lay.addWidget(self._fp_btn)

        self._fp_ok = QLabel("✅  Password เปลี่ยนแล้ว!")
        self._fp_ok.setAlignment(Qt.AlignCenter)
        self._fp_ok.setStyleSheet("color:#16a34a;font-size:11pt;border:none;background:transparent;")
        self._fp_ok.setVisible(False)
        lay.addWidget(self._fp_ok)

        outer.addWidget(card, alignment=Qt.AlignCenter)
        self._fp_found_user = [None]
        return W

    def _on_forgot_next(self):
        """Handle Next / Reset Password button on forgot page."""
        if not self._fp_found_user[0]:
            uname = self._fp_user.text().strip()
            u = self.db.get_user(uname)
            if not u:
                self._fp_user_err.setVisible(True); return
            self._fp_user_err.setVisible(False)
            self._fp_found_user[0] = uname
            self._fp_user.setEnabled(False)
            self._fp_step2.setVisible(True)
            self._fp_btn.setText("Reset Password")
        else:
            npw = self._fp_new_pw.text(); cpw = self._fp_confirm.text()
            if npw != cpw:
                self._fp_pw_err.setVisible(True); return
            if not npw: return
            self._fp_pw_err.setVisible(False)
            rows = self.db._read_all()
            for r in rows:
                if r["user"] == self._fp_found_user[0]:
                    r["password"] = npw; break
            self.db._write_all(rows)
            self._fp_ok.setVisible(True)
            self._fp_btn.setEnabled(False)
            QTimer.singleShot(1600, lambda: (
                self._stack.setCurrentIndex(0), self._clear_forgot()))

    def _clear_forgot(self):
        """Reset forgot-password page to initial state."""
        self._fp_found_user[0] = None
        self._fp_user.clear(); self._fp_user.setEnabled(True)
        self._fp_new_pw.clear(); self._fp_confirm.clear()
        self._fp_step2.setVisible(False)
        self._fp_btn.setText("Next"); self._fp_btn.setEnabled(True)
        for w in (self._fp_user_err, self._fp_pw_err, self._fp_ok):
            w.setVisible(False)

    # ──────────────────────────────────────────────────────────────────────
    def _show_forgot(self):
        """Show the forgot-password dialog."""
        from PySide6.QtWidgets import QDialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Forgot Password")
        dlg.setFixedWidth(380)
        dlg.setStyleSheet(f"background:{self._BG};")
        lay = QVBoxLayout(dlg); lay.setSpacing(12); lay.setContentsMargins(32, 28, 32, 28)

        title = QLabel("Forgot password?")
        title.setStyleSheet(f"font-size: 15pt;font-weight:bold;color:{self._BLUE};")
        lay.addWidget(title)
        sub = QLabel("กรอก Username ของคุณ")
        sub.setStyleSheet("font-size: 10pt;color:#555;")
        lay.addWidget(sub)

        user_inp = self._input("Username")
        lay.addWidget(user_inp)
        user_err = self._err_lbl("⚠  ไม่พบ Username นี้")
        lay.addWidget(user_err)

        # ── step 2: reset fields (hidden at first) ──
        step2 = QWidget(); step2.setStyleSheet("background:transparent;")
        s2 = QVBoxLayout(step2); s2.setContentsMargins(0,0,0,0); s2.setSpacing(8)
        s2.addWidget(self._field_lbl("New Password:"))
        pw_row, new_pw = self._password_row("New Password")
        s2.addWidget(pw_row)
        s2.addWidget(self._field_lbl("Confirm New Password:"))
        cp_row, confirm_pw = self._password_row("Confirm Password")
        s2.addWidget(cp_row)
        pw_err = self._err_lbl("⚠  Password ไม่ตรงกัน")
        s2.addWidget(pw_err)
        step2.setVisible(False)
        lay.addWidget(step2)

        btn = self._primary_btn("Next")
        lay.addWidget(btn)

        found_user = [None]

        def on_next():
            if not found_user[0]:
                # Step 1: verify username
                uname = user_inp.text().strip()
                u = self.db.get_user(uname)
                if not u:
                    user_err.setVisible(True); return
                user_err.setVisible(False)
                found_user[0] = uname
                user_inp.setEnabled(False)
                step2.setVisible(True)
                btn.setText("Reset Password")
            else:
                # Step 2: reset
                npw = new_pw.text(); cpw = confirm_pw.text()
                if npw != cpw:
                    pw_err.setVisible(True); return
                if not npw: return
                pw_err.setVisible(False)
                self.db.update_bio(found_user[0], self.db.get_user(found_user[0]).get("bio",""))
                # Actually update password
                rows = self.db._read_all()
                for r in rows:
                    if r["user"] == found_user[0]:
                        r["password"] = npw; break
                self.db._write_all(rows)
                show_toast(self, "✅  Password เปลี่ยนแล้ว!", "#16a34a")
                dlg.accept()

        btn.clicked.connect(on_next)
        dlg.exec()

    # ──────────────────────────────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────────────────────────────
    def _on_login(self):
        """Validate and submit the login form."""
        u = self._login_user.text().strip()
        p = self._login_pass.text()
        self._login_err.setVisible(False)
        if not u or not p:
            self._login_err.setText("⚠  กรุณากรอก Username และ Password")
            self._login_err.setVisible(True); return
        ud = self.db.login(u, p)
        if ud:
            self._login_user.clear(); self._login_pass.clear()
            self.main_window.on_login_success(u)
        else:
            self._login_err.setText("⚠  Username หรือ Password ไม่ถูกต้อง")
            self._login_err.setVisible(True)

    def _on_register(self):
        """Validate and submit the registration form."""
        u   = self._reg_user.text().strip()
        p   = self._reg_pass.text()
        cp  = self._reg_confirm.text()
        self._reg_user_err.setVisible(False)
        self._reg_pw_err.setVisible(False)
        self._reg_ok.setVisible(False)
        if not u or not p: return
        if self.db.get_user(u):
            self._reg_user_err.setVisible(True); return
        if p != cp:
            self._reg_pw_err.setVisible(True); return
        self.db.register(u, p)
        self._reg_ok.setVisible(True)
        self._clear_register()
        QTimer.singleShot(1400, lambda: self._stack.setCurrentIndex(0))

    def _clear_register(self):
        """Clear all register form fields and hide error labels."""
        for w in (self._reg_user, self._reg_pass, self._reg_confirm):
            w.clear()
        for w in (self._reg_user_err, self._reg_pw_err, self._reg_ok):
            w.setVisible(False)

    # ──────────────────────────────────────────────────────────────────────
    # Widget factory helpers
    # ──────────────────────────────────────────────────────────────────────
    def _input(self, placeholder):
        """Return a styled rounded QLineEdit."""
        f = QLineEdit(); f.setPlaceholderText(placeholder); f.setFixedHeight(44)
        f.setStyleSheet(f"""
            QLineEdit {{
                border: 2.5px solid {self._BLUE};
                border-radius: 22px;
                padding: 0 16px;
                font-size: 11pt;
                background: {self._BG};
                color: #222;
            }}
            QLineEdit:focus {{ border-color: {self._DARK_BLUE}; }}
        """)
        return f

    def _password_row(self, placeholder):
        """Return (container_widget, line_edit) with 👁 show/hide toggle."""
        container = QWidget(); container.setStyleSheet("background:transparent;")
        h = QHBoxLayout(container); h.setContentsMargins(0,0,0,0); h.setSpacing(0)

        field = QLineEdit(); field.setPlaceholderText(placeholder)
        field.setEchoMode(QLineEdit.Password); field.setFixedHeight(44)
        field.setStyleSheet(f"""
            QLineEdit {{
                border: 2.5px solid {self._BLUE};
                border-top-left-radius: 22px;
                border-bottom-left-radius: 22px;
                border-right: none;
                padding: 0 16px;
                font-size: 11pt;
                background: {self._BG};
                color: #222;
            }}
            QLineEdit:focus {{ border-color: {self._DARK_BLUE}; }}
        """)

        toggle = QPushButton("︶"); toggle.setFixedSize(44, 44)
        toggle.setCursor(Qt.PointingHandCursor); toggle.setCheckable(True)
        toggle.setStyleSheet(f"""
            QPushButton {{
                border: 2.5px solid {self._BLUE};
                border-top-right-radius: 22px;
                border-bottom-right-radius: 22px;
                border-left: none;
                background: {self._BG};
                font-size: 12pt;
                color: {self._BLUE};
            }}
            QPushButton:hover {{ background: #e3eeff; }}
            QPushButton:checked {{ background: #d0e4ff; }}
        """)
        def _toggle_echo(checked):
            field.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
            toggle.setText("👁" if checked else "︶")
        toggle.toggled.connect(_toggle_echo)
        h.addWidget(field); h.addWidget(toggle)
        return container, field

    def _primary_btn(self, text):
        """Return a styled primary action button."""
        btn = QPushButton(text); btn.setFixedHeight(46)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {self._BLUE};
                color: white;
                border-radius: 23px;
                font-size: 11pt;
                font-weight: bold;
                border: none;
            }}
            QPushButton:hover {{ background: {self._DARK_BLUE}; }}
            QPushButton:pressed {{ background: #0a3a80; }}
        """)
        return btn

    def _link_btn(self, text):
        """Return a flat underlined link-style button."""
        btn = QPushButton(text); btn.setFlat(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                color: {self._BLUE}; font-size: 10pt;
                text-decoration: underline; border: none; background: transparent;
            }}
            QPushButton:hover {{ color: {self._DARK_BLUE}; }}
        """)
        return btn

    def _err_lbl(self, text):
        """Return a hidden red error label."""
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{self._RED};font-size: 9pt;border:none;"
                          f"background:transparent;padding-left:8px;")
        lbl.setVisible(False)
        return lbl

    def _dim_lbl(self, text):
        """Return a small dim label."""
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{DIM};font-size: 9pt;border:none;background:transparent;")
        return lbl

    def _field_lbl(self, text):
        """Return a small field label."""
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 10pt;font-weight:600;border:none;background:transparent;color:#333;")
        return lbl


# ==================== FeedbackDialog ====================
class _FeedbackDialog(QDialog):
    RECIPIENT = "burawitchaya.r@kkumail.com"

    def __init__(self, main_window, parent=None):
        """Initialise the instance.

        Args:
            main_window (MainWindow): Root window (supplies current_user).
                    parent (QWidget | None): Optional dialog parent.
        """
        super().__init__(parent or main_window)
        self.main_window = main_window
        self.setWindowTitle("Send Feedback")
        self.setFixedWidth(460); self.setMinimumHeight(360)
        self.setStyleSheet(f"""
            QDialog {{ background:{SURFACE}; }}
            QLabel  {{ background:transparent; color:{TEXT}; border:none; }}
            QLineEdit, QTextEdit {{
                background:{PANEL}; color:{TEXT};
                border:1px solid {EDGE}; border-radius:8px; padding:6px 10px;
                font-size: 9pt;
            }}
            QLineEdit:focus, QTextEdit:focus {{ border-color:#3b82f6; }}
        """)
        lay = QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(14)

        # Title
        title = QLabel("💬  Send Feedback"); title.setFont(F(15, 700))
        title.setStyleSheet(f"color:{TEXT};")
        sub = QLabel(f"Your message will be sent to  {self.RECIPIENT}")
        sub.setFont(F(9)); sub.setStyleSheet(f"color:{DIM};")
        lay.addWidget(title); lay.addWidget(sub)

        # Topic
        lay.addWidget(self._lbl("Topic"))
        self.topic = QLineEdit()
        self.topic.setPlaceholderText("e.g. Bug report, Suggestion, Other…")
        self.topic.setFixedHeight(36); lay.addWidget(self.topic)

        # Message
        lay.addWidget(self._lbl("Message"))
        self.msg_edit = QTextEdit()
        self.msg_edit.setPlaceholderText("Describe your feedback here…")
        self.msg_edit.setMinimumHeight(120); lay.addWidget(self.msg_edit)

        # Status
        self.status = QLabel(""); self.status.setFont(F(9))
        self.status.setAlignment(Qt.AlignCenter); lay.addWidget(self.status)

        # Buttons
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        cancel = QPushButton("Cancel"); cancel.setFixedHeight(38)
        cancel.setStyleSheet(f"QPushButton{{background:{GHOST};color:{DIM};border:1px solid {EDGE};border-radius:10px;}}QPushButton:hover{{background:{EDGE};color:{TEXT};}}")
        cancel.clicked.connect(self.reject)

        self.send_btn = QPushButton("📨  Send"); self.send_btn.setFixedHeight(38)
        self.send_btn.setStyleSheet("QPushButton{background:#1d4ed8;color:white;border:none;border-radius:10px;font-weight:700;font-size: 10pt;}QPushButton:hover{background:#2563eb;}QPushButton:disabled{background:#2a2e40;color:#5a637a;}")
        self.send_btn.clicked.connect(self._send)
        btn_row.addWidget(cancel); btn_row.addWidget(self.send_btn)
        lay.addLayout(btn_row)

    def _lbl(self, text):
        l = QLabel(text); l.setFont(F(10, 600))
        l.setStyleSheet(f"color:{DIM};")
        return l

    def _send(self):
        """Validate inputs and append the feedback entry to feedback.txt.

        The entry is formatted with a timestamp, username, topic, and body.
        Shows an inline error label if topic or body is empty.

        Returns:
            None

        Raises:
            OSError: Propagated as an inline error message if the file
                cannot be written.

        Examples:
            >>> dlg._send()   # called internally by the Send button
        """
        topic = self.topic.text().strip()
        body  = self.msg_edit.toPlainText().strip()
        user  = self.main_window.current_user or "Guest"

        if not topic:
            self._err("Please enter a topic."); return
        if not body:
            self._err("Please write your message."); return

        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (f"{'='*60}\n"
                 f"Date    : {timestamp}\n"
                 f"From    : {user}\n"
                 f"Topic   : {topic}\n"
                 f"Message :\n{body}\n\n")
        try:
            with open("feedback.txt", "a", encoding="utf-8") as f:
                f.write(entry)
            self.status.setText("✅  Feedback saved! Thank you.")
            self.status.setStyleSheet("color:#4ade80;background:transparent;border:none;")
            self.send_btn.setEnabled(False)
            QTimer.singleShot(1600, self.accept)
        except Exception as e:
            self._err(f"Could not save: {e}")

    def _err(self, msg):
        """Execute err.

        Args:
            msg (str): Error text to display in the status label.
        """
        self.status.setText(f"⚠  {msg}")
        self.status.setStyleSheet("color:#f87171;background:transparent;border:none;")


# ==================== MainMenuPage ====================
class MainMenuPage(QWidget):
    """Main game-select screen — HomeCard list + DetailPanel side-by-side."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # ── Animated neon background ──────────────────────────
        self.bg = NeonBackground("normal", self)
        self.bg.setGeometry(0, 0, 920, 700)
        self.bg.lower()

        layout = QVBoxLayout(self); layout.setSpacing(0); layout.setContentsMargins(0, 0, 0, 0)

        # ── Menu bar ──────────────────────────────────────────
        mb = main_window.menuBar()
        mb.setStyleSheet(f"""
            QMenuBar {{
                background: {PANEL}; color: {TEXT};
                border-bottom: 1px solid {EDGE}; font-size: 10pt;
            }}
            QMenuBar::item {{ background: transparent; padding: 4px 12px; border-radius: 4px; }}
            QMenuBar::item:selected, QMenuBar::item:pressed {{ background: {GHOST}; color: {TEXT}; }}
            QMenu {{
                background: {PANEL}; color: {TEXT};
                border: 1px solid {EDGE}; border-radius: 8px; padding: 4px;
            }}
            QMenu::item {{ padding: 6px 24px 6px 16px; border-radius: 4px; }}
            QMenu::item:selected {{ background: {GHOST}; color: {TEXT}; }}
            QMenu::separator {{ background: {EDGE}; height: 1px; margin: 4px 8px; }}
        """)
        fm = mb.addMenu("&File")
        ea = QAction("&Exit", self); ea.setShortcut("Ctrl+Q"); ea.triggered.connect(main_window.close); fm.addAction(ea)
        pm = mb.addMenu("&Progress Menu")
        for lbl, sc, idx in [("&Ranking","Ctrl+R",2),("&Task","Ctrl+T",3),("R&eward","Ctrl+Shift+R",4)]:
            a = QAction(lbl, self); a.setShortcut(sc); a.setShortcutContext(Qt.ApplicationShortcut)
            a.triggered.connect(lambda _, i=idx: main_window.go_to(i)); pm.addAction(a)

        from PySide6.QtCore import QObject, QEvent
        class _HoverMenuBar(QObject):
            def __init__(self, menubar):
                super().__init__(menubar); self._mb = menubar
                self._active = False; self._mb.installEventFilter(self)
            def eventFilter(self, obj, event):
                if obj is self._mb:
                    if event.type() == QEvent.MouseButtonPress: self._active = True
                    elif event.type() == QEvent.HoverMove and self._active:
                        action = self._mb.actionAt(event.position().toPoint())
                        if action: self._mb.setActiveAction(action)
                    elif event.type() == QEvent.Leave: self._active = False
                return False
        self._hover_mb = _HoverMenuBar(mb)

        # ── Scrollable inner area ─────────────────────────────
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(20, 14, 20, 20); inner_lay.setSpacing(0)
        scroll.setWidget(inner); layout.addWidget(scroll)

        # ── Top bar: hamburger + brand + user ─────────────────
        top = QHBoxLayout(); top.setSpacing(10); top.setContentsMargins(0, 0, 0, 14)
        hb = QPushButton("☰"); hb.setFixedSize(38, 38)
        hb.setStyleSheet(f"QPushButton{{background:{PANEL};color:{TEXT};border:1px solid {EDGE};border-radius:10px;font-size:13pt;}}QPushButton:hover{{background:{EDGE};}}")
        hb.clicked.connect(main_window.toggle_hamburger); top.addWidget(hb)

        brand_col = QVBoxLayout(); brand_col.setSpacing(0)
        brand = QLabel("CLICKJOY ✦"); brand.setFont(F(22, 900))
        brand.setStyleSheet(f"color:{TEXT};background:transparent;letter-spacing:4px;")
        self._brand_glow = QGraphicsDropShadowEffect(); self._brand_glow.setBlurRadius(18)
        self._brand_glow.setColor(QColor(ACCENT)); self._brand_glow.setOffset(0, 0)
        brand.setGraphicsEffect(self._brand_glow)
        self._tagline = QLabel("▸  beat your record")
        self._tagline.setFont(F(9, 500))
        self._tagline.setStyleSheet(f"color:{ACCENT};background:transparent;letter-spacing:2px;")
        brand_col.addWidget(brand); brand_col.addWidget(self._tagline)
        top.addLayout(brand_col, 1)

        self.user_lbl = QLabel("👤 Guest"); self.user_lbl.setFont(F(9))
        self.user_lbl.setStyleSheet(f"color:{DIM};background:transparent;"); top.addWidget(self.user_lbl)
        inner_lay.addLayout(top)

        # ── Stats banner ──────────────────────────────────────
        banner = QWidget(); banner.setFixedHeight(80)
        banner.setAttribute(Qt.WA_TranslucentBackground)
        bl = QHBoxLayout(banner); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(10)
        self.total_chip = self._stat_chip("TOTAL CLICKS", "0", ACCENT)
        self.cps_chip   = self._stat_chip("BEST CPS",     "—", NEON["cpm"][0])
        self.streak_chip = self._stat_chip("FLIP STREAK", "0", NEON["flip"][0])
        bl.addWidget(self.total_chip); bl.addWidget(self.cps_chip); bl.addWidget(self.streak_chip)
        inner_lay.addWidget(banner); inner_lay.addSpacing(12)

        # ── Section label ─────────────────────────────────────
        sec = QLabel("SELECT GAME"); sec.setFont(FM(9, bold=True))
        sec.setStyleSheet(f"color:{DIM};background:transparent;letter-spacing:3px;padding-bottom:6px;")
        inner_lay.addWidget(sec)

        # ── Body: HomeCard list (left) + DetailPanel (right) ──
        body = QHBoxLayout(); body.setSpacing(14); body.setContentsMargins(0, 0, 0, 0)

        # Left: scrollable HomeCard list
        list_scroll = QScrollArea(); list_scroll.setWidgetResizable(True)
        list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        list_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        list_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        list_scroll.setMinimumHeight(300)
        list_w = QWidget(); list_w.setStyleSheet("background:transparent;")
        list_lay = QVBoxLayout(list_w)
        list_lay.setSpacing(4); list_lay.setContentsMargins(0, 0, 2, 4)
        list_lay.setAlignment(Qt.AlignTop)
        self._cards = {}
        for field, name, icon, subtitle in GAME_LIST:
            card = GameCard(field, name, icon, subtitle, self._on_card_click)
            list_lay.addWidget(card); self._cards[field] = card
        list_scroll.setWidget(list_w)
        body.addWidget(list_scroll, stretch=3)   # 60%

        # Right: detail panel
        self.detail = DetailPanel(main_window)
        self.detail.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.detail.setFixedWidth(260)
        body.addWidget(self.detail, stretch=0)   # fixed width

        inner_lay.addLayout(body, stretch=1)

        # ── Footer ────────────────────────────────────────────
        inner_lay.addSpacing(8)
        fsep = QFrame(); fsep.setFixedHeight(1); fsep.setStyleSheet(f"background:{EDGE};")
        inner_lay.addWidget(fsep)
        fl = QLabel("CLICKJOY  ·  REACTION TRAINING SUITE  ·  v2.4.1")
        fl.setFont(FM(7)); fl.setAlignment(Qt.AlignCenter)
        fl.setStyleSheet(f"color:{GHOST};padding-top:6px;background:transparent;")
        inner_lay.addWidget(fl)

    def _update_accent(self, hex_color):
        self._tagline.setStyleSheet(f"color:{hex_color};background:transparent;letter-spacing:2px;")
        self._brand_glow.setColor(QColor(hex_color))
        self.total_chip._neon = hex_color
        self.total_chip._val_lbl.setStyleSheet(f"color:{hex_color};background:transparent;")
        eff = self.total_chip._val_lbl.graphicsEffect()
        if eff: eff.setColor(QColor(hex_color))
        self.total_chip.update()

    def _stat_chip(self, label, value, neon):
        """Large stat banner chip widget."""
        w = QWidget(); w.setAttribute(Qt.WA_TranslucentBackground)
        w._neon = neon
        lay = QVBoxLayout(w); lay.setContentsMargins(16, 10, 16, 10); lay.setSpacing(2)
        cap = QLabel(label); cap.setFont(F(8, 500))
        cap.setStyleSheet(f"color:{DIM};background:transparent;letter-spacing:2px;")
        val = QLabel(value); val.setFont(FM(20, True))
        val.setStyleSheet(f"color:{neon};background:transparent;")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(20)
        eff.setColor(QColor(neon)); eff.setOffset(0, 0); val.setGraphicsEffect(eff)
        lay.addWidget(cap); lay.addWidget(val)
        w._val_lbl = val
        def paint(ev, widget=w):
            pa = QPainter(widget); pa.setRenderHint(QPainter.Antialiasing)
            nc = QColor(widget._neon); ww, wh = widget.width(), widget.height()
            path = QPainterPath()
            path.addRoundedRect(QRectF(0.5, 0.5, ww - 1, wh - 1), 12, 12)
            pa.fillPath(path, QColor(18, 21, 32, 220))
            pa.strokePath(path, QPen(QColor(nc.red(), nc.green(), nc.blue(), 80), 1))
            hi = QLinearGradient(0, 0, 0, 20)
            hi.setColorAt(0, QColor(nc.red(), nc.green(), nc.blue(), 25))
            hi.setColorAt(1, QColor(nc.red(), nc.green(), nc.blue(), 0))
            pa.fillPath(path, QBrush(hi)); pa.end()
        w.paintEvent = paint
        return w

    def _on_card_click(self, field):
        """Highlight the selected HomeCard and update the detail panel."""
        # Highlight: re-tint HomeCards (set target hover to 1 for selected, 0 for others)
        for fid, card in self._cards.items():
            card._target = 1.0 if fid == field else 0.0
            card._hover  = 1.0 if fid == field else 0.0
            card.update()
        # Update detail panel
        for gf, name, icon, sub in GAME_LIST:
            if gf == field:
                self.detail.update_game(field, name, icon, sub)
                break

    def update_user_label(self):
        u = self.main_window.current_user
        self.user_lbl.setText(f"👤 {u or 'Guest'}")
        self._refresh_chips()
        self.detail.refresh_score()

    def _refresh_chips(self):
        u = self.main_window.current_user
        if u:
            ud = self.main_window.db.get_user(u)
            if ud:
                total = sum(ud.get(f, 0) for f in ALL_DB_FIELDS)
                self.total_chip._val_lbl.setText(f"{total:,}")
                self.streak_chip._val_lbl.setText(str(G.flip_best_h or G.flip_best_t))
        cps = G.cpm_cps
        self.cps_chip._val_lbl.setText(f"{cps:.2f}" if cps > 0 else "—")

    def resizeEvent(self, e):
        self.bg.setGeometry(0, 0, self.width(), self.height()); super().resizeEvent(e)

    def showEvent(self, e):
        self._refresh_chips()
        self.detail.refresh_score()
        self.main_window.task_page.refresh()
        super().showEvent(e)

    def refresh_theme(self):
        """Rebuild palette-baked stylesheets after a theme change."""
        mb = self.main_window.menuBar()
        mb.setStyleSheet(f"""
            QMenuBar {{
                background: {PANEL}; color: {TEXT};
                border-bottom: 1px solid {EDGE}; font-size: 10pt;
            }}
            QMenuBar::item {{ background: transparent; padding: 4px 12px; border-radius: 4px; }}
            QMenuBar::item:selected, QMenuBar::item:pressed {{ background: {GHOST}; color: {TEXT}; }}
            QMenu {{
                background: {PANEL}; color: {TEXT};
                border: 1px solid {EDGE}; border-radius: 8px; padding: 4px;
            }}
            QMenu::item {{ padding: 6px 24px 6px 16px; border-radius: 4px; }}
            QMenu::item:selected {{ background: {GHOST}; color: {TEXT}; }}
            QMenu::separator {{ background: {EDGE}; height: 1px; margin: 4px 8px; }}
        """)
        self.user_lbl.setStyleSheet(f"color:{DIM};background:transparent;")

        # Refresh every GameCard with its current selected state
        for field, card in self._cards.items():
            card._neon, card._glow = NEON.get(field, ("#3b82f6", "#0f2a5c", "", ""))[:2]
            card._set_style(card._selected)

        # Re-apply the detail panel with the current field (picks up new palette + NEON)
        field = self.detail._current_field
        for gf, name, icon, sub in GAME_LIST:
            if gf == field:
                self.detail.update_game(field, name, icon, sub)
                break

        self.update()


# ==================== HamburgerMenuPage ====================
class HamburgerMenuPage(QWidget):
    """Slide-in side-drawer navigation panel.

    Contains a live-search bar that filters both page links and game
    shortcuts.  Animates in/out via QPropertyAnimation.
    """
    def __init__(self, parent, main_window):
        """Initialise the instance.

        Args:
            container (QWidget): The parent container widget.
                    main_window (MainWindow): Root window reference.
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.main_window = main_window
        self.setFixedWidth(280)
        self.setStyleSheet(f"""
            HamburgerMenuPage {{ background-color:{SURFACE}; border-right:1px solid {EDGE}; }}
            HamburgerMenuPage QWidget {{ background-color:{SURFACE}; }}
            HamburgerMenuPage QLineEdit {{
                background:{PANEL}; color:{TEXT};
                border:1px solid {EDGE}; border-radius:8px; padding:0 10px;
            }}
        """)

        lay = QVBoxLayout(self); lay.setSpacing(6); lay.setContentsMargins(12,12,12,12)

        # Close button
        self._close_btn = QPushButton("☰  Close"); self._close_btn.setFixedHeight(34)
        self._close_btn.setStyleSheet(f"QPushButton{{background:{GHOST};color:{DIM};border:1px solid {EDGE};border-radius:8px;font-size: 10pt;text-align:left;padding-left:10px;}}QPushButton:hover{{background:{EDGE};color:{TEXT};}}")
        self._close_btn.clicked.connect(main_window.toggle_hamburger); lay.addWidget(self._close_btn)

        # Search bar
        self._search = QLineEdit(); self._search.setPlaceholderText("🔍  Search pages & games…")
        self._search.setFixedHeight(34); lay.addWidget(self._search)
        self._search.textChanged.connect(self._on_search)

        # User row
        pr = QHBoxLayout(); il = QLabel("👤"); il.setFont(F(16))
        il.setStyleSheet("background:transparent;border:none;")
        self.name_btn = QPushButton("Guest"); self.name_btn.setFlat(True)
        self.name_btn.setFont(F(11, 700))
        self.name_btn.setStyleSheet(f"color:{TEXT};background:transparent;border:none;text-align:left;")
        self.name_btn.clicked.connect(lambda: (main_window.toggle_hamburger(), main_window.go_to(6)))
        pr.addWidget(il); pr.addWidget(self.name_btn); pr.addStretch(); lay.addLayout(pr)

        self._sep_widgets = []
        def _sep():
            ln = QFrame(); ln.setFrameShape(QFrame.HLine)
            ln.setStyleSheet(f"background:{EDGE};max-height:1px;border:none;")
            self._sep_widgets.append(ln); return ln

        lay.addWidget(_sep())

        # ── Scrollable content area ───────────────────────────
        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(f"QScrollArea{{border:none;background:{SURFACE};}}QScrollBar:vertical{{background:{SURFACE};width:4px;border-radius:2px;}}QScrollBar::handle:vertical{{background:{EDGE};border-radius:2px;min-height:20px;}}QScrollBar::handle:vertical:hover{{background:#3b82f6;}}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        self._scroll_content = QWidget(); self._scroll_content.setStyleSheet(f"background:{SURFACE};")
        self._content_lay = QVBoxLayout(self._scroll_content); self._content_lay.setSpacing(2)
        self._content_lay.setContentsMargins(0,0,0,0); self._content_lay.setAlignment(Qt.AlignTop)
        self._scroll.setWidget(self._scroll_content); lay.addWidget(self._scroll, 1)

        # Pages section label
        self._pages_lbl = self._section_label("PAGES")
        self._content_lay.addWidget(self._pages_lbl)

        # Page buttons
        self._page_btns = []
        self._page_btn_colors = []
        for label, idx, color, icon in [
            ("Ranking",  2, "#f59e0b", "🏆"),
            ("Task",     3, "#10b981", "📋"),
            ("Reward",   4, "#ec4899", "⭐"),
            ("Setting",  5, "#8b5cf6", "⚙️"),
            ("Profile",  6, "#06b6d4", "👤"),
        ]:
            btn = self._nav_btn(f"{icon}  {label}", color)
            btn.clicked.connect(lambda _, i=idx: (main_window.toggle_hamburger(), main_window.go_to(i)))
            self._content_lay.addWidget(btn)
            self._page_btns.append((label.lower(), btn))
            self._page_btn_colors.append(color)

        self._content_lay.addSpacing(4)
        self._content_lay.addWidget(_sep())
        self._content_lay.addSpacing(4)

        # Games section label
        self._games_lbl = self._section_label("GAMES")
        self._content_lay.addWidget(self._games_lbl)

        # Game buttons (all 12)
        self._game_btns = []
        self._game_btn_colors = []
        for key, name, icon, _ in GAME_LIST:
            neon = NEON[key][0]
            btn = self._nav_btn(f"{icon}  {name}", neon)
            btn.clicked.connect(lambda _, k=key: (main_window.toggle_hamburger(), main_window.go_game(k)))
            self._content_lay.addWidget(btn)
            self._game_btns.append((name.lower(), btn))
            self._game_btn_colors.append(key)

        self._content_lay.addSpacing(4)
        self._content_lay.addWidget(_sep())
        self._content_lay.addSpacing(2)

        # Logout
        self._logout_btn = QPushButton("🚪  Logout"); self._logout_btn.setFixedHeight(38)
        self._logout_btn.setStyleSheet(f"QPushButton{{background:transparent;color:#f87171;border:none;border-radius:8px;text-align:left;padding-left:10px;font-size: 9pt;}}QPushButton:hover{{background:{GHOST};}}")
        self._logout_btn.clicked.connect(self._logout)
        self._content_lay.addWidget(self._logout_btn)

    def _section_label(self, text):
        lbl = QLabel(text); lbl.setFont(FM(8, bold=True))
        lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;padding:4px 4px 2px 4px;letter-spacing:2px;")
        return lbl

    def _nav_btn(self, label, color):
        btn = QPushButton(label); btn.setFixedHeight(36)
        btn.setStyleSheet(f"QPushButton{{background:transparent;color:{DIM};border:none;border-radius:8px;text-align:left;padding-left:12px;font-size: 9pt;}}QPushButton:hover{{background:{GHOST};color:{color};}}")
        return btn

    def _on_search(self, text):
        """Execute on search.

        Args:
            text (str): Current search query string from the input field.

        Examples:
            >>> menu._on_search('flip')
        """
        q = text.strip().lower()
        # Filter page buttons
        any_page = False
        for name, btn in self._page_btns:
            vis = (q == "") or (q in name)
            btn.setVisible(vis)
            if vis: any_page = True
        self._pages_lbl.setVisible(any_page)

        # Filter game buttons
        any_game = False
        for name, btn in self._game_btns:
            vis = (q == "") or (q in name)
            btn.setVisible(vis)
            if vis: any_game = True
        self._games_lbl.setVisible(any_game)

        # Logout always visible when no search
        self._logout_btn.setVisible(q == "")

    def update_user_label(self): self.name_btn.setText(self.main_window.current_user or "Guest")
    def _logout(self):
        self.main_window.current_user = None
        self.main_window.toggle_hamburger()
        self.main_window._tb.setVisible(False)
        self.main_window.menuBar().setVisible(False)
        self.main_window.go_to(0)

    def refresh_theme(self):
        """Rebuild all palette-baked stylesheets after a theme change."""
        self.setStyleSheet(f"""
            HamburgerMenuPage {{ background-color:{SURFACE}; border-right:1px solid {EDGE}; }}
            HamburgerMenuPage QWidget {{ background-color:{SURFACE}; }}
            HamburgerMenuPage QLineEdit {{
                background:{PANEL}; color:{TEXT};
                border:1px solid {EDGE}; border-radius:8px; padding:0 10px;
            }}
        """)
        self._close_btn.setStyleSheet(f"QPushButton{{background:{GHOST};color:{DIM};border:1px solid {EDGE};border-radius:8px;font-size: 10pt;text-align:left;padding-left:10px;}}QPushButton:hover{{background:{EDGE};color:{TEXT};}}")
        self.name_btn.setStyleSheet(f"color:{TEXT};background:transparent;border:none;text-align:left;")
        self._scroll.setStyleSheet(f"QScrollArea{{border:none;background:{SURFACE};}}QScrollBar:vertical{{background:{SURFACE};width:4px;border-radius:2px;}}QScrollBar::handle:vertical{{background:{EDGE};border-radius:2px;min-height:20px;}}QScrollBar::handle:vertical:hover{{background:#3b82f6;}}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        self._scroll_content.setStyleSheet(f"background:{SURFACE};")
        for ln in self._sep_widgets:
            ln.setStyleSheet(f"background:{EDGE};max-height:1px;border:none;")
        self._logout_btn.setStyleSheet(f"QPushButton{{background:transparent;color:#f87171;border:none;border-radius:8px;text-align:left;padding-left:10px;font-size: 9pt;}}QPushButton:hover{{background:{GHOST};}}")
        self._pages_lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;padding:4px 4px 2px 4px;letter-spacing:2px;")
        self._games_lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;padding:4px 4px 2px 4px;letter-spacing:2px;")
        for i, (_, btn) in enumerate(self._page_btns):
            color = self._page_btn_colors[i]
            btn.setStyleSheet(f"QPushButton{{background:transparent;color:{DIM};border:none;border-radius:8px;text-align:left;padding-left:12px;font-size: 9pt;}}QPushButton:hover{{background:{GHOST};color:{color};}}")
        for i, (_, btn) in enumerate(self._game_btns):
            key = self._game_btn_colors[i]
            color = NEON[key][0]
            btn.setStyleSheet(f"QPushButton{{background:transparent;color:{DIM};border:none;border-radius:8px;text-align:left;padding-left:12px;font-size: 9pt;}}QPushButton:hover{{background:{GHOST};color:{color};}}")
        self.update()



# ==================== Player Profile Dialog ====================
class _PlayerProfileDialog(QDialog):
    def __init__(self, u, current_user, parent=None):
        """Initialise the instance.

        Args:
            u (dict): User record dict from DataManager.
                    current_user (str | None): Username of the logged-in user.
                    parent (QWidget | None): Optional dialog parent.
        """
        super().__init__(parent)
        is_me = u["user"] == current_user
        title = "My Profile" if is_me else f"{u['user']}'s Profile"
        self.setWindowTitle(title)
        self.setMinimumWidth(420); self.setMinimumHeight(500)
        self.setStyleSheet(f"""
            QDialog {{ background:{SURFACE}; }}
            QLabel {{ background:transparent; color:{TEXT}; border:none; }}
        """)
        lay = QVBoxLayout(self); lay.setContentsMargins(24,24,24,24); lay.setSpacing(14)

        # Header
        hrow = QHBoxLayout(); hrow.setSpacing(16)

        # Avatar — show photo if available, else initial letter
        avatar_path = u.get("avatar", "")
        class _Av(QWidget):
            def __init__(self, name, is_me, av_path):
                """Initialise the instance.

                Args:
                    u (dict): User record dict from DataManager.
                            current_user (str | None): Username of the logged-in user.
                            parent (QWidget | None): Optional dialog parent.
                """
                super().__init__(); self.setFixedSize(72,72)
                self._name = name; self._is_me = is_me
                self._pm = None
                if av_path and os.path.exists(av_path):
                    from PySide6.QtGui import QPixmap
                    pm = QPixmap(av_path)
                    if not pm.isNull():
                        self._pm = pm.scaled(72, 72, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            def paintEvent(self, ev):
                pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
                nc = QColor(NEON["normal"][0]) if self._is_me else QColor("#5a637a")
                clip = QPainterPath(); clip.addEllipse(QPointF(36,36), 34.0, 34.0)
                pa.setClipPath(clip)
                if self._pm:
                    pa.drawPixmap(0, 0, self._pm)
                else:
                    pa.fillPath(clip, QColor(PANEL))
                    pa.setFont(F(22, 700)); pa.setPen(nc)
                    pa.drawText(QRect(0,0,72,72), Qt.AlignCenter, self._name[0].upper() if self._name else "?")
                pa.setClipping(False)
                pa.setPen(QPen(nc, 2.5)); pa.setBrush(Qt.NoBrush)
                pa.drawEllipse(QPointF(36,36), 34.0, 34.0)
                pa.end()
        av_w = _Av(u["user"], is_me, avatar_path); hrow.addWidget(av_w, 0, Qt.AlignVCenter)

        name_col = QVBoxLayout(); name_col.setSpacing(4)
        name_lbl = QLabel(u["user"]); name_lbl.setFont(F(18, 700))
        me_badge = QLabel("  YOU  ") if is_me else None
        if me_badge:
            me_badge.setFont(FM(8, bold=True))
            nc_str = NEON["normal"][0]
            me_badge.setStyleSheet(f"color:{nc_str};background:transparent;border:1px solid {nc_str};border-radius:4px;padding:1px 4px;")
            me_badge.setMaximumWidth(50)
        uid_lbl = QLabel(f"UID: {u['uid']}"); uid_lbl.setFont(FM(9))
        uid_lbl.setStyleSheet(f"color:{DIM};")
        name_col.addWidget(name_lbl)
        if me_badge: name_col.addWidget(me_badge)
        name_col.addWidget(uid_lbl)
        hrow.addLayout(name_col, 1)
        lay.addLayout(hrow)

        # Bio
        bio = u.get("bio", "")
        if bio:
            bio_lbl = QLabel(f'"{bio}"'); bio_lbl.setFont(F(10))
            bio_lbl.setWordWrap(True)
            bio_lbl.setStyleSheet(f"color:{DIM};background:{PANEL};border:1px solid {EDGE};border-radius:8px;padding:6px 10px;")
            lay.addWidget(bio_lbl)

        # Rewards
        rewards = u.get("reward", [])
        rew_row = QHBoxLayout(); rew_row.setSpacing(6)
        rew_title = QLabel("⭐  Rewards:"); rew_title.setFont(F(10, 700))
        rew_title.setStyleSheet(f"color:{TEXT};")
        rew_val = QLabel("  ".join(rewards) if rewards else "None")
        rew_val.setFont(F(10))
        rew_val.setStyleSheet(f"color:{'#fbbf24' if rewards else DIM};")
        rew_row.addWidget(rew_title); rew_row.addWidget(rew_val); rew_row.addStretch()
        lay.addLayout(rew_row)

        # Divider
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:{EDGE};max-height:1px;border:none;"); lay.addWidget(sep)

        # Bar chart
        chart_lbl = QLabel("Game Activity"); chart_lbl.setFont(F(11, 700))
        lay.addWidget(chart_lbl)
        chart = _StatsBarChart()
        chart.set_data([
            ("Normal",    u.get("normal",0),  "#3b82f6"),
            ("Flip",      u.get("flip",0),    "#f59e0b"),
            ("Switch",    u.get("switch",0),  "#10b981"),
            ("Swap",      u.get("swap",0),    "#ec4899"),
            ("CpTime",    u.get("cpm",0),     "#8b5cf6"),
            ("Stopwatch", u.get("stop",0),    "#06b6d4"),
            ("Pop It",    u.get("pop",0),     "#f97316"),
            ("Focus",     u.get("focus",0),   "#e879f9"),
            ("Chaos",     u.get("chaos",0),   "#ff4d4d"),
            ("Memory",    u.get("memory",0),  "#00e5ff"),
            ("Dopamine",  u.get("dopa",0),    "#39ff14"),
            ("ColorShift",u.get("rcs",0),     "#a3e635"),
        ])
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        scroll.setWidget(chart); lay.addWidget(scroll, 1)

        # Close button
        close_btn = QPushButton("Close"); close_btn.setFixedHeight(36)
        close_btn.setStyleSheet(f"QPushButton{{background:{GHOST};color:{DIM};border:1px solid {EDGE};border-radius:10px;font-size: 9pt;}}QPushButton:hover{{background:{EDGE};color:{TEXT};}}")
        close_btn.clicked.connect(self.accept); lay.addWidget(close_btn)


# ==================== RankingPage ====================
class RankingPage(QWidget):
    """Leaderboard page.

    Displays a QTableWidget of players sorted by selected game score.
    Supports category filter buttons, real-time player-name search,
    double-click to view profile, and a right-click context menu.
    """
    STYLES = [
        ("🖱️ Total","total","#858585"),("🖱️ Normal","normal","#3b82f6"),
        ("🪙 Flip","flip","#f59e0b"),("🔘 Switch","switch","#10b981"),
        ("🟣 Pop It","pop","#f97316"),("🔄 Swap","swap","#ec4899"),
        ("⏱️ CPM","cpm","#8b5cf6"),("⏲️ Stop","stop","#06b6d4"),
        ("◈ Focus","focus","#e879f9"),("⚡ Chaos","chaos","#ff4d4d"),
        ("◫ Memory","memory","#00e5ff"),("◑ Dopamine","dopa","#39ff14"),
        ("◐ Color Shift","rcs","#a3e635"),
    ]
    def __init__(self, main_window):
        """Initialise the instance.

        Args:
            main_window (MainWindow): Root window reference.
        """
        super().__init__()
        self.main_window = main_window
        self._cur_field="total"; self._cur_display="Total Click"; self._cur_color="#858585"
        self._btns = {}
        layout = QVBoxLayout(self); layout.setContentsMargins(8,8,8,8); layout.setSpacing(10)
        _hrow = QHBoxLayout(); _hrow.setSpacing(10); _hrow.setContentsMargins(0,0,0,0)
        _hrow.addWidget(_make_back_btn(lambda: main_window.go_to(1)), 0, Qt.AlignVCenter)
        self._htitle = QLabel("🏆 Ranking Page"); self._htitle.setFont(F(16, 700))
        self._htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        _hrow.addWidget(self._htitle, 1, Qt.AlignVCenter)
        layout.addLayout(_hrow)
        self.csl = QLabel("Total Click"); self.csl.setFont(F(13, 700))
        self.csl.setAlignment(Qt.AlignCenter)
        self.csl.setStyleSheet(f"color:{TEXT};background:{PANEL};border:1px solid {EDGE};border-radius:8px;padding:4px;")
        layout.addWidget(self.csl)
        self._bs = QScrollArea(); self._bs.setFixedHeight(44); self._bs.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._bs.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self._bs.setWidgetResizable(False)
        self._bs.setStyleSheet(f"QScrollArea{{background:{BG};border:none;}}QScrollBar:horizontal{{background:{SURFACE};height:4px;border-radius:2px;}}QScrollBar::handle:horizontal{{background:{EDGE};border-radius:2px;min-width:30px;}}QScrollBar::handle:horizontal:hover{{background:#3b82f6;}}QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal{{width:0;}}")
        self._bw = QWidget(); self._bw.setStyleSheet(f"background:{BG};")
        br = QHBoxLayout(self._bw); br.setContentsMargins(0,0,0,0); br.setSpacing(6)
        for label, field, color in self.STYLES:
            btn = QPushButton(label); btn.setCheckable(True); btn.setFixedHeight(32); btn.setFixedWidth(110)
            btn.setStyleSheet(f"QPushButton{{background:{PANEL};color:{DIM};border:1px solid {EDGE};border-radius:8px;font-size: 8pt;font-weight:bold;}}QPushButton:checked{{background:{color}22;color:{color};border:1px solid {color};}}QPushButton:hover{{background:{color}15;color:{color};border:1px solid {color};}}")
            btn.clicked.connect(lambda _, f=field, d=label, c=color: self.load_ranking(f,d,c))
            br.addWidget(btn); self._btns[field] = (btn, color)
        n = len(self.STYLES); self._bw.setFixedWidth(n*110+(n-1)*6+4); self._bs.setWidget(self._bw); layout.addWidget(self._bs)

        # Player search
        search_row = QHBoxLayout(); search_row.setSpacing(8)
        search_icon = QLabel("🔍"); search_icon.setStyleSheet("background:transparent;border:none;")
        self._player_search = QLineEdit(); self._player_search.setPlaceholderText("Filter player…")
        self._player_search.setFixedHeight(32)
        self._player_search.setStyleSheet(f"QLineEdit{{background:{PANEL};color:{TEXT};border:1px solid {EDGE};border-radius:8px;padding:0 10px;font-size: 9pt;}}QLineEdit:focus{{border-color:#3b82f6;}}")
        self._player_search.textChanged.connect(self._filter_rows)
        search_row.addWidget(search_icon); search_row.addWidget(self._player_search)
        layout.addLayout(search_row)

        self.rt = QTableWidget(); self.rt.setColumnCount(3)
        self.rt.setHorizontalHeaderLabels(["Rank","Player","Score"])
        hdr = self.rt.horizontalHeader()
        hdr.setSectionResizeMode(0,QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1,QHeaderView.Stretch)
        hdr.setSectionResizeMode(2,QHeaderView.Stretch)
        self.rt.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rt.setSelectionBehavior(QTableWidget.SelectRows)
        self.rt.verticalHeader().setVisible(False); self.rt.setShowGrid(False)
        self.rt.setCursor(Qt.PointingHandCursor)
        self.rt.itemDoubleClicked.connect(self._on_row_double_click)
        self.rt.setContextMenuPolicy(Qt.CustomContextMenu)
        self.rt.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.rt)

        # Hint label
        hint = QLabel("  Double-click a player to view their profile")
        hint.setFont(F(9)); hint.setStyleSheet(f"color:{DIM};background:transparent;border:none;")
        layout.addWidget(hint)

    def refresh(self): self.load_ranking(self._cur_field, self._cur_display, self._cur_color)

    def refresh_theme(self):
        """Rebuild palette-baked stylesheets after a theme change."""
        self._htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        self.csl.setStyleSheet(f"color:{self._cur_color};background:{PANEL};border:1px solid {EDGE};border-radius:8px;padding:4px;")
        self._bs.setStyleSheet(f"QScrollArea{{background:{BG};border:none;}}QScrollBar:horizontal{{background:{SURFACE};height:4px;border-radius:2px;}}QScrollBar::handle:horizontal{{background:{EDGE};border-radius:2px;min-width:30px;}}QScrollBar::handle:horizontal:hover{{background:#3b82f6;}}QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal{{width:0;}}")
        self._bw.setStyleSheet(f"background:{BG};")
        self._player_search.setStyleSheet(f"QLineEdit{{background:{PANEL};color:{TEXT};border:1px solid {EDGE};border-radius:8px;padding:0 10px;font-size: 9pt;}}QLineEdit:focus{{border-color:#3b82f6;}}")
        for field, (btn, color) in self._btns.items():
            btn.setStyleSheet(f"QPushButton{{background:{PANEL};color:{DIM};border:1px solid {EDGE};border-radius:8px;font-size: 8pt;font-weight:bold;}}QPushButton:checked{{background:{color}22;color:{color};border:1px solid {color};}}QPushButton:hover{{background:{color}15;color:{color};border:1px solid {color};}}")
        # Re-render table rows so medal tints and text colours update
        self.load_ranking(self._cur_field, self._cur_display, self._cur_color)
    def _filter_rows(self, text):
        """Execute filter rows.

        Args:
            text (str): Filter query; rows whose player name does not contain this text are hidden.

        Examples:
            >>> page._filter_rows('ali')
        """
        q = text.strip().lower()
        for row in range(self.rt.rowCount()):
            item = self.rt.item(row, 1)
            self.rt.setRowHidden(row, bool(q and item and q not in item.text().lower()))

    def _on_row_double_click(self, item):
        """Execute on row double click.

        Args:
            item (QTableWidgetItem): The double-clicked cell.
        """
        row = item.row()
        username = self.rt.item(row, 1).text() if self.rt.item(row, 1) else None
        if not username: return
        u = self.main_window.db.get_user(username)
        if not u: return
        dlg = _PlayerProfileDialog(u, self.main_window.current_user, self)
        dlg.exec()

    def _show_context_menu(self, pos):
        """Execute show context menu.

        Args:
            pos (QPoint): Viewport-relative position of the right-click.
        """
        from PySide6.QtWidgets import QMenu
        item = self.rt.itemAt(pos)
        if not item: return
        row = item.row()
        username_item = self.rt.item(row, 1)
        if not username_item: return
        username = username_item.text()

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background:{PANEL}; color:{TEXT}; border:1px solid {EDGE}; border-radius:8px; padding:4px; }}
            QMenu::item {{ padding:6px 20px; border-radius:6px; }}
            QMenu::item:selected {{ background:{GHOST}; color:{TEXT}; }}
            QMenu::separator {{ background:{EDGE}; height:1px; margin:4px 8px; }}
        """)
        view_act = QAction(f"👤  View {username}'s Profile", self)
        view_act.triggered.connect(lambda: self._open_profile(username))
        menu.addAction(view_act)

        if username == self.main_window.current_user:
            menu.addSeparator()
            go_act = QAction("🔗  Go to My Profile Page", self)
            go_act.triggered.connect(lambda: self.main_window.go_to(6))
            menu.addAction(go_act)

        menu.exec(self.rt.viewport().mapToGlobal(pos))

    def _open_profile(self, username):
        """Execute open profile.

        Args:
            username (str): Username whose profile dialog to open.
        """
        u = self.main_window.db.get_user(username)
        if u:
            dlg = _PlayerProfileDialog(u, self.main_window.current_user, self)
            dlg.exec()

    def load_ranking(self, field, display_name, color="#e8ecff"):
        """Execute load ranking.

        Args:
            field (str): Score field to sort by.
                    display_name (str): Human-readable category label.
                    color (str): Hex row highlight colour.

        Examples:
            >>> page.load_ranking('flip', 'Flip Coin', '#f59e0b')
        """
        self._cur_field=field; self._cur_display=display_name; self._cur_color=color
        self._player_search.blockSignals(True); self._player_search.clear(); self._player_search.blockSignals(False)
        self.csl.setText(display_name)
        self.csl.setStyleSheet(f"color:{color};background:{PANEL};border:1px solid {EDGE};border-radius:8px;padding:4px;")
        for f,(btn,c) in self._btns.items(): btn.setChecked(f==field)
        data = self.main_window.db.get_all_scores(field)
        self.rt.setRowCount(len(data))
        medal={0:"🥇",1:"🥈",2:"🥉"}
        # Medal row tints: blend the accent colour lightly into the surface
        def _medal_bg(rank, color):
            nc = QColor(color); s = QColor(SURFACE)
            mix = 0.18 if rank == 0 else (0.10 if rank == 1 else 0.06)
            return QColor(
                int(s.red()   * (1-mix) + nc.red()   * mix),
                int(s.green() * (1-mix) + nc.green() * mix),
                int(s.blue()  * (1-mix) + nc.blue()  * mix),
            )
        for row,(username,score) in enumerate(data):
            ri=QTableWidgetItem(medal.get(row,str(row+1))); pi=QTableWidgetItem(username); si=QTableWidgetItem(f"{score:,}")
            bg=_medal_bg(row, color) if row in medal else QColor(PANEL); is_me=username==self.main_window.current_user
            for item in [ri,pi,si]:
                item.setTextAlignment(Qt.AlignCenter); item.setBackground(bg)
                item.setForeground(QColor(color if is_me else TEXT))
            self.rt.setItem(row,0,ri); self.rt.setItem(row,1,pi); self.rt.setItem(row,2,si)


# ==================== TaskPage ====================
class TaskPage(QWidget):
    TASKS = [
        ("100click","🖱️","Normal Click\n100 times","normal",100),
        ("200flip","🪙","Flip Coin\n200 times","flip",200),
        ("1000switch","🔘","Switch\n1,000 times","switch",1000),
        ("300pop","🟣","Pop It\n300 times","pop",300),
        ("150swap","🔄","Swap Click\n150 times","swap",150),
        ("50cpm","⏱️","Click per Time\n50 times","cpm",50),
        ("100focus","◈","Focus Burst\n100 times","focus",100),
        ("200chaos","⚡","Chaos Control\n200 times","chaos",200),
        ("100memory","◫","Memory Flash\n100 times","memory",100),
        ("500dopa","◑","Dopamine Meter\n500 times","dopa",500),
        ("300rcs","◐","Color Shift\n300 times","rcs",300),
    ]
    def __init__(self, main_window):
        """Initialise the instance.

        Args:
            main_window (MainWindow): Root window reference.
        """
        super().__init__()
        self.main_window = main_window
        self.lm = QVBoxLayout(self); self.lm.setContentsMargins(8,8,8,8); self.lm.setSpacing(8)
        _hrow = QHBoxLayout(); _hrow.setSpacing(10); _hrow.setContentsMargins(0,0,0,0)
        _hrow.addWidget(_make_back_btn(lambda: main_window.go_to(1)), 0, Qt.AlignVCenter)
        _htitle = QLabel("📋 Task Page"); _htitle.setFont(F(16, 700))
        _htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        _hrow.addWidget(_htitle, 1, Qt.AlignVCenter)
        self.lm.addLayout(_hrow)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.lm.addWidget(self.scroll)
        self._build_content()

    def _build_content(self):
        old = self.scroll.takeWidget()
        if old: old.deleteLater()
        username = self.main_window.current_user; db = self.main_window.db
        user_data = db.get_user(username) if username else None
        sc = QWidget(); sc.setStyleSheet("background:transparent;")
        grid = QGridLayout(sc); grid.setSpacing(10); grid.setContentsMargins(4,4,4,4); grid.setAlignment(Qt.AlignTop)
        for i,(rid,icon,name,field,total) in enumerate(self.TASKS):
            current = int(user_data[field]) if user_data else 0
            claimed = db.has_reward(username,rid) if username else False
            grid.addWidget(self._make_card(rid,icon,name,current,total,claimed), i//2, i%2)
        self.scroll.setWidget(sc)

    def refresh(self): self._build_content()
    def _make_card(self, rid, icon, name, current, total, claimed):
        done = current >= total
        bc,bgc = ("#4ade80","#021308") if claimed else (("#fbbf24","#130e00") if done else (EDGE,PANEL))
        card = QFrame(); card.setFixedHeight(190); card.setObjectName("TCard")
        card.setStyleSheet(f"#TCard{{background:{bgc};border:1px solid {bc};border-radius:12px;}}")
        v = QVBoxLayout(card); v.setSpacing(6); v.setContentsMargins(10,10,10,10)
        il = QLabel(icon); il.setFont(F(26)); il.setAlignment(Qt.AlignCenter)
        il.setStyleSheet("border:none;background:transparent;"); v.addWidget(il)
        nl = QLabel(name); nl.setFont(F(10, 700)); nl.setAlignment(Qt.AlignCenter)
        nl.setStyleSheet(f"color:{TEXT};border:none;background:transparent;"); v.addWidget(nl)
        cc = "#4ade80" if (claimed or done) else "#3b82f6"
        bar = QProgressBar(); bar.setMinimum(0); bar.setMaximum(total); bar.setValue(min(current,total))
        bar.setFormat(f"{min(current,total):,} / {total:,}"); bar.setFixedHeight(22); bar.setAlignment(Qt.AlignCenter)
        bar.setStyleSheet(f"QProgressBar{{border:1px solid {EDGE};border-radius:8px;background:{SURFACE};color:{TEXT};font-size: 8pt;}}QProgressBar::chunk{{background:{cc};border-radius:7px;}}")
        v.addWidget(bar)
        if claimed:
            btn=QPushButton("✅  Claimed"); btn.setEnabled(False)
            btn.setStyleSheet("QPushButton{background:#021308;color:#4ade80;border:1px solid #4ade80;border-radius:8px;font-weight:bold;}")
        elif done:
            btn=QPushButton("🎁  Claim Reward")
            btn.setStyleSheet("QPushButton{background:#78350f;color:#fbbf24;border:1px solid #fbbf24;border-radius:8px;font-weight:bold;}QPushButton:hover{background:#92400e;}")
            btn.clicked.connect(lambda _, r=rid: self._claim(r))
        else:
            btn=QPushButton("🔒  Cannot Claim Yet"); btn.setEnabled(False)
            btn.setStyleSheet(f"QPushButton{{background:{GHOST};color:{DIM};border:1px solid {EDGE};border-radius:8px;}}")
        btn.setFixedHeight(34); v.addWidget(btn); return card

    def _claim(self, rid):
        u = self.main_window.current_user
        if not u: return
        self.main_window.db.add_reward(u, rid)
        self.main_window.reward_page.refresh(); self.refresh()


# ==================== RewardPage ====================
class RewardPage(QWidget):
    REWARDS = [
        ("100click","🖱️","Normal Click\n100 times","normal",100),
        ("200flip","🪙","Flip Coin\n200 times","flip",200),
        ("1000switch","🔘","Switch\n1,000 times","switch",1000),
        ("300pop","🟣","Pop It\n300 times","pop",300),
        ("150swap","🔄","Swap Click\n150 times","swap",150),
        ("50cpm","⏱️","Click per Time\n50 times","cpm",50),
        ("100focus","◈","Focus Burst\n100 times","focus",100),
        ("200chaos","⚡","Chaos Control\n200 times","chaos",200),
        ("100memory","◫","Memory Flash\n100 times","memory",100),
        ("500dopa","◑","Dopamine Meter\n500 times","dopa",500),
        ("300rcs","◐","Color Shift\n300 times","rcs",300),
    ]
    def __init__(self, main_window):
        """Initialise the instance.

        Args:
            main_window (MainWindow): Root window reference.
        """
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self); layout.setContentsMargins(8,8,8,8); layout.setSpacing(8)
        _hrow = QHBoxLayout(); _hrow.setSpacing(10); _hrow.setContentsMargins(0,0,0,0)
        _hrow.addWidget(_make_back_btn(lambda: main_window.go_to(1)), 0, Qt.AlignVCenter)
        _htitle = QLabel("⭐ Reward Page"); _htitle.setFont(F(16, 700))
        _htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        _hrow.addWidget(_htitle, 1, Qt.AlignVCenter)
        layout.addLayout(_hrow)
        sl = QLabel("Tasks you have completed"); sl.setFont(F(10))
        sl.setStyleSheet(f"color:{DIM};background:transparent;"); layout.addWidget(sl)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sc = QWidget(); self.sc.setStyleSheet("background:transparent;")
        self.grid = QGridLayout(self.sc); self.grid.setSpacing(10); self.grid.setContentsMargins(4,4,4,4); self.grid.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.sc); layout.addWidget(scroll)

    def refresh(self):
        """Execute refresh.
        """
        for i in reversed(range(self.grid.count())):
            if w := self.grid.itemAt(i).widget(): w.setParent(None)
        username = self.main_window.current_user; db = self.main_window.db
        for i,(rid,badge,name,field,threshold) in enumerate(self.REWARDS):
            unlocked = db.has_reward(username,rid) if username else False
            pct = db.get_reward_percent(rid)
            self.grid.addWidget(self._make_card(badge,name,pct,unlocked), i//2, i%2)

    def _make_card(self, badge, name, percent, unlocked):
        bc="#fbbf24" if unlocked else EDGE; bgc="#130e00" if unlocked else PANEL
        card=QFrame(); card.setFixedHeight(210); card.setObjectName("RCard")
        card.setStyleSheet(f"#RCard{{background:{bgc};border:1px solid {bc};border-radius:12px;}}")
        v=QVBoxLayout(card); v.setSpacing(6); v.setContentsMargins(10,10,10,10)
        il=QLabel(badge if unlocked else "🔒"); il.setFont(F(28)); il.setAlignment(Qt.AlignCenter)
        il.setStyleSheet("border:none;background:transparent;"); v.addWidget(il)
        nl=QLabel(name); nl.setFont(F(10, 700)); nl.setAlignment(Qt.AlignCenter)
        nl.setStyleSheet(f"color:{TEXT if unlocked else DIM};border:none;background:transparent;"); v.addWidget(nl)
        ol=QLabel(f"{percent:.1f}% of all players have this"); ol.setFont(F(8)); ol.setAlignment(Qt.AlignCenter)
        ol.setStyleSheet(f"color:{DIM};border:none;background:transparent;"); ol.setWordWrap(True); v.addWidget(ol)
        if percent>=50: rt,rc="Common","#4ade80"
        elif percent>=10: rt,rc="Uncommon","#60a5fa"
        elif percent>=1: rt,rc="Rare","#c084fc"
        else: rt,rc="🔥 Legendary","#f97316"
        rl=QLabel(rt if unlocked else "???"); rl.setFont(F(9, 700)); rl.setAlignment(Qt.AlignCenter)
        rl.setStyleSheet(f"color:{rc if unlocked else GHOST};border:none;background:transparent;"); v.addWidget(rl)
        return card


# ==================== SettingPage ====================
class _ThemeToggle(QWidget):
    """Animated pill-shaped toggle switch for dark / light theme."""
    toggled = Signal(bool)  # emits True = dark, False = light

    def __init__(self, is_dark=True, parent=None):
        super().__init__(parent)
        self.setFixedSize(64, 32)
        self.setCursor(Qt.PointingHandCursor)
        self._dark = is_dark
        self._pos = 1.0 if is_dark else 0.0   # 0.0 = light, 1.0 = dark
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

        # Track background: interpolate dark-neon-blue ↔ warm-light-amber
        t = self._pos   # 1 = dark, 0 = light
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

        # Neon border
        border_c = QColor("#3b82f6") if self._dark else QColor("#f59e0b")
        pa.strokePath(track_path, QPen(border_c, 1.5))

        # Icons: moon (dark) on the left, sun (light) on the right
        pa.setFont(F(9, 400))
        pa.setPen(QColor(255, 255, 255, 100))
        pa.drawText(QRect(4, 0, 20, h), Qt.AlignCenter, "🌙")
        pa.drawText(QRect(w-24, 0, 20, h), Qt.AlignCenter, "☀")

        # Thumb
        margin = 3
        travel = w - h            # total horizontal travel
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

        # Thumb glow
        glow_pen = QPen(QColor(thumb_c.red(), thumb_c.green(), thumb_c.blue(), 80), 5)
        pa.setPen(glow_pen); pa.setBrush(Qt.NoBrush)
        pa.drawEllipse(QPointF(cx, cy), thumb_r + 2, thumb_r + 2)
        pa.end()


class SettingPage(QWidget):
    def __init__(self, main_window):
        """Initialise the instance.

        Args:
            main_window (MainWindow): Root window reference.
        """
        super().__init__()
        self._main_window = main_window
        self._is_dark = True   # start in dark mode

        layout = QVBoxLayout(self); layout.setContentsMargins(16,16,16,16)
        layout.setSpacing(12)

        # ── Header row ────────────────────────────────────────
        _hrow = QHBoxLayout(); _hrow.setSpacing(10); _hrow.setContentsMargins(0,0,0,0)
        _hrow.addWidget(_make_back_btn(lambda: main_window.go_to(1)), 0, Qt.AlignVCenter)
        self._htitle = QLabel("⚙️  Settings"); self._htitle.setFont(F(16, 700))
        self._htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        _hrow.addWidget(self._htitle, 1, Qt.AlignVCenter)
        layout.addLayout(_hrow)

        layout.addSpacing(24)

        # ── Theme toggle row ──────────────────────────────────
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
        """Switch the whole application between dark and light themes.

        Args:
            is_dark (bool): True  -> apply dark neon palette.
                            False -> apply light palette.
        """
        self._is_dark = is_dark

        # 1. Mutate all module-level palette globals (BG, PANEL, TEXT …)
        apply_theme(is_dark)

        # 2. Rebuild and apply the global Qt stylesheet
        app = QApplication.instance()
        if app:
            app.setStyleSheet(
                _build_stylesheet(_DARK_PALETTE if is_dark else _LIGHT_PALETTE)
            )

        # 3. Rebuild stylesheets on widgets that baked colours at init time,
        #    and force a full repaint of every custom-painted widget.
        self._main_window.refresh_theme()

        # 4. Update the subtitle label on this settings card
        self._theme_sub.setText("Dark mode" if is_dark else "Light mode")

        # 5. Refresh this page's own widgets with the new palette
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


# ==================== ProfilePage ====================
class _AvatarDropZone(QWidget):
    """Drag-and-drop zone for profile picture. Shows current avatar or upload prompt."""
    avatar_changed = Signal(str)  # emits file path

    def __init__(self, neon="#3b82f6", parent=None):
        """Initialise the instance.

        Args:
            neon (str): Hex accent colour.
                    parent (QWidget | None): Optional parent widget.
        """
        super().__init__(parent)
        self._neon = neon; self._avatar_path = None; self._pixmap = None
        self._hover = False; self._drag_over = False; self._phase = 0.0
        self.setFixedSize(120, 120); self.setAcceptDrops(True); self.setCursor(Qt.PointingHandCursor)
        self._anim = QTimer(self); self._anim.setInterval(30)
        self._anim.timeout.connect(self._step); self._anim.start()

    def set_avatar(self, path):
        """Execute set avatar.

        Args:
            path (str): Absolute path to the image file.

        Examples:
            >>> zone.set_avatar('C:/photos/me.png')
        """
        from PySide6.QtGui import QPixmap
        self._avatar_path = path
        pm = QPixmap(path)
        if not pm.isNull():
            self._pixmap = pm.scaled(120, 120, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.update()

    def clear_avatar(self):
        self._avatar_path = None; self._pixmap = None; self.update()

    def _step(self): self._phase = (self._phase + 0.04) % (math.pi*2); self.update()

    def dragEnterEvent(self, e):
        """Accept drag events carrying image file URLs.

        Args:
            e (QDragEnterEvent): Drag-enter event from Qt.
        """
        if e.mimeData().hasUrls(): self._drag_over = True; e.acceptProposedAction(); self.update()

    def dragLeaveEvent(self, e): self._drag_over = False; self.update()

    def dropEvent(self, e):
        """Handle a drop event and load the image.

        Args:
            e (QDropEvent): Drop event from Qt.
        """
        self._drag_over = False
        urls = e.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.avatar_changed.emit(path)
        self.update()

    def mousePressEvent(self, e):
        """Handle mouse press.

        Args:
            e (QMouseEvent): Mouse event; opens QFileDialog.
        """
        if e.button() == Qt.LeftButton:
            from PySide6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(self, "Select Profile Picture", "",
                                                   "Images (*.png *.jpg *.jpeg)")
            if path: self.avatar_changed.emit(path)

    def enterEvent(self, e): self._hover = True;  self.update()
    def leaveEvent(self, e): self._hover = False; self.update()

    def paintEvent(self, ev):
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w = h = self.width(); r = w // 2
        nc = QColor(self._neon); pulse = 0.5 + 0.5*math.sin(self._phase)

        # Clip to circle
        clip = QPainterPath(); clip.addEllipse(QPointF(r, r), float(r-2), float(r-2))
        pa.setClipPath(clip)

        if self._pixmap:
            pa.drawPixmap(0, 0, self._pixmap)
        else:
            # Surface bg (theme-aware)
            pa.fillPath(clip, QColor(SURFACE))
            # Cloud upload icon
            pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), int(140+80*pulse)))
            pa.setFont(F(28, 400)); pa.drawText(QRect(0, 18, w, 40), Qt.AlignCenter, "☁")
            pa.setFont(F(8, 500))
            pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), int(120+60*pulse)))
            pa.drawText(QRect(0, 72, w, 30), Qt.AlignCenter, "DROP / CLICK")

        pa.setClipping(False)

        # Outer ring
        is_active = self._drag_over or self._hover
        ring_a = int(220 if self._drag_over else (180 if self._hover else (100+60*pulse)))
        ring_w = 3.0 if is_active else 2.0
        pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), ring_a), ring_w))
        pa.setBrush(Qt.NoBrush)
        pa.drawEllipse(QPointF(r, r), float(r-2), float(r-2))

        # Glow
        if is_active:
            glow = QPen(QColor(nc.red(), nc.green(), nc.blue(), 50), 8)
            pa.setPen(glow); pa.drawEllipse(QPointF(r, r), float(r+1), float(r+1))
        pa.end()


class _ConfirmAvatarDialog(QDialog):
    """Modal confirmation dialog before applying profile picture."""
    def __init__(self, path, parent=None):
        """Initialise the instance.

        Args:
            path (str): Path of the candidate avatar image.
                    parent (QWidget | None): Optional dialog parent.
        """
        super().__init__(parent)
        self.setWindowTitle("Change Profile Picture")
        self.setFixedSize(360, 320)
        self.setStyleSheet(f"""
            QDialog {{ background:{SURFACE}; border:1px solid {EDGE}; border-radius:16px; }}
            QLabel {{ background:transparent; color:{TEXT}; }}
            QPushButton {{ border-radius:10px; font-size: 10pt; font-weight:700; padding:8px 20px; }}
        """)
        lay = QVBoxLayout(self); lay.setContentsMargins(24,24,24,24); lay.setSpacing(16)

        title = QLabel("Use this photo as profile picture?")
        title.setFont(F(13, 700)); title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color:{TEXT};"); lay.addWidget(title)

        # Preview
        from PySide6.QtGui import QPixmap
        preview = QLabel(); preview.setFixedSize(120, 120); preview.setAlignment(Qt.AlignCenter)
        pm = QPixmap(path)
        if not pm.isNull():
            pm = pm.scaled(120, 120, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            # Circular clip via mask
            mask_pm = pm.copy()
            preview.setPixmap(mask_pm)
        preview.setStyleSheet(f"border:2px solid {NEON['normal'][0]};border-radius:60px;")
        lay.addWidget(preview, 0, Qt.AlignCenter)

        sub = QLabel(path.split("/")[-1].split("\\")[-1])
        sub.setFont(F(9)); sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"color:{DIM};"); lay.addWidget(sub)

        lay.addStretch()

        btns = QHBoxLayout(); btns.setSpacing(10)
        cancel = QPushButton("Cancel"); cancel.setFixedHeight(40)
        cancel.setStyleSheet(f"QPushButton{{background:{GHOST};color:{DIM};border:1px solid {EDGE};}}QPushButton:hover{{background:{EDGE};color:{TEXT};}}")
        cancel.clicked.connect(self.reject)

        confirm = QPushButton("✓  Set as Profile Photo"); confirm.setFixedHeight(40)
        nc = QColor(NEON['normal'][0]); r,g,b = nc.red(),nc.green(),nc.blue()
        confirm.setStyleSheet(f"QPushButton{{background:rgba({r},{g},{b},200);color:{TEXT};border:none;}}QPushButton:hover{{background:rgba({r},{g},{b},255);}}")
        confirm.clicked.connect(self.accept)

        btns.addWidget(cancel); btns.addWidget(confirm)
        lay.addLayout(btns)


class ProfilePage(QWidget):
    """User profile page.

    Features: avatar drop zone, in-place bio editing, reward display,
    and an animated bar chart of game activity scores.
    Data is persisted to the CSV via DataManager.
    """
    def __init__(self, main_window):
        """Initialise the instance.

        Args:
            main_window (MainWindow): Root window reference.
        """
        super().__init__()
        self.main_window = main_window
        self._avatar_path = None
        self._bio_text = "Click here to write something about yourself…"
        layout = QVBoxLayout(self); layout.setContentsMargins(16,16,16,16); layout.setSpacing(12)

        # ── Header row ───────────────────────────────────────
        _hrow = QHBoxLayout(); _hrow.setSpacing(10); _hrow.setContentsMargins(0,0,0,0)
        _hrow.addWidget(_make_back_btn(lambda: main_window.go_to(1)), 0, Qt.AlignVCenter)
        self._htitle = QLabel("👤 My Profile"); self._htitle.setFont(F(16, 700))
        self._htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        _hrow.addWidget(self._htitle, 1, Qt.AlignVCenter)
        layout.addLayout(_hrow)

        # ── Avatar + name + bio card ─────────────────────────
        self._profile_card = QFrame()
        self._profile_card.setStyleSheet(f"QFrame{{background:{PANEL};border:1px solid {EDGE};border-radius:16px;}}")
        card_lay = QVBoxLayout(self._profile_card); card_lay.setContentsMargins(20,20,20,20); card_lay.setSpacing(12)

        top = QHBoxLayout(); top.setSpacing(18)
        self.avatar_zone = _AvatarDropZone(NEON["normal"][0])
        self.avatar_zone.avatar_changed.connect(self._on_avatar_drop)
        top.addWidget(self.avatar_zone, 0, Qt.AlignTop)

        name_col = QVBoxLayout(); name_col.setSpacing(3); name_col.setAlignment(Qt.AlignVCenter)
        self.name_lbl = QLabel("—"); self.name_lbl.setFont(F(20, 700))
        self.name_lbl.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        self.uid_lbl = QLabel("—"); self.uid_lbl.setFont(FM(9))
        self.uid_lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;")
        name_col.addWidget(self.name_lbl); name_col.addWidget(self.uid_lbl)
        top.addLayout(name_col, 1)
        card_lay.addLayout(top)

        # ── In-place bio editor (click label to edit) ─────────
        from PySide6.QtWidgets import QStackedWidget as _SW
        self._bio_stack = _SW()
        self._bio_stack.setStyleSheet("background:transparent;")

        class _ClickLabel(QLabel):
            clicked = Signal()
            def mousePressEvent(self, e):
                if e.button() == Qt.LeftButton: self.clicked.emit()
            def enterEvent(self, e): self.setCursor(Qt.IBeamCursor)
            def leaveEvent(self, e): self.unsetCursor()

        self._bio_label = _ClickLabel(self._bio_text)
        self._bio_label.setFont(F(10)); self._bio_label.setWordWrap(True)
        self._bio_label.setStyleSheet(
            f"color:{DIM};background:transparent;border:none;"
            f"padding:4px 2px;"
        )
        self._bio_label.clicked.connect(self._bio_start_edit)

        self._bio_edit = QLineEdit(self._bio_text)
        self._bio_edit.setFont(F(10))
        self._bio_edit.setStyleSheet(f"""
            QLineEdit{{
                color:{TEXT};background:{SURFACE};
                border:1px solid {NEON['normal'][0]};
                border-radius:8px;padding:4px 8px;
            }}
        """)
        self._bio_edit.returnPressed.connect(self._bio_confirm)
        self._bio_edit.editingFinished.connect(self._bio_confirm)

        self._bio_stack.addWidget(self._bio_label)   # index 0 = view
        self._bio_stack.addWidget(self._bio_edit)    # index 1 = edit
        card_lay.addWidget(self._bio_stack)
        layout.addWidget(self._profile_card)

        # ── Rewards section ───────────────────────────────────
        rew_row = QHBoxLayout(); rew_row.setSpacing(8)
        rew_icon = QLabel("⭐"); rew_icon.setFont(F(13))
        rew_icon.setStyleSheet("background:transparent;border:none;")
        rew_title = QLabel("Rewards"); rew_title.setFont(F(12, 700))
        rew_title.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        rew_row.addWidget(rew_icon); rew_row.addWidget(rew_title); rew_row.addStretch()
        layout.addLayout(rew_row)
        self._rewards_lbl = QLabel("No rewards yet"); self._rewards_lbl.setFont(F(11))
        self._rewards_lbl.setWordWrap(True)
        self._rewards_lbl.setStyleSheet(f"color:{DIM};background:{PANEL};border:1px solid {EDGE};border-radius:10px;padding:8px 12px;")
        layout.addWidget(self._rewards_lbl)

        # ── Bar chart ─────────────────────────────────────────
        chart_title = QLabel("Game Activity"); chart_title.setFont(F(12, 700))
        chart_title.setStyleSheet(f"color:{TEXT};background:transparent;")
        layout.addWidget(chart_title)

        self._chart = _StatsBarChart()
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        scroll.setWidget(self._chart)
        layout.addWidget(scroll, 1)

    # ── bio editing ──────────────────────────────────────────
    def _bio_start_edit(self):
        """Execute bio start edit.
        """
        self._bio_edit.setText(self._bio_text)
        self._bio_stack.setCurrentIndex(1)
        self._bio_edit.setFocus(); self._bio_edit.selectAll()

    def _bio_confirm(self):
        """Execute bio confirm.
        """
        txt = self._bio_edit.text().strip()
        if txt: self._bio_text = txt
        self._bio_label.setText(self._bio_text)
        self._bio_stack.setCurrentIndex(0)
        u = self.main_window.current_user
        if u:
            self.main_window.db.update_bio(u, self._bio_text)
            show_toast(self, "✓  Bio saved", "#3b82f6")

    def _on_avatar_drop(self, path):
        dlg = _ConfirmAvatarDialog(path, self)
        if dlg.exec() == QDialog.Accepted:
            self._avatar_path = path
            self.avatar_zone.set_avatar(path)
            u = self.main_window.current_user
            if u:
                self.main_window.db.update_avatar(u, path)
                show_toast(self, "✓  Profile photo updated", "#3b82f6")

    def refresh(self):
        """Execute refresh.
        """
        u_name = self.main_window.current_user
        if not u_name: return
        u = self.main_window.db.get_user(u_name)
        if not u: return
        self.name_lbl.setText(u["user"]); self.uid_lbl.setText(f"UID: {u['uid']}")
        # Load saved avatar
        saved_av = u.get("avatar", "")
        if saved_av and os.path.exists(saved_av):
            self.avatar_zone.set_avatar(saved_av)
        # Load saved bio
        saved_bio = u.get("bio", "")
        if saved_bio:
            self._bio_text = saved_bio
            self._bio_label.setText(self._bio_text)
            self._bio_edit.setText(self._bio_text)
        self._chart.set_data([
            ("Normal",   u.get("normal",0), "#3b82f6"),
            ("Flip",     u.get("flip",0),   "#f59e0b"),
            ("Switch",   u.get("switch",0), "#10b981"),
            ("Swap",     u.get("swap",0),   "#ec4899"),
            ("CpTime",   u.get("cpm",0),    "#8b5cf6"),
            ("Stopwatch",u.get("stop",0),   "#06b6d4"),
            ("Pop It",   u.get("pop",0),    "#f97316"),
            ("Focus",    u.get("focus",0),  "#e879f9"),
            ("Chaos",    u.get("chaos",0),  "#ff4d4d"),
            ("Memory",   u.get("memory",0), "#00e5ff"),
            ("Dopamine", u.get("dopa",0),   "#39ff14"),
            ("ColorShift",u.get("rcs",0),   "#a3e635"),
        ])
        # Rewards
        rewards = u.get("reward", [])
        self._rewards_lbl.setText("  ".join(rewards) if rewards else "No rewards yet")

    def refresh_theme(self):
        """Rebuild palette-baked stylesheets after a theme change."""
        self._htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        self._profile_card.setStyleSheet(f"QFrame{{background:{PANEL};border:1px solid {EDGE};border-radius:16px;}}")
        self.name_lbl.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        self.uid_lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;")
        self._bio_label.setStyleSheet(f"color:{DIM};background:transparent;border:none;padding:4px 2px;")
        self._bio_edit.setStyleSheet(f"QLineEdit{{color:{TEXT};background:{SURFACE};border:1px solid {NEON['normal'][0]};border-radius:8px;padding:4px 8px;}}")
        self._rewards_lbl.setStyleSheet(f"color:{DIM};background:{PANEL};border:1px solid {EDGE};border-radius:10px;padding:8px 12px;")
        self.avatar_zone.update()
        self.update()


class _StatsBarChart(QWidget):
    """Neon horizontal bar chart with animated fills, glow caps, and top-game crown."""
    ROW_H  = 50
    BAR_H  = 18
    PAD_L  = 82
    PAD_R  = 72
    PAD_T  = 10

    def __init__(self, parent=None):
        """Initialise the instance.

        Args:
            parent (QWidget | None): Optional parent widget.
        """
        super().__init__(parent)
        self._data: list = []   # (label, value, color)
        self._fills: list = []  # current animated fill 0-1
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
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
        if not self._data: return
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        W  = self.width()
        bar_area = W - self.PAD_L - self.PAD_R
        mx_val = max(v for _, v, _ in self._data) or 1
        # find top game
        top_i = max(range(len(self._data)), key=lambda i: self._data[i][1])
        pulse = 0.5 + 0.5 * math.sin(self._glow_t)

        for i, (label, val, color) in enumerate(self._data):
            y  = self.PAD_T + i * self.ROW_H
            cy = y + self.ROW_H // 2
            by = cy - self.BAR_H // 2
            nc = QColor(color); r, g, b = nc.red(), nc.green(), nc.blue()
            is_top = (i == top_i and val > 0)

            # ── label ────────────────────────────────────────
            lbl_color = QColor(TEXT) if is_top else QColor(DIM)
            pa.setFont(F(9, 700 if is_top else 400))
            pa.setPen(lbl_color)
            pa.drawText(QRect(0, by, self.PAD_L - 8, self.BAR_H),
                        Qt.AlignRight | Qt.AlignVCenter, label)

            # ── track ────────────────────────────────────────
            track = QPainterPath()
            track.addRoundedRect(QRectF(self.PAD_L, by, bar_area, self.BAR_H), 5, 5)
            pa.fillPath(track, QColor(GHOST))

            # ── fill ─────────────────────────────────────────
            fw = self._fills[i] * bar_area
            if fw > 2:
                fill = QPainterPath()
                fill.addRoundedRect(QRectF(self.PAD_L, by, fw, self.BAR_H), 5, 5)
                grad = QLinearGradient(self.PAD_L, 0, self.PAD_L + fw, 0)
                grad.setColorAt(0.0, QColor(r, g, b, 100))
                grad.setColorAt(0.6, QColor(r, g, b, 200))
                grad.setColorAt(1.0, QColor(r, g, b, 255))
                pa.fillPath(fill, QBrush(grad))

                # glow inner highlight line
                pa.setPen(QPen(QColor(255,255,255,35), 1))
                pa.drawLine(QPointF(self.PAD_L + 4, by + 3),
                            QPointF(self.PAD_L + fw - 4, by + 3))

                # end-cap glow
                glow_alpha = int(80 + 60 * pulse) if is_top else 55
                cap_x = self.PAD_L + fw
                for radius, alpha_mult in ((14, 0.6), (8, 1.0)):
                    grd = QRadialGradient(cap_x, cy, radius)
                    grd.setColorAt(0, QColor(r, g, b, int(glow_alpha * alpha_mult)))
                    grd.setColorAt(1, QColor(r, g, b, 0))
                    pa.fillRect(QRectF(cap_x - radius, cy - radius, radius*2, radius*2),
                                QBrush(grd))

                # outer glow for top bar (pulsing)
                if is_top:
                    outer = QPen(QColor(r, g, b, int(60 + 50 * pulse)), 3)
                    pa.setPen(outer); pa.setBrush(Qt.NoBrush)
                    pa.drawRoundedRect(QRectF(self.PAD_L - 1, by - 1, fw + 2, self.BAR_H + 2), 6, 6)

            # ── value ─────────────────────────────────────────
            pa.setFont(FM(9, bold=True))
            alpha_val = 230 if val > 0 else 60
            pa.setPen(QColor(r, g, b, alpha_val))
            pa.drawText(QRect(int(self.PAD_L + bar_area + 6), by, self.PAD_R - 6, self.BAR_H),
                        Qt.AlignLeft | Qt.AlignVCenter, f"{val:,}")

            # ── crown for top ─────────────────────────────────
            if is_top and val > 0:
                pa.setFont(F(10)); pa.setPen(QColor(255, 215, 0, int(180 + 60 * pulse)))
                pa.drawText(QRect(int(self.PAD_L + bar_area + 44), by - 2, 20, self.BAR_H + 4),
                            Qt.AlignCenter, "👑")
        pa.end()



# ══════════════════════════════════════════════════════════════
#  GLOBAL SESSION STATE
# ══════════════════════════════════════════════════════════════
class _G:
    """In-memory session state — synced to DB on each action."""
    normal = 0
    flip = 0; flip_streak = 0; flip_side = None; flip_best_h = 0; flip_best_t = 0
    switch = 0; switch_on = False
    swap = 0
    cpm_cps = 0.0
    stop_best = float("inf")
    pop = 0
    focus_best = 0
    chaos_best = 0
    memory_best = 0
    dopa_best = 0
    rcs_best = 0

G = _G()


# ══════════════════════════════════════════════════════════════
#  HELPER
# ══════════════════════════════════════════════════════════════
def cap_lbl(text, color):
    lbl = QLabel(text.upper())
    lbl.setFont(F(8, 500))
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(f"color:{color};background:transparent;letter-spacing:2px;")
    return lbl


# ══════════════════════════════════════════════════════════════
#  BASE PAGE  (shared scaffold for all game pages)
# ══════════════════════════════════════════════════════════════
class BasePage(QWidget):
    """Abstract base class for all 12 game pages (template-method pattern).

    Subclasses must define:
        KEY (str): Game key matching GAME_LIST (used for theming and routing).

    Provides:
        - NeonBackground fill behind all content.
        - PageHeader with back-navigation to MainMenuPage.
        - Scrollable self.root QVBoxLayout for game UI.
        - _ghost_btn(text) helper that returns a styled reset QPushButton.

    Args:
        main_window (MainWindow): Reference to the root window for navigation.

    Examples:
        Subclass example::

            class MyGame(BasePage):
                KEY = "mygame"
                def __init__(self, mw):
                    super().__init__(mw)
                    self.root.addWidget(QLabel("Hello!"))
    """
    KEY = ""

    def __init__(self, main_window, parent=None):
        """Initialise the instance.

        Args:
            main_window (MainWindow): Root window reference.
        """
        super().__init__(parent)
        self.main_window = main_window
        neon, glow, accent, bg_tint = NEON.get(self.KEY, ("#3b82f6","#0f2a5c","#60a5fa","#060c1a"))
        self.neon = neon; self.glow = glow; self.accent = accent

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Animated background (sits behind everything)
        self.bg = NeonBackground(self.KEY, self)
        self.bg.setGeometry(0, 0, 920, 700)
        self.bg.lower()

        # Page header with back nav
        class _Nav:
            def __init__(s, mw): s._mw = mw
            def go(s, _): s._mw.go_to(1)
        self.header = PageHeader(self.KEY, _Nav(main_window), self)
        outer.addWidget(self.header)

        # Scrollable content area
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        self.root = QVBoxLayout(inner)
        self.root.setContentsMargins(24, 20, 24, 24)
        self.root.setSpacing(10)
        self.root.setAlignment(Qt.AlignTop)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

        self._build_content()

    def _build_content(self):
        pass  # override in subclass

    def _ghost_btn(self, text):
        """Execute ghost btn.

        Args:
            text (str): Button label.

        Returns:
            QPushButton: Styled transparent reset button.

        Examples:
            >>> btn = self._ghost_btn('Reset')
        """
        btn = QPushButton(text); btn.setFont(F(11, 500))
        btn.setFixedHeight(34); btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {GHOST}; color: {DIM};
                border: 1px solid {EDGE}; border-radius: 8px; padding: 0 16px;
            }}
            QPushButton:hover {{ background: {EDGE}; color: {TEXT}; }}
        """)
        return btn

    def resizeEvent(self, e):
        self.bg.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(e)


# ══════════════════════════════════════════════════════════════
#  NORMAL CLICK
# ══════════════════════════════════════════════════════════════
class NormalClickPage(BasePage):
    """Game: Normal Click — count raw clicks as fast as possible.

    Inherits BasePage. Tracks click count in global state G.normal.
    """
    KEY = "normal"

    def _build_content(self):
        self._session = 0
        root = self.root

        self.score = GlowLabel("0", self.neon, 68, mono=True)
        root.addWidget(self.score, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("total clicks", self.neon))
        root.addSpacing(32)

        ctr = QWidget(); ctr.setFixedSize(260, 260)
        ctr.setStyleSheet("background:transparent;")
        self.btn = NeonTapButton("TAP", self.neon, self.accent, 230, ctr)
        self.btn.move(15, 15); self.btn.clicked = self._tap
        self.parts = Particles(ctr); self.parts.setGeometry(0, 0, 260, 260)
        self.brackets = CornerBrackets(self.neon, 20, 2, ctr)
        self.brackets.setGeometry(0, 0, 260, 260)
        root.addWidget(ctr, 0, Qt.AlignCenter)
        root.addStretch()

        row = QHBoxLayout(); row.setSpacing(12)
        self.sess_c = StatChip("session", "0", self.neon)
        self.best_c = StatChip("all time", f"{G.normal:,}", self.neon)
        row.addWidget(self.sess_c); row.addWidget(self.best_c)
        root.addLayout(row)

    def _tap(self):
        G.normal += 1; self._session += 1
        db = self.main_window.db; u = self.main_window.current_user
        if u: db.update_score(u, "normal", G.normal)
        self.score.set(f"{G.normal:,}")
        self.sess_c.set(f"{self._session:,}")
        self.best_c.set(f"{G.normal:,}")
        self.parts.burst(130, 130, self.neon, 18)

    def showEvent(self, e):
        u = self.main_window.current_user
        if u:
            ud = self.main_window.db.get_user(u)
            if ud: G.normal = ud.get("normal", 0)
        self.score.set(f"{G.normal:,}"); self.best_c.set(f"{G.normal:,}")
        super().showEvent(e)


# ══════════════════════════════════════════════════════════════
#  FLIP COIN — helper widgets
# ══════════════════════════════════════════════════════════════
class ResultBanner(QWidget):
    def __init__(self, parent=None):
        """Initialise the instance.

        Args:
            parent (QWidget | None): Optional parent widget.
        """
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
        """Execute show result.

        Args:
            score (int): Score to display.
                    neon (str): Hex accent colour.

        Examples:
            >>> banner.show_result(206, '#f59e0b')
        """
        self._text   = text
        self._color  = QColor(color)
        self._frame  = 0
        self._active = True
        self._t.start()

    def _step(self):
        self._frame += 1
        t = self._frame
        if t < 12:
            self._scale = 0.5 + (t / 12) * 0.9; self._alpha = t / 12
        elif t < 38:
            self._scale = 1.0 + math.sin((t - 12) / 26 * math.pi) * 0.06; self._alpha = 1.0
        elif t < 55:
            self._alpha = 1.0 - (t - 38) / 17; self._scale = 1.0
        else:
            self._active = False; self._alpha = 0.0; self._t.stop()
        self.update()

    def paintEvent(self, ev):
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
        if self._alpha <= 0: return
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        nc = self._color; a = int(self._alpha * 255)
        pa.save()
        pa.translate(cx, cy); pa.scale(self._scale, self._scale); pa.translate(-cx, -cy)
        has_streak = "×" in self._text
        font_size  = 22 if has_streak else 42
        pill_w     = 210 if has_streak else 180
        pill_h     = 52  if has_streak else 64
        pill = QPainterPath()
        pill.addRoundedRect(QRectF(cx - pill_w // 2, cy - pill_h // 2, pill_w, pill_h), 18, 18)
        pa.fillPath(pill, QColor(nc.red(), nc.green(), nc.blue(), int(a * 0.22)))
        pa.strokePath(pill, QPen(QColor(nc.red(), nc.green(), nc.blue(), int(a * 0.7)), 2))
        pa.setFont(FM(font_size, True))
        pa.setPen(QColor(0, 0, 0, int(a * 0.5)))
        pa.drawText(QRect(2, 2, w, h), Qt.AlignCenter, self._text)
        pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), a))
        pa.drawText(QRect(0, 0, w, h), Qt.AlignCenter, self._text)
        pa.restore(); pa.end()


class StreakBadge(QWidget):
    def __init__(self, parent=None):
        """Initialise the instance.

        Args:
            parent (QWidget | None): Optional parent widget.
        """
        super().__init__(parent)
        self.setFixedSize(110, 70)
        self._streak = 0; self._pulse = 0.0
        self._neon = QColor(GHOST)
        self._t = QTimer(self); self._t.setInterval(14); self._t.timeout.connect(self._step)
        self._t.start()

    def set_streak(self, n, color):
        self._streak = n; self._neon = QColor(color)
        self._pulse = 1.4 if n > 1 else 0.0; self.update()

    def _step(self):
        if self._pulse > 0:
            self._pulse = max(0.0, self._pulse - 0.06); self.update()

    def paintEvent(self, ev):
        """Render this widget using QPainter.

        Args:
            ev (QPaintEvent): Paint event from Qt.
        """
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
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


# ══════════════════════════════════════════════════════════════
#  FLIP COIN PAGE
# ══════════════════════════════════════════════════════════════
class FlipCoinPage(BasePage):
    """Game: Flip Coin — flip a coin and track heads/tails streaks.

    Inherits BasePage. Uses CoinDisc for animated flip and StreakBadge.
    """
    KEY = "flip"

    def _build_content(self):
        root = self.root

        top = QHBoxLayout(); top.setSpacing(10)
        self.flips_c = StatChip("flips", "0", self.neon)
        self.side_c  = StatChip("last",  "—", self.neon)
        top.addWidget(self.flips_c); top.addWidget(self.side_c)
        root.addLayout(top); root.addSpacing(18)

        coin_wrap = QWidget(); coin_wrap.setFixedSize(220, 220)
        coin_wrap.setStyleSheet("background:transparent;")
        self.coin = CoinDisc(coin_wrap)
        self.coin.result_landed.connect(self._on_landed)
        self.banner = ResultBanner(coin_wrap)
        self.banner.setGeometry(0, 0, 220, 220)
        root.addWidget(coin_wrap, 0, Qt.AlignCenter); root.addSpacing(10)

        self.streak_badge = StreakBadge()
        self.streak_badge.set_streak(0, self.neon)
        root.addWidget(self.streak_badge, 0, Qt.AlignCenter)
        root.addSpacing(14)

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

        bot = QHBoxLayout(); bot.setSpacing(10)
        self.bh = StatChip("best H streak", "0", NEON["flip"][0])
        self.bt = StatChip("best T streak", "0", NEON["swap"][0])
        bot.addWidget(self.bh); bot.addWidget(self.bt)
        root.addLayout(bot)

        self._shake_frames = 0
        self._shake_t = QTimer(self)
        self._shake_t.setInterval(14)
        self._shake_t.timeout.connect(self._do_shake)
        self._last_result = None

    def _flip(self):
        result = random.choice(["H", "T"]); G.flip += 1
        db = self.main_window.db; u = self.main_window.current_user
        if u: db.update_score(u, "flip", G.flip)
        if result == G.flip_side: G.flip_streak += 1
        else: G.flip_streak = 1; G.flip_side = result
        if result == "H": G.flip_best_h = max(G.flip_best_h, G.flip_streak)
        else:             G.flip_best_t = max(G.flip_best_t, G.flip_streak)
        self._last_result = result
        self.coin.flip_to(result)
        self.flips_c.set(G.flip); self.side_c.set(result)
        self.bh.set(G.flip_best_h); self.bt.set(G.flip_best_t)

    def _on_landed(self):
        result = self._last_result
        if result is None: return
        color  = NEON["flip"][0] if result == "H" else NEON["swap"][0]
        label  = "HEADS!" if result == "H" else "TAILS!"
        if G.flip_streak >= 3:
            label = f"{label}  🔥×{G.flip_streak}"
        self.banner.show_result(label, color)
        self.streak_badge.set_streak(G.flip_streak, color)

    def _do_shake(self): pass  # disabled

    def showEvent(self, e):
        u = self.main_window.current_user
        if u:
            ud = self.main_window.db.get_user(u)
            if ud: G.flip = ud.get("flip", 0)
        self.flips_c.set(G.flip)
        super().showEvent(e)




# ══════════════════════════════════════════════════════════════
#  SWITCH
# ══════════════════════════════════════════════════════════════
class SwitchPage(BasePage):
    """Game: Switch — toggle a NeonToggle on and off, count total toggles.

    Inherits BasePage.
    """
    KEY = "switch"

    def _build_content(self):
        self._on_ct = 0; self._off_ct = 0
        root = self.root
        self.score = GlowLabel("0", self.neon, 58, mono=True)
        root.addWidget(self.score, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("toggles", self.neon))
        root.addStretch()

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
        db = self.main_window.db; u = self.main_window.current_user
        if u: db.update_score(u, "switch", G.switch)
        if G.switch_on: self._on_ct += 1; self.on_c.set(self._on_ct)
        else:           self._off_ct += 1; self.off_c.set(self._off_ct)
        self.score.set(f"{G.switch:,}")
        if G.switch_on:
            self.state_lbl.setText("ON")
            self.state_lbl.setStyleSheet(f"color:{self.neon};background:transparent;")
            eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(35)
            eff.setColor(QColor(self.neon)); eff.setOffset(0, 0)
            self.state_lbl.setGraphicsEffect(eff)
        else:
            self.state_lbl.setText("OFF")
            self.state_lbl.setStyleSheet(f"color:{GHOST};background:transparent;")
            self.state_lbl.setGraphicsEffect(None)

    def showEvent(self, e):
        u = self.main_window.current_user
        if u:
            ud = self.main_window.db.get_user(u)
            if ud: G.switch = ud.get("switch", 0)
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
    """Game: Swap Click — the button jumps to a random position on each hit.

    Inherits BasePage. Rewards precision clicking.
    """
    KEY = "swap"

    def _build_content(self):
        root = self.root
        self.score = GlowLabel("0", self.neon, 52, mono=True)
        root.addWidget(self.score, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("hits", self.neon)); root.addSpacing(8)

        self.zone = QWidget(); self.zone.setMinimumHeight(360)
        self.zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.zone.setStyleSheet("background:transparent;")
        self.parts    = Particles(self.zone); self.parts.setGeometry(0, 0, 600, 600)
        self.swap_btn = NeonTapButton("◎", self.neon, self.accent, 74, self.zone)
        self.swap_btn.move(140, 150); self.swap_btn.clicked = self._hit

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
        sz = 16
        pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), 80), 2))
        pa.drawLine(2, sz, 2, 2); pa.drawLine(2, 2, sz, 2)
        pa.drawLine(w - sz, 2, w - 2, 2); pa.drawLine(w - 2, 2, w - 2, sz)
        pa.drawLine(2, h - sz, 2, h - 2); pa.drawLine(2, h - 2, sz, h - 2)
        pa.drawLine(w - sz, h - 2, w - 2, h - 2); pa.drawLine(w - 2, h - sz, w - 2, h - 2)
        pa.end()

    def _hit(self):
        G.swap += 1; self.score.set(f"{G.swap:,}")
        db = self.main_window.db; u = self.main_window.current_user
        if u: db.update_score(u, "swap", G.swap)
        w = max(20, self.zone.width() - 84); h = max(20, self.zone.height() - 84)
        ox = self.swap_btn.x() + 37; oy = self.swap_btn.y() + 37
        self.parts.setGeometry(0, 0, self.zone.width(), self.zone.height())
        self.parts.burst(ox, oy, self.neon, 20)
        self.swap_btn.move(random.randint(8, w), random.randint(8, h))

    def showEvent(self, e):
        u = self.main_window.current_user
        if u:
            ud = self.main_window.db.get_user(u)
            if ud: G.swap = ud.get("swap", 0)
        self.score.set(f"{G.swap:,}"); super().showEvent(e)



# ══════════════════════════════════════════════════════════════
#  CLICK PER TIME
# ══════════════════════════════════════════════════════════════
class ClickPerTimePage(BasePage):
    """Game: Click per Time — measure clicks per second over a chosen duration.

    Inherits BasePage. Uses NeonRing for countdown and calculates CPS.
    """
    KEY = "cpm"

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
        self.cps_c  = StatChip("cps",      "—",                        self.neon)
        self.best_c = StatChip("best cps", f"{G.cpm_cps:.2f}",          self.neon)
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
        if cps > G.cpm_cps:
            G.cpm_cps = cps; self.best_c.set(f"{cps:.2f}")
            db = self.main_window.db; u = self.main_window.current_user
            if u: db.update_score(u, "cpm", self._clicks)

    def _reset(self):
        self._ticker.stop(); self._running = self._finished = False
        self._clicks = 0; self.clicks_lbl.set("0"); self.cps_c.set("—")
        self.tap_btn.setEnabled(True); self.t_input.setEnabled(True); self._sync_ring()

    def showEvent(self, e):
        if not self._running and not self._finished: self._sync_ring()
        self.best_c.set(f"{G.cpm_cps:.2f}"); super().showEvent(e)


# ══════════════════════════════════════════════════════════════
#  STOPWATCH
# ══════════════════════════════════════════════════════════════
class StopwatchPage(BasePage):
    """Game: Stopwatch — stop the timer as close to the target time as possible.

    Inherits BasePage. Scores accuracy in milliseconds.
    """
    KEY = "stop"

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
        self.ss_btn.setCursor(Qt.PointingHandCursor)
        self.ss_btn.clicked.connect(self._toggle)
        self._style_ss(False); root.addWidget(self.ss_btn, 0, Qt.AlignCenter); root.addSpacing(28)

        self.excess_lbl = GlowLabel("—", DIM, 42, mono=True)
        root.addWidget(self.excess_lbl, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("excess time", DIM)); root.addStretch()

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
        eff.setColor(QColor(self.neon)); eff.setOffset(0, 3)
        self.ss_btn.setGraphicsEffect(eff)

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
            neon_stop = NEON["stop"][0]; neon_cpm = NEON["cpm"][0]
            neon_flip = NEON["flip"][0]; neon_swap = NEON["swap"][0]
            if   ae <= 0.15: color = neon_stop
            elif ae <= 0.60: color = neon_cpm
            elif ae <= 1.50: color = neon_flip
            else:            color = neon_swap
            self.excess_lbl.setText(f"{sign}{ae:.2f}s")
            self.excess_lbl.setStyleSheet(f"color:{color};background:transparent;")
            eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(28)
            eff.setColor(QColor(color)); eff.setOffset(0, 0)
            self.excess_lbl.setGraphicsEffect(eff)
            if ae < abs(G.stop_best): G.stop_best = excess
            be = G.stop_best; bs = "+" if be >= 0 else "-"
            self.best_c.set(f"{bs}{abs(be):.2f}s"); self.tgt_c.set(f"{target:.1f} s")
            db = self.main_window.db; u = self.main_window.current_user
            if u: db.update_score(u, "stop", getattr(G, "stop_count", 0) + 1)

    def _tick(self):
        self.live_lbl.set(f"{self._elapsed.elapsed() / 1000.0:.2f}")

    def _reset(self):
        self._ticker.stop(); self._running = False; self._style_ss(False)
        self.live_lbl.set("0.00"); self.excess_lbl.setText("—")
        self.excess_lbl.setStyleSheet(f"color:{DIM};background:transparent;")
        self.excess_lbl.setGraphicsEffect(None); self.t_input.setEnabled(True)

    def showEvent(self, e):
        if G.stop_best < float("inf"):
            be = G.stop_best; bs = "+" if be >= 0 else "-"
            self.best_c.set(f"{bs}{abs(be):.2f}s")
        super().showEvent(e)



# ══════════════════════════════════════════════════════════════
#  POP IT
# ══════════════════════════════════════════════════════════════
class BubbleWidget(QWidget):
    def __init__(self, row, col, neon, accent, parent=None):
        super().__init__(parent)
        self.row = row; self.col = col
        self.neon = neon; self.accent = accent
        self.setFixedSize(58, 58)
        self.setCursor(Qt.PointingHandCursor)
        self._popped  = False; self._pop_anim = 0.0; self._hover = False
        self._t = QTimer(self); self._t.setInterval(16); self._t.timeout.connect(self._tick)
        self.on_popped = None

    def reset(self):
        self._popped = False; self._pop_anim = 0.0; self._t.stop(); self.update()

    def _tick(self):
        self._pop_anim = min(1.0, self._pop_anim + 0.10); self.update()
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
        nc = QColor(self.neon)

        if self._popped:
            t = self._pop_anim
            radius = int(20 - 6 * t); depth = int(4 * t)
            pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), int(160 - 100*t)), 2))
            pa.setBrush(QColor(10, 12, 20, 180))
            pa.drawEllipse(cx - 22, cy - 22, 44, 44)
            inner = QPainterPath()
            inner.addEllipse(QPointF(cx, cy + depth), float(radius), float(radius))
            pa.fillPath(inner, QColor(6, 8, 14, 220))
            pa.strokePath(inner, QPen(QColor(nc.red(), nc.green(), nc.blue(), int(80 - 50*t)), 1))
            pa.setPen(Qt.NoPen)
            pa.setBrush(QColor(nc.red(), nc.green(), nc.blue(), int(60 - 40*t)))
            pa.drawEllipse(QPointF(cx, cy + depth + 1), 4.0, 4.0)
        else:
            hover_boost = 8 if self._hover else 0
            outer_r = 24 + hover_boost // 3
            if self._hover:
                glow = QRadialGradient(cx, cy, outer_r + 12)
                glow.setColorAt(0.6, QColor(nc.red(), nc.green(), nc.blue(), 0))
                glow.setColorAt(0.85, QColor(nc.red(), nc.green(), nc.blue(), 55))
                glow.setColorAt(1.0,  QColor(nc.red(), nc.green(), nc.blue(), 0))
                pa.setBrush(QBrush(glow)); pa.setPen(Qt.NoPen)
                pa.drawEllipse(cx - outer_r - 12, cy - outer_r - 12, (outer_r+12)*2, (outer_r+12)*2)
            bubble = QPainterPath()
            bubble.addEllipse(QPointF(cx, cy), float(outer_r), float(outer_r))
            tint_bg = QColor(nc.red()//6, nc.green()//6, nc.blue()//6, 200)
            pa.fillPath(bubble, tint_bg)
            fill_grd = QRadialGradient(cx, cy + outer_r * 0.3, outer_r * 1.1)
            fill_grd.setColorAt(0.0, QColor(nc.red(), nc.green(), nc.blue(), 70))
            fill_grd.setColorAt(0.6, QColor(nc.red(), nc.green(), nc.blue(), 45))
            fill_grd.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 20))
            pa.fillPath(bubble, QBrush(fill_grd))
            border_a = 200 if self._hover else 140
            pa.strokePath(bubble, QPen(QColor(nc.red(), nc.green(), nc.blue(), border_a),
                                       2.0 if self._hover else 1.5))
            shine = QRadialGradient(cx - outer_r * 0.28, cy - outer_r * 0.32, outer_r * 0.45)
            shine.setColorAt(0.0, QColor(255, 255, 255, 90 if not self._hover else 120))
            shine.setColorAt(1.0, QColor(255, 255, 255, 0))
            pa.fillPath(bubble, QBrush(shine))
            rim = QRadialGradient(cx, cy + outer_r * 0.5, outer_r * 0.7)
            rim.setColorAt(0.0, QColor(0, 0, 0, 0)); rim.setColorAt(1.0, QColor(0, 0, 0, 60))
            pa.fillPath(bubble, QBrush(rim))
        pa.end()


class PopItPage(BasePage):
    """Game: Pop It — pop all bubbles in a 4x5 grid as fast as possible.

    Inherits BasePage. Uses BubbleWidget for individual dome animations.
    """
    KEY = "pop"
    ROWS = 4; COLS = 5

    def _build_content(self):
        self._total_popped = 0; self._round_popped = 0
        self._round = 1; self._total_bubbles = self.ROWS * self.COLS
        self._best_time = None
        root = self.root

        top = QHBoxLayout(); top.setSpacing(10)
        self.score_c = StatChip("total pops", "0",  self.neon)
        self.round_c = StatChip("round",      "1",  self.neon)
        self.best_c  = StatChip("best time",  "—",  self.neon)
        top.addWidget(self.score_c); top.addWidget(self.round_c); top.addWidget(self.best_c)
        root.addLayout(top); root.addSpacing(14)

        self.timer_lbl = GlowLabel("0.00", self.neon, 30, mono=True)
        root.addWidget(self.timer_lbl, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("seconds this round", self.neon)); root.addSpacing(10)

        grid_w = QWidget(); grid_w.setStyleSheet("background:transparent;")
        grid_w.setAttribute(Qt.WA_TranslucentBackground)
        grid_layout = QVBoxLayout(grid_w)
        grid_layout.setContentsMargins(0, 0, 0, 0); grid_layout.setSpacing(8)

        self._bubbles = []
        for r in range(self.ROWS):
            row_layout = QHBoxLayout(); row_layout.setSpacing(8); row_layout.addStretch()
            row_widgets = []
            for c in range(self.COLS):
                use_neon   = self.neon   if (r + c) % 2 == 0 else self.accent
                use_accent = self.accent if (r + c) % 2 == 0 else self.neon
                b = BubbleWidget(r, c, use_neon, use_accent, grid_w)
                b.on_popped = self._bubble_popped
                row_layout.addWidget(b); row_widgets.append(b)
            row_layout.addStretch(); self._bubbles.append(row_widgets)
            grid_layout.addLayout(row_layout)

        root.addWidget(grid_w, 0, Qt.AlignCenter); root.addStretch()
        rst = self._ghost_btn("◀  NEW ROUND"); rst.clicked.connect(self._new_round)
        root.addWidget(rst, 0, Qt.AlignCenter)

        self._timer_elapsed = QElapsedTimer()
        self._ticker = QTimer(self); self._ticker.setInterval(30)
        self._ticker.timeout.connect(self._tick_timer)

    def _bubble_popped(self):
        self._total_popped += 1; self._round_popped += 1
        G.pop += 1; self.score_c.set(str(G.pop))
        db = self.main_window.db; u = self.main_window.current_user
        if u: db.update_score(u, "pop", G.pop)
        if self._round_popped == 1:
            self._timer_elapsed.start(); self._ticker.start()
        if self._round_popped >= self._total_bubbles:
            elapsed = self._timer_elapsed.elapsed() / 1000.0
            self._ticker.stop(); self.timer_lbl.set(f"{elapsed:.2f}")
            if self._best_time is None or elapsed < self._best_time:
                self._best_time = elapsed; self.best_c.set(f"{elapsed:.2f}s")
            QTimer.singleShot(700, self._new_round)

    def _tick_timer(self):
        self.timer_lbl.set(f"{self._timer_elapsed.elapsed() / 1000.0:.2f}")

    def _new_round(self):
        self._ticker.stop(); self._round += 1; self._round_popped = 0
        self.round_c.set(str(self._round)); self.timer_lbl.set("0.00")
        for row in self._bubbles:
            for b in row: b.reset()

    def showEvent(self, e):
        u = self.main_window.current_user
        if u:
            ud = self.main_window.db.get_user(u)
            if ud: G.pop = ud.get("pop", 0)
        self.score_c.set(str(G.pop)); super().showEvent(e)


# ══════════════════════════════════════════════════════════════
#  FOCUS BURST — helpers
# ══════════════════════════════════════════════════════════════
class _FocusShape:
    SHAPES = ["circle", "square", "triangle", "diamond", "star"]

    def __init__(self, zone_w, zone_h):
        self.zone_w = zone_w; self.zone_h = zone_h
        self.shape = random.choice(self.SHAPES)
        color_keys = list(NEON.keys()); self.color_key = random.choice(color_keys)
        self.color = NEON[self.color_key][0]
        self.size = random.randint(22, 36)
        self.x = random.uniform(self.size, zone_w - self.size)
        self.y = random.uniform(self.size, zone_h - self.size)
        speed = random.uniform(0.6, 1.4); angle = random.uniform(0, math.pi * 2)
        self.vx = math.cos(angle) * speed; self.vy = math.sin(angle) * speed

    def step(self, speed_mult=1.0):
        self.x += self.vx * speed_mult; self.y += self.vy * speed_mult
        if self.x - self.size < 0:            self.x = self.size;            self.vx = abs(self.vx)
        if self.x + self.size > self.zone_w:  self.x = self.zone_w - self.size; self.vx = -abs(self.vx)
        if self.y - self.size < 0:            self.y = self.size;            self.vy = abs(self.vy)
        if self.y + self.size > self.zone_h:  self.y = self.zone_h - self.size; self.vy = -abs(self.vy)

    def draw(self, pa, highlight=False, flash_wrong=False):
        nc = QColor("#ef4444" if flash_wrong else self.color)
        sz = self.size; cx = int(self.x); cy = int(self.y)
        grd = QRadialGradient(cx, cy, sz + 10)
        grd.setColorAt(0.4, QColor(nc.red(), nc.green(), nc.blue(), 130 if highlight else 60))
        grd.setColorAt(1.0, QColor(nc.red(), nc.green(), nc.blue(), 0))
        pa.setBrush(QBrush(grd)); pa.setPen(Qt.NoPen)
        pa.drawEllipse(cx - sz - 10, cy - sz - 10, (sz+10)*2, (sz+10)*2)
        pa.setBrush(QColor(nc.red(), nc.green(), nc.blue(), 160 if highlight else 100))
        pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), 255 if highlight else 180),
                       2.5 if highlight else 1.5))
        if self.shape == "circle":
            pa.drawEllipse(QPointF(cx, cy), float(sz), float(sz))
        elif self.shape == "square":
            pa.drawRoundedRect(QRectF(cx - sz, cy - sz, sz * 2, sz * 2), 5, 5)
        elif self.shape == "triangle":
            pa.drawPolygon(QPolygonF([QPointF(cx, cy-sz), QPointF(cx+sz, cy+sz), QPointF(cx-sz, cy+sz)]))
        elif self.shape == "diamond":
            pa.drawPolygon(QPolygonF([QPointF(cx, cy-sz), QPointF(cx+sz, cy), QPointF(cx, cy+sz), QPointF(cx-sz, cy)]))
        elif self.shape == "star":
            pts = [QPointF(cx + (sz if i%2==0 else sz*0.42) * math.cos(math.radians(i*36-90)),
                           cy + (sz if i%2==0 else sz*0.42) * math.sin(math.radians(i*36-90)))
                   for i in range(10)]
            pa.drawPolygon(QPolygonF(pts))
        if highlight:
            sheen = QRadialGradient(cx - sz*0.3, cy - sz*0.3, sz*0.5)
            sheen.setColorAt(0, QColor(255, 255, 255, 80)); sheen.setColorAt(1, QColor(255, 255, 255, 0))
            pa.setBrush(QBrush(sheen)); pa.setPen(Qt.NoPen)
            pa.drawEllipse(QPointF(cx, cy), float(sz), float(sz))


class _TargetHintWidget(QWidget):
    def __init__(self, neon, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._shape = "circle"; self._color = neon
        self._phase = 0.0
        self._t = QTimer(self); self._t.setInterval(30); self._t.timeout.connect(self._step); self._t.start()

    def set_target(self, shape, color): self._shape = shape; self._color = color; self.update()

    def _step(self): self._phase = (self._phase + 0.06) % (math.pi * 2); self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); cx = w // 2; cy = h // 2
        nc = QColor(self._color); sz = min(w, h) // 2 - 6
        pulse = 0.5 + 0.5 * math.sin(self._phase)
        pa.setBrush(QColor(nc.red(), nc.green(), nc.blue(), int(25 + 20*pulse)))
        pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), int(100 + 80*pulse)), 1.5))
        pa.drawEllipse(QPointF(cx, cy), float(sz + 5), float(sz + 5))
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
    def reset_speed(self): self._speed_mult = max(1.0, self._speed_mult - 0.15)
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
        for i in range(len(self._shapes) - 1, -1, -1):
            s = self._shapes[i]
            if math.hypot(px - s.x, py - s.y) <= s.size + 4:
                t_shape, t_ckey, _ = self._target
                if s.shape == t_shape and s.color_key == t_ckey:
                    self.on_correct(s)
                else:
                    self._wrong_id = i; self._wrong_timer = 18; self.on_wrong()
                return

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); nc = QColor(self.neon)
        bg = QPainterPath(); bg.addRoundedRect(QRectF(1, 1, w-2, h-2), 16, 16)
        pa.fillPath(bg, QColor(10, 11, 18, 140))
        pa.strokePath(bg, QPen(QColor(nc.red(), nc.green(), nc.blue(), 40), 1))
        sz = 14; pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), 70), 2))
        pa.drawLine(2, sz, 2, 2); pa.drawLine(2, 2, sz, 2)
        pa.drawLine(w-sz, 2, w-2, 2); pa.drawLine(w-2, 2, w-2, sz)
        pa.drawLine(2, h-sz, 2, h-2); pa.drawLine(2, h-2, sz, h-2)
        pa.drawLine(w-sz, h-2, w-2, h-2); pa.drawLine(w-2, h-sz, w-2, h-2)
        if not self._running:
            pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), 100)); pa.setFont(F(14, 500))
            pa.drawText(QRect(0, 0, w, h), Qt.AlignCenter, "Press START to begin")
            pa.end(); return
        for i, s in enumerate(self._shapes):
            t_shape, t_ckey, _ = self._target
            s.draw(pa, highlight=(s.shape == t_shape and s.color_key == t_ckey),
                   flash_wrong=(i == self._wrong_id))
        pa.end()


class FocusBurstPage(BasePage):
    """Game: Focus Burst — click the correct target among decoys for 30 seconds.

    Inherits BasePage. Speed increases on consecutive correct clicks.
    """
    KEY = "focus"
    DURATION = 30

    def _build_content(self):
        self._combo = 0; self._correct = 0; self._running = False
        self._elapsed = QElapsedTimer()
        self._ticker = QTimer(self); self._ticker.setInterval(80)
        self._ticker.timeout.connect(self._tick_round)
        self._next_change = 8
        root = self.root

        hint_row = QHBoxLayout(); hint_row.addStretch()
        hl = QLabel("TARGET →"); hl.setFont(F(10, 500))
        hl.setStyleSheet(f"color:{DIM};background:transparent;letter-spacing:2px;")
        hint_row.addWidget(hl); hint_row.addSpacing(8)
        self.target_hint = _TargetHintWidget(self.neon); self.target_hint.setFixedSize(52, 52)
        hint_row.addWidget(self.target_hint); hint_row.addStretch()
        root.addLayout(hint_row); root.addSpacing(6)

        self.time_bar = _TimeBar(self.neon); self.time_bar.setFixedHeight(8)
        root.addWidget(self.time_bar); root.addSpacing(10)

        self.zone = FocusZone(self.neon, self._on_correct, self._on_wrong)
        self.zone.setMinimumHeight(280)
        self.zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.zone, 1); root.addSpacing(10)

        stats = QHBoxLayout(); stats.setSpacing(10)
        self.combo_c   = StatChip("combo",     "0",                self.neon)
        self.correct_c = StatChip("hits",      "0",                self.neon)
        self.best_c    = StatChip("best combo", str(G.focus_best), self.neon)
        stats.addWidget(self.combo_c); stats.addWidget(self.correct_c); stats.addWidget(self.best_c)
        root.addLayout(stats); root.addSpacing(10)

        self.ss_btn = QPushButton("▶  START"); self.ss_btn.setFont(F(15, 700))
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
        eff.setColor(QColor(self.neon)); eff.setOffset(0, 3); self.ss_btn.setGraphicsEffect(eff)

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
            db = self.main_window.db; u = self.main_window.current_user
            if u: db.update_score(u, "focus", G.focus_best)
        self.zone.boost_speed()
        if self._correct % self._next_change == 0:
            self.zone.change_target(); self._update_hint()
            self._next_change = max(4, self._next_change - 1)

    def _on_wrong(self):
        self._combo = 0; self.combo_c.set("0"); self.zone.reset_speed()

    def _tick_round(self):
        remaining = max(0.0, self.DURATION - self._elapsed.elapsed() / 1000.0)
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
    GOAL = 15
    DURATION = 30

    _FAKE_LABELS = [
        "CLICK", "PRESS", "GO!", "TAP", "HIT", "OK", "YES",
        "★", "◆", "▶", "NOW", "→", "DO IT", "FREE",
        "WIN", "BONUS", "×2", "⚡", "◉", "▣",
    ]

    def __init__(self, neon, on_correct, on_wrong, parent=None):
        super().__init__(parent)
        self.neon = neon; self.on_correct = on_correct; self.on_wrong = on_wrong
        self._running = False; self._hits = 0; self._target_id = -1
        self._buttons: list = []; self._wobble = 0.0
        self._flash_wrong_id = -1; self._flash_timer = 0
        self._move_timer = QTimer(self); self._move_timer.setInterval(50)
        self._move_timer.timeout.connect(self._step)

    def start(self):
        self._running = True; self._hits = 0
        self._spawn_buttons(); self._move_timer.start()

    def stop(self):
        self._running = False; self._move_timer.stop()
        self._buttons.clear(); self._target_id = -1; self.update()

    def get_hits(self): return self._hits

    def _spawn_buttons(self):
        self._buttons.clear()
        w, h = max(self.width(), 300), max(self.height(), 300)
        placed = []

        def overlaps(x, y, bw, bh):
            return any(abs(x - p[0]) < bw + 8 and abs(y - p[1]) < bh + 8 for p in placed)

        tw, th = 88, 38
        for _ in range(200):
            tx = random.randint(4, w - tw - 4); ty = random.randint(4, h - th - 4)
            if not overlaps(tx, ty, tw, th): break
        placed.append((tx, ty, tw, th))
        self._target_id = 0
        self._buttons.append({
            "x": float(tx), "y": float(ty), "w": tw, "h": th,
            "label": "CLICK ME", "is_target": True,
            "wobble_phase": random.uniform(0, math.pi * 2),
            "vx": random.choice([-1,1]) * random.uniform(0.6, 1.4),
            "vy": random.choice([-1,1]) * random.uniform(0.6, 1.4),
        })
        for i in range(1, 18):
            bw = random.randint(48, 90); bh = random.randint(26, 40)
            for _ in range(200):
                bx = random.randint(4, w - bw - 4); by_ = random.randint(4, h - bh - 4)
                if not overlaps(bx, by_, bw, bh): break
            placed.append((bx, by_, bw, bh))
            self._buttons.append({
                "x": float(bx), "y": float(by_), "w": bw, "h": bh,
                "label": random.choice(self._FAKE_LABELS), "is_target": False,
                "wobble_phase": random.uniform(0, math.pi * 2),
                "vx": random.choice([-1,1]) * random.uniform(0.3, 1.8),
                "vy": random.choice([-1,1]) * random.uniform(0.3, 1.8),
            })

    def _step(self):
        if not self._running: return
        self._wobble += 0.07
        w, h = self.width(), self.height()
        for b in self._buttons:
            b["wobble_phase"] += 0.04; b["x"] += b["vx"]; b["y"] += b["vy"]
            if b["x"] < 0:            b["x"] = 0;            b["vx"] =  abs(b["vx"])
            if b["x"] + b["w"] > w:   b["x"] = w - b["w"];   b["vx"] = -abs(b["vx"])
            if b["y"] < 0:            b["y"] = 0;            b["vy"] =  abs(b["vy"])
            if b["y"] + b["h"] > h:   b["y"] = h - b["h"];   b["vy"] = -abs(b["vy"])
        if self._flash_timer > 0:
            self._flash_timer -= 1
            if self._flash_timer == 0: self._flash_wrong_id = -1
        self.update()

    def _relocate_target(self):
        w, h = max(self.width(), 300), max(self.height(), 300)
        b = self._buttons[self._target_id]
        for _ in range(100):
            nx = random.randint(4, w - b["w"] - 4); ny = random.randint(4, h - b["h"] - 4)
            ok = all(ob is b or abs(nx - ob["x"]) >= b["w"] + 6 or abs(ny - ob["y"]) >= b["h"] + 6
                     for ob in self._buttons)
            if ok: break
        b["x"], b["y"] = float(nx), float(ny)
        b["vx"] = random.choice([-1,1]) * random.uniform(0.8, 1.8)
        b["vy"] = random.choice([-1,1]) * random.uniform(0.8, 1.8)
        for ob in self._buttons:
            if not ob["is_target"]: ob["label"] = random.choice(self._FAKE_LABELS)

    def mousePressEvent(self, ev):
        if not self._running or ev.button() != Qt.LeftButton: return
        try:    px, py = ev.position().x(), ev.position().y()
        except: px, py = float(ev.x()), float(ev.y())
        for i in range(len(self._buttons) - 1, -1, -1):
            b = self._buttons[i]
            if b["x"] <= px <= b["x"] + b["w"] and b["y"] <= py <= b["y"] + b["h"]:
                if b["is_target"]:
                    self._hits += 1; self._relocate_target(); self.on_correct(self._hits)
                else:
                    self._flash_wrong_id = i; self._flash_timer = 14; self.on_wrong()
                return

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); nc = QColor(self.neon)
        bg = QPainterPath(); bg.addRoundedRect(QRectF(1, 1, w-2, h-2), 16, 16)
        pa.fillPath(bg, QColor(10, 11, 18, 140))
        pa.strokePath(bg, QPen(QColor(nc.red(), nc.green(), nc.blue(), 40), 1))
        if not self._running:
            pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), 100)); pa.setFont(F(14, 500))
            pa.drawText(QRect(0, 0, w, h), Qt.AlignCenter, "Press START to begin")
            pa.end(); return
        for i, b in enumerate(self._buttons):
            bx, by_ = int(b["x"]), int(b["y"]); bw, bh = b["w"], b["h"]
            is_tgt = b["is_target"]
            wobble = math.sin(b["wobble_phase"]) * 2.5
            draw_x = bx + (0 if is_tgt else int(wobble)); draw_y = by_
            rect = QRectF(draw_x, draw_y, bw, bh)
            path = QPainterPath(); path.addRoundedRect(rect, 8, 8)
            if is_tgt:
                pulse = 0.6 + 0.4 * math.sin(self._wobble * 1.8)
                pa.fillPath(path, QColor(nc.red(), nc.green(), nc.blue(), int(180 + 60*pulse)))
                pa.strokePath(path, QPen(QColor(nc.red(), nc.green(), nc.blue(), int(120*pulse)), 3))
                pa.setPen(QColor(255, 255, 255, 255)); pa.setFont(F(10, 700))
                pa.drawText(QRect(draw_x, draw_y, bw, bh), Qt.AlignCenter, b["label"])
            else:
                flash = (i == self._flash_wrong_id)
                if flash:
                    pa.fillPath(path, QColor(220, 30, 30, 200))
                    pa.strokePath(path, QPen(QColor(255, 80, 80, 200), 2))
                else:
                    shade = (i * 37) % 60
                    pa.fillPath(path, QColor(30+shade, 32+shade, 48+shade, 160))
                    pa.strokePath(path, QPen(QColor(80, 90, 120, 100), 1))
                txt_col = QColor(220, 80, 80, 200) if flash else QColor(180, 185, 210, 180)
                pa.setPen(txt_col); pa.setFont(F(9, 500))
                pa.drawText(QRect(draw_x, draw_y, bw, bh), Qt.AlignCenter, b["label"])
        pa.end()


class ChaosControlPage(BasePage):
    """Game: Chaos Control — find and click the one real button among 18 moving fakes.

    Inherits BasePage. Buttons wobble and flash to increase difficulty.
    """
    KEY = "chaos"
    GOAL = 15; DURATION = 30

    def _build_content(self):
        self._hits = 0; self._misses = 0; self._running = False
        self._elapsed = QElapsedTimer()
        self._ticker = QTimer(self); self._ticker.setInterval(80)
        self._ticker.timeout.connect(self._tick)
        root = self.root

        self.time_bar = _TimeBar(self.neon); self.time_bar.setFixedHeight(8)
        root.addWidget(self.time_bar); root.addSpacing(8)

        self.goal_lbl = QLabel(f"HIT THE REAL BUTTON  0 / {self.GOAL}")
        self.goal_lbl.setFont(F(10, 600)); self.goal_lbl.setAlignment(Qt.AlignCenter)
        self.goal_lbl.setStyleSheet(f"color:{self.neon};background:transparent;letter-spacing:2px;")
        root.addWidget(self.goal_lbl); root.addSpacing(6)

        self.zone = ChaosZone(self.neon, self._on_correct, self._on_wrong)
        self.zone.setMinimumHeight(300)
        self.zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.zone, 1); root.addSpacing(10)

        stats = QHBoxLayout(); stats.setSpacing(10)
        self.hits_c = StatChip("hits",      "0",                self.neon)
        self.miss_c = StatChip("misses",    "0",                self.neon)
        self.best_c = StatChip("best hits", str(G.chaos_best),  self.neon)
        stats.addWidget(self.hits_c); stats.addWidget(self.miss_c); stats.addWidget(self.best_c)
        root.addLayout(stats); root.addSpacing(10)

        self.ss_btn = QPushButton("▶  START"); self.ss_btn.setFont(F(15, 700))
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
        eff.setColor(QColor(self.neon)); eff.setOffset(0, 3); self.ss_btn.setGraphicsEffect(eff)

    def _toggle(self):
        if not self._running:
            self._running = True; self._hits = 0; self._misses = 0
            self.hits_c.set("0"); self.miss_c.set("0")
            self.goal_lbl.setText(f"HIT THE REAL BUTTON  0 / {self.GOAL}")
            self._elapsed.start(); self.time_bar.set(1.0)
            self._style_btn(True); self.zone.start(); self._ticker.start()
        else:
            self._end_round()

    def _on_correct(self, total_hits):
        self._hits = total_hits; self.hits_c.set(str(self._hits))
        self.goal_lbl.setText(f"HIT THE REAL BUTTON  {self._hits} / {self.GOAL}")
        if self._hits >= self.GOAL: self._end_round()

    def _on_wrong(self):
        self._misses += 1; self.miss_c.set(str(self._misses))

    def _tick(self):
        remaining = max(0.0, self.DURATION - self._elapsed.elapsed() / 1000.0)
        self.time_bar.set(remaining / self.DURATION)
        if remaining <= 0: self._end_round()

    def _end_round(self):
        self._ticker.stop(); self._running = False; self.zone.stop()
        self._style_btn(False); self.time_bar.set(0.0)
        if self._hits > G.chaos_best:
            G.chaos_best = self._hits; self.best_c.set(str(G.chaos_best))
            db = self.main_window.db; u = self.main_window.current_user
            if u: db.update_score(u, "chaos", G.chaos_best)

    def showEvent(self, e): self.best_c.set(str(G.chaos_best)); super().showEvent(e)


# ══════════════════════════════════════════════════════════════
#  MEMORY FLASH
# ══════════════════════════════════════════════════════════════
class MemoryGrid(QWidget):
    COLS = 4

    def __init__(self, neon, accent, on_input, parent=None):
        super().__init__(parent)
        self.neon = neon; self.accent = accent; self.on_input = on_input
        self._n_tiles = 8; self._pattern: list = []; self._revealed: list = []
        self._lit_show = -1; self._wrong_id = -1; self._wrong_timer = 0
        self._result_flash = 0; self._result_win = False
        self._phase = "idle"; self._pulse = 0.0
        self._anim_t = QTimer(self); self._anim_t.setInterval(16)
        self._anim_t.timeout.connect(self._anim_step); self._anim_t.start()

    def _rows(self): return math.ceil(self._n_tiles / self.COLS)

    def _tile_rect(self, idx):
        cols = self.COLS; rows = self._rows()
        w, h = self.width(), self.height()
        pad = 10; gap = 8
        tw = (w - pad*2 - gap*(cols-1)) / cols
        th = (h - pad*2 - gap*(rows-1)) / rows
        c = idx % cols; r = idx // cols
        return QRectF(pad + c*(tw+gap), pad + r*(th+gap), tw, th)

    def setup(self, n_tiles, pattern):
        self._n_tiles = n_tiles; self._pattern = list(pattern); self._revealed.clear()
        self._lit_show = -1; self._wrong_id = -1; self._wrong_timer = 0
        self._result_flash = 0; self._phase = "idle"; self.update()

    def play_show(self, lit_index):
        self._lit_show = lit_index; self._phase = "show"; self.update()

    def hide_show(self):
        self._lit_show = -1; self.update()

    def set_phase(self, phase):
        self._phase = phase
        if phase == "idle": self._lit_show = -1; self._revealed.clear()
        self.update()

    def flash_result(self, win):
        self._result_win = win; self._result_flash = 28; self._phase = "result"; self.update()

    def mousePressEvent(self, ev):
        if self._phase != "input" or ev.button() != Qt.LeftButton: return
        try:    px, py = ev.position().x(), ev.position().y()
        except: px, py = float(ev.x()), float(ev.y())
        for i in range(self._n_tiles):
            if self._tile_rect(i).contains(px, py):
                if i in self._revealed: return
                expected = self._pattern[len(self._revealed)]
                correct  = (i == expected)
                if correct: self._revealed.append(i)
                else: self._wrong_id = i; self._wrong_timer = 18
                self.on_input(i, correct); self.update(); return

    def _anim_step(self):
        self._pulse = (self._pulse + 0.04) % (math.pi * 2)
        if self._wrong_timer > 0:
            self._wrong_timer -= 1
            if self._wrong_timer == 0: self._wrong_id = -1
        if self._result_flash > 0: self._result_flash -= 1
        self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        nc = QColor(self.neon); pulse = 0.5 + 0.5 * math.sin(self._pulse)

        if self._phase == "result" and self._result_flash > 0:
            alpha = int(self._result_flash / 28 * 180)
            col = QColor(60, 220, 100, alpha) if self._result_win else QColor(220, 50, 50, alpha)
            pa.fillRect(0, 0, self.width(), self.height(), col)

        for i in range(self._n_tiles):
            rect = self._tile_rect(i)
            path = QPainterPath(); path.addRoundedRect(rect, 10, 10)
            is_lit   = (i == self._lit_show)
            is_done  = (i in self._revealed)
            is_wrong = (i == self._wrong_id)
            is_next  = (self._phase == "input" and
                        len(self._revealed) < len(self._pattern) and
                        i == self._pattern[len(self._revealed)])
            if is_lit:
                glow_a = int(200 + 55 * pulse)
                pa.fillPath(path, QColor(nc.red(), nc.green(), nc.blue(), glow_a))
                pa.strokePath(path, QPen(QColor(255, 255, 255, 200), 2))
                inner = QPainterPath(); inner.addRoundedRect(rect.adjusted(6,6,-6,-6), 6, 6)
                pa.fillPath(inner, QColor(255, 255, 255, 90))
            elif is_done:
                pa.fillPath(path, QColor(nc.red(), nc.green(), nc.blue(), 200))
                pa.strokePath(path, QPen(QColor(255, 255, 255, 120), 1.5))
            elif is_wrong:
                pa.fillPath(path, QColor(220, 50, 50, 220))
                pa.strokePath(path, QPen(QColor(255, 80, 80, 200), 2))
            else:
                shade = 22 + (i % 3) * 5
                pa.fillPath(path, QColor(shade, shade+2, shade+12, 210))
                border_a = int(50 + 30*pulse) if (self._phase == "input" and is_next) else 45
                pa.strokePath(path, QPen(QColor(nc.red(), nc.green(), nc.blue(), border_a), 1))
            if self._phase in ("idle", "show"):
                pa.setPen(QColor(255, 255, 255, 25 if not is_lit else 0))
                pa.setFont(F(9, 400))
                pa.drawText(rect.toRect(), Qt.AlignCenter, str(i + 1))
        pa.end()


class MemoryFlashPage(BasePage):
    """Game: Memory Flash — repeat a pattern of tiles from memory.

    Inherits BasePage. Pattern length increases each round.
    """
    KEY = "memory"
    _BASE_FLASH_MS = 600; _BASE_GAP_MS = 200
    _MIN_FLASH_MS  = 180; _MIN_GAP_MS  = 80

    def _build_content(self):
        self._round = 0; self._score = 0; self._running = False
        self._phase = "idle"; self._pattern: list = []
        self._show_idx = 0; self._input_ok = 0
        self._show_timer = QTimer(self); self._show_timer.setSingleShot(True)
        self._show_timer.timeout.connect(self._show_next_step)
        self._feedback_timer = QTimer(self); self._feedback_timer.setSingleShot(True)
        self._feedback_timer.timeout.connect(self._next_round)
        root = self.root

        self.status_lbl = QLabel("Press START")
        self.status_lbl.setFont(F(13, 600)); self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet(f"color:{self.neon};background:transparent;letter-spacing:1px;")
        root.addWidget(self.status_lbl); root.addSpacing(6)

        bar_row = QHBoxLayout(); bar_row.setSpacing(8)
        self.round_lbl = QLabel("ROUND 0"); self.round_lbl.setFont(F(9, 500))
        self.round_lbl.setStyleSheet(f"color:{DIM};background:transparent;letter-spacing:2px;")
        bar_row.addWidget(self.round_lbl); bar_row.addStretch()
        self.speed_lbl = QLabel("SPEED ×1.0"); self.speed_lbl.setFont(F(9, 500))
        self.speed_lbl.setStyleSheet(f"color:{DIM};background:transparent;letter-spacing:2px;")
        bar_row.addWidget(self.speed_lbl); root.addLayout(bar_row); root.addSpacing(4)

        self.grid = MemoryGrid(self.neon, self.accent, self._on_tile_input)
        self.grid.setMinimumHeight(260)
        self.grid.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.grid, 1); root.addSpacing(10)

        chips = QHBoxLayout(); chips.setSpacing(10)
        self.score_c = StatChip("score",      "0",                self.neon)
        self.round_c = StatChip("round",      "0",                self.neon)
        self.best_c  = StatChip("best score", str(G.memory_best), self.neon)
        chips.addWidget(self.score_c); chips.addWidget(self.round_c); chips.addWidget(self.best_c)
        root.addLayout(chips); root.addSpacing(10)

        self.ss_btn = QPushButton("▶  START"); self.ss_btn.setFont(F(15, 700))
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
        eff.setColor(QColor(self.neon)); eff.setOffset(0, 3); self.ss_btn.setGraphicsEffect(eff)

    def _flash_ms(self):
        return max(self._MIN_FLASH_MS, int(self._BASE_FLASH_MS / (1.0 + (self._round-1)*0.15)))

    def _gap_ms(self):
        return max(self._MIN_GAP_MS, int(self._BASE_GAP_MS / (1.0 + (self._round-1)*0.15)))

    def _n_tiles(self): return min(8, 5 + (self._round - 1) // 2)

    def _pattern_len(self): return min(self._n_tiles(), 3 + self._round // 2)

    def _toggle(self):
        if not self._running:
            self._running = True; self._round = 0; self._score = 0
            self.score_c.set("0"); self.round_c.set("0"); self._style_btn(True)
            self._next_round()
        else:
            self._stop_game()

    def _stop_game(self):
        self._running = False; self._show_timer.stop(); self._feedback_timer.stop()
        self.grid.set_phase("idle"); self._style_btn(False)
        self.status_lbl.setText("Stopped")
        if self._score > G.memory_best:
            G.memory_best = self._score; self.best_c.set(str(G.memory_best))
            db = self.main_window.db; u = self.main_window.current_user
            if u: db.update_score(u, "memory", G.memory_best)

    def _next_round(self):
        if not self._running: return
        self._round += 1; n = self._n_tiles(); pl = self._pattern_len()
        self._pattern = random.sample(range(n), pl); self._input_ok = 0
        self.round_lbl.setText(f"ROUND {self._round}"); self.round_c.set(str(self._round))
        sp = 1.0 + (self._round - 1) * 0.15
        self.speed_lbl.setText(f"SPEED ×{sp:.1f}")
        self.grid.setup(n, self._pattern)
        self.status_lbl.setText("Watch the pattern…")
        self._show_idx = 0; self._show_timer.start(400)

    def _show_next_step(self):
        if not self._running: return
        if self._show_idx < len(self._pattern):
            self.grid.play_show(self._pattern[self._show_idx])
            QTimer.singleShot(self._flash_ms(), self._after_flash)
        else:
            self.grid.hide_show(); self.grid.set_phase("input")
            self.status_lbl.setText(f"Repeat the pattern!  (0 / {len(self._pattern)})")

    def _after_flash(self):
        if not self._running: return
        self.grid.hide_show(); self._show_idx += 1; self._show_timer.start(self._gap_ms())

    def _on_tile_input(self, tile_idx, correct):
        if not self._running: return
        if correct:
            self._input_ok += 1
            self.status_lbl.setText(f"Repeat the pattern!  ({self._input_ok} / {len(self._pattern)})")
            if self._input_ok == len(self._pattern):
                self._score += 1; self.score_c.set(str(self._score))
                if self._score > G.memory_best:
                    G.memory_best = self._score; self.best_c.set(str(G.memory_best))
                self.grid.flash_result(True); self.status_lbl.setText("✓  Pattern matched!")
                self._feedback_timer.start(700)
        else:
            self.grid.flash_result(False); self.status_lbl.setText("✗  Wrong tile!  Game over.")
            self._feedback_timer.stop(); QTimer.singleShot(900, self._stop_game)

    def showEvent(self, e): self.best_c.set(str(G.memory_best)); super().showEvent(e)



# ══════════════════════════════════════════════════════════════
#  DOPAMINE METER
# ══════════════════════════════════════════════════════════════
class _EnergyBar(QWidget):
    def __init__(self, neon, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._neon = neon; self._fill = 0.0; self._target = 0.0; self._phase = 0.0
        self._anim_t = QTimer(self); self._anim_t.setInterval(16)
        self._anim_t.timeout.connect(self._step); self._anim_t.start()

    def set_fill(self, v): self._target = max(0.0, min(1.0, v))

    def _step(self):
        self._fill += (self._target - self._fill) * 0.12
        self._phase = (self._phase + 0.05) % (math.pi * 2)
        self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        nc = QColor(self._neon); r, g, b = nc.red(), nc.green(), nc.blue()
        track = QPainterPath(); track.addRoundedRect(QRectF(0, 0, w, h), w//2, w//2)
        pa.fillPath(track, QColor(18, 22, 32, 220))
        pa.strokePath(track, QPen(QColor(r, g, b, 55), 1.5))
        pa.setPen(QPen(QColor(255, 255, 255, 18), 1))
        for i in range(1, 10):
            y = int(h * i / 10); pa.drawLine(2, y, w - 2, y)
        fill_h = int(h * self._fill)
        if fill_h > 1:
            fill_y = h - fill_h
            fill_path = QPainterPath()
            fill_path.addRoundedRect(QRectF(0, fill_y, w, fill_h), w//2, w//2)
            t = self._fill
            if t < 0.6:
                cr, cg, cb = r, g, b
            elif t < 0.85:
                ratio = (t - 0.6) / 0.25
                cr = int(r + (255-r)*ratio); cg = int(g + (200-g)*ratio); cb = int(b*(1-ratio))
            else:
                ratio = (t - 0.85) / 0.15; cr = 255; cg = int(200*(1-ratio)); cb = 0
            pulse = 0.75 + 0.25 * math.sin(self._phase)
            grd = QLinearGradient(0, fill_y + fill_h, 0, fill_y)
            grd.setColorAt(0.0, QColor(cr, cg, cb, int(200*pulse)))
            grd.setColorAt(0.5, QColor(min(cr+40,255), min(cg+40,255), min(cb+40,255), int(230*pulse)))
            grd.setColorAt(1.0, QColor(255, 255, 255, int(180*pulse)))
            pa.fillPath(fill_path, QBrush(grd))
            pa.strokePath(fill_path, QPen(QColor(cr, cg, cb, int(60*pulse)), 6))
        pa.setPen(QColor(r, g, b, 160)); pa.setFont(F(7, 600))
        pa.drawText(QRect(0, 0, w, 18), Qt.AlignCenter, "E")
        pa.end()


class _ZoneWindow(QWidget):
    def __init__(self, neon, on_click, parent=None):
        super().__init__(parent)
        self.neon = neon; self.on_click = on_click
        self.setAttribute(Qt.WA_TranslucentBackground); self.setCursor(Qt.CrossCursor)
        self._running = False; self._ring_r = 80.0; self._target_r = 80.0
        self._phase = 0.0; self._miss_flash = 0; self._hit_flash = 0
        self._anim_t = QTimer(self); self._anim_t.setInterval(16)
        self._anim_t.timeout.connect(self._step)

    def start(self):
        self._running = True; self._ring_r = 80.0; self._target_r = 80.0
        self._miss_flash = 0; self._hit_flash = 0; self._anim_t.start()

    def stop(self): self._running = False; self._anim_t.stop(); self.update()
    def shrink(self): self._target_r = max(28.0, self._target_r - 2.5)
    def reset_ring(self): self._target_r = 80.0

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
        dist = math.hypot(px - self.width()/2, py - self.height()/2)
        if dist <= self._ring_r + 6:
            self._hit_flash = 14; self.on_click(True)
        else:
            self._miss_flash = 14; self.on_click(False)

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); cx, cy = w/2, h/2
        nc = QColor(self.neon); r, g, b = nc.red(), nc.green(), nc.blue()
        bg = QPainterPath(); bg.addRoundedRect(QRectF(1, 1, w-2, h-2), 16, 16)
        pa.fillPath(bg, QColor(10, 12, 18, 160))
        if not self._running:
            pa.setPen(QColor(r, g, b, 80)); pa.setFont(F(13, 500))
            pa.drawText(QRect(0, 0, w, h), Qt.AlignCenter, "Press START to begin")
            pa.end(); return
        pulse = 0.5 + 0.5 * math.sin(self._phase)
        if self._miss_flash > 0:
            pa.fillPath(bg, QColor(220, 40, 40, int(self._miss_flash/14*70)))
        if self._hit_flash > 0:
            pa.fillPath(bg, QColor(r, g, b, int(self._hit_flash/14*60)))
        pa.setPen(QPen(QColor(r, g, b, 25), 1)); pa.setBrush(Qt.NoBrush)
        pa.drawEllipse(QPointF(cx, cy), self._ring_r + 22, self._ring_r + 22)
        pa.setPen(QPen(QColor(r, g, b, int(40+30*pulse)), 18))
        pa.drawEllipse(QPointF(cx, cy), float(self._ring_r), float(self._ring_r))
        pa.setPen(QPen(QColor(r, g, b, int(160+80*pulse)), 3))
        pa.drawEllipse(QPointF(cx, cy), float(self._ring_r), float(self._ring_r))
        pa.setPen(QPen(QColor(r, g, b, 120), 1))
        pa.drawLine(QPointF(cx-10, cy), QPointF(cx+10, cy))
        pa.drawLine(QPointF(cx, cy-10), QPointF(cx, cy+10))
        pa.setPen(QPen(QColor(255, 255, 255, 40), 1))
        for deg in range(0, 360, 30):
            rad = math.radians(deg + self._phase * 10)
            x1 = cx + (self._ring_r-5)*math.cos(rad); y1 = cy + (self._ring_r-5)*math.sin(rad)
            x2 = cx + (self._ring_r+5)*math.cos(rad); y2 = cy + (self._ring_r+5)*math.sin(rad)
            pa.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        pa.setPen(QColor(255, 255, 255, 50)); pa.setFont(F(9, 400))
        pa.drawText(QRect(0, h-28, w, 24), Qt.AlignCenter, "Click INSIDE the Ring  •  Stay Calm")
        pa.end()


class DopamineMeterPage(BasePage):
    """Game: Dopamine Meter — click inside a shrinking ring for 60 seconds.

    Inherits BasePage. Clicking outside drains the energy bar (impulse penalty).
    """
    KEY = "dopa"; DURATION = 60
    _E_HIT_FAST = +8.0; _E_MISS = -15.0; _E_DECAY = -0.04; _E_MAX = 100.0
    _MAX_CPS = 3.5; _IMPULSE_PEN = -12.0

    def _build_content(self):
        self._running = False; self._energy = 0.0; self._score = 0
        self._clicks_this_sec = 0; self._hits = 0; self._misses = 0; self._peak = 0
        self._elapsed = QElapsedTimer()
        self._ticker = QTimer(self); self._ticker.setInterval(50); self._ticker.timeout.connect(self._tick)
        self._sec_t  = QTimer(self); self._sec_t.setInterval(1000); self._sec_t.timeout.connect(self._on_second)
        root = self.root

        top_row = QHBoxLayout(); top_row.setSpacing(12)
        self.ebar = _EnergyBar(self.neon)
        self.ebar.setFixedWidth(28); self.ebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        top_row.addWidget(self.ebar)

        right_col = QVBoxLayout(); right_col.setSpacing(8)
        self.time_bar = _TimeBar(self.neon); self.time_bar.setFixedHeight(8)
        right_col.addWidget(self.time_bar)
        self.status_lbl = QLabel("Stay controlled — click inside the ring")
        self.status_lbl.setFont(F(10, 500)); self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet(f"color:{self.neon};background:transparent;letter-spacing:1px;")
        right_col.addWidget(self.status_lbl)
        self.zone = _ZoneWindow(self.neon, self._on_click)
        self.zone.setMinimumHeight(240)
        self.zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_col.addWidget(self.zone, 1)
        top_row.addLayout(right_col, 1)
        root.addLayout(top_row, 1); root.addSpacing(10)

        self.energy_lbl = GlowLabel("0%", self.neon, 42, mono=True)
        root.addWidget(self.energy_lbl, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("focus energy", self.neon)); root.addSpacing(8)

        chips = QHBoxLayout(); chips.setSpacing(10)
        self.peak_c = StatChip("peak",       "0%",              self.neon)
        self.hits_c = StatChip("controlled", "0",               self.neon)
        self.miss_c = StatChip("impulsive",  "0",               self.neon)
        self.best_c = StatChip("best peak",  f"{G.dopa_best}%", self.neon)
        for c in (self.peak_c, self.hits_c, self.miss_c, self.best_c): chips.addWidget(c)
        root.addLayout(chips); root.addSpacing(10)

        self.ss_btn = QPushButton("▶  START"); self.ss_btn.setFont(F(15, 700))
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
        eff.setColor(QColor(self.neon)); eff.setOffset(0, 3); self.ss_btn.setGraphicsEffect(eff)

    def _set_energy(self, v):
        self._energy = max(0.0, min(self._E_MAX, v))
        pct = int(self._energy); self.energy_lbl.set(f"{pct}%")
        self.ebar.set_fill(self._energy / self._E_MAX)
        if pct > self._peak: self._peak = pct; self.peak_c.set(f"{self._peak}%")

    def _status_for_energy(self):
        e = self._energy
        if e >= 80: return "🔥  MAX FOCUS — incredible control!"
        if e >= 60: return "⚡  High energy — keep it steady"
        if e >= 40: return "✓  Good rhythm — stay calm"
        if e >= 20: return "↓  Losing focus — slow down"
        return "✗  Too impulsive — breathe and aim"

    def _toggle(self):
        if not self._running:
            self._running = True; self._energy = 30.0
            self._hits = 0; self._misses = 0; self._peak = 0; self._clicks_this_sec = 0
            self.hits_c.set("0"); self.miss_c.set("0"); self.peak_c.set("0%")
            self._set_energy(30.0); self._elapsed.start(); self.time_bar.set(1.0)
            self._style_btn(True); self.zone.start(); self._ticker.start(); self._sec_t.start()
        else:
            self._end_session()

    def _on_click(self, controlled):
        if not self._running: return
        self._clicks_this_sec += 1
        if controlled:
            self._hits += 1; self.hits_c.set(str(self._hits))
            self._set_energy(self._energy + self._E_HIT_FAST)
            self.status_lbl.setText(self._status_for_energy())
        else:
            self._misses += 1; self.miss_c.set(str(self._misses))
            self._set_energy(self._energy + self._E_MISS)
            self.status_lbl.setText("✗  Outside ring — aim carefully!")

    def _on_second(self):
        if not self._running: return
        if self._clicks_this_sec > self._MAX_CPS:
            self._set_energy(self._energy + self._IMPULSE_PEN)
            self.status_lbl.setText("⚠  Slow down! Too rapid clicking.")
        self._clicks_this_sec = 0; self.zone.shrink()

    def _tick(self):
        if not self._running: return
        remaining = max(0.0, self.DURATION - self._elapsed.elapsed()/1000.0)
        self.time_bar.set(remaining / self.DURATION)
        self._set_energy(self._energy + self._E_DECAY)
        if remaining <= 0: self._end_session()

    def _end_session(self):
        self._ticker.stop(); self._sec_t.stop(); self._running = False
        self.zone.stop(); self.zone.reset_ring(); self._style_btn(False); self.time_bar.set(0.0)
        if self._peak > G.dopa_best:
            G.dopa_best = self._peak; self.best_c.set(f"{G.dopa_best}%")
            db = self.main_window.db; u = self.main_window.current_user
            if u: db.update_score(u, "dopa", G.dopa_best)
        self.status_lbl.setText(f"Session done!  Peak energy: {self._peak}%")

    def showEvent(self, e): self.best_c.set(f"{G.dopa_best}%"); super().showEvent(e)


# ══════════════════════════════════════════════════════════════
#  REACTION COLOR SHIFT
# ══════════════════════════════════════════════════════════════
_RCS_COLORS = [
    ("blue",   "BLUE",   "#3b82f6", "#0a1a40", False),
    ("red",    "RED",    "#ff4d4d", "#3a0000", False),
    ("green",  "GREEN",  "#10b981", "#001a10", False),
    ("purple", "PURPLE", "#8b5cf6", "#1a0040", False),
    ("orange", "ORANGE", "#f97316", "#3a1000", False),
    ("cyan",   "CYAN",   "#06b6d4", "#001a25", False),
]


class _ColorFlashZone(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._cur_color = QColor(10, 11, 18); self._tgt_color = QColor(10, 11, 18)
        self._phase = 0.0
        self._anim_t = QTimer(self); self._anim_t.setInterval(16)
        self._anim_t.timeout.connect(self._step); self._anim_t.start()

    def flash(self, hex_color): self._tgt_color = QColor(hex_color)
    def reset(self): self._tgt_color = QColor(10, 11, 18)

    def _step(self):
        c = self._cur_color; t = self._tgt_color
        self._cur_color = QColor(
            int(c.red()   + (t.red()   - c.red())   * 0.15),
            int(c.green() + (t.green() - c.green()) * 0.15),
            int(c.blue()  + (t.blue()  - c.blue())  * 0.15),
        )
        self._phase = (self._phase + 0.025) % (math.pi * 2); self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); c = self._cur_color
        grd = QRadialGradient(w/2, h/2, max(w, h)*0.7)
        pulse = 0.85 + 0.15 * math.sin(self._phase)
        bright = QColor(min(255, int(c.red()*1.4*pulse)), min(255, int(c.green()*1.4*pulse)), min(255, int(c.blue()*1.4*pulse)))
        dark   = QColor(max(0, int(c.red()*0.25)),        max(0, int(c.green()*0.25)),        max(0, int(c.blue()*0.25)))
        grd.setColorAt(0.0, bright); grd.setColorAt(1.0, dark)
        pa.fillRect(0, 0, w, h, QBrush(grd)); pa.end()


class _ColorButton(QWidget):
    def __init__(self, key, label, neon_hex, bg_hex, on_press, parent=None):
        super().__init__(parent)
        self.key = key; self._neon = neon_hex; self._bg = bg_hex
        self._label = label; self._on_press = on_press
        self._hover = False; self._flash = 0; self._flash_ok = True
        self.setCursor(Qt.PointingHandCursor); self.setMinimumHeight(56)
        self._anim_t = QTimer(self); self._anim_t.setInterval(16)
        self._anim_t.timeout.connect(self._step)

    def do_flash(self, correct):
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
        path = QPainterPath(); path.addRoundedRect(QRectF(0, 0, w, h), 14, 14)
        if self._flash > 0:
            t = self._flash / 22
            fc = QColor(int(r*0.4+40*t), int(g*0.4+180*t), int(b*0.4+40*t), 240) if self._flash_ok else QColor(200, int(30*t), int(30*t), 240)
            pa.fillPath(path, fc)
        elif self._hover:
            grd = QLinearGradient(0, 0, w, 0)
            grd.setColorAt(0, QColor(r, g, b, 120)); grd.setColorAt(1, QColor(r, g, b, 60))
            pa.fillPath(path, QBrush(grd))
        else:
            pa.fillPath(path, QColor(bg.red(), bg.green(), bg.blue(), 200))
        pa.strokePath(path, QPen(QColor(r, g, b, 200 if self._hover else 100), 2))
        bar = QPainterPath(); bar.addRoundedRect(QRectF(0, h*0.2, 4, h*0.6), 2, 2)
        pa.fillPath(bar, nc)
        pa.setPen(QColor(255, 255, 255, 230)); pa.setFont(F(15, 700))
        pa.drawText(QRect(0, 0, w, h), Qt.AlignCenter, self._label)
        pa.end()


class _ReactionTimerBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._progress = 0.0; self._neon = "#ffffff"; self._danger = False

    def start_drain(self, neon): self._neon = neon; self._progress = 1.0; self._danger = False
    def set(self, v): self._progress = max(0.0, min(1.0, v)); self._danger = v < 0.25; self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); r = h//2
        pa.setBrush(QColor(255, 255, 255, 15)); pa.setPen(Qt.NoPen)
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
    """Game: Color Shift — react by clicking the button matching the displayed colour.

    Inherits BasePage. Tracks reaction time over 15 rounds.
    """
    KEY = "rcs"; ROUNDS = 15; WINDOW_MS = 2000; MIN_WIN_MS = 800

    def _build_content(self):
        self._running = False; self._round = 0; self._score = 0; self._streak = 0
        self._target_key = ""; self._window_ms = self.WINDOW_MS; self._waiting = False
        self._elapsed_r = QElapsedTimer()
        self._drain_t = QTimer(self); self._drain_t.setInterval(16); self._drain_t.timeout.connect(self._drain_tick)
        self._next_t  = QTimer(self); self._next_t.setSingleShot(True); self._next_t.timeout.connect(self._next_round)
        root = self.root

        flash_container = QWidget()
        flash_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        flash_container.setMinimumHeight(160)
        flash_layout = QVBoxLayout(flash_container); flash_layout.setContentsMargins(0, 0, 0, 0)
        self.flash_zone = _ColorFlashZone(); self.flash_zone.setParent(flash_container); self.flash_zone.lower()

        self.round_lbl = QLabel("Press START"); self.round_lbl.setFont(F(11, 600))
        self.round_lbl.setAlignment(Qt.AlignCenter)
        self.round_lbl.setStyleSheet("color:rgba(255,255,255,200);background:transparent;")
        flash_layout.addStretch(); flash_layout.addWidget(self.round_lbl)

        self.color_lbl = QLabel(""); self.color_lbl.setFont(F(38, 900))
        self.color_lbl.setAlignment(Qt.AlignCenter)
        self.color_lbl.setStyleSheet("color:white;background:transparent;")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(40); eff.setColor(QColor("white")); eff.setOffset(0,0)
        self.color_lbl.setGraphicsEffect(eff); flash_layout.addWidget(self.color_lbl)

        self.react_lbl = QLabel(""); self.react_lbl.setFont(FM(13, True))
        self.react_lbl.setAlignment(Qt.AlignCenter)
        self.react_lbl.setStyleSheet("color:rgba(255,255,255,180);background:transparent;")
        flash_layout.addWidget(self.react_lbl); flash_layout.addStretch()
        root.addWidget(flash_container, 1)

        self.react_bar = _ReactionTimerBar(); self.react_bar.setFixedHeight(10)
        root.addWidget(self.react_bar); root.addSpacing(8)

        self._btns: dict = {}
        for row_i in range(2):
            row = QHBoxLayout(); row.setSpacing(8)
            for col_j in range(3):
                idx = row_i * 3 + col_j
                key, label, neon, bg, _ = _RCS_COLORS[idx]
                btn = _ColorButton(key, label, neon, bg, self._on_btn_press)
                self._btns[key] = btn; row.addWidget(btn)
            root.addLayout(row); root.addSpacing(6)
        root.addSpacing(4)

        chips = QHBoxLayout(); chips.setSpacing(10)
        self.score_c  = StatChip("score",  "0",             self.neon)
        self.streak_c = StatChip("streak", "0",             self.neon)
        self.best_c   = StatChip("best",   str(G.rcs_best), self.neon)
        for c in (self.score_c, self.streak_c, self.best_c): chips.addWidget(c)
        root.addLayout(chips); root.addSpacing(10)

        self.ss_btn = QPushButton("▶  START"); self.ss_btn.setFont(F(15, 700))
        self.ss_btn.setFixedWidth(200); self.ss_btn.setFixedHeight(48)
        self.ss_btn.setCursor(Qt.PointingHandCursor); self.ss_btn.clicked.connect(self._toggle)
        self._style_btn(False); root.addWidget(self.ss_btn, 0, Qt.AlignCenter)

    def resizeEvent(self, e):
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

    def _toggle(self):
        if not self._running:
            self._running=True; self._round=0; self._score=0; self._streak=0
            self._window_ms=self.WINDOW_MS; self.score_c.set("0"); self.streak_c.set("0")
            self._style_btn(True); self._next_round()
        else:
            self._end_session(aborted=True)

    def _next_round(self):
        if not self._running: return
        self._round += 1
        if self._round > self.ROUNDS: self._end_session(aborted=False); return
        choices = [c for c in _RCS_COLORS if c[0] != self._target_key]
        entry = random.choice(choices); self._target_key = entry[0]
        _, label, neon, bg, _ = entry
        self.round_lbl.setText(f"ROUND {self._round} / {self.ROUNDS}")
        self.color_lbl.setText(label)
        self.react_lbl.setText("")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(50); eff.setColor(QColor(neon)); eff.setOffset(0,0)
        self.color_lbl.setGraphicsEffect(eff)
        self.color_lbl.setStyleSheet(f"color:{neon};background:transparent;")
        self.flash_zone.flash(bg); self.react_bar.start_drain(neon)
        self._waiting = False; self._elapsed_r.start(); self._drain_t.start()

    def _drain_tick(self):
        if not self._running: return
        elapsed = self._elapsed_r.elapsed()
        remaining = max(0.0, self._window_ms - elapsed)
        self.react_bar.set(remaining / self._window_ms)
        if remaining <= 0: self._drain_t.stop(); self._on_timeout()

    def _on_timeout(self):
        self._streak = 0; self.streak_c.set("0"); self.react_lbl.setText("✗  Too slow!")
        self.color_lbl.setText(""); self.flash_zone.reset()
        for btn in self._btns.values(): btn.do_flash(False)
        self._waiting = True; self._next_t.start(900)

    def _on_btn_press(self, key):
        if not self._running or self._waiting: return
        self._drain_t.stop(); react_ms = self._elapsed_r.elapsed()
        correct = (key == self._target_key); self._btns[key].do_flash(correct)
        if correct:
            self._streak += 1
            pts = 100 + max(0, int((self._window_ms - react_ms)/self._window_ms*50)) + (self._streak-1)*10
            self._score += pts; self.score_c.set(str(self._score)); self.streak_c.set(str(self._streak))
            self.react_lbl.setText(f"✓  {react_ms} ms  +{pts} pts")
            self._window_ms = max(self.MIN_WIN_MS, self._window_ms - 30)
        else:
            self._streak = 0; self.streak_c.set("0"); self.react_lbl.setText("✗  Wrong color!")
            self.flash_zone.reset()
        self.color_lbl.setText(""); self._waiting = True
        self._next_t.start(700 if correct else 1000)

    def _end_session(self, aborted=False):
        self._drain_t.stop(); self._next_t.stop(); self._running = False
        self.flash_zone.reset(); self._style_btn(False); self.react_bar.set(0.0)
        self.color_lbl.setText("")
        if self._score > G.rcs_best:
            G.rcs_best = self._score; self.best_c.set(str(G.rcs_best))
            db = self.main_window.db; u = self.main_window.current_user
            if u: db.update_score(u, "rcs", G.rcs_best)
        self.round_lbl.setText("Stopped" if aborted else f"Done!  Score: {self._score}  •  Best: {G.rcs_best}")
        self.react_lbl.setText("")

    def showEvent(self, e): self.best_c.set(str(G.rcs_best)); super().showEvent(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Set a proper default font to prevent Qt "Point size <= 0" warnings
    default_font = QFont("Segoe UI", 11)
    app.setFont(default_font)
    app.setStyleSheet(GLOBAL_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())