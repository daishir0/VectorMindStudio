from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pathlib import Path

from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.output_repository import OutputRepository
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.output import OutputDetailResponse # This schema needs to be created
from app.domain.entities.user import User
from app.api.deps.auth import get_current_active_user

router = APIRouter()

@router.get("", response_model=ApiResponse[PaginatedResponse[OutputDetailResponse]])
async def list_outputs(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """生成されたアウトプットの一覧を取得"""
    repo = OutputRepository(session)
    offset = (page - 1) * limit
    outputs, total = await repo.get_outputs_by_user(user_id=current_user.id, offset=offset, limit=limit)
    
    response_data = PaginatedResponse(
        items=outputs,
        total=total,
        page=page,
        limit=limit,
        has_more=(total > offset + len(outputs))
    )
    return ApiResponse(success=True, data=response_data)

@router.get("/{output_id}", response_model=ApiResponse[OutputDetailResponse])
async def get_output(
    output_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """特定のアウトプット詳細を取得"""
    repo = OutputRepository(session)
    output = await repo.get_by_id(output_id=output_id, user_id=current_user.id)
    if not output:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
    return ApiResponse(success=True, data=output)

@router.get("/{output_id}/content")
async def get_output_content(
    output_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """アウトプットのコンテンツを取得"""
    repo = OutputRepository(session)
    output = await repo.get_by_id(output_id=output_id, user_id=current_user.id)
    
    if not output:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
    
    if not output.content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output content not available")
        
    # Return the content directly as it's already stored in the database
    return ApiResponse(success=True, data={
        "content": output.content,
        "output_id": output.id
    })

@router.delete("/{output_id}")
async def delete_output(
    output_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """アウトプットを削除"""
    repo = OutputRepository(session)
    
    # First, check if output exists and belongs to user
    output = await repo.get_by_id(output_id=output_id, user_id=current_user.id)
    if not output:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
    
    # Delete the output from database
    success = await repo.delete(output_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete output")
    
    return ApiResponse(success=True, data={"message": f"Output {output_id} deleted successfully"})
