"""unified notifications

Revision ID: a1b2c3d4e5f7
Revises: ffff00000001
Create Date: 2026-07-30 20:41:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, None] = "ffff00000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create notification_preferences table
    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "websocket_enabled", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "database_enabled", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "project_updates", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column("invitations", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("role_changes", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "marketing_emails", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("system_alerts", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_notification_preferences_user_id"),
        "notification_preferences",
        ["user_id"],
        unique=True,
    )

    # 2. Add columns to notifications
    # We must first create the types if they don't exist, but since it's an enum, we can just use VARCHAR for simplicity or create the ENUM.
    # Let's create the ENUMs
    notificationchannel = postgresql.ENUM(
        "DATABASE", "EMAIL", "WEBSOCKET", name="notificationchannel"
    )
    notificationchannel.create(op.get_bind())

    notificationstatus = postgresql.ENUM(
        "PENDING", "SENT", "FAILED", "READ", name="notificationstatus"
    )
    notificationstatus.create(op.get_bind())

    notificationpriority = postgresql.ENUM(
        "LOW", "NORMAL", "HIGH", "URGENT", name="notificationpriority"
    )
    notificationpriority.create(op.get_bind())

    op.add_column(
        "notifications",
        sa.Column(
            "channel",
            postgresql.ENUM(
                "DATABASE",
                "EMAIL",
                "WEBSOCKET",
                name="notificationchannel",
                create_type=False,
            ),
            server_default="DATABASE",
            nullable=False,
        ),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING",
                "SENT",
                "FAILED",
                "READ",
                name="notificationstatus",
                create_type=False,
            ),
            server_default="PENDING",
            nullable=False,
        ),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "priority",
            postgresql.ENUM(
                "LOW",
                "NORMAL",
                "HIGH",
                "URGENT",
                name="notificationpriority",
                create_type=False,
            ),
            server_default="NORMAL",
            nullable=False,
        ),
    )

    op.add_column(
        "notifications",
        sa.Column(
            "metadata_info", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    op.add_column(
        "notifications", sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "notifications",
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        op.f("ix_notifications_status"), "notifications", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_notifications_priority"), "notifications", ["priority"], unique=False
    )
    op.create_index(
        op.f("ix_notifications_read_at"), "notifications", ["read_at"], unique=False
    )

    # Add new values to NotificationType Enum
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'welcome'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'password_reset'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'role_change'")


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_read_at"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_priority"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_status"), table_name="notifications")

    op.drop_column("notifications", "scheduled_at")
    op.drop_column("notifications", "sent_at")
    op.drop_column("notifications", "metadata_info")
    op.drop_column("notifications", "priority")
    op.drop_column("notifications", "status")
    op.drop_column("notifications", "channel")

    op.execute("DROP TYPE IF EXISTS notificationpriority")
    op.execute("DROP TYPE IF EXISTS notificationstatus")
    op.execute("DROP TYPE IF EXISTS notificationchannel")

    op.drop_index(
        op.f("ix_notification_preferences_user_id"),
        table_name="notification_preferences",
    )
    op.drop_table("notification_preferences")
