from __future__ import annotations

from fastapi import Depends, HTTPException, Request

from app.auth.models import UserRole
from app.auth.service import auth_service


def get_token_from_request(request: Request) -> str:
    token = request.cookies.get("access_token")
    if token:
        return token

    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()

    raise HTTPException(status_code=401, detail="Authentication required")


def get_current_user(request: Request) -> dict:
    token = get_token_from_request(request)
    try:
        payload = auth_service.decode_access_token(token)
    except Exception as exc:  # pragma: no cover - security guard
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    username = payload.get("sub")
    role = payload.get("role")
    if not username or not role:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return {"username": username, "role": role}


def require_role(*allowed_roles: str):
    def dependency(request: Request) -> dict:
        user = get_current_user(request)
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Role not allowed")
        return user

    return Depends(dependency)


def require_admin_user(request: Request) -> dict:
    user = get_current_user(request)
    if user["role"] != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin rights required")
    return user
