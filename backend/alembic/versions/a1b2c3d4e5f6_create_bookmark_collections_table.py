"""Create bookmark collections and collection_bookmarks tables

Revision ID: a1b2c3d4e5f6
Revises: 7a9e8f1d2c3b
Create Date: 2026-07-20 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "7a9e8f1d2c3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "bookmark_collections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column(
            "is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_user_collection_name"),
    )
    op.create_index(
        op.f("ix_bookmark_collections_user_id"),
        "bookmark_collections",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "collection_bookmarks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("collection_id", sa.UUID(), nullable=False),
        sa.Column("bookmark_id", sa.UUID(), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["bookmark_id"], ["bookmarks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["collection_id"], ["bookmark_collections.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "collection_id", "bookmark_id", name="uq_collection_bookmark"
        ),
    )
    op.create_index(
        op.f("ix_collection_bookmarks_collection_id"),
        "collection_bookmarks",
        ["collection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_collection_bookmarks_bookmark_id"),
        "collection_bookmarks",
        ["bookmark_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_collection_bookmarks_bookmark_id"), table_name="collection_bookmarks"
    )
    op.drop_index(
        op.f("ix_collection_bookmarks_collection_id"), table_name="collection_bookmarks"
    )
    op.drop_table("collection_bookmarks")
    op.drop_index(
        op.f("ix_bookmark_collections_user_id"), table_name="bookmark_collections"
    )
    op.drop_table("bookmark_collections")
