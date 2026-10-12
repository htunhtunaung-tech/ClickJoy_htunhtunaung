import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow,
                             QVBoxLayout, QWidget, QHBoxLayout,
                             QGridLayout, QLineEdit,
                             QPushButton, QLabel,
                             QTextEdit, QStackedWidget, QFrame,
                             QTableWidget,
                             QTableWidgetItem, QScrollArea, QProgressBar,
                             QMessageBox, QHeaderView, QSizePolicy)

from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QSize, QDate
from PySide6.QtGui import QPixmap, QFont, QAction, QIcon, QColor, QPalette

# ==================== Dark Neon Palette ====================
BG      = "#0e0f14"
SURFACE = "#13151c"
PANEL   = "#181b25"
EDGE    = "#22263a"
TEXT    = "#e8ecff"
DIM     = "#5a637a"
GHOST   = "#2a2e40"

# Per-game neon: (neon, glow_dark, label)
NEON = {
    "normal": ("#3b82f6", "#0f2a5c"),
    "flip":   ("#f59e0b", "#5a3600"),
    "switch": ("#10b981", "#043d28"),
    "swap":   ("#ec4899", "#5a0c30"),
    "cpm":    ("#8b5cf6", "#2d0f5c"),
    "stop":   ("#06b6d4", "#023648"),
    "pop":    ("#f97316", "#5c1f00"),
    "focus":  ("#e879f9", "#4d0060"),
    "chaos":  ("#ff4d4d", "#5a0000"),
    "memory": ("#00e5ff", "#003648"),
    "dopa":   ("#39ff14", "#073a00"),
    "rcs":    ("#a3e635", "#2e4a00"),
}

GLOBAL_STYLE = f"""
* {{ font-family: 'Segoe UI', Arial, sans-serif; }}
QWidget {{ background-color: {BG}; color: {TEXT}; }}
QMainWindow {{ background-color: {BG}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{
    background: {SURFACE}; width: 6px; border-radius: 3px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {EDGE}; border-radius: 3px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
QTableWidget {{
    background: {SURFACE}; gridline-color: {EDGE};
    border: 1px solid {EDGE}; border-radius: 8px; outline: none;
}}
QHeaderView::section {{
    background: {PANEL}; color: {DIM};
    border: none; border-bottom: 1px solid {EDGE};
    padding: 6px; font-weight: bold; font-size: 10px;
}}
QTableWidget::item {{ padding: 4px; border: none; }}
QTableWidget::item:selected {{ background: {EDGE}; color: {TEXT}; }}
QLineEdit {{
    background: {SURFACE}; color: {TEXT};
    border: 1px solid {EDGE}; border-radius: 8px;
    padding: 0 10px;
}}
QLineEdit:focus {{ border: 1px solid #3b82f6; }}
QProgressBar {{
    border: 1px solid {EDGE}; border-radius: 6px;
    background: {SURFACE}; color: {TEXT}; text-align: center;
}}
QProgressBar::chunk {{ border-radius: 5px; }}
"""

# ==================== Data Manager ====================
DATA_FILE = "data.txt"
ALL_DB_FIELDS = ["normal", "flip", "switch", "pop", "swap", "cpm", "stop",
                 "focus", "chaos", "memory", "dopa", "rcs"]

class DataManager:
    def __init__(self):
        if not os.path.exists(DATA_FILE):
            open(DATA_FILE, "w", encoding="utf-8").close()

    def _parse_line(self, line: str) -> dict | None:
        line = line.strip()
        if not line:
            return None
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            return None

        def _val(key):
            for p in parts[3:]:
                k = p.split("=", 1)[0].strip()
                if k == key:
                    return p.split("=", 1)[1].strip()
            return "0"

        reward_raw = _val("reward")
        rewards = [r for r in reward_raw.split() if r] if reward_raw != "0" else []

        return {
            "user":     parts[0],
            "password": parts[1],
            "uid":      parts[2],
            "total":    int(_val("total")  or 0),
            "normal":   int(_val("normal") or 0),
            "flip":     int(_val("flip")   or 0),
            "switch":   int(_val("switch") or 0),
            "pop":      int(_val("pop")    or 0),
            "swap":     int(_val("swap")   or 0),
            "cpm":      int(_val("cpm")    or 0),
            "stop":     int(_val("stop")   or 0),
            "focus":    int(_val("focus")  or 0),
            "chaos":    int(_val("chaos")  or 0),
            "memory":   int(_val("memory") or 0),
            "dopa":     int(_val("dopa")   or 0),
            "rcs":      int(_val("rcs")    or 0),
            "reward":   rewards,
        }

    def _dict_to_line(self, d: dict) -> str:
        rw = " ".join(d.get("reward", [])) if d.get("reward") else ""
        return (
            f"{d['user']},{d['password']},{d['uid']},"
            f"total = {d['total']},"
            f"normal = {d['normal']},"
            f"flip = {d['flip']},"
            f"switch = {d['switch']},"
            f"pop = {d['pop']},"
            f"swap = {d['swap']},"
            f"cpm = {d['cpm']},"
            f"stop = {d['stop']},"
            f"focus = {d['focus']},"
            f"chaos = {d['chaos']},"
            f"memory = {d['memory']},"
            f"dopa = {d['dopa']},"
            f"rcs = {d['rcs']},"
            f"reward = {rw}"
        )

    def _read_all(self) -> list[dict]:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return [d for line in f if (d := self._parse_line(line))]

    def _write_all(self, rows: list[dict]):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(self._dict_to_line(r) + "\n")

    def _next_uid(self, rows: list[dict]) -> str:
        if not rows:
            return "00000001"
        return str(max(int(r["uid"]) for r in rows) + 1).zfill(8)

    def user_exists(self, username: str) -> bool:
        return any(r["user"] == username for r in self._read_all())

    def register(self, username: str, password: str) -> bool:
        rows = self._read_all()
        if any(r["user"] == username for r in rows):
            return False
        rows.append({
            "user": username, "password": password,
            "uid": self._next_uid(rows),
            "total": 0, "normal": 0, "flip": 0, "switch": 0,
            "pop": 0, "swap": 0, "cpm": 0, "stop": 0,
            "focus": 0, "chaos": 0, "memory": 0, "dopa": 0, "rcs": 0,
            "reward": [],
        })
        self._write_all(rows)
        return True

    def login(self, username: str, password: str) -> dict | None:
        for r in self._read_all():
            if r["user"] == username and r["password"] == password:
                return r
        return None

    def get_user(self, username: str) -> dict | None:
        for r in self._read_all():
            if r["user"] == username:
                return r
        return None

    def update_score(self, username: str, field: str, value: int):
        rows = self._read_all()
        for r in rows:
            if r["user"] == username:
                r[field] = value
                r["total"] = sum(r.get(f, 0) for f in ALL_DB_FIELDS)
                break
        self._write_all(rows)

    def add_reward(self, username: str, reward_id: str):
        rows = self._read_all()
        for r in rows:
            if r["user"] == username:
                if reward_id not in r["reward"]:
                    r["reward"].append(reward_id)
                break
        self._write_all(rows)

    def has_reward(self, username: str, reward_id: str) -> bool:
        u = self.get_user(username)
        return bool(u) and reward_id in u["reward"]

    def get_all_scores(self, field: str) -> list[tuple[str, int]]:
        rows = self._read_all()
        result = [(r["user"], r.get(field, 0)) for r in rows]
        result.sort(key=lambda x: x[1], reverse=True)
        return result

    def get_reward_percent(self, reward_id: str) -> float:
        rows = self._read_all()
        if not rows:
            return 0.0
        return (sum(1 for r in rows if reward_id in r["reward"]) / len(rows)) * 100.0


# ==================== Neon Game Button ====================
def make_game_btn(label: str, icon: str, subtitle: str, field: str, callback) -> QPushButton:
    """สร้างปุ่มเกมสไตล์ neon card"""
    neon, glow = NEON.get(field, ("#3b82f6", "#0f2a5c"))
    btn = QPushButton()
    btn.setMinimumHeight(70)
    btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    btn.setText(f"{icon}  {label}\n{subtitle}")
    btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {PANEL};
            color: {TEXT};
            border: 1px solid {EDGE};
            border-left: 3px solid {neon};
            border-radius: 10px;
            text-align: left;
            padding: 8px 14px;
        }}
        QPushButton:hover {{
            background: {glow};
            border: 1px solid {neon};
            border-left: 4px solid {neon};
            color: white;
        }}
        QPushButton:pressed {{
            background: {neon}33;
        }}
    """)
    btn.clicked.connect(callback)
    return btn


# ==================== Main Window ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clickjoy")
        self.resize(800, 700)

        self.db = DataManager()
        self.current_user = None

        self.container = QWidget()
        self.setCentralWidget(self.container)
        self.container.setFixedSize(800, 700)

        self.stack = QStackedWidget(self.container)
        self.stack.setGeometry(0, 0, 800, 700)

        self.login_page   = LoginPage(self)
        self.main_menu    = MainMenuPage(self)
        self.ranking_page = RankingPage(self)
        self.task_page    = TaskPage(self)
        self.reward_page  = RewardPage(self)
        self.setting_page = SettingPage(self)
        self.profile_page = ProfilePage(self)

        for page in [self.login_page, self.main_menu, self.ranking_page,
                     self.task_page, self.reward_page, self.setting_page,
                     self.profile_page]:
            self.stack.addWidget(page)

        # Hamburger menu (same structure as original)
        self.ham_menu = HamburgerMenuPage(self.container, self)
        self.ham_menu.setGeometry(-280, 0, 280, 700)
        self.ham_open = False

        self.stack.setCurrentIndex(0)

    def go_to(self, index):
        self.stack.setCurrentIndex(index)

    def on_login_success(self, username):
        self.current_user = username
        self.main_menu.update_user_label()
        self.ham_menu.update_user_label()
        self.ranking_page.refresh()
        self.task_page.refresh()
        self.reward_page.refresh()
        self.profile_page.refresh()
        self.go_to(1)

    def toggle_hamburger(self):
        self.ham_menu.raise_()
        w, h = 280, 700
        anim = QPropertyAnimation(self.ham_menu, b"geometry")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        if not self.ham_open:
            anim.setStartValue(QRect(-w, 0, w, h))
            anim.setEndValue(QRect(0, 0, w, h))
            self.ham_open = True
        else:
            anim.setStartValue(QRect(0, 0, w, h))
            anim.setEndValue(QRect(-w, 0, w, h))
            self.ham_open = False
        anim.start()
        self._anim = anim


# ==================== Login / Register Page ====================
class LoginPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.db = main_window.db

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        box = QFrame()
        box.setFixedWidth(320)
        box.setStyleSheet(f"""
            QFrame {{
                background: {PANEL};
                border: 1px solid {EDGE};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(box)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("🖱️ Clickjoy")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {TEXT}; border: none; background: transparent;")
        layout.addWidget(title)

        self.mode_lbl = QLabel("Login")
        self.mode_lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.mode_lbl.setAlignment(Qt.AlignCenter)
        self.mode_lbl.setStyleSheet(f"color: {DIM}; border: none; background: transparent;")
        layout.addWidget(self.mode_lbl)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        self.user_input.setFixedHeight(38)
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setFixedHeight(38)
        layout.addWidget(self.pass_input)

        self.action_btn = QPushButton("Login")
        self.action_btn.setFixedHeight(42)
        self.action_btn.setStyleSheet("""
            QPushButton {
                background: #1d4ed8; color: white;
                font-weight: bold; font-size: 14px;
                border-radius: 10px; border: none;
            }
            QPushButton:hover { background: #2563eb; }
            QPushButton:pressed { background: #1e40af; }
        """)
        self.action_btn.clicked.connect(self._on_action)
        layout.addWidget(self.action_btn)

        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet(
            f"color: #f87171; border: none; background: transparent;"
        )
        layout.addWidget(self.status_lbl)

        toggle_row = QHBoxLayout()
        toggle_lbl = QLabel("ยังไม่มีบัญชี?")
        toggle_lbl.setStyleSheet(
            f"color: {DIM}; border: none; background: transparent; font-size: 11px;"
        )
        self.toggle_btn = QPushButton("Register")
        self.toggle_btn.setFlat(True)
        self.toggle_btn.setStyleSheet(
            "color: #3b82f6; font-weight: bold; border: none;"
            " background: transparent; font-size: 11px;"
        )
        self.toggle_btn.clicked.connect(self._toggle_mode)
        toggle_row.addStretch()
        toggle_row.addWidget(toggle_lbl)
        toggle_row.addWidget(self.toggle_btn)
        toggle_row.addStretch()
        layout.addLayout(toggle_row)

        outer.addWidget(box)
        self._mode = "login"

    def _toggle_mode(self):
        if self._mode == "login":
            self._mode = "register"
            self.mode_lbl.setText("Register")
            self.action_btn.setText("Register")
            self.toggle_btn.setText("Login")
        else:
            self._mode = "login"
            self.mode_lbl.setText("Login")
            self.action_btn.setText("Login")
            self.toggle_btn.setText("Register")
        self.status_lbl.setText("")

    def _on_action(self):
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()
        if not username or not password:
            self.status_lbl.setText("กรุณากรอก username และ password")
            return
        if self._mode == "login":
            user_data = self.db.login(username, password)
            if user_data:
                self.status_lbl.setText("")
                self.main_window.on_login_success(username)
            else:
                self.status_lbl.setText("❌ Username หรือ Password ไม่ถูกต้อง")
        else:
            success = self.db.register(username, password)
            if success:
                self.status_lbl.setStyleSheet(
                    "color: #4ade80; border: none; background: transparent;"
                )
                self.status_lbl.setText("✅ สมัครสำเร็จ! กรุณา Login")
                self._toggle_mode()
            else:
                self.status_lbl.setStyleSheet(
                    "color: #f87171; border: none; background: transparent;"
                )
                self.status_lbl.setText("❌ Username นี้มีอยู่แล้ว")


# ==================== Main Menu ====================
class MainMenuPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- Menu Bar ---
        self.menu_bar = main_window.menuBar()
        self.menu_bar.setStyleSheet(f"""
            QMenuBar {{
                background: {PANEL}; color: {TEXT};
                border-bottom: 1px solid {EDGE};
            }}
            QMenuBar::item:selected {{ background: {EDGE}; }}
            QMenu {{
                background: {PANEL}; color: {TEXT};
                border: 1px solid {EDGE};
            }}
            QMenu::item:selected {{ background: {EDGE}; }}
        """)

        file_menu = self.menu_bar.addMenu("&File")
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.main_window.close)
        file_menu.addAction(exit_action)

        progress_menu = self.menu_bar.addMenu("&Progress Menu")

        add_rank_action = QAction("&Ranking", self)
        add_rank_action.setShortcut("Ctrl+R")
        add_rank_action.setShortcutContext(Qt.ApplicationShortcut)
        add_rank_action.triggered.connect(lambda: self.main_window.go_to(2))
        progress_menu.addAction(add_rank_action)

        add_task_action = QAction("&Task", self)
        add_task_action.setShortcut("Ctrl+T")
        add_task_action.setShortcutContext(Qt.ApplicationShortcut)
        add_task_action.triggered.connect(lambda: self.main_window.go_to(3))
        progress_menu.addAction(add_task_action)

        add_reward_action = QAction("R&eward", self)
        add_reward_action.setShortcut("Ctrl+Shift+R")
        add_reward_action.setShortcutContext(Qt.ApplicationShortcut)
        add_reward_action.triggered.connect(lambda: self.main_window.go_to(4))
        progress_menu.addAction(add_reward_action)

        # --- Top bar with hamburger + user ---
        top_layout = QHBoxLayout()
        top_layout.setSpacing(0)

        hamburger_top_btn = QPushButton("☰")
        hamburger_top_btn.setFixedSize(36, 36)
        hamburger_top_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PANEL}; color: {TEXT};
                border: 1px solid {EDGE}; border-radius: 8px; font-size: 16px;
            }}
            QPushButton:hover {{ background: {EDGE}; }}
        """)
        hamburger_top_btn.clicked.connect(self.main_window.toggle_hamburger)
        top_layout.addWidget(hamburger_top_btn)
        top_layout.addStretch()

        self.user_lbl = QLabel("👤 Guest")
        self.user_lbl.setFont(QFont("Segoe UI", 10))
        self.user_lbl.setStyleSheet(f"color: {DIM}; background: transparent;")
        top_layout.addWidget(self.user_lbl)
        layout.addLayout(top_layout)

        # --- Ranking / Task / Reward card buttons (ORIGINAL LAYOUT KEPT) ---
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(8)

        ranking_btn = self._make_nav_card("🏆", "Ranking", "#f59e0b")
        ranking_btn.clicked.connect(lambda: self.main_window.go_to(2))
        cards_layout.addWidget(ranking_btn)

        task_btn = self._make_nav_card("📋", "Task", "#10b981")
        task_btn.clicked.connect(lambda: self.main_window.go_to(3))
        cards_layout.addWidget(task_btn)

        reward_btn = self._make_nav_card("⭐", "Reward", "#ec4899")
        reward_btn.clicked.connect(lambda: self.main_window.go_to(4))
        cards_layout.addWidget(reward_btn)

        layout.addLayout(cards_layout)

        # --- "Let's Click" heading ---
        lets_click_lbl = QLabel("Let's Click")
        lets_click_lbl.setFont(QFont("Segoe UI", 20, QFont.Bold))
        lets_click_lbl.setStyleSheet(f"color: {TEXT}; background: transparent;")
        layout.addWidget(lets_click_lbl)

        # --- Scrollable area for all game buttons ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)
        scroll_layout.setContentsMargins(0, 0, 6, 0)

        # Normal Click (full width)
        normal_btn = make_game_btn(
            "Normal Click", "🖱️", "tap as fast as you can", "normal",
            lambda: self._add_score("normal", 1)
        )
        normal_btn.setFixedHeight(70)
        scroll_layout.addWidget(normal_btn)

        # Grid for all other games (2 columns)
        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(8)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        game_grid = [
            ("Flip Coin",         "🪙", "heads or tails?",            "flip",   0, 0),
            ("Switch",            "🔘", "toggle the switch",           "switch", 0, 1),
            ("Pop It",            "🟣", "pop every bubble fast!",      "pop",    1, 0),
            ("Swap Click",        "🔄", "chase the target",            "swap",   1, 1),
            ("Click per Time",    "⏱️", "race the clock",              "cpm",    2, 0),
            ("Stopwatch",         "⏲️", "hit the exact time",          "stop",   2, 1),
            ("Focus Burst",       "◈",  "click only the right shape",  "focus",  3, 0),
            ("Chaos Control",     "⚡",  "find the real button!",       "chaos",  3, 1),
            ("Memory Flash",      "◫",  "remember the pattern",        "memory", 4, 0),
            ("Dopamine Meter",    "◑",  "stay controlled, fill meter", "dopa",   4, 1),
            ("Color Shift",       "◐",  "match the color — react fast","rcs",    5, 0),
        ]

        for name, icon, sub, field, row, col in game_grid:
            btn = make_game_btn(name, icon, sub, field,
                                lambda f=field: self._add_score(f, 1))
            btn.setFixedHeight(70)
            grid_layout.addWidget(btn, row, col)

        scroll_layout.addWidget(grid_widget)
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

    def _make_nav_card(self, icon: str, label: str, color: str) -> QPushButton:
        btn = QPushButton(f"{icon}\n\n{label}")
        btn.setFixedHeight(110)
        btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {PANEL};
                color: {TEXT};
                border: 1px solid {EDGE};
                border-top: 3px solid {color};
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background: {color}22;
                border: 1px solid {color};
                border-top: 3px solid {color};
                color: {color};
            }}
            QPushButton:pressed {{
                background: {color}44;
            }}
        """)
        return btn

    def update_user_label(self):
        name = self.main_window.current_user or "Guest"
        self.user_lbl.setText(f"👤 {name}")

    def _add_score(self, field, amount):
        username = self.main_window.current_user
        if not username:
            return
        db = self.main_window.db
        user = db.get_user(username)
        new_val = int(user[field]) + amount
        db.update_score(username, field, new_val)
        self.main_window.task_page.refresh()


# ==================== Hamburger Menu (original structure, dark styled) ====================
class HamburgerMenuPage(QWidget):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True) 
        self.main_window = main_window
        self.setFixedWidth(280)

        # Override global QWidget rule with explicit stylesheet on this widget
        self.setStyleSheet(f"""
            HamburgerMenuPage {{
                background-color: {SURFACE};
                border-right: 1px solid {EDGE};
            }}
            HamburgerMenuPage QWidget {{
                background-color: {SURFACE};
            }}
            HamburgerMenuPage QPushButton {{
                background: transparent; color: {DIM};
                border: none; border-radius: 8px;
                text-align: left; padding-left: 10px; font-size: 12px;
            }}
            HamburgerMenuPage QLineEdit {{
                background: {PANEL}; color: {TEXT};
                border: 1px solid {EDGE}; border-radius: 8px; padding: 0 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Close / hamburger toggle button
        close_btn = QPushButton("☰ Close")
        close_btn.setFixedHeight(34)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {GHOST}; color: {DIM};
                border: 1px solid {EDGE}; border-radius: 8px; font-size: 15px;
            }}
            QPushButton:hover {{ background: {EDGE}; color: {TEXT}; }}
        """)
        close_btn.clicked.connect(self.main_window.toggle_hamburger)
        layout.addWidget(close_btn)

        # Search bar (same as original)
        search = QLineEdit()
        search.setPlaceholderText("🔍  Search")
        search.setFixedHeight(34)
        layout.addWidget(search)

        # Profile row (same as original)
        profile_row = QHBoxLayout()
        icon_lbl = QLabel("👤")
        icon_lbl.setFont(QFont("Segoe UI", 16))
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        self.name_btn = QPushButton("Guest")
        self.name_btn.setFlat(True)
        self.name_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.name_btn.setStyleSheet(
            f"color: {TEXT}; background: transparent; border: none; text-align: left;"
        )
        self.name_btn.clicked.connect(lambda: (self.main_window.toggle_hamburger(),
                                               self.main_window.go_to(6)))
        profile_row.addWidget(icon_lbl)
        profile_row.addWidget(self.name_btn)
        profile_row.addStretch()
        layout.addLayout(profile_row)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"background: {EDGE}; max-height: 1px; border: none;")
        layout.addWidget(line)

        # Nav items (same labels/indexes as original)
        nav_items = [
            ("🏆  Ranking", 2, "#f59e0b"),
            ("📋  Task",    3, "#10b981"),
            ("⭐  Reward",  4, "#ec4899"),
            ("⚙️  Setting", 5, "#8b5cf6"),
            ("👤  Profile", 6, "#06b6d4"),
        ]
        for label, idx, color in nav_items:
            btn = QPushButton(label)
            btn.setFixedHeight(38)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {DIM};
                    border: none; border-radius: 8px;
                    text-align: left; padding-left: 10px; font-size: 12px;
                }}
                QPushButton:hover {{ background: {GHOST}; color: {color}; }}
            """)
            btn.clicked.connect(lambda checked, i=idx: (
                self.main_window.toggle_hamburger(), self.main_window.go_to(i)))
            layout.addWidget(btn)

        # Logout
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet(f"background: {EDGE}; max-height: 1px; border: none;")
        layout.addWidget(line2)

        logout_btn = QPushButton("🚪  Logout")
        logout_btn.setFixedHeight(38)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: #f87171;
                border: none; border-radius: 8px;
                text-align: left; padding-left: 10px; font-size: 12px;
            }}
            QPushButton:hover {{ background: {GHOST}; }}
        """)
        logout_btn.clicked.connect(self._logout)
        layout.addWidget(logout_btn)

        layout.addStretch()

    def update_user_label(self):
        self.name_btn.setText(self.main_window.current_user or "Guest")

    def _logout(self):
        self.main_window.current_user = None
        self.main_window.toggle_hamburger()
        self.main_window.go_to(0)


# ==================== Ranking Page ====================
class RankingPage(QWidget):
    STYLES = [
        ("🖱️ Total",        "total",  "#858585"),
        ("🖱️ Normal",       "normal", "#3b82f6"),
        ("🪙 Flip",         "flip",   "#f59e0b"),
        ("🔘 Switch",       "switch", "#10b981"),
        ("🟣 Pop It",       "pop",    "#f97316"),
        ("🔄 Swap",         "swap",   "#ec4899"),
        ("⏱️ CPM",          "cpm",    "#8b5cf6"),
        ("⏲️ Stop",         "stop",   "#06b6d4"),
        ("◈ Focus",         "focus",  "#e879f9"),
        ("⚡ Chaos",        "chaos",  "#ff4d4d"),
        ("◫ Memory",        "memory", "#00e5ff"),
        ("◑ Dopamine",      "dopa",   "#39ff14"),
        ("◐ Color Shift",   "rcs",    "#a3e635"),
    ]

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._cur_field   = "total"
        self._cur_display = "Total Click"
        self._cur_color   = "#858585"
        self._btns = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        back = QPushButton("← Back to Main")
        back.setFixedHeight(32)
        back.setStyleSheet(f"""
            QPushButton {{
                background: {GHOST}; color: {DIM};
                border: 1px solid {EDGE}; border-radius: 8px;
                font-size: 11px; padding: 0 10px;
            }}
            QPushButton:hover {{ background: {EDGE}; color: {TEXT}; }}
        """)
        back.clicked.connect(lambda: main_window.go_to(1))
        layout.addWidget(back, alignment=Qt.AlignLeft)

        lbl = QLabel("🏆 Ranking Page")
        lbl.setContentsMargins(0, 4, 0, 0)
        lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl.setStyleSheet(f"color: {TEXT}; background: transparent;")
        layout.addWidget(lbl)

        self.current_style_lbl = QLabel("Total Click")
        self.current_style_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.current_style_lbl.setAlignment(Qt.AlignCenter)
        self.current_style_lbl.setContentsMargins(0, 0, 0, 4)  
        self.current_style_lbl.setStyleSheet(
            f"color: #e8ecff; background: {PANEL}; border: 1px solid {EDGE};"
            f" border-radius: 8px; padding: 4px;"
        )
        layout.addWidget(self.current_style_lbl)

        # Scrollable filter buttons — horizontal scrollbar visible
        btn_scroll = QScrollArea()
        btn_scroll.setFixedHeight(44)   # 32px btn + 4px bar + 4px padding
        btn_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        btn_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        btn_scroll.setWidgetResizable(False)
        btn_scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {BG}; border: none;
            }}
            QScrollBar:horizontal {{
                background: {SURFACE}; height: 4px;
                border-radius: 2px; margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: {EDGE}; border-radius: 2px; min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: #3b82f6;
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{ width: 0; }}
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{ background: none; }}
        """)

        bw = QWidget()
        bw.setStyleSheet(f"background: {BG};")
        br = QHBoxLayout(bw)
        br.setContentsMargins(0, 0, 0, 0)
        br.setSpacing(6)

        self._btn_widgets = []
        for label, field, color in self.STYLES:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setFixedWidth(110)   # fixed width per button so total is predictable
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {PANEL}; color: {DIM};
                    border: 1px solid {EDGE}; border-radius: 8px;
                    font-size: 10px; font-weight: bold;
                }}
                QPushButton:checked {{
                    background: {color}22; color: {color}; border: 1px solid {color};
                }}
                QPushButton:hover {{
                    background: {color}15; color: {color}; border: 1px solid {color};
                }}
            """)
            btn.clicked.connect(
                lambda _, f=field, d=label, c=color: self.load_ranking(f, d, c)
            )
            br.addWidget(btn)
            self._btns[field] = (btn, color)
            self._btn_widgets.append(btn)

        # Width = n_buttons * (btn_width + spacing) + margins
        n = len(self.STYLES)
        bw.setFixedWidth(n * 110 + (n - 1) * 6 + 4)
        btn_scroll.setWidget(bw)
        layout.addWidget(btn_scroll)

        # Table
        self.ranking_table = QTableWidget()
        self.ranking_table.setColumnCount(3)
        self.ranking_table.setHorizontalHeaderLabels(["Rank", "Player", "Score"])
        header = self.ranking_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.ranking_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ranking_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.ranking_table.verticalHeader().setVisible(False)
        self.ranking_table.setShowGrid(False)
        layout.addWidget(self.ranking_table)

    def refresh(self):
        self.load_ranking(self._cur_field, self._cur_display, self._cur_color)

    def load_ranking(self, field, display_name, color="#e8ecff"):
        self._cur_field   = field
        self._cur_display = display_name
        self._cur_color   = color
        self.current_style_lbl.setText(display_name)
        self.current_style_lbl.setStyleSheet(
            f"color: {color}; background: {PANEL}; border: 1px solid {EDGE};"
            f" border-radius: 8px; padding: 4px;"
        )
        for f, (btn, c) in self._btns.items():
            btn.setChecked(f == field)

        data = self.main_window.db.get_all_scores(field)
        self.ranking_table.setRowCount(len(data))
        medal = {0: "🥇", 1: "🥈", 2: "🥉"}
        row_bg_map = {0: "#1a1400", 1: "#0f1018", 2: "#12100a"}

        for row, (username, score) in enumerate(data):
            rank_item   = QTableWidgetItem(medal.get(row, str(row + 1)))
            player_item = QTableWidgetItem(username)
            score_item  = QTableWidgetItem(f"{score:,}")

            bg = row_bg_map.get(row, PANEL)
            is_me = username == self.main_window.current_user
            for item in [rank_item, player_item, score_item]:
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(QColor(bg))
                item.setForeground(QColor(color if is_me else TEXT))

            self.ranking_table.setItem(row, 0, rank_item)
            self.ranking_table.setItem(row, 1, player_item)
            self.ranking_table.setItem(row, 2, score_item)


# ==================== Task Page ====================
class TaskPage(QWidget):
    TASKS = [
        ("100click",   "🖱️", "Normal Click\n100 times",         "normal", 100),
        ("200flip",    "🪙", "Flip Coin\n200 times",             "flip",   200),
        ("1000switch", "🔘", "Switch\n1,000 times",              "switch", 1000),
        ("300pop",     "🟣", "Pop It\n300 times",                "pop",    300),
        ("150swap",    "🔄", "Swap Click\n150 times",            "swap",   150),
        ("50cpm",      "⏱️", "Click per Time\n50 times",         "cpm",    50),
        ("100focus",   "◈",  "Focus Burst\n100 times",           "focus",  100),
        ("200chaos",   "⚡",  "Chaos Control\n200 times",         "chaos",  200),
        ("100memory",  "◫",  "Memory Flash\n100 times",          "memory", 100),
        ("500dopa",    "◑",  "Dopamine Meter\n500 times",        "dopa",   500),
        ("300rcs",     "◐",  "Color Shift\n300 times",           "rcs",    300),
    ]

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout_main = QVBoxLayout(self)
        self.layout_main.setContentsMargins(8, 8, 8, 8)
        self.layout_main.setSpacing(8)

        back = QPushButton("← Back to Main")
        back.setFixedHeight(32)
        back.setStyleSheet(f"""
            QPushButton {{
                background: {GHOST}; color: {DIM};
                border: 1px solid {EDGE}; border-radius: 8px;
                font-size: 11px; padding: 0 10px;
            }}
            QPushButton:hover {{ background: {EDGE}; color: {TEXT}; }}
        """)
        back.clicked.connect(lambda: main_window.go_to(1))
        self.layout_main.addWidget(back, alignment=Qt.AlignLeft)

        lbl = QLabel("📋 Task Page")
        lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl.setStyleSheet(f"color: {TEXT}; background: transparent;")
        self.layout_main.addWidget(lbl)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout_main.addWidget(self.scroll)
        self._build_content()

    def _build_content(self):
        old = self.scroll.takeWidget()   # ← เพิ่ม
        if old: old.deleteLater()  

        username = self.main_window.current_user
        db = self.main_window.db
        user_data = db.get_user(username) if username else None

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        grid = QGridLayout(scroll_content)
        grid.setSpacing(10)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setAlignment(Qt.AlignTop)

        for i, (rid, icon, name, field, total) in enumerate(self.TASKS):
            current = int(user_data[field]) if user_data else 0
            claimed = db.has_reward(username, rid) if username else False
            card = self._make_task_card(rid, icon, name, current, total, claimed)
            grid.addWidget(card, i // 2, i % 2)

        self.scroll.setWidget(scroll_content)

    def refresh(self):
        self._build_content()

    def _make_task_card(self, reward_id, icon, name, current, total, claimed):
        done = current >= total

        if claimed:
            bc, bgc = "#4ade80", "#021308"
        elif done:
            bc, bgc = "#fbbf24", "#130e00"
        else:
            bc, bgc = EDGE, PANEL

        card = QFrame()
        card.setFixedHeight(190)
        card.setObjectName("TCard")
        card.setStyleSheet(f"""
            #TCard {{
                background: {bgc}; border: 1px solid {bc}; border-radius: 12px;
            }}
        """)
        v = QVBoxLayout(card)
        v.setSpacing(6)
        v.setContentsMargins(10, 10, 10, 10)

        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI", 26))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        v.addWidget(icon_lbl)

        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet(
            f"color: {TEXT}; border: none; background: transparent;"
        )
        v.addWidget(name_lbl)

        chunk_c = "#4ade80" if (claimed or done) else "#3b82f6"
        bar = QProgressBar()
        bar.setMinimum(0)
        bar.setMaximum(total)
        bar.setValue(min(current, total))
        bar.setFormat(f"{min(current,total):,} / {total:,}")
        bar.setFixedHeight(22)
        bar.setAlignment(Qt.AlignCenter)
        bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {EDGE}; border-radius: 8px;
                background: {SURFACE}; color: {TEXT}; font-size: 10px;
            }}
            QProgressBar::chunk {{ background: {chunk_c}; border-radius: 7px; }}
        """)
        v.addWidget(bar)

        if claimed:
            btn = QPushButton("✅  Claimed")
            btn.setEnabled(False)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: #021308; color: #4ade80;
                    border: 1px solid #4ade80; border-radius: 8px; font-weight: bold;
                }}
            """)
        elif done:
            btn = QPushButton("🎁  Claim Reward")
            btn.setStyleSheet("""
                QPushButton {
                    background: #78350f; color: #fbbf24;
                    border: 1px solid #fbbf24; border-radius: 8px; font-weight: bold;
                }
                QPushButton:hover { background: #92400e; }
                QPushButton:pressed { background: #451a03; }
            """)
            btn.clicked.connect(lambda _, rid=reward_id: self._claim(rid))
        else:
            btn = QPushButton("🔒  Cannot Claim Yet")
            btn.setEnabled(False)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {GHOST}; color: {DIM};
                    border: 1px solid {EDGE}; border-radius: 8px;
                }}
            """)

        btn.setFixedHeight(34)
        v.addWidget(btn)
        return card

    def _claim(self, reward_id):
        username = self.main_window.current_user
        if not username:
            return
        self.main_window.db.add_reward(username, reward_id)
        self.main_window.reward_page.refresh()
        self.refresh()

# ==================== Reward Page ====================
class RewardPage(QWidget):
    REWARDS = [
        ("100click",   "🖱️", "Normal Click\n100 times",      "normal", 100),
        ("200flip",    "🪙", "Flip Coin\n200 times",          "flip",   200),
        ("1000switch", "🔘", "Switch\n1,000 times",           "switch", 1000),
        ("300pop",     "🟣", "Pop It\n300 times",             "pop",    300),
        ("150swap",    "🔄", "Swap Click\n150 times",         "swap",   150),
        ("50cpm",      "⏱️", "Click per Time\n50 times",      "cpm",    50),
        ("100focus",   "◈",  "Focus Burst\n100 times",        "focus",  100),
        ("200chaos",   "⚡",  "Chaos Control\n200 times",      "chaos",  200),
        ("100memory",  "◫",  "Memory Flash\n100 times",       "memory", 100),
        ("500dopa",    "◑",  "Dopamine Meter\n500 times",     "dopa",   500),
        ("300rcs",     "◐",  "Color Shift\n300 times",        "rcs",    300),
    ]

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        back = QPushButton("← Back to Main")
        back.setFixedHeight(32)
        back.setStyleSheet(f"""
            QPushButton {{
                background: {GHOST}; color: {DIM};
                border: 1px solid {EDGE}; border-radius: 8px;
                font-size: 11px; padding: 0 10px;
            }}
            QPushButton:hover {{ background: {EDGE}; color: {TEXT}; }}
        """)
        back.clicked.connect(lambda: main_window.go_to(1))
        layout.addWidget(back, alignment=Qt.AlignLeft)

        lbl = QLabel("⭐ Reward Page")
        lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl.setStyleSheet(f"color: {TEXT}; background: transparent;")
        layout.addWidget(lbl)

        sub_lbl = QLabel("Tasks you have completed")
        sub_lbl.setFont(QFont("Segoe UI", 10))
        sub_lbl.setStyleSheet(f"color: {DIM}; background: transparent;")
        layout.addWidget(sub_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.scroll_content)
        self.grid.setSpacing(10)
        self.grid.setContentsMargins(4, 4, 4, 4)
        self.grid.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll)

    def refresh(self):
        for i in reversed(range(self.grid.count())):
            if w := self.grid.itemAt(i).widget():
                w.setParent(None)

        username = self.main_window.current_user
        db = self.main_window.db
        for i, (rid, badge, name, field, threshold) in enumerate(self.REWARDS):
            unlocked = db.has_reward(username, rid) if username else False
            pct = db.get_reward_percent(rid)
            card = self._make_reward_card(badge, name, pct, unlocked)
            self.grid.addWidget(card, i // 2, i % 2)

    def _make_reward_card(self, badge, name, percent, unlocked):
        bc = "#fbbf24" if unlocked else EDGE
        bgc = "#130e00" if unlocked else PANEL

        card = QFrame()
        card.setFixedHeight(210)
        card.setObjectName("RCard")
        card.setStyleSheet(f"""
            #RCard {{ background: {bgc}; border: 1px solid {bc}; border-radius: 12px; }}
        """)
        v = QVBoxLayout(card)
        v.setSpacing(6)
        v.setContentsMargins(10, 10, 10, 10)

        icon_lbl = QLabel(badge if unlocked else "🔒")
        icon_lbl.setFont(QFont("Segoe UI", 28))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        v.addWidget(icon_lbl)

        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet(
            f"color: {TEXT if unlocked else DIM}; border: none; background: transparent;"
        )
        v.addWidget(name_lbl)

        owners_lbl = QLabel(f"{percent:.1f}% of all players have this")
        owners_lbl.setFont(QFont("Segoe UI", 8))
        owners_lbl.setAlignment(Qt.AlignCenter)
        owners_lbl.setStyleSheet(f"color: {DIM}; border: none; background: transparent;")
        owners_lbl.setWordWrap(True)
        v.addWidget(owners_lbl)

        if percent >= 50:
            rt, rc = "Common",       "#4ade80"
        elif percent >= 10:
            rt, rc = "Uncommon",     "#60a5fa"
        elif percent >= 1:
            rt, rc = "Rare",         "#c084fc"
        else:
            rt, rc = "🔥 Legendary", "#f97316"

        rarity_lbl = QLabel(rt if unlocked else "???")
        rarity_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        rarity_lbl.setAlignment(Qt.AlignCenter)
        rarity_lbl.setStyleSheet(
            f"color: {rc if unlocked else GHOST}; border: none; background: transparent;"
        )
        v.addWidget(rarity_lbl)
        return card


# ==================== Setting Page ====================
class SettingPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        lbl = QLabel("⚙️ Setting Page")
        lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color: {TEXT}; background: transparent;")
        layout.addWidget(lbl)

        back = QPushButton("← Back to Main")
        back.setFixedHeight(38)
        back.setFixedWidth(160)
        back.setStyleSheet(f"""
            QPushButton {{
                background: {GHOST}; color: {DIM};
                border: 1px solid {EDGE}; border-radius: 8px;
            }}
            QPushButton:hover {{ background: {EDGE}; color: {TEXT}; }}
        """)
        back.clicked.connect(lambda: main_window.go_to(1))
        layout.addWidget(back, alignment=Qt.AlignCenter)


# ==================== Profile Page ====================
class ProfilePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        back = QPushButton("← Back to Main")
        back.setFixedHeight(32)
        back.setStyleSheet(f"""
            QPushButton {{
                background: {GHOST}; color: {DIM};
                border: 1px solid {EDGE}; border-radius: 8px;
                font-size: 11px; padding: 0 10px;
            }}
            QPushButton:hover {{ background: {EDGE}; color: {TEXT}; }}
        """)
        back.clicked.connect(lambda: main_window.go_to(1))
        layout.addWidget(back, alignment=Qt.AlignLeft)

        lbl = QLabel("👤 Profile")
        lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl.setStyleSheet(f"color: {TEXT}; background: transparent;")
        layout.addWidget(lbl)

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {PANEL}; border: 1px solid {EDGE}; border-radius: 14px;
            }}
        """)
        info_layout = QVBoxLayout(frame)
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(20, 20, 20, 20)

        self._vals = {}
        rows = [
            ("Username",        "#e8ecff"), ("UID",             "#5a637a"),
            ("Total Clicks",    "#3b82f6"), ("Normal Click",    "#3b82f6"),
            ("Flip Coin",       "#f59e0b"), ("Switch",          "#10b981"),
            ("Swap Click",      "#ec4899"), ("Click per Time",  "#8b5cf6"),
            ("Stopwatch",       "#06b6d4"), ("Pop It",          "#f97316"),
            ("Focus Burst",     "#e879f9"), ("Chaos Control",   "#ff4d4d"),
            ("Memory Flash",    "#00e5ff"), ("Dopamine Meter",  "#39ff14"),
            ("Color Shift",     "#a3e635"), ("Rewards",         "#fbbf24"),
        ]
        for label, color in rows:
            h = QHBoxLayout()
            lbl2 = QLabel(label)
            lbl2.setStyleSheet(
                f"color: {DIM}; font-size: 12px; background: transparent; border: none;"
            )
            val = QLabel("—")
            val.setFont(QFont("Segoe UI", 12, QFont.Bold))
            val.setStyleSheet(
                f"color: {color}; background: transparent; border: none;"
            )
            val.setAlignment(Qt.AlignRight)
            h.addWidget(lbl2)
            h.addStretch()
            h.addWidget(val)
            info_layout.addLayout(h)
            self._vals[label] = val

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(frame)
        layout.addWidget(scroll)

    def refresh(self):
        username = self.main_window.current_user
        if not username:
            return
        u = self.main_window.db.get_user(username)
        if not u:
            return
        self._vals["Username"].setText(u["user"])
        self._vals["UID"].setText(u["uid"])
        self._vals["Total Clicks"].setText(f"{u['total']:,}")
        self._vals["Normal Click"].setText(f"{u['normal']:,}")
        self._vals["Flip Coin"].setText(f"{u['flip']:,}")
        self._vals["Switch"].setText(f"{u['switch']:,}")
        self._vals["Swap Click"].setText(f"{u['swap']:,}")
        self._vals["Click per Time"].setText(f"{u['cpm']:,}")
        self._vals["Stopwatch"].setText(f"{u['stop']:,}")
        self._vals["Pop It"].setText(f"{u['pop']:,}")
        self._vals["Focus Burst"].setText(f"{u['focus']:,}")
        self._vals["Chaos Control"].setText(f"{u['chaos']:,}")
        self._vals["Memory Flash"].setText(f"{u['memory']:,}")
        self._vals["Dopamine Meter"].setText(f"{u['dopa']:,}")
        self._vals["Color Shift"].setText(f"{u['rcs']:,}")
        rewards = u["reward"] if u["reward"] else ["none"]
        self._vals["Rewards"].setText(", ".join(rewards))


# ==================== Entry Point ====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())