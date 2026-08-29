"""merge_multiple_heads

Revision ID: 6e20f3f5e34f
Revises: 1003a1b2c3d4, 1db933f16507, c17b9c709b6c, f482656172b6
Create Date: 2026-08-26 10:34:01.754445

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e20f3f5e34f'
down_revision: Union[str, Sequence[str], None] = ('1003a1b2c3d4', '1db933f16507', 'c17b9c709b6c', 'f482656172b6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
