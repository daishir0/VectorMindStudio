import openai
from typing import Dict, Any, Optional
import asyncio
import time

from app.core.config import settings


class OpenAIClient:
    """OpenAI APIクライアント"""
    
    def __init__(self):
        self.client = None
    
    def _ensure_client(self):
        """クライアントの遅延初期化"""
        if self.client is None:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key is not configured")
            
            openai.api_key = settings.OPENAI_API_KEY
            self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_text(
        self, 
        prompt: str, 
        variables: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """テキスト生成"""
        
        self._ensure_client()
        start_time = time.time()
        
        # 変数を置換
        if variables:
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                prompt = prompt.replace(placeholder, str(value))
        
        try:
            response = await self.client.chat.completions.create(
                model=model or settings.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            generation_time = int((time.time() - start_time) * 1000)  # ミリ秒
            
            return {
                "content": response.choices[0].message.content,
                "model": model or settings.OPENAI_MODEL,
                "generation_time_ms": generation_time,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def create_embedding(self, text: str) -> list[float]:
        """テキストの埋め込みベクトルを生成"""
        
        self._ensure_client()
        try:
            response = await self.client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            raise Exception(f"OpenAI Embedding API error: {str(e)}")

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """複数のテキストの埋め込みベクトルを生成"""
        
        self._ensure_client()
        try:
            response = await self.client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=texts
            )
            
            return [d.embedding for d in response.data]
            
        except Exception as e:
            raise Exception(f"OpenAI Embedding API error: {str(e)}")


# シングルトンインスタンス
openai_client = OpenAIClient()