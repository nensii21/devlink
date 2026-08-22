"""add background jobs

Revision ID: b3b8e5c2e123
Revises: a1b2c3d4e5f7, f6a7b8c9d0e1
Create Date: 2026-08-03 23:25:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b3b8e5c2e123"
down_revision: Union[str, Sequence[str], None] = ("a1b2c3d4e5f7", "f6a7b8c9d0e1")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "background_jobs",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("task_name", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "running", "completed", "failed", "retry", name="jobstatus"
            ),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("queue", sa.String(length=100), nullable=True),
        sa.Column("worker", sa.String(length=255), nullable=True),
        sa.Column("retries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processing_time", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_background_jobs_task_name"),
        "background_jobs",
        ["task_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_background_jobs_status"), "background_jobs", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_background_jobs_created_at"),
        "background_jobs",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_background_jobs_created_at"), table_name="background_jobs")
    op.drop_index(op.f("ix_background_jobs_status"), table_name="background_jobs")
    op.drop_index(op.f("ix_background_jobs_task_name"), table_name="background_jobs")
    op.drop_table("background_jobs")

    # Drop enum if postgresql
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('DROP TYPE IF EXISTS jobstatus')
