"""Create donations table

Revision ID: 1003a1b2c3d4
Revises: 1004a1b2c3d4
Create Date: 2026-08-22 17:35:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1003a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "1004a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "donations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("donor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("stripe_session_id", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["donor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(
        op.f("ix_donations_donor_id"), "donations", ["donor_id"], unique=False
    )
    op.create_index(
        op.f("ix_donations_recipient_id"), "donations", ["recipient_id"], unique=False
    )
    op.create_index(op.f("ix_donations_status"), "donations", ["status"], unique=False)
    op.create_index(
        op.f("ix_donations_stripe_session_id"),
        "donations",
        ["stripe_session_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_donations_stripe_session_id"), table_name="donations")
    op.drop_index(op.f("ix_donations_status"), table_name="donations")
    op.drop_index(op.f("ix_donations_recipient_id"), table_name="donations")
    op.drop_index(op.f("ix_donations_donor_id"), table_name="donations")
    op.drop_table("donations")
