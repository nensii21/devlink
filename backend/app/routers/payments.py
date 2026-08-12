from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.user_subscription import UserSubscription
from app.models.payment_history import PaymentHistory
from app.schemas.payment import PaymentHistoryResponse, UpdatePaymentMethodRequest

router = APIRouter(prefix="/payments", tags=["payments"])

@router.get("/history", response_model=List[PaymentHistoryResponse])
def get_payment_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    history = db.query(PaymentHistory).filter(
        PaymentHistory.user_id == current_user.id
    ).order_by(desc(PaymentHistory.created_at)).all()
    return history

@router.post("/update-method")
def update_payment_method(
    req: UpdatePaymentMethodRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(UserSubscription).filter(UserSubscription.user_id == current_user.id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    # Mock token handling - in reality, we'd call Stripe/Braintree to update the payment method
    # Here we just parse the token for a mock brand/last4 if available or hardcode
    brand = "Visa"
    last4 = "4242"
    if "mastercard" in req.token.lower():
        brand = "Mastercard"
        last4 = "5555"

    sub.payment_method_brand = brand
    sub.payment_method_last4 = last4
    
    db.commit()
    db.refresh(sub)
    return {"message": "Payment method updated successfully", "brand": brand, "last4": last4}
