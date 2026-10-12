from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QStackedWidget, QFrame, QDialog)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from theme_and_animation import (F, FM, DIM, TEXT, EDGE, PANEL, SURFACE, GHOST,
    show_toast)

# ==================== FeedbackDialog ====================
class _FeedbackDialog(QDialog):
    RECIPIENT = "burawitchaya.r@kkumail.com"

    def __init__(self, main_window, parent=None):
        super().__init__(parent or main_window)
        self.main_window = main_window
        self.setWindowTitle("Send Feedback")
        self.setFixedWidth(460); self.setMinimumHeight(360)
        self.setStyleSheet(f"""
            QDialog {{ background:{SURFACE}; }}
            QLabel  {{ background:transparent; color:{TEXT}; border:none; }}
            QLineEdit, QTextEdit {{
                background:{PANEL}; color:{TEXT};
                border:1px solid {EDGE}; border-radius:8px; padding:6px 10px;
                font-size: 9pt;
            }}
            QLineEdit:focus, QTextEdit:focus {{ border-color:#3b82f6; }}
        """)
        from PySide6.QtWidgets import QTextEdit
        lay = QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(14)
        title = QLabel("💬  Send Feedback"); title.setFont(F(15, 700))
        title.setStyleSheet(f"color:{TEXT};")
        sub = QLabel(f"Your message will be sent to  {self.RECIPIENT}")
        sub.setFont(F(9)); sub.setStyleSheet(f"color:{DIM};")
        lay.addWidget(title); lay.addWidget(sub)
        lay.addWidget(self._lbl("Topic"))
        self.topic = QLineEdit()
        self.topic.setPlaceholderText("e.g. Bug report, Suggestion, Other…")
        self.topic.setFixedHeight(36); lay.addWidget(self.topic)
        lay.addWidget(self._lbl("Message"))
        self.msg_edit = QTextEdit()
        self.msg_edit.setPlaceholderText("Describe your feedback here…")
        self.msg_edit.setMinimumHeight(120); lay.addWidget(self.msg_edit)
        self.status = QLabel(""); self.status.setFont(F(9))
        self.status.setAlignment(Qt.AlignCenter); lay.addWidget(self.status)
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        cancel = QPushButton("Cancel"); cancel.setFixedHeight(38)
        cancel.setStyleSheet(f"QPushButton{{background:{GHOST};color:{DIM};border:1px solid {EDGE};border-radius:10px;}}QPushButton:hover{{background:{EDGE};color:{TEXT};}}")
        cancel.clicked.connect(self.reject)
        self.send_btn = QPushButton("📨  Send"); self.send_btn.setFixedHeight(38)
        self.send_btn.setStyleSheet("QPushButton{background:#1d4ed8;color:white;border:none;border-radius:10px;font-weight:700;font-size: 10pt;}QPushButton:hover{background:#2563eb;}QPushButton:disabled{background:#2a2e40;color:#5a637a;}")
        self.send_btn.clicked.connect(self._send)
        btn_row.addWidget(cancel); btn_row.addWidget(self.send_btn)
        lay.addLayout(btn_row)

    def _lbl(self, text):
        l = QLabel(text); l.setFont(F(10, 600)); l.setStyleSheet(f"color:{DIM};"); return l

    def _send(self):
        topic = self.topic.text().strip()
        body  = self.msg_edit.toPlainText().strip()
        user  = self.main_window.current_user or "Guest"
        if not topic: self._err("Please enter a topic."); return
        if not body:  self._err("Please write your message."); return
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (f"{'='*60}\n"
                 f"Date    : {timestamp}\n"
                 f"From    : {user}\n"
                 f"Topic   : {topic}\n"
                 f"Message :\n{body}\n\n")
        try:
            with open("feedback.txt", "a", encoding="utf-8") as f:
                f.write(entry)
            self.status.setText("✅  Feedback saved! Thank you.")
            self.status.setStyleSheet("color:#4ade80;background:transparent;border:none;")
            self.send_btn.setEnabled(False)
            QTimer.singleShot(1600, self.accept)
        except Exception as e:
            self._err(f"Could not save: {e}")

    def _err(self, msg):
        self.status.setText(f"⚠  {msg}")
        self.status.setStyleSheet("color:#f87171;background:transparent;border:none;")


# ==================== LoginPage ====================
class LoginPage(QWidget):
    _BLUE      = "#1a6fcf"
    _DARK_BLUE = "#0d4fa0"
    _BG        = "#f5f5e8"
    _RED       = "#e53935"

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.db          = main_window.db
        self._mode       = "login"
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_login_card())
        self._stack.addWidget(self._build_register_card())
        self._stack.addWidget(self._build_forgot_card())
        self._stack.setCurrentIndex(0)
        outer.addWidget(self._stack)

    def _build_login_card(self):
        W = QWidget(); W.setStyleSheet("background:transparent;")
        outer = QVBoxLayout(W); outer.setAlignment(Qt.AlignCenter)
        card = QFrame(); card.setFixedWidth(380)
        card.setStyleSheet(f"QFrame {{border: 3px solid {self._BLUE};border-radius: 18px;background: {self._BG};}}")
        lay = QVBoxLayout(card); lay.setSpacing(14); lay.setContentsMargins(36, 32, 36, 32)
        av = QLabel("👤"); av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet("font-size: 44pt; border: none; background: transparent;")
        lay.addWidget(av)
        title = QLabel("🖱️  Clickjoy"); title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 20pt; font-weight: bold; font-style: italic;color: {self._BLUE}; border: none; background: transparent;")
        lay.addWidget(title); lay.addSpacing(4)
        self._login_user = self._input("Username"); lay.addWidget(self._login_user)
        pw_row, self._login_pass = self._password_row("Password"); lay.addWidget(pw_row)
        self._login_err = self._err_lbl("⚠  Username หรือ Password ไม่ถูกต้อง"); lay.addWidget(self._login_err)
        signin = self._primary_btn("Sign in"); signin.clicked.connect(self._on_login); lay.addWidget(signin)
        fp = self._link_btn("Forgot password?"); fp.clicked.connect(lambda: self._stack.setCurrentIndex(2)); lay.addWidget(fp, alignment=Qt.AlignCenter)
        lay.addSpacing(2)
        row = QHBoxLayout(); row.addStretch(); row.addWidget(self._dim_lbl("Don't have an account?"))
        ca = self._link_btn("Create account"); ca.clicked.connect(lambda: self._stack.setCurrentIndex(1)); row.addWidget(ca); row.addStretch()
        lay.addLayout(row)
        outer.addWidget(card, alignment=Qt.AlignCenter); return W

    def _build_register_card(self):
        W = QWidget(); W.setStyleSheet("background:transparent;")
        outer = QVBoxLayout(W); outer.setAlignment(Qt.AlignCenter)
        card = QFrame(); card.setFixedWidth(400)
        card.setStyleSheet(f"QFrame {{border: 3px solid {self._BLUE};border-radius: 18px;background: {self._BG};}}")
        lay = QVBoxLayout(card); lay.setSpacing(10); lay.setContentsMargins(36, 28, 36, 28)
        back_row = QHBoxLayout()
        back = QPushButton("← Back"); back.setFlat(True); back.setCursor(Qt.PointingHandCursor)
        back.setStyleSheet(f"QPushButton{{color:{self._BLUE};font-size: 10pt;font-weight:bold;border:none;background:transparent;text-align:left;}}QPushButton:hover{{color:{self._DARK_BLUE};}}")
        back.clicked.connect(lambda: (self._stack.setCurrentIndex(0), self._clear_register()))
        back_row.addWidget(back); back_row.addStretch(); lay.addLayout(back_row)
        title = QLabel("Create Account"); title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 17pt; font-weight: bold; font-style: italic; color: {self._BLUE}; border: none; background: transparent;")
        lay.addWidget(title); lay.addSpacing(4)
        lay.addWidget(self._field_lbl("Username:"))
        self._reg_user = self._input("Username"); lay.addWidget(self._reg_user)
        self._reg_user_err = self._err_lbl("⚠ This username is already taken"); lay.addWidget(self._reg_user_err)
        lay.addWidget(self._field_lbl("Password:"))
        pw_row, self._reg_pass = self._password_row("Password"); lay.addWidget(pw_row)
        lay.addWidget(self._field_lbl("Confirm Password:"))
        cp_row, self._reg_confirm = self._password_row("Confirm Password"); lay.addWidget(cp_row)
        self._reg_pw_err = self._err_lbl("⚠  Passwords do not match"); lay.addWidget(self._reg_pw_err)
        create = self._primary_btn("Create Account"); create.clicked.connect(self._on_register); lay.addWidget(create)
        self._reg_ok = QLabel("✅  Account created successfully! Please sign in.")
        self._reg_ok.setAlignment(Qt.AlignCenter)
        self._reg_ok.setStyleSheet("color:#16a34a;font-size: 10pt;border:none;background:transparent;")
        self._reg_ok.setVisible(False); lay.addWidget(self._reg_ok)
        outer.addWidget(card, alignment=Qt.AlignCenter); return W

    def _build_forgot_card(self):
        W = QWidget(); W.setStyleSheet("background:transparent;")
        outer = QVBoxLayout(W); outer.setAlignment(Qt.AlignCenter)
        card = QFrame(); card.setFixedWidth(400)
        card.setStyleSheet(f"QFrame {{border: 3px solid {self._BLUE};border-radius: 18px;background: {self._BG};}}")
        lay = QVBoxLayout(card); lay.setSpacing(12); lay.setContentsMargins(36, 28, 36, 28)
        back_row = QHBoxLayout()
        back = QPushButton("← Back"); back.setFlat(True); back.setCursor(Qt.PointingHandCursor)
        back.setStyleSheet(f"QPushButton{{color:{self._BLUE};font-size:11pt;font-weight:bold;border:none;background:transparent;text-align:left;}}QPushButton:hover{{color:{self._DARK_BLUE};}}")
        back.clicked.connect(lambda: (self._stack.setCurrentIndex(0), self._clear_forgot()))
        back_row.addWidget(back); back_row.addStretch(); lay.addLayout(back_row)
        title = QLabel("Forgot password?")
        title.setStyleSheet(f"font-size: 20pt; font-weight: bold; font-style: italic;color: {self._BLUE}; border: none; background: transparent;")
        lay.addWidget(title)
        sub = QLabel("Enter your username")
        sub.setStyleSheet("font-size: 11pt; color: #555; border: none; background: transparent;")
        lay.addWidget(sub); lay.addSpacing(4)
        self._fp_user = self._input("Username"); lay.addWidget(self._fp_user)
        self._fp_user_err = self._err_lbl("⚠  Username not found"); lay.addWidget(self._fp_user_err)
        self._fp_step2 = QWidget(); self._fp_step2.setStyleSheet("background:transparent;")
        s2 = QVBoxLayout(self._fp_step2); s2.setContentsMargins(0,4,0,0); s2.setSpacing(8)
        s2.addWidget(self._field_lbl("New Password:"))
        pw_row, self._fp_new_pw = self._password_row("New Password"); s2.addWidget(pw_row)
        s2.addWidget(self._field_lbl("Confirm New Password:"))
        cp_row, self._fp_confirm = self._password_row("Confirm Password"); s2.addWidget(cp_row)
        self._fp_pw_err = self._err_lbl("⚠  Passwords do not match"); s2.addWidget(self._fp_pw_err)
        self._fp_step2.setVisible(False); lay.addWidget(self._fp_step2)
        self._fp_btn = self._primary_btn("Next"); self._fp_btn.clicked.connect(self._on_forgot_next); lay.addWidget(self._fp_btn)
        self._fp_ok = QLabel("✅  Password changed successfully!")
        self._fp_ok.setAlignment(Qt.AlignCenter)
        self._fp_ok.setStyleSheet("color:#16a34a;font-size:11pt;border:none;background:transparent;")
        self._fp_ok.setVisible(False); lay.addWidget(self._fp_ok)
        outer.addWidget(card, alignment=Qt.AlignCenter)
        self._fp_found_user = [None]; return W

    def _on_forgot_next(self):
        if not self._fp_found_user[0]:
            uname = self._fp_user.text().strip()
            u = self.db.get_user(uname)
            if not u: self._fp_user_err.setVisible(True); return
            self._fp_user_err.setVisible(False)
            self._fp_found_user[0] = uname
            self._fp_user.setEnabled(False)
            self._fp_step2.setVisible(True)
            self._fp_btn.setText("Reset Password")
        else:
            npw = self._fp_new_pw.text(); cpw = self._fp_confirm.text()
            if npw != cpw: self._fp_pw_err.setVisible(True); return
            if not npw: return
            self._fp_pw_err.setVisible(False)
            rows = self.db._read_all()
            for r in rows:
                if r["user"] == self._fp_found_user[0]: r["password"] = npw; break
            self.db._write_all(rows)
            self._fp_ok.setVisible(True)
            self._fp_btn.setEnabled(False)
            QTimer.singleShot(1600, lambda: (self._stack.setCurrentIndex(0), self._clear_forgot()))

    def _clear_forgot(self):
        self._fp_found_user[0] = None
        self._fp_user.clear(); self._fp_user.setEnabled(True)
        self._fp_new_pw.clear(); self._fp_confirm.clear()
        self._fp_step2.setVisible(False)
        self._fp_btn.setText("Next"); self._fp_btn.setEnabled(True)
        for w in (self._fp_user_err, self._fp_pw_err, self._fp_ok): w.setVisible(False)

    def _on_login(self):
        u = self._login_user.text().strip(); p = self._login_pass.text()
        self._login_err.setVisible(False)
        if not u or not p:
            self._login_err.setText("⚠  Please enter your Username and Password")
            self._login_err.setVisible(True); return
        ud = self.db.login(u, p)
        if ud:
            self._login_user.clear(); self._login_pass.clear()
            self.main_window.on_login_success(u)
        else:
            self._login_err.setText("⚠  Username or Password is incorrect")
            self._login_err.setVisible(True)

    def _on_register(self):
        u = self._reg_user.text().strip(); p = self._reg_pass.text(); cp = self._reg_confirm.text()
        self._reg_user_err.setVisible(False); self._reg_pw_err.setVisible(False); self._reg_ok.setVisible(False)
        if not u or not p: return
        if self.db.get_user(u): self._reg_user_err.setVisible(True); return
        if p != cp: self._reg_pw_err.setVisible(True); return
        self.db.register(u, p); self._reg_ok.setVisible(True)
        self._clear_register()
        QTimer.singleShot(1400, lambda: self._stack.setCurrentIndex(0))

    def _clear_register(self):
        for w in (self._reg_user, self._reg_pass, self._reg_confirm): w.clear()
        for w in (self._reg_user_err, self._reg_pw_err, self._reg_ok): w.setVisible(False)

    def _input(self, placeholder):
        f = QLineEdit(); f.setPlaceholderText(placeholder); f.setFixedHeight(44)
        f.setStyleSheet(f"""QLineEdit {{border: 2.5px solid {self._BLUE};border-radius: 22px;
            padding: 0 16px;font-size: 11pt;background: {self._BG};color: #222;}}
            QLineEdit:focus {{ border-color: {self._DARK_BLUE}; }}""")
        return f

    def _password_row(self, placeholder):
        container = QWidget(); container.setStyleSheet("background:transparent;")
        h = QHBoxLayout(container); h.setContentsMargins(0,0,0,0); h.setSpacing(0)
        field = QLineEdit(); field.setPlaceholderText(placeholder)
        field.setEchoMode(QLineEdit.Password); field.setFixedHeight(44)
        field.setStyleSheet(f"""QLineEdit {{border: 2.5px solid {self._BLUE};
            border-top-left-radius: 22px;border-bottom-left-radius: 22px;border-right: none;
            padding: 0 16px;font-size: 11pt;background: {self._BG};color: #222;}}
            QLineEdit:focus {{ border-color: {self._DARK_BLUE}; }}""")
        toggle = QPushButton("︶"); toggle.setFixedSize(44, 44)
        toggle.setCursor(Qt.PointingHandCursor); toggle.setCheckable(True)
        toggle.setStyleSheet(f"""QPushButton {{border: 2.5px solid {self._BLUE};
            border-top-right-radius: 22px;border-bottom-right-radius: 22px;border-left: none;
            background: {self._BG};font-size: 12pt;color: {self._BLUE};}}
            QPushButton:hover {{ background: #e3eeff; }}
            QPushButton:checked {{ background: #d0e4ff; }}""")
        def _toggle_echo(checked):
            field.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
            toggle.setText("👁" if checked else "︶")
        toggle.toggled.connect(_toggle_echo)
        h.addWidget(field); h.addWidget(toggle); return container, field

    def _primary_btn(self, text):
        btn = QPushButton(text); btn.setFixedHeight(46); btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""QPushButton {{background: {self._BLUE};color: white;border-radius: 23px;
            font-size: 11pt;font-weight: bold;border: none;}}
            QPushButton:hover {{ background: {self._DARK_BLUE}; }}
            QPushButton:pressed {{ background: #0a3a80; }}""")
        return btn

    def _link_btn(self, text):
        btn = QPushButton(text); btn.setFlat(True); btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""QPushButton {{color: {self._BLUE}; font-size: 10pt;
            text-decoration: underline; border: none; background: transparent;}}
            QPushButton:hover {{ color: {self._DARK_BLUE}; }}""")
        return btn

    def _err_lbl(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{self._RED};font-size: 9pt;border:none;background:transparent;padding-left:8px;")
        lbl.setVisible(False); return lbl

    def _dim_lbl(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{DIM};font-size: 9pt;border:none;background:transparent;")
        return lbl

    def _field_lbl(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 10pt;font-weight:600;border:none;background:transparent;color:#333;")
        return lbl
