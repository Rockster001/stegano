# -*- mode: python ; coding: utf-8 -*-
# ---------------------------------------------------------------------------
# PyInstaller recipe for Stegano - builds ONE self-contained Stegano.exe
#
# You normally do not run this by hand: build_exe.bat does it for you.
# Manual build (from the project folder):
#     pyinstaller stegano.spec --noconfirm
# ---------------------------------------------------------------------------

import os

a = Analysis(
    ['Stegano.py'],
    pathex=[],
    binaries=[],
    datas=[
        # sounds the app plays (sfx + the idle music used on Windows)
        (os.path.join('audio', 'sfx'), 'audio/sfx'),
        (os.path.join('audio', 'music', 'Idle.mp3'), 'audio/music'),
        (os.path.join('audio', 'music', 'idle.wav'), 'audio/music'),
        # background artwork
        ('STEGANO.png', '.'),
        # first-run starter images -> bundled under 'starters/'
        (os.path.join('Images', 'Virgin Images', 'Angry Kid.jpg'), 'starters'),
        (os.path.join('Images', 'Virgin Images', 'ManRefusingToWearaMask.png'), 'starters'),
        (os.path.join('Images', 'Virgin Images', 'ManWearingaMask.png'), 'starters'),
        (os.path.join('Images', 'Virgin Images', 'TeeEssBeeInfo.png'), 'starters'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Stegano',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='stegano.ico',
)
