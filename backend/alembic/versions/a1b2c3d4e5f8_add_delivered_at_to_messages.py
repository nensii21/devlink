"""add delivered_at to messages

Revision ID: a1b2c3d4e5f8
Revises: ea6d6738e0ae
Create Date: 2026-08-14 12:26:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f8"
down_revision: Union[str, None] = "ffff00000005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "messages", sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        op.f("ix_messages_delivered_at"), "messages", ["delivered_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_messages_delivered_at"), table_name="messages")
    op.drop_column("messages", "delivered_at")
