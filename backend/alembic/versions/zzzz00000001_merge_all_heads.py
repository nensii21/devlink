"""merge the migration graph back to a single head

``alembic upgrade head`` cannot resolve a target while more than one head
exists, so a multi-head graph is not a tidiness problem -- it is a broken
deploy. CI enforces a single head, and the check has been failing for every
branch that touches a migration.

This was #926, which was closed after collapsing eleven heads. It regressed
the same way it happened the first time: several feature branches each added a
migration chained off whatever was current when they branched, and merging
them produced siblings rather than a chain. There are five again:

    366aca8c8494          add_connections_table
    a1b2c3d4e5f8          add delivered_at to messages
    ea6d6738e0b0          add owner_id to project_milestones
    ffff00000004          add collaboration status to user
    video_intro_url_001   add video introduction url columns to users

A merge revision is the right tool here rather than rewriting any of their
``down_revision`` pointers: the five are genuinely independent -- they touch
different tables and can be applied in any order -- and rewriting history that
has already been applied to a database would strand every environment that has
run one of them.

Nothing is created or dropped here. It exists purely so the graph has one
head again.

Revision ID: zzzz00000001
Revises: 366aca8c8494, a1b2c3d4e5f8, ea6d6738e0b0, ffff00000004, video_intro_url_001
Create Date: 2026-08-16
"""

from typing import Sequence, Union

revision: str = "zzzz00000001"
down_revision: Union[str, Sequence[str], None] = (
    "ea6d6738e0b0",
    "video_intro_url_001",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: this revision only rejoins the graph."""


def downgrade() -> None:
    """No-op: see :func:`upgrade`."""
