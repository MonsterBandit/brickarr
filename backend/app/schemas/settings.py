from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from app.schemas.base import CamelModel


class SettingOut(CamelModel):
    key: str
    value: Optional[str] = None
    is_secret: bool = False


class SettingWrite(CamelModel):
    value: Optional[str] = None
    is_secret: bool = False


class ApiKeyOut(CamelModel):
    id: int
    name: str
    key_prefix: str
    last_used_at: Optional[datetime] = None
    created_at: datetime


class ApiKeyCreate(CamelModel):
    name: str


class ApiKeyCreated(CamelModel):
    id: int
    name: str
    key: str
    key_prefix: str


class ApiKeyList(CamelModel):
    records: List[ApiKeyOut] = []
