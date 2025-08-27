from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.core.config import settings

# 非同期エンジン作成
if "sqlite" in settings.DATABASE_URL:
    # SQLite用の設定
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
    )
else:
    # その他のデータベース用設定
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )

# セッションメーカー
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 同期データベースエンジンとセッション（デモアカウント用）
sync_database_url = settings.DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://")
sync_engine = create_engine(
    sync_database_url,
    echo=settings.DEBUG,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False} if "sqlite" in sync_database_url else {}
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """データベースセッション取得"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# 下位互換のためのエイリアス
get_db = get_session


def get_sync_db() -> Session:
    """同期データベースセッション取得（デモアカウント初期化用）"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def create_tables():
    """テーブル作成"""
    from app.infrastructure.database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """テーブル削除"""
    from app.infrastructure.database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)