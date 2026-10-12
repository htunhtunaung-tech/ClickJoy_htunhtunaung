from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QFrame,
                               QLabel, QPushButton, QScrollArea, QLineEdit)
from PySide6.QtCore import Qt

from theme_and_animation import (F, FM, NEON, TEXT, DIM, GHOST, EDGE, PANEL, SURFACE)
from game_data import GAME_LIST


class HamburgerMenuPage(QWidget):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.main_window = main_window
        self.setFixedWidth(280)
        self.setStyleSheet(f"""
            HamburgerMenuPage {{ background-color:{SURFACE}; border-right:1px solid {EDGE}; }}
            HamburgerMenuPage QWidget {{ background-color:{SURFACE}; }}
            HamburgerMenuPage QLineEdit {{
                background:{PANEL}; color:{TEXT};
                border:1px solid {EDGE}; border-radius:8px; padding:0 10px;
            }}
        """)

        lay = QVBoxLayout(self); lay.setSpacing(6); lay.setContentsMargins(12,12,12,12)

        self._close_btn = QPushButton("☰  Close"); self._close_btn.setFixedHeight(34)
        self._close_btn.setStyleSheet(f"QPushButton{{background:{GHOST};color:{DIM};border:1px solid {EDGE};border-radius:8px;font-size: 10pt;text-align:left;padding-left:10px;}}QPushButton:hover{{background:{EDGE};color:{TEXT};}}")
        self._close_btn.clicked.connect(main_window.toggle_hamburger); lay.addWidget(self._close_btn)

        self._search = QLineEdit(); self._search.setPlaceholderText("🔍  Search pages & games…")
        self._search.setFixedHeight(34); lay.addWidget(self._search)
        self._search.textChanged.connect(self._on_search)

        pr = QHBoxLayout(); il = QLabel("👤"); il.setFont(F(16))
        il.setStyleSheet("background:transparent;border:none;")
        self.name_btn = QPushButton("Guest"); self.name_btn.setFlat(True)
        self.name_btn.setFont(F(11, 700))
        self.name_btn.setStyleSheet(f"color:{TEXT};background:transparent;border:none;text-align:left;")
        self.name_btn.clicked.connect(lambda: (main_window.toggle_hamburger(), main_window.go_to(6)))
        pr.addWidget(il); pr.addWidget(self.name_btn); pr.addStretch(); lay.addLayout(pr)

        self._sep_widgets = []
        def _sep():
            ln = QFrame(); ln.setFrameShape(QFrame.HLine)
            ln.setStyleSheet(f"background:{EDGE};max-height:1px;border:none;")
            self._sep_widgets.append(ln); return ln

        lay.addWidget(_sep())

        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(f"QScrollArea{{border:none;background:{SURFACE};}}QScrollBar:vertical{{background:{SURFACE};width:4px;border-radius:2px;}}QScrollBar::handle:vertical{{background:{EDGE};border-radius:2px;min-height:20px;}}QScrollBar::handle:vertical:hover{{background:#3b82f6;}}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        self._scroll_content = QWidget(); self._scroll_content.setStyleSheet(f"background:{SURFACE};")
        self._content_lay = QVBoxLayout(self._scroll_content); self._content_lay.setSpacing(2)
        self._content_lay.setContentsMargins(0,0,0,0); self._content_lay.setAlignment(Qt.AlignTop)
        self._scroll.setWidget(self._scroll_content); lay.addWidget(self._scroll, 1)

        self._pages_lbl = self._section_label("PAGES")
        self._content_lay.addWidget(self._pages_lbl)

        self._page_btns = []
        self._page_btn_colors = []
        for label, idx, color, icon in [
            ("Ranking",  2, "#f59e0b", "🏆"),
            ("Task",     3, "#10b981", "📋"),
            ("Reward",   4, "#ec4899", "⭐"),
            ("Setting",  5, "#8b5cf6", "⚙️"),
            ("Profile",  6, "#06b6d4", "👤"),
        ]:
            btn = self._nav_btn(f"{icon}  {label}", color)
            btn.clicked.connect(lambda _, i=idx: (main_window.toggle_hamburger(), main_window.go_to(i)))
            self._content_lay.addWidget(btn)
            self._page_btns.append((label.lower(), btn))
            self._page_btn_colors.append(color)

        self._content_lay.addSpacing(4)
        self._content_lay.addWidget(_sep())
        self._content_lay.addSpacing(4)

        self._games_lbl = self._section_label("GAMES")
        self._content_lay.addWidget(self._games_lbl)

        self._game_btns = []
        self._game_btn_colors = []
        for key, name, icon, _ in GAME_LIST:
            neon = NEON[key][0]
            btn = self._nav_btn(f"{icon}  {name}", neon)
            btn.clicked.connect(lambda _, k=key: (main_window.toggle_hamburger(), main_window.go_game(k)))
            self._content_lay.addWidget(btn)
            self._game_btns.append((name.lower(), btn))
            self._game_btn_colors.append(key)

        self._content_lay.addSpacing(4)
        self._content_lay.addWidget(_sep())
        self._content_lay.addSpacing(2)

        self._logout_btn = QPushButton("🚪  Logout"); self._logout_btn.setFixedHeight(38)
        self._logout_btn.setStyleSheet(f"QPushButton{{background:transparent;color:#f87171;border:none;border-radius:8px;text-align:left;padding-left:10px;font-size: 9pt;}}QPushButton:hover{{background:{GHOST};}}")
        self._logout_btn.clicked.connect(self._logout)
        self._content_lay.addWidget(self._logout_btn)

    def _section_label(self, text):
        lbl = QLabel(text); lbl.setFont(FM(8, bold=True))
        lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;padding:4px 4px 2px 4px;letter-spacing:2px;")
        return lbl

    def _nav_btn(self, label, color):
        btn = QPushButton(label); btn.setFixedHeight(36)
        btn.setStyleSheet(f"QPushButton{{background:transparent;color:{DIM};border:none;border-radius:8px;text-align:left;padding-left:12px;font-size: 9pt;}}QPushButton:hover{{background:{GHOST};color:{color};}}")
        return btn

    def _on_search(self, text):
        q = text.strip().lower()
        any_page = False
        for name, btn in self._page_btns:
            vis = (q == "") or (q in name)
            btn.setVisible(vis)
            if vis: any_page = True
        self._pages_lbl.setVisible(any_page)
        any_game = False
        for name, btn in self._game_btns:
            vis = (q == "") or (q in name)
            btn.setVisible(vis)
            if vis: any_game = True
        self._games_lbl.setVisible(any_game)
        self._logout_btn.setVisible(q == "")

    def update_user_label(self): self.name_btn.setText(self.main_window.current_user or "Guest")
    def _logout(self):
        self.main_window.current_user = None
        self.main_window.toggle_hamburger()
        self.main_window._tb.setVisible(False)
        self.main_window.menuBar().setVisible(False)
        self.main_window.go_to(0)

    def refresh_theme(self):
        self.setStyleSheet(f"""
            HamburgerMenuPage {{ background-color:{SURFACE}; border-right:1px solid {EDGE}; }}
            HamburgerMenuPage QWidget {{ background-color:{SURFACE}; }}
            HamburgerMenuPage QLineEdit {{
                background:{PANEL}; color:{TEXT};
                border:1px solid {EDGE}; border-radius:8px; padding:0 10px;
            }}
        """)
        self._close_btn.setStyleSheet(f"QPushButton{{background:{GHOST};color:{DIM};border:1px solid {EDGE};border-radius:8px;font-size: 10pt;text-align:left;padding-left:10px;}}QPushButton:hover{{background:{EDGE};color:{TEXT};}}")
        self.name_btn.setStyleSheet(f"color:{TEXT};background:transparent;border:none;text-align:left;")
        self._scroll.setStyleSheet(f"QScrollArea{{border:none;background:{SURFACE};}}QScrollBar:vertical{{background:{SURFACE};width:4px;border-radius:2px;}}QScrollBar::handle:vertical{{background:{EDGE};border-radius:2px;min-height:20px;}}QScrollBar::handle:vertical:hover{{background:#3b82f6;}}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        self._scroll_content.setStyleSheet(f"background:{SURFACE};")
        for ln in self._sep_widgets:
            ln.setStyleSheet(f"background:{EDGE};max-height:1px;border:none;")
        self._logout_btn.setStyleSheet(f"QPushButton{{background:transparent;color:#f87171;border:none;border-radius:8px;text-align:left;padding-left:10px;font-size: 9pt;}}QPushButton:hover{{background:{GHOST};}}")
        self._pages_lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;padding:4px 4px 2px 4px;letter-spacing:2px;")
        self._games_lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;padding:4px 4px 2px 4px;letter-spacing:2px;")
        for i, (_, btn) in enumerate(self._page_btns):
            color = self._page_btn_colors[i]
            btn.setStyleSheet(f"QPushButton{{background:transparent;color:{DIM};border:none;border-radius:8px;text-align:left;padding-left:12px;font-size: 9pt;}}QPushButton:hover{{background:{GHOST};color:{color};}}")
        for i, (_, btn) in enumerate(self._game_btns):
            key = self._game_btn_colors[i]
            color = NEON[key][0]
            btn.setStyleSheet(f"QPushButton{{background:transparent;color:{DIM};border:none;border-radius:8px;text-align:left;padding-left:12px;font-size: 9pt;}}QPushButton:hover{{background:{GHOST};color:{color};}}")
        self.update()
