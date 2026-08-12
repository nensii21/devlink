from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

from app.dependencies import get_current_active_user, get_database
from app.models.user import User
from app.models.user_subscription import UserSubscription
from app.schemas.subscription import SubscriptionResponse, SubscriptionUpgradeRequest

router = APIRouter(
    prefix="/api/subscriptions",
    tags=["Subscriptions"],
)

@router.get("/me", response_model=SubscriptionResponse)
def get_my_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
):
    stmt = select(UserSubscription).where(UserSubscription.user_id == current_user.id)
    sub = db.scalar(stmt)
    if not sub:
        now = datetime.now(timezone.utc)
        sub = UserSubscription(
            user_id=current_user.id,
            tier="free",
            status="active",
            created_at=now,
            updated_at=now
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub

@router.post("/upgrade", response_model=SubscriptionResponse)
def upgrade_subscription(
    req: SubscriptionUpgradeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
):
    stmt = select(UserSubscription).where(UserSubscription.user_id == current_user.id)
    sub = db.scalar(stmt)
    now = datetime.now(timezone.utc)
    
    if not sub:
        sub = UserSubscription(user_id=current_user.id)
        db.add(sub)
        
    sub.tier = req.tier
    sub.status = "active"
    sub.updated_at = now
    
    if req.tier == "pro":
        # Mock 1 month subscription
        sub.current_period_end = now + timedelta(days=30)
    else:
        sub.current_period_end = None
        
    db.commit()
    db.refresh(sub)
    return sub

@router.post("/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
):
    stmt = select(UserSubscription).where(UserSubscription.user_id == current_user.id)
    sub = db.scalar(stmt)
    now = datetime.now(timezone.utc)
    
    if not sub:
        sub = UserSubscription(user_id=current_user.id)
        db.add(sub)
        
    sub.tier = "free"
    sub.status = "canceled"
    sub.updated_at = now
    sub.current_period_end = None
    sub.payment_method_brand = None
    sub.payment_method_last4 = None
        
    db.commit()
    db.refresh(sub)
    return sub
