from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, JSON, ForeignKey, Index, UniqueConstraint
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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # リレーション
    user = relationship("UserModel", back_populates="research_papers")
    sections = relationship("PaperSectionModel", back_populates="paper", cascade="all, delete-orphan")
    chat_sessions = relationship("PaperChatSessionModel", back_populates="paper", cascade="all, delete-orphan")


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
