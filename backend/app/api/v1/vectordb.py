from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from pydantic import BaseModel

from app.infrastructure.database.session import get_session
from app.schemas.common import ApiResponse
from app.domain.entities.user import User
from app.api.deps.auth import get_current_active_user
from app.services.vector_service import VectorService
from app.infrastructure.external.chroma_client import chroma_client

router = APIRouter()

class VectorDocumentInfo(BaseModel):
    id: str
    filename: str
    upload_id: str
    chunk_number: int
    chunk_size: int
    document_preview: str  # 最初の100文字程度
    distance: float = None
    relevance_score: float = None

class VectorDBStats(BaseModel):
    total_documents: int
    unique_files: int
    total_chunks: int
    average_chunk_size: float
    collection_name: str
    user_documents: List[VectorDocumentInfo]

@router.get("/stats", response_model=ApiResponse[VectorDBStats])
async def get_vectordb_stats(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """現在のユーザーのVectorDB統計情報を取得"""
    try:
        # ChromaDBに接続されていない場合は接続
        if not chroma_client._collection:
            await chroma_client.connect()
        
        collection = chroma_client.collection
        
        # ユーザーのドキュメントを取得
        user_docs = collection.get(
            where={"user_id": current_user.id},
            include=["documents", "metadatas"]
        )
        
        if not user_docs['ids']:
            # ユーザーのドキュメントがない場合
            stats = VectorDBStats(
                total_documents=0,
                unique_files=0,
                total_chunks=0,
                average_chunk_size=0.0,
                collection_name=chroma_client.collection_name,
                user_documents=[]
            )
            return ApiResponse(success=True, data=stats)
        
        # 統計情報を計算
        total_documents = len(user_docs['ids'])
        unique_files = len(set(metadata['upload_id'] for metadata in user_docs['metadatas']))
        total_chunks = total_documents
        chunk_sizes = [metadata['chunk_size'] for metadata in user_docs['metadatas']]
        average_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0.0
        
        # ドキュメント情報を構築
        user_documents = []
        for i, doc_id in enumerate(user_docs['ids']):
            metadata = user_docs['metadatas'][i]
            document = user_docs['documents'][i] if i < len(user_docs['documents']) else ""
            
            doc_info = VectorDocumentInfo(
                id=doc_id,
                filename=metadata.get('filename', 'Unknown'),
                upload_id=metadata.get('upload_id', ''),
                chunk_number=metadata.get('chunk_number', 0),
                chunk_size=metadata.get('chunk_size', 0),
                document_preview=document[:150] + "..." if len(document) > 150 else document
            )
            user_documents.append(doc_info)
        
        # ファイル名でソート
        user_documents.sort(key=lambda x: (x.filename, x.chunk_number))
        
        stats = VectorDBStats(
            total_documents=total_documents,
            unique_files=unique_files,
            total_chunks=total_chunks,
            average_chunk_size=round(average_chunk_size, 2),
            collection_name=chroma_client.collection_name,
            user_documents=user_documents
        )
        
        return ApiResponse(success=True, data=stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve VectorDB stats: {e}"
        )

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

@router.post("/search-preview", response_model=ApiResponse[List[VectorDocumentInfo]])
async def search_preview(
    request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """ベクター検索のプレビューを実行"""
    try:
        vector_service = VectorService()
        results = await vector_service.search_similar(
            query=request.query,
            user_id=current_user.id,
            limit=request.limit
        )
        
        preview_results = []
        for result in results:
            metadata = result['metadata']
            doc_info = VectorDocumentInfo(
                id=result['id'],
                filename=metadata.get('filename', 'Unknown'),
                upload_id=metadata.get('upload_id', ''),
                chunk_number=metadata.get('chunk_number', 0),
                chunk_size=metadata.get('chunk_size', 0),
                document_preview=result['document'][:150] + "..." if len(result['document']) > 150 else result['document'],
                distance=result['distance'],
                relevance_score=result['relevance_score']
            )
            preview_results.append(doc_info)
        
        return ApiResponse(success=True, data=preview_results)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not perform search: {e}"
        )