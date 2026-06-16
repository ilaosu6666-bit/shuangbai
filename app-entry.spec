# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for packaging 智影溯源 as a single-file Windows EXE."""
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

# ── Collect PyTorch resources (large C extensions, DLLs) ──
torch_datas, torch_binaries, torch_hiddenimports = collect_all('torch')
tv_datas, tv_binaries, tv_hiddenimports = collect_all('torchvision')

# ── Determine icon path ──
icon_path = None
candidates = ['icon.ico', 'icon.png']
for c in candidates:
    if os.path.exists(c):
        icon_path = c
        break

a = Analysis(
    ['desktop_launcher.py'],
    pathex=[],
    binaries=torch_binaries + tv_binaries,
    datas=[
        # Data directories
        ('cases', 'cases'),
        ('model_parameter', 'model_parameter'),
        ('loss_fig', 'loss_fig'),
        # Python source files (needed at runtime for streamlit bootstrap)
        ('game.py', '.'),
        ('part1.py', '.'),
        ('streamlit_app.py', '.'),
    ] + torch_datas + tv_datas,
    hiddenimports=[
        # Core dependencies
        'torch',
        'torchvision',
        'streamlit',
        'numpy',
        'pandas',
        'PIL',
        'cv2',
        'matplotlib',
        'tqdm',
        # Medical imaging
        'pydicom',
        'pydicom.encoders',
        'pydicom.encoders.gdcm',
        'SimpleITK',
        # ML / data
        'sklearn',
        'scipy',
        # Streamlit internals (may be missed by analysis)
        'streamlit.runtime',
        'streamlit.runtime.scriptrunner',
        'streamlit.web',
        'streamlit.web.bootstrap',
        'streamlit.elements',
        'altair',
    ] + torch_hiddenimports + tv_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude packages not needed at runtime to reduce size
        'IPython',
        'jupyter',
        'notebook',
        'ipykernel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='智影溯源',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # No terminal window (GUI app)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
