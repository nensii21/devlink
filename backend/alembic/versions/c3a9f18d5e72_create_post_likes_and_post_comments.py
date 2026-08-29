"""create posts, post_likes and post_comments tables

`Post` carried `likes_count` and `comments_count` and nothing else, so a like
had no owner and a comment had no body. `post_likes` and `post_comments` give
both a home; the unique constraint on (post_id, user_id) is what makes liking
idempotent.

`posts` is here because it turned out not to exist. No migration has ever
created it -- the model, the router and the frontend feed were all built on a
table that only appears when `Base.metadata.create_all` runs, which is to say
in the test suite and nowhere else. It is one of 36 such tables (#1408); this
migration creates the one it needs a foreign key to, and leaves the rest.

Revision ID: c3a9f18d5e72
Revises: 847b3a909e4c
Create Date: 2026-08-28 11:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "c3a9f18d5e72"
down_revision: Union[str, Sequence[str], None] = "847b3a909e4c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    """Whether `name` already exists, so this migration is safe to run against
    a schema that was built by `create_all` rather than by the chain."""
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    # `posts` has no migration of its own (#1408). Created here with
    # `checkfirst` semantics -- an environment whose schema came from
    # `create_all` already has it, and re-creating it would fail.
    if not _has_table("posts"):
        op.create_table(
            "posts",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column(
                "author_id",
                UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("content", sa.Text(), nullable=False),
            # `'{}'`, not `'[]'`: this is a Postgres `text[]`, whose empty
            # literal is braces. The model spells the default `"[]"` because
            # its SQLite variant is JSON, where that is the right empty value.
            sa.Column(
                "tags",
                postgresql.ARRAY(sa.String()),
                server_default=sa.text("'{}'::text[]"),
                nullable=False,
            ),
            sa.Column(
                "likes_count", sa.Integer(), server_default="0", nullable=False
            ),
            sa.Column(
                "comments_count", sa.Integer(), server_default="0", nullable=False
            ),
            sa.Column(
                "status",
                sa.String(length=20),
                server_default="published",
                nullable=False,
            ),
            sa.Column("publish_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index("ix_posts_author_id", "posts", ["author_id"])
        op.create_index("ix_posts_status", "posts", ["status"])
        op.create_index("ix_posts_created_at", "posts", ["created_at"])

    op.create_table(
        "post_likes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "post_id",
            UUID(as_uuid=True),
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # The database enforces "one like per user per post", rather than a
        # SELECT in the handler, so two concurrent likes cannot both pass.
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_likes_post_user"),
    )
    op.create_index("ix_post_likes_post_id", "post_likes", ["post_id"])
    op.create_index("ix_post_likes_user_id", "post_likes", ["user_id"])

    op.create_table(
        "post_comments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "post_id",
            UUID(as_uuid=True),
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_post_comments_post_id", "post_comments", ["post_id"])
    op.create_index("ix_post_comments_author_id", "post_comments", ["author_id"])
    op.create_index("ix_post_comments_created_at", "post_comments", ["created_at"])

    # The counters were maintained by hand and could not be trusted, so
    # rebuild them from the rows that now exist. Both tables are empty at this
    # point, which is the correct answer: nothing was ever recorded.
    op.execute("UPDATE posts SET likes_count = 0, comments_count = 0")


def downgrade() -> None:
    op.drop_index("ix_post_comments_created_at", table_name="post_comments")
    op.drop_index("ix_post_comments_author_id", table_name="post_comments")
    op.drop_index("ix_post_comments_post_id", table_name="post_comments")
    op.drop_table("post_comments")

    op.drop_index("ix_post_likes_user_id", table_name="post_likes")
    op.drop_index("ix_post_likes_post_id", table_name="post_likes")
    op.drop_table("post_likes")

    # `posts` predates this migration in any environment built by
    # `create_all`, so dropping it on the way down would remove something this
    # revision did not necessarily create. It is dropped only if this
    # migration is what put it there -- which, on a chain-built database, it
    # is.
    if _has_table("posts"):
        op.drop_index("ix_posts_created_at", table_name="posts")
        op.drop_index("ix_posts_status", table_name="posts")
        op.drop_index("ix_posts_author_id", table_name="posts")
        op.drop_table("posts")
