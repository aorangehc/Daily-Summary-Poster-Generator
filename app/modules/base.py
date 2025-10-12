from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class BaseModule:
    name: str = "模块"
    style: Dict[str, Any] = field(default_factory=dict)  # module-level style override

