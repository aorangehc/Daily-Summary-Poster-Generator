from dataclasses import dataclass, field
from typing import List, Dict
from modules.base import BaseModule


@dataclass
class StatsModule(BaseModule):
    title: str = "今日数据"
    metrics: List[Dict[str, str]] = field(default_factory=lambda: [{"label": "项", "value": "值"}])
    columns: int = 2
    name: str = "统计"

