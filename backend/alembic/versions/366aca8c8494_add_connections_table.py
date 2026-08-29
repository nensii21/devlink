"""add_connections_table

Revision ID: 366aca8c8494
Revises: 1ed7f3b882d0
Create Date: 2026-08-12

"""

from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "366aca8c8494"
down_revision = "87f7eda46e7e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "connections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("requester_id", sa.UUID(), nullable=False),
        sa.Column("recipient_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING", "ACCEPTED", "DECLINED", "WITHDRAWN", name="connectionstatus"
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("requester_id", "recipient_id", name="uq_connection_pair"),
    )
    op.create_index(
        op.f("ix_connections_recipient_id"),
        "connections",
        ["recipient_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_connections_requester_id"),
        "connections",
        ["requester_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_connections_status"), "connections", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_connections_status"), table_name="connections")
    op.drop_index(op.f("ix_connections_requester_id"), table_name="connections")
    op.drop_index(op.f("ix_connections_recipient_id"), table_name="connections")
    op.drop_table("connections")
    op.execute("DROP TYPE IF EXISTS connectionstatus")
