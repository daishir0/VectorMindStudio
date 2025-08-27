"""
論文執筆AIエージェントの基底クラス
ReadyTensor Agentic AI ベストプラクティスに基づく実装
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import logging
import time
import uuid
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """エージェント実行状態"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentResult:
    """エージェント実行結果"""
    agent_name: str
    status: AgentStatus
    result: Any
    execution_time: float
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


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


class BaseAgent(ABC):
    """
    論文執筆AIエージェントの基底クラス
    
    アンチパターン対策:
    - エスケープハッチ: タイムアウト設定
    - エラー処理: グレースフルデグラデーション
    - 責任境界明確化: 単一責任原則
    """
    
    def __init__(
        self, 
        name: str, 
        description: str,
        max_retries: int = 3,
        timeout: int = 30
    ):
        self.name = name
        self.description = description
        self.max_retries = max_retries
        self.timeout = timeout
        self.status = AgentStatus.PENDING
        self.current_task: Optional[AgentTask] = None
        
    async def execute_task(self, task: AgentTask) -> AgentResult:
        """
        タスクを実行する（エラーハンドリング・リトライ機能付き）
        
        Args:
            task: 実行タスク
            
        Returns:
            AgentResult: 実行結果
        """
        self.current_task = task
        self.status = AgentStatus.IN_PROGRESS
        start_time = time.time()
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                logger.info(f"{self.name}: タスク実行開始 (試行 {retry_count + 1}/{self.max_retries + 1})")
                
                # タイムアウト制御
                result = await self._execute_with_timeout(task)
                
                execution_time = time.time() - start_time
                self.status = AgentStatus.COMPLETED
                
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.COMPLETED,
                    result=result,
                    execution_time=execution_time,
                    metadata={
                        "retry_count": retry_count,
                        "task_id": task.id
                    }
                )
                
            except TimeoutError as e:
                execution_time = time.time() - start_time
                logger.error(f"{self.name}: タスクタイムアウト ({execution_time:.2f}秒)")
                self.status = AgentStatus.TIMEOUT
                
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.TIMEOUT,
                    result=None,
                    execution_time=execution_time,
                    error_message=f"タスクがタイムアウトしました ({self.timeout}秒)",
                    metadata={"retry_count": retry_count, "task_id": task.id}
                )
                
            except Exception as e:
                retry_count += 1
                last_error = e
                logger.warning(f"{self.name}: タスク実行失敗 (試行 {retry_count}): {e}")
                
                if retry_count <= self.max_retries:
                    # 指数バックオフでリトライ
                    wait_time = min(2 ** retry_count, 10)
                    await self._wait(wait_time)
                
        # 全リトライ失敗
        execution_time = time.time() - start_time
        self.status = AgentStatus.FAILED
        
        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.FAILED,
            result=None,
            execution_time=execution_time,
            error_message=f"最大リトライ回数に達しました: {last_error}",
            metadata={"retry_count": retry_count - 1, "task_id": task.id}
        )
    
    async def _execute_with_timeout(self, task: AgentTask) -> Any:
        """タイムアウト付きでタスクを実行"""
        import asyncio
        
        try:
            return await asyncio.wait_for(
                self._execute_core(task),
                timeout=task.timeout or self.timeout
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"タスクが{self.timeout}秒でタイムアウトしました")
    
    @abstractmethod
    async def _execute_core(self, task: AgentTask) -> Any:
        """
        コア実行ロジック（サブクラスで実装）
        
        Args:
            task: 実行タスク
            
        Returns:
            実行結果
        """
        pass
    
    async def _wait(self, seconds: float) -> None:
        """非同期待機"""
        import asyncio
        await asyncio.sleep(seconds)
    
    def create_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        priority: int = 1,
        timeout: Optional[int] = None
    ) -> AgentTask:
        """タスクを作成"""
        return AgentTask(
            id=str(uuid.uuid4()),
            task_type=task_type,
            parameters=parameters,
            context=context,
            priority=priority,
            timeout=timeout or self.timeout
        )
    
    def get_capabilities(self) -> Dict[str, Any]:
        """エージェントの能力を返す"""
        return {
            "name": self.name,
            "description": self.description,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "status": self.status.value,
            "supported_task_types": self._get_supported_task_types()
        }
    
    @abstractmethod
    def _get_supported_task_types(self) -> List[str]:
        """サポートするタスクタイプのリスト"""
        pass


class AgentError(Exception):
    """エージェント固有のエラー"""
    pass


class AgentValidationError(AgentError):
    """エージェント入力検証エラー"""
    pass


class AgentExecutionError(AgentError):
    """エージェント実行エラー"""
    pass