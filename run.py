import threading
import time
import webbrowser
import sys
import os
import socket
import ctypes
from waitress import serve
from app import app
from models import db

APP_NAME = "AmanaERP"
DEFAULT_PORT = 5000
HOST = "127.0.0.1"

def get_appdata_path():
    return os.path.join(os.environ.get('LOCALAPPDATA', ''), APP_NAME)

def find_free_port(start_port):
    for port in range(start_port, start_port + 20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((HOST, port))
            return port
        except OSError:
            pass
    print(f"FATAL: Could not find a free port starting from {start_port}.", file=sys.stderr)
    sys.exit(1)

def get_database_path():
    app_data_dir = get_appdata_path()
    data_dir = os.path.join(app_data_dir, "data")
    return os.path.join(data_dir, "ha_business.db")

def check_first_run():
    return not os.path.exists(get_database_path())

def ensure_data_directory_exists():
    db_path = get_database_path()
    data_dir = os.path.dirname(db_path)
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
            print(f"Created data directory: {data_dir}")
        except OSError as e:
            print(f"FATAL: Could not create data directory at {data_dir}: {e}", file=sys.stderr)
            alt_dir = os.path.join(os.path.expanduser("~"), "AmanaERP", "data")
            try:
                os.makedirs(alt_dir, exist_ok=True)
                print(f"Using alternative data directory: {alt_dir}")
            except:
                sys.exit(1)

def is_already_running():
    mutex_name = "Global\\AmanaERP_SingleInstance"
    try:
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
        if ctypes.windll.kernel32.GetLastError() == 183:
            ctypes.windll.user32.MessageBoxW(0, "Amana ERP is already running.", "Amana ERP", 0x30)
            return True
        return False
    except Exception:
        return False

def open_browser(url):
    def _open():
        time.sleep(1.5)
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"ERROR: Failed to open browser: {e}", file=sys.stderr)
            print(f"Please manually open your browser to: {url}")
    threading.Thread(target=_open, daemon=True).start()

if __name__ == "__main__":
    if is_already_running():
        sys.exit(0)

    if sys.platform.startswith('win'):
        import multiprocessing
        multiprocessing.freeze_support()

    ensure_data_directory_exists()

    database_path = get_database_path()
    print(f"Database path: {database_path}")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'

    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")

    port = find_free_port(DEFAULT_PORT)
    base_url = f"http://{HOST}:{port}"
    target_url = f"{base_url}/" if check_first_run() else f"{base_url}/login"

    open_browser(target_url)

    print(f"--- Starting Amana ERP ---")
    print(f"Server running on {base_url}")
    print(f"Database located at: {database_path}")
    print("Close this window to stop the application.")

    try:
        serve(app, host=HOST, port=port, threads=8)
    except Exception as e:
        print(f"FATAL: Server failed to start: {e}", file=sys.stderr)
        input("Press Enter to exit...")
        sys.exit(1)