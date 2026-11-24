from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from app.auth.models import UserRole
from app.auth.service import auth_service
from app.logging_conf import get_logger

router = APIRouter(prefix="/api", tags=["auth"])
logger = get_logger("auth")


@router.post("/register")
async def register_user(payload: dict):
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    try:
        user = auth_service.register_user(username, password, UserRole.USER.value)
        logger.info("register | username=%s | role=%s", username, user.role)
        return {"message": "User registered successfully", "username": username, "role": user.role}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login")
async def login_user(payload: dict, response: Response):
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    user = auth_service.authenticate_user(username, password)
    if user is None:
        logger.warning("login_failure | username=%s", username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = auth_service.create_access_token(user.username, user.role)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60,
    )
    logger.info("login_success | username=%s | role=%s", username, user.role)
    return {"message": "Login successful", "username": username, "role": user.role, "token": token}
