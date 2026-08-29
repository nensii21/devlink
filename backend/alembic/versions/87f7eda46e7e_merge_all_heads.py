"""merge all heads

Revision ID: 87f7eda46e7e
Revises: 622221f708e8, b6d3f2a71c48, c8f4a1e93b27, d9e2b7c4f183, e7c1a9b45d20, ffff00000004
Create Date: 2026-08-12 11:45:42.204495

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "87f7eda46e7e"
down_revision: Union[str, Sequence[str], None] = (
    "622221f708e8",
    "b6d3f2a71c48",
    "c8f4a1e93b27",
    "d9e2b7c4f183",
    "e7c1a9b45d20",
    "ffff00000004",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
