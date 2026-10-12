"how do i use qstackwidget klao help"

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow,
                            QWidget, QStackedWidget,
                            QVBoxLayout, QHBoxLayout, QGridLayout,
                            QPushButton, QLineEdit, QSpinBox, QTextEdit, QSlider, QLabel,
                            QMenu, QMenuBar,
                               )
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Setting")
        self.setFixedSize(400,600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.stack = QStackedWidget(self.central_widget)


        self.page_main = Setting_Main()
        self.page_video = Setting_Video()
        self.page_sound = Setting_Sound()


        self.stack.addWidget(self.page_main)
        self.stack.addWidget(self.page_video)
        self.stack.addWidget(self.page_sound)


        self.page_main.button_video.clicked.connect(lambda: self.go_to(1))

    def go_to(self, a):
        self.stack.setCurrentIndex(a)

class Setting_Main(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        button_go_back = QPushButton("<")
        layout.addWidget(button_go_back, alignment=Qt.AlignmentFlag.AlignLeft)

        self.button_video = QPushButton("Video Setting")
        layout.addWidget(self.button_video, alignment=Qt.AlignmentFlag.AlignCenter)

        self.button_sound = QPushButton("Sound Setting")
        layout.addWidget(self.button_sound, alignment=Qt.AlignmentFlag.AlignCenter)

class Setting_Video(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        button_go_back = QPushButton("<")
        layout.addWidget(button_go_back, alignment=Qt.AlignmentFlag.AlignLeft)

class Setting_Sound(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        button_go_back = QPushButton("<")
        layout.addWidget(button_go_back, alignment=Qt.AlignmentFlag.AlignLeft)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())