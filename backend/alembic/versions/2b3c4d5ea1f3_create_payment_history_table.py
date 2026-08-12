"""create payment_history table and add payment methods to user_subscriptions

Revision ID: 2b3c4d5ea1f3
Revises: 2b3c4d5ea1f2
Create Date: 2026-08-12 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2b3c4d5ea1f3'
down_revision = '2b3c4d5ea1f2'
branch_labels = None
depends_on = None

def upgrade():
    # add payment methods to user_subscriptions
    op.add_column('user_subscriptions', sa.Column('payment_method_brand', sa.String(length=50), nullable=True))
    op.add_column('user_subscriptions', sa.Column('payment_method_last4', sa.String(length=4), nullable=True))

    # create payment_history table
    op.create_table('payment_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('invoice_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_history_id'), 'payment_history', ['id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_payment_history_id'), table_name='payment_history')
    op.drop_table('payment_history')
    op.drop_column('user_subscriptions', 'payment_method_last4')
    op.drop_column('user_subscriptions', 'payment_method_brand')
