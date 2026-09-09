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
