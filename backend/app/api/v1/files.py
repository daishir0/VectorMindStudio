from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel

from app.infrastructure.database.session import get_session
from app.schemas.file import FileUploadResponse, FileListResponse
from app.schemas.common import ApiResponse, PaginatedResponse
from app.domain.entities.user import User
from app.api.deps.auth import get_current_active_user
from app.services.file_service import FileService
from app.services.vector_service import VectorService
from app.infrastructure.repositories.file_repository import FileRepository

router = APIRouter()

class UpdateTagsRequest(BaseModel):
    tags: List[str]

class BulkUpdateTagsRequest(BaseModel):
    file_ids: List[str]
    tags: List[str]

class BulkDeleteRequest(BaseModel):
    file_ids: List[str]

@router.post("/upload", response_model=ApiResponse[FileUploadResponse], status_code=status.HTTP_202_ACCEPTED)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """ファイルアップロードエンドポイント"""
    
    # ファイルサイズチェック (例: 50MB)
    if file.size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the limit of 50MB"
        )

    try:
        file_service = FileService(session, background_tasks)
        uploaded_file = await file_service.process_upload(
            file=file,
            user_id=current_user.id
        )
        
        return ApiResponse(
            success=True, 
            data=uploaded_file, 
            message="File upload received. Processing will start shortly."
        )
    except IOError as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not process file '{file.filename}': {e}"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while processing '{file.filename}': {e}"
        )

@router.get("", response_model=ApiResponse[PaginatedResponse[FileListResponse]])
async def list_files(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = Query(None, description="ファイル名で検索"),
    tags: Optional[str] = Query(None, description="タグで検索（カンマ区切り）"),
    sort_field: Optional[str] = Query(None, description="ソートフィールド（filename, status, created_at, updated_at）"),
    sort_order: Optional[str] = Query("asc", description="ソート順序（asc, desc）"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """アップロードされたファイルの一覧を取得（検索・フィルタリング機能付き）"""
    file_repo = FileRepository(session)
    offset = (page - 1) * limit
    
    # タグリストを準備
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
    
    files, total = await file_repo.get_files_by_user_with_filters(
        user_id=current_user.id, 
        offset=offset, 
        limit=limit,
        search=search,
        tags=tag_list,
        sort_field=sort_field,
        sort_order=sort_order
    )
    
    response_data = PaginatedResponse(
        items=files,
        total=total,
        page=page,
        limit=limit,
        has_more=(total > offset + len(files))
    )
    
    return ApiResponse(success=True, data=response_data)

@router.get("/{file_id}", response_model=ApiResponse[FileListResponse])
async def get_file_details(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """ファイルの詳細を取得"""
    file_repo = FileRepository(session)
    file = await file_repo.get_by_id(file_id)
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # ユーザーが所有者かチェック
    if file.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    file_response = FileListResponse(
        id=file.id,
        filename=file.filename,
        status=file.status,
        tags=file.tags or [],
        created_at=file.created_at,
        updated_at=file.updated_at
    )
    
    return ApiResponse(success=True, data=file_response)

@router.get("/{file_id}/content")
async def get_file_content(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """ファイルの内容を取得（変換済みMarkdownファイル）"""
    file_repo = FileRepository(session)
    file = await file_repo.get_by_id(file_id)
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # ユーザーが所有者かチェック
    if file.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # 変換済みファイルが存在するかチェック
    if not file.converted_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Converted file not available"
        )
    
    converted_path = Path(file.converted_path)
    if not converted_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Converted file not found on disk"
        )
    
    try:
        with open(converted_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return ApiResponse(
            success=True,
            data={"content": content, "filename": file.filename}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read file: {e}"
        )

@router.delete("/{file_id}", response_model=ApiResponse[dict])
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """ファイルを削除"""
    file_repo = FileRepository(session)
    file = await file_repo.get_by_id(file_id)
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # ユーザーが所有者かチェック
    if file.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # ChromaDBからベクターデータを削除
        vector_service = VectorService()
        try:
            await vector_service.delete_vectors_by_upload_id(file_id)
        except Exception as e:
            # ベクターデータの削除が失敗してもファイル削除は続行
            print(f"Warning: Failed to delete vector data for file {file_id}: {e}")
        
        # ファイルシステムからファイルを削除
        if file.original_path:
            original_path = Path(file.original_path)
            if original_path.exists():
                original_path.unlink()
        
        if file.converted_path:
            converted_path = Path(file.converted_path)
            if converted_path.exists():
                converted_path.unlink()
        
        # データベースから削除
        await file_repo.delete(file_id)
        
        return ApiResponse(
            success=True,
            data={"message": "File deleted successfully"},
            message="ファイルが正常に削除されました"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not delete file: {e}"
        )

@router.patch("/bulk/tags", response_model=ApiResponse[dict])
async def bulk_update_tags(
    request: BulkUpdateTagsRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """複数ファイルのタグを一括更新"""
    file_repo = FileRepository(session)
    
    try:
        updated_count = await file_repo.bulk_update_tags(
            file_ids=request.file_ids,
            tags=request.tags,
            user_id=current_user.id
        )
        
        return ApiResponse(
            success=True,
            data={"updated_count": updated_count},
            message=f"{updated_count}件のファイルのタグが更新されました"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not update tags: {e}"
        )

@router.patch("/{file_id}/tags", response_model=ApiResponse[FileListResponse])
async def update_file_tags(
    file_id: str,
    request: UpdateTagsRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """ファイルのタグを更新"""
    file_repo = FileRepository(session)
    
    # ファイルの存在確認と権限チェック
    file = await file_repo.get_by_id(file_id)
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    if file.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    try:
        # タグを更新
        updated_file = await file_repo.update_tags(file_id, request.tags)
        
        file_response = FileListResponse(
            id=updated_file.id,
            filename=updated_file.filename,
            status=updated_file.status,
            tags=updated_file.tags or [],
            created_at=updated_file.created_at,
            updated_at=updated_file.updated_at
        )
        
        return ApiResponse(success=True, data=file_response, message="タグが更新されました")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not update tags: {e}"
        )

@router.post("/bulk-delete", response_model=ApiResponse[dict])
async def bulk_delete_files(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """複数ファイルを一括削除"""
    if not request.file_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file IDs provided"
        )
    
    file_repo = FileRepository(session)
    vector_service = VectorService()
    
    deleted_count = 0
    failed_count = 0
    errors = []
    
    for file_id in request.file_ids:
        try:
            file = await file_repo.get_by_id(file_id)
            
            if not file:
                failed_count += 1
                errors.append(f"File {file_id} not found")
                continue
            
            # ユーザーが所有者かチェック
            if file.user_id != current_user.id:
                failed_count += 1
                errors.append(f"Access denied for file {file_id}")
                continue
            
            # ChromaDBからベクターデータを削除
            try:
                await vector_service.delete_vectors_by_upload_id(file_id)
            except Exception as e:
                # ベクターデータの削除が失敗してもファイル削除は続行
                print(f"Warning: Failed to delete vector data for file {file_id}: {e}")
            
            # ファイルシステムからファイルを削除
            if file.original_path:
                original_path = Path(file.original_path)
                if original_path.exists():
                    original_path.unlink()
            
            if file.converted_path:
                converted_path = Path(file.converted_path)
                if converted_path.exists():
                    converted_path.unlink()
            
            # データベースから削除
            await file_repo.delete(file_id)
            deleted_count += 1
            
        except Exception as e:
            failed_count += 1
            errors.append(f"Failed to delete file {file_id}: {str(e)}")
    
    response_data = {
        "deleted_count": deleted_count,
        "failed_count": failed_count,
        "errors": errors if errors else None
    }
    
    if failed_count > 0:
        message = f"{deleted_count}件のファイルを削除しました。{failed_count}件の削除に失敗しました。"
    else:
        message = f"{deleted_count}件のファイルを正常に削除しました。"
    
    return ApiResponse(
        success=deleted_count > 0,
        data=response_data,
        message=message
    )
