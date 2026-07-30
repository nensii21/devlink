"""Add issues and duplicate_suggestions tables

Revision ID: b2e4f6a8c0d1
Revises: 1a2b3c4d5e6f
Create Date: 2026-07-22

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = "b2e4f6a8c0d1"
down_revision = "1a2b3c4d5e6f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create issues table
    op.create_table(
        "issues",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "author_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("open", "in_progress", "closed", "duplicate", name="issuestatus"),
            nullable=False,
            server_default="open",
            index=True,
        ),
        sa.Column(
            "priority",
            sa.Enum("low", "medium", "high", "critical", name="issuepriority"),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("labels", sa.String(500), nullable=True),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column(
            "is_duplicate_checked", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            index=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Create duplicate_suggestions table
    op.create_table(
        "duplicate_suggestions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_issue_id",
            UUID(as_uuid=True),
            sa.ForeignKey("issues.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "duplicate_issue_id",
            UUID(as_uuid=True),
            sa.ForeignKey("issues.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("duplicate_suggestions")
    op.drop_table("issues")
    op.execute("DROP TYPE IF EXISTS issuestatus")
    op.execute("DROP TYPE IF EXISTS issuepriority")
