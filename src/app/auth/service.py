from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher

from app.auth.models import UserRecord, UserRole
from app.auth.storage import UserStore
from app.config import settings


class AuthService:
    def __init__(self, store: UserStore | None = None) -> None:
        self.store = store or UserStore()
        self.password_hasher = PasswordHasher()

    @staticmethod
    def _validate_username(username: str) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_]{3,24}", username):
            raise ValueError("Username must be 3-24 characters and use letters, numbers, or underscores only.")

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(ch.isupper() for ch in password):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(ch.islower() for ch in password):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not any(ch.isdigit() for ch in password):
            raise ValueError("Password must contain at least one number.")

    def _hash_password(self, password: str) -> str:
        return self.password_hasher.hash(password)

    def _verify_password(self, password: str, password_hash: str) -> bool:
        try:
            self.password_hasher.verify(password_hash, password)
            return True
        except Exception:
            return False

    def register_user(self, username: str, password: str, role: str = UserRole.USER.value) -> UserRecord:
        username = username.strip()
        self._validate_username(username)
        self._validate_password(password)
        if self.store.get_user(username) is not None:
            raise ValueError("Username already exists.")
        password_hash = self._hash_password(password)
        return self.store.create_user(username, password_hash, role)

    def authenticate_user(self, username: str, password: str) -> UserRecord | None:
        user = self.store.get_user(username)
        if user is None:
            return None
        if self._verify_password(password, user.password_hash):
            return user
        return None

    @staticmethod
    def create_access_token(username: str, role: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": username,
            "role": role,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def decode_access_token(token: str) -> dict:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


user_store = UserStore()
auth_service = AuthService(user_store)
