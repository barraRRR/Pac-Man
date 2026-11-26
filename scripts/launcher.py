"""Launcher used only by the packaged build (PyInstaller)."""

import os
import sys

from src.main import main


if __name__ == "__main__":
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base)
    sys.argv = [sys.argv[0], os.path.join(base, "config.json")]
    sys.exit(main())
