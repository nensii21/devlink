"""create stripe webhook events table

Records the id of every Stripe webhook event we have finished processing, so
a redelivery is a no-op instead of a second completion and a second
notification. Stripe retries a delivery until it gets a 2xx, for up to three
days, so redeliveries are ordinary traffic rather than an edge case.

Revision ID: e1d7c9a4b620
Revises: 847b3a909e4c
Create Date: 2026-08-28 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "e1d7c9a4b620"
down_revision: Union[str, Sequence[str], None] = "847b3a909e4c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stripe_webhook_events",
        # Stripe's event id is the natural key. Making it the primary key
        # means a concurrent redelivery loses on the unique constraint rather
        # than racing an in-flight handler.
        sa.Column("event_id", sa.String(length=255), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("donation_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_stripe_webhook_events_donation_id",
        "stripe_webhook_events",
        ["donation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_stripe_webhook_events_donation_id",
        table_name="stripe_webhook_events",
    )
    op.drop_table("stripe_webhook_events")
