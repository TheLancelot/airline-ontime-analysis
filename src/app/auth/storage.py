from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from app.auth.models import UserRecord
from app.config import settings


class UserStore:
    def __init__(self, file_path: Path | None = None) -> None:
        self.file_path = file_path or settings.USER_STORE_PATH
        self._lock = threading.RLock()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_exists()

    def _ensure_exists(self) -> None:
        if not self.file_path.exists():
            self._write_all({"users": []})

    def _read_all(self) -> dict[str, Any]:
        try:
            with self.file_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"users": []}
        return data if isinstance(data, dict) else {"users": []}

    def _write_all(self, payload: dict[str, Any]) -> None:
        tmp_path = self.file_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        tmp_path.replace(self.file_path)

    def list_users(self) -> list[UserRecord]:
        with self._lock:
            data = self._read_all()
            users = []
            for item in data.get("users", []):
                users.append(UserRecord(**item))
            return users

    def get_user(self, username: str) -> UserRecord | None:
        with self._lock:
            for user in self.list_users():
                if user.username == username:
                    return user
            return None

    def create_user(self, username: str, password_hash: str, role: str) -> UserRecord:
        with self._lock:
            users = self.list_users()
            existing = self.get_user(username)
            if existing is not None:
                raise ValueError("User already exists")
            record = UserRecord(username=username, password_hash=password_hash, role=role)
            users.append(record)
            self._write_all({"users": [user.to_dict() for user in users]})
            return record

    def update_user(self, username: str, **kwargs: Any) -> UserRecord:
        with self._lock:
            users = self.list_users()
            for user in users:
                if user.username == username:
                    for key, value in kwargs.items():
                        setattr(user, key, value)
                    self._write_all({"users": [u.to_dict() for u in users]})
                    return user
            raise KeyError(f"User not found: {username}")
