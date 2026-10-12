"""Ponto de entrada da aplicação Desktop CustomTkinter (python app_desktop.py)."""

from __future__ import annotations

import os
from pathlib import Path

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    meipass = Path(sys._MEIPASS)
    for p in meipass.glob("tcl9*"):
        if p.is_dir():
            os.environ["TCL_LIBRARY"] = str(p)
            break
    for p in meipass.glob("tk9*"):
        if p.is_dir():
            os.environ["TK_LIBRARY"] = str(p)
            break

from matraca.gui.desktop_app import main

if __name__ == "__main__":
    sys.exit(main())
