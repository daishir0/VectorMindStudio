from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, JSON, ForeignKey
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
