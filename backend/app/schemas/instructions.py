from __future__ import annotations

from typing import List, Optional

from app.schemas.base import CamelModel


class InstructionOut(CamelModel):
    id: int
    description: Optional[str] = None
    source_url: Optional[str] = None
    downloaded: bool = False
    local_path: Optional[str] = None
    size_bytes: Optional[int] = None


class InstructionsEnvelope(CamelModel):
    records: List[InstructionOut] = []


class InstructionDownloadRequest(CamelModel):
    instruction_ids: Optional[List[int]] = None
