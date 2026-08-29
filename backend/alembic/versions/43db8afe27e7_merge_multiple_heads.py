"""merge_multiple_heads

Revision ID: 43db8afe27e7
Revises: 1003a1b2c3d4, 1db933f16507, 86ea2ebe9a06, c17b9c709b6c, f482656172b6
Create Date: 2026-08-26 10:46:29.640706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43db8afe27e7'
down_revision: Union[str, Sequence[str], None] = ('1003a1b2c3d4', '1db933f16507', '86ea2ebe9a06', 'c17b9c709b6c', 'f482656172b6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
