from dataclasses import dataclass
from modules.base import BaseModule


@dataclass
class TitleModule(BaseModule):
    title: str = "今日总结"
    subtitle: str = "2025-06-01"
    align: str = "left"  # left|center
    name: str = "标题"

