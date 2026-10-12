from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QElapsedTimer, QTimer
from PySide6.QtGui import QColor
from theme_and_animation import (GlowLabel, StatChip, StyledInput, F, FM, NEON, DIM, TEXT)
from base_game_page import BasePage, G

class StopwatchPage(BasePage):
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
        root.addWidget(QLabel(), 0, Qt.AlignCenter)  # spacer
        from theme_and_animation import cap_lbl
        root.addWidget(cap_lbl("seconds", self.neon)); root.addSpacing(28)
        self.ss_btn = __import__("PySide6.QtWidgets", fromlist=["QPushButton"]).QPushButton("▶  START")
        self.ss_btn.setFont(F(16, 700)); self.ss_btn.setFixedWidth(240); self.ss_btn.setFixedHeight(56)
        self.ss_btn.setCursor(Qt.PointingHandCursor); self.ss_btn.clicked.connect(self._toggle)
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
            self.ss_btn.setStyleSheet(f"QPushButton {{background:rgba({r//2},{g//2},{b//2},220);color:{TEXT};border:1px solid rgba({r},{g},{b},120);border-radius:14px;}}QPushButton:hover{{background:rgba({r},{g},{b},200);}}")
        else:
            self.ss_btn.setStyleSheet(f"QPushButton {{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 rgba({r},{g},{b},200),stop:1 rgba({r2},{g2},{b2},200));color:{TEXT};border:none;border-radius:14px;}}QPushButton:hover{{background:rgba({r},{g},{b},255);}}QPushButton:pressed{{background:rgba({r//2},{g//2},{b//2},255);}}")
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
            G.stop += 1
            if u: db.update_score(u, "stop", G.stop)

    def _tick(self):
        self.live_lbl.set(f"{self._elapsed.elapsed() / 1000.0:.2f}")

    def _reset(self):
        self._ticker.stop(); self._running = False; self._style_ss(False)
        self.live_lbl.set("0.00"); self.excess_lbl.setText("—")
        self.excess_lbl.setStyleSheet(f"color:{DIM};background:transparent;")
        self.excess_lbl.setGraphicsEffect(None); self.t_input.setEnabled(True)

    def showEvent(self, e):
        u = self.main_window.current_user
        if u:
            ud = self.main_window.db.get_user(u)
            if ud: G.stop = ud.get('stop', 0)
        if G.stop_best < float("inf"):
            be = G.stop_best; bs = "+" if be >= 0 else "-"
            self.best_c.set(f"{bs}{abs(be):.2f}s")
        super().showEvent(e)