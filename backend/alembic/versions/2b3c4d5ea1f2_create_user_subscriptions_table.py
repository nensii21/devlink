"""create user_subscriptions table

Revision ID: 2b3c4d5ea1f2
Revises: ea6d6738e0ae
Create Date: 2026-08-12 20:17:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2b3c4d5ea1f2'
down_revision = 'ea6d6738e0ae'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('user_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tier', sa.String(length=50), nullable=False, server_default='free'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_subscriptions_user_id'), 'user_subscriptions', ['user_id'], unique=True)

def downgrade():
    op.drop_index(op.f('ix_user_subscriptions_user_id'), table_name='user_subscriptions')
    op.drop_table('user_subscriptions')