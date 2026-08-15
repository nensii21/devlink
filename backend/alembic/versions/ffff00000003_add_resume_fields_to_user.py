"""add resume fields to user

Revision ID: ffff00000003
Revises: ffff00000002
Create Date: 2026-08-10 10:55:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ffff00000003"
down_revision = "ffff00000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # add json columns to users table
    op.add_column("users", sa.Column("experience", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("education", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("certifications", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "certifications")
    op.drop_column("users", "education")
    op.drop_column("users", "experience")
