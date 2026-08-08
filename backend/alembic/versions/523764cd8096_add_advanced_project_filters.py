"""add advanced project filters

Revision ID: 523764cd8096
Revises: 3d3fd43150c1
Create Date: 2026-07-25 10:15:00.000000

This revision was originally authored with `down_revision = None`, which made
it a second root of the graph rather than a link in the chain. Every operation
below alters `projects`, a table created by 3d3fd43150c1, but nothing recorded
that ordering. Alembic topologically sorts disconnected roots, and the sort
happened to place this one late enough to work -- that was luck, not a
guarantee, and a future revision that perturbs the sort would turn it into
`relation "projects" does not exist` on a fresh database.

Reparenting onto 3d3fd43150c1 states the real dependency. The revision id is
unchanged, so environments that already applied it keep their alembic_version
row and nothing re-runs.

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "523764cd8096"
down_revision: Union[str, Sequence[str], None] = "3d3fd43150c1"
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
