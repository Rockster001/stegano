import hashlib
import os
import re
import shutil
import tempfile

from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from stegano_config import DELIMITER, STEALTH_HEADER
from stegano_core import _decrypt_bytes_aes, _encrypt_bytes_aes, decode_image, encode_image


_BACKGROUND_FILENAME = "wallpaper.png"
_SCRATCHPAD_FILENAME = "cache.txt"
_KEY_PREFIX = "STEGANO_SCRATCHPAD_V1:"
_KEY_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ScratchpadStorageError(Exception):
    pass


class ScratchpadStore:
    def __init__(self, data_dir, bundled_background_path):
        self.data_dir = data_dir
        self.background_path = os.path.join(data_dir, _BACKGROUND_FILENAME)
        self.scratchpad_path = os.path.join(data_dir, _SCRATCHPAD_FILENAME)
        self.bundled_background_path = bundled_background_path
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            self._ensure_background()
            self.password = self._load_or_create_password()
        except ScratchpadStorageError:
            raise
        except OSError as exc:
            raise ScratchpadStorageError(
                "Could not initialize Scratchpad storage."
            ) from exc

    def _copy_background(self):
        if not os.path.isfile(self.bundled_background_path):
            raise ScratchpadStorageError("The bundled background image is unavailable.")
        try:
            with tempfile.NamedTemporaryFile(
                prefix=".wallpaper-",
                suffix=".png",
                dir=self.data_dir,
                delete=False,
            ) as temp_file:
                temp_path = temp_file.name
            shutil.copyfile(self.bundled_background_path, temp_path)
            os.replace(temp_path, self.background_path)
        except OSError as exc:
            if "temp_path" in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            raise ScratchpadStorageError(
                "Could not create the per-user background image."
            ) from exc

    def _ensure_background(self):
        if not os.path.exists(self.background_path):
            self._copy_background()

        try:
            with Image.open(self.background_path) as image:
                image.verify()
        except (OSError, ValueError):
            self._copy_background()
            try:
                with Image.open(self.background_path) as image:
                    image.verify()
            except (OSError, ValueError) as exc:
                raise ScratchpadStorageError(
                    "The background image is damaged and cannot be restored."
                ) from exc

    @staticmethod
    def _password_from_timestamp(timestamp_ns):
        seed = b"Stegano Scratchpad password v1:" + str(timestamp_ns).encode("ascii")
        return hashlib.sha256(seed).hexdigest()

    def _load_or_create_password(self):
        try:
            embedded, was_encrypted = decode_image(self.background_path, DELIMITER)
        except (OSError, ValueError) as exc:
            raise ScratchpadStorageError(
                "Could not read the Scratchpad background image."
            ) from exc

        if not was_encrypted and embedded.startswith(_KEY_PREFIX):
            password = embedded[len(_KEY_PREFIX):]
            if _KEY_PATTERN.fullmatch(password):
                return password

        timestamp_ns = os.stat(self.background_path).st_mtime_ns
        password = self._password_from_timestamp(timestamp_ns)
        self._embed_password(password, timestamp_ns)
        return password

    def _embed_password(self, password, timestamp_ns):
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                prefix=".wallpaper-",
                suffix=".png",
                dir=self.data_dir,
                delete=False,
            ) as temp_file:
                temp_path = temp_file.name

            encode_image(
                self.background_path,
                _KEY_PREFIX + password,
                temp_path,
                STEALTH_HEADER,
                DELIMITER,
                out_format="PNG",
            )
            os.utime(temp_path, ns=(os.stat(self.background_path).st_atime_ns, timestamp_ns))
            os.replace(temp_path, self.background_path)
        except (OSError, ValueError, TypeError) as exc:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            raise ScratchpadStorageError(
                "Could not store the Scratchpad key in the background image."
            ) from exc

    def load(self):
        if not os.path.exists(self.scratchpad_path):
            return ""
        try:
            with open(self.scratchpad_path, "rb") as scratchpad_file:
                encrypted = scratchpad_file.read()
        except OSError as exc:
            raise ScratchpadStorageError(
                "Could not read the saved Scratchpad."
            ) from exc

        plaintext = _decrypt_bytes_aes(encrypted, self.password)
        if plaintext is None:
            raise ScratchpadStorageError(
                "The saved Scratchpad could not be decrypted."
            )
        try:
            return plaintext.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ScratchpadStorageError(
                "The saved Scratchpad is damaged or unreadable."
            ) from exc

    def save(self, text):
        if not isinstance(text, str):
            raise ScratchpadStorageError("Scratchpad text must be plain text.")
        if not text.strip():
            self.delete()
            return

        encrypted = _encrypt_bytes_aes(text.encode("utf-8"), self.password)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                prefix=".cache-",
                suffix=".tmp",
                dir=self.data_dir,
                delete=False,
            ) as temp_file:
                temp_path = temp_file.name
                temp_file.write(encrypted)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temp_path, self.scratchpad_path)
        except OSError as exc:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            raise ScratchpadStorageError(
                "Could not save the Scratchpad."
            ) from exc

    def delete(self):
        try:
            if os.path.exists(self.scratchpad_path):
                os.remove(self.scratchpad_path)
        except OSError as exc:
            raise ScratchpadStorageError(
                "Could not delete the saved Scratchpad."
            ) from exc


class ScratchpadWindow(QDialog):
    def __init__(self, store, text="", storage_error=None, parent=None):
        super().__init__(parent, Qt.Window)
        self.store = store
        self.setWindowTitle("Scratchpad")
        self.setModal(False)
        self.resize(720, 480)

        layout = QVBoxLayout(self)
        self.editor = QPlainTextEdit()
        self.editor.setPlainText(text)
        self.editor.setStyleSheet(
            "QPlainTextEdit { background-color: #1e1e1e; color: #E0E0E0; "
            "border: 1px solid #555; border-radius: 4px; padding: 8px; "
            "font-family: 'Segoe UI', sans-serif; font-size: 14px; }"
        )
        layout.addWidget(self.editor)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #bdbdbd;")
        layout.addWidget(self.status_label)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.clear_button = QPushButton("Clear")
        self.restore_button = QPushButton("Restore")
        self.save_button = QPushButton("Save")
        buttons.addWidget(self.clear_button)
        buttons.addWidget(self.restore_button)
        buttons.addWidget(self.save_button)
        layout.addLayout(buttons)

        self.clear_button.clicked.connect(self._clear)
        self.restore_button.clicked.connect(self._restore)
        self.save_button.clicked.connect(self._save)
        self._set_status(storage_error, error=bool(storage_error))

    def _set_status(self, text, error=False):
        self.status_label.setText(text or "")
        self.status_label.setStyleSheet(
            "color: #ff7777;" if error else "color: #bdbdbd;"
        )

    def _clear(self):
        self.editor.clear()
        self._set_status("Cleared. The saved text is still available with Restore.")

    def _restore(self):
        if self.store is None:
            self._set_status("Scratchpad storage is unavailable.", error=True)
            return
        try:
            restored = self.store.load()
        except ScratchpadStorageError as exc:
            self._set_status(str(exc), error=True)
            return
        if not restored:
            self._set_status("There is no saved Scratchpad text to restore.")
            return
        if self.editor.toPlainText().strip():
            reply = QMessageBox.question(
                self,
                "Restore Scratchpad",
                "Replace the current Scratchpad text with the saved text?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        self.editor.setPlainText(restored)
        self._set_status("Scratchpad restored.")

    def _save(self):
        if self.store is None:
            self._set_status("Scratchpad storage is unavailable.", error=True)
            return
        text = self.editor.toPlainText()
        if not text.strip():
            self._set_status(
                "Nothing to save. The saved text remains available with Restore."
            )
            return
        try:
            self.store.save(text)
        except ScratchpadStorageError as exc:
            self._set_status(str(exc), error=True)
            return
        self._set_status("Scratchpad saved.")
