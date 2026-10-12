from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QPushButton
from PySide6.QtCore import Qt
from theme_and_animation import (F, FM, NeonBackground, PageHeader, NEON,
    GHOST, EDGE, DIM, TEXT)

# ══════════════════════════════════════════════════════════════
#  GLOBAL SESSION STATE
# ══════════════════════════════════════════════════════════════
class _G:
    """In-memory session state — synced to DB on each action."""
    normal = 0
    flip = 0; flip_streak = 0; flip_side = None; flip_best_h = 0; flip_best_t = 0
    switch = 0; switch_on = False
    swap = 0
    cpm = 0; cpm_cps = 0.0
    stop = 0; stop_best = float("inf")
    pop = 0
    focus = 0; focus_best = 0
    chaos = 0; chaos_best = 0
    memory = 0; memory_best = 0
    dopa = 0; dopa_best = 0
    rcs = 0; rcs_best = 0

G = _G()


# ══════════════════════════════════════════════════════════════
#  BASE PAGE  (shared scaffold for all game pages)
# ══════════════════════════════════════════════════════════════
class BasePage(QWidget):
    KEY = ""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        neon, glow, accent, bg_tint = NEON.get(self.KEY, ("#3b82f6","#0f2a5c","#60a5fa","#060c1a"))
        self.neon = neon; self.glow = glow; self.accent = accent

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.bg = NeonBackground(self.KEY, self)
        self.bg.setGeometry(0, 0, 920, 700)
        self.bg.lower()

        class _Nav:
            def __init__(s, mw): s._mw = mw
            def go(s, _): s._mw.go_to(1)
        self.header = PageHeader(self.KEY, _Nav(main_window), self)
        outer.addWidget(self.header)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        self.root = QVBoxLayout(inner)
        self.root.setContentsMargins(24, 20, 24, 24)
        self.root.setSpacing(10)
        self.root.setAlignment(Qt.AlignTop)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

        self._build_content()

    def _build_content(self):
        pass

    def _ghost_btn(self, text):
        btn = QPushButton(text); btn.setFont(F(11, 500))
        btn.setFixedHeight(34); btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {GHOST}; color: {DIM};
                border: 1px solid {EDGE}; border-radius: 8px; padding: 0 16px;
            }}
            QPushButton:hover {{ background: {EDGE}; color: {TEXT}; }}
        """)
        return btn

    def resizeEvent(self, e):
        self.bg.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(e)