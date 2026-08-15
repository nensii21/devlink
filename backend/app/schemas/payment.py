from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class PaymentHistoryBase(BaseModel):
    amount: int
    currency: str
    status: str
    invoice_url: Optional[str] = None
    created_at: datetime

class PaymentHistoryResponse(PaymentHistoryBase):
    id: UUID
    user_id: UUID

    class Config:
        orm_mode = True
        from_attributes = True

class UpdatePaymentMethodRequest(BaseModel):
    token: str  # Mock stripe token
