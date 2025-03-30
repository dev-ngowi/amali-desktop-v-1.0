# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('Application/Components', 'Application/Components'), ('Helper', 'Helper'), ('Layouts', 'Layouts'), ('Resources', 'Resources'), ('Data', 'Data'), ('Database', 'Database')]
datas += collect_data_files('escpos')


a = Analysis(
    ['amali.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['PyQt5.QtWidgets', 'PyQt5.QtGui', 'PyQt5.QtCore', 'bcrypt', 'escpos'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='amali',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
