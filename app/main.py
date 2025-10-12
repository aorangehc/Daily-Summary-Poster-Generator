import sys
import os
import platform
import ctypes

from ui.window import AppWindow


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

