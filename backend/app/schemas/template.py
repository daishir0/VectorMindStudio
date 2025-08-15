from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime
from app.domain.entities.template import TemplateStatus, TemplateVariable

T = TypeVar('T')


class TemplateBase(BaseModel):
    """テンプレート基本スキーマ"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    content: str = Field(..., min_length=1)
    variables: List[TemplateVariable] = []
    requirements: str = Field("", max_length=2000)
    status: TemplateStatus = TemplateStatus.DRAFT


class TemplateCreate(TemplateBase):
    """テンプレート作成スキーマ"""
    pass


class TemplateUpdate(BaseModel):
    """テンプレート更新スキーマ"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = Field(None, min_length=1)
    variables: Optional[List[TemplateVariable]] = None
    requirements: Optional[str] = Field(None, max_length=2000)
    status: Optional[TemplateStatus] = None


class TemplateResponse(BaseModel):
    """テンプレート応答スキーマ"""
    id: str
    name: str
    description: Optional[str]
    content: str
    variables: List[TemplateVariable]
    requirements: str
    status: TemplateStatus
    user_id: str
    usage_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """テンプレート一覧応答スキーマ"""
    id: str
    name: str
    description: Optional[str]
    status: TemplateStatus
    usage_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TemplateUse(BaseModel):
    """テンプレート使用スキーマ"""
    variables: Dict[str, Any] = {}
    
    @validator('variables')
    def validate_variables(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Variables must be a dictionary')
        return v


class TemplateSearch(BaseModel):
    """テンプレート検索スキーマ"""
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(10, ge=1, le=100)
    filters: Optional[Dict[str, Any]] = None
    
    @validator('query')
    def validate_query(cls, v):
        return v.strip()


from app.schemas.common import PaginatedResponse
