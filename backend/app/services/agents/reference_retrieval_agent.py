"""
参考資料検索エージェント - Reference Retrieval Agent

アップロードされた資料からベクトル検索で関連情報を取得
"""
from typing import Any, Dict, List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from .base_agent import BaseAgent, AgentTask, AgentValidationError, AgentExecutionError
from app.services.vector_service import VectorService
from app.infrastructure.repositories.file_repository import FileRepository

logger = logging.getLogger(__name__)


class ReferenceRetrievalAgent(BaseAgent):
    """
    参考資料検索エージェント

    実装パターン: Knowledge Retrieval Node
    責務: アップロードされた資料から関連情報をベクトル検索で取得

    機能:
    1. ユーザークエリに基づいてベクトル検索
    2. アップロードファイル全体とチャンクの両方から検索
    3. 関連度スコアによるランキング
    4. タグフィルタリング対応
    """

    def __init__(self, session: AsyncSession):
        super().__init__(
            name="ReferenceRetrievalAgent",
            description="アップロード資料から関連情報をベクトル検索で取得するエージェント",
            max_retries=2,
            timeout=30
        )
        self.session = session
        self.vector_service = VectorService()
        self.file_repository = FileRepository(session)

    def _get_supported_task_types(self) -> List[str]:
        return [
            "search_references",
            "find_similar_content",
            "retrieve_by_tags",
            "get_file_chunks"
        ]

    async def _execute_core(self, task: AgentTask) -> Any:
        """コア実行ロジック"""
        task_type = task.task_type
        parameters = task.parameters

        if task_type == "search_references":
            return await self._search_references(parameters)
        elif task_type == "find_similar_content":
            return await self._find_similar_content(parameters)
        elif task_type == "retrieve_by_tags":
            return await self._retrieve_by_tags(parameters)
        elif task_type == "get_file_chunks":
            return await self._get_file_chunks(parameters)
        else:
            raise AgentValidationError(f"未サポートのタスクタイプ: {task_type}")

    async def _search_references(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        参考資料検索（メイン機能）

        ユーザーの検索クエリに基づいて、以下の2つのソースから情報を取得:
        1. アップロードファイル全体のメタデータ検索
        2. ベクトル化されたチャンクからの類似度検索
        """
        query = params.get("query")
        user_id = params.get("user_id")
        limit = params.get("limit", 5)
        tags = params.get("tags")  # Optional: タグフィルタ

        if not query or not user_id:
            raise AgentValidationError("query と user_id は必須です")

        try:
            logger.info(f"[ReferenceRetrievalAgent] 参考資料検索開始: '{query[:50]}...'")

            # ソース1: ベクトル検索でチャンクレベルの類似コンテンツを取得
            vector_results = await self.vector_service.search_similar_content(
                query=query,
                user_id=user_id,
                limit=limit,
                tags=tags
            )

            # ソース2: ファイルメタデータからファイル全体を取得
            # ベクトル検索で見つかったファイルIDを抽出
            file_ids = list(set([r["upload_id"] for r in vector_results if r.get("upload_id")]))

            file_metadata = []
            for file_id in file_ids[:limit]:
                file_info = await self.file_repository.get_upload_by_id(file_id)
                if file_info:
                    file_metadata.append({
                        "file_id": file_info.id,
                        "filename": file_info.filename,
                        "content_type": file_info.content_type,
                        "size_bytes": file_info.size_bytes,
                        "original_path": file_info.original_path,
                        "converted_path": file_info.converted_path,
                        "tags": file_info.tags or [],
                        "created_at": file_info.created_at.isoformat(),
                        "status": file_info.status
                    })

            # 結果を統合
            logger.info(f"[ReferenceRetrievalAgent] 検索完了: チャンク{len(vector_results)}件, ファイル{len(file_metadata)}件")

            return {
                "query": query,
                "chunks_found": len(vector_results),
                "files_found": len(file_metadata),
                "chunk_results": [
                    {
                        "content": r["content"][:500] + "..." if len(r["content"]) > 500 else r["content"],
                        "filename": r["filename"],
                        "chunk_number": r["chunk_number"],
                        "relevance_score": round(r["relevance_score"], 3),
                        "tags": r["tags"]
                    }
                    for r in vector_results
                ],
                "file_metadata": file_metadata,
                "search_summary": self._generate_search_summary(query, vector_results, file_metadata),
                "action": "search_references",
                "success": True
            }

        except Exception as e:
            logger.error(f"[ReferenceRetrievalAgent] 参考資料検索エラー: {e}")
            raise AgentExecutionError(f"参考資料検索に失敗しました: {e}")

    async def _find_similar_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """類似コンテンツ検索（チャンクのみ）"""
        query = params.get("query")
        user_id = params.get("user_id")
        limit = params.get("limit", 10)

        if not query or not user_id:
            raise AgentValidationError("query と user_id は必須です")

        try:
            results = await self.vector_service.search_similar_content(
                query=query,
                user_id=user_id,
                limit=limit
            )

            return {
                "query": query,
                "results_count": len(results),
                "similar_chunks": [
                    {
                        "content": r["content"],
                        "filename": r["filename"],
                        "chunk_number": r["chunk_number"],
                        "relevance_score": round(r["relevance_score"], 3)
                    }
                    for r in results
                ],
                "action": "find_similar_content",
                "success": True
            }

        except Exception as e:
            logger.error(f"[ReferenceRetrievalAgent] 類似コンテンツ検索エラー: {e}")
            raise AgentExecutionError(f"類似コンテンツ検索に失敗しました: {e}")

    async def _retrieve_by_tags(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """タグベースで資料を検索"""
        tags = params.get("tags", [])
        user_id = params.get("user_id")
        query = params.get("query", "")

        if not user_id:
            raise AgentValidationError("user_id は必須です")

        if not tags:
            raise AgentValidationError("tags は必須です（1つ以上）")

        try:
            # タグフィルタ付きでベクトル検索
            results = await self.vector_service.search_similar_content(
                query=query or "関連する資料を探す",  # クエリがない場合はデフォルト
                user_id=user_id,
                limit=10,
                tags=tags
            )

            return {
                "tags": tags,
                "results_count": len(results),
                "filtered_chunks": [
                    {
                        "content": r["content"][:300] + "..." if len(r["content"]) > 300 else r["content"],
                        "filename": r["filename"],
                        "chunk_number": r["chunk_number"],
                        "tags": r["tags"]
                    }
                    for r in results
                ],
                "action": "retrieve_by_tags",
                "success": True
            }

        except Exception as e:
            logger.error(f"[ReferenceRetrievalAgent] タグ検索エラー: {e}")
            raise AgentExecutionError(f"タグ検索に失敗しました: {e}")

    async def _get_file_chunks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """特定ファイルのチャンク一覧を取得"""
        file_id = params.get("file_id")
        user_id = params.get("user_id")

        if not file_id or not user_id:
            raise AgentValidationError("file_id と user_id は必須です")

        try:
            # ファイル情報取得
            file_info = await self.file_repository.get_upload_by_id(file_id)

            if not file_info:
                raise AgentValidationError(f"ファイル {file_id} が見つかりません")

            # ベクトルDBから該当ファイルのチャンクを検索
            # 簡易的にファイル名で検索
            results = await self.vector_service.search_similar_content(
                query=file_info.filename,
                user_id=user_id,
                limit=100  # 大きめの値でファイル全体のチャンクを取得
            )

            # 該当ファイルのチャンクのみフィルタ
            file_chunks = [r for r in results if r["upload_id"] == file_id]

            return {
                "file_id": file_id,
                "filename": file_info.filename,
                "chunks_count": len(file_chunks),
                "chunks": [
                    {
                        "chunk_number": c["chunk_number"],
                        "content": c["content"]
                    }
                    for c in sorted(file_chunks, key=lambda x: x["chunk_number"])
                ],
                "action": "get_file_chunks",
                "success": True
            }

        except Exception as e:
            logger.error(f"[ReferenceRetrievalAgent] ファイルチャンク取得エラー: {e}")
            raise AgentExecutionError(f"ファイルチャンク取得に失敗しました: {e}")

    def _generate_search_summary(
        self,
        query: str,
        chunk_results: List[Dict[str, Any]],
        file_metadata: List[Dict[str, Any]]
    ) -> str:
        """検索結果のサマリーを生成"""
        if not chunk_results and not file_metadata:
            return f"「{query}」に関連する資料は見つかりませんでした。"

        summary = f"「{query}」に関連する資料を{len(file_metadata)}ファイル、{len(chunk_results)}チャンク発見しました。\n\n"

        if file_metadata:
            summary += "【関連ファイル】\n"
            for i, file in enumerate(file_metadata[:3], 1):
                summary += f"{i}. {file['filename']}"
                if file['tags']:
                    summary += f" (タグ: {', '.join(file['tags'])})"
                summary += "\n"
            summary += "\n"

        if chunk_results:
            summary += "【最も関連性の高いチャンク】\n"
            top_chunk = chunk_results[0]
            summary += f"ファイル: {top_chunk['filename']}\n"
            summary += f"関連度: {top_chunk['relevance_score']:.1%}\n"
            summary += f"内容抜粋: {top_chunk['content'][:200]}...\n"

        return summary
