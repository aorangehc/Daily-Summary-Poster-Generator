from dataclasses import dataclass
from modules.base import BaseModule


@dataclass
class QuoteModule(BaseModule):
    text: str = "日日精进，久久为功。"
    author: str = "——"
    name: str = "金句"

