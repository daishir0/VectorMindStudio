from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.security import verify_token
from app.infrastructure.database.session import get_session
from app.domain.entities.user import User, UserRole
from app.infrastructure.database.models import UserModel
from sqlalchemy import select

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> User:
    """現在のユーザーを取得"""
    
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # トークンを検証してユーザーIDを取得
        payload = verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # データベースからユーザー情報を取得
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await session.execute(stmt)
        user_model = result.scalar_one_or_none()
        
        if user_model is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # ユーザーエンティティに変換
        user = User(
            id=user_model.id,
            username=user_model.username,
            email=user_model.email,
            full_name=user_model.full_name,
            hashed_password=user_model.hashed_password,
            is_active=user_model.is_active,
            is_verified=user_model.is_verified,
            roles=[UserRole(role) for role in user_model.roles] if user_model.roles else [UserRole.USER],
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
            last_login=user_model.last_login
        )
        
        return user
        
    except Exception as e:
        print(f"Authentication error: {e}")  # デバッグ用
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """アクティブなユーザーのみを取得"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """認証済みのユーザーのみを取得"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )
    return current_user

def require_role(required_role: UserRole):
    """指定されたロールを持つユーザーのみアクセス可能"""
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if required_role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return role_checker

def require_admin():
    """管理者のみアクセス可能"""
    return require_role(UserRole.ADMIN)

def require_permission(permission: str):
    """指定された権限を持つユーザーのみアクセス可能"""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # TODO: 権限チェックのロジックを実装
        # 現在は管理者のみ全権限を持つと仮定
        if UserRole.ADMIN not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    
    return permission_checker

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> Optional[User]:
    """オプショナルな認証（ログインしていなくてもアクセス可能）"""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None