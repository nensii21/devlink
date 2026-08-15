"""create pinned projects table

Revision ID: b6d3f2a71c48
Revises: d4e5f6a7b8c9
Create Date: 2026-08-10 20:40:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "b6d3f2a71c48"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pinned_projects",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        # 0-based and contiguous, compacted by the service on every removal.
        sa.Column(
            "position", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # One pin per project per user. Unlike position this never
        # legitimately collides, so it is safe to enforce here.
        sa.UniqueConstraint(
            "user_id", "project_id", name="uq_pinned_projects_user_project"
        ),
        sa.CheckConstraint("position >= 0", name="ck_pinned_projects_position"),
    )

    op.create_index(
        op.f("ix_pinned_projects_user_id"), "pinned_projects", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_pinned_projects_project_id"),
        "pinned_projects",
        ["project_id"],
        unique=False,
    )
    # The read path: one user's pins in display order.
    op.create_index(
        "ix_pinned_projects_user_position",
        "pinned_projects",
        ["user_id", "position"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_pinned_projects_user_position", table_name="pinned_projects")
    op.drop_index(op.f("ix_pinned_projects_project_id"), table_name="pinned_projects")
    op.drop_index(op.f("ix_pinned_projects_user_id"), table_name="pinned_projects")
    op.drop_table("pinned_projects")
