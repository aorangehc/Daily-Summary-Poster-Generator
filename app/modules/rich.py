from dataclasses import dataclass, field
from typing import List, Optional
from modules.base import BaseModule


@dataclass
class RichModule(BaseModule):
    # highly customizable block: optional title, body, list items, image
    title: Optional[str] = None
    body: Optional[str] = None
    items: List[str] = field(default_factory=list)
    image_path: Optional[str] = None
    align: str = "left"  # left|center
    name: str = "自定义模块"

