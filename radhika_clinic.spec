# PyInstaller spec for Radhika Dental Clinic.
#
# Build (on Windows, inside the project's virtualenv):
#     pyinstaller radhika_clinic.spec
#
# The finished RadhikaClinic.exe is written to dist/RadhikaClinic/.
# Distribute the whole dist/RadhikaClinic folder, or add --onefile below
# for a single .exe (slower to start, easier to hand out).

# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RadhikaClinic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RadhikaClinic',
)
