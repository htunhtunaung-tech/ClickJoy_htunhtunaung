import random
from PySide6.QtWidgets import QWidget, QLabel, QSizePolicy
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QBrush
from theme_and_animation import GlowLabel, StatChip, NeonTapButton, Particles, cap_lbl, DIM, NEON
from base_game_page import BasePage, G

class SwapClickPage(BasePage):
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
        from theme_and_animation import F
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
        sz = 16; pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), 80), 2))
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
