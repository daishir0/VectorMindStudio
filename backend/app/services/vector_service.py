import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid

from app.infrastructure.external.chroma_client import chroma_client
from app.infrastructure.external.openai_client import openai_client
from app.infrastructure.database.models import UploadModel

logger = logging.getLogger(__name__)

class VectorService:
    """ベクトル化とChromaDBへの保存・検索を管理するサービス"""

    def __init__(self):
        self.chunk_size = 1000  # チャンクの文字数
        self.chunk_overlap = 200 # チャンク間のオーバーラップ

    def _chunk_text(self, text: str) -> List[str]:
        """テキストをチャンクに分割する"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start += self.chunk_size - self.chunk_overlap
        return chunks

    async def create_embeddings_for_upload(self, upload: UploadModel):
        """アップロードされたファイルの埋め込みを作成し、ChromaDBに保存する"""
        logger.info(f"Vector service received upload: {upload.id}, converted_path: {upload.converted_path}")
        
        if not upload.converted_path or not Path(upload.converted_path).exists():
            logger.error(f"Converted file not found - path: {upload.converted_path}, exists: {Path(upload.converted_path).exists() if upload.converted_path else 'None'}")
            raise ValueError(f"Converted file not found for upload id {upload.id}")

        logger.info(f"Starting embedding creation for: {upload.filename}")

        with open(upload.converted_path, 'r', encoding='utf-8') as f:
            content = f.read()

        chunks = self._chunk_text(content)
        if not chunks:
            logger.warning(f"No text chunks to process for file: {upload.filename}")
            return

        try:
            embeddings = await openai_client.get_embeddings(chunks)
        except Exception as e:
            logger.error(f"Failed to get embeddings from OpenAI for {upload.id}: {e}")
            raise

        collection = chroma_client.collection
        ids = [f"{upload.id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "upload_id": upload.id,
                "user_id": upload.user_id,
                "filename": upload.filename,
                "chunk_number": i,
                "chunk_size": len(chunk),
                "tags": ','.join(upload.tags or [])  # タグをカンマ区切り文字列として保存
            }
            for i, chunk in enumerate(chunks)
        ]

        try:
            collection.add(
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Successfully added {len(chunks)} chunks to ChromaDB for file {upload.id}")
        except Exception as e:
            logger.error(f"Failed to add embeddings to ChromaDB for {upload.id}: {e}")
            raise

    async def search_similar(
        self, query: str, user_id: str, limit: int = 10, tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """類似ドキュメントを検索する"""
        try:
            query_embedding = await openai_client.get_embeddings([query])
            if not query_embedding:
                return []

            collection = chroma_client.collection
            
            # whereクエリの構築
            where_conditions = [{"user_id": user_id}]
            if tags:
                # タグフィルタを追加（完全一致）
                # 単一タグの場合は完全一致、複数タグの場合はOR条件
                if len(tags) == 1:
                    where_conditions.append({"tags": {"$eq": tags[0]}})
                else:
                    tag_conditions = [{"tags": {"$eq": tag}} for tag in tags]
                    where_conditions.append({"$or": tag_conditions})
            
            # 条件が複数ある場合は$andで結合
            if len(where_conditions) == 1:
                where_clause = where_conditions[0]
            else:
                where_clause = {"$and": where_conditions}
            
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=limit,
                where=where_clause
            )

            formatted_results = []
            if not results['ids'] or not results['ids'][0]:
                return []

            for i, doc_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                # タグを文字列からリストに変換
                tags_str = metadata.get('tags', '')
                tags_list = tags_str.split(',') if tags_str else []
                
                formatted_results.append({
                    "id": doc_id,
                    "document": results['documents'][0][i],
                    "metadata": metadata,
                    "distance": results['distances'][0][i],
                    "relevance_score": 1 - results['distances'][0][i],
                    "tags": tags_list,
                    "filename": metadata.get('filename'),
                    "upload_id": metadata.get('upload_id')
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Similarity search failed for user {user_id}: {e}")
            raise

    async def delete_vectors_by_upload_id(self, upload_id: str):
        """ファイルIDに基づいてベクターデータを削除する"""
        try:
            collection = chroma_client.collection
            
            # まずそのupload_idに関連するIDを取得
            results = collection.get(
                where={"upload_id": upload_id}
            )
            
            if not results['ids']:
                logger.info(f"No vectors found for upload_id {upload_id}")
                return
            
            # 関連するベクターデータをすべて削除
            collection.delete(
                where={"upload_id": upload_id}
            )
            
            logger.info(f"Successfully deleted {len(results['ids'])} vectors for upload_id {upload_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete vectors for upload_id {upload_id}: {e}")
            raise

    async def search_similar_content(
        self, query: str, user_id: str, limit: int = 5, tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """チャット用の類似コンテンツ検索（ファイル名と内容を含む）"""
        try:
            query_embedding = await openai_client.get_embeddings([query])
            if not query_embedding:
                return []

            collection = chroma_client.collection
            
            # whereクエリの構築
            where_conditions = [{"user_id": user_id}]
            if tags:
                # タグフィルタを追加（完全一致）
                # 単一タグの場合は完全一致、複数タグの場合はOR条件
                if len(tags) == 1:
                    where_conditions.append({"tags": {"$eq": tags[0]}})
                else:
                    tag_conditions = [{"tags": {"$eq": tag}} for tag in tags]
                    where_conditions.append({"$or": tag_conditions})
            
            # 条件が複数ある場合は$andで結合
            if len(where_conditions) == 1:
                where_clause = where_conditions[0]
            else:
                where_clause = {"$and": where_conditions}
            
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=limit,
                where=where_clause
            )

            formatted_results = []
            if not results['ids'] or not results['ids'][0]:
                return []

            for i, doc_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                # タグを文字列からリストに変換
                tags_str = metadata.get('tags', '')
                tags_list = tags_str.split(',') if tags_str else []
                
                formatted_results.append({
                    "id": doc_id,
                    "content": results['documents'][0][i],
                    "filename": metadata.get('filename', 'unknown'),
                    "upload_id": metadata.get('upload_id'),
                    "chunk_number": metadata.get('chunk_number', 0),
                    "tags": tags_list,
                    "distance": results['distances'][0][i],
                    "relevance_score": 1 - results['distances'][0][i]
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Similar content search failed for user {user_id}: {e}")
            raise

    async def update_file_tags(self, upload_id: str, tags: List[str]):
        """ファイルに関連する全埋め込みのタグを更新する"""
        try:
            collection = chroma_client.collection
            
            # upload_idに関連する全ての埋め込みを取得
            results = collection.get(
                where={"upload_id": upload_id}
            )
            
            if not results['ids']:
                logger.info(f"No vectors found for upload_id {upload_id}")
                return
            
            # 既存のメタデータを取得してタグのみ更新
            updated_metadatas = []
            for metadata in results['metadatas']:
                updated_metadata = metadata.copy()
                # タグをカンマ区切りの文字列として保存（ChromaDBの制約のため）
                updated_metadata['tags'] = ','.join(tags) if tags else ''
                updated_metadatas.append(updated_metadata)
            
            # メタデータを一括更新
            collection.update(
                ids=results['ids'],
                metadatas=updated_metadatas
            )
            
            logger.info(f"Successfully updated tags for {len(results['ids'])} vectors for upload_id {upload_id}")
            
        except Exception as e:
            logger.error(f"Failed to update tags for upload_id {upload_id}: {e}")
            raise
