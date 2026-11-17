import os
import tempfile
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QEvent, QPointF, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QApplication, QLabel, QLineEdit, QMainWindow, QPushButton, QTextBrowser

import Stegano
from Stegano import SteganographyApp


def test_clicking_focused_layer_two_password_shows_layer_two():
    app = QApplication.instance() or QApplication([])
    window = SteganographyApp.__new__(SteganographyApp)
    QMainWindow.__init__(window)
    window.pwd_input = QLineEdit(window)
    window.pwd_input2 = QLineEdit(window)
    window.text_area = QTextBrowser(window)
    window.text_area.setReadOnly(True)
    window._editing_layer = 2
    window._currently_shown_layer = 1
    window._decoded_layer1_message = "first layer"
    window._decoded_layer2_message = "second layer"
    window._message1_buffer = ""
    window._message2_buffer = ""
    window._tooltip_map = {}
    window.help_mode_active = False
    window._update_pass_field_highlight = lambda: None
    window._update_counter = lambda: None
    event = QMouseEvent(
        QEvent.MouseButtonPress,
        QPointF(0, 0),
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier,
    )

    window.eventFilter(window.pwd_input2, event)

    assert window._currently_shown_layer == 2
    assert window.text_area.toPlainText() == "second layer"
    window.deleteLater()
    app.processEvents()


def test_successful_layer_two_decode_displays_layer_two(monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = SteganographyApp.__new__(SteganographyApp)
    QMainWindow.__init__(window)
    window.pwd_input = QLineEdit(window)
    window.pwd_input2 = QLineEdit(window)
    window.text_area = QTextBrowser(window)
    window.watermark = QLabel(window)
    window.edit_btn = QPushButton(window)
    window.copy_btn = QPushButton(window)
    window.save_btn = QPushButton(window)
    window.cancel_btn = QPushButton(window)
    window.audio = SimpleNamespace(play_sfx=lambda *_: None)
    window.current_image_path = "unused.png"
    window.delimiter = "\x00\x00\x03"
    window._editing_layer = 2
    window._currently_shown_layer = 1
    window.original_message = ""
    window._decoded_layer1_message = ""
    window._decoded_layer2_message = ""
    window._message1_buffer = ""
    window._message2_buffer = ""
    window._tooltip_map = {}
    window.help_mode_active = False
    window._set_worker = lambda _: None
    window._update_watermark = lambda: None
    window._save_password_to_list = lambda _: None
    window._status = lambda *_: None
    window._update_counter = lambda: None
    window._update_pass_field_highlight = lambda: None
    monkeypatch.setattr(Stegano, "extract_dual_layer2_blob", lambda *_: b"layer2")

    window._on_decode_result(
        "second layer", True, 2, "first-pass", "second-pass", "first layer", "dual"
    )

    assert window._currently_shown_layer == 2
    assert window.text_area.toPlainText() == "second layer"

    window.eventFilter(window.pwd_input, QEvent(QEvent.FocusIn))

    assert window._currently_shown_layer == 1
    assert window.text_area.toPlainText() == "first layer"
    assert window.original_message == "first layer"

    window._enter_edit_mode()
    window.text_area.setPlainText("edited first layer")
    window._cancel_edit()

    assert window.text_area.toPlainText() == "first layer"
    window.deleteLater()
    app.processEvents()


def test_clear_for_reuse_resets_message_state_and_protects_source(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = SteganographyApp.__new__(SteganographyApp)
    QMainWindow.__init__(window)
    source_path = tmp_path / "used.png"
    source_path.write_bytes(b"original image")
    tempdir = tempfile.TemporaryDirectory(prefix="stegano-ui-test-")
    clean_path = os.path.join(tempdir.name, "clean_cover.png")
    with open(clean_path, "wb") as clean_image:
        clean_image.write(b"clean working image")

    window._clean_cover_tempdir = None
    window._clean_cover_path = None
    window._cleared_source_path = None
    window._pending_clean_cover_tempdir = tempdir
    window._pending_clean_cover_path = clean_path
    window.current_image_path = str(source_path)
    window.pwd_input = QLineEdit(window)
    window.pwd_input.setText("old-password")
    window.pwd_input2 = QLineEdit(window)
    window.pwd_input2.setText("old-password-two")
    window.text_area = QTextBrowser(window)
    window.text_area.setPlainText("old hidden message")
    window.text_area.setReadOnly(True)
    window.watermark = QLabel(window)
    window.edit_btn = QPushButton(window)
    window.copy_btn = QPushButton(window)
    window.save_btn = QPushButton(window)
    window.cancel_btn = QPushButton(window)
    window.original_message = "old hidden message"
    window._layer2_active = True
    window._editing_layer = 2
    window._message1_buffer = "old layer one"
    window._message2_buffer = "old layer two"
    window._decoded_layer1_message = "old layer one"
    window._decoded_layer2_message = "old layer two"
    window._decoded_layer2_blob = b"old layer two blob"
    window._currently_shown_layer = 2
    window._loaded_image_format = "dual"
    window._loaded_image_has_message = True
    window._loaded_image_is_encrypted = True
    window._set_worker = lambda _: None
    window._update_watermark = lambda: None
    window._update_counter = lambda: None
    window._status = lambda *_: None
    window.audio = SimpleNamespace(play_sfx=lambda *_: None)
    window.worker_running = False
    window.delimiter = "\x00\x00\x03"

    window._on_clear_for_reuse_success("OK")

    assert window.current_image_path == clean_path
    assert window._clean_cover_path == clean_path
    assert window._cleared_source_path == str(source_path)
    assert source_path.read_bytes() == b"original image"
    assert Stegano._paths_are_same_file(str(source_path), str(source_path))
    assert not Stegano._paths_are_same_file(str(source_path), clean_path)
    suggested_name = Stegano._unique_reuse_output_name(str(tmp_path))
    assert suggested_name == "reused_image_steganosed"
    (tmp_path / f"{suggested_name}.png").write_bytes(b"existing output")
    assert Stegano._unique_reuse_output_name(str(tmp_path)) == "reused_image_steganosed_2"
    assert window.pwd_input.text() == ""
    assert window.pwd_input2.text() == ""
    assert window.text_area.toPlainText() == ""
    assert not window.text_area.isReadOnly()
    assert window._message1_buffer == ""
    assert window._message2_buffer == ""
    assert window._decoded_layer2_blob is None
    assert window._editing_layer == 1
    assert window._currently_shown_layer == 0
    assert window._loaded_image_format == "none"
    assert not window._loaded_image_has_message
    assert not window._loaded_image_is_encrypted

    decode_args = {}

    class Signal:
        def connect(self, _callback):
            pass

    class FakeDecodeWorker:
        def __init__(self, path, delimiter, pass1, pass2):
            decode_args["path"] = path
            self.decoding_finished = Signal()
            self.error = Signal()

        def start(self):
            pass

    monkeypatch.setattr(Stegano, "DecodeWorker", FakeDecodeWorker)
    window.pwd_input.setText("old-password")
    window.pwd_input2.setText("old-password-two")
    window._attempt_decode()

    assert decode_args["path"] == clean_path

    window._cleanup_clean_cover_tempdirs()
    window.deleteLater()
    app.processEvents()
