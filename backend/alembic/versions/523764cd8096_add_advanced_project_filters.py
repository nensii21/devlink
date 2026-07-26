"""add advanced project filters

Revision ID: 523764cd8096
Revises:
Create Date: 2026-07-25 10:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "523764cd8096"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects", sa.Column("language", sa.String(length=100), nullable=True)
    )
    op.create_index(
        op.f("ix_projects_language"), "projects", ["language"], unique=False
    )
    op.add_column(
        "projects", sa.Column("experience", sa.String(length=50), nullable=True)
    )
    op.create_index(
        op.f("ix_projects_experience"), "projects", ["experience"], unique=False
    )
    op.add_column(
        "projects",
        sa.Column("is_remote", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index(
        op.f("ix_projects_is_remote"), "projects", ["is_remote"], unique=False
    )
    op.add_column(
        "projects",
        sa.Column("is_paid", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index(op.f("ix_projects_is_paid"), "projects", ["is_paid"], unique=False)
    op.add_column(
        "projects",
        sa.Column(
            "is_open_source", sa.Boolean(), server_default="false", nullable=False
        ),
    )
    op.create_index(
        op.f("ix_projects_is_open_source"), "projects", ["is_open_source"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_is_open_source"), table_name="projects")
    op.drop_column("projects", "is_open_source")
    op.drop_index(op.f("ix_projects_is_paid"), table_name="projects")
    op.drop_column("projects", "is_paid")
    op.drop_index(op.f("ix_projects_is_remote"), table_name="projects")
    op.drop_column("projects", "is_remote")
    op.drop_index(op.f("ix_projects_experience"), table_name="projects")
    op.drop_column("projects", "experience")
    op.drop_index(op.f("ix_projects_language"), table_name="projects")
    op.drop_column("projects", "language")
