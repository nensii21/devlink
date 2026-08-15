"""create project time logs table

Revision ID: e7c1a9b45d20
Revises: f2a8c61d97b5
Create Date: 2026-08-10 20:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "e7c1a9b45d20"
down_revision: Union[str, Sequence[str], None] = "f2a8c61d97b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_time_logs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        # A milestone can be deleted while the work that went into it still
        # happened, so the log survives the milestone rather than cascading.
        sa.Column("milestone_id", UUID(as_uuid=True), nullable=True),
        # Whole minutes, not hours-as-float: summing floats across hundreds of
        # entries lets a summary drift away from its own line items.
        sa.Column("minutes", sa.Integer(), nullable=False),
        # The day the work happened, which is often not the day it was entered.
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column(
            "is_billable", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["milestone_id"], ["project_milestones.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        # Belt and braces alongside the service-level check: a single entry can
        # never be zero, negative, or longer than a day.
        sa.CheckConstraint(
            "minutes > 0 AND minutes <= 1440", name="ck_project_time_logs_minutes"
        ),
    )

    op.create_index(
        op.f("ix_project_time_logs_project_id"),
        "project_time_logs",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_time_logs_user_id"),
        "project_time_logs",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_time_logs_milestone_id"),
        "project_time_logs",
        ["milestone_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_time_logs_work_date"),
        "project_time_logs",
        ["work_date"],
        unique=False,
    )

    # The project report: everything logged on a project, by day.
    op.create_index(
        "ix_project_time_logs_project_date",
        "project_time_logs",
        ["project_id", "work_date"],
        unique=False,
    )
    # One person's history across their whole timeline.
    op.create_index(
        "ix_project_time_logs_user_date",
        "project_time_logs",
        ["user_id", "work_date"],
        unique=False,
    )
    # The 24-hour cap check, which reads one user's entries on one project for
    # one day and runs on every write.
    op.create_index(
        "ix_project_time_logs_project_user_date",
        "project_time_logs",
        ["project_id", "user_id", "work_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_project_time_logs_project_user_date", table_name="project_time_logs"
    )
    op.drop_index("ix_project_time_logs_user_date", table_name="project_time_logs")
    op.drop_index("ix_project_time_logs_project_date", table_name="project_time_logs")
    op.drop_index(
        op.f("ix_project_time_logs_work_date"), table_name="project_time_logs"
    )
    op.drop_index(
        op.f("ix_project_time_logs_milestone_id"), table_name="project_time_logs"
    )
    op.drop_index(op.f("ix_project_time_logs_user_id"), table_name="project_time_logs")
    op.drop_index(
        op.f("ix_project_time_logs_project_id"), table_name="project_time_logs"
    )
    op.drop_table("project_time_logs")
