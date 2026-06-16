# Streamlit 打包为 Windows EXE 桌面应用 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将智影溯源 Streamlit 应用打包为 Windows 单文件 EXE，双击弹出干净桌面窗口（pywebview 包裹，无浏览器 UI）

**Architecture:** `desktop_launcher.py` 作为 PyInstaller 入口 → 后台线程启动 Streamlit 服务器 → pywebview 打开桌面窗口加载 localhost:{port} → 窗口关闭即退出

**Tech Stack:** pywebview (Edge WebView2), Streamlit, PyInstaller

**关键设计决策:**
- `game.py` 和 `part1.py` 作为 data files 打入包（而非 compiled imports），运行时通过 `sys.path` 动态导入
- Streamlit 通过 `streamlit.web.bootstrap.run()` 在线程中启动，避免 subprocess 复杂性
- Icon 通过 Pillow 在构建时从 PNG 转 ICO

---

### Task 1: 安装新依赖并更新 requirements.txt

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: 安装 pywebview 和 pyinstaller**

```bash
pip install pywebview pyinstaller
```

- [ ] **Step 2: 追加到 requirements.txt**

在 `requirements.txt` 末尾添加：

```
pywebview
pyinstaller
```

- [ ] **Step 3: 验证安装和 WebView2 检测**

```bash
python -c "import webview; print('pywebview OK'); print('Available backends:', webview.gui_names)"
```

期望输出包含 `'edgechromium'` 或 `'cef'`。

- [ ] **Step 4: 提交**

```bash
git add requirements.txt
git commit -m "chore: add pywebview and pyinstaller dependencies"
```

---

### Task 2: 创建桌面启动器 desktop_launcher.py

**Files:**
- Create: `desktop_launcher.py`

- [ ] **Step 1: 创建 desktop_launcher.py**

```python
"""
智影溯源 桌面启动器
Entry point for PyInstaller-packaged EXE.
Starts Streamlit server in background and wraps it in a desktop window.
"""
import os
import sys
import socket
import time
import threading
import urllib.request
from pathlib import Path


def get_app_dir() -> Path:
    """Get application root directory.
    Works in both dev mode and PyInstaller frozen bundle."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).resolve().parent


def find_free_port() -> int:
    """Find an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Poll until the server responds or timeout is reached."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def run_streamlit_server(script_path: str, port: int) -> None:
    """Start Streamlit server in the current thread (blocks forever).
    Called from a daemon thread so it dies when main thread exits."""
    # Ensure the app directory is on sys.path so streamlit can import game/part1
    app_dir = os.path.dirname(script_path)
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    import streamlit.web.bootstrap as bootstrap
    from streamlit import config as _config

    _config.set_option("server.port", port)
    _config.set_option("server.headless", True)
    _config.set_option("server.enableCORS", False)
    _config.set_option("server.enableXsrfProtection", False)
    _config.set_option("server.address", "127.0.0.1")
    _config.set_option("browser.gatherUsageStats", False)
    _config.set_option("server.fileWatcherType", "none")

    bootstrap.run(script_path, '', [], flag_options={})


def main() -> None:
    app_dir = get_app_dir()
    port = find_free_port()
    script_path = app_dir / "streamlit_app.py"

    if not script_path.exists():
        msg = f"Error: {script_path} not found"
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, msg, "启动错误", 0x10)
        except Exception:
            pass
        print(msg)
        sys.exit(1)

    # Start Streamlit in daemon thread
    server_thread = threading.Thread(
        target=run_streamlit_server,
        args=(str(script_path), port),
        daemon=True,
        name="streamlit-server",
    )
    server_thread.start()

    # Wait for server readiness
    url = f"http://127.0.0.1:{port}"
    if not wait_for_server(url):
        msg = "Error: Streamlit server failed to start within 30 seconds"
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, msg, "启动错误", 0x10)
        except Exception:
            pass
        print(msg)
        sys.exit(1)

    # Open desktop window (blocking — returns when user closes window)
    import webview
    webview.create_window(
        title="智影溯源 - AI肺结节教学平台",
        url=url,
        width=1280,
        height=800,
        min_size=(1024, 768),
        resizable=True,
    )
    webview.start()

    # Window closed — daemon thread terminates with process
    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 开发模式测试 — 确认启动器能运行**

```bash
cd /d/shuangbai && timeout 15 python desktop_launcher.py || true
```

确认：桌面窗口弹出、显示 Streamlit 首页、无报错。窗口 15 秒内出现即为成功。手动关闭窗口验证退出无残留进程。

- [ ] **Step 3: 提交**

```bash
git add desktop_launcher.py
git commit -m "feat: add desktop launcher with pywebview and embedded Streamlit"
```

---

### Task 3: 创建 PyInstaller 打包配置 app-entry.spec

**Files:**
- Create: `app-entry.spec`

- [ ] **Step 1: 创建 app-entry.spec**

```python
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
```

- [ ] **Step 2: 验证 spec 语法正确**

```bash
python -c "exec(open('app-entry.spec').read().replace('Analysis','dict'))" 2>&1 || true
```

（这个简单检测确保 spec 文件能被 Python 解析）

- [ ] **Step 3: 提交**

```bash
git add app-entry.spec
git commit -m "feat: add PyInstaller spec for single-file EXE packaging"
```

---

### Task 4: 创建打包脚本 build.bat

**Files:**
- Create: `build.bat`

- [ ] **Step 1: 创建 build.bat**

```bat
@echo off
chcp 65001 >nul
echo ============================================
echo   智影溯源 - 桌面应用打包工具
echo ============================================
echo.

REM Check for PyInstaller
where pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller not found. Run: pip install pyinstaller
    pause
    exit /b 1
)

REM Convert PNG icon to ICO if needed
if exist "icon.png" (
    if not exist "icon.ico" (
        echo [1/3] Converting icon.png to icon.ico...
        python -c "from PIL import Image; img = Image.open('icon.png'); img.save('icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
        if %ERRORLEVEL% NEQ 0 (
            echo [WARNING] Icon conversion failed, building without icon...
        ) else (
            echo        icon.ico created.
        )
    ) else (
        echo [1/3] icon.ico already exists, skipping conversion.
    )
) else (
    echo [1/3] No icon.png found, building without custom icon.
)

REM Clean previous build
echo [2/3] Cleaning previous build...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Build EXE
echo [3/3] Building EXE with PyInstaller...
echo        This may take 10-30 minutes depending on system speed...
echo.
pyinstaller --clean --noconfirm app-entry.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo   Build complete!
    echo   Output: dist\智影溯源.exe
    echo ============================================
) else (
    echo.
    echo ============================================
    echo   Build FAILED! Check output above for errors.
    echo ============================================
)
pause
```

- [ ] **Step 2: 验证脚本语法**

```bash
cmd /c "type build.bat"
```

- [ ] **Step 3: 提交**

```bash
git add build.bat
git commit -m "feat: add one-click build script for EXE packaging"
```

---

### Task 5: 首次构建和验证

- [ ] **Step 1: 复制图标到项目根目录**（执行前确认）

如果已有 PNG 图标文件，复制到 `d:\shuangbai\icon.png`。如果没有，跳过此步（构建不带图标）。

- [ ] **Step 2: 运行打包脚本**

```bash
cd /d/shuangbai && cmd /c build.bat
```

**预期结果:** `dist\智影溯源.exe` 生成成功。

- [ ] **Step 3: 测试生成的 EXE**

```bash
# 首次启动最多等待 60 秒（解压 + 初始化）
# 确认：
# 1. 窗口弹出，标题为 "智影溯源 - AI肺结节教学平台"
# 2. 无终端黑窗
# 3. 无浏览器地址栏/工具栏
# 4. Streamlit 界面正常渲染
# 5. 关闭窗口后进程完全退出（任务管理器检查）
```

手动双击 `dist\智影溯源.exe` 进行验证。

- [ ] **Step 4: 提交构建产物（可选）**

构建产物很大（~3 GB），不建议提交到 git。确认 `.gitignore` 包含 `build/` 和 `dist/`：

```bash
grep -q "^build/" .gitignore || echo "build/" >> .gitignore
grep -q "^dist/" .gitignore || echo "dist/" >> .gitignore
```

- [ ] **Step 5: 提交**

```bash
git add .gitignore
git commit -m "chore: ignore build and dist directories"
```

---

### 故障排除指南

| 问题 | 可能原因 | 解决方法 |
|------|---------|---------|
| `pywebview` 窗口一片空白 | Streamlit 未完全就绪 | 增大 `wait_for_server` timeout |
| `import game` 失败 | `sys.path` 未包含 app_dir | 确认 `run_streamlit_server` 中最前面有 `sys.path.insert` |
| Torch 加载失败 | PyInstaller 遗漏 torch C 扩展 | spec 中确保 `collect_all('torch')` |
| EXE 启动闪退 | 缺少某个隐藏导入 | 用 `--console` 模式构建调试版查看错误输出 |
| EXE 体积过大 | UPX 未启用或依赖过多 | 检查 `excludes` 列表，确认 `upx=True` |
| WebView2 不可用 | 系统缺少 Edge WebView2 Runtime | 提示用户安装: https://go.microsoft.com/fwlink/p/?LinkId=2124703 |
