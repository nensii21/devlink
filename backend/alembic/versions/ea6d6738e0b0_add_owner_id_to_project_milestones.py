"""add owner_id to project_milestones

Revision ID: ea6d6738e0b0
Revises: ea6d6738e0ae
Create Date: 2026-08-12 20:01:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ea6d6738e0b0"
down_revision = "ea6d6738e0ae"
down_revision = "f2a8c61d97b5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "project_milestones",
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f("ix_project_milestones_owner_id"),
        "project_milestones",
        ["owner_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_project_milestones_owner_id",
        "project_milestones",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "fk_project_milestones_owner_id", "project_milestones", type_="foreignkey"
    )
    op.drop_index(
        op.f("ix_project_milestones_owner_id"), table_name="project_milestones"
    )
    op.drop_column("project_milestones", "owner_id")
