import math
import random

from PySide6.QtWidgets import (QHBoxLayout, QVBoxLayout, QWidget,
                                QPushButton, QSizePolicy, QLabel,
                                QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QRectF, QPointF, QRect
from PySide6.QtGui import (QPainter, QPainterPath, QColor, QPen, QBrush,
                            QRadialGradient, QLinearGradient, QFont)

from theme_and_animation import (F, FM, GlowLabel, StatChip, cap_lbl,
                                  _TimeBar, NEON, TEXT, DIM, GHOST, EDGE,
                                  PANEL, BG, SURFACE)
from base_game_page import BasePage, G


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
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(22 if not running else 8)
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
        G.chaos += self._hits
        db = self.main_window.db; u = self.main_window.current_user
        if u: db.update_score(u, "chaos", G.chaos)

    def showEvent(self, e):
        u = self.main_window.current_user
        if u:
            ud = self.main_window.db.get_user(u)
            if ud: G.chaos = ud.get('chaos', 0)
        self.best_c.set(str(G.chaos_best)); super().showEvent(e)