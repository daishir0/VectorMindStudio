"""
Enhanced Base Agent - 簡易実装

analysis_agentとquality_agentの互換性のため
"""
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from .base_agent import BaseAgent, AgentTask, AgentResult, AgentStatus


@dataclass
class ExecutionMetrics:
    """実行メトリクス"""
    items_processed: int = 0
    items_successful: int = 0
    items_failed: int = 0
    total_tokens: int = 0
    api_calls: int = 0
    cache_hits: int = 0
    warnings: list = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items_processed": self.items_processed,
            "items_successful": self.items_successful,
            "items_failed": self.items_failed,
            "total_tokens": self.total_tokens,
            "api_calls": self.api_calls,
            "cache_hits": self.cache_hits,
            "warnings": self.warnings
        }


class EnhancedBaseAgent(BaseAgent):
    """
    拡張基底エージェント

    BaseAgentを継承し、メトリクス機能を追加
    """

    def __init__(
        self,
        name: str = "EnhancedAgent",
        description: str = "Enhanced agent with metrics",
        session: Optional[Any] = None,
        timeout: int = 90,
        max_retries: int = 3
    ):
        super().__init__(
            name=name,
            description=description,
            max_retries=max_retries,
            timeout=timeout
        )
        self.session = session

    async def _execute_core(self, task: AgentTask) -> Any:
        """
        コア実行ロジック（メトリクス付き）

        サブクラスで_execute_core(task, metrics)を実装する必要がある
        """
        metrics = ExecutionMetrics()

        # サブクラスの_execute_core(task, metrics)を呼び出し
        result = await self._execute_core_with_metrics(task, metrics)

        # メトリクスを結果に含める
        if isinstance(result, dict):
            result["metrics"] = metrics.to_dict()

        return result

    async def _execute_core_with_metrics(self, task: AgentTask, metrics: ExecutionMetrics) -> Any:
        """
        サブクラスで実装するメソッド

        このメソッドをオーバーライドする
        """
        raise NotImplementedError("サブクラスで_execute_core_with_metricsを実装してください")

    def _get_supported_task_types(self) -> list:
        """サポートするタスクタイプ（サブクラスでオーバーライド）"""
        return []


# 互換性のため、AgentTaskをエクスポート
__all__ = ['EnhancedBaseAgent', 'ExecutionMetrics', 'AgentTask']
