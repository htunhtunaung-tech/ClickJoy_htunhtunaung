import math
import random

from PySide6.QtWidgets import (QHBoxLayout, QVBoxLayout, QWidget,
                                QPushButton, QSizePolicy, QLabel,
                                QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QRectF, QPointF, QRect
from PySide6.QtGui import (QPainter, QPainterPath, QColor, QPen, QBrush,
                            QRadialGradient, QLinearGradient)

from theme_and_animation import (F, FM, GlowLabel, StatChip, cap_lbl,
                                  NEON, TEXT, DIM, GHOST, EDGE, PANEL)
from base_game_page import BasePage, G


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

        # Keep flash_zone filling the container whenever it resizes
        def _fc_resize(e, fc=flash_container, fz=self.flash_zone):
            fz.setGeometry(0, 0, fc.width(), fc.height())
        flash_container.resizeEvent = _fc_resize

        self.round_lbl = QLabel("Press START"); self.round_lbl.setFont(F(11, 600))
        self.round_lbl.setAlignment(Qt.AlignCenter)
        self.round_lbl.setStyleSheet("color:rgba(255,255,255,200);background:transparent;")
        flash_layout.addStretch(); flash_layout.addWidget(self.round_lbl)

        self.color_lbl = QLabel(""); self.color_lbl.setFont(F(38, 900))
        self.color_lbl.setAlignment(Qt.AlignCenter)
        self.color_lbl.setStyleSheet("color:white;background:transparent;")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(40); eff.setColor(QColor("white")); eff.setOffset(0,0)
        self.color_lbl.setGraphicsEffect(eff); flash_layout.addWidget(self.color_lbl)

        self.react_lbl = QLabel(""); self.react_lbl.setFont(F(13, True))
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
            G.rcs += 1
            db = self.main_window.db; u = self.main_window.current_user
            if u: db.update_score(u, "rcs", G.rcs)
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
        self.round_lbl.setText("Stopped" if aborted else f"Done!  Score: {self._score}  •  Best: {G.rcs_best}")
        self.react_lbl.setText("")

    def showEvent(self, e):
        u = self.main_window.current_user
        if u:
            ud = self.main_window.db.get_user(u)
            if ud: G.rcs = ud.get('rcs', 0)
        self.best_c.set(str(G.rcs_best)); super().showEvent(e)