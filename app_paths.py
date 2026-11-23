"""
app_paths.py - centralised path handling for Stegano.

Makes the program work identically when running from source and when
running as a PyInstaller one-file executable (where read-only bundled
files live in a temporary extraction folder pointed to by sys._MEIPASS).

Also owns the release-checklist behaviour:
  - the default image folder:  Documents\\Stegano\\Images
  - first-run seeding of that folder with the starter ("virgin") images
  - the crash log used if the packaged app fails to start
"""
import os
import sys
import shutil
import logging
from datetime import datetime

logger = logging.getLogger("Stegano")

# True when running as a PyInstaller bundle, False when running from source.
IS_FROZEN = getattr(sys, "frozen", False)

# Starter ("virgin") images shipped inside the executable.
STARTER_FILES = [
    "Angry Kid.jpg",
    "ManRefusingToWearaMask.png",
    "ManWearingaMask.png",
    "TeeEssBeeInfo.png",
]


def resource_path(relative=""):
    """Absolute path to a bundled read-only resource.

    Running from source  -> the project folder (where this file lives).
    Frozen (one-file)    -> the temporary extraction folder (sys._MEIPASS).
    """
    if IS_FROZEN:
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative) if relative else base


def documents_dir():
    """The user's real Documents folder.

    Uses the operating system's known-folders API when available (this
    follows OneDrive-redirected Documents on Windows) with a plain
    home-directory fallback.
    """
    try:
        from PyQt5.QtCore import QStandardPaths
        docs = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        if docs and os.path.isdir(docs):
            return docs
    except Exception:
        pass
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    return docs if os.path.isdir(docs) else os.path.expanduser("~")


def stegano_home():
    """The writable per-user folder for Stegano files: Documents\\Stegano."""
    return os.path.join(documents_dir(), "Stegano")


def local_app_data_dir():
    """The per-user local application-data folder for Stegano."""
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        base = os.path.join(os.path.expanduser("~"), "AppData", "Local")
    return os.path.join(base, "Stegano")


def images_dir():
    """Default folder for the Select Image dialog: Documents\\Stegano\\Images."""
    return os.path.join(stegano_home(), "Images")


def _starter_source_dir():
    """Where the starter images can be copied from (bundled or, when
    running from source, the repository's virgin-image folder)."""
    bundled = resource_path("starters")
    if os.path.isdir(bundled):
        return bundled
    dev = os.path.join(resource_path(), "Images", "Virgin Images")
    if os.path.isdir(dev):
        return dev
    return None


def ensure_starter_images():
    """First run: create Documents\\Stegano\\Images and copy the starter
    images into it, so the Select Image dialog opens on a useful folder.

    Never overwrites or deletes anything. All failures are logged and
    swallowed - this runs at startup and must never stop the app.
    Returns the folder path on success, otherwise None.
    """
    try:
        target = images_dir()
        if os.path.isdir(target):
            return target  # already seeded (or the user created it)
        os.makedirs(target, exist_ok=True)
        src = _starter_source_dir()
        if not src:
            logger.info("Created empty image folder (no starters bundled): %s", target)
            return target
        copied = 0
        for name in STARTER_FILES:
            s = os.path.join(src, name)
            d = os.path.join(target, name)
            if os.path.exists(s) and not os.path.exists(d):
                shutil.copy2(s, d)
                copied += 1
        logger.info("Seeded %d starter image(s) into %s", copied, target)
        return target
    except Exception as e:
        logger.warning("Starter-image seeding skipped: %s", e)
        return None


def write_crash_log(text):
    """Append a crash report to Documents\\Stegano\\crash.log.

    Used by the packaged app so a startup failure is never completely
    silent - the user has something to send back.
    """
    try:
        log_dir = stegano_home()
        os.makedirs(log_dir, exist_ok=True)
        path = os.path.join(log_dir, "crash.log")
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n--- %s ---\n%s\n" % (datetime.now().isoformat(), text))
        return path
    except Exception:
        return None
