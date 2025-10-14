"""
テスト用の共通フィクスチャ
"""
import pytest
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.models import Base, UserModel


@pytest.fixture(scope="function")
async def db_session():
    """テスト用の非同期セッション"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """テスト用ユーザー"""
    user = UserModel(
        id=str(uuid.uuid4()),
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_here",
        is_active=True,
        is_verified=True,
        roles=["user"]
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
