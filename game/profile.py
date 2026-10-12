import os
import math

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QFrame,
                               QLabel, QPushButton, QScrollArea, QLineEdit,
                               QDialog, QFileDialog, QStackedWidget)
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, QRect, Signal
from PySide6.QtGui import (QPainter, QPainterPath, QColor, QPen, QBrush, QRadialGradient)

from theme_and_animation import (F, FM, _make_back_btn, _StatsBarChart, show_toast,
                                  NEON, TEXT, DIM, GHOST, EDGE, PANEL, SURFACE)


class _AvatarDropZone(QWidget):
    avatar_changed = Signal(str)

    def __init__(self, neon="#3b82f6", parent=None):
        super().__init__(parent)
        self._neon = neon; self._avatar_path = None; self._pixmap = None
        self._hover = False; self._drag_over = False; self._phase = 0.0
        self.setFixedSize(120, 120); self.setAcceptDrops(True); self.setCursor(Qt.PointingHandCursor)
        self._anim = QTimer(self); self._anim.setInterval(30)
        self._anim.timeout.connect(self._step); self._anim.start()

    def set_avatar(self, path):
        from PySide6.QtGui import QPixmap
        self._avatar_path = path
        pm = QPixmap(path)
        if not pm.isNull():
            self._pixmap = pm.scaled(120, 120, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.update()

    def clear_avatar(self):
        self._avatar_path = None; self._pixmap = None; self.update()

    def _step(self): self._phase = (self._phase + 0.04) % (math.pi*2); self.update()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): self._drag_over = True; e.acceptProposedAction(); self.update()

    def dragLeaveEvent(self, e): self._drag_over = False; self.update()

    def dropEvent(self, e):
        self._drag_over = False
        urls = e.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.avatar_changed.emit(path)
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            path, _ = QFileDialog.getOpenFileName(self, "Select Profile Picture", "",
                                                   "Images (*.png *.jpg *.jpeg)")
            if path: self.avatar_changed.emit(path)

    def enterEvent(self, e): self._hover = True;  self.update()
    def leaveEvent(self, e): self._hover = False; self.update()

    def paintEvent(self, ev):
        pa = QPainter(self); pa.setRenderHint(QPainter.Antialiasing)
        w = h = self.width(); r = w // 2
        nc = QColor(self._neon); pulse = 0.5 + 0.5*math.sin(self._phase)
        clip = QPainterPath(); clip.addEllipse(QPointF(r, r), float(r-2), float(r-2))
        pa.setClipPath(clip)
        if self._pixmap:
            pa.drawPixmap(0, 0, self._pixmap)
        else:
            pa.fillPath(clip, QColor(SURFACE))
            pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), int(140+80*pulse)))
            pa.setFont(F(28, 400)); pa.drawText(QRect(0, 18, w, 40), Qt.AlignCenter, "☁")
            pa.setFont(F(8, 500))
            pa.setPen(QColor(nc.red(), nc.green(), nc.blue(), int(120+60*pulse)))
            pa.drawText(QRect(0, 72, w, 30), Qt.AlignCenter, "DROP / CLICK")
        pa.setClipping(False)
        is_active = self._drag_over or self._hover
        ring_a = int(220 if self._drag_over else (180 if self._hover else (100+60*pulse)))
        ring_w = 3.0 if is_active else 2.0
        pa.setPen(QPen(QColor(nc.red(), nc.green(), nc.blue(), ring_a), ring_w))
        pa.setBrush(Qt.NoBrush)
        pa.drawEllipse(QPointF(r, r), float(r-2), float(r-2))
        if is_active:
            glow = QPen(QColor(nc.red(), nc.green(), nc.blue(), 50), 8)
            pa.setPen(glow); pa.drawEllipse(QPointF(r, r), float(r+1), float(r+1))
        pa.end()


class _ConfirmAvatarDialog(QDialog):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Profile Picture")
        self.setFixedSize(360, 320)
        self.setStyleSheet(f"""
            QDialog {{ background:{SURFACE}; border:1px solid {EDGE}; border-radius:16px; }}
            QLabel {{ background:transparent; color:{TEXT}; }}
            QPushButton {{ border-radius:10px; font-size: 10pt; font-weight:700; padding:8px 20px; }}
        """)
        lay = QVBoxLayout(self); lay.setContentsMargins(24,24,24,24); lay.setSpacing(16)
        title = QLabel("Use this photo as profile picture?")
        title.setFont(F(13, 700)); title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color:{TEXT};"); lay.addWidget(title)
        from PySide6.QtGui import QPixmap
        preview = QLabel(); preview.setFixedSize(120, 120); preview.setAlignment(Qt.AlignCenter)
        pm = QPixmap(path)
        if not pm.isNull():
            pm = pm.scaled(120, 120, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            preview.setPixmap(pm)
        preview.setStyleSheet(f"border:2px solid {NEON['normal'][0]};border-radius:60px;")
        lay.addWidget(preview, 0, Qt.AlignCenter)
        sub = QLabel(path.split("/")[-1].split("\\")[-1])
        sub.setFont(F(9)); sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"color:{DIM};"); lay.addWidget(sub)
        lay.addStretch()
        btns = QHBoxLayout(); btns.setSpacing(10)
        cancel = QPushButton("Cancel"); cancel.setFixedHeight(40)
        cancel.setStyleSheet(f"QPushButton{{background:{GHOST};color:{DIM};border:1px solid {EDGE};}}QPushButton:hover{{background:{EDGE};color:{TEXT};}}")
        cancel.clicked.connect(self.reject)
        confirm = QPushButton("✓  Set as Profile Photo"); confirm.setFixedHeight(40)
        nc = QColor(NEON['normal'][0]); r,g,b = nc.red(),nc.green(),nc.blue()
        confirm.setStyleSheet(f"QPushButton{{background:rgba({r},{g},{b},200);color:{TEXT};border:none;}}QPushButton:hover{{background:rgba({r},{g},{b},255);}}")
        confirm.clicked.connect(self.accept)
        btns.addWidget(cancel); btns.addWidget(confirm)
        lay.addLayout(btns)


class ProfilePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._avatar_path = None
        self._bio_text = "Click here to write something about yourself…"
        layout = QVBoxLayout(self); layout.setContentsMargins(16,16,16,16); layout.setSpacing(12)

        _hrow = QHBoxLayout(); _hrow.setSpacing(10); _hrow.setContentsMargins(0,0,0,0)
        _hrow.addWidget(_make_back_btn(lambda: main_window.go_to(1)), 0, Qt.AlignVCenter)
        self._htitle = QLabel("👤 My Profile"); self._htitle.setFont(F(16, 700))
        self._htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        _hrow.addWidget(self._htitle, 1, Qt.AlignVCenter)
        layout.addLayout(_hrow)

        self._profile_card = QFrame()
        self._profile_card.setStyleSheet(f"QFrame{{background:{PANEL};border:1px solid {EDGE};border-radius:16px;}}")
        card_lay = QVBoxLayout(self._profile_card); card_lay.setContentsMargins(20,20,20,20); card_lay.setSpacing(12)

        top = QHBoxLayout(); top.setSpacing(18)
        self.avatar_zone = _AvatarDropZone(NEON["normal"][0])
        self.avatar_zone.avatar_changed.connect(self._on_avatar_drop)
        top.addWidget(self.avatar_zone, 0, Qt.AlignTop)

        name_col = QVBoxLayout(); name_col.setSpacing(3); name_col.setAlignment(Qt.AlignVCenter)
        self.name_lbl = QLabel("—"); self.name_lbl.setFont(F(20, 700))
        self.name_lbl.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        self.uid_lbl = QLabel("—"); self.uid_lbl.setFont(FM(9))
        self.uid_lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;")
        name_col.addWidget(self.name_lbl); name_col.addWidget(self.uid_lbl)
        top.addLayout(name_col, 1)
        card_lay.addLayout(top)

        self._bio_stack = QStackedWidget()
        self._bio_stack.setStyleSheet("background:transparent;")

        class _ClickLabel(QLabel):
            clicked = Signal()
            def mousePressEvent(self, e):
                if e.button() == Qt.LeftButton: self.clicked.emit()
            def enterEvent(self, e): self.setCursor(Qt.IBeamCursor)
            def leaveEvent(self, e): self.unsetCursor()

        self._bio_label = _ClickLabel(self._bio_text)
        self._bio_label.setFont(F(10)); self._bio_label.setWordWrap(True)
        self._bio_label.setStyleSheet(f"color:{DIM};background:transparent;border:none;padding:4px 2px;")
        self._bio_label.clicked.connect(self._bio_start_edit)

        self._bio_edit = QLineEdit(self._bio_text)
        self._bio_edit.setFont(F(10))
        self._bio_edit.setStyleSheet(f"""
            QLineEdit{{
                color:{TEXT};background:{SURFACE};
                border:1px solid {NEON['normal'][0]};
                border-radius:8px;padding:4px 8px;
            }}
        """)
        self._bio_edit.returnPressed.connect(self._bio_confirm)
        self._bio_edit.editingFinished.connect(self._bio_confirm)

        self._bio_stack.addWidget(self._bio_label)
        self._bio_stack.addWidget(self._bio_edit)
        card_lay.addWidget(self._bio_stack)
        layout.addWidget(self._profile_card)

        rew_row = QHBoxLayout(); rew_row.setSpacing(8)
        rew_icon = QLabel("⭐"); rew_icon.setFont(F(13))
        rew_icon.setStyleSheet("background:transparent;border:none;")
        rew_title = QLabel("Rewards"); rew_title.setFont(F(12, 700))
        rew_title.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        rew_row.addWidget(rew_icon); rew_row.addWidget(rew_title); rew_row.addStretch()
        layout.addLayout(rew_row)
        self._rewards_lbl = QLabel("No rewards yet"); self._rewards_lbl.setFont(F(11))
        self._rewards_lbl.setWordWrap(True)
        self._rewards_lbl.setStyleSheet(f"color:{DIM};background:{PANEL};border:1px solid {EDGE};border-radius:10px;padding:8px 12px;")
        layout.addWidget(self._rewards_lbl)

        chart_title = QLabel("Game Activity"); chart_title.setFont(F(12, 700))
        chart_title.setStyleSheet(f"color:{TEXT};background:transparent;")
        layout.addWidget(chart_title)

        self._chart = _StatsBarChart()
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        scroll.setWidget(self._chart)
        layout.addWidget(scroll, 1)

    def _bio_start_edit(self):
        self._bio_edit.setText(self._bio_text)
        self._bio_stack.setCurrentIndex(1)
        self._bio_edit.setFocus(); self._bio_edit.selectAll()

    def _bio_confirm(self):
        txt = self._bio_edit.text().strip()
        if txt: self._bio_text = txt
        self._bio_label.setText(self._bio_text)
        self._bio_stack.setCurrentIndex(0)
        u = self.main_window.current_user
        if u:
            self.main_window.db.update_bio(u, self._bio_text)
            show_toast(self, "✓  Bio saved", "#3b82f6")

    def _on_avatar_drop(self, path):
        dlg = _ConfirmAvatarDialog(path, self)
        if dlg.exec() == QDialog.Accepted:
            self._avatar_path = path
            self.avatar_zone.set_avatar(path)
            u = self.main_window.current_user
            if u:
                self.main_window.db.update_avatar(u, path)
                show_toast(self, "✓  Profile photo updated", "#3b82f6")

    def refresh(self):
        u_name = self.main_window.current_user
        if not u_name: return
        u = self.main_window.db.get_user(u_name)
        if not u: return
        self.name_lbl.setText(u["user"]); self.uid_lbl.setText(f"UID: {u['uid']}")
        saved_av = u.get("avatar", "")
        if saved_av and os.path.exists(saved_av):
            self.avatar_zone.set_avatar(saved_av)
        saved_bio = u.get("bio", "")
        if saved_bio:
            self._bio_text = saved_bio
            self._bio_label.setText(self._bio_text)
            self._bio_edit.setText(self._bio_text)
        self._chart.set_data([
            ("Normal",   u.get("normal",0), "#3b82f6"),
            ("Flip",     u.get("flip",0),   "#f59e0b"),
            ("Switch",   u.get("switch",0), "#10b981"),
            ("Swap",     u.get("swap",0),   "#ec4899"),
            ("CpTime",   u.get("cpm",0),    "#8b5cf6"),
            ("Stopwatch",u.get("stop",0),   "#06b6d4"),
            ("Pop It",   u.get("pop",0),    "#f97316"),
            ("Focus",    u.get("focus",0),  "#e879f9"),
            ("Chaos",    u.get("chaos",0),  "#ff4d4d"),
            ("Memory",   u.get("memory",0), "#00e5ff"),
            ("Dopamine", u.get("dopa",0),   "#39ff14"),
            ("ColorShift",u.get("rcs",0),   "#a3e635"),
        ])
        rewards = u.get("reward", [])
        self._rewards_lbl.setText("  ".join(rewards) if rewards else "No rewards yet")

    def refresh_theme(self):
        self._htitle.setStyleSheet(f"color:{TEXT};background:transparent;")
        self._profile_card.setStyleSheet(f"QFrame{{background:{PANEL};border:1px solid {EDGE};border-radius:16px;}}")
        self.name_lbl.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        self.uid_lbl.setStyleSheet(f"color:{DIM};background:transparent;border:none;")
        self._bio_label.setStyleSheet(f"color:{DIM};background:transparent;border:none;padding:4px 2px;")
        self._bio_edit.setStyleSheet(f"QLineEdit{{color:{TEXT};background:{SURFACE};border:1px solid {NEON['normal'][0]};border-radius:8px;padding:4px 8px;}}")
        self._rewards_lbl.setStyleSheet(f"color:{DIM};background:{PANEL};border:1px solid {EDGE};border-radius:10px;padding:8px 12px;")
        self.avatar_zone.update()
        self.update()