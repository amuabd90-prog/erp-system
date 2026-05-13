import threading
import time
import webbrowser
import sys
import os
from waitress import serve
from app import app


def open_browser():
    """Open browser after server starts"""
    time.sleep(2.0)  # Give server more time to start
    try:
        webbrowser.open("http://127.0.0.1:5000")
        print("✓ Browser opened successfully")
    except Exception as e:
        print(f"✗ Failed to open browser: {e}")


def check_first_run():
    """Check if this is first run (no database exists)"""
    db_path = os.path.join(os.getcwd(), "instance", "ha_business.db")
    return not os.path.exists(db_path)


if __name__ == "__main__":
    print("=" * 50)
    print("Starting Amana ERP...")
    print("=" * 50)
    
    # Check if first run
    if check_first_run():
        print("🔧 First run detected - Setup wizard will be available")
        target_url = "http://127.0.0.1:5000/setup"
    else:
        target_url = "http://127.0.0.1:5000/login"
    
    # Start browser in separate thread
    def delayed_browser_open():
        time.sleep(3.0)  # Give more time for server to start
        try:
            webbrowser.open(target_url)
            print(f"✓ Browser opened to {target_url}")
        except Exception as e:
            print(f"✗ Failed to open browser: {e}")
            print(f"Please manually open: {target_url}")
    
    threading.Thread(target=delayed_browser_open, daemon=True).start()
    
    # Start server
    print("🚀 Starting server on http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        serve(app, host="127.0.0.1", port=5000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        print("Press any key to exit...")
        input()
        sys.exit(1)
