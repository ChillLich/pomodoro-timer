#!/usr/bin/env python3
"""Launcher for Pomodoro Timer: venv + dependencies + launch."""

import subprocess
import sys
from pathlib import Path

IS_WIN = sys.platform == "win32"
VENV_BIN = "Scripts" if IS_WIN else "bin"
PYTHON_EXE = "pythonw.exe" if IS_WIN else "python"


def get_python():
    return Path(f"venv/{VENV_BIN}/{PYTHON_EXE}")


def run(cmd, capture=True):
    kwargs = {"check": True}
    if capture:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    try:
        return subprocess.run(cmd, **kwargs)
    except subprocess.CalledProcessError as e:
        print(f"Error: {' '.join(cmd)}")
        if capture and hasattr(e, "stderr") and e.stderr:
            print(e.stderr.strip())
        sys.exit(1)


def main():
    # 1. venv
    if not Path("venv").exists():
        print("Creating venv...")
        run([sys.executable, "-m", "venv", "venv"])

    python = get_python()

    # 2. requirements.txt
    if not Path("requirements.txt").exists():
        Path("requirements.txt").write_text("pygame==2.5.2\nkeyboard==0.13.5\n", encoding="utf-8")
        print("Created requirements.txt")

    # 3. Dependencies
    print("Installing dependencies...")
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", "--only-binary=:all:", "-r", "requirements.txt"])

    # 4. Launch (detach from console)
    print("Launching Pomodoro Timer...")
    if IS_WIN:
        subprocess.Popen([str(python), "mygui.py"], creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        subprocess.Popen([str(python), "mygui.py"], start_new_session=True)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped")
