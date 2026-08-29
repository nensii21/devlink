from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class StripeWebhookEvent(Base):
    """
    One row per Stripe event id we have finished processing.

    Stripe retries a webhook delivery until it gets a 2xx, for up to three
    days, and it makes no promise of delivering an event only once even after
    that. Without a record of what has already been handled, a retry runs the
    handler a second time: the donation is marked completed again and the
    recipient is notified again.

    The event id is the primary key, so a concurrent duplicate delivery loses
    the insert on the unique constraint rather than racing through the handler
    alongside the first one.
    """

    __tablename__ = "stripe_webhook_events"

    event_id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # The donation the event resolved to, when it resolved to one. Kept for
    # support questions ("we never got the notification for this payment"),
    # not read by the handler.
    donation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<StripeWebhookEvent(event_id='{self.event_id}', "
            f"event_type='{self.event_type}')>"
        )
