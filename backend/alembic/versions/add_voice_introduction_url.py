"""add voice introduction url to users

Revision ID: voice_intro_url_001
Revises: ea6d6738e0ae
Create Date: 2026-08-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "voice_intro_url_001"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("voice_introduction_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "voice_introduction_url")
