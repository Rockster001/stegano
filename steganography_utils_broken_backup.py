import hashlib
import itertools
import secrets
import numpy as np
from PIL import Image
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

STEALTH_HEADER = hashlib.sha256(b"STEGO_MAGIC").digest()
LEGACY_HEADER = b"STEGO_MAGIC"
DUAL_HEADER = hashlib.sha256(b"STEGO_DUAL_MAGIC").digest()
DELIMITER = "\x00\x00\x03"

AES_KEY_SIZE = 32
AES_SALT_SIZE = 16
AES_IV_SIZE = 16
PBKDF2_ITERATIONS = 100000

def _encrypt_bytes_aes(data, password):
    if not password: return data
    salt = secrets.token_bytes(AES_SALT_SIZE)
    iv = secrets.token_bytes(AES_IV_SIZE)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=AES_KEY_SIZE, salt=salt, iterations=PBKDF2_ITERATIONS, backend=default_backend())
    key = kdf.derive(password.encode())
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    return salt + iv + encrypted_data

def _decrypt_bytes_aes(encrypted_data, password):
    if not password: return encrypted_data
    if len(encrypted_data) < AES_SALT_SIZE + AES_IV_SIZE: return None
    salt = encrypted_data[:AES_SALT_SIZE]
    iv = encrypted_data[AES_SALT_SIZE:AES_SALT_SIZE + AES_IV_SIZE]
    encrypted = encrypted_data[AES_SALT_SIZE + AES_IV_SIZE:]
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=AES_KEY_SIZE, salt=salt, iterations=PBKDF2_ITERATIONS, backend=default_backend())
    key = kdf.derive(password.encode())
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
    if not password: return data
    key = hashlib.sha256(password.encode()).digest()
    return bytes(b ^ k for b, k in zip(data, itertools.cycle(key)))

def _embed_bits_and_save(img_path, full_data, save_path, out_format="PNG"):
    img = Image.open(img_path)
    exif_data, icc_data, dpi_data = img.info.get("exif"), img.info.get("icc_profile"), img.info.get("dpi")
    img_rgb = img.convert("RGB")
    arr = np.array(img_rgb)
    h, w, c = arr.shape
    flat = arr.reshape(-1)
    bits = np.unpackbits(np.frombuffer(full_data, dtype=np.uint8))
    if bits.size > flat.size: raise ValueError("Message exceeds image capacity.")
    flat[:bits.size] = (flat[:bits.size] & 0xFE) | bits
    new_img = Image.fromarray(flat.reshape(h, w, c).astype(np.uint8), "RGB")
    out_format = out_format.upper()
    if out_format == "BMP": kwargs = {"format": "BMP"}
    elif out_format == "TIFF":
        kwargs = {"format": "TIFF"}
        if icc_data: kwargs["icc_profile"] = icc_data
    elif out_format == "WEBP":
        kwargs = {"format": "WEBP", "lossless": True}
        if icc_data: kwargs["icc_profile"] = icc_data
    else:
        kwargs = {"format": "PNG"}
        if exif_data: kwargs["exif"] = exif_data
        if icc_data: kwargs["icc_profile"] = icc_data
        if dpi_data: kwargs["dpi"] = dpi_data
    new_img.save(save_path, **kwargs)

def encode_image(img_path, msg, save_path, header_bytes, delim, out_format="PNG", password=""):
    payload = msg.encode("utf-8")
    if password: payload = _encrypt_bytes_aes(payload, password)
    full_data = header_bytes + payload + delim.encode("utf-8")
    _embed_bits_and_save(img_path, full_data, save_path, out_format)

def encode_dual_image(img_path, msg1, msg2, save_path, dual_header_bytes, delim, out_format="PNG", pass1="", pass2=""):
    if msg2 and not pass2:
        pass2 = pass1
    payload1 = msg1.encode("utf-8")
    if pass1: payload1 = _encrypt_bytes_aes(payload1, pass1)
    payload2 = _encrypt_bytes_aes(msg2.encode("utf-8"), pass2)
    delim_bytes = delim.encode("utf-8")
    full_data = dual_header_bytes + payload1 + delim_bytes + payload2 + delim_bytes
    _embed_bits_and_save(img_path, full_data, save_path, out_format)

def decode_image(img_path, delim, password=""):
    img = Image.open(img_path).convert("RGB")
    arr = np.array(img)
    flat = arr.reshape(-1) & 1
    usable_len = (flat.size // 8) * 8
    if usable_len == 0: return "", False
    raw_bytes = np.packbits(flat[:usable_len]).tobytes()
    delim_bytes = delim.encode("utf-8")
    idx_stealth = raw_bytes.find(STEALTH_HEADER)
    idx_legacy = raw_bytes.find(LEGACY_HEADER)
    if idx_stealth != -1:
        idx = idx_stealth; header_len = len(STEALTH_HEADER)
    elif idx_legacy != -1:
        idx = idx_legacy; header_len = len(LEGACY_HEADER)
    else:
        return "", False
    payload_start = idx + header_len
    d_idx = raw_bytes[payload_start:].find(delim_bytes)
    if d_idx == -1: return "", False
    payload_bytes = raw_bytes[payload_start : payload_start + d_idx]
    if password:
        try:
            decrypted_bytes = _decrypt_bytes_aes(payload_bytes, password)
            if decrypted_bytes is not None:
                text = decrypted_bytes.decode("utf-8")
                return text, True
        except (UnicodeDecodeError, ValueError, TypeError):
            pass
        try:
            decrypted_bytes = _encrypt_bytes(payload_bytes, password)
            text = decrypted_bytes.decode("utf-8")
            return text, True
        except (UnicodeDecodeError, ValueError, TypeError):
            pass
        try:
            text = payload_bytes.decode("utf-8")
            return text, True
        except UnicodeDecodeError:
            return "", False
    try:
        text = payload_bytes.decode("utf-8")
        return text, False
    except UnicodeDecodeError:
        return "", False

def extract_dual_layer2_blob(img_path, delim):
    layer1_bytes, layer2_bytes = _extract_dual_layers(img_path, delim)
    return layer2_bytes

def encode_dual_image_from_blobs(img_path, msg1, pass1, layer2_blob, dual_header_bytes, delim, save_path, out_format="PNG"):
    if not layer2_blob:
        raise ValueError("Refusing to compose dual file: original layer 2 bytes are missing.")
    delim_bytes = delim.encode("utf-8")
    if delim_bytes in layer2_blob:
        raise ValueError("Refusing to compose dual file: delimiter sequence found inside layer 2 bytes.")
    payload1 = msg1.encode("utf-8")
    if pass1: payload1 = _encrypt_bytes_aes(payload1, pass1)
    full_data = dual_header_bytes + payload1 + delim_bytes + layer2_blob + delim_bytes
    _embed_bits_and_save(img_path, full_data, save_path, out_format)

def _extract_raw_lsb_bytes(img_path):
    img = Image.open(img_path).convert("RGB")
    arr = np.array(img)
    flat = arr.reshape(-1) & 1
    usable_len = (flat.size // 8) * 8
    if usable_len == 0: return b""
    return np.packbits(flat[:usable_len]).tobytes()

def _extract_dual_layers(img_path, delim):
    raw_bytes = _extract_raw_lsb_bytes(img_path)
    if not raw_bytes:
        return None, None
    idx = raw_bytes.find(DUAL_HEADER)
    if idx == -1:
        return None, None
    payload_start = idx + len(DUAL_HEADER)
    delim_bytes = delim.encode("utf-8")
    d1_idx = raw_bytes[payload_start:].find(delim_bytes)
    if d1_idx == -1:
        return None, None
    layer1_end = payload_start + d1_idx
    layer1_bytes = raw_bytes[payload_start:layer1_end]
    layer2_start = layer1_end + len(delim_bytes)
    d2_idx = raw_bytes[layer2_start:].find(delim_bytes)
    if d2_idx == -1:
        raise ValueError("Corrupted dual-layer file: layer 2 terminator is missing. File left unmodified.")
    layer2_end = layer2_start + d2_idx
    layer2_bytes = raw_bytes[layer2_start:layer2_end]
    return layer1_bytes, layer2_bytes

def _try_decrypt_payload(payload_bytes, password):
    if password:
        try:
            decrypted_bytes = _decrypt_bytes_aes(payload_bytes, password)
            if decrypted_bytes is not None:
                return decrypted_bytes.decode("utf-8"), True
        except (UnicodeDecodeError, ValueError, TypeError):
            pass
        try:
            decrypted_bytes = _encrypt_bytes(payload_bytes, password)
            return decrypted_bytes.decode("utf-8"), True
        except (UnicodeDecodeError, ValueError, TypeError):
            pass
        try:
            return payload_bytes.decode("utf-8"), False
        except UnicodeDecodeError:
            return None, False
    try:
        return payload_bytes.decode("utf-8"), False
    except UnicodeDecodeError:
        return None, False

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
            return 'none'
        if raw_bytes.find(DUAL_HEADER) != -1:
            return 'dual'
        if raw_bytes.find(STEALTH_HEADER) != -1 or raw_bytes.find(LEGACY_HEADER) != -1:
            return 'single'
        return 'none'
    except Exception:
        return 'none'

STEALTH_HEADER = hashlib.sha256(b"STEGO_MAGIC").digest()
LEGACY_HEADER = b"STEGO_MAGIC"

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
