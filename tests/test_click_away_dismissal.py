import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt5.QtCore import QEventLoop, Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QWidget

from password_utils import SavedPasswordsDialog
from ui_components import ZoomImageViewer


def _app():
    return QApplication.instance() or QApplication([])


def test_image_viewer_closes_and_consumes_click_outside(tmp_path):
    app = _app()
    image_path = tmp_path / "image.png"
    Image.new("RGB", (20, 20), "blue").save(str(image_path))
    parent = QWidget()
    outside_button = QPushButton("Outside", parent)
    outside_button.show()
    clicked = []
    outside_button.clicked.connect(lambda: clicked.append(True))
    viewer = ZoomImageViewer(str(image_path), parent)
    viewer.show()
    app.processEvents()
    QTest.mouseClick(viewer.zoom_lbl, Qt.LeftButton)
    assert viewer.isVisible()

    QTest.mouseClick(outside_button, Qt.LeftButton)

    assert not viewer.isVisible()
    assert clicked == []
    parent.close()


def test_saved_password_dialog_closes_without_using_selection_on_outside_click():
    app = _app()
    parent = QWidget()
    parent.show()
    outside_button = QPushButton("Outside", parent)
    outside_button.show()
    clicked = []
    outside_button.clicked.connect(lambda: clicked.append(True))
    dialog = SavedPasswordsDialog(["password-one"], parent)
    fallback_closed = []
    fallback_timer = QTimer(dialog)
    fallback_timer.setSingleShot(True)
    loop = QEventLoop()
    assert not dialog.isModal()

    def close_if_click_away_failed():
        fallback_closed.append(True)
        dialog.reject()

    dialog.finished.connect(loop.quit)
    QTimer.singleShot(0, lambda: QTest.mouseClick(outside_button, Qt.LeftButton))
    fallback_timer.timeout.connect(close_if_click_away_failed)
    fallback_timer.start(500)
    dialog.show()
    loop.exec_()
    fallback_timer.stop()

    assert not dialog.isVisible()
    assert dialog.result() == QDialog.Rejected
    assert dialog.selected_password is None
    assert clicked == []
    assert fallback_closed == []
    parent.close()
