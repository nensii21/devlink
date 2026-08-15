"""create project releases table

Revision ID: c8f4a1e93b27
Revises: d4e5f6a7b8c9
Create Date: 2026-08-10 21:05:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "c8f4a1e93b27"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# create_type=False: the types are created explicitly in upgrade() with
# checkfirst, so create_table must not try to emit CREATE TYPE a second time.
release_type_enum = postgresql.ENUM(
    "MAJOR",
    "MINOR",
    "PATCH",
    "PRERELEASE",
    name="releasetype",
    create_type=False,
)
release_status_enum = postgresql.ENUM(
    "DRAFT",
    "PUBLISHED",
    name="releasestatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    release_type_enum.create(bind, checkfirst=True)
    release_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "project_releases",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        # A release outlives the person who cut it, so the author reference is
        # nulled rather than cascading the row away.
        sa.Column("author_id", UUID(as_uuid=True), nullable=True),
        # Free-form on purpose: v1.2.0, 2026.08 and beta-3 are all legitimate.
        # Uniqueness per project is enforced case-insensitively in the service.
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "highlights", sa.JSON(), server_default=sa.text("'[]'"), nullable=False
        ),
        sa.Column("release_type", release_type_enum, nullable=False),
        sa.Column("status", release_status_enum, nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_pinned", sa.Boolean(), server_default=sa.text("false"), nullable=False
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
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_project_releases_project_id"),
        "project_releases",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_releases_author_id"),
        "project_releases",
        ["author_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_releases_status"), "project_releases", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_project_releases_published_at"),
        "project_releases",
        ["published_at"],
        unique=False,
    )

    # The public listing: one project's published releases, newest first.
    op.create_index(
        "ix_project_releases_project_published",
        "project_releases",
        ["project_id", "published_at"],
        unique=False,
    )
    # The duplicate-version check and the maintainer's draft list.
    op.create_index(
        "ix_project_releases_project_status",
        "project_releases",
        ["project_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_project_releases_project_status", table_name="project_releases")
    op.drop_index(
        "ix_project_releases_project_published", table_name="project_releases"
    )
    op.drop_index(
        op.f("ix_project_releases_published_at"), table_name="project_releases"
    )
    op.drop_index(op.f("ix_project_releases_status"), table_name="project_releases")
    op.drop_index(op.f("ix_project_releases_author_id"), table_name="project_releases")
    op.drop_index(op.f("ix_project_releases_project_id"), table_name="project_releases")
    op.drop_table("project_releases")

    bind = op.get_bind()
    release_status_enum.drop(bind, checkfirst=True)
    release_type_enum.drop(bind, checkfirst=True)
