from __future__ import annotations

import uuid
import hmac
import hashlib
import json
import httpx
import structlog
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models.webhook import WebhookDelivery, WebhookDeadLetterQueue, WebhookDeliveryStatus

logger = structlog.get_logger("devlink.webhooks")


def calculate_backoff_delay(
    attempt: int,
    initial_delay: int = 2,
    multiplier: int = 2,
    max_delay: int = 3600,
) -> int:
    """
    Calculates exponential backoff delay in seconds.
    attempt 1: initial_delay (2s)
    attempt 2: initial_delay * multiplier^1 (4s)
    attempt 3: initial_delay * multiplier^2 (8s)
    """
    if attempt <= 1:
        return initial_delay
    delay = initial_delay * (multiplier ** (attempt - 1))
    return min(delay, max_delay)


class WebhookService:

    @classmethod
    def generate_signature(cls, payload: Dict[str, Any] | str, secret: str) -> str:
        """
        Generates an HMAC-SHA256 signature for webhook payload verification.
        """
        if isinstance(payload, dict):
            payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        else:
            payload_bytes = str(payload).encode("utf-8")
        
        signature = hmac.new(
            secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    @classmethod
    def dispatch_webhook(
        cls,
        db: Session,
        event_type: str,
        target_url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, Any]] = None,
        secret: Optional[str] = None,
        max_retries: int = 5,
    ) -> WebhookDelivery:
        # Include signature header if a shared secret is provided
        req_headers = headers or {}
        if secret:
            sig = cls.generate_signature(payload, secret)
            req_headers["X-DevLink-Signature"] = sig

        delivery = WebhookDelivery(
            id=uuid.uuid4(),
            event_type=event_type,
            target_url=target_url,
            payload=payload,
            headers=req_headers,
            status=WebhookDeliveryStatus.PENDING,
            attempts=0,
            max_retries=max_retries,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)

        # Attempt initial delivery immediately
        cls._execute_delivery(db, delivery)
        return delivery

    @classmethod
    def _send_http_request(cls, url: str, payload: dict, headers: dict) -> httpx.Response:
        with httpx.Client(timeout=10.0) as client:
            return client.post(url, json=payload, headers=headers)

    @classmethod
    def _execute_delivery(cls, db: Session, delivery: WebhookDelivery) -> bool:
        now = datetime.now(timezone.utc)
        delivery.attempts += 1
        delivery.last_attempt_at = now

        req_headers = {"Content-Type": "application/json", "User-Agent": "DevLink-Webhook/1.0"}
        if delivery.headers:
            req_headers.update(delivery.headers)

        success = False
        status_code: Optional[int] = None
        resp_text: Optional[str] = None
        error_msg: Optional[str] = None

        try:
            response = cls._send_http_request(delivery.target_url, delivery.payload, req_headers)
            status_code = response.status_code
            resp_text = response.text[:2000] if response.text else ""

            if 200 <= status_code < 300:
                success = True
            else:
                error_msg = f"HTTP {status_code}: {resp_text[:200]}"
        except Exception as exc:
            error_msg = f"Network/HTTP Exception: {str(exc)}"
            logger.warning("webhook_delivery_failed", delivery_id=str(delivery.id), error=error_msg)

        delivery.response_status_code = status_code
        delivery.response_body = resp_text
        delivery.error_message = error_msg

        if success:
            delivery.status = WebhookDeliveryStatus.DELIVERED
            delivery.next_retry_at = None
            db.commit()
            return True

        # Failed delivery attempt -> schedule retry or move to DLQ
        if delivery.attempts < delivery.max_retries:
            delivery.status = WebhookDeliveryStatus.FAILED
            delay_seconds = calculate_backoff_delay(delivery.attempts)
            delivery.next_retry_at = now + timedelta(seconds=delay_seconds)
            db.commit()
        else:
            delivery.status = WebhookDeliveryStatus.EXHAUSTED
            delivery.next_retry_at = None
            db.commit()
            cls._move_to_dlq(db, delivery)

        return False

    @classmethod
    def _move_to_dlq(cls, db: Session, delivery: WebhookDelivery) -> WebhookDeadLetterQueue:
        existing = db.scalar(
            select(WebhookDeadLetterQueue).where(WebhookDeadLetterQueue.delivery_id == delivery.id)
        )
        if existing:
            existing.total_attempts = delivery.attempts
            existing.failure_reason = delivery.error_message or "Max retries exhausted"
            existing.failed_at = datetime.now(timezone.utc)
            db.commit()
            return existing

        dlq_item = WebhookDeadLetterQueue(
            id=uuid.uuid4(),
            delivery_id=delivery.id,
            event_type=delivery.event_type,
            target_url=delivery.target_url,
            payload=delivery.payload,
            headers=delivery.headers,
            total_attempts=delivery.attempts,
            failure_reason=delivery.error_message or "Max retries exhausted",
            failed_at=datetime.now(timezone.utc),
            is_replayed=False,
        )
        db.add(dlq_item)
        db.commit()
        db.refresh(dlq_item)
        return dlq_item

    @classmethod
    def process_pending_retries(cls, db: Session) -> Dict[str, int]:
        now = datetime.now(timezone.utc)
        stmt = select(WebhookDelivery).where(
            or_(
                WebhookDelivery.status == WebhookDeliveryStatus.PENDING,
                WebhookDelivery.status == WebhookDeliveryStatus.FAILED,
            ),
            WebhookDelivery.next_retry_at <= now,
        ).order_by(WebhookDelivery.next_retry_at.asc()).limit(50)

        pending_items = list(db.scalars(stmt))
        processed = 0
        succeeded = 0

        for item in pending_items:
            processed += 1
            if cls._execute_delivery(db, item):
                succeeded += 1

        return {"processed": processed, "succeeded": succeeded, "failed": processed - succeeded}

    @classmethod
    def get_deliveries(
        cls,
        db: Session,
        page: int = 1,
        limit: int = 20,
        status: Optional[WebhookDeliveryStatus] = None,
        event_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        stmt = select(WebhookDelivery)

        if status:
            stmt = stmt.where(WebhookDelivery.status == status)
        if event_type:
            stmt = stmt.where(WebhookDelivery.event_type == event_type)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        offset = (page - 1) * limit
        paginated_stmt = stmt.order_by(WebhookDelivery.created_at.desc()).offset(offset).limit(limit)

        items = list(db.scalars(paginated_stmt))
        pages = (total + limit - 1) // limit if limit > 0 else 1

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    @classmethod
    def get_dlq_entries(
        cls,
        db: Session,
        page: int = 1,
        limit: int = 20,
        is_replayed: Optional[bool] = None,
    ) -> Dict[str, Any]:
        stmt = select(WebhookDeadLetterQueue)

        if is_replayed is not None:
            stmt = stmt.where(WebhookDeadLetterQueue.is_replayed == is_replayed)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        offset = (page - 1) * limit
        paginated_stmt = stmt.order_by(WebhookDeadLetterQueue.failed_at.desc()).offset(offset).limit(limit)

        items = list(db.scalars(paginated_stmt))
        pages = (total + limit - 1) // limit if limit > 0 else 1

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    @classmethod
    def get_dlq_entry(cls, db: Session, dlq_id: uuid.UUID) -> Optional[WebhookDeadLetterQueue]:
        return db.scalar(select(WebhookDeadLetterQueue).where(WebhookDeadLetterQueue.id == dlq_id))

    @classmethod
    def replay_dlq_entry(cls, db: Session, dlq_id: uuid.UUID) -> WebhookDelivery:
        dlq_item = cls.get_dlq_entry(db, dlq_id)
        if not dlq_item:
            raise ValueError(f"DLQ entry {dlq_id} not found")

        delivery = db.scalar(select(WebhookDelivery).where(WebhookDelivery.id == dlq_item.delivery_id))
        if not delivery:
            delivery = WebhookDelivery(
                id=dlq_item.delivery_id,
                event_type=dlq_item.event_type,
                target_url=dlq_item.target_url,
                payload=dlq_item.payload,
                headers=dlq_item.headers,
                status=WebhookDeliveryStatus.PENDING,
                attempts=0,
                max_retries=5,
            )
            db.add(delivery)
            db.commit()

        is_success = cls._execute_delivery(db, delivery)

        now = datetime.now(timezone.utc)
        dlq_item.is_replayed = True
        dlq_item.replayed_at = now
        if is_success:
            delivery.status = WebhookDeliveryStatus.REPLAYED
        db.commit()

        return delivery

    @classmethod
    def replay_all_dlq_entries(cls, db: Session) -> Dict[str, int]:
        stmt = select(WebhookDeadLetterQueue).where(WebhookDeadLetterQueue.is_replayed.is_(False))
        unreplayed_items = list(db.scalars(stmt))

        replayed_count = 0
        succeeded_count = 0

        for dlq in unreplayed_items:
            replayed_count += 1
            try:
                deliv = cls.replay_dlq_entry(db, dlq.id)
                if deliv.status in {WebhookDeliveryStatus.DELIVERED, WebhookDeliveryStatus.REPLAYED}:
                    succeeded_count += 1
            except Exception:
                pass

        return {"total_replayed": replayed_count, "successful": succeeded_count, "failed": replayed_count - succeeded_count}

    @classmethod
    def delete_dlq_entry(cls, db: Session, dlq_id: uuid.UUID) -> bool:
        dlq_item = cls.get_dlq_entry(db, dlq_id)
        if not dlq_item:
            return False
        db.delete(dlq_item)
        db.commit()
        return True

    @classmethod
    def get_metrics(cls, db: Session) -> Dict[str, Any]:
        total_deliveries = db.scalar(select(func.count(WebhookDelivery.id))) or 0
        successful = db.scalar(
            select(func.count(WebhookDelivery.id)).where(
                or_(
                    WebhookDelivery.status == WebhookDeliveryStatus.DELIVERED,
                    WebhookDelivery.status == WebhookDeliveryStatus.REPLAYED,
                )
            )
        ) or 0
        failed = db.scalar(
            select(func.count(WebhookDelivery.id)).where(
                or_(
                    WebhookDelivery.status == WebhookDeliveryStatus.FAILED,
                    WebhookDelivery.status == WebhookDeliveryStatus.EXHAUSTED,
                )
            )
        ) or 0
        pending = db.scalar(
            select(func.count(WebhookDelivery.id)).where(WebhookDelivery.status == WebhookDeliveryStatus.PENDING)
        ) or 0

        dlq_count = db.scalar(select(func.count(WebhookDeadLetterQueue.id))) or 0
        replayed_count = db.scalar(
            select(func.count(WebhookDeadLetterQueue.id)).where(WebhookDeadLetterQueue.is_replayed.is_(True))
        ) or 0

        success_rate = (successful / total_deliveries * 100.0) if total_deliveries > 0 else 100.0

        return {
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful,
            "failed_deliveries": failed,
            "pending_deliveries": pending,
            "dlq_count": dlq_count,
            "replayed_count": replayed_count,
            "delivery_success_rate": round(success_rate, 2),
        }
    