"""Add profile view features

Revision ID: zzzz00000002
Revises: zzzz00000001
Create Date: 2026-08-26 15:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'zzzz00000002'
down_revision = ('a3f7c1d29b48', 'b7e4d2f8c916')
branch_labels = None
depends_on = None

def _table_exists(bind, table_name) -> bool:
    return table_name in inspect(bind).get_table_names()

def _column_exists(bind, table_name, column_name) -> bool:
    return column_name in {c["name"] for c in inspect(bind).get_columns(table_name)}

def upgrade() -> None:
    bind = op.get_bind()

    # Handle profile_views table
    if not _table_exists(bind, 'profile_views'):
        op.create_table(
            'profile_views',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('viewed_user_id', UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column('viewer_id', UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column('is_anonymous', sa.Boolean(), nullable=False, default=False),
            sa.Column('visit_count', sa.Integer(), nullable=False, default=1),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"))
        )
        op.create_index('ix_profile_views_viewed_user_id', 'profile_views', ['viewed_user_id'])
        op.create_index('ix_profile_views_viewer_id', 'profile_views', ['viewer_id'])
        op.create_index('ix_profile_views_created_at', 'profile_views', ['created_at'])
        op.create_index('idx_profile_view_target_time', 'profile_views', ['viewed_user_id', 'created_at'])
        op.create_index('idx_profile_view_unique_recent', 'profile_views', ['viewed_user_id', 'viewer_id'])
    else:
        if not _column_exists(bind, 'profile_views', 'visit_count'):
            op.add_column('profile_views', sa.Column('visit_count', sa.Integer(), nullable=True))
            op.execute("UPDATE profile_views SET visit_count = 1")
            op.alter_column('profile_views', 'visit_count', nullable=False)
            
    # Add hide_profile_views to users
    if not _column_exists(bind, 'users', 'hide_profile_views'):
        op.add_column('users', sa.Column('hide_profile_views', sa.Boolean(), nullable=True))
        op.execute("UPDATE users SET hide_profile_views = FALSE")
        op.alter_column('users', 'hide_profile_views', nullable=False)

def downgrade() -> None:
    bind = op.get_bind()
    
    if _column_exists(bind, 'users', 'hide_profile_views'):
        op.drop_column('users', 'hide_profile_views')
        
    if _table_exists(bind, 'profile_views'):
        op.drop_table('profile_views')
