import sys
import os
import platform
import ctypes

# Allow running as script: `python app/main.py`
if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.ui.window import AppWindow


def set_windows_dpi_awareness():
    if platform.system() != "Windows":
        return
    try:
        # Try Per-Monitor v1 awareness
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main():
    set_windows_dpi_awareness()
    app = AppWindow()
    app.run()


if __name__ == "__main__":
    main()
