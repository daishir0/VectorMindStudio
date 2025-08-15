from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.infrastructure.database.session import get_session
from app.schemas.chat import (
    ChatRequest, 
    ChatResponse, 
    ChatSessionListResponse, 
    ChatHistoryResponse,
    ChatSession,
    ChatMessage
)
from app.schemas.common import ApiResponse
from app.domain.entities.user import User
from app.api.deps.auth import get_current_active_user
from app.services.chat_service import ChatService

router = APIRouter()

@router.post("/message", response_model=ApiResponse[ChatResponse])
async def send_chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """チャットメッセージを送信してRAG応答を取得"""
    
    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )
    
    try:
        chat_service = ChatService(session)
        response = await chat_service.process_chat_message(
            user_id=current_user.id,
            message=request.message,
            session_id=request.session_id,
            max_documents=request.max_documents or 5,
            tags=request.tags
        )
        
        return ApiResponse(
            success=True,
            data=response,
            message="Chat response generated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}"
        )

@router.get("/sessions", response_model=ApiResponse[ChatSessionListResponse])
async def get_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """ユーザーのチャットセッション一覧を取得"""
    
    try:
        chat_service = ChatService(session)
        sessions_data = await chat_service.get_user_sessions(current_user.id)
        
        sessions = [
            ChatSession(
                id=s["id"],
                title=s["title"],
                created_at=s["created_at"],
                updated_at=s["updated_at"],
                message_count=s["message_count"]
            )
            for s in sessions_data
        ]
        
        response = ChatSessionListResponse(sessions=sessions)
        
        return ApiResponse(
            success=True,
            data=response,
            message="Chat sessions retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat sessions: {str(e)}"
        )

@router.get("/sessions/{session_id}/history", response_model=ApiResponse[ChatHistoryResponse])
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """特定のセッションの会話履歴を取得"""
    
    try:
        chat_service = ChatService(session)
        messages = await chat_service.get_session_history(session_id, current_user.id)
        
        response = ChatHistoryResponse(
            session_id=session_id,
            messages=messages
        )
        
        return ApiResponse(
            success=True,
            data=response,
            message="Chat history retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )

@router.delete("/sessions/{session_id}", response_model=ApiResponse[dict])
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """チャットセッションを削除"""
    
    try:
        chat_service = ChatService(session)
        success = await chat_service.delete_session(session_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return ApiResponse(
            success=True,
            data={"message": "Chat session deleted successfully"},
            message="セッションが正常に削除されました"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chat session: {str(e)}"
        )