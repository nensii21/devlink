"""Add resume_url to users

Revision ID: a2c5d3f7e1b4
Revises: f533805006ed
Create Date: 2026-07-05 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a2c5d3f7e1b4"
down_revision: Union[str, Sequence[str], None] = "f533805006ed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("resume_url", sa.String(length=500), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "resume_url")
