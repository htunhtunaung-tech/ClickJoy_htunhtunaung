from PySide6.QtWidgets import QWidget, QHBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from theme_and_animation import (GlowLabel, StatChip, NeonToggle, CornerBrackets, cap_lbl,
    NEON, GHOST, DIM, F)
from base_game_page import BasePage, G

class SwitchPage(BasePage):
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