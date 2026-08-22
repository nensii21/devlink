"""merge availability and messaging heads

Revision ID: c17b9c709b6c
Revises: 404be10112ad, f3a7b1c2d9e0
Create Date: 2026-08-21 11:47:39.923321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c17b9c709b6c'
down_revision: Union[str, Sequence[str], None] = ('404be10112ad', 'f3a7b1c2d9e0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
