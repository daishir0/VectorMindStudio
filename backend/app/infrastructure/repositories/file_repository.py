from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional, List, Tuple
import uuid
from datetime import datetime
import logging

from app.infrastructure.database.models import UploadModel

logger = logging.getLogger(__name__)

class FileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_upload_record(
        self, 
        user_id: str, 
        filename: str, 
        content_type: str, 
        size_bytes: int, 
        original_path: str
    ) -> UploadModel:
        """アップロードレコードをデータベースに作成"""
        new_upload = UploadModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            original_path=original_path,
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(new_upload)
        await self.session.commit()
        try:
            await self.session.refresh(new_upload)
        except Exception as e:
            logger.warning(f"Failed to refresh new upload {new_upload.id}: {e}")
        return new_upload

    async def get_by_id(self, upload_id: str) -> Optional[UploadModel]:
        """IDでアップロードレコードを取得"""
        stmt = select(UploadModel).where(UploadModel.id == upload_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_files_by_user(self, user_id: str, offset: int, limit: int) -> Tuple[List[UploadModel], int]:
        """ユーザーのファイル一覧をページネーション付きで取得"""
        # Get total count
        count_stmt = select(func.count(UploadModel.id)).where(UploadModel.user_id == user_id)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # Get paginated results
        stmt = select(UploadModel).where(UploadModel.user_id == user_id).order_by(UploadModel.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        files = result.scalars().all()
        return files, total

    async def update_status(
        self, 
        upload_id: str, 
        status: str, 
        converted_path: Optional[str] = None, 
        error_message: Optional[str] = None
    ) -> Optional[UploadModel]:
        """アップロードステータスを更新"""
        logger.info(f"Repository update_status called with: upload_id={upload_id}, status={status}, converted_path={converted_path}")
        upload = await self.get_by_id(upload_id)
        if upload:
            upload.status = status
            if converted_path and converted_path.strip():  # 空文字列もチェック
                logger.info(f"Setting converted_path to: {converted_path}")
                upload.converted_path = converted_path
            elif converted_path is not None:  # 明示的にNoneでない場合のみ警告
                logger.warning(f"converted_path is empty/invalid: '{converted_path}'")
            if error_message:
                upload.error_message = error_message
            upload.updated_at = datetime.utcnow()
            await self.session.commit()
            try:
                await self.session.refresh(upload)
                logger.info(f"After update - upload.converted_path: {upload.converted_path}")
            except Exception as e:
                logger.warning(f"Failed to refresh upload {upload_id}: {e}")
        return upload

    async def update_vector_status(
        self, 
        upload_id: str, 
        status: str, 
        error_message: Optional[str] = None
    ) -> Optional[UploadModel]:
        """ベクトル化ステータスを更新"""
        upload = await self.get_by_id(upload_id)
        if upload:
            upload.vector_status = status
            if error_message:
                # To avoid overwriting a conversion error
                upload.error_message = f"{upload.error_message or ''} | Vectorization Error: {error_message}"
            upload.updated_at = datetime.utcnow()
            await self.session.commit()
            try:
                await self.session.refresh(upload)
            except Exception as e:
                logger.warning(f"Failed to refresh upload {upload_id}: {e}")
        return upload

    async def delete(self, upload_id: str) -> bool:
        """アップロードレコードを削除"""
        upload = await self.get_by_id(upload_id)
        if upload:
            await self.session.delete(upload)
            await self.session.commit()
            logger.info(f"Deleted upload record: {upload_id}")
            return True
        return False

    async def get_files_by_user_with_filters(
        self, user_id: str, offset: int, limit: int, 
        search: Optional[str] = None, tags: Optional[List[str]] = None,
        sort_field: Optional[str] = None, sort_order: str = "asc"
    ) -> Tuple[List[UploadModel], int]:
        """ユーザーのファイル一覧を検索・フィルタリング付きで取得"""
        # ベースクエリ
        base_query = select(UploadModel).where(UploadModel.user_id == user_id)
        
        # ファイル名での検索
        if search:
            base_query = base_query.where(UploadModel.filename.contains(search))
        
        # タグでの検索（JSONフィールドでの検索）
        if tags:
            logger.info(f"Applying tag filters: {tags}")
            for tag in tags:
                # 日本語文字がUnicodeエスケープ形式で保存されているため、エンコードして検索
                import json
                # タグをJSONエンコードして、データベース内の形式に合わせる
                encoded_tag = json.dumps(tag, ensure_ascii=True)[1:-1]  # クォートを除去
                logger.info(f"Adding tag filter for: {tag} -> searching for: {encoded_tag}")
                base_query = base_query.where(UploadModel.tags.contains(encoded_tag))
        
        # 総件数取得
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # ソート処理
        if sort_field and hasattr(UploadModel, sort_field):
            sort_column = getattr(UploadModel, sort_field)
            if sort_order.lower() == "desc":
                result_query = base_query.order_by(sort_column.desc())
            else:
                result_query = base_query.order_by(sort_column.asc())
        else:
            # デフォルトソート: 作成日時の新しい順
            result_query = base_query.order_by(UploadModel.created_at.desc())
        
        # ページネーション適用
        result_query = result_query.offset(offset).limit(limit)
        result = await self.session.execute(result_query)
        files = result.scalars().all()
        
        return files, total

    async def update_tags(self, upload_id: str, tags: List[str]) -> Optional[UploadModel]:
        """ファイルのタグを更新"""
        upload = await self.get_by_id(upload_id)
        if upload:
            upload.tags = tags
            upload.updated_at = datetime.utcnow()
            await self.session.commit()
            try:
                await self.session.refresh(upload)
                logger.info(f"Updated tags for upload: {upload_id}")
            except Exception as e:
                logger.warning(f"Failed to refresh upload {upload_id}: {e}")
            return upload
        return None

    async def bulk_update_tags(self, file_ids: List[str], tags: List[str], user_id: str) -> int:
        """複数ファイルのタグを一括更新"""
        # ユーザーが所有するファイルのみを対象に更新
        stmt = select(UploadModel).where(
            and_(
                UploadModel.id.in_(file_ids),
                UploadModel.user_id == user_id
            )
        )
        
        result = await self.session.execute(stmt)
        files = result.scalars().all()
        
        updated_count = 0
        for file in files:
            file.tags = tags
            file.updated_at = datetime.utcnow()
            updated_count += 1
        
        await self.session.commit()
        logger.info(f"Bulk updated tags for {updated_count} files")
        return updated_count

    async def get_all_user_tags(self, user_id: str) -> set:
        """ユーザーの全ファイルからユニークなタグを取得"""
        stmt = select(UploadModel.tags).where(UploadModel.user_id == user_id)
        result = await self.session.execute(stmt)
        
        all_tags = set()
        for tags_list in result.scalars():
            if tags_list:  # None チェック
                all_tags.update(tags_list)
        
        return all_tags
