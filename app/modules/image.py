from dataclasses import dataclass
from modules.base import BaseModule


@dataclass
class ImageModule(BaseModule):
    path: str = ""
    fit: str = "cover"  # cover|contain
    height: int = 200
    name: str = "图片/贴纸"

