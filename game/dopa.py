import math

from PySide6.QtWidgets import (QHBoxLayout, QVBoxLayout, QWidget,
                                QPushButton, QSizePolicy, QLabel,
                                QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QRectF, QPointF, QRect
from PySide6.QtGui import (QPainter, QPainterPath, QColor, QPen, QBrush,
                            QRadialGradient, QLinearGradient)

from theme_and_animation import (F, FM, GlowLabel, StatChip, cap_lbl,
                                  _TimeBar, NEON, TEXT, DIM, GHOST, EDGE, PANEL)
from base_game_page import BasePage, G


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
