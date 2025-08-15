from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any

from app.services.vector_service import VectorService
from app.schemas.common import ApiResponse
from app.domain.entities.user import User
from app.api.deps.auth import get_current_active_user

router = APIRouter()

class SearchQuery(BaseModel):
    query: str
    limit: int = 10

class SearchResult(BaseModel):
    id: str
    document: str
    metadata: Dict[str, Any]
    distance: float
    relevance_score: float

@router.post("", response_model=ApiResponse[List[SearchResult]])
async def search_documents(
    search_query: SearchQuery,
    current_user: User = Depends(get_current_active_user)
):
    """セマンティック検索を実行して類似ドキュメントを取得する"""
    try:
        vector_service = VectorService()
        results = await vector_service.search_similar(
            query=search_query.query, 
            limit=search_query.limit, 
            user_id=current_user.id
        )
        return ApiResponse(success=True, data=results)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {e}"
        )
