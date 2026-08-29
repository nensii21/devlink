"""Add interview tracking to applications

Revision ID: 1004a1b2c3d4
Revises: zzzz00000001
Create Date: 2026-08-22 17:25:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1004a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "zzzz00000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to applications
    op.add_column(
        "applications",
        sa.Column(
            "interview_scheduled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "applications",
        sa.Column(
            "interview_link",
            sa.String(length=500),
            nullable=True,
        ),
    )

    # Add 'interviewing' to ApplicationStatus enum
    op.execute("ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'interviewing'")


def downgrade() -> None:
    # Drop new columns
    op.drop_column("applications", "interview_link")
    op.drop_column("applications", "interview_scheduled_at")

    # We cannot easily drop a value from an enum type in PostgreSQL
    # so we leave the enum as is.
