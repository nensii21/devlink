"""Merge heads for emoji reactions branch

Revision ID: 1b25791a33de
Revises: 366aca8c8494, a1b2c3d4e5f8, voice_intro_url_001, ffff00000004, ffff00000005
Create Date: 2026-08-15 18:53:41.527220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b25791a33de'
down_revision: Union[str, Sequence[str], None] = ('366aca8c8494', 'a1b2c3d4e5f8', 'voice_intro_url_001', 'ffff00000004', 'ffff00000005')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
