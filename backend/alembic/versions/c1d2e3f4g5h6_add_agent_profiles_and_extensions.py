"""add_agent_profiles_and_extensions

Revision ID: c1d2e3f4g5h6
Revises: ab5b9cf4af59
Create Date: 2025-10-14 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4g5h6'
down_revision: Union[str, None] = 'ab5b9cf4af59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # データベース接続とインスペクターを取得
    conn = op.get_bind()
    inspector = inspect(conn)

    # ai_agents テーブルに新しいカラムを追加（既にある場合はスキップ）
    existing_columns = [col['name'] for col in inspector.get_columns('ai_agents')]

    if 'class_path' not in existing_columns or 'is_deletable' not in existing_columns:
        with op.batch_alter_table('ai_agents', schema=None) as batch_op:
            if 'class_path' not in existing_columns:
                batch_op.add_column(sa.Column('class_path', sa.String(), nullable=True))
            if 'is_deletable' not in existing_columns:
                batch_op.add_column(sa.Column('is_deletable', sa.Boolean(), nullable=False, server_default='1'))

    # agent_profiles テーブル作成（既にある場合はスキップ）
    existing_tables = inspector.get_table_names()

    if 'agent_profiles' not in existing_tables:
        op.create_table(
            'agent_profiles',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('paper_type', sa.String(), nullable=False),
            sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('user_id', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        )
        op.create_index('idx_profiles_paper_type', 'agent_profiles', ['paper_type'])
        op.create_index('idx_profiles_user', 'agent_profiles', ['user_id'])
        op.create_index('idx_profiles_default', 'agent_profiles', ['is_default'])

    # agent_profile_settings テーブル作成（既にある場合はスキップ）
    if 'agent_profile_settings' not in existing_tables:
        op.create_table(
            'agent_profile_settings',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('profile_id', sa.String(), nullable=False),
            sa.Column('agent_id', sa.String(), nullable=False),
            sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('priority_override', sa.Integer(), nullable=True),
            sa.Column('wake_words_override', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['profile_id'], ['agent_profiles.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['agent_id'], ['ai_agents.id'], ondelete='CASCADE'),
        )
        op.create_index('idx_profile_settings_profile', 'agent_profile_settings', ['profile_id'])
        op.create_index('idx_profile_settings_agent', 'agent_profile_settings', ['agent_id'])

    # research_papers テーブルに新しいカラムを追加（既にある場合はスキップ）
    research_papers_columns = [col['name'] for col in inspector.get_columns('research_papers')]

    if 'agent_profile_id' not in research_papers_columns or 'custom_agent_settings' not in research_papers_columns:
        with op.batch_alter_table('research_papers', schema=None) as batch_op:
            if 'agent_profile_id' not in research_papers_columns:
                batch_op.add_column(sa.Column('agent_profile_id', sa.String(), nullable=True))
            if 'custom_agent_settings' not in research_papers_columns:
                batch_op.add_column(sa.Column('custom_agent_settings', sa.JSON(), nullable=True))

            # 外部キーとインデックスは既存チェックが複雑なので、エラーハンドリングで対応
            try:
                batch_op.create_foreign_key('fk_papers_profile', 'agent_profiles', ['agent_profile_id'], ['id'])
            except:
                pass  # 既に存在する場合はスキップ

            try:
                batch_op.create_index('idx_papers_profile', ['agent_profile_id'])
            except:
                pass  # 既に存在する場合はスキップ


def downgrade() -> None:
    # research_papers テーブルのカラムを削除（SQLite用にbatch mode使用）
    with op.batch_alter_table('research_papers', schema=None) as batch_op:
        batch_op.drop_index('idx_papers_profile')
        batch_op.drop_constraint('fk_papers_profile', type_='foreignkey')
        batch_op.drop_column('custom_agent_settings')
        batch_op.drop_column('agent_profile_id')

    # agent_profile_settings テーブルを削除
    op.drop_table('agent_profile_settings')

    # agent_profiles テーブルを削除
    op.drop_table('agent_profiles')

    # ai_agents テーブルのカラムを削除（SQLite用にbatch mode使用）
    with op.batch_alter_table('ai_agents', schema=None) as batch_op:
        batch_op.drop_column('is_deletable')
        batch_op.drop_column('class_path')
