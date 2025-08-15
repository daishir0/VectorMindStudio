from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class FileUploadResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    status: str
    created_at: datetime

class FileDetailResponse(FileUploadResponse):
    original_path: str
    converted_path: Optional[str]
    error_message: Optional[str]
    updated_at: datetime

class FileListResponse(BaseModel):
    id: str
    filename: str
    status: str
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
