import os
from PyQt5.QtWidgets import QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer
import numpy as np

class _SuppressStderr:
    def __enter__(self):
        self._old_stderr_fd = os.dup(2)
        self._devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(self._devnull_fd, 2)
    def __exit__(self, *args):
        os.dup2(self._old_stderr_fd, 2)
        os.close(self._devnull_fd)
        os.close(self._old_stderr_fd)

class ToastNotification(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignCenter)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setFixedWidth(300)
        self.hide()
    def show_toast(self, message, duration_ms=3000):
        self.setText(message)
        self.setStyleSheet("""
            QLabel { background-color: rgba(40, 40, 40, 0.95); color: #E0E0E0; border: 1px solid #4A85B8; border-radius: 8px; padding: 12px 16px; font-size: 14px; }
        """)
        self.adjustSize()
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            y = 50
            self.move(x, y)
        self.show()
        QTimer.singleShot(duration_ms, self.hide)

class LoadingSpinner(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.setAlignment(Qt.AlignCenter)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_spinner)
        sp = self.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.setSizePolicy(sp)
        self.hide()
    def start_spinning(self):
        self.angle = 0
        self.timer.start(50)
        self.show()
        self._update_spinner()
    def stop_spinning(self):
        self.timer.stop()
        self.hide()
    def _update_spinner(self):
        self.angle = (self.angle + 15) % 360
        opacity = 0.3 + 0.7 * abs(np.sin(np.radians(self.angle)))
        self.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                border: 3px solid rgba(100, 100, 100, {opacity});
                border-top: 3px solid #4A85B8;
                border-radius: 50%;
            }}
        """)

def _format_size(b):
    if b < 1024: return f"{b} B"
    if b < 1048576: return f"{b/1024:.1f} KB"
    return f"{b/1048576:.1f} MB"
