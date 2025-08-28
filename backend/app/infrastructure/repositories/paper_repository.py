"""
論文関連のデータベース操作を担当するリポジトリ
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from app.infrastructure.database.models import (
    ResearchPaperModel, PaperSectionModel, PaperSectionHistoryModel,
    PaperChatSessionModel, PaperChatMessageModel, UserModel
)


class PaperRepository:
    """論文関連のリポジトリクラス"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # === 論文関連 ===
    async def create_paper(
        self, 
        user_id: str, 
        title: str, 
        description: Optional[str] = None
    ) -> ResearchPaperModel:
        """新しい論文を作成"""
        paper = ResearchPaperModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            description=description,
            status="draft"
        )
        
        self.session.add(paper)
        await self.session.commit()
        await self.session.refresh(paper)
        return paper
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[ResearchPaperModel]:
        """IDで論文を取得"""
        stmt = select(ResearchPaperModel).where(ResearchPaperModel.id == paper_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_papers_by_user(
        self, 
        user_id: str, 
        offset: int = 0, 
        limit: int = 20
    ) -> tuple[List[ResearchPaperModel], int]:
        """ユーザーの論文一覧を取得"""
        # 総数取得
        count_stmt = select(func.count(ResearchPaperModel.id)).where(
            ResearchPaperModel.user_id == user_id
        )
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()
        
        # 論文一覧取得
        stmt = (
            select(ResearchPaperModel)
            .where(ResearchPaperModel.user_id == user_id)
            .order_by(ResearchPaperModel.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        papers = result.scalars().all()
        
        return list(papers), total
    
    async def update_paper(
        self, 
        paper_id: str, 
        update_data: Dict[str, Any]
    ) -> ResearchPaperModel:
        """論文を更新"""
        update_data["updated_at"] = datetime.utcnow()
        
        stmt = (
            update(ResearchPaperModel)
            .where(ResearchPaperModel.id == paper_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        
        return await self.get_paper_by_id(paper_id)
    
    async def delete_paper(self, paper_id: str) -> bool:
        """論文を削除（関連するセクション等も自動削除）"""
        stmt = delete(ResearchPaperModel).where(ResearchPaperModel.id == paper_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
    
    # === セクション関連 ===
    async def create_section(
        self,
        paper_id: str,
        position: int,
        section_number: str,
        title: str,
        user_id: Optional[str] = None,
        content: str = "",
        summary: str = ""
    ) -> PaperSectionModel:
        """新しいセクションを作成"""
        if not user_id:
            # paper_idからuser_idを取得
            paper = await self.get_paper_by_id(paper_id)
            if not paper:
                raise ValueError(f"Paper not found: {paper_id}")
            user_id = paper.user_id
        
        section = PaperSectionModel(
            id=str(uuid.uuid4()),
            paper_id=paper_id,
            user_id=user_id,
            position=position,
            section_number=section_number,
            title=title,
            content=content,
            summary=summary,
            word_count=len(content.split()) if content else 0,
            status="draft"
        )
        
        self.session.add(section)
        await self.session.commit()
        await self.session.refresh(section)
        return section
    
    async def get_section_by_id(self, section_id: str) -> Optional[PaperSectionModel]:
        """IDでセクションを取得"""
        stmt = select(PaperSectionModel).where(
            and_(
                PaperSectionModel.id == section_id,
                PaperSectionModel.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_sections_by_paper(self, paper_id: str) -> List[PaperSectionModel]:
        """論文のセクション一覧を位置順で取得"""
        stmt = (
            select(PaperSectionModel)
            .where(
                and_(
                    PaperSectionModel.paper_id == paper_id,
                    PaperSectionModel.is_deleted == False
                )
            )
            .order_by(PaperSectionModel.position)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_next_position(self, paper_id: str) -> int:
        """論文内で次に使用する位置番号を取得"""
        stmt = (
            select(func.max(PaperSectionModel.position))
            .where(
                and_(
                    PaperSectionModel.paper_id == paper_id,
                    PaperSectionModel.is_deleted == False
                )
            )
        )
        result = await self.session.execute(stmt)
        max_position = result.scalar()
        return (max_position or 0) + 1
    
    async def update_section(
        self, 
        section_id: str, 
        update_data: Dict[str, Any]
    ) -> PaperSectionModel:
        """セクションを更新（履歴も保存）"""
        # 現在の状態を履歴として保存
        current_section = await self.get_section_by_id(section_id)
        if current_section:
            await self._create_section_history(current_section)
        
        # 更新実行
        update_data["updated_at"] = datetime.utcnow()
        
        stmt = (
            update(PaperSectionModel)
            .where(PaperSectionModel.id == section_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        
        return await self.get_section_by_id(section_id)
    
    async def delete_section(self, section_id: str) -> bool:
        """セクションを論理削除（子セクションも含む）"""
        section = await self.get_section_by_id(section_id)
        if not section:
            return False
        
        # 子セクションも論理削除
        children = await self.get_child_sections(section_id)
        all_section_ids = [section_id] + [child.id for child in children]
        
        stmt = (
            update(PaperSectionModel)
            .where(PaperSectionModel.id.in_(all_section_ids))
            .values(is_deleted=True, updated_at=datetime.utcnow())
        )
        await self.session.execute(stmt)
        await self.session.commit()
        
        return True
    
    async def _create_section_history(self, section: PaperSectionModel) -> PaperSectionHistoryModel:
        """セクション履歴を作成"""
        # 現在のバージョン番号を取得
        count_stmt = select(func.count(PaperSectionHistoryModel.id)).where(
            PaperSectionHistoryModel.section_id == section.id
        )
        count_result = await self.session.execute(count_stmt)
        version_number = count_result.scalar() + 1
        
        history = PaperSectionHistoryModel(
            id=str(uuid.uuid4()),
            section_id=section.id,
            title=section.title,
            content=section.content,
            summary=section.summary,
            version_number=version_number,
            change_description="自動バックアップ"
        )
        
        self.session.add(history)
        await self.session.commit()
        return history
    
    async def get_section_history(self, section_id: str) -> List[PaperSectionHistoryModel]:
        """セクション履歴を取得"""
        stmt = (
            select(PaperSectionHistoryModel)
            .where(PaperSectionHistoryModel.section_id == section_id)
            .order_by(PaperSectionHistoryModel.version_number.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    # === チャット関連 ===
    async def create_chat_session(
        self,
        paper_id: str,
        user_id: str,
        title: str
    ) -> PaperChatSessionModel:
        """新しいチャットセッションを作成"""
        session = PaperChatSessionModel(
            id=str(uuid.uuid4()),
            paper_id=paper_id,
            user_id=user_id,
            title=title
        )
        
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session
    
    async def get_chat_session_by_id(self, session_id: str) -> Optional[PaperChatSessionModel]:
        """チャットセッションを取得"""
        stmt = select(PaperChatSessionModel).where(
            PaperChatSessionModel.id == session_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_chat_sessions_by_paper(self, paper_id: str) -> List[PaperChatSessionModel]:
        """論文のチャットセッション一覧を取得"""
        stmt = (
            select(PaperChatSessionModel)
            .where(PaperChatSessionModel.paper_id == paper_id)
            .order_by(PaperChatSessionModel.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def create_chat_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_name: Optional[str] = None,
        todo_tasks: Optional[List[Dict]] = None,
        references: Optional[List[Dict]] = None
    ) -> PaperChatMessageModel:
        """チャットメッセージを作成"""
        message = PaperChatMessageModel(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            agent_name=agent_name,
            todo_tasks=todo_tasks or [],
            references=references or []
        )
        
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        
        # セッションの更新日時も更新
        await self.session.execute(
            update(PaperChatSessionModel)
            .where(PaperChatSessionModel.id == session_id)
            .values(updated_at=datetime.utcnow())
        )
        await self.session.commit()
        
        return message
    
    async def get_chat_messages_by_session(self, session_id: str) -> List[PaperChatMessageModel]:
        """セッションのメッセージ一覧を取得"""
        stmt = (
            select(PaperChatMessageModel)
            .where(PaperChatMessageModel.session_id == session_id)
            .order_by(PaperChatMessageModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def reorder_sections(self, paper_id: str, section_orders: List[Dict[str, Any]]) -> bool:
        """
        セクションの順序を一括で変更
        section_orders: [{"section_id": "xxx", "new_position": 1}, ...]
        """
        try:
            # ステップ1: 一時的なpositionに変更してUNIQUE制約を回避
            for i, order in enumerate(section_orders):
                temp_position = 1000 + i  # 十分に大きな値でUNIQUE制約を回避
                stmt = (
                    update(PaperSectionModel)
                    .where(PaperSectionModel.id == order["section_id"])
                    .values(
                        position=temp_position,
                        updated_at=datetime.utcnow()
                    )
                )
                await self.session.execute(stmt)
            
            # ステップ2: 正しいpositionに更新（section_numberは保持）
            for order in section_orders:
                stmt = (
                    update(PaperSectionModel)
                    .where(PaperSectionModel.id == order["section_id"])
                    .values(
                        position=order["new_position"],
                        updated_at=datetime.utcnow()
                    )
                )
                await self.session.execute(stmt)
            
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"セクション順序変更エラー: {e}")
            return False
    
    async def move_section_to_position(self, section_id: str, new_position: int) -> bool:
        """
        指定セクションを新しい位置に移動
        """
        try:
            # 対象セクションの取得
            section = await self.get_section_by_id(section_id)
            if not section:
                return False
            
            # 同じ論文の全セクションを取得
            sections = await self.get_sections_by_paper(section.paper_id)
            if not sections or new_position < 1 or new_position > len(sections):
                return False
            
            # 新しい並び順を計算
            sections_list = list(sections)
            current_section = next(s for s in sections_list if s.id == section_id)
            sections_list.remove(current_section)
            sections_list.insert(new_position - 1, current_section)
            
            # position値を再割り当て（section_numberは保持）
            section_orders = []
            for i, s in enumerate(sections_list, 1):
                section_orders.append({
                    "section_id": s.id,
                    "new_position": i
                })
            
            return await self.reorder_sections(section.paper_id, section_orders)
        
        except Exception as e:
            logger.error(f"セクション移動エラー: {e}")
            return False