"""
論文執筆AIエージェントパッケージ（LangGraph専用）

このパッケージはLangGraphワークフローで使用される7つの専門エージェントを提供します。
"""
from .base_agent import BaseAgent, AgentTask, AgentResult, AgentStatus
from .outline_agent import OutlineAgent
from .writer_agent import WriterAgent
from .analysis_agent import AnalysisAgent
from .discovery_agent import DiscoveryAgent
from .quality_agent import QualityAgent
from .strategy_agent import StrategyAgent
from .reference_retrieval_agent import ReferenceRetrievalAgent

__all__ = [
    # 基底クラス
    "BaseAgent",
    "AgentTask",
    "AgentResult",
    "AgentStatus",

    # LangGraph専門エージェント（7種）
    "OutlineAgent",           # アウトライン管理
    "WriterAgent",            # コンテンツ生成
    "AnalysisAgent",          # 批判的分析
    "DiscoveryAgent",         # 知識発見
    "QualityAgent",           # 品質保証
    "StrategyAgent",          # 戦略立案
    "ReferenceRetrievalAgent", # 参考文献
]
