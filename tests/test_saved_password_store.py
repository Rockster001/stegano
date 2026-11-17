import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QSettings

from saved_password_store import (
    SavedPasswordStorageError,
    SavedPasswordStore,
    protect_passwords,
    unprotect_passwords,
)
from stegano_config import AES_IV_SIZE, AES_KEY_SIZE, AES_SALT_SIZE, PBKDF2_ITERATIONS
from stegano_core import _decrypt_bytes_aes, _encrypt_bytes_aes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def _legacy_encrypt(data, password):
    salt = b"s" * AES_SALT_SIZE
    iv = b"i" * AES_IV_SIZE
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=AES_KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend(),
    )
    key = kdf.derive(password.encode())
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    return salt + iv + encryptor.update(padded_data) + encryptor.finalize()


def _settings(path):
    return QSettings(str(path), QSettings.IniFormat)


def test_dpapi_protected_saved_passwords_roundtrip():
    passwords = ["first", "unicode-秘密", "contains spaces"]

    encrypted = protect_passwords(passwords)

    assert encrypted != b""
    assert unprotect_passwords(encrypted) == passwords


def test_tampered_dpapi_data_is_rejected():
    encrypted = bytearray(protect_passwords(["secret"]))
    encrypted[-1] ^= 1

    try:
        unprotect_passwords(bytes(encrypted))
    except SavedPasswordStorageError:
        pass
    else:
        raise AssertionError("Tampered DPAPI data should not be accepted.")


def test_legacy_saved_passwords_migrate_and_remove_old_copy(tmp_path):
    settings = _settings(tmp_path / "settings.ini")
    legacy_key = "legacy-key"
    settings.setValue(
        "savedPasswords",
        [
            _encrypt_bytes_aes(b"new-format legacy entry", legacy_key).hex(),
            _legacy_encrypt(b"old-format legacy entry", legacy_key).hex(),
        ],
    )
    settings.sync()
    store = SavedPasswordStore(settings, legacy_key, _decrypt_bytes_aes)

    assert store.load() == ["new-format legacy entry", "old-format legacy entry"]
    assert settings.contains("savedPasswordsDpapiV1")
    assert not settings.contains("savedPasswords")
    assert store.load() == ["new-format legacy entry", "old-format legacy entry"]


def test_corrupt_legacy_entry_is_not_deleted_or_overwritten(tmp_path):
    settings = _settings(tmp_path / "settings.ini")
    original = ["not-hex"]
    settings.setValue("savedPasswords", original)
    settings.sync()
    store = SavedPasswordStore(settings, "legacy-key", _decrypt_bytes_aes)

    try:
        store.load()
    except SavedPasswordStorageError as exc:
        assert "left unchanged" in str(exc)
    else:
        raise AssertionError("Corrupt legacy data should block migration.")

    assert settings.value("savedPasswords", [], type=list) == original
    assert not settings.contains("savedPasswordsDpapiV1")
