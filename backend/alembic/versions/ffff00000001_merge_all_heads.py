"""Merge all branch heads into a single head

Revision ID: ffff00000001
Revises: 4b4c96034900, 523764cd8096, a1b2c3d4e5f6, a2c5d3f7e1b4, b2e4f6a8c0d1, b7f6e5d4c3a2, c5d6e7f8a9b0, d87970cbb1e6, f1b4a3a6b5c7
Create Date: 2026-07-28

"""

from typing import Sequence, Union

revision: str = "ffff00000001"
down_revision: Union[str, Sequence[str], None] = (
    "4b4c96034900",
    "523764cd8096",
    "a1b2c3d4e5f6",
    "a2c5d3f7e1b4",
    "b2e4f6a8c0d1",
    "b7f6e5d4c3a2",
    "c5d6e7f8a9b0",
    "d87970cbb1e6",
    "f1b4a3a6b5c7",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
