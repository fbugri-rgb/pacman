# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller recipe for a self-contained Pac-Man executable.

Build it with ``make package``, or directly with::

    pyinstaller --noconfirm pacman.spec

The configuration file is bundled so the packaged game starts with no
argument, and it is copied next to the executable as well so a player can
retune the levels without rebuilding anything.  Written for PyInstaller 6.
"""

import os

ROOT = os.path.abspath(os.getcwd())

analysis = Analysis(
    ["pac-man.py"],
    pathex=[ROOT],
    binaries=[],
    datas=[("config.json", ".")],
    hiddenimports=["mazegenerator"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "unittest",
        "pytest",
        "mypy",
        "flake8",
        "PyInstaller",
    ],
    noarchive=False,
)

archive = PYZ(analysis.pure)

executable = EXE(
    archive,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="pac-man",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
