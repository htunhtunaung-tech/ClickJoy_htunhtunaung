from PySide6.QtWidgets import QWidget, QHBoxLayout
from PySide6.QtCore import Qt, QElapsedTimer, QTimer
from theme_and_animation import (GlowLabel, StatChip, NeonRing, NeonTapButton, Particles,
    StyledInput, _TimeBar, cap_lbl, F, NEON, DIM)
from base_game_page import BasePage, G

class ClickPerTimePage(BasePage):
    KEY = "cpm"

    def _build_content(self):
        self._clicks = 0; self._running = False; self._finished = False
        self._elapsed = QElapsedTimer()
        self._ticker  = QTimer(self); self._ticker.setInterval(16)
        self._ticker.timeout.connect(self._tick)
        root = self.root
        dur_row = QHBoxLayout()
        from PySide6.QtWidgets import QLabel
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
        root.addWidget(cap_lbl("clicks", self.neon)); root.addSpacing(14)
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
        G.cpm += 1
        db = self.main_window.db; u = self.main_window.current_user
        if u: db.update_score(u, "cpm", G.cpm)
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

    def _reset(self):
        self._ticker.stop(); self._running = self._finished = False
        self._clicks = 0; self.clicks_lbl.set("0"); self.cps_c.set("—")
        self.tap_btn.setEnabled(True); self.t_input.setEnabled(True); self._sync_ring()

    def showEvent(self, e):
        if not self._running and not self._finished: self._sync_ring()
        u = self.main_window.current_user
        if u:
            ud = self.main_window.db.get_user(u)
            if ud: G.cpm = ud.get('cpm', 0)
        self.best_c.set(f"{G.cpm_cps:.2f}"); super().showEvent(e)