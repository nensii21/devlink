"""add post_id to user_reports

Revision ID: b9f8e7d6c5b4
Revises: a3f7426b04f8
Create Date: 2026-08-31 16:22:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'b9f8e7d6c5b4'
down_revision = 'a3f7426b04f8'
branch_labels = None
depends_on = None


def _column_exists(bind, table_name, column_name) -> bool:
    return column_name in {c["name"] for c in inspect(bind).get_columns(table_name)}


def upgrade():
    bind = op.get_bind()
    if not _column_exists(bind, 'user_reports', 'post_id'):
        op.add_column('user_reports', sa.Column('post_id', sa.UUID(), nullable=True))
        op.create_foreign_key('fk_user_reports_post_id', 'user_reports', 'posts', ['post_id'], ['id'], ondelete='CASCADE')
        op.create_index(op.f('ix_user_reports_post_id'), 'user_reports', ['post_id'], unique=False)


def downgrade():
    bind = op.get_bind()
    if _column_exists(bind, 'user_reports', 'post_id'):
        op.drop_index(op.f('ix_user_reports_post_id'), table_name='user_reports')
        op.drop_constraint('fk_user_reports_post_id', 'user_reports', type_='foreignkey')
        op.drop_column('user_reports', 'post_id')
