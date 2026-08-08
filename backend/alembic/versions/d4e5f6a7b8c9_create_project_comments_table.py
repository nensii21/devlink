"""create project comments table

Revision ID: d4e5f6a7b8c9
Revises: c9a1f2b3d4e5
Create Date: 2026-08-06 16:40:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c9a1f2b3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_comments",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", UUID(as_uuid=True), nullable=False),
        # Null for a top-level comment. Self-referential, one level deep --
        # the service reparents a reply-to-a-reply onto its grandparent.
        sa.Column("parent_id", UUID(as_uuid=True), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "is_edited", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        # Soft delete: a removed comment is tombstoned rather than erased so
        # that replies underneath keep their parent.
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by_id", UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["project_comments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["deleted_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_project_comments_project_id"),
        "project_comments",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_comments_author_id"),
        "project_comments",
        ["author_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_comments_parent_id"),
        "project_comments",
        ["parent_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_comments_deleted_at"),
        "project_comments",
        ["deleted_at"],
        unique=False,
    )

    # The listing query: top-level comments for one project, newest first.
    op.create_index(
        "ix_project_comments_project_created",
        "project_comments",
        ["project_id", "created_at"],
        unique=False,
    )
    # Fetching the replies for a page of top-level comments.
    op.create_index(
        "ix_project_comments_parent_created",
        "project_comments",
        ["parent_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_project_comments_parent_created", table_name="project_comments")
    op.drop_index("ix_project_comments_project_created", table_name="project_comments")
    op.drop_index(op.f("ix_project_comments_deleted_at"), table_name="project_comments")
    op.drop_index(op.f("ix_project_comments_parent_id"), table_name="project_comments")
    op.drop_index(op.f("ix_project_comments_author_id"), table_name="project_comments")
    op.drop_index(op.f("ix_project_comments_project_id"), table_name="project_comments")
    op.drop_table("project_comments")
