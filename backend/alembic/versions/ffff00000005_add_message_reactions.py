"""add message reactions

Revision ID: ffff00000005
Revises: ffff00000003
Create Date: 2026-08-12 11:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ffff00000005'
down_revision = 'ffff00000003'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'message_reactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('emoji', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id', 'user_id', 'emoji', name='uq_message_user_emoji')
    )
    op.create_index(op.f('ix_message_reactions_created_at'), 'message_reactions', ['created_at'], unique=False)
    op.create_index(op.f('ix_message_reactions_message_id'), 'message_reactions', ['message_id'], unique=False)
    op.create_index(op.f('ix_message_reactions_user_id'), 'message_reactions', ['user_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_message_reactions_user_id'), table_name='message_reactions')
    op.drop_index(op.f('ix_message_reactions_message_id'), table_name='message_reactions')
    op.drop_index(op.f('ix_message_reactions_created_at'), table_name='message_reactions')
    op.drop_table('message_reactions')
