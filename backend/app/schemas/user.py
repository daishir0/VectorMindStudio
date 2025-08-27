from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.domain.entities.user import UserRole


class UserBase(BaseModel):
    """ユーザー基本スキーマ"""
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(BaseModel):
    """ユーザー作成スキーマ"""
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    """ユーザー更新スキーマ"""
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """ユーザー応答スキーマ"""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    roles: List[UserRole] = []
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    requires_password_change: bool = False  # パスワード変更が必要かどうか
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """ログインスキーマ"""
    username: str
    password: str


class PasswordChange(BaseModel):
    """パスワード変更スキーマ"""
    current_password: str
    new_password: str
