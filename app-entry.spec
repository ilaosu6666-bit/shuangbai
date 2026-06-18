# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for packaging 智影溯源 as a single-file Windows EXE."""
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files

# ── Collect PyTorch resources (large C extensions, DLLs) ──
torch_datas, torch_binaries, torch_hiddenimports = collect_all('torch')
tv_datas, tv_binaries, tv_hiddenimports = collect_all('torchvision')

# ── Collect Streamlit frontend files (critical: HTML/JS/CSS for the UI) ──
streamlit_datas = collect_data_files('streamlit')

# ── Determine icon path ──
icon_path = None
candidates = ['icon.ico']
for c in candidates:
    if os.path.exists(c):
        icon_path = c
        break

# ── Safely collect metadata ──
_extra_datas = []
for _pkg in ['streamlit', 'altair']:
    try:
        from PyInstaller.utils.hooks import copy_metadata
        _meta = copy_metadata(_pkg)
        _extra_datas.extend(_meta)  # copy_metadata returns list, extend not append
    except Exception:
        pass  # Package metadata not available

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
    ] + _extra_datas + torch_datas + tv_datas + streamlit_datas,
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
        # Webview (desktop_launcher.py runtime import)
        'webview',
        # Medical imaging
        'pydicom',
        'pydicom.encoders',
        'pydicom.encoders.gdcm',
        'SimpleITK',
        # ML / data
        'sklearn',
        'scipy',
        'altair',
        # Streamlit transitive dependencies
        'tornado',
        'blinker',
        'protobuf',
        'pyarrow',
        'click',
        'cachetools',
        'packaging',
        'pympler',
        'watchdog',
        'rich',
        'tenacity',
        'toml',
        'tzlocal',
        'validators',
        'semver',
        'requests',
        'gitpython',
        # Standard library
        'importlib.metadata',
        # Streamlit internals
        'streamlit.runtime.scriptrunner.magic_funcs',
        'streamlit.runtime.scriptrunner.script_runner',
        'streamlit.runtime.state',
        'streamlit.runtime.caching',
        'streamlit.runtime.session_manager',
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
        # Bloat packages
        'pip',
        'setuptools',
        'wheel',
        'pkg_resources',
        'tkinter',
        'pytest',
        '_pytest',
        'lib2to3',
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
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # No terminal window (GUI app)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
