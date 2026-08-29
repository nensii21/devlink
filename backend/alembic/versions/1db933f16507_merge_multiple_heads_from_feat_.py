"""Merge multiple heads from feat/organization-roles-987-v2

Revision ID: 1db933f16507
Revises: 5854bc656348, f3a7b1c2d9e0
Create Date: 2026-08-21 11:38:26.950333

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "1db933f16507"
down_revision: Union[str, Sequence[str], None] = ("5854bc656348", "f3a7b1c2d9e0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
