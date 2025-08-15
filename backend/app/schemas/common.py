from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar, List

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """API統一レスポンス形式"""
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[dict] = None

class MessageResponse(BaseModel):
    """シンプルなメッセージ応答"""
    message: str

class PaginationParams(BaseModel):
    """ページネーションパラメータ"""
    page: int = Field(1, ge=1, description="ページ番号")
    limit: int = Field(20, ge=1, le=100, description="1ページあたりの件数")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit

class PaginatedResponse(BaseModel, Generic[T]):
    """ページネーション付きレスポンス"""
    items: List[T]
    total: int
    page: int
    limit: int
    has_more: bool
