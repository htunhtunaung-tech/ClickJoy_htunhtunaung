from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QFrame,
                               QLabel, QPushButton, QScrollArea, QProgressBar,
                               QGridLayout)
from PySide6.QtCore import Qt

from theme_and_animation import (F, FM, _make_back_btn,
                                  TEXT, DIM, GHOST, EDGE, PANEL, SURFACE)


class TaskPage(QWidget):
    TASKS = [
        ("100click","🖱️","Normal Click\n100 times","normal",100),
        ("200flip","🪙","Flip Coin\n200 times","flip",200),
        ("1000switch","🔘","Switch\n1,000 times","switch",1000),
        ("300pop","🟣","Pop It\n300 times","pop",300),
        ("150swap","🔄","Swap Click\n150 times","swap",150),
        ("50cpm","⏱️","Click per Time\n50 times","cpm",50),
        ("100focus","◈","Focus Burst\n100 times","focus",100),
        ("200chaos","⚡","Chaos Control\n200 times","chaos",200),
        ("100memory","◫","Memory Flash\n100 times","memory",100),
        ("500dopa","◑","Dopamine Meter\n500 times","dopa",500),
        ("300rcs","◐","Color Shift\n300 times","rcs",300),
    ]
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.lm = QVBoxLayout(self); self.lm.setContentsMargins(8,8,8,8); self.lm.setSpacing(8)
        _hrow = QHBoxLayout(); _hrow.setSpacing(10); _hrow.setContentsMargins(0,0,0,0)
        _hrow.addWidget(_make_back_btn(lambda: main_window.go_to(1)), 0, Qt.AlignVCenter)
        _htitle = QLabel("📋 Task Page"); _htitle.setFont(F(16, 700))
        _htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        _hrow.addWidget(_htitle, 1, Qt.AlignVCenter)
        self.lm.addLayout(_hrow)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.lm.addWidget(self.scroll)
        self._build_content()

    def _build_content(self):
        old = self.scroll.takeWidget()
        if old: old.deleteLater()
        username = self.main_window.current_user; db = self.main_window.db
        user_data = db.get_user(username) if username else None
        sc = QWidget(); sc.setStyleSheet("background:transparent;")
        grid = QGridLayout(sc); grid.setSpacing(10); grid.setContentsMargins(4,4,4,4); grid.setAlignment(Qt.AlignTop)
        for i,(rid,icon,name,field,total) in enumerate(self.TASKS):
            current = int(user_data[field]) if user_data else 0
            claimed = db.has_reward(username,rid) if username else False
            grid.addWidget(self._make_card(rid,icon,name,current,total,claimed), i//2, i%2)
        self.scroll.setWidget(sc)

    def refresh(self): self._build_content()

    def _make_card(self, rid, icon, name, current, total, claimed):
        done = current >= total
        bc,bgc = ("#4ade80","#021308") if claimed else (("#fbbf24","#130e00") if done else (EDGE,PANEL))
        card = QFrame(); card.setFixedHeight(190); card.setObjectName("TCard")
        card.setStyleSheet(f"#TCard{{background:{bgc};border:1px solid {bc};border-radius:12px;}}")
        v = QVBoxLayout(card); v.setSpacing(6); v.setContentsMargins(10,10,10,10)
        il = QLabel(icon); il.setFont(F(26)); il.setAlignment(Qt.AlignCenter)
        il.setStyleSheet("border:none;background:transparent;"); v.addWidget(il)
        nl = QLabel(name); nl.setFont(F(10, 700)); nl.setAlignment(Qt.AlignCenter)
        nl.setStyleSheet(f"color:{TEXT};border:none;background:transparent;"); v.addWidget(nl)
        cc = "#4ade80" if (claimed or done) else "#3b82f6"
        bar = QProgressBar(); bar.setMinimum(0); bar.setMaximum(total); bar.setValue(min(current,total))
        bar.setFormat(f"{min(current,total):,} / {total:,}"); bar.setFixedHeight(22); bar.setAlignment(Qt.AlignCenter)
        bar.setStyleSheet(f"QProgressBar{{border:1px solid {EDGE};border-radius:8px;background:{SURFACE};color:{TEXT};font-size: 8pt;}}QProgressBar::chunk{{background:{cc};border-radius:7px;}}")
        v.addWidget(bar)
        if claimed:
            btn=QPushButton("✅  Claimed"); btn.setEnabled(False)
            btn.setStyleSheet("QPushButton{background:#021308;color:#4ade80;border:1px solid #4ade80;border-radius:8px;font-weight:bold;}")
        elif done:
            btn=QPushButton("🎁  Claim Reward")
            btn.setStyleSheet("QPushButton{background:#78350f;color:#fbbf24;border:1px solid #fbbf24;border-radius:8px;font-weight:bold;}QPushButton:hover{background:#92400e;}")
            btn.clicked.connect(lambda _, r=rid: self._claim(r))
        else:
            btn=QPushButton("🔒  Cannot Claim Yet"); btn.setEnabled(False)
            btn.setStyleSheet(f"QPushButton{{background:{GHOST};color:{DIM};border:1px solid {EDGE};border-radius:8px;}}")
        btn.setFixedHeight(34); v.addWidget(btn); return card

    def _claim(self, rid):
        u = self.main_window.current_user
        if not u: return
        self.main_window.db.add_reward(u, rid)
        self.main_window.reward_page.refresh(); self.refresh()


class RewardPage(QWidget):
    REWARDS = [
        ("100click","🖱️","Normal Click\n100 times","normal",100),
        ("200flip","🪙","Flip Coin\n200 times","flip",200),
        ("1000switch","🔘","Switch\n1,000 times","switch",1000),
        ("300pop","🟣","Pop It\n300 times","pop",300),
        ("150swap","🔄","Swap Click\n150 times","swap",150),
        ("50cpm","⏱️","Click per Time\n50 times","cpm",50),
        ("100focus","◈","Focus Burst\n100 times","focus",100),
        ("200chaos","⚡","Chaos Control\n200 times","chaos",200),
        ("100memory","◫","Memory Flash\n100 times","memory",100),
        ("500dopa","◑","Dopamine Meter\n500 times","dopa",500),
        ("300rcs","◐","Color Shift\n300 times","rcs",300),
    ]
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self); layout.setContentsMargins(8,8,8,8); layout.setSpacing(8)
        _hrow = QHBoxLayout(); _hrow.setSpacing(10); _hrow.setContentsMargins(0,0,0,0)
        _hrow.addWidget(_make_back_btn(lambda: main_window.go_to(1)), 0, Qt.AlignVCenter)
        _htitle = QLabel("⭐ Reward Page"); _htitle.setFont(F(16, 700))
        _htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        _hrow.addWidget(_htitle, 1, Qt.AlignVCenter)
        layout.addLayout(_hrow)
        sl = QLabel("Tasks you have completed"); sl.setFont(F(10))
        sl.setStyleSheet(f"color:{DIM};background:transparent;"); layout.addWidget(sl)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sc = QWidget(); self.sc.setStyleSheet("background:transparent;")
        self.grid = QGridLayout(self.sc); self.grid.setSpacing(10); self.grid.setContentsMargins(4,4,4,4); self.grid.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.sc); layout.addWidget(scroll)

    def refresh(self):
        for i in reversed(range(self.grid.count())):
            if w := self.grid.itemAt(i).widget(): w.setParent(None)
        username = self.main_window.current_user; db = self.main_window.db
        for i,(rid,badge,name,field,threshold) in enumerate(self.REWARDS):
            unlocked = db.has_reward(username,rid) if username else False
            pct = db.get_reward_percent(rid)
            self.grid.addWidget(self._make_card(badge,name,pct,unlocked), i//2, i%2)

    def _make_card(self, badge, name, percent, unlocked):
        bc="#fbbf24" if unlocked else EDGE; bgc="#130e00" if unlocked else PANEL
        card=QFrame(); card.setFixedHeight(210); card.setObjectName("RCard")
        card.setStyleSheet(f"#RCard{{background:{bgc};border:1px solid {bc};border-radius:12px;}}")
        v=QVBoxLayout(card); v.setSpacing(6); v.setContentsMargins(10,10,10,10)
        il=QLabel(badge if unlocked else "🔒"); il.setFont(F(28)); il.setAlignment(Qt.AlignCenter)
        il.setStyleSheet("border:none;background:transparent;"); v.addWidget(il)
        nl=QLabel(name); nl.setFont(F(10, 700)); nl.setAlignment(Qt.AlignCenter)
        nl.setStyleSheet(f"color:{TEXT if unlocked else DIM};border:none;background:transparent;"); v.addWidget(nl)
        ol=QLabel(f"{percent:.1f}% of all players have this"); ol.setFont(F(8)); ol.setAlignment(Qt.AlignCenter)
        ol.setStyleSheet(f"color:{DIM};border:none;background:transparent;"); ol.setWordWrap(True); v.addWidget(ol)
        if percent>=50: rt,rc="Common","#4ade80"
        elif percent>=10: rt,rc="Uncommon","#60a5fa"
        elif percent>=1: rt,rc="Rare","#c084fc"
        else: rt,rc="🔥 Legendary","#f97316"
        rl=QLabel(rt if unlocked else "???"); rl.setFont(F(9, 700)); rl.setAlignment(Qt.AlignCenter)
        rl.setStyleSheet(f"color:{rc if unlocked else GHOST};border:none;background:transparent;"); v.addWidget(rl)
        return card
