from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.infrastructure.database.session import get_session
from app.infrastructure.database.models import UserModel
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    PasswordChange
)
from app.schemas.common import ApiResponse, MessageResponse
from app.domain.entities.user import User, UserRole
from app.api.deps.auth import get_current_active_user
from app.services.demo_account_service import DemoAccountService

import uuid
from datetime import datetime

router = APIRouter()

@router.post("/register", response_model=ApiResponse[UserResponse])
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    """新規ユーザー登録"""
    
    # ユーザー名とメールアドレスの重複チェック
    stmt = select(UserModel).where(
        (UserModel.username == user_data.username) | 
        (UserModel.email == user_data.email)
    )
    result = await session.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # パスワードハッシュ化
    hashed_password = get_password_hash(user_data.password)
    
    # ユーザー作成
    new_user = UserModel(
        id=str(uuid.uuid4()),
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=False,  # メール認証が必要
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    # レスポンス用のユーザー情報
    user_response = UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        roles=[],
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
        last_login=new_user.last_login
    )
    
    return ApiResponse(
        success=True,
        data=user_response,
        message="User registered successfully"
    )

@router.post("/login", response_model=ApiResponse[dict])
async def login(
    user_credentials: UserLogin,
    session: AsyncSession = Depends(get_session)
):
    """ユーザーログイン"""
    
    # ユーザー名またはメールアドレスでユーザーを検索
    stmt = select(UserModel).where(
        (UserModel.username == user_credentials.username) | 
        (UserModel.email == user_credentials.username)
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # ログイン時刻を更新
    user.last_login = datetime.utcnow()
    await session.commit()
    
    # アクセストークンとリフレッシュトークンを生成
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id}, expires_delta=refresh_token_expires
    )
    
    token_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
    
    return ApiResponse(
        success=True,
        data=token_data,
        message="Login successful"
    )

@router.get("/demo-credentials", response_model=ApiResponse[dict])
async def get_demo_credentials():
    """デモアカウントの認証情報を取得（フロントエンド用）"""
    # デモアカウントが有効かどうかをチェック（簡易版）
    if DemoAccountService.DEMO_USERNAME:
        return ApiResponse(
            success=True,
            data={
                "username": DemoAccountService.DEMO_USERNAME,
                "email": DemoAccountService.DEMO_EMAIL,
                "message": "デモアカウントを使用して、システムの機能をお試しいただけます"
            },
            message="Demo credentials available"
        )
    else:
        return ApiResponse(
            success=False,
            data={},
            message="Demo account not available"
        )

@router.post("/refresh", response_model=ApiResponse[dict])
async def refresh_token(
    refresh_data: dict,
    session: AsyncSession = Depends(get_session)
):
    """リフレッシュトークンを使用してアクセストークンを更新"""
    
    refresh_token = refresh_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required"
        )
    
    try:
        payload = verify_token(refresh_token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # ユーザーの存在確認
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # 新しいアクセストークンを生成
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        token_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
        return ApiResponse(
            success=True,
            data=token_data,
            message="Token refreshed successfully"
        )
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """現在のユーザー情報を取得"""
    
    user_response = UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        roles=current_user.roles,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login,
        requires_password_change=DemoAccountService.requires_password_change(
            type('MockUser', (), {
                'username': current_user.username,
                'is_verified': current_user.is_verified
            })()
        )
    )
    
    return ApiResponse(
        success=True,
        data=user_response
    )

@router.patch("/me", response_model=ApiResponse[UserResponse])
async def update_current_user(
    user_update: dict,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """現在のユーザー情報を更新"""
    
    # データベースからユーザーを取得
    stmt = select(UserModel).where(UserModel.id == current_user.id)
    result = await session.execute(stmt)
    user_model = result.scalar_one_or_none()
    
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 更新可能なフィールドのみ更新
    allowed_fields = {"username", "email", "full_name"}
    for field, value in user_update.items():
        if field in allowed_fields and value is not None:
            setattr(user_model, field, value)
    
    user_model.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(user_model)
    
    # レスポンス作成
    user_response = UserResponse(
        id=user_model.id,
        username=user_model.username,
        email=user_model.email,
        full_name=user_model.full_name,
        is_active=user_model.is_active,
        is_verified=user_model.is_verified,
        roles=[UserRole(role) for role in user_model.roles] if user_model.roles else [UserRole.USER],
        created_at=user_model.created_at,
        updated_at=user_model.updated_at,
        last_login=user_model.last_login
    )
    
    return ApiResponse(
        success=True,
        data=user_response,
        message="User updated successfully"
    )

@router.post("/change-password", response_model=ApiResponse[MessageResponse])
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """パスワード変更"""
    
    # データベースからユーザーを取得
    stmt = select(UserModel).where(UserModel.id == current_user.id)
    result = await session.execute(stmt)
    user_model = result.scalar_one_or_none()
    
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 現在のパスワードを確認
    if not verify_password(password_data.current_password, user_model.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # 新しいパスワードをハッシュ化して保存
    user_model.hashed_password = get_password_hash(password_data.new_password)
    user_model.updated_at = datetime.utcnow()
    
    # デモアカウントの場合はverified状態に変更
    if DemoAccountService.is_demo_account(user_model.username):
        user_model.is_verified = True
    
    await session.commit()
    
    return ApiResponse(
        success=True,
        data=MessageResponse(message="Password changed successfully"),
        message="Password changed successfully"
    )

@router.post("/logout", response_model=ApiResponse[MessageResponse])
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """ログアウト（トークンの無効化）"""
    
    # TODO: トークンブラックリストの実装
    # 現在は単純にSuccessレスポンスを返す
    
    return ApiResponse(
        success=True,
        data=MessageResponse(message="Logged out successfully"),
        message="Logged out successfully"
    )