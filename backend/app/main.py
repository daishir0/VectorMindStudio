from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.infrastructure.database.session import create_tables, get_sync_db
from app.infrastructure.external.chroma_client import chroma_client
from app.infrastructure.files.storage import ensure_storage_dirs
from app.services.demo_account_service import DemoAccountService


# ロガー設定
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper()))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # 起動時処理
    logger.info("Starting VectorMindStudio...")
    
    # データベーステーブル作成
    await create_tables()
    logger.info("Database tables created")

    # ストレージディレクトリ作成
    originals, converted = ensure_storage_dirs()
    logger.info(f"Storage initialized: originals={originals} converted={converted}")
    
    # ChromaDB接続
    try:
        await chroma_client.connect()
        logger.info("ChromaDB connected")
    except Exception as e:
        logger.warning(f"ChromaDB connection failed: {e}")
    
    # セキュアデモアカウント生成（開発環境のみ）
    try:
        gen = get_sync_db()
        db = next(gen)
        username, password = DemoAccountService.create_or_update_demo_account(db)
        if username and password:
            logger.info("Demo account initialized successfully")
        gen.close()
    except Exception as e:
        logger.warning(f"Demo account initialization failed: {e}")
    
    yield
    
    # 終了時処理
    logger.info("Shutting down VectorMindStudio...")
    await chroma_client.disconnect()


def create_application() -> FastAPI:
    """FastAPIアプリケーションファクトリ"""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="VectorMindStudio API - AI-powered knowledge management platform",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan
    )
    
    # ミドルウェア設定
    setup_middleware(app)
    
    # ルーター設定
    setup_routers(app)
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """ミドルウェアの設定"""
    
    # CORS設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )
    
    # セキュリティヘッダー
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    
    # リクエスト処理時間ログ
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"{request.method} {request.url.path} - "
            f"{response.status_code} - {process_time:.4f}s"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response


def setup_routers(app: FastAPI) -> None:
    """ルーターの設定"""
    
    from app.api.v1.router import api_router
    
    # API v1 ルーターをマウント
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # ヘルスチェックエンドポイント
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": settings.VERSION
        }
    
    @app.get("/")
    async def root():
        return {
            "message": "VectorMindStudio API",
            "version": settings.VERSION,
            "docs_url": f"{settings.API_V1_STR}/docs"
        }


# アプリケーションインスタンス作成
app = create_application()
