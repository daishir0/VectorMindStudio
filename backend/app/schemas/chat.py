from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    """チャットメッセージ"""
    id: str
    role: str  # 'user' | 'assistant'
    content: str
    timestamp: datetime
    sources: Optional[List[str]] = None


class ChatRequest(BaseModel):
    """チャットリクエスト"""
    message: str
    session_id: Optional[str] = None
    max_documents: Optional[int] = 5  # 取得する関連文書の最大数
    tags: Optional[List[str]] = None  # 参照文書のタグフィルター


class ChatResponse(BaseModel):
    """チャット応答"""
    message: ChatMessage
    session_id: str
    sources: Optional[List[str]] = None


class ChatSession(BaseModel):
    """チャットセッション"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ChatSessionListResponse(BaseModel):
    """チャットセッション一覧"""
    sessions: List[ChatSession]


class ChatHistoryResponse(BaseModel):
    """チャット履歴"""
    session_id: str
    messages: List[ChatMessage]