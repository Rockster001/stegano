import ctypes
import json
import sys
from ctypes import wintypes

from PyQt5.QtCore import QSettings

from stegano_config import MAX_SAVED_PASSWORDS


_CRYPTPROTECT_UI_FORBIDDEN = 0x1
_PROTECTED_KEY = "savedPasswordsDpapiV1"
_LEGACY_KEY = "savedPasswords"


class SavedPasswordStorageError(Exception):
    pass


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def _dpapi_transform(data, protect):
    if sys.platform != "win32":
        raise SavedPasswordStorageError("Saved-password protection requires Windows.")
    if not data:
        action = "protect" if protect else "unprotect"
        raise SavedPasswordStorageError(
            "Cannot %s empty saved-password data." % action
        )

    input_buffer = ctypes.create_string_buffer(data, len(data))
    input_blob = _DataBlob(
        len(data),
        ctypes.cast(input_buffer, ctypes.POINTER(ctypes.c_ubyte)),
    )
    output_blob = _DataBlob()

    try:
        crypt32 = ctypes.WinDLL("crypt32.dll", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)
    except OSError as exc:
        raise SavedPasswordStorageError("Windows DPAPI is unavailable.") from exc

    protect_data = crypt32.CryptProtectData
    protect_data.argtypes = [
        ctypes.POINTER(_DataBlob),
        wintypes.LPCWSTR,
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    protect_data.restype = wintypes.BOOL

    unprotect_data = crypt32.CryptUnprotectData
    unprotect_data.argtypes = [
        ctypes.POINTER(_DataBlob),
        ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    unprotect_data.restype = wintypes.BOOL
    local_free = kernel32.LocalFree
    local_free.argtypes = [ctypes.c_void_p]
    local_free.restype = ctypes.c_void_p

    function = protect_data if protect else unprotect_data
    try:
        if protect:
            succeeded = function(
                ctypes.byref(input_blob),
                "Stegano saved passwords",
                None,
                None,
                None,
                _CRYPTPROTECT_UI_FORBIDDEN,
                ctypes.byref(output_blob),
            )
        else:
            succeeded = function(
                ctypes.byref(input_blob),
                None,
                None,
                None,
                None,
                _CRYPTPROTECT_UI_FORBIDDEN,
                ctypes.byref(output_blob),
            )

        if not succeeded:
            error_code = ctypes.get_last_error()
            error = ctypes.WinError(error_code)
            raise SavedPasswordStorageError(
                "Windows DPAPI could not %s saved passwords: %s"
                % ("protect" if protect else "unprotect", error.strerror)
            ) from error

        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        if output_blob.pbData:
            local_free(ctypes.cast(output_blob.pbData, ctypes.c_void_p))


def _validate_passwords(passwords):
    if not isinstance(passwords, list) or len(passwords) > MAX_SAVED_PASSWORDS:
        raise SavedPasswordStorageError("The saved-password list has an invalid format.")
    if any(not isinstance(password, str) for password in passwords):
        raise SavedPasswordStorageError("The saved-password list has an invalid format.")
    return passwords


def protect_passwords(passwords):
    serialized = json.dumps(
        _validate_passwords(passwords),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return _dpapi_transform(serialized, protect=True)


def unprotect_passwords(encrypted_data):
    try:
        serialized = _dpapi_transform(encrypted_data, protect=False)
        passwords = json.loads(serialized.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SavedPasswordStorageError(
            "The protected saved-password list is damaged or unreadable."
        ) from exc
    return _validate_passwords(passwords)


class SavedPasswordStore:
    def __init__(self, settings, legacy_key, legacy_decrypt):
        self.settings = settings
        self.legacy_key = legacy_key
        self.legacy_decrypt = legacy_decrypt
        self.last_warning = None

    def _sync(self, action):
        self.settings.sync()
        if self.settings.status() != QSettings.NoError:
            raise SavedPasswordStorageError(
                "Could not %s saved passwords in the Windows settings store."
                % action
            )

    def _remove_legacy_entry(self):
        if not self.settings.contains(_LEGACY_KEY):
            return
        self.settings.remove(_LEGACY_KEY)
        self._sync("remove the old saved-password copy")

    def load(self):
        self.last_warning = None
        if self.settings.contains(_PROTECTED_KEY):
            encoded = self.settings.value(_PROTECTED_KEY, "", type=str)
            try:
                passwords = unprotect_passwords(bytes.fromhex(encoded))
            except (TypeError, ValueError) as exc:
                raise SavedPasswordStorageError(
                    "The protected saved-password list has an invalid encoding."
                ) from exc
            try:
                self._remove_legacy_entry()
            except SavedPasswordStorageError as exc:
                self.last_warning = str(exc)
            return passwords

        if not self.settings.contains(_LEGACY_KEY):
            return []

        stored = self.settings.value(_LEGACY_KEY, [], type=list)
        if not isinstance(stored, list):
            raise SavedPasswordStorageError(
                "The old saved-password list has an invalid format; it was left unchanged."
            )

        passwords = []
        for index, item in enumerate(stored, start=1):
            try:
                if not isinstance(item, str):
                    raise ValueError("entry is not text")
                encrypted = bytes.fromhex(item)
                decrypted = self.legacy_decrypt(encrypted, self.legacy_key)
                if decrypted is None:
                    raise ValueError("entry could not be decrypted")
                passwords.append(decrypted.decode("utf-8"))
            except (TypeError, ValueError, UnicodeDecodeError) as exc:
                raise SavedPasswordStorageError(
                    "Saved-password entry %d could not be migrated; the old list was left unchanged."
                    % index
                ) from exc

        try:
            self.save(passwords)
        except SavedPasswordStorageError as exc:
            self.last_warning = str(exc)
        return passwords

    def save(self, passwords):
        self.last_warning = None
        try:
            encrypted = protect_passwords(passwords).hex()
        except SavedPasswordStorageError:
            raise
        except (TypeError, ValueError) as exc:
            raise SavedPasswordStorageError(
                "Could not encode the saved-password list."
            ) from exc

        self.settings.setValue(_PROTECTED_KEY, encrypted)
        self._sync("save")
        self._remove_legacy_entry()
