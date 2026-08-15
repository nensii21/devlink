"""create project_calendar_events table

Revision ID: 1a2b3c4d5ea1
Revises: ea6d6738e0b0
Create Date: 2026-08-12 20:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5ea1'
down_revision = 'ea6d6738e0b0'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('project_calendar_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_calendar_events_project_id'), 'project_calendar_events', ['project_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_project_calendar_events_project_id'), table_name='project_calendar_events')
    op.drop_table('project_calendar_events')
