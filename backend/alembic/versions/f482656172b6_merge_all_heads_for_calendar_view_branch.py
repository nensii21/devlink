"""Merge all heads for calendar view branch

Revision ID: f482656172b6
Revises: 1a2b3c4d5ea1, 366aca8c8494, a1b2c3d4e5f8, voice_intro_url_001, ffff00000004
Create Date: 2026-08-15 18:48:50.384511

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f482656172b6"
down_revision: Union[str, Sequence[str], None] = (
    "1a2b3c4d5ea1",
    "366aca8c8494",
    "a1b2c3d4e5f8",
    "voice_intro_url_001",
    "ffff00000004",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
