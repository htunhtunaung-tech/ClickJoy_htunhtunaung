import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QStackedWidget
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve
from PySide6.QtGui import QFont, QAction

from theme_and_animation import (F, FM, NEON, NAMES, GLOBAL_STYLE,
                                  DARK_STYLE, LIGHT_STYLE, _build_stylesheet,
                                  _DARK_PALETTE, _LIGHT_PALETTE,
                                  TEXT, DIM, GHOST, EDGE, PANEL, BG)
from data_manager import DataManager
from login import LoginPage, _FeedbackDialog
from menu import MainMenuPage
from hamburger import HamburgerMenuPage
from ranking import RankingPage
from task import TaskPage, RewardPage
from setting import SettingPage
from profile import ProfilePage
from normal import NormalClickPage
from flip import FlipCoinPage
from switch import SwitchPage
from swap import SwapClickPage
from cpm import ClickPerTimePage
from stop import StopwatchPage
from pop import PopItPage
from focus import FocusBurstPage
from chaos import ChaosControlPage
from memory import MemoryFlashPage
from dopa import DopamineMeterPage
from rcs import ColorShiftPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clickjoy")
        self.resize(920, 700)
        self.db = DataManager()
        self.current_user = None
        self.container = QWidget()
        self.setCentralWidget(self.container)
        self.stack = QStackedWidget(self.container)
        self.stack.setGeometry(0, 0, self.container.width(), self.container.height())

        self.login_page   = LoginPage(self)
        self.main_menu    = MainMenuPage(self)
        self.ranking_page = RankingPage(self)
        self.task_page    = TaskPage(self)
        self.reward_page  = RewardPage(self)
        self.setting_page = SettingPage(self)
        self.profile_page = ProfilePage(self)

        for p in [self.login_page,self.main_menu,self.ranking_page,
                  self.task_page,self.reward_page,self.setting_page,self.profile_page]:
            self.stack.addWidget(p)

        self.ham_menu = HamburgerMenuPage(self.container, self)
        self.ham_menu.setGeometry(-280,0,280,700)
        self.ham_open = False

        _game_classes = [
            NormalClickPage, FlipCoinPage,    SwitchPage,       SwapClickPage,
            ClickPerTimePage, StopwatchPage,  PopItPage,        FocusBurstPage,
            ChaosControlPage, MemoryFlashPage, DopamineMeterPage, ColorShiftPage,
        ]
        self._game_pages = {}
        for cls in _game_classes:
            page = cls(self)
            self.stack.addWidget(page)
            self._game_pages[cls.KEY] = page

        self.stack.setCurrentIndex(0)

        from PySide6.QtWidgets import QToolBar
        self._tb = QToolBar("Quick Access"); self._tb.setMovable(False)
        self._tb.setStyleSheet(f"""
            QToolBar {{ background:{PANEL}; border-bottom:1px solid {EDGE}; spacing:4px; padding:2px 6px; }}
            QToolButton {{ background:transparent; color:{DIM}; border:none; border-radius:6px;
                           padding:4px 10px; font-size: 9pt; }}
            QToolButton:hover {{ background:{GHOST}; color:{TEXT}; }}
        """)
        for icon, label, idx in [("🏆","Ranking",2),("📋","Task",3),("⭐","Reward",4),("⚙️","Settings",5),("👤","Profile",6)]:
            a = QAction(f"{icon}  {label}", self)
            a.triggered.connect(lambda _, i=idx: self.go_to(i))
            self._tb.addAction(a)
        self._tb.addSeparator()
        fb_action = QAction("💬  Feedback", self)
        fb_action.triggered.connect(lambda: _FeedbackDialog(self).exec())
        self._tb.addAction(fb_action)
        self.addToolBar(self._tb)

        self._status_bar = self.statusBar()
        self._status_bar.setStyleSheet(f"""
            QStatusBar {{ background:{PANEL}; color:{DIM}; border-top:1px solid {EDGE};
                          font-size: 8pt; padding:0 8px; }}
            QStatusBar::item {{ border:none; }}
        """)
        self._status_bar.showMessage("Welcome to Clickjoy  •  Select a game to start")

        self._tb.setVisible(False)
        self.menuBar().setVisible(False)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        w, h = self.container.width(), self.container.height()
        self.stack.setGeometry(0, 0, w, h)
        if hasattr(self, 'ham_menu'):
            y = self.ham_menu.y()
            self.ham_menu.setGeometry(self.ham_menu.x(), 0, 280, h)

    _PAGE_NAMES = {0:"Login", 1:"Game Select", 2:"Ranking", 3:"Task",
                   4:"Reward", 5:"Settings", 6:"Profile"}

    def go_to(self, index):
        self.stack.setCurrentIndex(index)
        name = self._PAGE_NAMES.get(index, "")
        user = self.current_user or "Guest"
        msg = f"📍 {name}  •  Logged in as {user}" if self.current_user else f"📍 {name}"
        if hasattr(self, '_status_bar'): self._status_bar.showMessage(msg)
        # Refresh each page every time it's navigated to —
        # QStackedWidget showEvent is unreliable on repeated visits.
        if index == 1 and hasattr(self, 'main_menu'):
            self.main_menu._refresh_chips()
            self.main_menu.detail.refresh_score()
        elif index == 2 and hasattr(self, 'ranking_page'):
            self.ranking_page.refresh()
        elif index == 3 and hasattr(self, 'task_page'):
            self.task_page.refresh()
        elif index == 4 and hasattr(self, 'reward_page'):
            self.reward_page.refresh()
        elif index == 6 and hasattr(self, 'profile_page'):
            self.profile_page.refresh()

    def go_game(self, key):
        page = self._game_pages.get(key)
        if page:
            self.stack.setCurrentWidget(page)
            if hasattr(self, '_status_bar'):
                self._status_bar.showMessage(f"🎮 {NAMES.get(key, key)}  •  {self.current_user or 'Guest'}")

    def on_login_success(self, username):
        self.current_user = username
        self.main_menu.update_user_label()
        self.ham_menu.update_user_label()
        self.ranking_page.refresh(); self.task_page.refresh()
        self.reward_page.refresh(); self.profile_page.refresh()
        self._tb.setVisible(True)
        self.menuBar().setVisible(True)
        self.go_to(1)
        if hasattr(self, '_status_bar'):
            self._status_bar.showMessage(f"✅ Logged in as {username}  •  Select a game to start")

    def toggle_hamburger(self):
        self.ham_menu.raise_()
        w, h = 280, self.container.height()
        anim = QPropertyAnimation(self.ham_menu, b"geometry")
        anim.setDuration(300); anim.setEasingCurve(QEasingCurve.OutCubic)
        if not self.ham_open:
            anim.setStartValue(QRect(-w,0,w,h)); anim.setEndValue(QRect(0,0,w,h))
            self.ham_open = True
        else:
            anim.setStartValue(QRect(0,0,w,h)); anim.setEndValue(QRect(-w,0,w,h))
            self.ham_open = False
        anim.start(); self._anim = anim

    def refresh_theme(self):
        self._tb.setStyleSheet(f"""
            QToolBar {{ background:{PANEL}; border-bottom:1px solid {EDGE}; spacing:4px; padding:2px 6px; }}
            QToolButton {{ background:transparent; color:{DIM}; border:none; border-radius:6px;
                           padding:4px 10px; font-size: 9pt; }}
            QToolButton:hover {{ background:{GHOST}; color:{TEXT}; }}
        """)
        self._status_bar.setStyleSheet(f"""
            QStatusBar {{ background:{PANEL}; color:{DIM}; border-top:1px solid {EDGE};
                          font-size: 8pt; padding:0 8px; }}
            QStatusBar::item {{ border:none; }}
        """)
        self.main_menu.refresh_theme()
        self.ham_menu.refresh_theme()
        self.ranking_page.refresh_theme()
        self.profile_page.refresh_theme()
        self.task_page.refresh()
        self.reward_page.refresh()
        self.container.update()
        for i in range(self.stack.count()):
            w = self.stack.widget(i)
            if w: w.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    default_font = QFont("Segoe UI", 11)
    app.setFont(default_font)
    app.setStyleSheet(GLOBAL_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())