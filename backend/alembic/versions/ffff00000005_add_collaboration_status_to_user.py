"""add collaboration status to user

Revision ID: ffff00000005
Revises: 366aca8c8494
Create Date: 2026-08-13 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ffff00000005"
down_revision = "366aca8c8494"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # add collaboration status column to users table
    op.add_column(
        "users",
        sa.Column(
            "collaboration_status",
            sa.String(40),
            nullable=True,
            server_default="available",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "collaboration_status")
