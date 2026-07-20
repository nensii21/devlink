"""add user badges

Revision ID: 1a2b3c4d5e6f
Revises: 7a9e8f1d2c3b
Create Date: 2026-07-20 17:35:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '7a9e8f1d2c3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('badges', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'badges')
