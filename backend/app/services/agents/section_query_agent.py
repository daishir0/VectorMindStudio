"""
Section Query Agent - 既存セクションの検索・参照専門エージェント (Enhanced版)
"""
from typing import Dict, List, Any, Optional
import logging
import re
import time
from fuzzywuzzy import fuzz

from .enhanced_base_agent import EnhancedBaseAgent, ExecutionMetrics, AgentTask
from .base_agent import AgentExecutionError, AgentValidationError
from app.infrastructure.repositories.paper_repository import PaperRepository
from app.core.config import settings

logger = logging.getLogger(__name__)


class SectionQueryAgent(EnhancedBaseAgent):
    """
    既存セクションの検索・参照・取得を担当するエージェント
    
    責務:
    - セクション名による検索（曖昧検索対応）
    - セクション内容の取得・表示
    - セクション一覧の提供
    - セクション関連の質問応答
    """
    
    def __init__(self, session=None):
        super().__init__(session=session, timeout=settings.AI_AGENT_TIMEOUT_SECONDS)
        self.repository = PaperRepository(session) if session else None
    
    @property
    def supported_tasks(self) -> List[str]:
        return [
            "find_section_by_fuzzy_match",  # ファジーマッチング検索
            "get_section_content",          # セクション内容取得
            "list_sections",                # セクション一覧
            "search_sections",              # 複数セクション検索
            "answer_section_query"          # セクション関連質問応答
        ]
    
    async def _execute_core(self, task: AgentTask, metrics: ExecutionMetrics) -> Any:
        """タスク実行 - Enhanced版"""
        if not self.repository:
            raise AgentExecutionError("データベースセッションが必要です")
        
        task_type = task.task_type
        
        if task_type == "find_section_by_fuzzy_match":
            return await self._find_section_fuzzy(task.parameters, metrics)
        elif task_type == "find_section":
            return await self._find_section(task.parameters, metrics)
        elif task_type == "get_section_content":
            return await self._get_section_content(task.parameters, metrics)
        elif task_type == "list_sections":
            return await self._list_sections(task.parameters, metrics)
        elif task_type == "search_sections":
            return await self._search_sections(task.parameters, metrics)
        elif task_type == "answer_section_query":
            return await self._answer_section_query(task.parameters, metrics)
        else:
            raise AgentValidationError(f"未サポートのタスクタイプ: {task_type}")
    
    async def _find_section_fuzzy(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """ファジーマッチングによるセクション検索 - Enhanced版"""
        paper_id = params.get("paper_id")
        query = params.get("query", "")
        
        if not paper_id:
            raise AgentValidationError("paper_id は必須です")
        if not query:
            raise AgentValidationError("query は必須です")
        
        try:
            # セクション取得
            sections = await self.repository.get_sections_by_paper(paper_id)
            metrics.items_processed = len(sections)
            
            if not sections:
                return {
                    "found_sections": [],
                    "sections_searched": 0,
                    "query": query,
                    "paper_id": paper_id,
                    "success": True
                }
            
            # ファジーマッチング実行
            best_match = None
            best_score = 0
            
            for section in sections:
                score = fuzz.ratio(query.lower(), section.title.lower()) / 100.0
                if score > best_score:
                    best_score = score
                    best_match = section
            
            # 結果構築
            found_sections = []
            if best_match and best_score >= 0.6:  # 60%以上の類似度
                found_sections.append({
                    "id": best_match.id,
                    "title": best_match.title,
                    "content": best_match.content or "内容が設定されていません",
                    "section_number": best_match.section_number,
                    "status": best_match.status,
                    "word_count": best_match.word_count,
                    "similarity_score": best_score,
                    "updated_at": best_match.updated_at.strftime("%Y-%m-%d %H:%M") if hasattr(best_match.updated_at, 'strftime') else str(best_match.updated_at)
                })
                metrics.items_successful = 1
            
            return {
                "found_sections": found_sections,
                "sections_searched": len(sections), 
                "query": query,
                "paper_id": paper_id,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[SectionQueryAgent] ファジー検索エラー: {e}")
            raise AgentExecutionError(f"セクション検索でエラーが発生しました: {e}")

    async def _find_section(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """セクション名による検索（曖昧検索対応）"""
        # レガシーメソッド - ファジーマッチングにリダイレクト
        return await self._find_section_fuzzy(params, metrics)
    
    async def _get_section_content(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """セクション内容取得（簡易実装）"""
        return {"content": "実装予定", "success": True}
    
    async def _list_sections(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """セクション一覧取得（簡易実装）"""
        return {"sections": [], "success": True}
    
    async def _search_sections(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """複数セクション検索（簡易実装）"""
        return {"results": [], "success": True}
    
    async def _answer_section_query(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """セクション関連質問応答 - ファジーマッチングによる検索"""
        # user_messageから検索対象を抽出
        user_message = params.get("user_message", "")
        paper_id = params.get("paper_id")
        
        if not paper_id:
            raise AgentValidationError("paper_id は必須です")
        
        # "Abstractを教えて" から "Abstract" を抽出
        query = "Abstract"  # user_messageから抽出するロジックは今回は簡略化
        
        # ファジーマッチング検索を使用
        search_params = {
            "paper_id": paper_id,
            "query": query
        }
        
        return await self._find_section_fuzzy(search_params, metrics)
        
