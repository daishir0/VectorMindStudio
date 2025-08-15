import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import logging
import os
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

class ChromaDBClient:
    """ChromaDBの接続と操作を管理するクライアント"""
    def __init__(self):
        self.host = settings.CHROMA_HOST
        self.port = settings.CHROMA_PORT
        self.collection_name = settings.CHROMA_COLLECTION_NAME
        self._client: chromadb.ClientAPI = None
        self._collection: chromadb.Collection = None
        self._embedding_function = None

    async def connect(self):
        """データベースに接続し、コレクションを準備する"""
        if self._client:
            logger.info("ChromaDB client already connected.")
            return

        try:
            self._client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(anonymized_telemetry=False, allow_reset=True)
            )
            # クライアントが実際に接続可能か確認
            self._client.heartbeat()

            self._embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.EMBEDDING_MODEL
            )

            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._embedding_function,
                metadata={"hnsw:space": "cosine"} # 類似度計算の戦略
            )
            logger.info(f"Successfully connected to ChromaDB at {self.host}:{self.port} and got collection '{self.collection_name}'.")

        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            self._client = None
            raise ConnectionError(f"ChromaDB connection failed: {e}")

    async def disconnect(self):
        """データベースから切断する"""
        # HttpClientには明示的なdisconnectメソッドがないため、参照をクリア
        self._client = None
        self._collection = None
        logger.info("ChromaDB client disconnected.")

    @property
    def collection(self) -> chromadb.Collection:
        if not self._collection:
            raise RuntimeError("ChromaDB is not connected. Call connect() first.")
        return self._collection

# シングルトンインスタンス
chroma_client = ChromaDBClient()
