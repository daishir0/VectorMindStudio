from pydantic_settings import BaseSettings
from pydantic import validator, Field
from typing import List, Optional
from pathlib import Path
import os


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # 基本設定
    PROJECT_NAME: str = "VectorMindStudio"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API設定
    API_V1_STR: str = "/api/v1"
    
    # データベース設定
    DATABASE_URL: str = "sqlite+aiosqlite:///./vectormind.db"
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///./test_vectormind.db"
    
    # ストレージ設定
    STORAGE_DIR: str = "./storage"  # backend配下相対
    
    # ChromaDB設定
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8011
    CHROMA_COLLECTION_NAME: str = "vectormind_embeddings"
    
    # セキュリティ設定
    SECRET_KEY: str = Field(..., env="SECRET_KEY")  # 環境変数から必須で読み込み
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OpenAI設定 (.envファイルから読み込み)
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # CORS設定
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3010", "http://localhost:3011", "http://localhost:5183"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # レート制限
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # ログ設定
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    @validator('BACKEND_CORS_ORIGINS', pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            if isinstance(v, str):
                import json
                return json.loads(v)
            return v
        raise ValueError(v)
    
    @validator('ALLOWED_HOSTS', pre=True)
    def assemble_allowed_hosts(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            if isinstance(v, str):
                import json
                return json.loads(v)
            return v
        raise ValueError(v)
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        """SECRET_KEYのセキュリティ検証"""
        dangerous_values = [
            "your-super-secret-key-here",
            "your-super-secret-key-change-this-in-production",
            "secret",
            "changeme",
            "default"
        ]
        
        if v.lower() in [val.lower() for val in dangerous_values]:
            raise ValueError(
                f"SECRET_KEYにデフォルト値が設定されています。"
                f"強力なランダムキーを生成して設定してください。"
                f"例: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        if len(v) < 32:
            raise ValueError("SECRET_KEYは最低32文字以上である必要があります")
            
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()


# 設定インスタンス
settings = get_settings()
