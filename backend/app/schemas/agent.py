from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ========== Enums ==========

class AgentCategory(str, Enum):
    """エージェントカテゴリ"""
    SEARCH = "search"
    ANALYSIS = "analysis"
    WRITING = "writing"
    QUALITY = "quality"
    CUSTOM = "custom"


class ExecutorType(str, Enum):
    """エージェント実行タイプ"""
    CODE_BASED = "code_based"  # Pythonクラスベース（既存14エージェント）
    LLM_BASED = "llm_based"    # LLMベース（カスタムエージェント）


class ResponseFormat(str, Enum):
    """レスポンスフォーマット"""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


class WakeWordMatchType(str, Enum):
    """ウェイクワードマッチタイプ"""
    EXACT = "exact"        # 完全一致
    SEMANTIC = "semantic"  # 意味的類似性
    REGEX = "regex"        # 正規表現


class PaperType(str, Enum):
    """論文タイプ"""
    MEDICAL = "medical"
    ENGINEERING = "engineering"
    HUMANITIES = "humanities"
    GENERAL = "general"


class ExecutionStatus(str, Enum):
    """実行ステータス"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


# ========== Wake Word Schemas ==========

class WakeWordBase(BaseModel):
    """ウェイクワード基本スキーマ"""
    keyword: str = Field(..., min_length=1, max_length=200, description="ウェイクワードキーワード")
    match_type: WakeWordMatchType = Field(WakeWordMatchType.SEMANTIC, description="マッチタイプ")
    priority: int = Field(10, ge=1, le=100, description="優先度（1-100）")


class WakeWordCreate(WakeWordBase):
    """ウェイクワード作成スキーマ"""
    pass


class WakeWordUpdate(BaseModel):
    """ウェイクワード更新スキーマ"""
    keyword: Optional[str] = Field(None, min_length=1, max_length=200)
    match_type: Optional[WakeWordMatchType] = None
    priority: Optional[int] = Field(None, ge=1, le=100)


class WakeWordResponse(WakeWordBase):
    """ウェイクワードレスポンス"""
    id: str
    agent_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ========== Capability Schemas ==========

class CapabilityBase(BaseModel):
    """エージェント能力基本スキーマ"""
    task_type: str = Field(..., min_length=1, max_length=100, description="タスクタイプ")
    description: Optional[str] = Field(None, max_length=1000, description="能力の説明")
    input_format: Optional[Dict[str, Any]] = Field(None, description="入力フォーマット定義")
    output_format: Optional[Dict[str, Any]] = Field(None, description="出力フォーマット定義")


class CapabilityCreate(CapabilityBase):
    """エージェント能力作成スキーマ"""
    pass


class CapabilityUpdate(BaseModel):
    """エージェント能力更新スキーマ"""
    task_type: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    input_format: Optional[Dict[str, Any]] = None
    output_format: Optional[Dict[str, Any]] = None


class CapabilityResponse(CapabilityBase):
    """エージェント能力レスポンス"""
    id: str
    agent_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ========== AI Agent Schemas ==========

class AgentBase(BaseModel):
    """エージェント基本スキーマ"""
    name: str = Field(..., min_length=1, max_length=100, description="エージェント名（内部ID）")
    display_name: str = Field(..., min_length=1, max_length=200, description="表示名")
    description: str = Field(..., min_length=1, description="エージェントの説明")
    category: AgentCategory = Field(AgentCategory.CUSTOM, description="カテゴリ")
    is_active: bool = Field(True, description="有効/無効")
    priority: int = Field(10, ge=1, le=100, description="優先度（1-100）")
    executor_type: ExecutorType = Field(ExecutorType.LLM_BASED, description="実行タイプ")

    # LLMベース用設定
    llm_model: Optional[str] = Field("gpt-4o-mini", description="使用するLLMモデル")
    system_prompt: str = Field(..., min_length=1, description="システムプロンプト")
    user_prompt_template: str = Field(..., min_length=1, description="ユーザープロンプトテンプレート")
    response_format: ResponseFormat = Field(ResponseFormat.TEXT, description="レスポンスフォーマット")

    # 実行設定
    max_retries: int = Field(3, ge=0, le=10, description="最大リトライ回数")
    timeout_seconds: int = Field(90, ge=10, le=600, description="タイムアウト秒数")

    # メタデータ
    tags: Optional[List[str]] = Field(None, description="タグリスト")
    agent_metadata: Optional[Dict[str, Any]] = Field(None, description="追加メタデータ")


class AgentCreate(AgentBase):
    """エージェント作成スキーマ"""
    class_path: Optional[str] = Field(None, max_length=500, description="code_based用Pythonクラスパス")
    wake_words: Optional[List[WakeWordCreate]] = Field(None, description="ウェイクワードリスト")
    capabilities: Optional[List[CapabilityCreate]] = Field(None, description="能力リスト")

    @validator('class_path')
    def validate_class_path_for_code_based(cls, v, values):
        """code_basedの場合はclass_pathが必須"""
        if values.get('executor_type') == ExecutorType.CODE_BASED and not v:
            raise ValueError('code_based executor requires class_path')
        return v


class AgentUpdate(BaseModel):
    """エージェント更新スキーマ（システムエージェントは制限あり）"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    category: Optional[AgentCategory] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=100)

    # LLMベース用設定（システムエージェントは変更不可）
    llm_model: Optional[str] = None
    system_prompt: Optional[str] = Field(None, min_length=1)
    user_prompt_template: Optional[str] = Field(None, min_length=1)
    response_format: Optional[ResponseFormat] = None

    # 実行設定
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    timeout_seconds: Optional[int] = Field(None, ge=10, le=600)

    # メタデータ
    tags: Optional[List[str]] = None
    agent_metadata: Optional[Dict[str, Any]] = None

    # Wake words と capabilities は別エンドポイントで管理
    wake_words: Optional[List[WakeWordCreate]] = None
    capabilities: Optional[List[CapabilityCreate]] = None


class AgentResponse(AgentBase):
    """エージェントレスポンス"""
    id: str
    is_system: bool
    is_deletable: bool
    class_path: Optional[str] = None
    created_by: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # 関連データ
    wake_words: List[WakeWordResponse] = []
    capabilities: List[CapabilityResponse] = []

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """エージェント一覧レスポンス"""
    id: str
    name: str
    display_name: str
    description: str
    category: AgentCategory
    is_active: bool
    is_system: bool
    is_deletable: bool
    priority: int
    executor_type: ExecutorType
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== Agent Profile Schemas ==========

class AgentProfileBase(BaseModel):
    """エージェントプロファイル基本スキーマ"""
    name: str = Field(..., min_length=1, max_length=200, description="プロファイル名")
    description: Optional[str] = Field(None, description="プロファイルの説明")
    paper_type: PaperType = Field(..., description="論文タイプ")
    is_default: bool = Field(False, description="デフォルトプロファイル")


class AgentProfileCreate(AgentProfileBase):
    """エージェントプロファイル作成スキーマ"""
    pass


class AgentProfileUpdate(BaseModel):
    """エージェントプロファイル更新スキーマ"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    paper_type: Optional[PaperType] = None
    is_default: Optional[bool] = None


class AgentProfileResponse(AgentProfileBase):
    """エージェントプロファイルレスポンス"""
    id: str
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # 設定数（集計用）
    settings_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ========== Agent Profile Settings Schemas ==========

class AgentProfileSettingBase(BaseModel):
    """プロファイル設定基本スキーマ"""
    agent_id: str = Field(..., description="エージェントID")
    is_enabled: bool = Field(True, description="有効/無効")
    priority_override: Optional[int] = Field(None, ge=1, le=100, description="優先度オーバーライド")
    wake_words_override: Optional[List[WakeWordCreate]] = Field(None, description="ウェイクワードオーバーライド")


class AgentProfileSettingCreate(AgentProfileSettingBase):
    """プロファイル設定作成スキーマ"""
    profile_id: str = Field(..., description="プロファイルID")


class AgentProfileSettingUpdate(BaseModel):
    """プロファイル設定更新スキーマ"""
    is_enabled: Optional[bool] = None
    priority_override: Optional[int] = Field(None, ge=1, le=100)
    wake_words_override: Optional[List[WakeWordCreate]] = None


class AgentProfileSettingResponse(AgentProfileSettingBase):
    """プロファイル設定レスポンス"""
    id: str
    profile_id: str
    created_at: datetime
    updated_at: datetime

    # エージェント情報（JOIN用）
    agent: Optional[AgentListResponse] = None

    class Config:
        from_attributes = True


# ========== Execution Log Schemas ==========

class ExecutionLogResponse(BaseModel):
    """実行ログレスポンス"""
    id: str
    agent_id: str
    paper_id: Optional[str] = None
    session_id: Optional[str] = None
    status: ExecutionStatus
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    created_at: datetime

    # エージェント情報
    agent: Optional[AgentListResponse] = None

    class Config:
        from_attributes = True


# ========== Bulk Operations Schemas ==========

class BulkAgentSettingUpdate(BaseModel):
    """一括エージェント設定更新"""
    agent_settings: List[AgentProfileSettingBase] = Field(..., description="エージェント設定リスト")


class BulkDeleteRequest(BaseModel):
    """一括削除リクエスト"""
    ids: List[str] = Field(..., min_items=1, description="削除対象IDリスト")


# ========== Statistics Schemas ==========

class AgentStatistics(BaseModel):
    """エージェント統計情報"""
    total_agents: int
    active_agents: int
    system_agents: int
    custom_agents: int
    agents_by_category: Dict[str, int]
    agents_by_executor_type: Dict[str, int]


class AgentExecutionStats(BaseModel):
    """エージェント実行統計"""
    agent_id: str
    agent_name: str
    total_executions: int
    success_count: int
    failure_count: int
    avg_execution_time_ms: float
    last_executed_at: Optional[datetime] = None
