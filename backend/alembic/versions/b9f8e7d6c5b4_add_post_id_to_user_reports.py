"""create or update user_reports table with post_id

Revision ID: b9f8e7d6c5b4
Revises: a3f7426b04f8
Create Date: 2026-08-31 16:22:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = 'b9f8e7d6c5b4'
down_revision = 'a3f7426b04f8'
branch_labels = None
depends_on = None


def _table_exists(bind, table_name) -> bool:
    return table_name in inspect(bind).get_table_names()


def _column_exists(bind, table_name, column_name) -> bool:
    if not _table_exists(bind, table_name):
        return False
    return column_name in {c["name"] for c in inspect(bind).get_columns(table_name)}


def upgrade():
    bind = op.get_bind()
    if not _table_exists(bind, 'user_reports'):
        op.create_table(
            'user_reports',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('reporter_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('reported_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('post_id', UUID(as_uuid=True), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=True),
            sa.Column('reason', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        )
        op.create_index('ix_user_reports_reporter_id', 'user_reports', ['reporter_id'], unique=False)
        op.create_index('ix_user_reports_reported_id', 'user_reports', ['reported_id'], unique=False)
        op.create_index('ix_user_reports_post_id', 'user_reports', ['post_id'], unique=False)
    else:
        if not _column_exists(bind, 'user_reports', 'post_id'):
            op.add_column('user_reports', sa.Column('post_id', UUID(as_uuid=True), nullable=True))
            op.create_foreign_key('fk_user_reports_post_id', 'user_reports', 'posts', ['post_id'], ['id'], ondelete='CASCADE')
            op.create_index(op.f('ix_user_reports_post_id'), 'user_reports', ['post_id'], unique=False)


def downgrade():
    bind = op.get_bind()
    if _table_exists(bind, 'user_reports'):
        op.drop_table('user_reports')
