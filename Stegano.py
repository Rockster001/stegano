import sys
import os
import logging
import re
import html
import wave
import hashlib
import itertools
import platform
from datetime import datetime
import numpy as np
import secrets
from steganography_utils import _encrypt_bytes_aes, _decrypt_bytes_aes, _encrypt_bytes, encode_image, encode_dual_image, decode_image, decode_dual_image, _embed_bits_and_save, _extract_raw_lsb_bytes, detect_message_format, _extract_dual_layers, _try_decrypt_payload
from PIL import Image, ExifTags
from PyQt5.QtGui import QColor, QPalette, QFontMetrics, QKeySequence
os.environ["QT_LOGGING_RULES"] = ".warning=false;qt.qpa.=false;libpng.*=false"
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, QLabel, QPushButton,
    QTextBrowser, QFileDialog, QFrame, QMessageBox, QTextEdit, QLineEdit,
    QScrollArea, QSlider, QSizePolicy, QToolBar, QProgressBar, QMenu, QAction, QListWidget, QShortcut, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QSettings, QUrl, QEvent, QPoint, QMargins
from PyQt5.QtGui import QFont, QPixmap, QCursor, QDesktopServices, QIcon
from PyQt5.QtMultimedia import QSoundEffect, QMediaPlayer, QMediaContent
from audio_manager import AudioManager
from password_utils import (
    estimate_password_strength,
    PasswordStrengthMeter,
    SavedPasswordsDialog
)
from ui_components import (
    ToastNotification,
    LoadingSpinner,
    _SuppressStderr,
    CustomHelpTooltip,
    ZoomImageViewer,
    convert_links_to_html
)
from workers import EncodeWorker, DecodeWorker, ImageLoadWorker


VERSION = os.path.basename(__file__).replace("Stegano", "").replace(".py", "")
STEALTH_HEADER = hashlib.sha256(b"STEGO_MAGIC").digest()
LEGACY_HEADER = b"STEGO_MAGIC"
DUAL_HEADER = hashlib.sha256(b"STEGO_DUAL_MAGIC").digest()
DELIMITER = "\x00\x00\x03"
THUMBNAIL_SIZE = 128
MIN_FONT_SIZE = 10
MAX_FONT_SIZE = 48
FONT_STEP = 2
DEFAULT_FONT_SIZE = 18
TOOLTIP_WIDTH = 400
TOOLTIP_HEIGHT = 120
TOOLTIP_DELAY_MS = 150
MAX_SAVED_PASSWORDS = 10
MAX_FILE_SIZE_MB = 50
WATERMARK_MIN_SIZE = 16
WATERMARK_MAX_SIZE = 800
WATERMARK_REF_SIZE = 100
WATERMARK_MIN_SCALE = 0.1
WATERMARK_MAX_SCALE = 5.0
ZOOM_STEP = 0.15
ZOOM_MIN = 0.05
ZOOM_MAX = 5.0
AES_KEY_SIZE = 32
AES_SALT_SIZE = 16
AES_IV_SIZE = 16
PBKDF2_ITERATIONS = 100000
TOAST_DURATION_MS = 3000

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s")
logger = logging.getLogger("Stegano")


APP_STYLESHEET = """
QWidget { background-color: transparent; color: #E0E0E0; font-family: "Segoe UI", sans-serif; }
QMainWindow { background-color: transparent; }
QLabel { color: #E0E0E0; font-size: 14px; }
QLabel#TitleText { color: #FFFFFF; font-size: 18px; font-weight: bold; } 
QLabel#Watermark { color: rgba(255, 255, 255, 0.18); font-weight: bold; }
QLabel#StatusText { color: #FFFFFF; font-size: 13px; }
QLabel#CounterText { color: #CCCCCC; font-size: 12px; text-align: right; }
QPushButton { background-color: #366B93; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-size: 13px; font-weight: bold; min-width: 100px; }
QPushButton:hover { background-color: #4A85B8; }
QPushButton:pressed { background-color: #2C547A; }
QPushButton:disabled { background-color: #444444; color: #777777; }
QPushButton#CloseBtn { background-color: transparent; color: #CCCCCC; border: none; font-size: 16px; min-width: 30px; padding: 0; margin: 0; }
QPushButton#CloseBtn:hover { background-color: #E81123; color: white; border-radius: 4px; }
QPushButton#HelpBtn { background-color: transparent; color: #CCCCCC; border: 1px solid #555; font-size: 14px; font-weight: bold; min-width: 28px; max-width: 28px; padding: 2px; border-radius: 14px; }
QPushButton#HelpBtn:hover { background-color: #4A85B8; color: white; border-color: #4A85B8; }
QPushButton#HelpBtnActive { background-color: #4CAF50; color: white; border: 1px solid #66BB6A; font-size: 14px; font-weight: bold; min-width: 28px; max-width: 28px; padding: 2px; border-radius: 14px; }
QPushButton#HelpBtnActive:hover { background-color: #66BB6A; }
QPushButton#MetaToggleBtn { background-color: #4A85B8; color: white; border: 1px solid #555; font-size: 14px; font-weight: bold; border-radius: 4px; padding: 4px 8px; min-width: 32px; min-height: 28px; }
QPushButton#MetaToggleBtn:hover { background-color: #5A9AC8; }
QPushButton#MetaToggleBtn:pressed { background-color: #3A6B98; }
QTextEdit, QTextBrowser { background-color: rgba(30, 30, 30, 0.85); color: #E0E0E0; border: 1px solid rgba(100, 100, 100, 0.5); border-radius: 6px; padding: 12px; selection-background-color: #366B93; }
QLineEdit { background-color: rgba(30, 30, 30, 0.85); color: #E0E0E0; border: 1px solid rgba(100, 100, 100, 0.5); border-radius: 4px; padding: 6px 8px; font-size: 13px; }
QLineEdit:focus { border: 1px solid #4A85B8; }
QFrame#Card { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(25, 25, 25, 0.85), stop:1 rgba(40, 40, 40, 0.85)); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1); }
QFrame#TitleBar { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(35, 35, 35, 0.9), stop:1 rgba(50, 50, 50, 0.9)); border-bottom: 1px solid rgba(85, 85, 85, 0.8); }
QScrollBar:vertical, QScrollBar:horizontal { background: rgba(50, 50, 50, 0.8); border: none; border-radius: 4px; margin: 2px; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background: rgba(100, 100, 100, 0.7); min-height: 20px; border-radius: 4px; }
QScrollBar::handle:hover { background: rgba(130, 130, 130, 0.9); }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QSlider::groove:horizontal { background: rgba(100,100,100, 0.7); height: 4px; border-radius: 2px; }
QSlider::handle:horizontal { background: #366B93; width: 12px; margin: -5px 0; border-radius: 6px; }
QSlider::handle:horizontal:hover { background: #4CAF50; }
QProgressBar { border: 1px solid rgba(100, 100, 100, 0.5); border-radius: 4px; background-color: rgba(30, 30, 30, 0.85); text-align: center; }
QProgressBar::chunk { background-color: #4CAF50; border-radius: 3px; }
QListWidget { background-color: rgba(30, 30, 30, 0.85); border: 1px solid rgba(100, 100, 100, 0.5); border-radius: 4px; }
QListWidget::item { padding: 8px; color: #E0E0E0; }
QListWidget::item:hover { background-color: rgba(74, 133, 184, 0.3); }
QListWidget::item:selected { background-color: rgba(74, 133, 184, 0.6); }
QDialog { background-color: #1e1e1e; color: #E0E0E0; }
"""



_COMMON_WEAK_WORDS = {
    "password", "letmein", "login", "admin", "welcome", "qwerty", "dragon",
    "master", "shadow", "monkey", "sunshine", "princess", "football",
    "baseball", "iloveyou", "trustno1", "superman", "batman", "starwars",
    "freedom", "whatever", "hunter", "killer", "george", "jennifer",
    "michael", "jordan", "hannah", "thomas", "robert", "daniel", "william",
    "charlie", "ninja", "pokemon", "minecraft", "summer", "winter",
    "spring", "autumn", "monday", "friday", "computer", "internet",
    "changeme", "default", "guest", "test", "temp", "secret", "abc",
    "abcd", "abcde", "abcdef", "access", "flower", "purple", "orange",
    "yellow", "cricket", "soccer", "hockey", "tennis", "chelsea",
    "arsenal", "liverpool", "united", "eagles", "cowboys", "yankees",
}

_KEYBOARD_ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm", "1234567890"]

def _has_repeated_char_run(password, run_length=3):
    count = 1
    for i in range(1, len(password)):
        if password[i] == password[i - 1]:
            count += 1
            if count >= run_length:
                return True
        else:
            count = 1
    return False

def _has_sequential_run(password, run_length=3):
    if len(password) < run_length:
        return False
    for i in range(len(password) - run_length + 1):
        chunk = password[i:i + run_length]
        ascending = all(ord(chunk[j + 1]) - ord(chunk[j]) == 1 for j in range(len(chunk) - 1))
        descending = all(ord(chunk[j]) - ord(chunk[j + 1]) == 1 for j in range(len(chunk) - 1))
        if ascending or descending:
            return True
    return False

def _has_keyboard_pattern(password, min_len=4):
    lowered = password.lower()
    for row in _KEYBOARD_ROWS:
        for i in range(len(row) - min_len + 1):
            chunk = row[i:i + min_len]
            if chunk in lowered or chunk[::-1] in lowered:
                return True
    return False

def _extract_alpha_runs(password):
    runs, current = [], ""
    for c in password:
        if c.isalpha():
            current += c
        else:
            if current: runs.append(current)
            current = ""
    if current: runs.append(current)
    return runs

def _has_common_word(password):
    return any(run.lower() in _COMMON_WEAK_WORDS for run in _extract_alpha_runs(password) if len(run) >= 4)

def _has_pattern_weakness(password):
    return (_has_common_word(password) or _has_keyboard_pattern(password)
            or _has_repeated_char_run(password) or _has_sequential_run(password))

def estimate_password_strength(password):
    if not password:
        return 0
    length_score = min(len(password), 20) / 20 * 60
    upper = sum(1 for c in password if c.isupper())
    digit = sum(1 for c in password if c.isdigit())
    symbol = sum(1 for c in password if not c.isalnum())
    diversity_score = sum(min(count, 3) / 3 * (40 / 3) for count in (upper, digit, symbol))
    score = length_score + diversity_score
    if _has_pattern_weakness(password):
        score = min(score, 30)
    return min(int(round(score)), 100)

def _password_strength_tier(score):
    if score <= 0: return 0
    if score < 20: return 1
    if score < 40: return 2
    if score < 60: return 3
    if score < 80: return 4
    return 5

class PasswordStrengthMeter(QWidget):
    TIER_COLORS = ["#666666", "#FF4444", "#FF4444", "#FFA500", "#4CAF50", "#4CAF50"]
    TIER_LABELS = ["No password", "Very Weak", "Weak", "Fair", "Strong", "Very Strong"]
    BOX_COUNT = 5
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        self.boxes = []
        for _ in range(self.BOX_COUNT):
            box = QLabel()
            box.setFixedSize(14, 10)
            box.setStyleSheet("background-color: rgba(100, 100, 100, 0.3); border-radius: 2px;")
            layout.addWidget(box)
            self.boxes.append(box)
    def update_strength(self, password):
        score = estimate_password_strength(password)
        tier = _password_strength_tier(score)
        color = self.TIER_COLORS[tier]
        for i, box in enumerate(self.boxes):
            if i < tier:
                box.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
            else:
                box.setStyleSheet("background-color: rgba(100, 100, 100, 0.3); border-radius: 2px;")
        self.setToolTip(self.TIER_LABELS[tier])


class SavedPasswordsDialog(QDialog):
    def __init__(self, passwords, parent=None):
        super().__init__(parent)
        self.passwords = list(passwords)
        self.selected_password = None
        self.setWindowTitle("Saved Passwords")
        self.setFixedSize(400, 350)
        self._init_ui()
        self._populate_list()
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        header = QLabel("Double-click a password to use it, or select and click Use")
        header.setStyleSheet("font-size: 12px; color: #888; margin-bottom: 5px;")
        layout.addWidget(header)
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_use)
        layout.addWidget(self.list_widget)
        button_layout = QHBoxLayout()
        self.use_btn = QPushButton("Use")
        self.use_btn.setFixedWidth(80)
        self.use_btn.clicked.connect(self._on_use_selected)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setFixedWidth(80)
        self.delete_btn.clicked.connect(self._on_delete)
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setFixedWidth(100)
        self.clear_btn.clicked.connect(self._on_clear_all)
        self.close_btn = QPushButton("Close")
        self.close_btn.setFixedWidth(80)
        self.close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.use_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)
    def _populate_list(self):
        self.list_widget.clear()
        for pwd in self.passwords:
            masked = pwd[:4] + "••••" if len(pwd) > 4 else pwd
            self.list_widget.addItem(masked)
    def _on_use(self, item):
        row = self.list_widget.row(item)
        if 0 <= row < len(self.passwords):
            self.selected_password = self.passwords[row]
            self.accept()
    def _on_use_selected(self):
        item = self.list_widget.currentItem()
        if item:
            self._on_use(item)
        else:
            QMessageBox.information(self, "No Selection", "Select a password from the list first.")
    def _on_delete(self):
        item = self.list_widget.currentItem()
        if item:
            row = self.list_widget.row(item)
            if 0 <= row < len(self.passwords):
                self.passwords.pop(row)
                self._populate_list()
    def _on_clear_all(self):
        reply = QMessageBox.question(
            self, "Clear All",
            "Remove all saved passwords?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.passwords = []
            self._populate_list()

def estimate_encrypted_payload_len(raw_len):
    padded_len = ((raw_len // 16) + 1) * 16
    return AES_SALT_SIZE + AES_IV_SIZE + padded_len

def check_image_for_message(img_path, delim):
    try:
        img = Image.open(img_path).convert("RGB")
        arr = np.array(img)
        flat = arr.reshape(-1) & 1
        usable_len = (flat.size // 8) * 8
        if usable_len == 0: return False, False
        raw_bytes = np.packbits(flat[:usable_len]).tobytes()
        delim_bytes = delim.encode("utf-8")
        idx_stealth = raw_bytes.find(STEALTH_HEADER)
        idx_legacy = raw_bytes.find(LEGACY_HEADER)
        if idx_stealth != -1:
            idx = idx_stealth; header_len = len(STEALTH_HEADER)
        elif idx_legacy != -1:
            idx = idx_legacy; header_len = len(LEGACY_HEADER)
        else:
            return False, False
        payload_start = idx + header_len
        d_idx = raw_bytes[payload_start:].find(delim_bytes)
        if d_idx == -1: return False, False
        payload_bytes = raw_bytes[payload_start : payload_start + d_idx]
        try:
            payload_bytes.decode("utf-8")
            return True, False
        except UnicodeDecodeError:
            return True, True
    except Exception:
        return False, False

class SteganographyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Steganosaurus", "SteganoApp")
        self.magic_header = STEALTH_HEADER
        self.delimiter = DELIMITER
        self.current_image_path = ""
        self.available_capacity_bits = 0
        self.worker_running = False
        self.original_message = ""
        self.meta_font_size = DEFAULT_FONT_SIZE
        self.text_font_size = DEFAULT_FONT_SIZE
        self.dragging = False
        self.offset = None
        self.encoderWorker = self.decoderWorker = self.loaderWorker = None
        self._pending_load_path = ""
        self._last_focused_pwd_field = None
        self._layer2_active = False
        self._editing_layer = 1
        self._message1_buffer = ""
        self._message2_buffer = ""
        self._decoded_layer1_message = ""
        self._currently_shown_layer = 0
        self.audio = AudioManager()
        self.help_mode_active = False
        self._tooltip_map = {}
        self.help_tooltip = QLabel()
        self.help_tooltip.setFixedSize(400, 120)
        self.help_tooltip.setWordWrap(True)
        self.help_tooltip.setAlignment(Qt.AlignCenter)
        self.help_tooltip.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.help_tooltip.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.help_tooltip.setStyleSheet("QLabel { background-color: #1a1a2e; color: #E0E0E0; border: 2px solid #4A85B8; border-radius: 8px; padding: 12px 16px; font-size: 14px; }")
        self.help_tooltip.hide()
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.setInterval(QApplication.doubleClickInterval())
        self._click_timer.timeout.connect(self._handle_thumb_single_click)
        self.active_viewer = None
        self._saved_passwords = self._load_saved_passwords()
        self.toast_notification = ToastNotification(self)
        self.loading_spinner = LoadingSpinner(self)
        self.password_strength_indicator = PasswordStrengthMeter(self)
        self.capacity_progress_bar = QProgressBar()
        self.capacity_progress_bar.setFixedHeight(8)
        self.capacity_progress_bar.setFixedWidth(80)
        self.capacity_progress_bar.setTextVisible(False)
        self.capacity_progress_bar.setStyleSheet("QProgressBar { border: none; background-color: rgba(100, 100, 100, 0.3); border-radius: 4px; } QProgressBar::chunk { background-color: #4CAF50; border-radius: 4px; }")
        self.capacity_percent_label = QLabel("0%", styleSheet="color:#ccc; min-width:32px;")
        self._previous_music_volume = 60
        self._is_muted = False
        self.setAcceptDrops(True)
        self._init_ui()
        QTimer.singleShot(500, self._update_watermark)
        self._restore_window_state()

    def _has_unsaved_changes(self):
        if not hasattr(self, 'save_btn') or not self.save_btn.isVisible():
            return False
        current_layer1 = (self.text_area.toPlainText() if self._editing_layer == 1 else self._message1_buffer).strip()
        current_layer2 = (self.text_area.toPlainText() if self._editing_layer == 2 else self._message2_buffer).strip()
        if not current_layer1 and not current_layer2:
            return False
        if current_layer2:
            return True
        return current_layer1 != self.original_message

    def closeEvent(self, event):
        if self._has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Unsaved Message",
                "You have a message that hasn't been saved into an image yet. Quit anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
        self._cleanup_workers()
        self.settings.setValue("geometry", self.saveGeometry())
        self._persist_saved_passwords()
        self.settings.sync()
        event.accept()

    def _get_local_key(self):
        seed = (platform.node() + "steganosaurus-local").encode()
        return hashlib.sha256(seed).digest()

    def _load_saved_passwords(self):
        stored = self.settings.value("savedPasswords", [], type=list)
        key_hex = self._get_local_key().hex()
        result = []
        for item in stored:
            try:
                decrypted = _decrypt_bytes_aes(bytes.fromhex(item), key_hex)
                if decrypted is not None:
                    result.append(decrypted.decode("utf-8"))
            except Exception:
                continue
        return result

    def _persist_saved_passwords(self):
        key_hex = self._get_local_key().hex()
        encrypted_list = []
        for pwd in self._saved_passwords:
            try:
                encrypted_list.append(_encrypt_bytes_aes(pwd.encode("utf-8"), key_hex).hex())
            except Exception:
                continue
        self.settings.setValue("savedPasswords", encrypted_list)

    def _restore_window_state(self):
        screen = QApplication.primaryScreen()
        fs_geometry = screen.geometry()
        self.setGeometry(fs_geometry)
        # Both a maximum AND a minimum, locked to the exact screen size -
        # permanently fullscreen means the window truly can't be resized
        # at all in either direction, not just capped from growing.
        self.setMaximumSize(fs_geometry.width(), fs_geometry.height())
        self.setMinimumSize(fs_geometry.width(), fs_geometry.height())
        self.showFullScreen()

    def _toggle_metadata_panel(self):
        if self.meta_content.isVisible():
            self.meta_content.hide()
            self.meta_toggle_btn.setText("▲")
        else:
            self.meta_content.show()
            self.meta_toggle_btn.setText("▼")

    def _update_undo_redo_buttons(self):
        if hasattr(self, 'undo_btn') and hasattr(self, 'redo_btn'):
            self.undo_btn.setEnabled(self.text_area.document().isUndoAvailable())
            self.redo_btn.setEnabled(self.text_area.document().isRedoAvailable())

    def _show_text_context_menu(self, pos):
        menu = QMenu(self)
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self._copy_message)
        menu.addAction(copy_action)
        select_all_action = QAction("Select All", self)
        select_all_action.triggered.connect(self.text_area.selectAll)
        menu.addAction(select_all_action)
        if not self.text_area.isReadOnly():
            menu.addSeparator()
            clear_action = QAction("Clear", self)
            clear_action.triggered.connect(self.text_area.clear)
            menu.addAction(clear_action)
        menu.exec_(self.text_area.mapToGlobal(pos))

    def _validate_file_size(self, file_path):
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB: return False, f"File too large ({file_size_mb:.1f}MB). Maximum size is {MAX_FILE_SIZE_MB}MB."
            return True, ""
        except OSError as e:
            return False, f"Cannot access file: {str(e)}"

    def _cleanup_workers(self):
        for w in [self.encoderWorker, self.decoderWorker, self.loaderWorker]:
            if w and w.isRunning(): w.wait()

    def _save_password_to_list(self, password):
        if not password:
            return
        if password in self._saved_passwords:
            self._saved_passwords.remove(password)
        self._saved_passwords.insert(0, password)
        self._saved_passwords = self._saved_passwords[:MAX_SAVED_PASSWORDS]
        self._persist_saved_passwords()

    def _show_saved_passwords_dialog(self):
        self.audio.play_sfx('click')
        dialog = SavedPasswordsDialog(self._saved_passwords, self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_password:
            target = self._last_focused_pwd_field if self._last_focused_pwd_field in (self.pwd_input, self.pwd_input2) else self.pwd_input
            target.setText(dialog.selected_password)
            if self.current_image_path and os.path.exists(self.current_image_path):
                QTimer.singleShot(100, self._attempt_decode)
        self._saved_passwords = dialog.passwords
        self._persist_saved_passwords()

    def resizeEvent(self, event):
        if hasattr(self, 'background') and self.background:
            cw = self.centralWidget()
            if cw:
                self.container.resize(cw.size())
                self.background.resize(cw.size())
        QTimer.singleShot(100, self._update_watermark)
        super().resizeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(200, self._update_watermark)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and hasattr(self, 'title_bar') and event.y() <= self.title_bar.height():
            self.dragging = True
            self.offset = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and self.offset:
            self.move(event.globalPos() - self.offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp')):
                    event.acceptProposedAction()
                    if hasattr(self, 'ws_frame'):
                        self.ws_frame.setStyleSheet("QFrame#Card { background-color: rgba(74, 133, 184, 0.3); border: 2px dashed #4A85B8; border-radius: 8px; }")
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        if hasattr(self, 'ws_frame'): self.ws_frame.setStyleSheet("")
        event.accept()

    def dropEvent(self, event):
        if hasattr(self, 'ws_frame'): self.ws_frame.setStyleSheet("")
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp')):
                    self.audio.play_sfx('click')
                    self._load_image(path)
                    self.toast_notification.show_toast(f"Loaded: {os.path.basename(path)}")
                    event.acceptProposedAction()
                    return
        event.ignore()

    def _register_tooltip(self, widget, text):
        self._tooltip_map[widget] = text
        widget.setAttribute(Qt.WA_Hover)
        widget.installEventFilter(self)

    def _retain_size_when_hidden(self, widget):
        sp = widget.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        widget.setSizePolicy(sp)

    def _toggle_help_mode(self):
        self.help_mode_active = not self.help_mode_active
        self.audio.play_sfx('click')
        if self.help_mode_active:
            self.help_btn.setObjectName("HelpBtnActive")
            self.help_btn.setText("?")
            self.setCursor(Qt.WhatsThisCursor)
            self._enable_panel_tooltips(True)
        else:
            self.help_btn.setObjectName("HelpBtn")
            self.help_btn.setText("?")
            self.setCursor(Qt.ArrowCursor)
            self.help_tooltip.hide()
            self._enable_panel_tooltips(False)
        self.help_btn.style().unpolish(self.help_btn)
        self.help_btn.style().polish(self.help_btn)

    def _enable_panel_tooltips(self, enable):
        panels_to_toggle = [
            (self.meta_display, "Shows file information, dimensions, capacity, and EXIF data for the loaded image."),
            (self.text_area, "Displays decoded messages or enter text to encode. Click text to start editing. Click links to open in browser."),
            (self.thumb, "Preview of the loaded image. Click to view full size. Double-click to load a new image. You can also drag-and-drop an image here."),
            (self.pwd_input, "Enter password for AES-256 encryption. Leave empty for no encryption."),
            (self.capacity_progress_bar, "Shows message capacity usage. Green = safe, Yellow = warning, Red = full."),
        ]
        if hasattr(self, 'pwd_memory_btn'):
            panels_to_toggle.append((self.pwd_memory_btn, "View and manage saved passwords. Passwords are automatically saved when used."))
        for widget, tooltip_text in panels_to_toggle:
            if enable: widget.setToolTip(tooltip_text)
            else: widget.setToolTip("")

    def _position_tooltip(self, obj):
        screen = QApplication.primaryScreen().geometry()
        tooltip_width = self.help_tooltip.width()
        tooltip_height = self.help_tooltip.height()
        widget_pos = obj.mapToGlobal(QPoint(0, 0))
        widget_width = obj.width()
        widget_height = obj.height()
        x = widget_pos.x() + (widget_width // 2) - (tooltip_width // 2)
        y = widget_pos.y() + widget_height + 10
        if x + tooltip_width > screen.right(): x = screen.right() - tooltip_width - 10
        if x < screen.left(): x = screen.left() + 10
        if y + tooltip_height > screen.bottom(): y = widget_pos.y() - tooltip_height - 10
        if y < screen.top(): y = screen.top() + 10
        self.help_tooltip.move(x, y)

    def _setup_bg(self, container):
        self.background = QLabel(container)
        self.background.setScaledContents(True)
        self.background.lower()
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "STEGANO.png")
        if os.path.exists(p):
            with _SuppressStderr():
                pix = QPixmap(p)
            self.background.setPixmap(pix) if not pix.isNull() else self.background.setStyleSheet("background:#1a1a1a")
        else:
            self.background.setStyleSheet("background:#1a1a1a")
        self.background.resize(container.size())

    def _update_watermark(self):
        if not hasattr(self, 'watermark') or not hasattr(self, 'ws_frame'): return
        text = self.watermark.text()
        if not text: return
        self.watermark.updateGeometry()
        self.ws_frame.updateGeometry()
        if self.ws_frame.layout(): self.ws_frame.layout().update()
        frame_rect = self.ws_frame.rect()
        margins = self.ws_frame.layout().contentsMargins() if self.ws_frame.layout() else QMargins(15, 15, 15, 15)
        controls_height = 60
        target_w = frame_rect.width() - margins.left() - margins.right() - 60
        target_h = frame_rect.height() - margins.top() - margins.bottom() - controls_height - 60
        if target_w <= 0 or target_h <= 0:
            window_rect = self.rect()
            target_w = max(200, window_rect.width() * 0.8)
            target_h = max(100, window_rect.height() * 0.5)
            if target_w <= 0 or target_h <= 0: target_w = 800; target_h = 400
        ref_size = WATERMARK_REF_SIZE
        font = QFont("Segoe UI", ref_size, QFont.Bold)
        font.setPixelSize(ref_size)
        font.setKerning(False)
        metrics = QFontMetrics(font)
        rect = metrics.boundingRect(text)
        if rect.width() == 0 or rect.height() == 0: return
        scale_w = target_w / rect.width() if rect.width() > 0 else 1.0
        scale_h = target_h / rect.height() if rect.height() > 0 else 1.0
        scale = min(scale_w, scale_h)
        scale = max(WATERMARK_MIN_SCALE, min(WATERMARK_MAX_SCALE, scale))
        final_size = int(ref_size * scale)
        final_size = max(WATERMARK_MIN_SIZE, min(final_size, WATERMARK_MAX_SIZE))
        font.setPixelSize(final_size)
        self.watermark.setFont(font)
        self.watermark.setStyleSheet(f"color: rgba(255, 255, 255, 0.18); background: transparent; font-size: {final_size}px;")

    def _format_size(self, b):
        if b < 1024: return f"{b} B"
        if b < 1048576: return f"{b/1024:.1f} KB"
        return f"{b/1048576:.1f} MB"

    def _show_keyboard_shortcuts(self):
        shortcuts_text = """
<h2 style='color: #4A85B8;'>Keyboard Shortcuts</h2>
<table style='color: #E0E0E0; border-collapse: collapse;'>
<tr><td style='padding: 8px; border-bottom: 1px solid #444;'><b>Ctrl+S</b></td><td style='padding: 8px; border-bottom: 1px solid #444;'>Save / Encode message</td></tr>
<tr><td style='padding: 8px; border-bottom: 1px solid #444;'><b>Ctrl+Scroll</b></td><td style='padding: 8px; border-bottom: 1px solid #444;'>Zoom text in/out</td></tr>
<tr><td style='padding: 8px; border-bottom: 1px solid #444;'><b>Escape</b></td><td style='padding: 8px; border-bottom: 1px solid #444;'>Close viewer / Cancel</td></tr>
<tr><td style='padding: 8px; border-bottom: 1px solid #444;'><b>Enter</b></td><td style='padding: 8px; border-bottom: 1px solid #444;'>Decode with password</td></tr>
</table>
<h3 style='color: #4A85B8; margin-top: 20px;'>Image Viewer Shortcuts</h3>
<table style='color: #E0E0E0; border-collapse: collapse;'>
<tr><td style='padding: 8px; border-bottom: 1px solid #444;'><b>+ / -</b></td><td style='padding: 8px; border-bottom: 1px solid #444;'>Zoom in/out</td></tr>
<tr><td style='padding: 8px; border-bottom: 1px solid #444;'><b>0</b></td><td style='padding: 8px; border-bottom: 1px solid #444;'>Reset zoom to 100%</td></tr>
<tr><td style='padding: 8px; border-bottom: 1px solid #444;'><b>C</b></td><td style='padding: 8px; border-bottom: 1px solid #444;'>Center image</td></tr>
<tr><td style='padding: 8px; border-bottom: 1px solid #444;'><b>F</b></td><td style='padding: 8px; border-bottom: 1px solid #444;'>Fit to window</td></tr>
<tr><td style='padding: 8px; border-bottom: 1px solid #444;'><b>Space</b></td><td style='padding: 8px; border-bottom: 1px solid #444;'>Toggle fullscreen</td></tr>
<tr><td style='padding: 8px; border-bottom: 1px solid #444;'><b>Mouse Wheel</b></td><td style='padding: 8px; border-bottom: 1px solid #444;'>Zoom in/out</td></tr>
<tr><td style='padding: 8px; border-bottom: 1px solid #444;'><b>Drag</b></td><td style='padding: 8px; border-bottom: 1px solid #444;'>Pan image</td></tr>
</table>
"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setTextFormat(Qt.RichText)
        msg.setText(shortcuts_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setStyleSheet("QMessageBox { background-color: #1a1a1a; } QLabel { color: #E0E0E0; } QPushButton { background-color: #366B93; color: white; border: none; padding: 8px 16px; border-radius: 4px; } QPushButton:hover { background-color: #4A85B8; }")
        msg.exec_()

    def _extract_metadata(self, path):
        if not path or not os.path.exists(path): return "<i>No image loaded</i>"
        try:
            img = Image.open(path)
            exif = img.getexif()
            lines = [
                f"<b>File:</b> {os.path.basename(path)}",
                f"<b>Size:</b> {self._format_size(os.path.getsize(path))}",
                f"<b>Dimensions:</b> {img.width} × {img.height} px",
                f"<b>Mode:</b> {img.mode}",
                f"<b>Format:</b> {img.format or 'Unknown'}",
                f"<b>Capacity:</b> {self._format_size(self.available_capacity_bits // 8)} ({(self.available_capacity_bits // 8):,} chars)",
                "<hr style='border-color:#444'>",
                "<b>EXIF / Metadata:</b>"
            ]
            if exif:
                for tag_id, val in exif.items():
                    try:
                        tag_name = html.escape(str(ExifTags.TAGS.get(tag_id, str(tag_id))))
                        v = html.escape(str(val))
                        lines.append(f"• {tag_name}: {v[:60]}{'...' if len(v) > 60 else ''}")
                    except Exception as e:
                        logger.debug(f"Skipping unreadable EXIF tag {tag_id}: {e}")
                        continue
            else:
                lines.append("• No EXIF data found.")
            return "<br>".join(lines)
        except Exception as e:
            return f"<i>Error: {str(e)}</i>"

    def _init_ui(self):
        self.setWindowTitle(f"Stegano {VERSION}")
        self.setStyleSheet(APP_STYLESHEET)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.resize(850, 650)
        cw = QWidget()
        cw.setStyleSheet("background:transparent")
        self.setCentralWidget(cw)
        ml = QVBoxLayout(cw)
        ml.setContentsMargins(0, 0, 0, 0)
        self.container = QWidget(cw)
        self.container.setAttribute(Qt.WA_TranslucentBackground, True)
        self.container.setStyleSheet("background:transparent")
        self.container.resize(self.size())
        self._setup_bg(self.container)
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self._handle_save_shortcut)
        tf = QFrame()
        tf.setObjectName("TitleBar")
        tl = QHBoxLayout(tf)
        tl.setContentsMargins(10, 6, 10, 6)
        title_label = QLabel(f"Stegano {VERSION}", objectName="TitleText")
        tl.addWidget(title_label)
        tl.addStretch()
        self.music_mute_btn = QPushButton("🎵 Music")
        self.music_mute_btn.setFixedHeight(34)
        self.music_mute_btn.setStyleSheet("QPushButton { background-color: #4A85B8; color: white; border: 1px solid #366B93; border-radius: 4px; font-size: 13px; font-weight: bold; padding: 0 12px; } QPushButton:hover { background-color: #5A9AC8; } QPushButton:pressed { background-color: #3A6B98; }")
        self.music_mute_btn.clicked.connect(self._toggle_mute)
        self._register_tooltip(self.music_mute_btn, "Click to mute/unmute background music")
        tl.addWidget(self.music_mute_btn)
        self.mus_vol = QSlider(Qt.Horizontal)
        self.mus_vol.setFixedWidth(100)
        self.mus_vol.setRange(0, 100)
        self.mus_vol.setValue(60)
        self.mus_vol.valueChanged.connect(self._on_slider_changed)
        tl.addWidget(self.mus_vol)
        self._register_tooltip(self.mus_vol, "Drag to adjust music volume")
        self.mus_vol_label = QLabel("60%", styleSheet="color:#ccc; min-width:35px; margin-left:5px;")
        tl.addWidget(self.mus_vol_label)
        self._register_tooltip(self.mus_vol_label, "Current music volume level")
        self.sfx_btn = QPushButton("🔊 SFX")
        self.sfx_btn.setFixedHeight(34)
        self.sfx_btn.setStyleSheet("QPushButton { background-color: #4A85B8; color: white; border: 1px solid #366B93; border-radius: 4px; font-size: 13px; font-weight: bold; padding: 0 12px; } QPushButton:hover { background-color: #5A9AC8; } QPushButton:pressed { background-color: #3A6B98; }")
        self.sfx_btn.clicked.connect(self._toggle_sfx)
        self._register_tooltip(self.sfx_btn, "Click to mute/unmute sound effects")
        tl.addWidget(self.sfx_btn)
        self.help_btn = QPushButton("?")
        self.help_btn.setObjectName("HelpBtn")
        self.help_btn.setFixedWidth(28)
        self.help_btn.setFixedHeight(28)
        self.help_btn.clicked.connect(self._toggle_help_mode)
        tl.addWidget(self.help_btn)
        self._register_tooltip(self.help_btn, "Toggle help tooltips. When active, hover over any element for an explanation.")
        self.shortcuts_btn = QPushButton("⌨")
        self.shortcuts_btn.setObjectName("HelpBtn")
        self.shortcuts_btn.setFixedWidth(28)
        self.shortcuts_btn.setFixedHeight(28)
        self.shortcuts_btn.clicked.connect(self._show_keyboard_shortcuts)
        tl.addWidget(self.shortcuts_btn)
        self._register_tooltip(self.shortcuts_btn, "Show keyboard shortcuts help")
        self.undo_btn = QPushButton("↶")
        self.undo_btn.setObjectName("HelpBtn")
        self.undo_btn.setFixedWidth(28)
        self.undo_btn.setFixedHeight(28)
        self.undo_btn.setEnabled(False)
        tl.addWidget(self.undo_btn)
        self._register_tooltip(self.undo_btn, "Undo (Ctrl+Z)")
        self.redo_btn = QPushButton("↷")
        self.redo_btn.setObjectName("HelpBtn")
        self.redo_btn.setFixedWidth(28)
        self.redo_btn.setFixedHeight(28)
        self.redo_btn.setEnabled(False)
        tl.addWidget(self.redo_btn)
        self._register_tooltip(self.redo_btn, "Redo (Ctrl+Y)")
        tl.addSpacing(10)
        self.clock_label = QLabel("00:00:00")
        self.clock_label.setStyleSheet("color:#ccc; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; min-width: 66px;")
        tl.addWidget(self.clock_label)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()
        tl.addSpacing(10)
        self.min_btn = QPushButton("─")
        self.min_btn.setObjectName("HelpBtn")
        self.min_btn.setFixedWidth(28)
        self.min_btn.setFixedHeight(28)
        self.min_btn.clicked.connect(self.showMinimized)
        tl.addWidget(self.min_btn)
        self._register_tooltip(self.min_btn, "Minimize the application window")
        cb = QPushButton("✕")
        cb.setObjectName("CloseBtn")
        cb.clicked.connect(self.close)
        tl.addWidget(cb)
        self._register_tooltip(cb, "Close the application")
        ml.addWidget(tf)
        self.title_bar = tf
        ip = QFrame()
        ip.setObjectName("Card")
        il = QHBoxLayout(ip)
        il.setContentsMargins(15, 15, 15, 15)
        self.meta_frame = QFrame()
        self.meta_frame.setObjectName("Card")
        meta_layout = QVBoxLayout(self.meta_frame)
        meta_layout.setContentsMargins(10, 10, 10, 10)
        meta_header = QHBoxLayout()
        meta_title = QLabel("Image Metadata")
        meta_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.meta_toggle_btn = QPushButton("▼")
        self.meta_toggle_btn.setObjectName("MetaToggleBtn")
        self.meta_toggle_btn.clicked.connect(self._toggle_metadata_panel)
        self._register_tooltip(self.meta_toggle_btn, "Toggle metadata panel visibility")
        meta_header.addWidget(meta_title)
        meta_header.addStretch()
        meta_header.addWidget(self.meta_toggle_btn)
        meta_layout.addLayout(meta_header)
        self.meta_content = QWidget()
        meta_content_layout = QVBoxLayout(self.meta_content)
        self.meta_display = QTextEdit()
        self.meta_display.setReadOnly(True)
        self.meta_display.setHtml("<i>No image loaded</i>")
        self.meta_display.setStyleSheet(f"background: rgba(20,20,20,80); border: 1px solid rgba(80,80,80,100); border-radius: 4px; color: #ccc; font-family: monospace; font-size: {self.meta_font_size}px; padding: 8px;")
        meta_content_layout.addWidget(self.meta_display)
        self._register_tooltip(self.meta_display, "Shows file information, dimensions, capacity, and EXIF data for the loaded image.")
        meta_layout.addWidget(self.meta_content)
        il.addWidget(self.meta_frame, 2)
        self.thumb = QLabel("No image")
        self.thumb.setFixedSize(256, 256)
        self.thumb.setAlignment(Qt.AlignCenter)
        self.thumb.setStyleSheet("background:rgba(40,40,40,100); border:2px solid #555; border-radius:8px; color:#fff;")
        il.addWidget(self.thumb)
        self._register_tooltip(self.thumb, "Preview of the loaded image. Click to view full size. Double-click to load a new image. You can also drag-and-drop an image here.")
        self.thumb.setCursor(Qt.PointingHandCursor)
        self.thumb.installEventFilter(self)
        bc = QVBoxLayout()
        self.sel_btn = QPushButton("Select Image")
        self.sel_btn.clicked.connect(self._select_image)
        bc.addWidget(self.sel_btn)
        self._register_tooltip(self.sel_btn, "Browse your computer for an image to encode or decode.")
        self.view_btn = QPushButton("View")
        self.view_btn.setEnabled(False)
        self.view_btn.clicked.connect(self._show_full_img)
        bc.addWidget(self.view_btn)
        self._register_tooltip(self.view_btn, "Open the loaded image in a zoomable full-screen viewer.")
        il.addLayout(bc)
        ml.addWidget(ip)
        self.ws_frame = QFrame()
        self.ws_frame.setObjectName("Card")
        ws_layout = QGridLayout(self.ws_frame)
        ws_layout.setContentsMargins(15, 15, 15, 15)
        self.watermark = QLabel()
        self.watermark.setObjectName("Watermark")
        self.watermark.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.watermark.setText("READY")
        self.watermark.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.watermark.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.watermark.setMinimumSize(1, 1)
        self.watermark.setMaximumSize(10000, 10000)
        self.text_area = QTextBrowser()
        self.text_area.setAcceptRichText(False)
        self.text_area.setAttribute(Qt.WA_TranslucentBackground, True)
        self.text_area.setStyleSheet(f"font-family: 'Consolas', 'Courier New', monospace; font-size: {self.text_font_size}px; background-color: transparent; border: none;")
        self.text_area.setOpenExternalLinks(False)
        self.text_area.setOpenLinks(False)
        self.text_area.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_area.customContextMenuRequested.connect(self._show_text_context_menu)
        self.text_area.setUndoRedoEnabled(True)
        self.text_area.textChanged.connect(self._update_undo_redo_buttons)
        self.text_area.textChanged.connect(self._update_counter)
        self.undo_btn.clicked.connect(self.text_area.undo)
        self.redo_btn.clicked.connect(self.text_area.redo)
        pal = self.text_area.palette()
        pal.setColor(QPalette.Link, QColor("#FFD700"))
        pal.setColor(QPalette.LinkVisited, QColor("#FFFFFF"))
        self.text_area.setPalette(pal)
        ws_layout.addWidget(self.watermark, 0, 0)
        ws_layout.addWidget(self.text_area, 0, 0)
        self.watermark.lower()
        self._register_tooltip(self.text_area, "Displays decoded messages or enter text to encode. Click text to start editing. Click links to open in browser.")
        self.meta_display.viewport().installEventFilter(self)
        self.text_area.viewport().installEventFilter(self)
        controls = QHBoxLayout()
        self.font_down = QPushButton("A-")
        self.font_down.setFixedWidth(30)
        self.font_down.clicked.connect(lambda: self._zoom_text(-FONT_STEP))
        controls.addWidget(self.font_down)
        self._register_tooltip(self.font_down, "Decrease message text size")
        self.f_lbl = QLabel(f"{self.text_font_size}px", styleSheet="color:#fff; min-width:40px;")
        controls.addWidget(self.f_lbl)
        self._register_tooltip(self.f_lbl, "Current message text size. Also adjustable with Ctrl+Scroll Wheel.")
        self.font_up = QPushButton("A+")
        self.font_up.setFixedWidth(30)
        self.font_up.clicked.connect(lambda: self._zoom_text(FONT_STEP))
        controls.addWidget(self.font_up)
        self._register_tooltip(self.font_up, "Increase message text size")
        controls.addSpacing(15)
        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("Password")
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setFixedWidth(140)
        self.pwd_input.returnPressed.connect(self._attempt_decode)
        self.pwd_input.textChanged.connect(self._on_password_changed)
        controls.addWidget(self.pwd_input)
        self._register_tooltip(self.pwd_input, "Enter a password to decrypt the hidden message. Press Enter to apply. Leave blank for unencrypted messages.")
        self.pwd_show_btn = QPushButton("👁")
        self.pwd_show_btn.setFixedWidth(30)
        self.pwd_show_btn.setCheckable(True)
        self.pwd_show_btn.clicked.connect(self._toggle_password_visibility)
        controls.addWidget(self.pwd_show_btn)
        self._register_tooltip(self.pwd_show_btn, "Show or hide the password as you type it")
        self.pwd_clear_btn = QPushButton("🗑")
        self.pwd_clear_btn.setFixedWidth(30)
        self.pwd_clear_btn.clicked.connect(self._clear_password)
        controls.addWidget(self.pwd_clear_btn)
        self._register_tooltip(self.pwd_clear_btn, "Clear the password field")
        self.pwd_memory_btn = QPushButton("🔑")
        self.pwd_memory_btn.setFixedWidth(30)
        self.pwd_memory_btn.clicked.connect(self._show_saved_passwords_dialog)
        controls.addWidget(self.pwd_memory_btn)
        self._register_tooltip(self.pwd_memory_btn, "View and manage saved passwords. Passwords are automatically saved when used.")
        controls.addSpacing(10)
        self.pwd_input2 = QLineEdit()
        self.pwd_input2.setPlaceholderText("Pass 2")
        self.pwd_input2.setEchoMode(QLineEdit.Password)
        self.pwd_input2.setFixedWidth(110)
        self.pwd_input2.returnPressed.connect(self._attempt_decode)
        self.pwd_input2.textChanged.connect(self._on_pass2_changed)
        controls.addWidget(self.pwd_input2)
        self._register_tooltip(self.pwd_input2, "Optional password field.")
        self.pwd_show_btn2 = QPushButton("👁")
        self.pwd_show_btn2.setFixedWidth(30)
        self.pwd_show_btn2.setCheckable(True)
        self.pwd_show_btn2.clicked.connect(lambda: self._toggle_password_field_visibility(self.pwd_input2, self.pwd_show_btn2))
        controls.addWidget(self.pwd_show_btn2)
        self._register_tooltip(self.pwd_show_btn2, "Show or hide this password as you type it")
        controls.addStretch()
        controls.addWidget(QLabel("Password:", styleSheet="color:#999; font-size:12px;"))
        controls.addWidget(self.password_strength_indicator)
        self._register_tooltip(self.password_strength_indicator, "Password strength indicator")
        controls.addSpacing(10)
        controls.addWidget(QLabel("Capacity:", styleSheet="color:#999; font-size:12px;"))
        controls.addWidget(self.capacity_progress_bar)
        controls.addWidget(self.capacity_percent_label)
        self._register_tooltip(self.capacity_progress_bar, "Capacity usage indicator")
        controls.addWidget(self.loading_spinner)
        controls.addSpacing(15)
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.clicked.connect(self._copy_message)
        self._retain_size_when_hidden(self.copy_btn)
        self.copy_btn.hide()
        controls.addWidget(self.copy_btn)
        self._register_tooltip(self.copy_btn, "Copy the decoded message to your clipboard.")
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self._toggle_edit)
        self._retain_size_when_hidden(self.edit_btn)
        self.edit_btn.hide()
        controls.addWidget(self.edit_btn)
        self._register_tooltip(self.edit_btn, "Unlock the decoded message for editing.")
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self._encode_msg)
        self._retain_size_when_hidden(self.save_btn)
        self.save_btn.hide()
        controls.addWidget(self.save_btn)
        self._register_tooltip(self.save_btn, "Encode your message into the image and save as a new file. (Ctrl+S)")
        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.clicked.connect(self._cancel_edit)
        self._retain_size_when_hidden(self.cancel_btn)
        self.cancel_btn.hide()
        controls.addWidget(self.cancel_btn)
        self._register_tooltip(self.cancel_btn, "Discard changes and return to view mode.")
        ws_layout.addLayout(controls, 1, 0)
        ml.addWidget(self.ws_frame)
        sf = QFrame()
        sf.setObjectName("Card")
        sl = QVBoxLayout(sf)
        sl.setContentsMargins(15, 8, 15, 8)
        status_row = QHBoxLayout()
        self.st_lbl = QLabel("Ready", objectName="StatusText")
        status_row.addWidget(self.st_lbl)
        self._register_tooltip(self.st_lbl, "Shows the current operation status and results.")
        status_row.addStretch()
        # No size grip: with the window now permanently locked to the
        # screen's exact size, a resize handle would be purely decorative
        # and non-functional - removed rather than left as a dead affordance.
        sl.addLayout(status_row)
        ml.addWidget(sf)
        self.move(QApplication.primaryScreen().geometry().center() - self.rect().center())
        QTimer.singleShot(200, self._update_watermark)
        # No showNormal() here - _restore_window_state() runs right after
        # this and always goes fullscreen, so calling showNormal() first
        # was a redundant step that got immediately overridden anyway.

    def _handle_save_shortcut(self):
        if self.save_btn.isVisible() and not self.worker_running:
            self._encode_msg()

    def _on_slider_changed(self, value):
        self.audio.set_music_volume(value)
        self.mus_vol_label.setText(f"{value}%")
        if value == 0:
            if not self._is_muted:
                self._is_muted = True
                self.music_mute_btn.setText("🔇 Music")
        else:
            if self._is_muted:
                self._is_muted = False
                self.music_mute_btn.setText("🎵 Music")
            self._previous_music_volume = value

    def _toggle_mute(self):
        self.audio.play_sfx('click')
        if self._is_muted:
            self._is_muted = False
            restore_vol = self._previous_music_volume if self._previous_music_volume > 0 else 60
            self.mus_vol.blockSignals(True)
            self.mus_vol.setValue(restore_vol)
            self.mus_vol.blockSignals(False)
            self.audio.set_music_volume(restore_vol)
            self.mus_vol_label.setText(f"{restore_vol}%")
            self.music_mute_btn.setText("🎵 Music")
        else:
            self._is_muted = True
            self._previous_music_volume = self.mus_vol.value()
            self.mus_vol.blockSignals(True)
            self.mus_vol.setValue(0)
            self.mus_vol.blockSignals(False)
            self.audio.set_music_volume(0)
            self.mus_vol_label.setText("0%")
            self.music_mute_btn.setText("🔇 Music")

    def _toggle_sfx(self):
        self.audio.play_sfx('click')
        is_enabled = self.audio.toggle_sfx()
        if is_enabled: self.sfx_btn.setText("🔊 SFX")
        else: self.sfx_btn.setText("🔇 SFX")

    def _update_clock(self):
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S"))

    def _copy_message(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_area.toPlainText())
        self._status("Message copied to clipboard!", "success")
        self.audio.play_sfx('success')

    def _clear_password(self):
        self.audio.play_sfx('click')
        target = self._last_focused_pwd_field if self._last_focused_pwd_field in (self.pwd_input, self.pwd_input2) else self.pwd_input
        target.clear()

    def _toggle_password_visibility(self):
        self._toggle_password_field_visibility(self.pwd_input, self.pwd_show_btn)

    def _toggle_password_field_visibility(self, field, btn):
        if btn.isChecked():
            field.setEchoMode(QLineEdit.Normal)
        else:
            field.setEchoMode(QLineEdit.Password)

    def _on_password_changed(self, text):
        self.password_strength_indicator.update_strength(text)
        self._update_counter()

    def _estimate_encrypted_len(self, raw_len):
        return estimate_encrypted_payload_len(raw_len)

    def _clear_pass_field_highlight(self):
        if hasattr(self, 'pwd_input'): self.pwd_input.setStyleSheet("")
        if hasattr(self, 'pwd_input2'): self.pwd_input2.setStyleSheet("")

    def _update_pass_field_highlight(self):
        active_style = "border: 2px solid #FFD700;"
        if self._editing_layer == 2 and self._layer2_active:
            self.pwd_input.setStyleSheet("")
            self.pwd_input2.setStyleSheet(active_style)
        else:
            self.pwd_input.setStyleSheet(active_style)
            self.pwd_input2.setStyleSheet("")

    def _reset_dual_compose_state(self):
        self._layer2_active = False
        self._editing_layer = 1
        self._message1_buffer = ""
        self._message2_buffer = ""
        self._decoded_layer1_message = ""
        self._currently_shown_layer = 0
        self._clear_pass_field_highlight()

    def _switch_to_layer(self, target):
        if self.text_area.isReadOnly():
            return
        if self._editing_layer == target:
            return
        if self._editing_layer == 1:
            self._message1_buffer = self.text_area.toPlainText()
        else:
            self._message2_buffer = self.text_area.toPlainText()
        self._editing_layer = target
        self.text_area.setPlainText(self._message1_buffer if target == 1 else self._message2_buffer)
        self._update_pass_field_highlight()
        self._update_counter()

    def _on_pass2_changed(self, text):
        if not self.text_area.isReadOnly():
            if text and not self._layer2_active:
                self._layer2_active = True
                current_layer1_text = self.text_area.toPlainText() if self._editing_layer == 1 else self._message1_buffer
                self._message2_buffer = current_layer1_text
                self._switch_to_layer(2)
        else:
            if not text and self._currently_shown_layer == 2 and self._decoded_layer1_message:
                self.original_message = self._decoded_layer1_message
                self.text_area.setHtml(convert_links_to_html(self._decoded_layer1_message))
                self._currently_shown_layer = 1
        self._update_counter()

    def _attempt_decode(self):
        if self.worker_running: return
        if not self.current_image_path or not os.path.exists(self.current_image_path): return
        self.audio.play_sfx('click')
        pass1 = self.pwd_input.text()
        pass2 = self.pwd_input2.text()
        self._set_worker(True)
        self.decoderWorker = DecodeWorker(self.current_image_path, self.delimiter, pass1, pass2)
        self.decoderWorker.decoding_finished.connect(lambda msg, enc, layer, l1msg: self._on_decode_result(msg, enc, layer, pass1, pass2, l1msg))
        self.decoderWorker.error.connect(self._on_decode_error)
        self.decoderWorker.start()

    def _on_decode_result(self, msg, is_encrypted, layer, pass1, pass2, layer1_msg):
        self._set_worker(False)
        if msg and layer > 0:
            self.original_message = msg
            self._decoded_layer1_message = layer1_msg
            self._currently_shown_layer = layer
            self.watermark.setText("DECODED")
            self._update_watermark()
            self.text_area.setHtml(convert_links_to_html(msg))
            self.text_area.setReadOnly(True)
            self.edit_btn.show()
            self.copy_btn.show()
            self.save_btn.hide()
            self.cancel_btn.hide()
            if pass1:
                self._save_password_to_list(pass1)
            if pass2 and layer == 2:
                self._save_password_to_list(pass2)
            if pass1 and not is_encrypted and layer == 1: self._status("Message found (Unencrypted). Password ignored.", "info")
            elif is_encrypted: self._status("Message decrypted successfully.", "success")
            else: self._status("Message found.", "success")
            self.audio.play_sfx('success')
            self._update_counter()
        else:
            self.original_message = ""
            self._decoded_layer1_message = ""
            self._currently_shown_layer = 0
            self.text_area.clear()
            self.text_area.setReadOnly(True)
            self.watermark.setText("PASSWORD REQUIRED")
            self._update_watermark()
            self.edit_btn.hide()
            self.copy_btn.hide()
            self._status("Incorrect password or no message found.", "error")
            self.audio.play_sfx('error')

    def _on_decode_error(self, e):
        self._set_worker(False)
        self._status(f"Error: {e}", "error")
        self.audio.play_sfx('error')

    def eventFilter(self, obj, event):
        if hasattr(self, 'pwd_input') and hasattr(self, 'pwd_input2') and obj in (self.pwd_input, self.pwd_input2):
            if event.type() == QEvent.FocusIn:
                self._last_focused_pwd_field = obj
                if obj is self.pwd_input:
                    self._switch_to_layer(1)
                    if not self.text_area.isReadOnly():
                        self._update_pass_field_highlight()
                elif obj is self.pwd_input2 and self._layer2_active:
                    self._switch_to_layer(2)
                    if not self.text_area.isReadOnly():
                        self._update_pass_field_highlight()
        if self.help_mode_active and obj in self._tooltip_map:
            if event.type() == QEvent.Enter:
                self.help_tooltip.setText(self._tooltip_map[obj])
                self._position_tooltip(obj)
                self.help_tooltip.show()
            elif event.type() == QEvent.Leave:
                self.help_tooltip.hide()
        if hasattr(self, 'thumb') and obj is self.thumb:
            if event.type() == QEvent.MouseButtonDblClick and event.button() == Qt.LeftButton:
                self._click_timer.stop()
                self._handle_thumb_double_click()
                return True
            elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._click_timer.start()
                return True
        if hasattr(self, 'text_area') and event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton and obj is self.text_area.viewport():
            if self.text_area.isReadOnly():
                pos = event.pos()
                href = self.text_area.anchorAt(pos)
                if href:
                    QDesktopServices.openUrl(QUrl(href))
                    return True
                else:
                    if hasattr(self, 'watermark') and self.watermark.text() == "DECODED":
                        self._enter_edit_mode(pos)
                        return True
            return False
        if event.type() == QEvent.Wheel:
            if hasattr(self, 'meta_display') and hasattr(self, 'text_area') and obj in (self.meta_display.viewport(), self.text_area.viewport()):
                if QApplication.keyboardModifiers() & Qt.ControlModifier:
                    delta = FONT_STEP if event.angleDelta().y() > 0 else -FONT_STEP
                    if obj is self.text_area.viewport(): self._zoom_text(delta)
                    else: self._zoom_meta(delta)
                    return True
        return super().eventFilter(obj, event)

    def _enter_edit_mode(self, click_pos=None):
        self.audio.play_sfx('click')
        self.text_area.setReadOnly(False)
        self.watermark.setText("ENCODE")
        self._update_watermark()
        self.edit_btn.hide()
        self.copy_btn.hide()
        self.save_btn.show()
        self.cancel_btn.show()
        self.text_area.setFocus()
        if click_pos is not None:
            cursor = self.text_area.cursorForPosition(click_pos)
            self.text_area.setTextCursor(cursor)
        
        if self._currently_shown_layer == 0:
            self.pwd_input2.clear()
            self._reset_dual_compose_state()
        else:
            self._editing_layer = self._currently_shown_layer
            if self._editing_layer == 2:
                self._layer2_active = True
                self._message2_buffer = self.text_area.toPlainText()
                # The real Layer 1 text was already known (cached) the
                # moment Layer 2 was revealed - carry it into the edit
                # buffer too, so switching to the Pass 1 field while
                # editing shows the real message instead of leaving it
                # blank/stale.
                self._message1_buffer = self._decoded_layer1_message
            else:
                self._layer2_active = False
                self._message1_buffer = self.text_area.toPlainText()
            self._update_pass_field_highlight()

    def _handle_thumb_single_click(self):
        if self.current_image_path and os.path.exists(self.current_image_path): self._show_full_img()
        else: self._select_image()

    def _handle_thumb_double_click(self):
        self._select_image()

    def _toggle_edit(self):
        self._enter_edit_mode()

    def _cancel_edit(self):
        self.audio.play_sfx('click')
        if self.original_message:
            self.text_area.setHtml(convert_links_to_html(self.original_message))
            self.text_area.setReadOnly(True)
            self.watermark.setText("DECODED")
            self._update_watermark()
            self.edit_btn.show()
            self.copy_btn.show()
        else:
            self.text_area.clear()
            self.text_area.setReadOnly(False)
            self.watermark.setText("ENCODE")
            self._update_watermark()
            self.save_btn.show()
            self.text_area.setFocus()
        self.pwd_input2.clear()
        self._reset_dual_compose_state()
        self.cancel_btn.hide()

    def _zoom_text(self, d):
        n = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, self.text_font_size + d))
        if n != self.text_font_size:
            self.text_font_size = n
            self.f_lbl.setText(f"{n}px")
            self.text_area.setStyleSheet(f"font-family: 'Consolas', 'Courier New', monospace; font-size: {n}px; background-color: transparent; border: none;")

    def _zoom_meta(self, d):
        n = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, self.meta_font_size + d))
        if n != self.meta_font_size:
            self.meta_font_size = n
            self.meta_display.setStyleSheet(f"background: rgba(20,20,20,80); border: 1px solid rgba(80,80,80,100); border-radius: 4px; color: #ccc; font-family: monospace; font-size: {n}px; padding: 8px;")

    def _show_full_img(self):
        if self.current_image_path and os.path.exists(self.current_image_path):
            try:
                if self.active_viewer and self.active_viewer.isVisible(): self.active_viewer.close()
            except RuntimeError: pass
            self.active_viewer = None
            self.active_viewer = ZoomImageViewer(self.current_image_path, self)
            self.active_viewer.show()

    def _select_image(self):
        if self.worker_running: return
        self.audio.play_sfx('click')
        p, _ = QFileDialog.getOpenFileName(self, "Select Image", self.settings.value("lastDir", os.path.dirname(os.path.abspath(__file__))), "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp)")
        if not p: return
        self.settings.setValue("lastDir", os.path.dirname(p))
        self._load_image(p)

    def _load_image(self, p):
        if self.worker_running: return
        if self._has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Unsaved Message",
                "Loading a new image will discard the message you haven't saved yet. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        is_valid, error_msg = self._validate_file_size(p)
        if not is_valid:
            self._status(error_msg, "error")
            self.audio.play_sfx('error')
            return
        try:
            if self.active_viewer and self.active_viewer.isVisible(): self.active_viewer.close()
        except RuntimeError: pass
        self.active_viewer = None
        self._pending_load_path = p
        self._set_worker(True)
        self.loaderWorker = ImageLoadWorker(p, self.delimiter)
        self.loaderWorker.loaded.connect(self._on_image_loaded)
        self.loaderWorker.error.connect(self._on_image_load_error)
        self.loaderWorker.start()

    def _on_image_loaded(self, result):
        p = self._pending_load_path
        self._set_worker(False)
        self.current_image_path = p
        self.available_capacity_bits = result['capacity_bits']
        self.pwd_input.clear()
        self.pwd_input2.clear()
        self._reset_dual_compose_state()
        with _SuppressStderr():
            thumb_pixmap = QPixmap(p)
        self.thumb.setPixmap(thumb_pixmap.scaled(THUMBNAIL_SIZE * 2, THUMBNAIL_SIZE * 2, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.thumb.setText("")
        self.view_btn.setEnabled(True)
        self.meta_display.setHtml(self._extract_metadata(p))
        has_message = result['has_message']
        is_encrypted = result['is_encrypted']
        if has_message:
            if is_encrypted:
                self.original_message = ""
                self.watermark.setText("PASSWORD REQUIRED")
                self._update_watermark()
                self.text_area.clear()
                self.text_area.setReadOnly(True)
                self.edit_btn.hide()
                self.copy_btn.hide()
                self.save_btn.hide()
                self.cancel_btn.hide()
                self._status("Encrypted message detected. Enter password and press Enter to decode.", "info")
                self.pwd_input.setFocus()
            else:
                msg = result['message']
                self.original_message = msg
                self.watermark.setText("DECODED")
                self._update_watermark()
                self.text_area.setHtml(convert_links_to_html(msg))
                self.text_area.setReadOnly(True)
                self.edit_btn.show()
                self.copy_btn.show()
                self.save_btn.hide()
                self.cancel_btn.hide()
                self._status("Message found (unencrypted).", "success")
                self.audio.play_sfx('success')
        else:
            self.original_message = ""
            self.watermark.setText("ENCODE")
            self._update_watermark()
            self.text_area.clear()
            self.text_area.setReadOnly(False)
            self.text_area.setFocus()
            self.edit_btn.hide()
            self.copy_btn.hide()
            self.save_btn.show()
            self.cancel_btn.show()
            self._status("Ready to encode", "info")
        self._update_counter()

    def _on_image_load_error(self, e):
        self._set_worker(False)
        self._status(f"Error loading image: {e}", "error")
        self.audio.play_sfx('error')

    def _update_counter(self):
        if not hasattr(self, 'capacity_progress_bar'):
            return
        pass1 = self.pwd_input.text() if hasattr(self, 'pwd_input') else ""
        pass2 = self.pwd_input2.text() if hasattr(self, 'pwd_input2') else ""
        current_layer1 = self.text_area.toPlainText() if self._editing_layer == 1 else self._message1_buffer
        msg1_bytes = len(current_layer1.encode('utf-8'))
        payload1_len = self._estimate_encrypted_len(msg1_bytes) if pass1 else msg1_bytes
        if pass2:
            current_layer2 = self.text_area.toPlainText() if self._editing_layer == 2 else self._message2_buffer
            msg2_bytes = len(current_layer2.encode('utf-8'))
            payload2_len = self._estimate_encrypted_len(msg2_bytes)
            c = payload1_len + payload2_len
            overhead = len(DUAL_HEADER) + len(self.delimiter) * 2
        else:
            c = payload1_len
            overhead = len(self.magic_header) + len(self.delimiter)
        m = (self.available_capacity_bits // 8) - overhead if self.available_capacity_bits else 0
        if m > 0:
            percentage = min(100, (c / m) * 100)
            self.capacity_progress_bar.setValue(int(percentage))
            self.capacity_percent_label.setText(f"{int(percentage)}%")
            if percentage >= 100:
                self.capacity_progress_bar.setStyleSheet("QProgressBar { border: none; background-color: rgba(100, 100, 100, 0.3); border-radius: 4px; } QProgressBar::chunk { background-color: #FF4444; border-radius: 4px; }")
            elif percentage >= 80:
                self.capacity_progress_bar.setStyleSheet("QProgressBar { border: none; background-color: rgba(100, 100, 100, 0.3); border-radius: 4px; } QProgressBar::chunk { background-color: #FFA500; border-radius: 4px; }")
            else:
                self.capacity_progress_bar.setStyleSheet("QProgressBar { border: none; background-color: rgba(100, 100, 100, 0.3); border-radius: 4px; } QProgressBar::chunk { background-color: #4CAF50; border-radius: 4px; }")
        else:
            self.capacity_progress_bar.setValue(0)
            self.capacity_percent_label.setText("0%")

    def _status(self, m, t="info"):
        colors = {'error': '#FF4444', 'success': '#44FF44', 'info': '#FFFFFF'}
        self.st_lbl.setStyleSheet(f"color: {colors.get(t, '#FFFFFF')}; font-size: 13px;")
        self.st_lbl.setText(m)

    def _set_worker(self, r):
        self._cleanup_workers()
        self.worker_running = r
        self.setCursor(Qt.BusyCursor if r else (Qt.WhatsThisCursor if self.help_mode_active else Qt.ArrowCursor))
        if r: self.loading_spinner.start_spinning()
        else: self.loading_spinner.stop_spinning()
        for x in (self.sel_btn, self.view_btn, self.font_down, self.font_up, self.save_btn, self.cancel_btn,
                  self.edit_btn, self.copy_btn, self.pwd_input, self.pwd_memory_btn, self.pwd_show_btn,
                  self.pwd_input2, self.pwd_show_btn2):
            if x: x.setEnabled(not r)
        if r: self._status("Processing...", "info")

    def _encode_msg(self):
        if self.worker_running: return
        if self._editing_layer == 1:
            self._message1_buffer = self.text_area.toPlainText()
        else:
            self._message2_buffer = self.text_area.toPlainText()
        m1 = self._message1_buffer.strip()
        if not m1: return self._status("Empty", "error")
        pass1 = self.pwd_input.text()
        pass2 = self.pwd_input2.text()
        m2 = self._message2_buffer.strip()
        if m2 and not pass2:
            return self._status("Message 2 has content - add a Pass 2 password before saving.", "error")
        is_dual = bool(pass2)
        if pass1:
            self._save_password_to_list(pass1)
        if is_dual:
            self._save_password_to_list(pass2)
        msg1_bytes_len = len(m1.encode('utf-8'))
        payload1_len = self._estimate_encrypted_len(msg1_bytes_len) if pass1 else msg1_bytes_len
        if is_dual:
            msg2_bytes_len = len(m2.encode('utf-8'))
            payload2_len = self._estimate_encrypted_len(msg2_bytes_len)
            total_payload = payload1_len + payload2_len
            header_len = len(DUAL_HEADER)
            delim_overhead = len(self.delimiter) * 2
        else:
            total_payload = payload1_len
            header_len = len(self.magic_header)
            delim_overhead = len(self.delimiter)
        if (header_len + total_payload + delim_overhead) * 8 > self.available_capacity_bits:
            max_chars = (self.available_capacity_bits // 8) - (header_len + delim_overhead)
            if pass1 or is_dual:
                max_chars = max(0, max_chars - AES_SALT_SIZE - AES_IV_SIZE - 16)
            return QMessageBox.warning(self, "Capacity", f"Message exceeds capacity. Max approx {max_chars} chars total.")
        base = os.path.splitext(os.path.basename(self.current_image_path))[0]
        default_name = f"{base}_steganosed"
        filters = "All Lossless Formats (*.png *.bmp *.tiff *.tif *.webp);;PNG Files (*.png);;BMP Files (*.bmp);;TIFF Files (*.tiff *.tif);;WebP Files (*.webp)"
        s, selected_filter = QFileDialog.getSaveFileName(self, "Save Image", os.path.join(self.settings.value("lastDir", ""), default_name), filters)
        if not s: return
        ext = os.path.splitext(s)[1].lower()
        if ext == ".png": out_fmt = "PNG"
        elif ext == ".bmp": out_fmt = "BMP"
        elif ext in [".tiff", ".tif"]: out_fmt = "TIFF"
        elif ext == ".webp": out_fmt = "WEBP"
        else:
            if "BMP" in selected_filter: out_fmt, ext = "BMP", ".bmp"
            elif "TIFF" in selected_filter: out_fmt, ext = "TIFF", ".tiff"
            elif "WebP" in selected_filter: out_fmt, ext = "WebP", ".webp"
            else: out_fmt, ext = "PNG", ".png"
            s += ext
        self.settings.setValue("lastDir", os.path.dirname(s))
        self._set_worker(True)
        self.audio.play_sfx('action')
        if is_dual:
            self.encoderWorker = EncodeWorker(encode_dual_image, (self.current_image_path, m1, m2, s, DUAL_HEADER, self.delimiter, out_fmt, pass1, pass2))
        else:
            self.encoderWorker = EncodeWorker(encode_image, (self.current_image_path, m1, s, self.magic_header, self.delimiter, out_fmt, pass1))
        self.encoderWorker.encoding_finished.connect(lambda: self._on_encode_success(m1, s))
        self.encoderWorker.error.connect(self._on_encode_error)
        self.encoderWorker.start()

    def _on_encode_success(self, msg, path):
        self.original_message = msg
        self.text_area.setHtml(convert_links_to_html(msg))
        self.text_area.setReadOnly(True)
        self.watermark.setText("DECODED")
        self._update_watermark()
        self.edit_btn.show()
        self.copy_btn.show()
        self.save_btn.hide()
        self.cancel_btn.hide()
        self.pwd_input.clear()
        self.pwd_input2.clear()
        self._reset_dual_compose_state()
        self._status(f"Saved: {os.path.basename(path)}", "success")
        self.audio.play_sfx('success')
        self._animate_success()
        self._set_worker(False)

    def _on_encode_error(self, e):
        self._status(f"Error: {e}", "error")
        self.audio.play_sfx('error')
        self._animate_error()
        self._set_worker(False)

    def _animate_success(self):
        self.watermark.setStyleSheet("color: rgba(76, 175, 80, 0.3); background: transparent; font-size: 100px;")
        QTimer.singleShot(500, lambda: self._update_watermark())

    def _animate_error(self):
        self.watermark.setStyleSheet("color: rgba(244, 67, 54, 0.3); background: transparent; font-size: 100px;")
        QTimer.singleShot(500, lambda: self._update_watermark())

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = SteganographyApp()
    window.show()
    sys.exit(app.exec_())
