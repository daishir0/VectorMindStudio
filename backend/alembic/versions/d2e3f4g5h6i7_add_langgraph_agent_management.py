"""add langgraph agent management tables

Revision ID: d2e3f4g5h6i7
Revises: c1d2e3f4g5h6
Create Date: 2025-10-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd2e3f4g5h6i7'
down_revision = 'c1d2e3f4g5h6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    LangGraphエージェント管理テーブルを追加

    4つのテーブルを作成:
    - langgraph_agents: エージェントマスタ
    - langgraph_intents: インテントマスタ
    - langgraph_chain_intents: チェーンインテントマスタ
    - langgraph_execution_logs: 実行ログ
    """

    # 1. langgraph_agents テーブル
    op.create_table(
        'langgraph_agents',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, comment='エージェント名'),
        sa.Column('display_name', sa.String(200), nullable=False, comment='表示名'),
        sa.Column('description', sa.Text(), nullable=True, comment='エージェントの説明'),
        sa.Column('class_path', sa.String(500), nullable=False, comment='Pythonクラスパス'),
        sa.Column('config', sa.JSON(), nullable=True, comment='エージェント固有の設定'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='有効/無効フラグ'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='LangGraphエージェントマスタ'
    )
    op.create_index('ix_langgraph_agents_name', 'langgraph_agents', ['name'], unique=True)

    # 2. langgraph_intents テーブル
    op.create_table(
        'langgraph_intents',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('intent_name', sa.String(100), nullable=False, comment='インテント名'),
        sa.Column('display_name', sa.String(200), nullable=False, comment='表示名'),
        sa.Column('description', sa.Text(), nullable=True, comment='インテントの説明'),
        sa.Column('agent_id', sa.String(36), nullable=False, comment='担当エージェントID'),
        sa.Column('parameters_schema', sa.JSON(), nullable=True, comment='パラメータのJSONスキーマ'),
        sa.Column('example_query', sa.Text(), nullable=True, comment='ユーザー依頼の例'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='有効/無効フラグ'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['langgraph_agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='LangGraphインテントマスタ'
    )
    op.create_index('ix_langgraph_intents_intent_name', 'langgraph_intents', ['intent_name'], unique=True)

    # 3. langgraph_chain_intents テーブル
    op.create_table(
        'langgraph_chain_intents',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('chain_name', sa.String(100), nullable=False, comment='チェーン名'),
        sa.Column('display_name', sa.String(200), nullable=False, comment='表示名'),
        sa.Column('description', sa.Text(), nullable=True, comment='チェーンの説明'),
        sa.Column('task_sequence', sa.JSON(), nullable=False, comment='タスク順序'),
        sa.Column('example_query', sa.Text(), nullable=True, comment='ユーザー依頼の例'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='有効/無効フラグ'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='LangGraphチェーンインテントマスタ'
    )
    op.create_index('ix_langgraph_chain_intents_chain_name', 'langgraph_chain_intents', ['chain_name'], unique=True)

    # 4. langgraph_execution_logs テーブル
    op.create_table(
        'langgraph_execution_logs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=False, comment='チャットセッションID'),
        sa.Column('user_id', sa.String(36), nullable=False, comment='ユーザーID'),
        sa.Column('paper_id', sa.String(36), nullable=False, comment='論文ID'),
        sa.Column('user_query', sa.Text(), nullable=False, comment='ユーザーの依頼'),
        sa.Column('intent', sa.String(100), nullable=True, comment='解析されたインテント'),
        sa.Column('intent_params', sa.JSON(), nullable=True, comment='インテントパラメータ'),
        sa.Column('agents_used', sa.JSON(), nullable=True, comment='使用されたエージェントのリスト'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True, comment='実行時間（ミリ秒）'),
        sa.Column('loop_count', sa.Integer(), nullable=True, default=0, comment='ループ回数'),
        sa.Column('validation_result', sa.String(50), nullable=True, comment='品質検証結果'),
        sa.Column('final_response', sa.Text(), nullable=True, comment='最終応答'),
        sa.Column('error', sa.Text(), nullable=True, comment='エラーメッセージ'),
        sa.Column('execution_metadata', sa.JSON(), nullable=True, comment='その他のメタデータ'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='LangGraph実行ログ'
    )
    op.create_index('ix_langgraph_execution_logs_session_id', 'langgraph_execution_logs', ['session_id'])
    op.create_index('ix_langgraph_execution_logs_user_id', 'langgraph_execution_logs', ['user_id'])
    op.create_index('ix_langgraph_execution_logs_paper_id', 'langgraph_execution_logs', ['paper_id'])
    op.create_index('ix_langgraph_execution_logs_created_at', 'langgraph_execution_logs', ['created_at'])


def downgrade() -> None:
    """
    LangGraphエージェント管理テーブルを削除
    """
    # 逆順で削除（外部キー制約を考慮）
    op.drop_index('ix_langgraph_execution_logs_created_at', table_name='langgraph_execution_logs')
    op.drop_index('ix_langgraph_execution_logs_paper_id', table_name='langgraph_execution_logs')
    op.drop_index('ix_langgraph_execution_logs_user_id', table_name='langgraph_execution_logs')
    op.drop_index('ix_langgraph_execution_logs_session_id', table_name='langgraph_execution_logs')
    op.drop_table('langgraph_execution_logs')

    op.drop_index('ix_langgraph_chain_intents_chain_name', table_name='langgraph_chain_intents')
    op.drop_table('langgraph_chain_intents')

    op.drop_index('ix_langgraph_intents_intent_name', table_name='langgraph_intents')
    op.drop_table('langgraph_intents')

    op.drop_index('ix_langgraph_agents_name', table_name='langgraph_agents')
    op.drop_table('langgraph_agents')
