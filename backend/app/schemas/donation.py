import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DonationCreate(BaseModel):
    """
    A request to open a Checkout Session.

    ``amount`` is in cents and is bounded here rather than only at Stripe.
    Without the bound, a request with a nonsensical amount still writes a
    pending ``Donation`` row before Stripe ever sees it and rejects it -- an
    unauthenticated endpoint that leaves rows behind on every invalid call.
    The floor matches Stripe's own minimum charge.
    """

    recipient_id: uuid.UUID
    amount: int = Field(
        ...,
        ge=50,
        le=1_000_000,
        description="Donation amount in cents (minimum 50, maximum 1,000,000).",
    )
    message: Optional[str] = Field(default=None, max_length=500)

    @field_validator("message")
    @classmethod
    def _strip_message(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class DonationResponse(BaseModel):
    id: uuid.UUID
    donor_id: Optional[uuid.UUID] = None
    recipient_id: uuid.UUID
    amount: int
    currency: str
    status: str
    message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
