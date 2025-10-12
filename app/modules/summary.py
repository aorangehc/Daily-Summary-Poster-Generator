from dataclasses import dataclass, field
from typing import List
from modules.base import BaseModule


@dataclass
class SummaryModule(BaseModule):
    title: str = "今日摘要"
    items: List[str] = field(default_factory=lambda: ["要点 A", "要点 B"]) 
    bullet: str = "•"
    name: str = "摘要"

