from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user_optional, get_database
from app.models.user import User
from app.schemas.donation import CheckoutSessionResponse, DonationCreate
from app.services.donation_service import (
    DonationService,
    PaymentDiscrepancy,
    StripeNotConfigured,
    WebhookVerificationError,
)

router = APIRouter(prefix="/donations", tags=["Donations"])


@router.post("/checkout", response_model=CheckoutSessionResponse)
def create_checkout_session(
    donation_data: DonationCreate,
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_current_user_optional),
):
    donor_id = current_user.id if current_user else None
    try:
        url = DonationService.create_checkout_session(db, donation_data, donor_id)
    except StripeNotConfigured as exc:
        # An operator problem, not a caller problem. 503 says "come back
        # later"; the previous 500 said "your request was broken".
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Donations are not currently available.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create checkout session",
        ) from exc

    return CheckoutSessionResponse(checkout_url=url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_database)):
    """
    Receive a Stripe webhook delivery.

    Unauthenticated by necessity -- Stripe has no credential to present -- so
    the signature check inside ``handle_webhook`` is the whole boundary. The
    status codes matter here beyond the usual reasons, because Stripe reads
    them: a 4xx stops the retries, a 5xx keeps them coming.

      * 400 -- we will never accept this request. Stop retrying.
      * 409 -- verified, but it contradicts our records. Needs a human, so
        stop retrying and surface it.
      * 503 -- we cannot verify anything right now. Retrying is right.
    """
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature header",
        )

    try:
        outcome = DonationService.handle_webhook(db, payload, sig_header)
    except StripeNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook processing is not configured.",
        ) from exc
    except PaymentDiscrepancy as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except WebhookVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {"status": "success", "outcome": outcome}
