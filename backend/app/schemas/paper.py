"""
論文執筆機能のスキーマ定義
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class PaperBase(BaseModel):
    """論文基底スキーマ"""
    title: str = Field(..., min_length=1, max_length=500, description="論文タイトル")
    description: Optional[str] = Field(None, max_length=2000, description="論文の説明")


class PaperCreate(PaperBase):
    """論文作成リクエスト"""
    pass


class PaperUpdate(BaseModel):
    """論文更新リクエスト"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, pattern="^(draft|in_progress|completed|published)$")


class PaperSummary(BaseModel):
    """論文サマリー（一覧表示用）"""
    id: str
    title: str
    status: str
    section_count: int = 0
    total_words: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PaperDetail(BaseModel):
    """論文詳細情報"""
    id: str
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# === セクション関連 ===

class SectionBase(BaseModel):
    """セクション基底スキーマ"""
    title: str = Field(..., min_length=1, max_length=300, description="セクションタイトル")
    content: str = Field(default="", description="セクション内容")


class SectionCreate(SectionBase):
    """セクション作成リクエスト"""
    parent_id: Optional[str] = Field(None, description="親セクションID")
    position: int = Field(default=-1, description="挿入位置（-1は末尾）")


class SectionUpdate(BaseModel):
    """セクション更新リクエスト"""
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    content: Optional[str] = None
    section_number: Optional[str] = Field(None, min_length=1, max_length=20, description="セクション番号（1, 1.1, A, I等）")
    status: Optional[str] = Field(None, pattern="^(draft|writing|review|completed)$")


class SectionOutline(BaseModel):
    """セクションアウトライン（構造表示用）"""
    id: str
    position: int
    section_number: str
    title: str
    word_count: int
    status: str
    summary: str
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SectionDetail(BaseModel):
    """セクション詳細情報"""
    id: str
    paper_id: str
    position: int
    section_number: str
    title: str
    content: str
    summary: str
    word_count: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SectionHistory(BaseModel):
    """セクション履歴"""
    id: str
    version_number: int
    title: str
    content: str
    summary: str
    change_description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# === チャット関連 ===

class ChatSessionCreate(BaseModel):
    """チャットセッション作成リクエスト"""
    title: str = Field(..., min_length=1, max_length=200, description="セッションタイトル")


class ChatSessionSummary(BaseModel):
    """チャットセッションサマリー"""
    id: str
    title: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    """チャットメッセージ作成リクエスト"""
    message: str = Field(..., min_length=1, max_length=5000, description="メッセージ内容")
    target_section_id: Optional[str] = Field(None, description="対象セクションID")


class TodoTaskInfo(BaseModel):
    """TODOタスク情報"""
    id: str
    description: str
    agent_name: str
    priority: int
    status: str
    result: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    """チャットメッセージ"""
    id: str
    role: str  # user, assistant, agent
    content: str
    agent_name: Optional[str] = None
    todo_tasks: List[TodoTaskInfo] = []
    references: List[Dict[str, Any]] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """チャットレスポンス"""
    message: str
    todo_tasks: List[TodoTaskInfo] = []
    task_results: Dict[str, Any] = {}
    references: List[Dict[str, Any]] = []
    suggestions: List[str] = []
    success: bool = True


# === セクション順序変更関連 ===

class SectionMoveRequest(BaseModel):
    """セクション移動リクエスト"""
    action: Literal["up", "down", "top", "bottom", "to_position"] = Field(..., description="移動アクション")
    new_position: Optional[int] = Field(None, description="移動先位置（to_positionの場合必須）")


class SectionMoveResponse(BaseModel):
    """セクション移動レスポンス"""
    success: bool
    message: str
    updated_sections: List[SectionOutline]


# === エージェント関連 ===

class AgentExecuteRequest(BaseModel):
    """エージェント実行リクエスト"""
    task: str = Field(..., description="実行タスク")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="パラメータ")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="コンテキスト")


class AgentExecuteResponse(BaseModel):
    """エージェント実行レスポンス"""
    result: Any
    execution_time: float
    status: str
    agent_name: str
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# === 検索・引用関連 ===

class ReferenceSearchRequest(BaseModel):
    """文献検索リクエスト"""
    query: Optional[str] = Field(None, max_length=1000)
    keywords: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=50)
    search_types: List[str] = Field(default=["vector", "tag", "keyword"])


class ReferenceSearchResult(BaseModel):
    """文献検索結果"""
    id: str
    filename: str
    content: str
    relevance_score: float
    tags: List[str]
    search_types: List[str]
    citation: Optional[str] = None


class ReferenceSearchResponse(BaseModel):
    """文献検索レスポンス"""
    search_results: List[ReferenceSearchResult]
    citations: List[str]
    search_summary: Dict[str, Any]
    query: Optional[str]
    keywords: List[str]
    tags: List[str]


# === YAML対応用のレスポンス ===

class YamlResponse(BaseModel):
    """YAML形式レスポンス用の汎用クラス"""
    success: bool
    data: Any
    message: Optional[str] = None
    
    def to_yaml(self) -> str:
        """YAMLフォーマットに変換"""
        import yaml
        return yaml.dump(
            self.dict(),
            allow_unicode=True,
            default_flow_style=False
        )