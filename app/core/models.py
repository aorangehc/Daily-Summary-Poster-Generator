from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class Gradient:
    # simple linear gradient definition
    type: str = "linear"  # only linear supported now
    start: str = "#000000"
    end: str = "#FFFFFF"
    angle: int = 90  # 0..360


@dataclass
class Style:
    # module-level style override; any field can be None to inherit theme
    bg_color: Optional[str] = None
    bg_gradient: Optional[Gradient] = None
    text_color: Optional[str] = None
    accent_color: Optional[str] = None
    radius: Optional[int] = None
    padding: Optional[int] = None


@dataclass
class CanvasConfig:
    width: int = 1240
    height: int = 1754
    dpi: int = 150
    padding: int = 64


@dataclass
class PosterConfig:
    canvas: CanvasConfig = field(default_factory=CanvasConfig)
    theme: str = "black_gold"
    modules: List[Dict[str, Any]] = field(default_factory=list)

