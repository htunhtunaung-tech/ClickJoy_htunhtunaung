from PySide6.QtCore import Qt
from theme_and_animation import GlowLabel, StatChip, NeonTapButton, Particles, CornerBrackets, cap_lbl, NEON
from base_game_page import BasePage, G

class NormalClickPage(BasePage):
    KEY = "normal"

    def _build_content(self):
        self._session = 0
        root = self.root
        self.score = GlowLabel("0", self.neon, 68, mono=True)
        root.addWidget(self.score, 0, Qt.AlignCenter)
        root.addWidget(cap_lbl("total clicks", self.neon))
        root.addSpacing(32)
        from PySide6.QtWidgets import QWidget
        ctr = QWidget(); ctr.setFixedSize(260, 260)
        ctr.setStyleSheet("background:transparent;")
        self.btn = NeonTapButton("TAP", self.neon, self.accent, 230, ctr)
        self.btn.move(15, 15); self.btn.clicked = self._tap
        self.parts = Particles(ctr); self.parts.setGeometry(0, 0, 260, 260)
        self.brackets = CornerBrackets(self.neon, 20, 2, ctr)
        self.brackets.setGeometry(0, 0, 260, 260)
        root.addWidget(ctr, 0, Qt.AlignCenter)
        root.addStretch()
        from PySide6.QtWidgets import QHBoxLayout
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
