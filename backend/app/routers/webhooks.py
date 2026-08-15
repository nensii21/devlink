import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
from app.models.user import User
from app.models.webhook import WebhookDeliveryStatus
from app.schemas.webhook import (
    WebhookDispatchParams,
    WebhookDeliveryResponse,
    WebhookDeliveryPaginatedResponse,
    WebhookDLQResponse,
    WebhookDLQPaginatedResponse,
    WebhookMetricsResponse,
)
from app.services.webhook_service import WebhookService

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks & DLQ"],
)


@router.post(
    "/dispatch",
    response_model=WebhookDeliveryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Dispatch a new webhook event with automatic retry",
)
def dispatch_webhook(
    params: WebhookDispatchParams,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Dispatch a webhook to a target URL with automatic retries and dead letter queue fallback."""
    return WebhookService.dispatch_webhook(
        db=db,
        event_type=params.event_type,
        target_url=params.target_url,
        payload=params.payload,
        headers=params.headers,
        max_retries=params.max_retries,
    )


@router.post(
    "/retry-pending",
    summary="Process and retry pending or failed webhooks",
)
def process_pending_retries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Triggers retry attempt for webhooks scheduled for exponential backoff retry."""
    return WebhookService.process_pending_retries(db=db)


@router.get(
    "/deliveries",
    response_model=WebhookDeliveryPaginatedResponse,
    summary="List webhook deliveries with status filters and pagination",
)
def get_webhook_deliveries(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[WebhookDeliveryStatus] = Query(
        None, description="Filter by status e.g. pending, delivered, failed, exhausted"
    ),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """List webhook delivery history."""
    return WebhookService.get_deliveries(
        db=db,
        page=page,
        limit=limit,
        status=status,
        event_type=event_type,
    )


@router.get(
    "/deliveries/{delivery_id}",
    response_model=WebhookDeliveryResponse,
    summary="Get single webhook delivery details",
)
def get_webhook_delivery(
    delivery_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Retrieve details for a specific webhook delivery."""
    res = WebhookService.get_deliveries(db=db, page=1, limit=1, status=None)
    for item in res["items"]:
        if item.id == delivery_id:
            return item
    raise HTTPException(status_code=404, detail="Webhook delivery not found")


@router.get(
    "/dlq",
    response_model=WebhookDLQPaginatedResponse,
    summary="List Dead Letter Queue (DLQ) entries",
)
def get_dlq_entries(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    is_replayed: Optional[bool] = Query(None, description="Filter by replayed status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Retrieve paginated entries from the Webhook Dead Letter Queue."""
    return WebhookService.get_dlq_entries(
        db=db,
        page=page,
        limit=limit,
        is_replayed=is_replayed,
    )


@router.get(
    "/dlq/{dlq_id}",
    response_model=WebhookDLQResponse,
    summary="Get DLQ entry details",
)
def get_dlq_entry(
    dlq_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Get single DLQ entry."""
    entry = WebhookService.get_dlq_entry(db=db, dlq_id=dlq_id)
    if not entry:
        raise HTTPException(status_code=404, detail="DLQ entry not found")
    return entry


@router.post(
    "/dlq/{dlq_id}/replay",
    response_model=WebhookDeliveryResponse,
    summary="Manually replay a failed webhook from DLQ",
)
def replay_dlq_entry(
    dlq_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Replay a failed webhook event from the Dead Letter Queue."""
    try:
        return WebhookService.replay_dlq_entry(db=db, dlq_id=dlq_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post(
    "/dlq/replay-all",
    summary="Replay all pending failed webhooks in DLQ",
)
def replay_all_dlq_entries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Bulk replay all active items in the Dead Letter Queue."""
    return WebhookService.replay_all_dlq_entries(db=db)


@router.delete(
    "/dlq/{dlq_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a DLQ entry",
)
def delete_dlq_entry(
    dlq_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Delete an entry from the Dead Letter Queue."""
    deleted = WebhookService.delete_dlq_entry(db=db, dlq_id=dlq_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="DLQ entry not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/metrics",
    response_model=WebhookMetricsResponse,
    summary="Get webhook delivery and DLQ metrics",
)
def get_webhook_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Get webhook delivery statistics, success rate, and DLQ counts."""
    return WebhookService.get_metrics(db=db)
