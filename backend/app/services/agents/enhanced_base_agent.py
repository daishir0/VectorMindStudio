"""
拡張されたBaseAgent - 統一メッセージングシステム対応版
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from enum import Enum

from .agent_messaging import (
    AgentMessagingFactory, 
    ExecutionMetrics, 
    AgentMessage,
    MessageType,
    TaskStatus
)

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """エージェント実行ステータス"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentTask:
    """エージェントタスク定義"""
    id: str
    task_type: str
    parameters: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    priority: int = 1
    timeout: int = 30  # 秒
    status: AgentStatus = AgentStatus.PENDING

@dataclass 
class AgentResult:
    """エージェント実行結果"""
    task_id: str
    status: AgentStatus
    result: Any
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    pre_message: Optional[AgentMessage] = None   # 実行前メッセージ
    post_message: Optional[AgentMessage] = None  # 実行後メッセージ

class EnhancedBaseAgent(ABC):
    """統一メッセージングシステム対応のベースエージェント"""
    
    def __init__(self, session = None, timeout: int = 30):
        self.session = session
        self.timeout = timeout
        self.agent_name = self.__class__.__name__
        
        # メッセージングシステム初期化
        self.messaging = AgentMessagingFactory.create_messaging(self.agent_name)
        
        logger.info(f"[{self.agent_name}] エージェント初期化完了")
    
    @property
    @abstractmethod
    def supported_tasks(self) -> List[str]:
        """サポートするタスクタイプ一覧"""
        pass
    
    async def execute_task(self, task: AgentTask) -> AgentResult:
        """
        統一メッセージングでタスクを実行
        1. 実行前メッセージ作成・送信
        2. 実際のタスク実行
        3. 実行後メッセージ作成・送信
        """
        logger.info(f"[{self.agent_name}] タスク実行開始: {task.task_type}")
        
        # メトリクス初期化
        metrics = ExecutionMetrics()
        
        # 1. 実行前メッセージ作成
        pre_message = self.messaging.create_pre_execution_message(task.parameters)
        logger.info(f"[{self.agent_name}] 実行前メッセージ: {pre_message.title}")
        
        try:
            # 2. 実際のコア処理実行
            task.status = AgentStatus.RUNNING
            result = await self._execute_with_timeout(task, metrics)
            
            # 成功時の処理
            task.status = AgentStatus.COMPLETED
            metrics.items_successful = metrics.items_processed
            metrics.complete()
            
            # 3. 実行後メッセージ作成（成功）
            task_result = {"success": True, **result} if isinstance(result, dict) else {"success": True, "result": result}
            post_message = self.messaging.create_post_execution_message(task_result, metrics)
            
            logger.info(f"[{self.agent_name}] タスク実行成功: {task.task_type}")
            
            return AgentResult(
                task_id=task.id,
                status=AgentStatus.COMPLETED,
                result=result,
                pre_message=pre_message,
                post_message=post_message,
                metadata={
                    "execution_time": metrics.execution_time,
                    "items_processed": metrics.items_processed,
                    "success_rate": metrics.success_rate
                }
            )
            
        except Exception as e:
            # 失敗時の処理
            task.status = AgentStatus.FAILED
            metrics.complete()
            
            # エラーメッセージ作成
            error_message = self.messaging.create_error_message(e, {"task": task.task_type})
            
            logger.error(f"[{self.agent_name}] タスク実行失敗: {e}")
            
            return AgentResult(
                task_id=task.id,
                status=AgentStatus.FAILED,
                result=None,
                error_message=str(e),
                pre_message=pre_message,
                post_message=error_message
            )
    
    async def _execute_with_timeout(self, task: AgentTask, metrics: ExecutionMetrics) -> Any:
        """タイムアウト付きでコア処理を実行"""
        try:
            return await asyncio.wait_for(
                self._execute_core(task, metrics),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"タスクが{self.timeout}秒でタイムアウトしました")
    
    @abstractmethod
    async def _execute_core(self, task: AgentTask, metrics: ExecutionMetrics) -> Any:
        """
        コア実行ロジック（サブクラスで実装）
        
        Args:
            task: 実行するタスク
            metrics: 実行メトリクス（更新可能）
        
        Returns:
            実行結果（辞書形式推奨）
        """
        pass
    
    def create_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        priority: int = 1,
        timeout: Optional[int] = None
    ) -> AgentTask:
        """タスクを作成"""
        if task_type not in self.supported_tasks:
            raise ValueError(f"サポートされていないタスクタイプ: {task_type}")
        
        return AgentTask(
            id=str(uuid.uuid4()),
            task_type=task_type,
            parameters=parameters,
            context=context or {},
            priority=priority,
            timeout=timeout or self.timeout
        )

# =====================================================
# 使用例：既存エージェントの拡張版
# =====================================================

class EnhancedSectionQueryAgent(EnhancedBaseAgent):
    """拡張版セクション検索エージェント"""
    
    def __init__(self, session, timeout: int = 30):
        super().__init__(session, timeout)
        self.repository = None
        if session:
            from app.infrastructure.repositories.paper_repository import PaperRepository
            self.repository = PaperRepository(session)
    
    @property
    def supported_tasks(self) -> List[str]:
        return [
            "find_section_by_fuzzy_match",
            "list_sections", 
            "search_sections",
            "answer_section_query"
        ]
    
    async def _execute_core(self, task: AgentTask, metrics: ExecutionMetrics) -> Any:
        """セクション検索のコア処理"""
        task_type = task.parameters.get("task_type")
        
        if task_type == "find_section_by_fuzzy_match":
            return await self._find_section_fuzzy(task, metrics)
        else:
            raise ValueError(f"未対応のタスクタイプ: {task_type}")
    
    async def _find_section_fuzzy(self, task: AgentTask, metrics: ExecutionMetrics) -> Dict[str, Any]:
        """ファジーマッチングによるセクション検索"""
        if not self.repository:
            raise RuntimeError("データベースセッションが必要です")
        
        # パラメータ取得
        paper_id = task.parameters.get("paper_id")
        query = task.parameters.get("query", "")
        
        # セクション取得
        sections = await self.repository.get_sections_by_paper(paper_id)
        metrics.items_processed = len(sections)
        
        if not sections:
            return {
                "found_sections": [],
                "sections_searched": 0,
                "query": query,
                "success": True
            }
        
        # ファジーマッチング実行
        from fuzzywuzzy import fuzz
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
                "word_count": best_match.word_count,
                "similarity_score": best_score,
                "updated_at": best_match.updated_at.strftime("%Y-%m-%d %H:%M")
            })
            metrics.items_successful = 1
        
        return {
            "found_sections": found_sections,
            "sections_searched": len(sections), 
            "query": query,
            "success": True
        }