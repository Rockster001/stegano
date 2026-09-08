import hashlib
import itertools
import secrets
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
