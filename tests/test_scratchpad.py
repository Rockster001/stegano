import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt5.QtWidgets import QApplication, QMessageBox

from app_paths import local_app_data_dir
from scratchpad import ScratchpadStorageError, ScratchpadStore, ScratchpadWindow
from stegano_core import clear_lsb_image
from Stegano import SteganographyApp


def _app():
    return QApplication.instance() or QApplication([])


def _store(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (64, 64), "navy").save(str(source))
    return ScratchpadStore(str(tmp_path / "app-data"), str(source))


def test_scratchpad_ciphertext_roundtrips_with_persistent_background_key(tmp_path):
    store = _store(tmp_path)
    original_password = store.password
    store.save("private scratchpad text")

    restarted_store = ScratchpadStore(store.data_dir, store.bundled_background_path)

    assert restarted_store.password == original_password
    assert restarted_store.load() == "private scratchpad text"
    with open(store.scratchpad_path, "rb") as saved_file:
        assert b"private scratchpad text" not in saved_file.read()


def test_timestamp_regenerates_key_if_hidden_payload_is_lost(tmp_path):
    store = _store(tmp_path)
    store.save("recoverable while timestamp remains")
    background_stat = os.stat(store.background_path)
    clean_background = tmp_path / "clean.png"
    clear_lsb_image(store.background_path, str(clean_background))
    os.utime(
        str(clean_background),
        ns=(background_stat.st_atime_ns, background_stat.st_mtime_ns),
    )
    os.replace(str(clean_background), store.background_path)

    recovered_store = ScratchpadStore(store.data_dir, store.bundled_background_path)

    assert recovered_store.password == store.password
    assert recovered_store.load() == "recoverable while timestamp remains"


def test_changed_timestamp_starts_new_key_after_hidden_payload_loss(tmp_path):
    store = _store(tmp_path)
    store.save("previous snapshot")
    background_stat = os.stat(store.background_path)
    clean_background = tmp_path / "clean.png"
    clear_lsb_image(store.background_path, str(clean_background))
    os.utime(
        str(clean_background),
        ns=(
            background_stat.st_atime_ns,
            background_stat.st_mtime_ns + 1_000_000_000,
        ),
    )
    os.replace(str(clean_background), store.background_path)

    new_store = ScratchpadStore(store.data_dir, store.bundled_background_path)

    assert new_store.password != store.password
    try:
        new_store.load()
    except ScratchpadStorageError as exc:
        assert "could not be decrypted" in str(exc)
    else:
        raise AssertionError("A changed timestamp must not decrypt old text.")


def test_clear_preserves_saved_snapshot_and_restore_requires_confirmation(
    tmp_path, monkeypatch
):
    app = _app()
    store = _store(tmp_path)
    store.save("saved snapshot")
    window = ScratchpadWindow(store, "current text")
    asked = []

    def confirm_restore(*args):
        asked.append(True)
        return QMessageBox.Yes

    monkeypatch.setattr(QMessageBox, "question", confirm_restore)
    window._clear()

    assert store.load() == "saved snapshot"

    window.editor.setPlainText("new current text")
    window._restore()

    assert asked == [True]
    assert window.editor.toPlainText() == "saved snapshot"
    window.close()
    app.processEvents()


def test_saving_empty_pad_does_not_remove_restore_snapshot(tmp_path):
    app = _app()
    store = _store(tmp_path)
    store.save("saved snapshot")
    window = ScratchpadWindow(store)

    window._save()

    assert store.load() == "saved snapshot"
    assert "Nothing to save" in window.status_label.text()
    window.close()
    app.processEvents()


def test_close_persistence_saves_nonempty_and_deletes_empty(tmp_path):
    store = _store(tmp_path)
    app_window = SteganographyApp.__new__(SteganographyApp)
    app_window.scratchpad_store = store
    app_window._scratchpad_window = None
    app_window._scratchpad_text = "kept between sessions"
    app_window._scratchpad_storage_warning = None

    app_window._persist_scratchpad()

    assert store.load() == "kept between sessions"

    app_window._scratchpad_text = ""
    app_window._persist_scratchpad()

    assert store.load() == ""
    assert not os.path.exists(store.scratchpad_path)


def test_local_app_data_path_is_under_current_user(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert local_app_data_dir() == os.path.join(str(tmp_path), "Stegano")
