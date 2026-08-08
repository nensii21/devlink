"""merge background jobs and microsoft id heads

Revision ID: c9a1f2b3d4e5
Revises: b3b8e5c2e123, ffff00000002
Create Date: 2026-08-06 15:10:00.000000

The graph forked immediately after the ten-way merge at ffff00000001.
ffff00000002 was written on top of that merge point, while b3b8e5c2e123 was
written on top of two of the branches feeding into it, so neither author saw
the other's revision and `alembic upgrade head` stopped resolving.

This revision only rejoins the two heads. It intentionally contains no schema
operations, which is what makes it safe to apply to a database that has
already run either branch.

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "c9a1f2b3d4e5"
down_revision: Union[str, Sequence[str], None] = ("b3b8e5c2e123", "ffff00000002")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: this revision exists to collapse two heads into one."""


def downgrade() -> None:
    """No-op: downgrading past this point re-opens the two original branches."""
