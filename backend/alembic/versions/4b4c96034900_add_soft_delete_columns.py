"""Add soft delete columns

Revision ID: 4b4c96034900
Revises: c14aa06f723a
Create Date: 2026-07-08 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4b4c96034900"
down_revision: Union[str, Sequence[str], None] = "c14aa06f723a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # --- users ---
    op.add_column(
        "users",
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "deleted_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_users_deleted_by_id_users",
        "users",
        "users",
        ["deleted_by_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # --- projects ---
    op.add_column(
        "projects",
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "deleted_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_projects_deleted_by_id_users",
        "projects",
        "users",
        ["deleted_by_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # --- organizations ---
    op.add_column(
        "organizations",
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "organizations",
        sa.Column(
            "deleted_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_organizations_deleted_by_id_users",
        "organizations",
        "users",
        ["deleted_by_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""

    # --- organizations ---
    op.drop_constraint(
        "fk_organizations_deleted_by_id_users",
        "organizations",
        type_="foreignkey",
    )
    op.drop_column("organizations", "deleted_by_id")
    op.drop_column("organizations", "deleted_at")

    # --- projects ---
    op.drop_constraint(
        "fk_projects_deleted_by_id_users",
        "projects",
        type_="foreignkey",
    )
    op.drop_column("projects", "deleted_by_id")
    op.drop_column("projects", "deleted_at")

    # --- users ---
    op.drop_constraint(
        "fk_users_deleted_by_id_users",
        "users",
        type_="foreignkey",
    )
    op.drop_column("users", "deleted_by_id")
    op.drop_column("users", "deleted_at")
