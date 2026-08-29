"""merge main and resolve conflicts

Revision ID: 5854bc656348
Revises: 30a41d646a74, ea6d6738e0b0
Create Date: 2026-08-17 15:17:41.449811

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "5854bc656348"
down_revision: Union[str, Sequence[str], None] = ("30a41d646a74", "ea6d6738e0b0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
