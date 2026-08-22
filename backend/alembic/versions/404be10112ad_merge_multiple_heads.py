"""merge multiple heads

Revision ID: 404be10112ad
Revises: voice_intro_url_001, ea6d6738e0b0
Create Date: 2026-08-16 09:42:16.314622

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '404be10112ad'
down_revision: Union[str, Sequence[str], None] = ('voice_intro_url_001', 'ea6d6738e0b0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
