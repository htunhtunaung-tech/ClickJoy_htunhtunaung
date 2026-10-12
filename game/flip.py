import math, random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, QRectF, QRect, QPointF, Signal
from PySide6.QtGui import (QColor, QPainter, QPainterPath, QPen, QBrush,
    QRadialGradient, QLinearGradient)
from theme_and_animation import (F, FM, StatChip, CoinDisc, NEON, GHOST, TEXT, DIM)
from base_game_page import BasePage, G

# ══════════════════════════════════════════════════════════════
#  FLIP COIN helpers
# ══════════════════════════════════════════════════════════════
class ResultBanner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._text  = ""; self._color = QColor(GHOST)
        self._alpha = 0.0; self._scale = 1.0; self._frame = 0; self._active = False
        self._t = QTimer(self); self._t.setInterval(14); self._t.timeout.connect(self._step)

    def show_result(self, text, color):
        self._text = text; self._color = QColor(color)
        self._frame = 0; self._active = True; self._t.start()

    def _step(self):
        self._frame += 1; t = self._frame
        if t < 12: self._scale = 0.5 + (t / 12) * 0.9; self._alpha = t / 12
        elif t < 38: self._scale = 1.0 + math.sin((t - 12) / 26 * math.pi) * 0.06; self._alpha = 1.0
        elif t < 55: self._alpha = 1.0 - (t - 38) / 17; self._scale = 1.0
        else: self._active = False; self._alpha = 0.0; self._t.stop()
        self.update()

    def paintEvent(self, ev):
        if self._alpha <= 0: return
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); cx, cy = w // 2, h // 2
        nc = self._color; a = int(self._alpha * 255)
        pa.save()
        pa.translate(cx, cy); pa.scale(self._scale, self._scale); pa.translate(-cx, -cy)
        has_streak = "×" in self._text
        font_size = 22 if has_streak else 42
        pill_w = 210 if has_streak else 180; pill_h = 52 if has_streak else 64
        pill = QPainterPath()
        pill.addRoundedRect(QRectF(cx - pill_w // 2, cy - pill_h // 2, pill_w, pill_h), 18, 18)
        pa.fillPath(pill, QColor(nc.red(), nc.green(), nc.blue(), int(a * 0.22)))
        pa.strokePath(pill, QPen(QColor(nc.red(), nc.green(), nc.blue(), int(a * 0.7)), 2))
        pa.setFont(FM(font_size, True))
        pa.setPen(QColor(0, 0, 0, int(a * 0.5)))
        pa.drawText(QRect(2, 2, w, h), Qt.AlignCenter, self._text)
        pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), a))
        pa.drawText(QRect(0, 0, w, h), Qt.AlignCenter, self._text)
        pa.restore(); pa.end()


class StreakBadge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(110, 70)
        self._streak = 0; self._pulse = 0.0; self._neon = QColor(GHOST)
        self._t = QTimer(self); self._t.setInterval(14); self._t.timeout.connect(self._step)
        self._t.start()

    def set_streak(self, n, color):
        self._streak = n; self._neon = QColor(color)
        self._pulse = 1.4 if n > 1 else 0.0; self.update()

    def _step(self):
        if self._pulse > 0: self._pulse = max(0.0, self._pulse - 0.06); self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        nc = self._neon; w, h = self.width(), self.height()
        sc = 1.0 + self._pulse * 0.12; cx, cy = w // 2, h // 2
        pa.translate(cx, cy); pa.scale(sc, sc); pa.translate(-cx, -cy)
        path = QPainterPath(); path.addRoundedRect(QRectF(1, 1, w - 2, h - 2), 12, 12)
        pa.fillPath(path, QColor(nc.red(), nc.green(), nc.blue(), 28))
        pa.strokePath(path, QPen(QColor(nc.red(), nc.green(), nc.blue(), 120), 1.5))
        pa.setFont(FM(22, True)); pa.setPen(nc)
        pa.drawText(QRect(0, 0, w, h - 18), Qt.AlignCenter, f"×{self._streak}")
        pa.setFont(F(8, 500)); pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), 160))
        pa.drawText(QRect(0, h - 22, w, 20), Qt.AlignCenter, "STREAK")
        pa.end()


# ══════════════════════════════════════════════════════════════
#  FLIP COIN PAGE
# ══════════════════════════════════════════════════════════════
class FlipCoinPage(BasePage):
    KEY = "flip"

    def _build_content(self):
        root = self.root
        top = QHBoxLayout(); top.setSpacing(10)
        self.flips_c = StatChip("flips", "0", self.neon)
        self.side_c  = StatChip("last",  "—", self.neon)
        top.addWidget(self.flips_c); top.addWidget(self.side_c)
        root.addLayout(top); root.addSpacing(18)
        coin_wrap = QWidget(); coin_wrap.setFixedSize(220, 220)
        coin_wrap.setStyleSheet("background:transparent;")
        self.coin = CoinDisc(coin_wrap)
        self.coin.result_landed.connect(self._on_landed)
        self.banner = ResultBanner(coin_wrap); self.banner.setGeometry(0, 0, 220, 220)
        root.addWidget(coin_wrap, 0, Qt.AlignCenter); root.addSpacing(10)
        self.streak_badge = StreakBadge()
        self.streak_badge.set_streak(0, self.neon)
        root.addWidget(self.streak_badge, 0, Qt.AlignCenter); root.addSpacing(14)
        nc = QColor(self.neon); r, g, b = nc.red(), nc.green(), nc.blue()
        nc2 = QColor(self.accent)
        self.fbtn = QPushButton("◆  FLIP"); self.fbtn.setFont(F(17, 700))
        self.fbtn.setFixedWidth(240); self.fbtn.setFixedHeight(58)
        self.fbtn.setCursor(Qt.PointingHandCursor)
        self.fbtn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 rgba({r},{g},{b},200),
                    stop:1 rgba({nc2.red()},{nc2.green()},{nc2.blue()},200));
                color:{TEXT}; border:none; border-radius:16px; letter-spacing:3px;
            }}
            QPushButton:hover  {{ background:rgba({r},{g},{b},255); }}
            QPushButton:pressed {{ background:rgba({r//2},{g//2},{b//2},240);padding-top:3px; }}
        """)
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(32)
        eff.setColor(QColor(self.neon)); eff.setOffset(0, 5)
        self.fbtn.setGraphicsEffect(eff)
        self.fbtn.clicked.connect(self._flip)
        root.addWidget(self.fbtn, 0, Qt.AlignCenter); root.addStretch()
        bot = QHBoxLayout(); bot.setSpacing(10)
        self.bh = StatChip("best H streak", "0", NEON["flip"][0])
        self.bt = StatChip("best T streak", "0", NEON["swap"][0])
        bot.addWidget(self.bh); bot.addWidget(self.bt)
        root.addLayout(bot)
        self._shake_frames = 0
        self._shake_t = QTimer(self); self._shake_t.setInterval(14)
        self._shake_t.timeout.connect(self._do_shake)
        self._last_result = None

    def _flip(self):
        result = random.choice(["H", "T"]); G.flip += 1
        db = self.main_window.db; u = self.main_window.current_user
        if u: db.update_score(u, "flip", G.flip)
        if result == G.flip_side: G.flip_streak += 1
        else: G.flip_streak = 1; G.flip_side = result
        if result == "H": G.flip_best_h = max(G.flip_best_h, G.flip_streak)
        else:             G.flip_best_t = max(G.flip_best_t, G.flip_streak)
        self._last_result = result
        self.coin.flip_to(result)
        self.flips_c.set(G.flip); self.side_c.set(result)
        self.bh.set(G.flip_best_h); self.bt.set(G.flip_best_t)

    def _on_landed(self):
        result = self._last_result
        if result is None: return
        color  = NEON["flip"][0] if result == "H" else NEON["swap"][0]
        label  = "HEADS!" if result == "H" else "TAILS!"
        if G.flip_streak >= 3: label = f"{label}  🔥×{G.flip_streak}"
        self.banner.show_result(label, color)
        self.streak_badge.set_streak(G.flip_streak, color)

    def _do_shake(self): pass

    def showEvent(self, e):
        u = self.main_window.current_user
        if u:
            ud = self.main_window.db.get_user(u)
            if ud: G.flip = ud.get("flip", 0)
        self.flips_c.set(G.flip)
        super().showEvent(e)
