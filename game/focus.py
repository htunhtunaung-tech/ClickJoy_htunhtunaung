import math
import random

from PySide6.QtWidgets import (QHBoxLayout, QVBoxLayout, QWidget,
                                QPushButton, QSizePolicy, QLabel,
                                QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QRect, QRectF, QPointF
from PySide6.QtGui import (QPainter, QPainterPath, QColor, QPen, QBrush,
                            QRadialGradient, QLinearGradient, QPolygonF)

from theme_and_animation import (F, GlowLabel, StatChip, cap_lbl, NEON,
                                  DIM, TEXT, EDGE, PANEL, SURFACE, BG, GHOST)
from base_game_page import BasePage, G


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
    """Game: Focus Burst — click the correct target among decoys for 30 seconds."""
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
        G.focus += 1
        db = self.main_window.db; u = self.main_window.current_user
        if u: db.update_score(u, "focus", G.focus)
        if self._combo > G.focus_best:
            G.focus_best = self._combo; self.best_c.set(str(G.focus_best))
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

    def showEvent(self, e):
        u = self.main_window.current_user
        if u:
            ud = self.main_window.db.get_user(u)
            if ud: G.focus = ud.get('focus', 0)
        self.best_c.set(str(G.focus_best)); super().showEvent(e)