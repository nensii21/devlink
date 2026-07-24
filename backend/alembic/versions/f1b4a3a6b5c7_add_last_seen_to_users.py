"""add last_seen to users

Revision ID: f1b4a3a6b5c7
Revises: 398a2154b3d5
Create Date: 2026-07-14 17:58:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f1b4a3a6b5c7"
down_revision: Union[str, Sequence[str], None] = "398a2154b3d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_seen")
