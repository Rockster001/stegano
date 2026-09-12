import os
from PyQt5.QtWidgets import QLabel, QWidget, QPushButton, QScrollArea, QMainWindow
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPixmap
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

ZOOM_STEP = 0.15
ZOOM_MIN = 0.05
ZOOM_MAX = 5.0

def _format_size(b):
    if b < 1024: return f"{b} B"
    if b < 1048576: return f"{b/1024:.1f} KB"
    return f"{b/1048576:.1f} MB"

class CustomHelpTooltip(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 120)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignCenter)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet("QLabel { background-color: #1a1a2e; color: #E0E0E0; border: 2px solid #4A85B8; border-radius: 8px; padding: 12px 16px; font-size: 14px; }")
        self.hide()

class ZoomImageViewer(QMainWindow):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        with _SuppressStderr():
            self.original_pixmap = QPixmap(image_path)
        self.zoom_factor = 1.0
        self._dragging = False
        self._drag_start_pos = QPoint()
        self._init_ui()
        self._apply_zoom()
    def _init_ui(self):
        self.setWindowTitle("Image Viewer")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setStyleSheet("QMainWindow { background-color: #1a1a1a; }")
        tb = self.addToolBar("Controls")
        tb.setFloatable(False)
        tb.setMovable(False)
        tb.setStyleSheet("QToolBar { background: #252525; border-bottom: 1px solid #444; padding: 4px; } QPushButton { color: #eee; background: #3a3a3a; border: 1px solid #555; padding: 5px 10px; border-radius: 3px; margin: 0 2px; } QPushButton:hover { background: #4a4a4a; } QLabel { color: #ccc; font-weight: bold; padding: 0 6px; }")
        for txt, cmd in [("➖", -ZOOM_STEP), ("➕", ZOOM_STEP), ("⊡ Fit", None), ("◎ Center", None), ("1:1", None), ("⛶ Full", None)]:
            btn = QPushButton(txt)
            if txt == "➖": btn.clicked.connect(lambda _, d=cmd: self._adjust_zoom(d))
            elif txt == "➕": btn.clicked.connect(lambda _, d=cmd: self._adjust_zoom(d))
            elif txt == "⊡ Fit": btn.clicked.connect(self._fit_window)
            elif txt == "◎ Center": btn.clicked.connect(self._center_image)
            elif txt == "1:1": btn.clicked.connect(self._reset_zoom)
            elif txt == "⛶ Full": btn.clicked.connect(self._toggle_fs)
            tb.addWidget(btn)
        self.zoom_lbl = QLabel("100%")
        tb.addSeparator()
        tb.addWidget(self.zoom_lbl)
        self.sa = QScrollArea()
        self.sa.setWidgetResizable(False)
        self.sa.setAlignment(Qt.AlignCenter)
        self.sa.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.sa.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.img_lbl = QLabel()
        self.img_lbl.setAlignment(Qt.AlignCenter)
        self.img_lbl.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.sa.setWidget(self.img_lbl)
        self.setCentralWidget(self.sa)
        self.sa.viewport().installEventFilter(self)
        self.resize(1000, 700)
        self.showNormal()
    def eventFilter(self, obj, event):
        if obj is self.sa.viewport():
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._dragging = True
                self._drag_start_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
            elif event.type() == QEvent.MouseButtonRelease:
                self._dragging = False
                self.setCursor(Qt.ArrowCursor)
            elif event.type() == QEvent.MouseMove and self._dragging:
                dx = event.pos().x() - self._drag_start_pos.x()
                dy = event.pos().y() - self._drag_start_pos.y()
                self.sa.horizontalScrollBar().setValue(self.sa.horizontalScrollBar().value() - dx)
                self.sa.verticalScrollBar().setValue(self.sa.verticalScrollBar().value() - dy)
                self._drag_start_pos = event.pos()
                return True
            elif event.type() == QEvent.Wheel:
                self._adjust_zoom(ZOOM_STEP if event.angleDelta().y() > 0 else -ZOOM_STEP)
                return True
        return super().eventFilter(obj, event)
    def _apply_zoom(self):
        if self.original_pixmap.isNull(): return
        self.zoom_factor = max(ZOOM_MIN, min(ZOOM_MAX, self.zoom_factor))
        w, h = int(self.original_pixmap.width() * self.zoom_factor), int(self.original_pixmap.height() * self.zoom_factor)
        self.img_lbl.setPixmap(self.original_pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.img_lbl.setMinimumSize(w, h)
        self.img_lbl.setMaximumSize(w, h)
        self.zoom_lbl.setText(f"{int(self.zoom_factor*100)}%")
    def _adjust_zoom(self, delta):
        self.zoom_factor += delta
        self._apply_zoom()
    def _fit_window(self):
        if self.original_pixmap.isNull(): return
        vw, vh = self.sa.viewport().width(), self.sa.viewport().height()
        self.zoom_factor = min(vw / self.original_pixmap.width(), vh / self.original_pixmap.height())
        self._apply_zoom()
        self._center_image()
    def _reset_zoom(self):
        self.zoom_factor = 1.0
        self._apply_zoom()
    def _center_image(self):
        hbar = self.sa.horizontalScrollBar()
        vbar = self.sa.verticalScrollBar()
        hbar.setValue(int((hbar.maximum() - hbar.minimum()) / 2))
        vbar.setValue(int((vbar.maximum() - vbar.minimum()) / 2))
    def _toggle_fs(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape: self.close()
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal): self._adjust_zoom(ZOOM_STEP)
        elif event.key() == Qt.Key_Minus: self._adjust_zoom(-ZOOM_STEP)
        elif event.key() == Qt.Key_0: self._reset_zoom()
        elif event.key() == Qt.Key_C: self._center_image()
        elif event.key() == Qt.Key_F: self._fit_window()
        elif event.key() == Qt.Key_Space: self._toggle_fs()
        else: super().keyPressEvent(event)
