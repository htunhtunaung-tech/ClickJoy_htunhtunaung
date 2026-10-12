from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QFrame,
                               QLabel, QPushButton, QScrollArea, QSizePolicy,
                               QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QRectF, QEvent
from PySide6.QtGui import (QPainter, QPainterPath, QColor, QPen, QBrush,
                            QRadialGradient, QLinearGradient)

from theme_and_animation import (F, FM, NeonBackground, NEON, ACCENT,
                                  TEXT, DIM, GHOST, EDGE, PANEL, SURFACE, BG)
from game_data import GAME_LIST, ICONS, NAMES, ALL_DB_FIELDS
from base_game_page import G


class GameCard(QFrame):
    def __init__(self, field, name, icon, subtitle, on_click, parent=None):
        super().__init__(parent)
        self.field = field
        self.on_click = on_click
        self._selected = False
        neon, glow, *_ = NEON.get(field, ("#3b82f6","#0f2a5c","",""))
        self._neon = neon; self._glow = glow
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("GameCard")

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 10, 14, 10); row.setSpacing(14)

        self.icon_box = QLabel(icon)
        self.icon_box.setFixedSize(52, 52)
        self.icon_box.setAlignment(Qt.AlignCenter)
        self.icon_box.setFont(F(22))
        self.icon_box.setStyleSheet(f"""
            QLabel {{
                background: {glow};
                border: 2px solid {neon};
                border-radius: 12px;
                color: {neon};
            }}
        """)
        row.addWidget(self.icon_box)

        txt = QVBoxLayout(); txt.setSpacing(2)
        self.name_lbl = QLabel(name)
        self.name_lbl.setFont(F(13, 700))
        self.name_lbl.setStyleSheet("background:transparent;border:none;")
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setFont(F(9))
        self.sub_lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;")
        txt.addWidget(self.name_lbl); txt.addWidget(self.sub_lbl)
        row.addLayout(txt, stretch=1)

        self.chevron = QLabel("›")
        self.chevron.setFont(F(18, 700))
        self.chevron.setStyleSheet(f"color:{neon};background:transparent;border:none;")
        row.addWidget(self.chevron)

        self._set_style(False)

    def _set_style(self, active):
        neon, glow = self._neon, self._glow
        r = int(neon[1:3],16); g = int(neon[3:5],16); b = int(neon[5:7],16)
        neon_dim = f"rgba({r},{g},{b},160)"
        if active:
            self.setStyleSheet(f"#GameCard{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {glow},stop:1 {PANEL});border:2px solid {neon};border-radius:12px;}}")
            self.name_lbl.setStyleSheet(f"color:#ffffff;background:transparent;border:none;")
            self.sub_lbl.setStyleSheet(f"color:{neon_dim};background:transparent;border:none;")
            self.chevron.setStyleSheet(f"color:{neon};background:transparent;border:none;")
        else:
            self.setStyleSheet(f"#GameCard{{background:{PANEL};border:1px solid {EDGE};border-radius:12px;}}")
            self.name_lbl.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
            self.sub_lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;")
            self.chevron.setStyleSheet(f"color:{neon};background:transparent;border:none;")

    def set_selected(self, val):
        self._selected = val; self._set_style(val)

    def enterEvent(self, e): self._set_style(True)
    def leaveEvent(self, e): self._set_style(self._selected)
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self.on_click(self.field)

    def paintEvent(self, ev):
        super().paintEvent(ev)
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        nc = QColor(self._neon); r, g, b = nc.red(), nc.green(), nc.blue()
        w, h = self.width(), self.height()
        bar_w = 4; bar_r = 2
        bar_x = 0; bar_y = int(h * 0.15); bar_h = int(h * 0.70)
        glow = QRadialGradient(bar_w, h // 2, 80)
        glow.setColorAt(0.0, QColor(r, g, b, 55))
        glow.setColorAt(1.0, QColor(r, g, b, 0))
        pa.setBrush(QBrush(glow)); pa.setPen(Qt.NoPen)
        pa.drawRect(0, 0, 90, h)
        bar_path = QPainterPath()
        bar_path.addRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), bar_r, bar_r)
        pa.fillPath(bar_path, nc)
        pa.end()


class DetailPanel(QFrame):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._current_field = "normal"
        self.setMinimumWidth(200)
        self.setMaximumWidth(280)
        self.setObjectName("DetailPanel")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18,18,18,18); lay.setSpacing(10)

        self.icon_lbl = QLabel("⬡")
        self.icon_lbl.setFont(F(40))
        self.icon_lbl.setAlignment(Qt.AlignLeft)
        self.icon_lbl.setStyleSheet("background:transparent;border:none;")
        lay.addWidget(self.icon_lbl)

        self.name_lbl = QLabel("NORMAL CLICK")
        self.name_lbl.setFont(FM(13, bold=True))
        self.name_lbl.setWordWrap(True)
        self.name_lbl.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        lay.addWidget(self.name_lbl)

        self.sub_lbl = QLabel("tap as fast as you can")
        self.sub_lbl.setFont(F(8))
        self.sub_lbl.setWordWrap(True)
        self.sub_lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;")
        lay.addWidget(self.sub_lbl)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{EDGE};border:none;"); lay.addWidget(sep)

        score_row = QHBoxLayout()
        sk = QLabel("My Score"); sk.setFont(F(8))
        sk.setStyleSheet(f"color:{DIM};background:transparent;border:none;")
        self.score_val = QLabel("—")
        self.score_val.setFont(FM(12, bold=True))
        self.score_val.setAlignment(Qt.AlignRight)
        self.score_val.setStyleSheet(f"color:{GHOST};background:transparent;border:none;")
        score_row.addWidget(sk); score_row.addStretch(); score_row.addWidget(self.score_val)
        lay.addLayout(score_row)
        lay.addStretch()

        self.play_btn = QPushButton("▶   PLAY")
        self.play_btn.setFixedHeight(40)
        self.play_btn.setFont(FM(10, bold=True))
        self.play_btn.setCursor(Qt.PointingHandCursor)
        lay.addWidget(self.play_btn)
        self.update_game("normal","Normal Click","⬡","tap as fast as you can")

    def update_game(self, field, name, icon, subtitle):
        self._current_field = field
        neon, glow, *_ = NEON.get(field, ("#3b82f6","#0f2a5c","",""))
        self.setStyleSheet(f"#DetailPanel{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {glow},stop:0.6 {SURFACE},stop:1 {PANEL});border:1px solid {neon}55;border-radius:14px;}}")
        self.icon_lbl.setText(icon)
        self.icon_lbl.setStyleSheet(f"color:{neon};background:transparent;border:none;")
        self.name_lbl.setText(name.upper())
        self.name_lbl.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        self.sub_lbl.setText(subtitle)
        self.sub_lbl.setStyleSheet(f"color:{neon}99;background:transparent;border:none;")
        self.play_btn.setStyleSheet(f"""
            QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {glow},stop:1 {neon}44);
            border:1px solid {neon};border-radius:9px;color:{neon};letter-spacing:2px;}}
            QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {glow},stop:1 {neon}77);}}
            QPushButton:pressed{{background:{neon}33;}}
        """)
        try: self.play_btn.clicked.disconnect()
        except (RuntimeError, TypeError): pass
        self.play_btn.clicked.connect(self._play)
        self.refresh_score()

    def refresh_score(self):
        username = self.main_window.current_user
        if not username:
            self.score_val.setText("—"); return
        u = self.main_window.db.get_user(username)
        if u:
            val = u.get(self._current_field, 0)
            neon, *_ = NEON.get(self._current_field, ("#3b82f6","#0f2a5c","",""))
            self.score_val.setText(f"{val:,}")
            self.score_val.setStyleSheet(f"color:{neon};background:transparent;border:none;")

    def _play(self):
        username = self.main_window.current_user
        if not username: return
        self.main_window.go_game(self._current_field)


class MainMenuPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.bg = NeonBackground("normal", self)
        self.bg.setGeometry(0, 0, 920, 700)
        self.bg.lower()

        layout = QVBoxLayout(self); layout.setSpacing(0); layout.setContentsMargins(0, 0, 0, 0)

        mb = main_window.menuBar()
        mb.setStyleSheet(f"""
            QMenuBar {{
                background: {PANEL}; color: {TEXT};
                border-bottom: 1px solid {EDGE}; font-size: 10pt;
            }}
            QMenuBar::item {{ background: transparent; padding: 4px 12px; border-radius: 4px; }}
            QMenuBar::item:selected, QMenuBar::item:pressed {{ background: {GHOST}; color: {TEXT}; }}
            QMenu {{
                background: {PANEL}; color: {TEXT};
                border: 1px solid {EDGE}; border-radius: 8px; padding: 4px;
            }}
            QMenu::item {{ padding: 6px 24px 6px 16px; border-radius: 4px; }}
            QMenu::item:selected {{ background: {GHOST}; color: {TEXT}; }}
            QMenu::separator {{ background: {EDGE}; height: 1px; margin: 4px 8px; }}
        """)
        from PySide6.QtGui import QAction
        fm = mb.addMenu("&File")
        ea = QAction("&Exit", self); ea.setShortcut("Ctrl+Q"); ea.triggered.connect(main_window.close); fm.addAction(ea)
        pm = mb.addMenu("&Progress Menu")
        for lbl, sc, idx in [("&Ranking","Ctrl+R",2),("&Task","Ctrl+T",3),("R&eward","Ctrl+Shift+R",4)]:
            a = QAction(lbl, self); a.setShortcut(sc); a.setShortcutContext(Qt.ApplicationShortcut)
            a.triggered.connect(lambda _, i=idx: main_window.go_to(i)); pm.addAction(a)

        from PySide6.QtCore import QObject
        class _HoverMenuBar(QObject):
            def __init__(self, menubar):
                super().__init__(menubar); self._mb = menubar
                self._active = False; self._mb.installEventFilter(self)
            def eventFilter(self, obj, event):
                if obj is self._mb:
                    if event.type() == QEvent.MouseButtonPress: self._active = True
                    elif event.type() == QEvent.HoverMove and self._active:
                        action = self._mb.actionAt(event.position().toPoint())
                        if action: self._mb.setActiveAction(action)
                    elif event.type() == QEvent.Leave: self._active = False
                return False
        self._hover_mb = _HoverMenuBar(mb)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(20, 14, 20, 20); inner_lay.setSpacing(0)
        scroll.setWidget(inner); layout.addWidget(scroll)

        top = QHBoxLayout(); top.setSpacing(10); top.setContentsMargins(0, 0, 0, 14)
        hb = QPushButton("☰"); hb.setFixedSize(38, 38)
        hb.setStyleSheet(f"QPushButton{{background:{PANEL};color:{TEXT};border:1px solid {EDGE};border-radius:10px;font-size:13pt;}}QPushButton:hover{{background:{EDGE};}}")
        hb.clicked.connect(main_window.toggle_hamburger); top.addWidget(hb)

        brand_col = QVBoxLayout(); brand_col.setSpacing(0)
        brand = QLabel("CLICKJOY ✦"); brand.setFont(F(22, 900))
        brand.setStyleSheet(f"color:{TEXT};background:transparent;letter-spacing:4px;")
        self._brand_glow = QGraphicsDropShadowEffect(); self._brand_glow.setBlurRadius(18)
        self._brand_glow.setColor(QColor(ACCENT)); self._brand_glow.setOffset(0, 0)
        brand.setGraphicsEffect(self._brand_glow)
        self._tagline = QLabel("▸  beat your record")
        self._tagline.setFont(F(9, 500))
        self._tagline.setStyleSheet(f"color:{ACCENT};background:transparent;letter-spacing:2px;")
        brand_col.addWidget(brand); brand_col.addWidget(self._tagline)
        top.addLayout(brand_col, 1)

        self.user_lbl = QLabel("👤 Guest"); self.user_lbl.setFont(F(9))
        self.user_lbl.setStyleSheet(f"color:{DIM};background:transparent;"); top.addWidget(self.user_lbl)
        inner_lay.addLayout(top)

        banner = QWidget(); banner.setFixedHeight(80)
        banner.setAttribute(Qt.WA_TranslucentBackground)
        bl = QHBoxLayout(banner); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(10)
        self.total_chip = self._stat_chip("TOTAL CLICKS", "0", ACCENT)
        self.cps_chip   = self._stat_chip("BEST CPS",     "—", NEON["cpm"][0])
        self.streak_chip = self._stat_chip("FLIP STREAK", "0", NEON["flip"][0])
        bl.addWidget(self.total_chip); bl.addWidget(self.cps_chip); bl.addWidget(self.streak_chip)
        inner_lay.addWidget(banner); inner_lay.addSpacing(12)

        sec = QLabel("SELECT GAME"); sec.setFont(FM(9, bold=True))
        sec.setStyleSheet(f"color:{DIM};background:transparent;letter-spacing:3px;padding-bottom:6px;")
        inner_lay.addWidget(sec)

        body = QHBoxLayout(); body.setSpacing(14); body.setContentsMargins(0, 0, 0, 0)

        list_scroll = QScrollArea(); list_scroll.setWidgetResizable(True)
        list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        list_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        list_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        list_scroll.setMinimumHeight(200)
        list_w = QWidget(); list_w.setStyleSheet("background:transparent;")
        list_lay = QVBoxLayout(list_w)
        list_lay.setSpacing(4); list_lay.setContentsMargins(0, 0, 2, 4)
        list_lay.setAlignment(Qt.AlignTop)
        self._cards = {}
        for field, name, icon, subtitle in GAME_LIST:
            card = GameCard(field, name, icon, subtitle, self._on_card_click)
            list_lay.addWidget(card); self._cards[field] = card
        list_scroll.setWidget(list_w)
        body.addWidget(list_scroll, stretch=3)

        self.detail = DetailPanel(main_window)
        self.detail.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        body.addWidget(self.detail, stretch=1)

        inner_lay.addLayout(body, stretch=1)

        inner_lay.addSpacing(8)
        fsep = QFrame(); fsep.setFixedHeight(1); fsep.setStyleSheet(f"background:{EDGE};")
        inner_lay.addWidget(fsep)
        fl = QLabel("CLICKJOY  ·  REACTION TRAINING SUITE  ·  v2.4.1")
        fl.setFont(FM(7)); fl.setAlignment(Qt.AlignCenter)
        fl.setStyleSheet(f"color:{GHOST};padding-top:6px;background:transparent;")
        inner_lay.addWidget(fl)

    def _update_accent(self, hex_color):
        self._tagline.setStyleSheet(f"color:{hex_color};background:transparent;letter-spacing:2px;")
        self._brand_glow.setColor(QColor(hex_color))
        self.total_chip._neon = hex_color
        self.total_chip._val_lbl.setStyleSheet(f"color:{hex_color};background:transparent;")
        eff = self.total_chip._val_lbl.graphicsEffect()
        if eff: eff.setColor(QColor(hex_color))
        self.total_chip.update()

    def _stat_chip(self, label, value, neon):
        w = QWidget(); w.setAttribute(Qt.WA_TranslucentBackground)
        w._neon = neon
        lay = QVBoxLayout(w); lay.setContentsMargins(16, 10, 16, 10); lay.setSpacing(2)
        cap = QLabel(label); cap.setFont(F(8, 500))
        cap.setStyleSheet(f"color:{DIM};background:transparent;letter-spacing:2px;")
        val = QLabel(value); val.setFont(FM(20, True))
        val.setStyleSheet(f"color:{neon};background:transparent;")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(20)
        eff.setColor(QColor(neon)); eff.setOffset(0, 0); val.setGraphicsEffect(eff)
        lay.addWidget(cap); lay.addWidget(val)
        w._val_lbl = val
        def paint(ev, widget=w):
            pa = QPainter(widget); pa.setRenderHint(QPainter.Antialiasing)
            nc = QColor(widget._neon); ww, wh = widget.width(), widget.height()
            path = QPainterPath()
            path.addRoundedRect(QRectF(0.5, 0.5, ww - 1, wh - 1), 12, 12)
            pa.fillPath(path, QColor(18, 21, 32, 220))
            pa.strokePath(path, QPen(QColor(nc.red(), nc.green(), nc.blue(), 80), 1))
            hi = QLinearGradient(0, 0, 0, 20)
            hi.setColorAt(0, QColor(nc.red(), nc.green(), nc.blue(), 25))
            hi.setColorAt(1, QColor(nc.red(), nc.green(), nc.blue(), 0))
            pa.fillPath(path, QBrush(hi)); pa.end()
        w.paintEvent = paint
        return w

    def _on_card_click(self, field):
        for fid, card in self._cards.items():
            card._target = 1.0 if fid == field else 0.0
            card._hover  = 1.0 if fid == field else 0.0
            card.update()
        for gf, name, icon, sub in GAME_LIST:
            if gf == field:
                self.detail.update_game(field, name, icon, sub)
                break

    def update_user_label(self):
        u = self.main_window.current_user
        self.user_lbl.setText(f"👤 {u or 'Guest'}")
        self._refresh_chips()
        self.detail.refresh_score()

    def _refresh_chips(self):
        u = self.main_window.current_user
        if u:
            ud = self.main_window.db.get_user(u)
            if ud:
                total = sum(ud.get(f, 0) for f in ALL_DB_FIELDS)
                self.total_chip._val_lbl.setText(f"{total:,}")
                streak = max(G.flip_best_h, G.flip_best_t)
                self.streak_chip._val_lbl.setText(str(streak) if streak > 0 else "0")
        cps = G.cpm_cps
        self.cps_chip._val_lbl.setText(f"{cps:.2f}" if cps > 0 else "—")
        self.total_chip.update()
        self.cps_chip.update()
        self.streak_chip.update()

    def resizeEvent(self, e):
        self.bg.setGeometry(0, 0, self.width(), self.height())
        # Hide detail panel on narrow windows (< 600px), show on wider ones
        if hasattr(self, 'detail'):
            self.detail.setVisible(self.width() >= 600)
        super().resizeEvent(e)

    def showEvent(self, e):
        self._refresh_chips()
        self.detail.refresh_score()
        self.main_window.task_page.refresh()
        super().showEvent(e)

    def refresh_theme(self):
        mb = self.main_window.menuBar()
        mb.setStyleSheet(f"""
            QMenuBar {{
                background: {PANEL}; color: {TEXT};
                border-bottom: 1px solid {EDGE}; font-size: 10pt;
            }}
            QMenuBar::item {{ background: transparent; padding: 4px 12px; border-radius: 4px; }}
            QMenuBar::item:selected, QMenuBar::item:pressed {{ background: {GHOST}; color: {TEXT}; }}
            QMenu {{
                background: {PANEL}; color: {TEXT};
                border: 1px solid {EDGE}; border-radius: 8px; padding: 4px;
            }}
            QMenu::item {{ padding: 6px 24px 6px 16px; border-radius: 4px; }}
            QMenu::item:selected {{ background: {GHOST}; color: {TEXT}; }}
            QMenu::separator {{ background: {EDGE}; height: 1px; margin: 4px 8px; }}
        """)
        self.user_lbl.setStyleSheet(f"color:{DIM};background:transparent;")
        for field, card in self._cards.items():
            card._neon, card._glow = NEON.get(field, ("#3b82f6", "#0f2a5c", "", ""))[:2]
            card._set_style(card._selected)
        field = self.detail._current_field
        for gf, name, icon, sub in GAME_LIST:
            if gf == field:
                self.detail.update_game(field, name, icon, sub)
                break
        self.update()