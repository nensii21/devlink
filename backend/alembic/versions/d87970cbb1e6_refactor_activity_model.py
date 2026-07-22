"""Refactor Activity model

Revision ID: d87970cbb1e6
Revises: 7a9e8f1d2c3b
Create Date: 2026-07-20 16:43:20.665761

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d87970cbb1e6"
down_revision: Union[str, Sequence[str], None] = "7a9e8f1d2c3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old foreign keys
    op.drop_constraint("activities_project_id_fkey", "activities", type_="foreignkey")
    op.drop_constraint(
        "activities_organization_id_fkey", "activities", type_="foreignkey"
    )
    op.drop_constraint(
        "activities_repository_id_fkey", "activities", type_="foreignkey"
    )
    op.drop_constraint(
        "activities_application_id_fkey", "activities", type_="foreignkey"
    )
    op.drop_constraint(
        "activities_builder_flare_id_fkey", "activities", type_="foreignkey"
    )

    op.drop_column("activities", "project_id")
    op.drop_column("activities", "organization_id")
    op.drop_column("activities", "repository_id")
    op.drop_column("activities", "application_id")
    op.drop_column("activities", "builder_flare_id")

    # Add new generic columns
    op.add_column("activities", sa.Column("target_id", sa.UUID(), nullable=True))
    op.add_column(
        "activities", sa.Column("target_type", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "activities",
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )

    # Create indexes
    op.create_index(
        op.f("ix_activities_target_id"), "activities", ["target_id"], unique=False
    )
    op.create_index(
        op.f("ix_activities_target_type"), "activities", ["target_type"], unique=False
    )
    op.create_index(
        op.f("ix_activities_created_at"), "activities", ["created_at"], unique=False
    )
    op.create_index(
        "ix_activities_type_created",
        "activities",
        ["activity_type", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_activities_activity_type"),
        "activities",
        ["activity_type"],
        unique=False,
    )

    # Note: For Enum, since we added 'project_milestone', 'team_invitation', 'comment_created', 'discussion_created',
    # we need to alter the enum type in postgres.
    op.execute("ALTER TYPE activitytype ADD VALUE IF NOT EXISTS 'project_milestone'")
    op.execute("ALTER TYPE activitytype ADD VALUE IF NOT EXISTS 'team_invitation'")
    op.execute("ALTER TYPE activitytype ADD VALUE IF NOT EXISTS 'comment_created'")
    op.execute("ALTER TYPE activitytype ADD VALUE IF NOT EXISTS 'discussion_created'")


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_activities_type_created", table_name="activities")
    op.drop_index(op.f("ix_activities_created_at"), table_name="activities")
    op.drop_index(op.f("ix_activities_target_type"), table_name="activities")
    op.drop_index(op.f("ix_activities_target_id"), table_name="activities")
    op.drop_index(op.f("ix_activities_activity_type"), table_name="activities")

    # Drop new columns
    op.drop_column("activities", "metadata")
    op.drop_column("activities", "target_type")
    op.drop_column("activities", "target_id")

    # Add old columns
    op.add_column(
        "activities",
        sa.Column("builder_flare_id", sa.UUID(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "activities",
        sa.Column("application_id", sa.UUID(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "activities",
        sa.Column("repository_id", sa.UUID(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "activities",
        sa.Column("organization_id", sa.UUID(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "activities",
        sa.Column("project_id", sa.UUID(), autoincrement=False, nullable=True),
    )

    op.create_foreign_key(
        "activities_builder_flare_id_fkey",
        "activities",
        "builder_flares",
        ["builder_flare_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "activities_application_id_fkey",
        "activities",
        "applications",
        ["application_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "activities_repository_id_fkey",
        "activities",
        "repositories",
        ["repository_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "activities_organization_id_fkey",
        "activities",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "activities_project_id_fkey",
        "activities",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )
