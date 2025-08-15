from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid


class UserRole(str, Enum):
    """ユーザーロール"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class User(BaseModel):
    """ユーザーエンティティ"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    full_name: Optional[str] = Field(None, max_length=100)
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    roles: List[UserRole] = [UserRole.USER]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower()
    
    def has_permission(self, permission: str) -> bool:
        """指定された権限を持っているかチェック"""
        # 管理者は全権限を持つ
        if UserRole.ADMIN in self.roles:
            return True
        
        # TODO: 具体的な権限チェックロジックを実装
        return False
    
    def has_role(self, role: UserRole) -> bool:
        """指定されたロールを持っているかチェック"""
        return role in self.roles
    
    def add_role(self, role: UserRole) -> None:
        """ロール追加"""
        if role not in self.roles:
            self.roles.append(role)
            self.updated_at = datetime.utcnow()
    
    def remove_role(self, role: UserRole) -> None:
        """ロール削除"""
        if role in self.roles:
            self.roles.remove(role)
            self.updated_at = datetime.utcnow()
    
    def update_last_login(self) -> None:
        """最終ログイン時間更新"""
        self.last_login = datetime.utcnow()
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }