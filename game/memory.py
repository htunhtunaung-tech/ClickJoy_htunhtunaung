import math
import random

from PySide6.QtWidgets import (QHBoxLayout, QVBoxLayout, QWidget,
                                QPushButton, QSizePolicy, QLabel,
                                QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, QRect
from PySide6.QtGui import (QPainter, QPainterPath, QColor, QPen, QBrush,
                            QRadialGradient, QLinearGradient)

from theme_and_animation import (F, FM, GlowLabel, StatChip, cap_lbl,
                                  NEON, TEXT, DIM, GHOST, EDGE, PANEL, BG, SURFACE)
from base_game_page import BasePage, G


class MemoryGrid(QWidget):
    COLS = 4

    def __init__(self, neon, accent, on_input, parent=None):
        super().__init__(parent)
        self.neon = neon; self.accent = accent; self.on_input = on_input
        self._n_tiles = 8; self._pattern: list = []; self._revealed: list = []
        self._lit_show = -1; self._wrong_id = -1; self._wrong_timer = 0
        self._result_flash = 0; self._result_win = False
        self._phase = "idle"; self._pulse = 0.0
        self._anim_t = QTimer(self); self._anim_t.setInterval(16)
        self._anim_t.timeout.connect(self._anim_step); self._anim_t.start()

    def _rows(self): return math.ceil(self._n_tiles / self.COLS)

    def _tile_rect(self, idx):
        cols = self.COLS; rows = self._rows()
        w, h = self.width(), self.height()
        pad = 10; gap = 8
        tw = (w - pad*2 - gap*(cols-1)) / cols
        th = (h - pad*2 - gap*(rows-1)) / rows
        c = idx % cols; r = idx // cols
        return QRectF(pad + c*(tw+gap), pad + r*(th+gap), tw, th)

    def setup(self, n_tiles, pattern):
        self._n_tiles = n_tiles; self._pattern = list(pattern); self._revealed.clear()
        self._lit_show = -1; self._wrong_id = -1; self._wrong_timer = 0
        self._result_flash = 0; self._phase = "idle"; self.update()

    def play_show(self, lit_index):
        self._lit_show = lit_index; self._phase = "show"; self.update()

    def hide_show(self):
        self._lit_show = -1; self.update()

    def set_phase(self, phase):
        self._phase = phase
        if phase == "idle": self._lit_show = -1; self._revealed.clear()
        self.update()

    def flash_result(self, win):
        self._result_win = win; self._result_flash = 28; self._phase = "result"; self.update()

    def mousePressEvent(self, ev):
        if self._phase != "input" or ev.button() != Qt.LeftButton: return
        try:    px, py = ev.position().x(), ev.position().y()
        except: px, py = float(ev.x()), float(ev.y())
        for i in range(self._n_tiles):
            if self._tile_rect(i).contains(px, py):
                if i in self._revealed: return
                expected = self._pattern[len(self._revealed)]
                correct  = (i == expected)
                if correct: self._revealed.append(i)
                else: self._wrong_id = i; self._wrong_timer = 18
                self.on_input(i, correct); self.update(); return

    def _anim_step(self):
        self._pulse = (self._pulse + 0.04) % (math.pi * 2)
        if self._wrong_timer > 0:
            self._wrong_timer -= 1
            if self._wrong_timer == 0: self._wrong_id = -1
        if self._result_flash > 0: self._result_flash -= 1
        self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        nc = QColor(self.neon); pulse = 0.5 + 0.5 * math.sin(self._pulse)

        if self._phase == "result" and self._result_flash > 0:
            alpha = int(self._result_flash / 28 * 180)
            col = QColor(60, 220, 100, alpha) if self._result_win else QColor(220, 50, 50, alpha)
            pa.fillRect(0, 0, self.width(), self.height(), col)

        for i in range(self._n_tiles):
            rect = self._tile_rect(i)
            path = QPainterPath(); path.addRoundedRect(rect, 10, 10)
            is_lit   = (i == self._lit_show)
            is_done  = (i in self._revealed)
            is_wrong = (i == self._wrong_id)
            is_next  = (self._phase == "input" and
                        len(self._revealed) < len(self._pattern) and
                        i == self._pattern[len(self._revealed)])
            if is_lit:
                glow_a = int(200 + 55 * pulse)
                pa.fillPath(path, QColor(nc.red(), nc.green(), nc.blue(), glow_a))
                pa.strokePath(path, QPen(QColor(255, 255, 255, 200), 2))
                inner = QPainterPath(); inner.addRoundedRect(rect.adjusted(6,6,-6,-6), 6, 6)
                pa.fillPath(inner, QColor(255, 255, 255, 90))
            elif is_done:
                pa.fillPath(path, QColor(nc.red(), nc.green(), nc.blue(), 200))
                pa.strokePath(path, QPen(QColor(255, 255, 255, 120), 1.5))
            elif is_wrong:
                pa.fillPath(path, QColor(220, 50, 50, 220))
                pa.strokePath(path, QPen(QColor(255, 80, 80, 200), 2))
            else:
                shade = 22 + (i % 3) * 5
                pa.fillPath(path, QColor(shade, shade+2, shade+12, 210))
                border_a = int(50 + 30*pulse) if (self._phase == "input" and is_next) else 45
                pa.strokePath(path, QPen(QColor(nc.red(), nc.green(), nc.blue(), border_a), 1))
            if self._phase in ("idle", "show"):
                pa.setPen(QColor(255, 255, 255, 25 if not is_lit else 0))
                pa.setFont(F(9, 400))
                pa.drawText(rect.toRect(), Qt.AlignCenter, str(i + 1))
        pa.end()


class MemoryFlashPage(BasePage):
    KEY = "memory"
    _BASE_FLASH_MS = 600; _BASE_GAP_MS = 200
    _MIN_FLASH_MS  = 180; _MIN_GAP_MS  = 80

    def _build_content(self):
        self._round = 0; self._score = 0; self._running = False
        self._phase = "idle"; self._pattern: list = []
        self._show_idx = 0; self._input_ok = 0
        self._show_timer = QTimer(self); self._show_timer.setSingleShot(True)
        self._show_timer.timeout.connect(self._show_next_step)
        self._feedback_timer = QTimer(self); self._feedback_timer.setSingleShot(True)
        self._feedback_timer.timeout.connect(self._next_round)
        root = self.root

        self.status_lbl = QLabel("Press START")
        self.status_lbl.setFont(F(13, 600)); self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet(f"color:{self.neon};background:transparent;letter-spacing:1px;")
        root.addWidget(self.status_lbl); root.addSpacing(6)

        bar_row = QHBoxLayout(); bar_row.setSpacing(8)
        self.round_lbl = QLabel("ROUND 0"); self.round_lbl.setFont(F(9, 500))
        self.round_lbl.setStyleSheet(f"color:{DIM};background:transparent;letter-spacing:2px;")
        bar_row.addWidget(self.round_lbl); bar_row.addStretch()
        self.speed_lbl = QLabel("SPEED ×1.0"); self.speed_lbl.setFont(F(9, 500))
        self.speed_lbl.setStyleSheet(f"color:{DIM};background:transparent;letter-spacing:2px;")
        bar_row.addWidget(self.speed_lbl); root.addLayout(bar_row); root.addSpacing(4)

        self.grid = MemoryGrid(self.neon, self.accent, self._on_tile_input)
        self.grid.setMinimumHeight(260)
        self.grid.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.grid, 1); root.addSpacing(10)

        chips = QHBoxLayout(); chips.setSpacing(10)
        self.score_c = StatChip("score",      "0",                self.neon)
        self.round_c = StatChip("round",      "0",                self.neon)
        self.best_c  = StatChip("best score", str(G.memory_best), self.neon)
        chips.addWidget(self.score_c); chips.addWidget(self.round_c); chips.addWidget(self.best_c)
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

    def _flash_ms(self):
        return max(self._MIN_FLASH_MS, int(self._BASE_FLASH_MS / (1.0 + (self._round-1)*0.15)))

    def _gap_ms(self):
        return max(self._MIN_GAP_MS, int(self._BASE_GAP_MS / (1.0 + (self._round-1)*0.15)))

    def _n_tiles(self): return min(8, 5 + (self._round - 1) // 2)

    def _pattern_len(self): return min(self._n_tiles(), 3 + self._round // 2)

    def _toggle(self):
        if not self._running:
            self._running = True; self._round = 0; self._score = 0
            self.score_c.set("0"); self.round_c.set("0"); self._style_btn(True)
            self._next_round()
        else:
            self._stop_game()

    def _stop_game(self):
        self._running = False; self._show_timer.stop(); self._feedback_timer.stop()
        self.grid.set_phase("idle"); self._style_btn(False)
        self.status_lbl.setText("Stopped")
        if self._score > G.memory_best:
            G.memory_best = self._score; self.best_c.set(str(G.memory_best))

    def _next_round(self):
        if not self._running: return
        self._round += 1; n = self._n_tiles(); pl = self._pattern_len()
        self._pattern = random.sample(range(n), pl); self._input_ok = 0
        self.round_lbl.setText(f"ROUND {self._round}"); self.round_c.set(str(self._round))
        sp = 1.0 + (self._round - 1) * 0.15
        self.speed_lbl.setText(f"SPEED ×{sp:.1f}")
        self.grid.setup(n, self._pattern)
        self.status_lbl.setText("Watch the pattern…")
        self._show_idx = 0; self._show_timer.start(400)

    def _show_next_step(self):
        if not self._running: return
        if self._show_idx < len(self._pattern):
            self.grid.play_show(self._pattern[self._show_idx])
            QTimer.singleShot(self._flash_ms(), self._after_flash)
        else:
            self.grid.hide_show(); self.grid.set_phase("input")
            self.status_lbl.setText(f"Repeat the pattern!  (0 / {len(self._pattern)})")

    def _after_flash(self):
        if not self._running: return
        self.grid.hide_show(); self._show_idx += 1; self._show_timer.start(self._gap_ms())

    def _on_tile_input(self, tile_idx, correct):
        if not self._running: return
        if correct:
            self._input_ok += 1
            self.status_lbl.setText(f"Repeat the pattern!  ({self._input_ok} / {len(self._pattern)})")
            if self._input_ok == len(self._pattern):
                self._score += 1; self.score_c.set(str(self._score))
                if self._score > G.memory_best:
                    G.memory_best = self._score; self.best_c.set(str(G.memory_best))
                G.memory += 1
                db = self.main_window.db; u = self.main_window.current_user
                if u: db.update_score(u, "memory", G.memory)
                self.grid.flash_result(True); self.status_lbl.setText("✓  Pattern matched!")
                self._feedback_timer.start(700)
        else:
            self.grid.flash_result(False); self.status_lbl.setText("✗  Wrong tile!  Game over.")
            self._feedback_timer.stop(); QTimer.singleShot(900, self._stop_game)

    def showEvent(self, e):
        u = self.main_window.current_user
        if u:
            ud = self.main_window.db.get_user(u)
            if ud: G.memory = ud.get('memory', 0)
        self.best_c.set(str(G.memory_best)); super().showEvent(e)