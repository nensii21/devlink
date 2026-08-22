from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Optional

class DonationCreate(BaseModel):
    recipient_id: uuid.UUID
    amount: int
    message: Optional[str] = None

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
