"""add_dynamic_agent_tables

Revision ID: ab5b9cf4af59
Revises: 857f87cadbac
Create Date: 2025-10-10 10:20:22.325104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab5b9cf4af59'
down_revision: Union[str, None] = '857f87cadbac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ai_agents テーブル作成
    op.create_table(
        'ai_agents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=False, server_default='custom'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('executor_type', sa.String(), nullable=False, server_default='llm_based'),
        sa.Column('llm_model', sa.String(), nullable=True, server_default='gpt-4o-mini'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('user_prompt_template', sa.Text(), nullable=False),
        sa.Column('response_format', sa.String(), nullable=True, server_default='text'),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('agent_metadata', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('idx_agents_name', 'ai_agents', ['name'])
    op.create_index('idx_agents_category', 'ai_agents', ['category'])
    op.create_index('idx_agents_is_active', 'ai_agents', ['is_active'])
    op.create_index('idx_agents_user_id', 'ai_agents', ['user_id'])

    # agent_wake_words テーブル作成
    op.create_table(
        'agent_wake_words',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('keyword', sa.String(), nullable=False),
        sa.Column('keyword_type', sa.String(), nullable=False, server_default='exact'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('semantic_weight', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('min_similarity_score', sa.Float(), nullable=True, server_default='0.7'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['ai_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('idx_wake_words_agent', 'agent_wake_words', ['agent_id'])
    op.create_index('idx_wake_words_keyword', 'agent_wake_words', ['keyword'])
    op.create_index('idx_wake_words_type', 'agent_wake_words', ['keyword_type'])
    op.create_index('idx_wake_words_user', 'agent_wake_words', ['user_id'])
    op.create_index('idx_wake_words_active_priority', 'agent_wake_words', ['is_active', 'priority'])

    # agent_capabilities テーブル作成
    op.create_table(
        'agent_capabilities',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('capability_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('best_for', sa.JSON(), nullable=True),
        sa.Column('supported_task_types', sa.JSON(), nullable=False),
        sa.Column('task_examples', sa.JSON(), nullable=True),
        sa.Column('average_execution_time', sa.Integer(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['ai_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('idx_capabilities_agent', 'agent_capabilities', ['agent_id'])
    op.create_index('idx_capabilities_type', 'agent_capabilities', ['capability_type'])

    # agent_execution_logs テーブル作成
    op.create_table(
        'agent_execution_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('triggered_by', sa.String(), nullable=False, server_default='wake_word'),
        sa.Column('wake_word_used', sa.String(), nullable=True),
        sa.Column('user_message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('result_summary', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('llm_calls', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['ai_agents.id']),
        sa.ForeignKeyConstraint(['session_id'], ['paper_chat_sessions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('idx_logs_agent', 'agent_execution_logs', ['agent_id'])
    op.create_index('idx_logs_session', 'agent_execution_logs', ['session_id'])
    op.create_index('idx_logs_user', 'agent_execution_logs', ['user_id'])
    op.create_index('idx_logs_created', 'agent_execution_logs', ['created_at'])
    op.create_index('idx_logs_status', 'agent_execution_logs', ['status'])


def downgrade() -> None:
    op.drop_table('agent_execution_logs')
    op.drop_table('agent_capabilities')
    op.drop_table('agent_wake_words')
    op.drop_table('ai_agents')
