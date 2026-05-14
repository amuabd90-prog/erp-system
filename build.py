import os
import shutil
import subprocess
import sys

# --- Configuration ---
APP_NAME = "AmanaERP"
ENTRY_SCRIPT = "run.py"
ICON_FILE = "static/icon.ico"

# --- Helper Functions ---
def clean():
    """Remove previous build artifacts."""
    print("--- Cleaning previous build files ---")
    for folder in ['build', 'dist', f"{APP_NAME}.spec"]:
        if os.path.isdir(folder):
            shutil.rmtree(folder, ignore_errors=True)
        elif os.path.isfile(folder):
            try:
                os.remove(folder)
            except OSError as e:
                print(f"Error removing file {folder}: {e}")
    print("✓ Cleaned successfully.")

def build():
    """Run PyInstaller to build the executable."""
    print("--- Starting PyInstaller build process ---")
    
    pyinstaller_command = [
        'pyinstaller',
        '--name', APP_NAME,
        '--noconfirm',
        '--noconsole',
        '--onedir',
        '--add-data', f'templates{os.pathsep}templates',
        '--add-data', f'static{os.pathsep}static',
        '--hidden-import', 'waitress',
        '--hidden-import', 'flask',
        '--hidden-import', 'flask_login',
        '--hidden-import', 'flask_sqlalchemy',
        '--hidden-import', 'sqlalchemy',
    ]

    if os.path.exists(ICON_FILE):
        pyinstaller_command.extend(['--icon', ICON_FILE])
    else:
        print(f"NOTE: Icon file not found at '{ICON_FILE}'. The executable will have a default icon.")

    pyinstaller_command.append(ENTRY_SCRIPT)

    print(f"Running command: {' '.join(pyinstaller_command)}")

    try:
        subprocess.check_call(pyinstaller_command)
        print("\n✓ PyInstaller build completed successfully!")
        print(f"Find the application in the 'dist/{APP_NAME}' folder.")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ ERROR: PyInstaller failed with exit code {e.returncode}.", file=sys.stderr)
        print("Please review the output above for specific errors.", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("\n✗ ERROR: 'pyinstaller' command not found.", file=sys.stderr)
        print("Please ensure PyInstaller is installed in your environment: pip install pyinstaller", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    clean()
    build()