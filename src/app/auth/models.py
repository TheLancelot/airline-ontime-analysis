from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


@dataclass
class UserRecord:
    username: str
    password_hash: str
    role: str

    def to_dict(self) -> dict:
        return asdict(self)
