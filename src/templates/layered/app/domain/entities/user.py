from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class User:
    id: int
    username: str
    password_hash: str
    roles: List[str] = field(default_factory=list)
