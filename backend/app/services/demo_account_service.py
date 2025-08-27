"""
デモアカウント管理サービス

セキュア初期化パターンで、毎回異なるランダムパスワードを生成し、
初回ログイン時にパスワード変更を強制するデモアカウントを管理します。
"""
import secrets
import string
import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.infrastructure.database.models import UserModel
from app.core.config import get_settings


logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class DemoAccountService:
    """デモアカウント管理サービス"""
    
    DEMO_USERNAME = "demo"
    DEMO_EMAIL = "demo@vectormindstudio.local"
    DEMO_FULL_NAME = "Demo User"
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """セキュアなランダムパスワード生成"""
        # 大文字、小文字、数字、記号を含む
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # 最低1つずつの文字種を保証
        if not any(c.isupper() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.islower() for c in password):
            password = password[:-2] + secrets.choice(string.ascii_lowercase) + password[-1:]
        if not any(c.isdigit() for c in password):
            password = password[:-3] + secrets.choice(string.digits) + password[-2:]
            
        return password
    
    @staticmethod
    def create_or_update_demo_account(db: Session) -> Tuple[str, str]:
        """
        デモアカウントを作成または更新
        
        Returns:
            Tuple[str, str]: (username, new_password)
        """
        settings = get_settings()
        
        # 開発環境でのみ実行（本番環境では無効化）
        if not settings.DEBUG and hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT == 'production':
            logger.warning("デモアカウント機能は本番環境では無効化されています")
            return None, None
        
        # 新しいランダムパスワード生成
        new_password = DemoAccountService.generate_secure_password()
        hashed_password = pwd_context.hash(new_password)
        
        # 既存のデモアカウントを確認
        demo_user = db.query(UserModel).filter(
            UserModel.username == DemoAccountService.DEMO_USERNAME
        ).first()
        
        if demo_user:
            # 既存アカウントのパスワード更新
            demo_user.hashed_password = hashed_password
            demo_user.is_verified = False  # パスワード変更強制のためfalseに設定
            logger.info(f"デモアカウント '{DemoAccountService.DEMO_USERNAME}' のパスワードを更新しました")
        else:
            # 新規デモアカウント作成
            demo_user = UserModel(
                id=f"demo-{secrets.token_hex(8)}",
                username=DemoAccountService.DEMO_USERNAME,
                email=DemoAccountService.DEMO_EMAIL,
                full_name=DemoAccountService.DEMO_FULL_NAME,
                hashed_password=hashed_password,
                is_active=True,
                is_verified=False,  # パスワード変更強制のためfalseに設定
                roles=["user", "demo"]
            )
            db.add(demo_user)
            logger.info(f"新しいデモアカウント '{DemoAccountService.DEMO_USERNAME}' を作成しました")
        
        db.commit()
        
        # セキュリティ情報をログ出力（起動時のみ）
        logger.info("=" * 60)
        logger.info("🎯 デモアカウント情報")
        logger.info(f"   ユーザー名: {DemoAccountService.DEMO_USERNAME}")
        logger.info(f"   パスワード: {new_password}")
        logger.info(f"   注意: 初回ログイン後にパスワード変更が必要です")
        logger.info("=" * 60)
        
        return DemoAccountService.DEMO_USERNAME, new_password
    
    @staticmethod
    def get_demo_credentials(db: Session) -> Optional[Tuple[str, str]]:
        """
        デモアカウントの認証情報を取得（フロントエンド用）
        注意: パスワードは返さず、存在確認のみ
        """
        demo_user = db.query(UserModel).filter(
            UserModel.username == DemoAccountService.DEMO_USERNAME
        ).first()
        
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
        return (
            DemoAccountService.is_demo_account(user.username) 
            and not user.is_verified
        )