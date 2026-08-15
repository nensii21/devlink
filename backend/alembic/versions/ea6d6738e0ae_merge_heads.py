"""merge heads

Revision ID: ea6d6738e0ae
Revises: 622221f708e8, b6d3f2a71c48, c8f4a1e93b27, d9e2b7c4f183, e7c1a9b45d20, ffff00000003
Create Date: 2026-08-12 11:37:06.215795

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "ea6d6738e0ae"
down_revision: Union[str, Sequence[str], None] = (
    "622221f708e8",
    "b6d3f2a71c48",
    "c8f4a1e93b27",
    "d9e2b7c4f183",
    "e7c1a9b45d20",
    "ffff00000003",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
