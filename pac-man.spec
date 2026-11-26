# -*- mode: python ; coding: utf-8 -*-
"""Spec de PyInstaller para congelar Pac-Man (subject VII)."""

from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ['scripts/launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('assets', 'assets'),
    ],
    hiddenimports=collect_submodules('mazegenerator'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'mypy', 'flake8'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Pac_Man',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Pac_Man',
)