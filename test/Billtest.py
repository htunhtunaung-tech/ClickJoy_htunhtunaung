import sys
import json
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStackedWidget, QFrame, QDateEdit,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QPen, QBrush

# ── Data store (simple JSON file) ──────────────────────────────────────────────
DATA_FILE = "users.json"

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2)

# ── Shared style helpers ────────────────────────────────────────────────────────
BG_COLOR        = "#f5f5e8"
BLUE            = "#1a6fcf"
DARK_BLUE       = "#0d4fa0"
RED             = "#e53935"
LIGHT_BLUE_BTN  = "#2196f3"

BASE_STYLE = f"""
    QWidget {{
        background-color: {BG_COLOR};
        font-family: 'Segoe UI', Arial, sans-serif;
        color: black;
    }}
"""

def styled_input(placeholder="", password=False):
    field = QLineEdit()
    field.setPlaceholderText(placeholder)
    if password:
        field.setEchoMode(QLineEdit.Password)
    field.setFixedHeight(48)
    field.setStyleSheet(f"""
        QLineEdit {{
            border: 2.5px solid {BLUE};
            border-radius: 24px;
            padding: 0 16px;
            font-size: 15px;
            background: {BG_COLOR};
            color: #222;
        }}
        QLineEdit:focus {{
            border-color: {DARK_BLUE};
        }}
    """)
    return field

def styled_button(text, primary=True):
    btn = QPushButton(text)
    btn.setFixedHeight(50)
    btn.setCursor(Qt.PointingHandCursor)
    if primary:
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LIGHT_BLUE_BTN};
                color: white;
                border-radius: 25px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }}
            QPushButton:hover {{ background-color: {DARK_BLUE}; }}
            QPushButton:pressed {{ background-color: #0a3a80; }}
        """)
    else:
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_COLOR};
                color: {BLUE};
                border: 2.5px solid {BLUE};
                border-radius: 25px;
                font-size: 15px;
            }}
            QPushButton:hover {{ background-color: #e3eeff; }}
        """)
    return btn

def error_label(text=""):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {RED}; font-size: 13px; padding-left: 12px;")
    lbl.setVisible(False)
    return lbl

def link_button(text):
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFlat(True)
    btn.setStyleSheet(f"""
        QPushButton {{
            color: {BLUE};
            font-size: 14px;
            text-decoration: underline;
            border: none;
            background: transparent;
        }}
        QPushButton:hover {{ color: {DARK_BLUE}; }}
    """)
    return btn

def password_input_row(placeholder="Password"):
    """Returns (container_widget, line_edit) with a show/hide toggle."""
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    h = QHBoxLayout(container)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(0)

    field = QLineEdit()
    field.setPlaceholderText(placeholder)
    field.setEchoMode(QLineEdit.Password)
    field.setFixedHeight(48)
    field.setStyleSheet(f"""
        QLineEdit {{
            border: 2.5px solid {BLUE};
            border-top-left-radius: 24px;
            border-bottom-left-radius: 24px;
            border-right: none;
            padding: 0 16px;
            font-size: 15px;
            background: {BG_COLOR};
            color: #222;
        }}
        QLineEdit:focus {{ border-color: {DARK_BLUE}; }}
    """)

    toggle = QPushButton("👁")
    toggle.setFixedSize(48, 48)
    toggle.setCursor(Qt.PointingHandCursor)
    toggle.setCheckable(True)
    toggle.setStyleSheet(f"""
        QPushButton {{
            border: 2.5px solid {BLUE};
            border-top-right-radius: 24px;
            border-bottom-right-radius: 24px;
            border-left: none;
            background: {BG_COLOR};
            font-size: 16px;
        }}
        QPushButton:hover {{ background: #e3eeff; }}
        QPushButton:checked {{ background: #d0e4ff; }}
    """)

    def toggle_echo(checked):
        field.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    toggle.toggled.connect(toggle_echo)
    h.addWidget(field)
    h.addWidget(toggle)
    return container, field


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 – Splash / Main
# ══════════════════════════════════════════════════════════════════════════════
class SplashPage(QWidget):
    def __init__(self, go_login):
        super().__init__()
        self.setStyleSheet(BASE_STYLE)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(40)

        # Title
        title = QLabel("Click Joy")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {BLUE}; font-size: 64px; font-weight: bold; font-style: italic;")
        layout.addWidget(title)

        version = QLabel("v.1.0.0")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet(f"color: {BLUE}; font-size: 20px;")
        layout.addWidget(version)

        layout.addSpacing(30)

        play_btn = styled_button("  PLAY  ")
        play_btn.setFixedWidth(280)
        play_btn.setFixedHeight(64)
        play_btn.setStyleSheet(f"""
            QPushButton {{
                border: 3px solid {BLUE};
                border-radius: 8px;
                color: {BLUE};
                font-size: 28px;
                font-weight: bold;
                background: {BG_COLOR};
                letter-spacing: 6px;
            }}
            QPushButton:hover {{ background: #e3eeff; }}
        """)
        play_btn.clicked.connect(go_login)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(play_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 – Login
# ══════════════════════════════════════════════════════════════════════════════
class LoginPage(QWidget):
    def __init__(self, go_main_menu, go_create, go_forgot):
        super().__init__()
        self.go_main_menu = go_main_menu
        self.setStyleSheet(BASE_STYLE)

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedWidth(400)
        card.setStyleSheet(f"""
            QFrame {{
                border: 3px solid {BLUE};
                border-radius: 16px;
                background: {BG_COLOR};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(14)
        layout.setContentsMargins(36, 36, 36, 36)

        # Avatar icon
        avatar = QLabel("👤")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("font-size: 64px; border: none;")
        layout.addWidget(avatar)
        layout.addSpacing(8)

        # Username
        self.username_input = styled_input("Username")
        layout.addWidget(self.username_input)

        # Password
        pw_container, self.password_input = password_input_row("Password")
        layout.addWidget(pw_container)

        # Error message
        self.error_lbl = error_label("⚠  Incorrect username or password.")
        layout.addWidget(self.error_lbl)

        # Sign in
        signin_btn = styled_button("Sign in")
        signin_btn.clicked.connect(self.handle_login)
        layout.addWidget(signin_btn)

        # Forgot password
        fp_btn = link_button("Forgot password?")
        fp_btn.clicked.connect(go_forgot)
        layout.addWidget(fp_btn, alignment=Qt.AlignCenter)

        layout.addSpacing(4)

        # Create account
        ca_btn = link_button("Create account")
        ca_btn.clicked.connect(go_create)
        layout.addWidget(ca_btn, alignment=Qt.AlignCenter)

        outer.addWidget(card, alignment=Qt.AlignCenter)

    def handle_login(self):
        users = load_users()
        uname = self.username_input.text().strip()
        pwd   = self.password_input.text()
        if uname in users and users[uname]["password"] == pwd:
            self.error_lbl.setVisible(False)
            self.username_input.clear()
            self.password_input.clear()
            self.go_main_menu()
        else:
            self.error_lbl.setVisible(True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 – Create Account
# ══════════════════════════════════════════════════════════════════════════════
class CreateAccountPage(QWidget):
    def __init__(self, go_login):
        super().__init__()
        self.go_login = go_login
        self.setStyleSheet(BASE_STYLE)

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedWidth(420)
        card.setStyleSheet(f"""
            QFrame {{
                border: 3px solid {BLUE};
                border-radius: 16px;
                background: {BG_COLOR};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(36, 30, 36, 30)

        # Back button
        back_row = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFlat(True)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                color: {BLUE}; font-size: 14px; font-weight: bold;
                border: none; background: transparent; text-align: left;
            }}
            QPushButton:hover {{ color: {DARK_BLUE}; }}
        """)
        back_btn.clicked.connect(go_login)
        back_row.addWidget(back_btn)
        back_row.addStretch()
        layout.addLayout(back_row)

        title = QLabel("Create Account")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; border: none;")
        layout.addWidget(title)
        layout.addSpacing(6)

        # Username
        lbl_u = QLabel("Username:")
        lbl_u.setStyleSheet("border: none; font-size: 14px;")
        layout.addWidget(lbl_u)
        self.username_input = styled_input("Username")
        layout.addWidget(self.username_input)
        self.username_err = error_label("⚠  This username is already taken.")
        layout.addWidget(self.username_err)

        # Date of birth
        lbl_d = QLabel("Date of Birth (DD/MM/YYYY):")
        lbl_d.setStyleSheet("border: none; font-size: 14px;")
        layout.addWidget(lbl_d)
        self.dob_edit = QDateEdit()
        self.dob_edit.setCalendarPopup(True)
        self.dob_edit.setDisplayFormat("dd/MM/yyyy")
        self.dob_edit.setDate(QDate.currentDate())
        self.dob_edit.setFixedHeight(48)
        self.dob_edit.setStyleSheet(f"""
            QDateEdit {{
                border: 2.5px solid {BLUE};
                border-radius: 24px;
                padding: 0 16px;
                font-size: 15px;
                background: {BG_COLOR};
            }}
            QDateEdit::drop-down {{ border: none; width: 30px; }}
        """)
        layout.addWidget(self.dob_edit)

        # Password
        lbl_p = QLabel("Password:")
        lbl_p.setStyleSheet("border: none; font-size: 14px;")
        layout.addWidget(lbl_p)
        pw_container, self.password_input = password_input_row("Password")
        layout.addWidget(pw_container)

        # Confirm Password
        lbl_c = QLabel("Confirm Password:")
        lbl_c.setStyleSheet("border: none; font-size: 14px;")
        layout.addWidget(lbl_c)
        cp_container, self.confirm_input = password_input_row("Confirm Password")
        layout.addWidget(cp_container)
        self.pw_err = error_label("⚠  Passwords do not match.")
        layout.addWidget(self.pw_err)

        # Create button
        create_btn = styled_button("Create")
        create_btn.clicked.connect(self.handle_create)
        layout.addWidget(create_btn)

        outer.addWidget(card, alignment=Qt.AlignCenter)

    def handle_create(self):
        users = load_users()
        uname = self.username_input.text().strip()
        pwd   = self.password_input.text()
        cpwd  = self.confirm_input.text()
        dob   = self.dob_edit.date().toString("dd/MM/yyyy")

        self.username_err.setVisible(False)
        self.pw_err.setVisible(False)

        if uname in users:
            self.username_err.setVisible(True)
            return
        if pwd != cpwd:
            self.pw_err.setVisible(True)
            return
        if not uname or not pwd:
            return

        users[uname] = {"password": pwd, "dob": dob}
        save_users(users)
        # Clear fields and go to login
        self.username_input.clear()
        self.password_input.clear()
        self.confirm_input.clear()
        self.go_login()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 – Forgot Password
# ══════════════════════════════════════════════════════════════════════════════
class ForgotPasswordPage(QWidget):
    def __init__(self, go_reset, go_login):
        super().__init__()
        self.go_reset = go_reset
        self.setStyleSheet(BASE_STYLE)

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedWidth(400)
        card.setStyleSheet(f"""
            QFrame {{
                border: 3px solid {BLUE};
                border-radius: 16px;
                background: {BG_COLOR};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(14)
        layout.setContentsMargins(36, 40, 36, 40)

        # Back button
        back_row = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFlat(True)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                color: {BLUE}; font-size: 14px; font-weight: bold;
                border: none; background: transparent; text-align: left;
            }}
            QPushButton:hover {{ color: {DARK_BLUE}; }}
        """)
        back_btn.clicked.connect(go_login)
        back_row.addWidget(back_btn)
        back_row.addStretch()
        layout.addLayout(back_row)

        title = QLabel("Forgot password?")
        title.setStyleSheet("font-size: 24px; font-weight: bold; border: none;")
        layout.addWidget(title)

        sub = QLabel("Please enter your username")
        sub.setStyleSheet("font-size: 14px; color: black; border: none;")
        layout.addWidget(sub)

        self.username_input = styled_input("Username")
        layout.addWidget(self.username_input)

        self.error_lbl = error_label("⚠  This name doesn't exist.")
        layout.addWidget(self.error_lbl)

        next_btn = styled_button("Next")
        next_btn.clicked.connect(self.handle_next)
        layout.addWidget(next_btn)

        outer.addWidget(card, alignment=Qt.AlignCenter)

    def handle_next(self):
        users = load_users()
        uname = self.username_input.text().strip()
        if uname in users:
            self.error_lbl.setVisible(False)
            self.go_reset(uname)
        else:
            self.error_lbl.setVisible(True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 – Reset Password
# ══════════════════════════════════════════════════════════════════════════════
class ResetPasswordPage(QWidget):
    def __init__(self, go_login):
        super().__init__()
        self.go_login = go_login
        self.current_user = ""
        self.setStyleSheet(BASE_STYLE)

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedWidth(420)
        card.setStyleSheet(f"""
            QFrame {{
                border: 3px solid {BLUE};
                border-radius: 16px;
                background: {BG_COLOR};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        layout.setContentsMargins(36, 36, 36, 36)

        title = QLabel("Reset password")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; border: none;")
        layout.addWidget(title)

        self.user_label = QLabel("Username: ")
        self.user_label.setStyleSheet(f"font-size: 15px; color: {BLUE}; border: none;")
        layout.addWidget(self.user_label)
        layout.addSpacing(6)

        pw_container, self.new_pw = password_input_row("New password")
        layout.addWidget(pw_container)

        cp_container, self.confirm_pw = password_input_row("Confirm password")
        layout.addWidget(cp_container)

        self.error_lbl = error_label("⚠  Passwords do not match.")
        layout.addWidget(self.error_lbl)

        reset_btn = styled_button("Reset password")
        reset_btn.clicked.connect(self.handle_reset)
        layout.addWidget(reset_btn)

        outer.addWidget(card, alignment=Qt.AlignCenter)

    def set_user(self, username):
        self.current_user = username
        self.user_label.setText(f"Username: {username}")
        self.new_pw.clear()
        self.confirm_pw.clear()
        self.error_lbl.setVisible(False)

    def handle_reset(self):
        npw = self.new_pw.text()
        cpw = self.confirm_pw.text()
        if npw != cpw:
            self.error_lbl.setVisible(True)
            return
        if not npw:
            return
        users = load_users()
        if self.current_user in users:
            users[self.current_user]["password"] = npw
            save_users(users)
        self.go_login()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 – Main Menu (placeholder after login)
# ══════════════════════════════════════════════════════════════════════════════
class MainMenuPage(QWidget):
    def __init__(self, go_splash):
        super().__init__()
        self.setStyleSheet(BASE_STYLE)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        welcome = QLabel("🎉 Welcome to ClickJoy!")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {BLUE};")
        layout.addWidget(welcome)

        sub = QLabel("Main menu — coming soon!")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("font-size: 18px; color: black;")
        layout.addWidget(sub)

        logout_btn = styled_button("Log out", primary=False)
        logout_btn.setFixedWidth(200)
        logout_btn.clicked.connect(go_splash)
        layout.addWidget(logout_btn, alignment=Qt.AlignCenter)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ══════════════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Click Joy")
        self.setGeometry(100, 100, 860, 620)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Create pages
        self.splash_page       = SplashPage(self.go_login)
        self.login_page        = LoginPage(self.go_main_menu, self.go_create, self.go_forgot)
        self.create_page       = CreateAccountPage(self.go_login)
        self.forgot_page       = ForgotPasswordPage(self.go_reset, self.go_login)
        self.reset_page        = ResetPasswordPage(self.go_login)
        self.main_menu_page    = MainMenuPage(self.go_splash)

        self.stack.addWidget(self.splash_page)     # 0
        self.stack.addWidget(self.login_page)      # 1
        self.stack.addWidget(self.create_page)     # 2
        self.stack.addWidget(self.forgot_page)     # 3
        self.stack.addWidget(self.reset_page)      # 4
        self.stack.addWidget(self.main_menu_page)  # 5

        self.stack.setCurrentIndex(0)

    def go_splash(self):      self.stack.setCurrentIndex(0)
    def go_login(self):       self.stack.setCurrentIndex(1)
    def go_create(self):      self.stack.setCurrentIndex(2)
    def go_forgot(self):      self.stack.setCurrentIndex(3)
    def go_main_menu(self):   self.stack.setCurrentIndex(5)

    def go_reset(self, username):
        self.reset_page.set_user(username)
        self.stack.setCurrentIndex(4)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
