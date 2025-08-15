from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Tuple
import logging

from app.infrastructure.database.models import OutputModel

logger = logging.getLogger(__name__)

class OutputRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, output_id: str, user_id: str) -> Optional[OutputModel]:
        """IDでアウトプットを取得"""
        stmt = select(OutputModel).where(OutputModel.id == output_id, OutputModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_outputs_by_user(
        self, user_id: str, offset: int, limit: int
    ) -> Tuple[List[OutputModel], int]:
        """ユーザーのアウトプット一覧をページネーション付きで取得"""
        count_stmt = select(func.count(OutputModel.id)).where(OutputModel.user_id == user_id)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = (
            select(OutputModel)
            .where(OutputModel.user_id == user_id)
            .order_by(OutputModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        outputs = result.scalars().all()
        return outputs, total

    async def get_by_id_only(self, output_id: str) -> Optional[OutputModel]:
        """IDでアウトプットを取得（ユーザーチェックなし）"""
        stmt = select(OutputModel).where(OutputModel.id == output_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, output_id: str) -> bool:
        """アウトプットレコードを削除"""
        output = await self.get_by_id_only(output_id)
        if output:
            await self.session.delete(output)
            await self.session.commit()
            logger.info(f"Deleted output record: {output_id}")
            return True
        return False
