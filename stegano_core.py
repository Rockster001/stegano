import base64
import binascii
import hashlib
import itertools
import secrets

import numpy as np
from PIL import Image
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from stegano_config import (
    AES_IV_SIZE,
    AES_KEY_SIZE,
    AES_SALT_SIZE,
    DUAL_HEADER,
    DELIMITER,
    LEGACY_DUAL_HEADER,
    LEGACY_HEADER,
    PBKDF2_ITERATIONS,
    STEALTH_HEADER,
)

AES_GCM_MAGIC = b"STG2:"
_AES_GCM_NONCE_SIZE = 12
_AES_GCM_TAG_SIZE = 16
_AES_GCM_ITERATIONS = 600_000

__all__ = [
    "STEALTH_HEADER",
    "LEGACY_HEADER",
    "DUAL_HEADER",
    "LEGACY_DUAL_HEADER",
    "DELIMITER",
    "AES_KEY_SIZE",
    "AES_SALT_SIZE",
    "AES_IV_SIZE",
    "AES_GCM_MAGIC",
    "PBKDF2_ITERATIONS",
    "clear_lsb_image",
    "_encrypt_bytes_aes",
    "_decrypt_bytes_aes",
    "estimate_encrypted_payload_len",
    "_encrypt_bytes",
    "_decrypt_payload_bytes",
    "_embed_bits_and_save",
    "encode_image",
    "encode_dual_image",
    "decode_image",
    "_extract_raw_lsb_bytes",
    "_extract_dual_layers",
    "_try_decrypt_payload",
    "decode_dual_image",
    "detect_message_format",
    "check_image_for_message",
    "extract_dual_layer2_blob",
    "encode_dual_image_from_blobs",
]


def _derive_key(password, salt, iterations):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=AES_KEY_SIZE,
        salt=salt,
        iterations=iterations,
        backend=default_backend(),
    )
    return kdf.derive(password.encode())


def _encrypt_bytes_aes(data, password):
    if not password:
        return data
    salt = secrets.token_bytes(AES_SALT_SIZE)
    nonce = secrets.token_bytes(_AES_GCM_NONCE_SIZE)
    key = _derive_key(password, salt, _AES_GCM_ITERATIONS)
    encrypted = AESGCM(key).encrypt(nonce, data, None)
    envelope = salt + nonce + encrypted
    return AES_GCM_MAGIC + base64.b64encode(envelope)


def estimate_encrypted_payload_len(raw_len):
    envelope_len = AES_SALT_SIZE + _AES_GCM_NONCE_SIZE + _AES_GCM_TAG_SIZE + raw_len
    return len(AES_GCM_MAGIC) + ((envelope_len + 2) // 3) * 4


def _decrypt_bytes_aes(encrypted_data, password):
    if encrypted_data.startswith(AES_GCM_MAGIC):
        if not password:
            return None
        try:
            envelope = base64.b64decode(
                encrypted_data[len(AES_GCM_MAGIC) :],
                validate=True,
            )
            minimum_len = AES_SALT_SIZE + _AES_GCM_NONCE_SIZE + _AES_GCM_TAG_SIZE
            if len(envelope) < minimum_len:
                return None
            salt = envelope[:AES_SALT_SIZE]
            nonce_start = AES_SALT_SIZE
            nonce_end = nonce_start + _AES_GCM_NONCE_SIZE
            nonce = envelope[nonce_start:nonce_end]
            key = _derive_key(password, salt, _AES_GCM_ITERATIONS)
            return AESGCM(key).decrypt(nonce, envelope[nonce_end:], None)
        except (binascii.Error, InvalidTag, TypeError, ValueError):
            return None

    if not password:
        return encrypted_data
    if len(encrypted_data) < AES_SALT_SIZE + AES_IV_SIZE:
        return None
    salt = encrypted_data[:AES_SALT_SIZE]
    iv = encrypted_data[AES_SALT_SIZE : AES_SALT_SIZE + AES_IV_SIZE]
    encrypted = encrypted_data[AES_SALT_SIZE + AES_IV_SIZE :]
    key = _derive_key(password, salt, PBKDF2_ITERATIONS)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    try:
        padded_data = decryptor.update(encrypted) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        return data
    except Exception:
        return None


def _encrypt_bytes(data, password):
    """Legacy XOR helper retained for compatibility with older payloads."""
    if not password:
        return data
    key = hashlib.sha256(password.encode()).digest()
    return bytes(b ^ k for b, k in zip(data, itertools.cycle(key)))


def _decrypt_payload_bytes(payload_bytes, password):
    """Return (decoded_bytes, was_encrypted)."""
    if payload_bytes.startswith(AES_GCM_MAGIC):
        if not password:
            return None, False
        try:
            decrypted = _decrypt_bytes_aes(payload_bytes, password)
            if decrypted is None:
                return None, False
            decrypted.decode("utf-8")
            return decrypted, True
        except (UnicodeDecodeError, ValueError, TypeError):
            return None, False

    if not password:
        try:
            payload_bytes.decode("utf-8")
            return payload_bytes, False
        except UnicodeDecodeError:
            return None, False

    try:
        decrypted = _decrypt_bytes_aes(payload_bytes, password)
        if decrypted is not None:
            decrypted.decode("utf-8")
            return decrypted, True
    except (UnicodeDecodeError, ValueError, TypeError):
        pass

    try:
        payload_bytes.decode("utf-8")
        return payload_bytes, False
    except UnicodeDecodeError:
        return None, False


def _image_rgb_data(img_path):
    with Image.open(img_path) as img:
        metadata = {
            "exif": img.info.get("exif"),
            "icc_profile": img.info.get("icc_profile"),
            "dpi": img.info.get("dpi"),
        }
        arr = np.array(img.convert("RGB"))
    return arr, metadata


def _save_rgb_array(arr, metadata, save_path, out_format):
    icc_data = metadata["icc_profile"]
    out_format = out_format.upper()
    if out_format == "BMP":
        kwargs = {"format": "BMP"}
    elif out_format == "TIFF":
        kwargs = {"format": "TIFF"}
        if icc_data:
            kwargs["icc_profile"] = icc_data
    elif out_format == "WEBP":
        kwargs = {"format": "WEBP", "lossless": True}
        if icc_data:
            kwargs["icc_profile"] = icc_data
    else:
        kwargs = {"format": "PNG"}
        if metadata["exif"]:
            kwargs["exif"] = metadata["exif"]
        if icc_data:
            kwargs["icc_profile"] = icc_data
        if metadata["dpi"]:
            kwargs["dpi"] = metadata["dpi"]
    Image.fromarray(arr.astype(np.uint8, copy=False), "RGB").save(save_path, **kwargs)


def _embed_bits_and_save(img_path, full_data, save_path, out_format="PNG"):
    arr, metadata = _image_rgb_data(img_path)
    flat = arr.reshape(-1)
    bits = np.unpackbits(np.frombuffer(full_data, dtype=np.uint8))
    if bits.size > flat.size:
        raise ValueError("Message exceeds image capacity.")
    flat[: bits.size] = (flat[: bits.size] & 0xFE) | bits
    _save_rgb_array(arr, metadata, save_path, out_format)


def clear_lsb_image(img_path, save_path):
    """Write a clean RGB working copy without retaining any existing LSB payload."""
    arr, metadata = _image_rgb_data(img_path)
    arr &= 0xFE
    _save_rgb_array(arr, metadata, save_path, "PNG")


def encode_image(img_path, msg, save_path, header_bytes, delim, out_format="PNG", password=""):
    payload = msg.encode("utf-8")
    if password:
        payload = _encrypt_bytes_aes(payload, password)
    full_data = header_bytes + payload + delim.encode("utf-8")
    _embed_bits_and_save(img_path, full_data, save_path, out_format)


def encode_dual_image(img_path, msg1, msg2, save_path, dual_header_bytes, delim, out_format="PNG", pass1="", pass2=""):
    if msg2 and not pass2:
        pass2 = pass1
    payload1 = msg1.encode("utf-8")
    if pass1:
        payload1 = _encrypt_bytes_aes(payload1, pass1)
    payload2 = _encrypt_bytes_aes(msg2.encode("utf-8"), pass2)
    delim_bytes = delim.encode("utf-8")
    full_data = dual_header_bytes + payload1 + delim_bytes + payload2 + delim_bytes
    _embed_bits_and_save(img_path, full_data, save_path, out_format)


def decode_image(img_path, delim, password=""):
    try:
        with Image.open(img_path) as img:
            arr = np.array(img.convert("RGB"))
    except Exception:
        return "", False
    flat = arr.reshape(-1) & 1
    usable_len = (flat.size // 8) * 8
    if usable_len == 0:
        return "", False
    raw_bytes = np.packbits(flat[:usable_len]).tobytes()
    delim_bytes = delim.encode("utf-8")
    idx, header_len = _find_message_header(raw_bytes, STEALTH_HEADER, LEGACY_HEADER)
    if idx == -1:
        return "", False
    payload_start = idx + header_len
    d_idx = raw_bytes[payload_start:].find(delim_bytes)
    if d_idx == -1:
        return "", False
    payload_bytes = raw_bytes[payload_start : payload_start + d_idx]
    decrypted_bytes, was_encrypted = _decrypt_payload_bytes(payload_bytes, password)
    if decrypted_bytes is None:
        return "", False
    return decrypted_bytes.decode("utf-8"), was_encrypted


def _find_message_header(raw_bytes, *header_candidates):
    for header in header_candidates:
        idx = raw_bytes.find(header)
        if idx != -1:
            return idx, len(header)
    return -1, 0


def _extract_raw_lsb_bytes(img_path):
    try:
        with Image.open(img_path) as img:
            arr = np.array(img.convert("RGB"))
    except Exception:
        return b""
    flat = arr.reshape(-1) & 1
    usable_len = (flat.size // 8) * 8
    if usable_len == 0:
        return b""
    return np.packbits(flat[:usable_len]).tobytes()


def _extract_dual_layers(img_path, delim):
    raw_bytes = _extract_raw_lsb_bytes(img_path)
    if not raw_bytes:
        return None, None

    idx, header_len = _find_message_header(raw_bytes, DUAL_HEADER, LEGACY_DUAL_HEADER)
    if idx == -1:
        return None, None

    payload_start = idx + header_len
    delim_bytes = delim.encode("utf-8")
    d1_idx = raw_bytes[payload_start:].find(delim_bytes)
    if d1_idx == -1:
        return None, None
    layer1_end = payload_start + d1_idx
    layer1_bytes = raw_bytes[payload_start:layer1_end]
    layer2_start = layer1_end + len(delim_bytes)
    d2_idx = raw_bytes[layer2_start:].find(delim_bytes)
    if d2_idx == -1:
        return layer1_bytes, None
    layer2_end = layer2_start + d2_idx
    layer2_bytes = raw_bytes[layer2_start:layer2_end]
    return layer1_bytes, layer2_bytes


def _try_decrypt_payload(payload_bytes, password):
    decrypted_bytes, was_encrypted = _decrypt_payload_bytes(payload_bytes, password)
    if decrypted_bytes is None:
        return None, False
    return decrypted_bytes.decode("utf-8"), was_encrypted


def decode_dual_image(img_path, delim, pass1="", pass2=""):
    layer1_bytes, layer2_bytes = _extract_dual_layers(img_path, delim)
    if layer1_bytes is None:
        return "", 0, False, ""
    layer1_text, layer1_was_enc = _try_decrypt_payload(layer1_bytes, pass1)
    if layer1_text is None:
        return "", 0, False, ""
    if layer2_bytes:
        layer2_text, layer2_was_enc = (None, False)
        if pass2:
            layer2_text, layer2_was_enc = _try_decrypt_payload(layer2_bytes, pass2)
        if layer2_text is None and pass1 and pass1 != pass2:
            layer2_text, layer2_was_enc = _try_decrypt_payload(layer2_bytes, pass1)
        if layer2_text is None and not pass2:
            layer2_text, layer2_was_enc = _try_decrypt_payload(layer2_bytes, "")
        if layer2_text is not None:
            return layer2_text, 2, layer2_was_enc, layer1_text
        if pass2:
            raise ValueError("Incorrect password.")
    return layer1_text, 1, layer1_was_enc, layer1_text


def detect_message_format(img_path, delim):
    try:
        raw_bytes = _extract_raw_lsb_bytes(img_path)
        if not raw_bytes:
            return "none"
        if _find_message_header(raw_bytes, DUAL_HEADER, LEGACY_DUAL_HEADER)[0] != -1:
            return "dual"
        if _find_message_header(raw_bytes, STEALTH_HEADER, LEGACY_HEADER)[0] != -1:
            return "single"
        return "none"
    except Exception:
        return "none"


def check_image_for_message(img_path, delim):
    try:
        with Image.open(img_path) as img:
            arr = np.array(img.convert("RGB"))
    except Exception:
        return False, False
    flat = arr.reshape(-1) & 1
    usable_len = (flat.size // 8) * 8
    if usable_len == 0:
        return False, False
    raw_bytes = np.packbits(flat[:usable_len]).tobytes()
    delim_bytes = delim.encode("utf-8")
    idx, header_len = _find_message_header(raw_bytes, STEALTH_HEADER, LEGACY_HEADER)
    if idx == -1:
        return False, False
    payload_start = idx + header_len
    d_idx = raw_bytes[payload_start:].find(delim_bytes)
    if d_idx == -1:
        return False, False
    payload_bytes = raw_bytes[payload_start : payload_start + d_idx]
    if payload_bytes.startswith(AES_GCM_MAGIC):
        return True, True
    try:
        payload_bytes.decode("utf-8")
        return True, False
    except UnicodeDecodeError:
        return True, True


def extract_dual_layer2_blob(img_path, delim):
    raw_bytes = _extract_raw_lsb_bytes(img_path)
    if not raw_bytes:
        return None
    start = raw_bytes.find(DUAL_HEADER)
    if start == -1:
        start = raw_bytes.find(LEGACY_DUAL_HEADER)
    if start == -1:
        return None
    d = delim.encode("utf-8")
    base = start + len(DUAL_HEADER if raw_bytes.find(DUAL_HEADER) != -1 else LEGACY_DUAL_HEADER)
    first = raw_bytes.find(d, base)
    if first == -1:
        return None
    second = raw_bytes.find(d, first + len(d))
    if second == -1:
        raise ValueError("Layer 2 terminator not found.")
    return raw_bytes[first + len(d) : second]


def encode_dual_image_from_blobs(img_path, msg1, pass1, layer2_blob, dual_header_bytes, delim, save_path, out_format="PNG"):
    if not layer2_blob:
        raise ValueError("No Layer 2 content to preserve.")
    d = delim.encode("utf-8")
    if d in layer2_blob:
        raise ValueError("Layer 2 content contains the delimiter.")
    payload1 = msg1.encode("utf-8")
    if pass1:
        payload1 = _encrypt_bytes_aes(payload1, pass1)
    full_data = dual_header_bytes + payload1 + d + layer2_blob + d
    _embed_bits_and_save(img_path, full_data, save_path, out_format)
