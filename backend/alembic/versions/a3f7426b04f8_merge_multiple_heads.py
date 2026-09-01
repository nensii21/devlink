"""merge multiple heads

Revision ID: a3f7426b04f8
Revises: 1069a1b2c3d4, 1309a1b2c3d4, 1311a1b2c3d4, e3f9a2b5d312, e97619c62904
Create Date: 2026-08-31 16:19:22.240642

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f7426b04f8'
down_revision: Union[str, Sequence[str], None] = ('1069a1b2c3d4', '1309a1b2c3d4', '1311a1b2c3d4', 'e3f9a2b5d312', 'e97619c62904')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
