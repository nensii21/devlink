"""add draft fields to projects

Revision ID: a3b4c5d6e7f8
Revises: e1d173dca5be
Create Date: 2026-07-22 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, Sequence[str], None] = "e1d173dca5be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_draft and last_draft_save columns to projects table."""
    op.add_column(
        "projects",
        sa.Column(
            "is_draft",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "last_draft_save",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_projects_is_draft"),
        "projects",
        ["is_draft"],
        unique=False,
    )


def downgrade() -> None:
    """Remove draft fields from projects table."""
    op.drop_index(op.f("ix_projects_is_draft"), table_name="projects")
    op.drop_column("projects", "last_draft_save")
    op.drop_column("projects", "is_draft")
