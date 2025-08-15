import os
import uuid
from typing import List, Optional, Tuple
from datetime import datetime
import logging

import openai
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.chat_repository import ChatRepository
from app.services.vector_service import VectorService
from app.infrastructure.database.models import ChatSessionModel, ChatMessageModel
from app.schemas.chat import ChatMessage, ChatResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.chat_repo = ChatRepository(session)
        self.vector_service = VectorService()
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    async def create_or_get_session(self, user_id: str, session_id: Optional[str] = None) -> ChatSessionModel:
        """チャットセッションを作成または取得"""
        if session_id:
            session = await self.chat_repo.get_session_by_id(session_id, user_id)
            if session:
                return session
        
        # 新しいセッションを作成
        return await self.chat_repo.create_session(user_id, "新しいチャット")

    async def process_chat_message(
        self, 
        user_id: str, 
        message: str, 
        session_id: Optional[str] = None,
        max_documents: int = 5,
        tags: Optional[List[str]] = None
    ) -> ChatResponse:
        """チャットメッセージを処理してRAG応答を生成"""
        
        # セッションを取得または作成
        session = await self.create_or_get_session(user_id, session_id)
        
        # ユーザーメッセージを保存
        user_message = await self.chat_repo.add_message(
            session_id=session.id,
            role="user",
            content=message
        )

        try:
            # ベクター検索で関連文書を取得（タグフィルター適用）
            relevant_docs = await self.vector_service.search_similar_content(
                query=message,
                user_id=user_id,
                limit=max_documents,
                tags=tags
            )
            
            # 会話履歴を取得（コンテキスト用）
            recent_messages = await self.chat_repo.get_recent_messages(session.id, limit=6)
            
            # OpenAI APIで応答を生成
            ai_response, sources = await self._generate_ai_response(
                user_message=message,
                relevant_docs=relevant_docs,
                conversation_history=recent_messages[:-1]  # 最新のユーザーメッセージは除く
            )
            
            # AIメッセージを保存
            assistant_message = await self.chat_repo.add_message(
                session_id=session.id,
                role="assistant",
                content=ai_response,
                sources=sources
            )
            
            # セッションタイトルを初回メッセージから生成
            if session.title == "新しいチャット":
                title = self._generate_session_title(message)
                await self.chat_repo.update_session_title(session.id, user_id, title)
            
            # レスポンスを作成
            response_message = ChatMessage(
                id=assistant_message.id,
                role=assistant_message.role,
                content=assistant_message.content,
                timestamp=assistant_message.created_at,
                sources=assistant_message.sources
            )
            
            return ChatResponse(
                message=response_message,
                session_id=session.id,
                sources=sources
            )
            
        except Exception as e:
            logger.error(f"Chat processing error: {e}")
            # エラーメッセージを保存
            error_message = await self.chat_repo.add_message(
                session_id=session.id,
                role="assistant",
                content="申し訳ございません。エラーが発生しました。しばらくしてから再度お試しください。"
            )
            
            response_message = ChatMessage(
                id=error_message.id,
                role=error_message.role,
                content=error_message.content,
                timestamp=error_message.created_at
            )
            
            return ChatResponse(
                message=response_message,
                session_id=session.id
            )

    async def _generate_ai_response(
        self, 
        user_message: str, 
        relevant_docs: List[dict], 
        conversation_history: List[ChatMessageModel]
    ) -> Tuple[str, List[str]]:
        """OpenAI APIを使用してAI応答を生成"""
        
        # 関連文書をコンテキストとして整理
        context_chunks = []
        sources = []
        
        for doc in relevant_docs:
            context_chunks.append(f"【{doc['filename']}】\n{doc['content']}")
            if doc['filename'] not in sources:
                sources.append(doc['filename'])
        
        context = "\n\n".join(context_chunks) if context_chunks else "関連する文書が見つかりませんでした。"
        
        # 会話履歴を整理
        history_messages = []
        for msg in conversation_history:
            history_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # システムプロンプト
        system_prompt = f"""あなたは VectorMindStudio のAIアシスタントです。ユーザーがアップロードした文書の内容に基づいて質問に回答してください。

以下の関連文書を参考にして回答してください：

{context}

回答の際は以下のガイドラインに従ってください：
1. 関連文書の内容に基づいて正確に回答してください
2. 文書に記載されていない情報については推測せず、「文書には記載されていません」と伝えてください
3. 回答は親しみやすく、わかりやすい日本語で行ってください
4. 必要に応じて文書の該当箇所を引用してください
5. 質問に直接関連する情報がない場合は、その旨を正直に伝えてください"""

        # メッセージリストを構築
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history_messages)
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            return ai_response, sources
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise e

    def _generate_session_title(self, first_message: str) -> str:
        """最初のメッセージからセッションタイトルを生成"""
        if len(first_message) <= 30:
            return first_message
        else:
            return first_message[:27] + "..."

    async def get_user_sessions(self, user_id: str) -> List[dict]:
        """ユーザーのチャットセッション一覧を取得"""
        sessions = await self.chat_repo.get_user_sessions(user_id)
        
        result = []
        for session in sessions:
            message_count = await self.chat_repo.get_session_message_count(session.id)
            result.append({
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "message_count": message_count
            })
        
        return result

    async def get_session_history(self, session_id: str, user_id: str) -> List[ChatMessage]:
        """セッションの会話履歴を取得"""
        messages = await self.chat_repo.get_session_messages(session_id, user_id)
        
        return [
            ChatMessage(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.created_at,
                sources=msg.sources
            )
            for msg in messages
        ]

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """チャットセッションを削除"""
        return await self.chat_repo.delete_session(session_id, user_id)