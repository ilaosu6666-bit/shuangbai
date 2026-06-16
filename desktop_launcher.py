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
