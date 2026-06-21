"""One-click launcher for GestureVision AI (cross-platform).

Run this with your system Python:

    python start.py

It will:
  1. Create a local virtual environment (.venv) if it doesn't exist.
  2. Install/update the dependencies from requirements.txt when needed.
  3. Launch the app (app.py) using the virtual environment's Python.

Works on Windows, Linux and macOS - no .bat / .sh script required.
"""

import hashlib
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
APP = ROOT / "app.py"
# Marker file remembers which requirements were last installed, so we only
# re-install when requirements.txt actually changes.
INSTALL_MARKER = VENV_DIR / ".requirements.hash"


def venv_python() -> Path:
    """Path to the Python executable inside the virtual environment."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def requirements_hash() -> str:
    """A short hash of requirements.txt, used to detect changes."""
    if not REQUIREMENTS.exists():
        return ""
    return hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()


def ensure_venv() -> None:
    """Create the virtual environment if it is missing."""
    if venv_python().exists():
        return
    print("[setup] Creating virtual environment in .venv ...")
    venv.create(VENV_DIR, with_pip=True)
    print("[setup] Virtual environment created.")


def ensure_dependencies() -> None:
    """Install dependencies only if they're missing or requirements changed."""
    current = requirements_hash()
    previous = INSTALL_MARKER.read_text().strip() if INSTALL_MARKER.exists() else ""

    if current and current == previous:
        print("[setup] Dependencies already up to date.")
        return

    print("[setup] Installing dependencies (this may take a minute) ...")
    py = str(venv_python())
    subprocess.run([py, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([py, "-m", "pip", "install", "-r", str(REQUIREMENTS)], check=True)
    INSTALL_MARKER.write_text(current)
    print("[setup] Dependencies installed.")


def launch_app() -> int:
    """Run app.py with the virtual environment's Python."""
    print("[run] Starting GestureVision AI ...\n")
    return subprocess.run([str(venv_python()), str(APP)]).returncode


def main() -> int:
    if not REQUIREMENTS.exists():
        print(f"ERROR: {REQUIREMENTS.name} not found. Run this from the project root.")
        return 1
    if not APP.exists():
        print(f"ERROR: {APP.name} not found. Run this from the project root.")
        return 1

    try:
        ensure_venv()
        ensure_dependencies()
    except subprocess.CalledProcessError as exc:
        print(f"\nERROR during setup: {exc}")
        print("Try deleting the .venv folder and running this script again.")
        return 1

    return launch_app()


if __name__ == "__main__":
    sys.exit(main())
