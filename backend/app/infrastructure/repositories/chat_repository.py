from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List, Tuple
import uuid
from datetime import datetime
import logging

from app.infrastructure.database.models import ChatSessionModel, ChatMessageModel

logger = logging.getLogger(__name__)

class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, user_id: str, title: str) -> ChatSessionModel:
        """新しいチャットセッションを作成"""
        new_session = ChatSessionModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(new_session)
        await self.session.commit()
        await self.session.refresh(new_session)
        return new_session

    async def get_session_by_id(self, session_id: str, user_id: str) -> Optional[ChatSessionModel]:
        """セッションIDでチャットセッションを取得（ユーザー権限チェック付き）"""
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[ChatSessionModel]:
        """ユーザーのチャットセッション一覧を取得"""
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.user_id == user_id
        ).order_by(desc(ChatSessionModel.updated_at)).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_session_title(self, session_id: str, user_id: str, title: str) -> Optional[ChatSessionModel]:
        """チャットセッションのタイトルを更新"""
        session = await self.get_session_by_id(session_id, user_id)
        if session:
            session.title = title
            session.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(session)
        return session

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """チャットセッションを削除"""
        session = await self.get_session_by_id(session_id, user_id)
        if session:
            await self.session.delete(session)
            await self.session.commit()
            return True
        return False

    async def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        sources: Optional[List[str]] = None
    ) -> ChatMessageModel:
        """チャットメッセージを追加"""
        new_message = ChatMessageModel(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            sources=sources or [],
            created_at=datetime.utcnow()
        )
        self.session.add(new_message)
        
        # セッションの最終更新時刻も更新
        stmt = select(ChatSessionModel).where(ChatSessionModel.id == session_id)
        result = await self.session.execute(stmt)
        session = result.scalar_one_or_none()
        if session:
            session.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(new_message)
        return new_message

    async def get_session_messages(self, session_id: str, user_id: str) -> List[ChatMessageModel]:
        """セッションのメッセージ一覧を取得"""
        # まずセッションの権限をチェック
        session = await self.get_session_by_id(session_id, user_id)
        if not session:
            return []
        
        stmt = select(ChatMessageModel).where(
            ChatMessageModel.session_id == session_id
        ).order_by(ChatMessageModel.created_at)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_recent_messages(self, session_id: str, limit: int = 10) -> List[ChatMessageModel]:
        """セッションの最新メッセージを取得（コンテキスト用）"""
        stmt = select(ChatMessageModel).where(
            ChatMessageModel.session_id == session_id
        ).order_by(desc(ChatMessageModel.created_at)).limit(limit)
        
        result = await self.session.execute(stmt)
        messages = result.scalars().all()
        return list(reversed(messages))  # 時系列順に並び替え

    async def get_session_message_count(self, session_id: str) -> int:
        """セッションのメッセージ数を取得"""
        stmt = select(func.count(ChatMessageModel.id)).where(
            ChatMessageModel.session_id == session_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()