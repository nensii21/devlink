"""merge multiple heads

Revision ID: 847b3a909e4c
Revises: 3570094ccd90, a3f7c1d29b48, b7e4d2f8c916
Create Date: 2026-08-27 21:26:51.687796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '847b3a909e4c'
down_revision: Union[str, Sequence[str], None] = ('3570094ccd90', 'a3f7c1d29b48', 'b7e4d2f8c916')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
