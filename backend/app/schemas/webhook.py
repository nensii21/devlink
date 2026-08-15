import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models.webhook import WebhookDeliveryStatus


class WebhookDispatchParams(BaseModel):
    event_type: str = Field(
        ..., description="Event action name e.g. project.created, user.updated"
    )
    target_url: str = Field(..., description="Destination webhook URL")
    payload: Dict[str, Any] = Field(..., description="JSON payload data")
    headers: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom HTTP headers"
    )
    max_retries: int = Field(
        default=5, ge=1, le=20, description="Max retry attempts limit"
    )


class WebhookDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    target_url: str
    payload: Dict[str, Any]
    headers: Optional[Dict[str, Any]] = None
    status: WebhookDeliveryStatus
    attempts: int
    max_retries: int
    next_retry_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    response_status_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WebhookDeliveryPaginatedResponse(BaseModel):
    items: List[WebhookDeliveryResponse]
    total: int
    page: int
    limit: int
    pages: int


class WebhookDLQResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    delivery_id: uuid.UUID
    event_type: str
    target_url: str
    payload: Dict[str, Any]
    headers: Optional[Dict[str, Any]] = None
    total_attempts: int
    failure_reason: str
    failed_at: datetime
    replayed_at: Optional[datetime] = None
    is_replayed: bool


class WebhookDLQPaginatedResponse(BaseModel):
    items: List[WebhookDLQResponse]
    total: int
    page: int
    limit: int
    pages: int


class WebhookMetricsResponse(BaseModel):
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    pending_deliveries: int
    dlq_count: int
    replayed_count: int
    delivery_success_rate: float
