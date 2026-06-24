from __future__ import annotations

from app.schemas.base import CamelModel


class LoginRequest(CamelModel):
    username: str
    password: str


class LoginResponse(CamelModel):
    status: str = "ok"
