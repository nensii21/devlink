"""add delivered_at to messages

Revision ID: ffff00000004
Revises: ffff00000003
Create Date: 2026-08-12 10:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ffff00000004'
down_revision = 'ffff00000003'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('messages', sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_messages_delivered_at'), 'messages', ['delivered_at'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_messages_delivered_at'), table_name='messages')
    op.drop_column('messages', 'delivered_at')
