"""create project milestones table

The Milestone model (#618) shipped without a migration. Nothing caught it
because the test suite builds its schema with ``Base.metadata.create_all``,
which reads the models directly and never touches the revision chain -- so
``project_milestones`` exists in every test run and in no migrated database.

This revision closes that gap. It is a prerequisite for #1041, whose time logs
reference milestones, but the missing table is a bug on its own.

Revision ID: f2a8c61d97b5
Revises: d4e5f6a7b8c9
Create Date: 2026-08-10 22:05:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "f2a8c61d97b5"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # checkfirst is not available on create_table, so guard on the inspector:
    # an environment that was bootstrapped with create_all already has this
    # table and must not fail here.
    bind = op.get_bind()
    if sa.inspect(bind).has_table("project_milestones"):
        return

    op.create_table(
        "project_milestones",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_completed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_archived", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_project_milestones_project_id"),
        "project_milestones",
        ["project_id"],
        unique=False,
    )
    # The timeline query: one project's milestones ordered by when they are due.
    op.create_index(
        "ix_project_milestones_project_due",
        "project_milestones",
        ["project_id", "due_date"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("project_milestones"):
        return

    op.drop_index("ix_project_milestones_project_due", table_name="project_milestones")
    op.drop_index(
        op.f("ix_project_milestones_project_id"), table_name="project_milestones"
    )
    op.drop_table("project_milestones")
