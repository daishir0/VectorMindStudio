from fastapi import UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import shutil
import logging
import uuid
import asyncio

from app.infrastructure.repositories.file_repository import FileRepository
from app.infrastructure.files.storage import get_originals_dir, get_converted_dir
from app.infrastructure.conversion.markitdown_converter import MarkitdownConverter
from app.services.vector_service import VectorService
from app.schemas.file import FileUploadResponse
from app.infrastructure.database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# 同時処理制限用セマフォ
CONCURRENT_PROCESSING_LIMIT = 3
processing_semaphore = asyncio.Semaphore(CONCURRENT_PROCESSING_LIMIT)

class FileService:
    def __init__(self, session: AsyncSession, background_tasks: BackgroundTasks):
        self.session = session
        self.repo = FileRepository(self.session)
        self.converter = MarkitdownConverter()
        self.vector_service = VectorService()
        self.background_tasks = background_tasks

    async def process_upload(self, file: UploadFile, user_id: str) -> FileUploadResponse:
        """アップロードされたファイルを処理し、DBに記録し、バックグラウンドで変換とベクトル化を開始する"""
        
        # 各ファイルアップロードに一意のディレクトリIDを生成
        upload_dir_id = str(uuid.uuid4())
        
        originals_dir = get_originals_dir()
        file_originals_dir = originals_dir / upload_dir_id
        file_originals_dir.mkdir(parents=True, exist_ok=True)
        file_location = file_originals_dir / file.filename
        
        try:
            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(file.file, file_object)
        except Exception as e:
            logger.error(f"Could not save file: {file.filename}. Error: {e}")
            raise IOError(f"Could not save file: {e}")

        upload_record = await self.repo.create_upload_record(
            user_id=user_id,
            filename=file.filename,
            content_type=file.content_type,
            size_bytes=file.size,
            original_path=str(file_location)
        )

        self.background_tasks.add_task(self.process_conversion_and_vectorization, upload_record.id, upload_dir_id)

        return FileUploadResponse(
            id=upload_record.id,
            filename=upload_record.filename,
            content_type=upload_record.content_type,
            size_bytes=upload_record.size_bytes,
            status=upload_record.status,
            created_at=upload_record.created_at
        )

    async def process_conversion_and_vectorization(self, upload_id: str, upload_dir_id: str):
        """ファイルの変換とベクトル化を非同期で実行"""
        async with processing_semaphore:  # 同時処理数を制限
            logger.info(f"Starting conversion for upload_id: {upload_id} (concurrent limit: {CONCURRENT_PROCESSING_LIMIT})")
            
            # Create a new database session for the background task
            async with AsyncSessionLocal() as session:
                try:
                    repo = FileRepository(session)
                    upload_record = await repo.get_by_id(upload_id)
                    if not upload_record:
                        logger.error(f"Upload record not found for id: {upload_id}")
                        return

                    await repo.update_status(upload_id, status="processing")

                    try:
                        input_path = get_originals_dir() / upload_dir_id / upload_record.filename
                        converted_dir = get_converted_dir() / upload_dir_id
                        logger.info(f"Converting {input_path} to {converted_dir}")
                        
                        # 同期処理のconvertを別スレッドで実行してgreenletエラーを回避
                        converted_path = await asyncio.to_thread(
                            self.converter.convert, 
                            input_path, 
                            converted_dir
                        )
                        logger.info(f"Conversion completed, result path: {converted_path}")
                        
                        logger.info(f"Updating database status for upload_id: {upload_id}")
                        updated_upload_record = await repo.update_status(
                            upload_id=upload_id,
                            status="completed",
                            converted_path=str(converted_path)
                        )
                        logger.info(f"Database updated successfully for upload_id: {upload_id}")
                        logger.info(f"Record after update - converted_path: {updated_upload_record.converted_path}")

                        # Start vectorization
                        await repo.update_vector_status(upload_id, status="processing")
                        
                        # Re-fetch the record to ensure we have the latest converted_path
                        fresh_upload_record = await repo.get_by_id(upload_id)
                        if not fresh_upload_record or not fresh_upload_record.converted_path:
                            logger.error(f"Converted path missing after update for upload_id: {upload_id}")
                            logger.error(f"Fresh record converted_path: {fresh_upload_record.converted_path if fresh_upload_record else 'Record not found'}")
                            raise Exception(f"Converted file not found for upload id {upload_id}")
                        
                        logger.info(f"Using fresh record with converted_path: {fresh_upload_record.converted_path}")
                        await self.vector_service.create_embeddings_for_upload(fresh_upload_record)
                        await repo.update_vector_status(upload_id, status="completed")
                        logger.info(f"Vectorization successful for upload_id: {upload_id}")

                    except Exception as e:
                        full_error = str(e)
                        logger.error(f"Processing failed for upload_id: {upload_id}. Error: {full_error}")
                        # Determine which step failed
                        current_upload = await repo.get_by_id(upload_id)
                        if current_upload and current_upload.status != "completed":
                            await repo.update_status(upload_id, status="failed", error_message=full_error)
                        else:
                            await repo.update_vector_status(upload_id, status="failed", error_message=full_error)
                except Exception as session_error:
                    logger.error(f"Session error in background task: {session_error}")
