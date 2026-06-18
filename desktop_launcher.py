"""
智影溯源 桌面启动器
Entry point for PyInstaller-packaged EXE.
Starts Streamlit server as a subprocess and wraps it in a desktop window.
"""
import os
import sys
import socket
import time
import subprocess
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
            with urllib.request.urlopen(url):
                return True
        except Exception:
            time.sleep(0.3)
    return False


def run_as_streamlit_server() -> None:
    """Run Streamlit server in this process (called via subprocess).
    Streamlit needs to run in the main thread for signal handling."""
    port = int(sys.argv[2])
    app_dir = get_app_dir()
    script_path = app_dir / "streamlit_app.py"

    if not script_path.exists():
        print(f"Error: {script_path} not found", flush=True)
        sys.exit(1)

    sys.path.insert(0, str(app_dir))

    import streamlit.web.bootstrap as bootstrap
    from streamlit import config as _config

    _config.set_option("server.port", port)
    _config.set_option("server.headless", True)
    _config.set_option("server.enableCORS", False)
    _config.set_option("server.enableXsrfProtection", False)
    _config.set_option("server.address", "127.0.0.1")
    _config.set_option("browser.gatherUsageStats", False)
    _config.set_option("server.fileWatcherType", "none")
    _config.set_option("global.developmentMode", False)

    bootstrap.run(str(script_path), '', [], flag_options={})


def show_error(msg: str) -> None:
    """Show error message via MessageBox and console."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, "启动错误", 0x10)
    except Exception:
        pass
    print(msg, flush=True)


def main() -> None:
    # If called with --streamlit-server flag, run as streamlit server subprocess
    if len(sys.argv) > 1 and sys.argv[1] == "--streamlit-server":
        run_as_streamlit_server()
        return

    app_dir = get_app_dir()
    port = find_free_port()
    script_path = app_dir / "streamlit_app.py"

    if not script_path.exists():
        show_error(f"Error: {script_path} not found")
        sys.exit(1)

    # Start Streamlit as a subprocess (needs main thread for signals)
    env = os.environ.copy()
    if getattr(sys, 'frozen', False):
        # Packaged EXE: call itself with --streamlit-server flag
        cmd = [sys.executable, "--streamlit-server", str(port)]
    else:
        # Dev mode: run this same script with Python
        cmd = [sys.executable, __file__, "--streamlit-server", str(port)]
    server_proc = subprocess.Popen(cmd, env=env)

    # Wait for server readiness
    health_url = f"http://127.0.0.1:{port}/_stcore/health"
    if not wait_for_server(health_url):
        server_proc.kill()
        show_error("Error: Streamlit server failed to start within 30 seconds")
        sys.exit(1)

    # Open desktop window
    try:
        import webview
        webview.create_window(
            title="智影溯源 - AI肺结节教学平台",
            url=f"http://127.0.0.1:{port}",
            width=1280,
            height=800,
            min_size=(1024, 768),
            resizable=True,
        )
        webview.start()
    finally:
        # Clean up streamlit subprocess when window closes
        server_proc.kill()
        server_proc.wait()
        sys.exit(0)


if __name__ == "__main__":
    main()
