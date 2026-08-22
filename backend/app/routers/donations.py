from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.dependencies import get_current_user, get_database, get_current_user_optional
from app.models.user import User
from app.schemas.donation import DonationCreate, CheckoutSessionResponse
from app.services.donation_service import DonationService

router = APIRouter(prefix="/donations", tags=["Donations"])

@router.post("/checkout", response_model=CheckoutSessionResponse)
def create_checkout_session(
    donation_data: DonationCreate,
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_current_user_optional),
):
    try:
        donor_id = current_user.id if current_user else None
        url = DonationService.create_checkout_session(db, donation_data, donor_id)
        return CheckoutSessionResponse(checkout_url=url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_database)):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe signature header")

    try:
        DonationService.handle_webhook(db, payload, sig_header)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
