from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class UploadStatus(str):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    original_path: str
    converted_path: Optional[str] = None
    status: str = Field(description="pending/completed/failed")
    engine: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UploadListResponse(BaseModel):
    items: List[UploadResponse]

