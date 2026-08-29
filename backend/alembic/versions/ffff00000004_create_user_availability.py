"""create_user_availability

Revision ID: ffff00000004
Revises: ffff00000003
Create Date: 2026-08-12 10:45:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ffff00000004"
down_revision = "ffff00000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_availability",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timezone", sa.String(), nullable=False, server_default="UTC"),
        sa.Column(
            "working_hours",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "meeting_duration", sa.Integer(), server_default="30", nullable=False
        ),
        sa.Column(
            "vacation_mode", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column("vacation_start", sa.Date(), nullable=True),
        sa.Column("vacation_end", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_availability")
