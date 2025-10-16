"""
LangGraphエージェント管理のエンティティ定義

LangGraphで使用されるエージェント、インテント、チェーン、実行ログを
データベースで管理するためのエンティティです。
"""

from sqlalchemy import Column, String, Boolean, Integer, Float, JSON, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.infrastructure.database.models import Base


class LangGraphAgent(Base):
    """
    LangGraphエージェントマスタ

    7つの専門エージェントの設定を管理します。
    """
    __tablename__ = "langgraph_agents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True, comment="エージェント名（例: outline_agent）")
    display_name = Column(String(200), nullable=False, comment="表示名（例: アウトラインエージェント）")
    description = Column(Text, comment="エージェントの説明")
    class_path = Column(String(500), nullable=False, comment="Pythonクラスパス（例: app.services.agents.OutlineAgent）")
    config = Column(JSON, comment="エージェント固有の設定（JSON）")
    is_active = Column(Boolean, default=True, nullable=False, comment="有効/無効フラグ")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # リレーションシップ
    intents = relationship("LangGraphIntent", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LangGraphAgent(name={self.name}, display_name={self.display_name})>"


class LangGraphIntent(Base):
    """
    LangGraphインテントマスタ

    25の単一タスクインテントを管理します。
    """
    __tablename__ = "langgraph_intents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    intent_name = Column(String(100), unique=True, nullable=False, index=True, comment="インテント名（例: create_section）")
    display_name = Column(String(200), nullable=False, comment="表示名（例: セクション作成）")
    description = Column(Text, comment="インテントの説明")
    agent_id = Column(String(36), ForeignKey("langgraph_agents.id"), nullable=False, comment="担当エージェントID")
    parameters_schema = Column(JSON, comment="パラメータのJSONスキーマ")
    example_query = Column(Text, comment="ユーザー依頼の例（例: 「新しいセクションを作成してください」）")
    is_active = Column(Boolean, default=True, nullable=False, comment="有効/無効フラグ")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # リレーションシップ
    agent = relationship("LangGraphAgent", back_populates="intents")

    def __repr__(self):
        return f"<LangGraphIntent(intent_name={self.intent_name}, display_name={self.display_name})>"


class LangGraphChainIntent(Base):
    """
    LangGraphチェーンインテントマスタ

    5つの複数エージェント連携タスク（Sequential Chain）を管理します。
    """
    __tablename__ = "langgraph_chain_intents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chain_name = Column(String(100), unique=True, nullable=False, index=True, comment="チェーン名（例: research_and_write）")
    display_name = Column(String(200), nullable=False, comment="表示名（例: 資料検索→執筆→品質チェック）")
    description = Column(Text, comment="チェーンの説明")
    task_sequence = Column(JSON, nullable=False, comment="タスク順序（例: [\"search_chromadb\", \"generate_content\", \"quality_assessment\"]）")
    example_query = Column(Text, comment="ユーザー依頼の例")
    is_active = Column(Boolean, default=True, nullable=False, comment="有効/無効フラグ")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<LangGraphChainIntent(chain_name={self.chain_name}, display_name={self.display_name})>"


class LangGraphExecutionLog(Base):
    """
    LangGraph実行ログ

    ワークフローの実行履歴を記録します。
    """
    __tablename__ = "langgraph_execution_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), index=True, nullable=False, comment="チャットセッションID")
    user_id = Column(String(36), index=True, nullable=False, comment="ユーザーID")
    paper_id = Column(String(36), index=True, nullable=False, comment="論文ID")
    user_query = Column(Text, nullable=False, comment="ユーザーの依頼")
    intent = Column(String(100), comment="解析されたインテント")
    intent_params = Column(JSON, comment="インテントパラメータ")
    agents_used = Column(JSON, comment="使用されたエージェントのリスト")
    execution_time_ms = Column(Integer, comment="実行時間（ミリ秒）")
    loop_count = Column(Integer, default=0, comment="ループ回数")
    validation_result = Column(String(50), comment="品質検証結果（ok/needs_refinement）")
    final_response = Column(Text, comment="最終応答")
    error = Column(Text, comment="エラーメッセージ（エラー時のみ）")
    execution_metadata = Column(JSON, comment="その他のメタデータ")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<LangGraphExecutionLog(id={self.id}, intent={self.intent}, session_id={self.session_id})>"
