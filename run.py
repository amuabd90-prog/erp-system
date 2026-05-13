import threading
import time
import webbrowser
import sys
import os
import socket
from waitress import serve
from app import app

# Configuration
APP_NAME = "AmanaERP"
DEFAULT_PORT = 5000
HOST = "127.0.0.1"

def get_appdata_path():
    """Returns the application's data path in AppData\Local."""
    return os.path.join(os.environ.get('LOCALAPPDATA', ''), APP_NAME)

def find_free_port(start_port):
    """Finds an available TCP port."""
    for port in range(start_port, start_port + 20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((HOST, port))
            return port
        except OSError:
            pass  # Port is in use, try next.
    print(f"FATAL: Could not find a free port starting from {start_port}.", file=sys.stderr)
    sys.exit(1)

def get_database_path():
    """Returns the full path to the database file."""
    app_data_dir = get_appdata_path()
    data_dir = os.path.join(app_data_dir, "data")
    return os.path.join(data_dir, "ha_business.db")

def check_first_run():
    """Checks if the database exists to determine if it's a first run."""
    return not os.path.exists(get_database_path())

def ensure_data_directory_exists():
    """Creates the data directory in AppData if it doesn't exist."""
    db_path = get_database_path()
    data_dir = os.path.dirname(db_path)
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
        except OSError as e:
            print(f"FATAL: Could not create data directory at {data_dir}: {e}", file=sys.stderr)
            sys.exit(1)

def open_browser(url):
    """Opens the web browser in a separate thread."""
    def _open():
        time.sleep(1.5)  # Give server time to start
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"ERROR: Failed to open browser: {e}", file=sys.stderr)
            print(f"Please manually open your browser to: {url}")
    threading.Thread(target=_open, daemon=True).start()

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        import multiprocessing
        multiprocessing.freeze_support()

    ensure_data_directory_exists()

    # Set the database URI in the app's configuration
    database_path = get_database_path()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    
    # From now on, SQLAlchemy will use the database in AppData

    port = find_free_port(DEFAULT_PORT)
    base_url = f"http://{HOST}:{port}"

    target_url = f"{base_url}/setup" if check_first_run() else f"{base_url}/login"

    open_browser(target_url)

    print(f"--- Starting Amana ERP ---")
    print(f"Server running on {base_url}")
    print(f"Database located at: {database_path}")
    print("Close this window to stop the application.")

    try:
        serve(app, host=HOST, port=port, threads=8)
    except Exception as e:
        print(f"FATAL: Server failed to start: {e}", file=sys.stderr)
        # In a real GUI app, this would be a message box.
        input("Press Enter to exit...")
        sys.exit(1)
