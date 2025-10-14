from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, JSON, Float, ForeignKey, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class UserModel(Base):
    """ユーザーテーブル"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    roles = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # リレーション
    templates = relationship("TemplateModel", back_populates="user", cascade="all, delete-orphan")
    outputs = relationship("OutputModel", back_populates="user", cascade="all, delete-orphan")
    research_papers = relationship("ResearchPaperModel", back_populates="user", cascade="all, delete-orphan")
    paper_sections = relationship("PaperSectionModel", back_populates="user", cascade="all, delete-orphan")
    paper_chat_sessions = relationship("PaperChatSessionModel", back_populates="user", cascade="all, delete-orphan")


class TemplateModel(Base):
    """テンプレートテーブル"""
    __tablename__ = "templates"
    
    id = Column(String, primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    variables = Column(JSON, default=list, nullable=False)
    requirements = Column(Text, default="", nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    status = Column(String(20), default="draft", nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    usage_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # リレーション
    user = relationship("UserModel", back_populates="templates")
    outputs = relationship("OutputModel", back_populates="template", cascade="all, delete-orphan")


class OutputModel(Base):
    """生成出力テーブル"""
    __tablename__ = "outputs"
    
    id = Column(String, primary_key=True)
    template_id = Column(String, ForeignKey("templates.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)  # アウトプット名
    input_variables = Column(JSON, default=dict, nullable=False)
    generated_content = Column(Text, nullable=False)
    ai_model = Column(String(100), nullable=False)
    generation_time = Column(Integer, nullable=False)  # ミリ秒
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # リレーション
    template = relationship("TemplateModel", back_populates="outputs")
    user = relationship("UserModel", back_populates="outputs")


class ApiKeyModel(Base):
    """APIキーテーブル"""
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False)
    permissions = Column(JSON, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # リレーション
    user = relationship("UserModel")


class AuditLogModel(Base):
    """監査ログテーブル"""
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String, nullable=True, index=True)
    details = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # リレーション
    user = relationship("UserModel")


class UploadModel(Base):
    """アップロード管理（原本と変換後のパス）"""
    __tablename__ = "uploads"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    filename = Column(String(300), nullable=False, index=True)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    original_path = Column(String(500), nullable=False)
    converted_path = Column(String(500), nullable=True)
    status = Column(String(20), default="pending", nullable=False, index=True)
    vector_status = Column(String(20), default="pending", nullable=False, index=True)
    engine = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    tags = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("UserModel")


class ChatSessionModel(Base):
    """チャットセッションテーブル"""
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # リレーション
    user = relationship("UserModel")
    messages = relationship("ChatMessageModel", back_populates="session", cascade="all, delete-orphan")


class ChatMessageModel(Base):
    """チャットメッセージテーブル"""
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(JSON, default=list, nullable=False)  # 参照元ファイル一覧
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # リレーション
    session = relationship("ChatSessionModel", back_populates="messages")


class ResearchPaperModel(Base):
    """研究論文テーブル"""
    __tablename__ = "research_papers"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="draft", nullable=False, index=True)  # draft, in_progress, completed, published
    agent_profile_id = Column(String, ForeignKey("agent_profiles.id"), nullable=True, index=True)
    custom_agent_settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # リレーション
    user = relationship("UserModel", back_populates="research_papers")
    sections = relationship("PaperSectionModel", back_populates="paper", cascade="all, delete-orphan")
    chat_sessions = relationship("PaperChatSessionModel", back_populates="paper", cascade="all, delete-orphan")
    agent_profile = relationship("AgentProfileModel", back_populates="papers")


class PaperSectionModel(Base):
    """論文セクションテーブル"""
    __tablename__ = "paper_sections"
    
    id = Column(String, primary_key=True)
    paper_id = Column(String, ForeignKey("research_papers.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    position = Column(Integer, nullable=False, index=True)  # 順序管理用: 1, 2, 3...
    section_number = Column(String(20), nullable=False)  # ユーザー表示用: "1", "1.1", "A", "II.3"
    title = Column(String(300), nullable=False)
    content = Column(Text, default='', nullable=False)
    summary = Column(Text, default='', nullable=False)  # AI自動生成要約（150-250文字）
    word_count = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="draft", nullable=False, index=True)  # draft, writing, review, completed
    is_deleted = Column(Boolean, default=False, nullable=False)  # 論理削除フラグ
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # リレーション
    paper = relationship("ResearchPaperModel", back_populates="sections")
    user = relationship("UserModel", back_populates="paper_sections")
    history = relationship("PaperSectionHistoryModel", back_populates="section", cascade="all, delete-orphan")
    
    # 複合制約
    __table_args__ = (
        UniqueConstraint('paper_id', 'position', name='uq_paper_position'),
        Index('idx_paper_sections_paper_position', 'paper_id', 'position'),
    )


class PaperSectionHistoryModel(Base):
    """論文セクション履歴テーブル"""
    __tablename__ = "paper_section_history"
    
    id = Column(String, primary_key=True)
    section_id = Column(String, ForeignKey("paper_sections.id"), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    version_number = Column(Integer, nullable=False)
    change_description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # リレーション
    section = relationship("PaperSectionModel", back_populates="history")


class PaperChatSessionModel(Base):
    """論文研究ディスカッションセッションテーブル"""
    __tablename__ = "paper_chat_sessions"
    
    id = Column(String, primary_key=True)
    paper_id = Column(String, ForeignKey("research_papers.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # リレーション
    paper = relationship("ResearchPaperModel", back_populates="chat_sessions")
    user = relationship("UserModel", back_populates="paper_chat_sessions")
    messages = relationship("PaperChatMessageModel", back_populates="session", cascade="all, delete-orphan")


class PaperChatMessageModel(Base):
    """論文研究ディスカッションメッセージテーブル"""
    __tablename__ = "paper_chat_messages"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("paper_chat_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'agent'
    content = Column(Text, nullable=False)
    agent_name = Column(String(100), nullable=True)  # エージェント名（agent roleの場合）
    todo_tasks = Column(JSON, default=list, nullable=False)  # TODOタスク情報
    references = Column(JSON, default=list, nullable=False)  # 参照した文献やセクション
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # リレーション
    session = relationship("PaperChatSessionModel", back_populates="messages")


class AIAgentModel(Base):
    """AIエージェントテーブル"""
    __tablename__ = "ai_agents"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False, server_default='custom', index=True)
    is_active = Column(Boolean, nullable=False, server_default='1', index=True)
    is_system = Column(Boolean, nullable=False, server_default='0')
    priority = Column(Integer, nullable=False, server_default='10')
    executor_type = Column(String, nullable=False, server_default='llm_based')
    llm_model = Column(String, nullable=True, server_default='gpt-4o-mini')
    max_retries = Column(Integer, nullable=False, server_default='3')
    timeout_seconds = Column(Integer, nullable=False, server_default='90')
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    response_format = Column(String, nullable=True, server_default='text')
    tags = Column(JSON, nullable=True)
    agent_metadata = Column(JSON, nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    class_path = Column(String, nullable=True)  # code_based用のPythonクラスパス
    is_deletable = Column(Boolean, nullable=False, server_default='1')  # 削除可能フラグ

    # リレーション
    wake_words = relationship("AgentWakeWordModel", back_populates="agent", cascade="all, delete-orphan")
    capabilities = relationship("AgentCapabilityModel", back_populates="agent", cascade="all, delete-orphan")
    execution_logs = relationship("AgentExecutionLogModel", back_populates="agent", cascade="all, delete-orphan")
    profile_settings = relationship("AgentProfileSettingModel", back_populates="agent", cascade="all, delete-orphan")


class AgentWakeWordModel(Base):
    """エージェント起動キーワードテーブル"""
    __tablename__ = "agent_wake_words"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword = Column(String, nullable=False, index=True)
    keyword_type = Column(String, nullable=False, server_default='exact', index=True)
    priority = Column(Integer, nullable=False, server_default='10')
    is_active = Column(Boolean, nullable=False, server_default='1')
    semantic_weight = Column(Float, nullable=True, server_default='1.0')
    min_similarity_score = Column(Float, nullable=True, server_default='0.7')
    usage_count = Column(Integer, nullable=False, server_default='0')
    last_triggered_at = Column(DateTime, nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # リレーション
    agent = relationship("AIAgentModel", back_populates="wake_words")

    # 複合インデックス
    __table_args__ = (
        Index('idx_wake_words_active_priority', 'is_active', 'priority'),
    )


class AgentCapabilityModel(Base):
    """エージェント能力定義テーブル"""
    __tablename__ = "agent_capabilities"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    capability_type = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    best_for = Column(JSON, nullable=True)
    supported_task_types = Column(JSON, nullable=False)
    task_examples = Column(JSON, nullable=True)
    average_execution_time = Column(Integer, nullable=True)
    success_rate = Column(Float, nullable=True, server_default='1.0')
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # リレーション
    agent = relationship("AIAgentModel", back_populates="capabilities")


class AgentExecutionLogModel(Base):
    """エージェント実行ログテーブル"""
    __tablename__ = "agent_execution_logs"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("ai_agents.id"), nullable=False, index=True)
    session_id = Column(String, ForeignKey("paper_chat_sessions.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    triggered_by = Column(String, nullable=False, server_default='wake_word')
    wake_word_used = Column(String, nullable=True)
    user_message = Column(Text, nullable=False)
    status = Column(String, nullable=False, index=True)
    execution_time_ms = Column(Integer, nullable=False)
    retry_count = Column(Integer, nullable=False, server_default='0')
    result_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    llm_calls = Column(Integer, nullable=False, server_default='1')
    created_at = Column(DateTime, nullable=False, server_default='CURRENT_TIMESTAMP', index=True)

    # リレーション
    agent = relationship("AIAgentModel", back_populates="execution_logs")


class AgentProfileModel(Base):
    """エージェントプロファイルテーブル（論文タイプ別の設定）"""
    __tablename__ = "agent_profiles"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    paper_type = Column(String, nullable=False, index=True)  # medical, engineering, humanities, general
    is_default = Column(Boolean, nullable=False, server_default='0', index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # リレーション
    user = relationship("UserModel")
    settings = relationship("AgentProfileSettingModel", back_populates="profile", cascade="all, delete-orphan")
    papers = relationship("ResearchPaperModel", back_populates="agent_profile")

    # インデックス
    __table_args__ = (
        Index('idx_profiles_paper_type', 'paper_type'),
        Index('idx_profiles_user', 'user_id'),
        Index('idx_profiles_default', 'is_default'),
    )


class AgentProfileSettingModel(Base):
    """プロファイル別エージェント設定テーブル"""
    __tablename__ = "agent_profile_settings"

    id = Column(String, primary_key=True)
    profile_id = Column(String, ForeignKey("agent_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    is_enabled = Column(Boolean, nullable=False, server_default='1')
    priority_override = Column(Integer, nullable=True)  # プロファイル内での優先度上書き
    wake_words_override = Column(JSON, nullable=True)  # ウェイクワード上書き
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # リレーション
    profile = relationship("AgentProfileModel", back_populates="settings")
    agent = relationship("AIAgentModel", back_populates="profile_settings")

    # インデックス
    __table_args__ = (
        Index('idx_profile_settings_profile', 'profile_id'),
        Index('idx_profile_settings_agent', 'agent_id'),
    )
