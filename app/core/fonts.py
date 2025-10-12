import os
import platform
from typing import Optional

from PIL import ImageFont


def _asset_font_path(filename: str) -> Optional[str]:
    # Resolve asset path (works under PyInstaller via _MEIPASS)
    import sys

    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base, "assets", "fonts", filename)
    return path if os.path.exists(path) else None


def _find_windows_font() -> Optional[str]:
    # Try common Chinese-capable fonts on Windows
    win_dir = os.environ.get("WINDIR", r"C:\\Windows")
    fonts_dir = os.path.join(win_dir, "Fonts")
    candidates = [
        "msyh.ttc",  # Microsoft YaHei
        "msyhbd.ttc",
        "msjh.ttc",  # Microsoft JhengHei
        "simhei.ttf",
        "simfang.ttf",
        "simkai.ttf",
        "simhei.ttf",
        "msmincho.ttc",
        "arialuni.ttf",
    ]
    for name in candidates:
        path = os.path.join(fonts_dir, name)
        if os.path.exists(path):
            return path
    return None


def _find_macos_font() -> Optional[str]:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _find_linux_font() -> Optional[str]:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def get_font(size: int, bold: bool = False):
    # Priority: asset font -> system font -> default
    asset = _asset_font_path("NotoSansSC-Regular.otf")
    if bold:
        asset_bold = _asset_font_path("NotoSansSC-Bold.otf")
        if asset_bold:
            try:
                return ImageFont.truetype(asset_bold, size=size)
            except Exception:
                pass
    if asset:
        try:
            return ImageFont.truetype(asset, size=size)
        except Exception:
            pass

    system = None
    sysname = platform.system()
    if sysname == "Windows":
        system = _find_windows_font()
    elif sysname == "Darwin":
        system = _find_macos_font()
    else:
        system = _find_linux_font()

    if system:
        try:
            return ImageFont.truetype(system, size=size)
        except Exception:
            pass

    # ultimate fallback
    return ImageFont.load_default()

