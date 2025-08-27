"""
デモアカウント管理サービス

簡易デモ用に固定パスワード (demo/demo) でアクセス可能な
デモアカウントを管理します。
"""
import secrets
import string
import logging
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.database.models import UserModel
from app.core.config import get_settings
from app.core.security import get_password_hash


logger = logging.getLogger(__name__)


class DemoAccountService:
    """デモアカウント管理サービス"""
    
    DEMO_USERNAME = "demo"
    DEMO_PASSWORD = "demo"  # 固定パスワード
    DEMO_EMAIL = "demo@vectormindstudio.local"
    DEMO_FULL_NAME = "Demo User"
    
    
    @staticmethod
    async def create_or_update_demo_account(db: AsyncSession) -> Tuple[str, str]:
        """
        デモアカウントを作成または更新
        
        Returns:
            Tuple[str, str]: (username, password)
        """
        settings = get_settings()
        
        # 開発環境でのみ実行（本番環境では無効化）
        if not settings.DEBUG and hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT == 'production':
            logger.warning("デモアカウント機能は本番環境では無効化されています")
            return None, None
        
        # 固定パスワードを使用
        password = DemoAccountService.DEMO_PASSWORD
        hashed_password = get_password_hash(password)
        
        # 既存のデモアカウントを確認
        stmt = select(UserModel).where(UserModel.username == DemoAccountService.DEMO_USERNAME)
        result = await db.execute(stmt)
        demo_user = result.scalar_one_or_none()
        
        if demo_user:
            # 既存アカウントのパスワードとロール更新
            demo_user.hashed_password = hashed_password
            demo_user.is_verified = True  # パスワード変更不要
            demo_user.roles = ["user"]  # ロールを正しく設定
            logger.info(f"デモアカウント '{DemoAccountService.DEMO_USERNAME}' を更新しました")
        else:
            # 新規デモアカウント作成
            demo_user = UserModel(
                id=f"demo-{secrets.token_hex(8)}",
                username=DemoAccountService.DEMO_USERNAME,
                email=DemoAccountService.DEMO_EMAIL,
                full_name=DemoAccountService.DEMO_FULL_NAME,
                hashed_password=hashed_password,
                is_active=True,
                is_verified=True,  # パスワード変更不要
                roles=["user"]
            )
            db.add(demo_user)
            logger.info(f"新しいデモアカウント '{DemoAccountService.DEMO_USERNAME}' を作成しました")
        
        await db.commit()
        
        # デモアカウント情報をログ出力
        logger.info("=" * 50)
        logger.info("🎯 デモアカウント情報")
        logger.info(f"   ユーザー名: {DemoAccountService.DEMO_USERNAME}")
        logger.info(f"   パスワード: {DemoAccountService.DEMO_PASSWORD}")
        logger.info("=" * 50)
        
        return DemoAccountService.DEMO_USERNAME, DemoAccountService.DEMO_PASSWORD
    
    @staticmethod
    async def get_demo_credentials(db: AsyncSession) -> Optional[Tuple[str, str]]:
        """
        デモアカウントの認証情報を取得（フロントエンド用）
        注意: パスワードは返さず、存在確認のみ
        """
        stmt = select(UserModel).where(UserModel.username == DemoAccountService.DEMO_USERNAME)
        result = await db.execute(stmt)
        demo_user = result.scalar_one_or_none()
        
        if demo_user:
            return DemoAccountService.DEMO_USERNAME, DemoAccountService.DEMO_EMAIL
        return None
    
    @staticmethod
    def is_demo_account(username: str) -> bool:
        """デモアカウントかどうかを判定"""
        return username == DemoAccountService.DEMO_USERNAME
    
    @staticmethod
    def requires_password_change(user: UserModel) -> bool:
        """パスワード変更が必要かどうかを判定"""
        # 固定パスワードを使用するため常にFalse
        return False