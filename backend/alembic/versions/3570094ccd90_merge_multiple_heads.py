"""merge_multiple_heads

Revision ID: 3570094ccd90
Revises: 6e20f3f5e34f
Create Date: 2026-08-26 10:51:33.963121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3570094ccd90'
down_revision: Union[str, Sequence[str], None] = '6e20f3f5e34f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
