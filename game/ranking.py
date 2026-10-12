import os

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QFrame,
                               QLabel, QPushButton, QScrollArea, QLineEdit,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QDialog)
from PySide6.QtCore import Qt, QRectF, QPointF, QRect
from PySide6.QtGui import (QPainter, QPainterPath, QColor, QPen, QAction)

from theme_and_animation import (F, FM, _make_back_btn, _StatsBarChart,
                                  NEON, TEXT, DIM, GHOST, EDGE, PANEL, SURFACE, BG)


class _PlayerProfileDialog(QDialog):
    def __init__(self, u, current_user, parent=None):
        super().__init__(parent)
        is_me = u["user"] == current_user
        title = "My Profile" if is_me else f"{u['user']}'s Profile"
        self.setWindowTitle(title)
        self.setMinimumWidth(420); self.setMinimumHeight(500)
        self.setStyleSheet(f"""
            QDialog {{ background:{SURFACE}; }}
            QLabel {{ background:transparent; color:{TEXT}; border:none; }}
        """)
        lay = QVBoxLayout(self); lay.setContentsMargins(24,24,24,24); lay.setSpacing(14)

        hrow = QHBoxLayout(); hrow.setSpacing(16)

        avatar_path = u.get("avatar", "")
        class _Av(QWidget):
            def __init__(self, name, is_me, av_path):
                super().__init__(); self.setFixedSize(72,72)
                self._name = name; self._is_me = is_me
                self._pm = None
                if av_path and os.path.exists(av_path):
                    from PySide6.QtGui import QPixmap
                    pm = QPixmap(av_path)
                    if not pm.isNull():
                        self._pm = pm.scaled(72, 72, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            def paintEvent(self, ev):
                pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
                nc = QColor(NEON["normal"][0]) if self._is_me else QColor("#5a637a")
                clip = QPainterPath(); clip.addEllipse(QPointF(36,36), 34.0, 34.0)
                pa.setClipPath(clip)
                if self._pm:
                    pa.drawPixmap(0, 0, self._pm)
                else:
                    pa.fillPath(clip, QColor(PANEL))
                    pa.setFont(F(22, 700)); pa.setPen(nc)
                    pa.drawText(QRect(0,0,72,72), Qt.AlignCenter, self._name[0].upper() if self._name else "?")
                pa.setClipping(False)
                pa.setPen(QPen(nc, 2.5)); pa.setBrush(Qt.NoBrush)
                pa.drawEllipse(QPointF(36,36), 34.0, 34.0)
                pa.end()
        av_w = _Av(u["user"], is_me, avatar_path); hrow.addWidget(av_w, 0, Qt.AlignVCenter)

        name_col = QVBoxLayout(); name_col.setSpacing(4)
        name_lbl = QLabel(u["user"]); name_lbl.setFont(F(18, 700))
        me_badge = QLabel("  YOU  ") if is_me else None
        if me_badge:
            me_badge.setFont(FM(8, bold=True))
            nc_str = NEON["normal"][0]
            me_badge.setStyleSheet(f"color:{nc_str};background:transparent;border:1px solid {nc_str};border-radius:4px;padding:1px 4px;")
            me_badge.setMaximumWidth(50)
        uid_lbl = QLabel(f"UID: {u['uid']}"); uid_lbl.setFont(FM(9))
        uid_lbl.setStyleSheet(f"color:{DIM};")
        name_col.addWidget(name_lbl)
        if me_badge: name_col.addWidget(me_badge)
        name_col.addWidget(uid_lbl)
        hrow.addLayout(name_col, 1)
        lay.addLayout(hrow)

        bio = u.get("bio", "")
        if bio:
            bio_lbl = QLabel(f'"{bio}"'); bio_lbl.setFont(F(10))
            bio_lbl.setWordWrap(True)
            bio_lbl.setStyleSheet(f"color:{DIM};background:{PANEL};border:1px solid {EDGE};border-radius:8px;padding:6px 10px;")
            lay.addWidget(bio_lbl)

        rewards = u.get("reward", [])
        rew_row = QHBoxLayout(); rew_row.setSpacing(6)
        rew_title = QLabel("⭐  Rewards:"); rew_title.setFont(F(10, 700))
        rew_title.setStyleSheet(f"color:{TEXT};")
        rew_val = QLabel("  ".join(rewards) if rewards else "None")
        rew_val.setFont(F(10))
        rew_val.setStyleSheet(f"color:{'#fbbf24' if rewards else DIM};")
        rew_row.addWidget(rew_title); rew_row.addWidget(rew_val); rew_row.addStretch()
        lay.addLayout(rew_row)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:{EDGE};max-height:1px;border:none;"); lay.addWidget(sep)

        chart_lbl = QLabel("Game Activity"); chart_lbl.setFont(F(11, 700))
        lay.addWidget(chart_lbl)
        chart = _StatsBarChart()
        chart.set_data([
            ("Normal",    u.get("normal",0),  "#3b82f6"),
            ("Flip",      u.get("flip",0),    "#f59e0b"),
            ("Switch",    u.get("switch",0),  "#10b981"),
            ("Swap",      u.get("swap",0),    "#ec4899"),
            ("CpTime",    u.get("cpm",0),     "#8b5cf6"),
            ("Stopwatch", u.get("stop",0),    "#06b6d4"),
            ("Pop It",    u.get("pop",0),     "#f97316"),
            ("Focus",     u.get("focus",0),   "#e879f9"),
            ("Chaos",     u.get("chaos",0),   "#ff4d4d"),
            ("Memory",    u.get("memory",0),  "#00e5ff"),
            ("Dopamine",  u.get("dopa",0),    "#39ff14"),
            ("ColorShift",u.get("rcs",0),     "#a3e635"),
        ])
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        scroll.setWidget(chart); lay.addWidget(scroll, 1)

        close_btn = QPushButton("Close"); close_btn.setFixedHeight(36)
        close_btn.setStyleSheet(f"QPushButton{{background:{GHOST};color:{DIM};border:1px solid {EDGE};border-radius:10px;font-size: 9pt;}}QPushButton:hover{{background:{EDGE};color:{TEXT};}}")
        close_btn.clicked.connect(self.accept); lay.addWidget(close_btn)


class RankingPage(QWidget):
    STYLES = [
        ("🖱️ Total","total","#858585"),("🖱️ Normal","normal","#3b82f6"),
        ("🪙 Flip","flip","#f59e0b"),("🔘 Switch","switch","#10b981"),
        ("🟣 Pop It","pop","#f97316"),("🔄 Swap","swap","#ec4899"),
        ("⏱️ CPM","cpm","#8b5cf6"),("⏲️ Stop","stop","#06b6d4"),
        ("◈ Focus","focus","#e879f9"),("⚡ Chaos","chaos","#ff4d4d"),
        ("◫ Memory","memory","#00e5ff"),("◑ Dopamine","dopa","#39ff14"),
        ("◐ Color Shift","rcs","#a3e635"),
    ]
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._cur_field="total"; self._cur_display="Total Click"; self._cur_color="#858585"
        self._btns = {}
        layout = QVBoxLayout(self); layout.setContentsMargins(8,8,8,8); layout.setSpacing(10)
        _hrow = QHBoxLayout(); _hrow.setSpacing(10); _hrow.setContentsMargins(0,0,0,0)
        _hrow.addWidget(_make_back_btn(lambda: main_window.go_to(1)), 0, Qt.AlignVCenter)
        self._htitle = QLabel("🏆 Ranking Page"); self._htitle.setFont(F(16, 700))
        self._htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        _hrow.addWidget(self._htitle, 1, Qt.AlignVCenter)
        layout.addLayout(_hrow)
        self.csl = QLabel("Total Click"); self.csl.setFont(F(13, 700))
        self.csl.setAlignment(Qt.AlignCenter)
        self.csl.setStyleSheet(f"color:{TEXT};background:{PANEL};border:1px solid {EDGE};border-radius:8px;padding:4px;")
        layout.addWidget(self.csl)
        self._bs = QScrollArea(); self._bs.setFixedHeight(44)
        self._bs.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._bs.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._bs.setWidgetResizable(False)
        self._bs.setStyleSheet(f"QScrollArea{{background:{BG};border:none;}}")
        # wheel → horizontal scroll
        def _bs_wheel(e):
            delta = e.angleDelta().y() or e.angleDelta().x()
            self._bs.horizontalScrollBar().setValue(
                self._bs.horizontalScrollBar().value() - delta // 2)
        self._bs.wheelEvent = _bs_wheel
        self._bw = QWidget(); self._bw.setStyleSheet(f"background:{BG};")
        br = QHBoxLayout(self._bw); br.setContentsMargins(0,0,0,0); br.setSpacing(6)
        for label, field, color in self.STYLES:
            btn = QPushButton(label); btn.setCheckable(True); btn.setFixedHeight(32); btn.setFixedWidth(110)
            btn.setStyleSheet(f"QPushButton{{background:{PANEL};color:{DIM};border:1px solid {EDGE};border-radius:8px;font-size: 8pt;font-weight:bold;}}QPushButton:checked{{background:{color}22;color:{color};border:1px solid {color};}}QPushButton:hover{{background:{color}15;color:{color};border:1px solid {color};}}")
            btn.clicked.connect(lambda _, f=field, d=label, c=color: self.load_ranking(f,d,c))
            br.addWidget(btn); self._btns[field] = (btn, color)
        n = len(self.STYLES); self._bw.setFixedWidth(n*110+(n-1)*6+4); self._bs.setWidget(self._bw); layout.addWidget(self._bs)

        search_row = QHBoxLayout(); search_row.setSpacing(8)
        search_icon = QLabel("🔍"); search_icon.setStyleSheet("background:transparent;border:none;")
        self._player_search = QLineEdit(); self._player_search.setPlaceholderText("Filter player…")
        self._player_search.setFixedHeight(32)
        self._player_search.setStyleSheet(f"QLineEdit{{background:{PANEL};color:{TEXT};border:1px solid {EDGE};border-radius:8px;padding:0 10px;font-size: 9pt;}}QLineEdit:focus{{border-color:#3b82f6;}}")
        self._player_search.textChanged.connect(self._filter_rows)
        search_row.addWidget(search_icon); search_row.addWidget(self._player_search)
        layout.addLayout(search_row)

        self.rt = QTableWidget(); self.rt.setColumnCount(3)
        self.rt.setHorizontalHeaderLabels(["Rank","Player","Score"])
        hdr = self.rt.horizontalHeader()
        hdr.setSectionResizeMode(0,QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1,QHeaderView.Stretch)
        hdr.setSectionResizeMode(2,QHeaderView.Stretch)
        self.rt.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rt.setSelectionBehavior(QTableWidget.SelectRows)
        self.rt.verticalHeader().setVisible(False); self.rt.setShowGrid(False)
        self.rt.setCursor(Qt.PointingHandCursor)
        self.rt.itemDoubleClicked.connect(self._on_row_double_click)
        self.rt.setContextMenuPolicy(Qt.CustomContextMenu)
        self.rt.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.rt)

        hint = QLabel("  Double-click a player to view their profile")
        hint.setFont(F(9)); hint.setStyleSheet(f"color:{DIM};background:transparent;border:none;")
        layout.addWidget(hint)

    def refresh(self): self.load_ranking(self._cur_field, self._cur_display, self._cur_color)

    def refresh_theme(self):
        self._htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        self.csl.setStyleSheet(f"color:{self._cur_color};background:{PANEL};border:1px solid {EDGE};border-radius:8px;padding:4px;")
        self._bs.setStyleSheet(f"QScrollArea{{background:{BG};border:none;}}")
        self._bw.setStyleSheet(f"background:{BG};")
        self._player_search.setStyleSheet(f"QLineEdit{{background:{PANEL};color:{TEXT};border:1px solid {EDGE};border-radius:8px;padding:0 10px;font-size: 9pt;}}QLineEdit:focus{{border-color:#3b82f6;}}")
        for field, (btn, color) in self._btns.items():
            btn.setStyleSheet(f"QPushButton{{background:{PANEL};color:{DIM};border:1px solid {EDGE};border-radius:8px;font-size: 8pt;font-weight:bold;}}QPushButton:checked{{background:{color}22;color:{color};border:1px solid {color};}}QPushButton:hover{{background:{color}15;color:{color};border:1px solid {color};}}")
        self.load_ranking(self._cur_field, self._cur_display, self._cur_color)

    def _filter_rows(self, text):
        q = text.strip().lower()
        for row in range(self.rt.rowCount()):
            item = self.rt.item(row, 1)
            self.rt.setRowHidden(row, bool(q and item and q not in item.text().lower()))

    def _on_row_double_click(self, item):
        row = item.row()
        username = self.rt.item(row, 1).text() if self.rt.item(row, 1) else None
        if not username: return
        u = self.main_window.db.get_user(username)
        if not u: return
        dlg = _PlayerProfileDialog(u, self.main_window.current_user, self)
        dlg.exec()

    def _show_context_menu(self, pos):
        from PySide6.QtWidgets import QMenu
        item = self.rt.itemAt(pos)
        if not item: return
        row = item.row()
        username_item = self.rt.item(row, 1)
        if not username_item: return
        username = username_item.text()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background:{PANEL}; color:{TEXT}; border:1px solid {EDGE}; border-radius:8px; padding:4px; }}
            QMenu::item {{ padding:6px 20px; border-radius:6px; }}
            QMenu::item:selected {{ background:{GHOST}; color:{TEXT}; }}
            QMenu::separator {{ background:{EDGE}; height:1px; margin:4px 8px; }}
        """)
        view_act = QAction(f"👤  View {username}'s Profile", self)
        view_act.triggered.connect(lambda: self._open_profile(username))
        menu.addAction(view_act)
        if username == self.main_window.current_user:
            menu.addSeparator()
            go_act = QAction("🔗  Go to My Profile Page", self)
            go_act.triggered.connect(lambda: self.main_window.go_to(6))
            menu.addAction(go_act)
        menu.exec(self.rt.viewport().mapToGlobal(pos))

    def _open_profile(self, username):
        u = self.main_window.db.get_user(username)
        if u:
            dlg = _PlayerProfileDialog(u, self.main_window.current_user, self)
            dlg.exec()

    def load_ranking(self, field, display_name, color="#e8ecff"):
        self._cur_field=field; self._cur_display=display_name; self._cur_color=color
        self._player_search.blockSignals(True); self._player_search.clear(); self._player_search.blockSignals(False)
        self.csl.setText(display_name)
        self.csl.setStyleSheet(f"color:{color};background:{PANEL};border:1px solid {EDGE};border-radius:8px;padding:4px;")
        for f,(btn,c) in self._btns.items(): btn.setChecked(f==field)
        data = self.main_window.db.get_all_scores(field)
        self.rt.setRowCount(len(data))
        medal={0:"🥇",1:"🥈",2:"🥉"}
        def _medal_bg(rank, color):
            nc = QColor(color); s = QColor(SURFACE)
            mix = 0.18 if rank == 0 else (0.10 if rank == 1 else 0.06)
            return QColor(
                int(s.red()   * (1-mix) + nc.red()   * mix),
                int(s.green() * (1-mix) + nc.green() * mix),
                int(s.blue()  * (1-mix) + nc.blue()  * mix),
            )
        for row,(username,score) in enumerate(data):
            ri=QTableWidgetItem(medal.get(row,str(row+1))); pi=QTableWidgetItem(username); si=QTableWidgetItem(f"{score:,}")
            bg=_medal_bg(row, color) if row in medal else QColor(PANEL); is_me=username==self.main_window.current_user
            for item in [ri,pi,si]:
                item.setTextAlignment(Qt.AlignCenter); item.setBackground(bg)
                item.setForeground(QColor(color if is_me else TEXT))
            self.rt.setItem(row,0,ri); self.rt.setItem(row,1,pi); self.rt.setItem(row,2,si)