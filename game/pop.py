from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer, QElapsedTimer
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush, QRadialGradient, QLinearGradient
from PySide6.QtCore import QRectF, QPointF

from theme_and_animation import (F, GlowLabel, StatChip, cap_lbl, NEON,
                                  DIM, TEXT, EDGE, PANEL, SURFACE, BG, GHOST)
from base_game_page import BasePage, G


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
