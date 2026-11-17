import os
import base64
from pathlib import Path

import pytest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PyQt5.QtWidgets import QApplication

from stegano_config import AES_IV_SIZE, AES_KEY_SIZE, AES_SALT_SIZE, DELIMITER, DUAL_HEADER, LEGACY_DUAL_HEADER, LEGACY_HEADER, PBKDF2_ITERATIONS, STEALTH_HEADER
from stegano_core import AES_GCM_MAGIC, _decrypt_bytes_aes, _decrypt_payload_bytes, _embed_bits_and_save, _encrypt_bytes_aes, check_image_for_message, clear_lsb_image, detect_message_format, estimate_encrypted_payload_len
from steganography_utils import decode_dual_image, decode_image, encode_dual_image, encode_image
from workers import DecodeWorker


def _make_image(path: Path, size=(64, 64)) -> None:
    image = Image.new("RGB", size, color=(10, 20, 30))
    image.save(path)


def _legacy_encrypt(data: bytes, password: str) -> bytes:
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


def test_authenticated_payload_roundtrip_rejects_tampering_and_missing_password():
    message = "authenticated message".encode("utf-8")
    encrypted = _encrypt_bytes_aes(message, "correct")

    assert encrypted.startswith(AES_GCM_MAGIC)
    assert _decrypt_bytes_aes(encrypted, "correct") == message
    assert estimate_encrypted_payload_len(len(message)) == len(encrypted)
    assert _decrypt_payload_bytes(encrypted, "") == (None, False)
    assert _decrypt_payload_bytes(encrypted, "wrong") == (None, False)

    tampered_envelope = bytearray(base64.b64decode(encrypted[len(AES_GCM_MAGIC) :]))
    tampered_envelope[-1] ^= 1
    tampered = AES_GCM_MAGIC + base64.b64encode(tampered_envelope)
    assert _decrypt_bytes_aes(tampered, "correct") is None


def test_legacy_single_layer_aes_payload_remains_decodable(tmp_path):
    cover = tmp_path / "cover.png"
    encoded_path = tmp_path / "legacy.png"
    _make_image(cover)
    message = "legacy encrypted message"
    payload = _legacy_encrypt(message.encode("utf-8"), "legacy-pass")
    _embed_bits_and_save(
        str(cover),
        LEGACY_HEADER + payload + DELIMITER.encode("utf-8"),
        str(encoded_path),
    )

    assert decode_image(str(encoded_path), DELIMITER, "legacy-pass") == (message, True)


def test_legacy_dual_layer_aes_payload_remains_decodable(tmp_path):
    cover = tmp_path / "cover.png"
    encoded_path = tmp_path / "legacy_dual.png"
    _make_image(cover)
    layer1 = _legacy_encrypt(b"legacy outer message", "outer-pass")
    layer2 = _legacy_encrypt(b"legacy inner message", "inner-pass")
    delim = DELIMITER.encode("utf-8")
    _embed_bits_and_save(
        str(cover),
        LEGACY_DUAL_HEADER + layer1 + delim + layer2 + delim,
        str(encoded_path),
    )

    assert decode_dual_image(
        str(encoded_path), DELIMITER, pass1="outer-pass", pass2="inner-pass"
    ) == ("legacy inner message", 2, True, "legacy outer message")


def test_authenticated_single_layer_is_detected_as_encrypted_without_password(tmp_path):
    cover = tmp_path / "cover.png"
    encoded_path = tmp_path / "secret.png"
    _make_image(cover)
    encode_image(
        str(cover),
        "hidden",
        str(encoded_path),
        LEGACY_HEADER,
        DELIMITER,
        password="secret",
    )

    assert check_image_for_message(str(encoded_path), DELIMITER) == (True, True)
    assert decode_image(str(encoded_path), DELIMITER) == ("", False)


def test_encode_decode_roundtrip_with_password(tmp_path):
    image_path = tmp_path / "cover.png"
    encoded_path = tmp_path / "secret.png"
    _make_image(image_path)

    message = "hello from stegano"
    encode_image(str(image_path), message, str(encoded_path), b"STEGO_MAGIC", DELIMITER, password="hunter2")

    decoded, was_encrypted = decode_image(str(encoded_path), DELIMITER, password="hunter2")

    assert decoded == message
    assert was_encrypted is True


def test_wrong_password_fails(tmp_path):
    image_path = tmp_path / "cover.png"
    encoded_path = tmp_path / "secret.png"
    _make_image(image_path)

    encode_image(str(image_path), "hidden", str(encoded_path), b"STEGO_MAGIC", DELIMITER, password="correct")

    decoded, was_encrypted = decode_image(str(encoded_path), DELIMITER, password="wrong")

    assert decoded == ""
    assert was_encrypted is False


@pytest.mark.parametrize(
    ("layer_count", "pass1", "pass2"),
    [
        (1, "", ""),
        (1, "single-pass", ""),
        (2, "", ""),
        (2, "outer-pass", "inner-pass"),
    ],
)
def test_clear_lsb_image_scrubs_payload_without_changing_source(
    tmp_path, layer_count, pass1, pass2
):
    cover_path = tmp_path / "cover.png"
    encoded_path = tmp_path / "used.png"
    clean_path = tmp_path / "clean.png"
    fresh_path = tmp_path / "fresh.png"
    _make_image(cover_path)

    if layer_count == 1:
        encode_image(
            str(cover_path), "previous message", str(encoded_path),
            STEALTH_HEADER, DELIMITER, password=pass1,
        )
    else:
        encode_dual_image(
            str(cover_path), "outer message", "inner message", str(encoded_path),
            DUAL_HEADER, DELIMITER, pass1=pass1, pass2=pass2,
        )

    original_bytes = encoded_path.read_bytes()
    clear_lsb_image(str(encoded_path), str(clean_path))

    assert encoded_path.read_bytes() == original_bytes
    assert detect_message_format(str(clean_path), DELIMITER) == "none"
    with Image.open(clean_path) as clean_image:
        assert all(
            channel % 2 == 0
            for pixel in clean_image.convert("RGB").getdata()
            for channel in pixel
        )

    encode_image(
        str(clean_path), "fresh message", str(fresh_path),
        STEALTH_HEADER, DELIMITER, password="new-pass",
    )
    assert decode_image(str(fresh_path), DELIMITER, "new-pass") == (
        "fresh message",
        True,
    )


def test_dual_layer_roundtrip(tmp_path):
    image_path = tmp_path / "cover.png"
    encoded_path = tmp_path / "dual.png"
    _make_image(image_path)

    encode_dual_image(
        str(image_path),
        "outer secret",
        "inner secret",
        str(encoded_path),
        b"STEGO_DUAL_MAGIC",
        DELIMITER,
        pass1="alpha",
        pass2="beta",
    )

    layer2, layer_count, was_encrypted, layer1 = decode_dual_image(str(encoded_path), DELIMITER, pass1="alpha", pass2="beta")

    assert layer_count == 2
    assert layer1 == "outer secret"
    assert layer2 == "inner secret"
    assert was_encrypted is True


def test_invalid_image_returns_clean_failure(tmp_path):
    invalid_path = tmp_path / "not_an_image.png"
    invalid_path.write_bytes(b"not a real image")

    assert decode_image(str(invalid_path), DELIMITER) == ("", False)


def test_decode_worker_emits_format_metadata(tmp_path):
    app = QApplication.instance() or QApplication([])
    image_path = tmp_path / "cover.png"
    encoded_path = tmp_path / "decoded.png"
    _make_image(image_path)

    encode_image(str(image_path), "hello from worker", str(encoded_path), b"STEGO_MAGIC", DELIMITER, password="hunter2")

    seen = {}
    worker = DecodeWorker(str(encoded_path), DELIMITER, "hunter2", "")
    worker.decoding_finished.connect(
        lambda msg, is_encrypted, layer, layer1_msg, fmt: seen.update(
            {"msg": msg, "is_encrypted": is_encrypted, "layer": layer, "layer1_msg": layer1_msg, "fmt": fmt}
        )
    )
    worker.run()

    assert seen == {
        "msg": "hello from worker",
        "is_encrypted": True,
        "layer": 1,
        "layer1_msg": "hello from worker",
        "fmt": "single",
    }
    app.processEvents()
