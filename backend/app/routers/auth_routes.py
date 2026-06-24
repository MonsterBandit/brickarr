from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth import (
    SETTING_AUTH_PASSWORD_HASH,
    SETTING_AUTH_USERNAME,
    issue_session_token,
    verify_password,
)
from app.config import settings
from app.db import get_db
from app.models.setting import Setting
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    u_row = db.get(Setting, SETTING_AUTH_USERNAME)
    p_row = db.get(Setting, SETTING_AUTH_PASSWORD_HASH)
    expected_user = u_row.value if u_row else None
    expected_hash = p_row.value if p_row else None
    if not expected_user or not expected_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"error": "Unauthorized",
                                    "message": "Forms login not configured"})
    if body.username != expected_user or not verify_password(body.password, expected_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"error": "Unauthorized", "message": "Invalid credentials"})
    token = issue_session_token(body.username)
    response.set_cookie(
        settings.session_cookie_name,
        token,
        httponly=True,
        samesite="lax",
        max_age=settings.session_max_age_seconds,
        path="/",
    )
    return LoginResponse(status="ok")


@router.post("/logout", response_model=LoginResponse)
def logout(response: Response):
    response.delete_cookie(settings.session_cookie_name, path="/")
    return LoginResponse(status="ok")
