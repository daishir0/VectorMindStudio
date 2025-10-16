"""
LangGraphエージェント管理のスキーマ定義
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ===== Agent Schemas =====

class LangGraphAgentBase(BaseModel):
    """エージェント基底スキーマ"""
    name: str = Field(..., description="エージェント名")
    display_name: str = Field(..., description="表示名")
    description: Optional[str] = Field(None, description="説明")
    class_path: str = Field(..., description="Pythonクラスパス")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="設定")
    is_active: bool = Field(True, description="有効/無効フラグ")


class LangGraphAgentCreate(LangGraphAgentBase):
    """エージェント作成リクエスト"""
    pass


class LangGraphAgentUpdate(BaseModel):
    """エージェント更新リクエスト"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    class_path: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class LangGraphAgentDetail(LangGraphAgentBase):
    """エージェント詳細"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Intent Schemas =====

class LangGraphIntentBase(BaseModel):
    """インテント基底スキーマ"""
    intent_name: str = Field(..., description="インテント名")
    display_name: str = Field(..., description="表示名")
    description: Optional[str] = Field(None, description="説明")
    agent_id: str = Field(..., description="担当エージェントID")
    parameters_schema: Optional[Dict[str, Any]] = Field(default_factory=dict, description="パラメータスキーマ")
    example_query: Optional[str] = Field(None, description="例文")
    is_active: bool = Field(True, description="有効/無効フラグ")


class LangGraphIntentCreate(LangGraphIntentBase):
    """インテント作成リクエスト"""
    pass


class LangGraphIntentDetail(LangGraphIntentBase):
    """インテント詳細"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LangGraphIntentWithAgent(LangGraphIntentDetail):
    """エージェント情報付きインテント"""
    agent_name: str
    agent_display_name: str


# ===== Chain Intent Schemas =====

class LangGraphChainIntentBase(BaseModel):
    """チェーンインテント基底スキーマ"""
    chain_name: str = Field(..., description="チェーン名")
    display_name: str = Field(..., description="表示名")
    description: Optional[str] = Field(None, description="説明")
    task_sequence: List[str] = Field(..., description="タスク順序")
    example_query: Optional[str] = Field(None, description="例文")
    is_active: bool = Field(True, description="有効/無効フラグ")


class LangGraphChainIntentCreate(LangGraphChainIntentBase):
    """チェーンインテント作成リクエスト"""
    pass


class LangGraphChainIntentDetail(LangGraphChainIntentBase):
    """チェーンインテント詳細"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Execution Log Schemas =====

class LangGraphExecutionLogSummary(BaseModel):
    """実行ログサマリー"""
    id: str
    session_id: str
    user_id: str
    paper_id: str
    user_query: str
    intent: Optional[str]
    agents_used: Optional[List[str]]
    execution_time_ms: Optional[int]
    validation_result: Optional[str]
    error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LangGraphExecutionStatsResponse(BaseModel):
    """実行統計レスポンス"""
    total_executions: int
    avg_execution_time_ms: float
    error_count: int
    success_rate: float
    intent_distribution: Dict[str, int]


# ===== Response Wrapper =====

class AgentListResponse(BaseModel):
    """エージェント一覧レスポンス"""
    agents: List[LangGraphAgentDetail]
    total: int


class IntentListResponse(BaseModel):
    """インテント一覧レスポンス"""
    intents: List[LangGraphIntentWithAgent]
    total: int


class ChainIntentListResponse(BaseModel):
    """チェーンインテント一覧レスポンス"""
    chain_intents: List[LangGraphChainIntentDetail]
    total: int
