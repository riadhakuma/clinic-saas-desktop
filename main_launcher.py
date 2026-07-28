import os
import sys
import multiprocessing
import threading
import time
import socket
import urllib.request
import traceback
import asyncio
import ctypes
import uvicorn
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.backend.paths import get_log_path, get_app_data_dir

def show_windows_msgbox(title, message):
    """Displays a native Windows error dialog box."""
    try:
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(0, str(message), str(title), 0x10) # 0x10 = MB_ICONERROR
    except Exception:
        pass

def log_error(msg):
    """Safely logs errors to writable AppData directory."""
    try:
        log_file = get_log_path()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def find_free_port(default_port=8000):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', default_port)) != 0:
                return default_port
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]
    except Exception as e:
        log_error(f"Error finding port: {e}")
        return default_port

def run_server(port):
    """Runs Uvicorn web server safely in a dedicated asyncio loop with log_config=None."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from app.backend.main import app
        # Setting log_config=None prevents PyInstaller --noconsole dictConfig / DefaultFormatter crashes!
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=port,
            log_level="critical",
            log_config=None,
            loop="asyncio",
            http="h11"
        )
        server = uvicorn.Server(config)
        loop.run_until_complete(server.serve())
    except Exception as e:
        err_msg = f"Server crash error: {e}\n{traceback.format_exc()}"
        log_error(err_msg)

def wait_for_server(port, timeout=15.0):
    """Polls server on 127.0.0.1 and localhost until active. Returns None if server fails."""
    start = time.time()
    urls = [f"http://127.0.0.1:{port}", f"http://localhost:{port}"]
    
    while time.time() - start < timeout:
        for url in urls:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=1) as resp:
                    if resp.status in (200, 404):
                        return url
            except Exception:
                pass
        time.sleep(0.3)
    return None

def get_last_error_log():
    """Reads the last 10 lines from app_error.log."""
    try:
        log_file = get_log_path()
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                return "".join(lines[-10:])
    except Exception:
        pass
    return "Aucune information de log disponible."

def main():
    multiprocessing.freeze_support()

    # Ensure writable AppData directory exists
    get_app_data_dir()

    port = find_free_port(8000)

    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()

    # Wait until Uvicorn server is 100% online
    working_url = wait_for_server(port, timeout=15.0)

    if not working_url:
        last_log = get_last_error_log()
        log_error(f"Server failed to start on port {port} after 15s.")
        show_windows_msgbox(
            "Erreur de Démarrage SaaS Clinique",
            f"Le serveur backend n'a pas pu démarrer.\n\nDétails de l'erreur:\n{last_log}\n\nFichier de log: %LOCALAPPDATA%\\ClinicManager\\app_error.log"
        )
        return

    try:
        import webview
        webview.create_window(
            title="Clinique SaaS - Gestion & WhatsApp",
            url=working_url,
            width=1280,
            height=800,
            background_color='#0f172a',
            resizable=True
        )
        webview.start()
    except Exception as e:
        log_error(f"PyWebView exception: {e}. Opening default browser fallback...")
        webbrowser.open(working_url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    main()
