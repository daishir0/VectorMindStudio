"""
論文執筆AIエージェントパッケージ
"""
from .base_agent import BaseAgent, AgentTask, AgentResult, AgentStatus
from .outline_agent import OutlineAgent
from .summary_agent import SummaryAgent
from .writer_agent import WriterAgent
from .logic_validator_agent import LogicValidatorAgent
from .reference_agent import ReferenceAgent

__all__ = [
    "BaseAgent",
    "AgentTask", 
    "AgentResult",
    "AgentStatus",
    "OutlineAgent",
    "SummaryAgent", 
    "WriterAgent",
    "LogicValidatorAgent",
    "ReferenceAgent"
]