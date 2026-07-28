import os
import sys

def get_app_data_dir() -> str:
    """
    Returns a safe, writable directory for DB files, logs, and user settings.
    Avoids System32 and protected Windows directories.
    """
    # 1. Check if running inside PyInstaller executable
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        # If folder is writable and NOT system32 / windows directory, use exe folder
        if not exe_dir.lower().startswith(r"c:\windows") and os.access(exe_dir, os.W_OK):
            return exe_dir
            
    # 2. Safe fallback: %LOCALAPPDATA%\ClinicManager or user home directory
    local_appdata = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    app_dir = os.path.join(local_appdata, "ClinicManager")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def get_db_path() -> str:
    return os.path.join(get_app_data_dir(), "clinic_data.db")

def get_log_path() -> str:
    return os.path.join(get_app_data_dir(), "app_error.log")
