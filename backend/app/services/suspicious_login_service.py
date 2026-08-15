from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.audit_log import AuditLog, AuditAction
from app.models.notification import NotificationType
from app.services.audit_log_service import AuditLogService
from app.services.notification_service import NotificationService


class SuspiciousLoginResult(BaseModel):
    is_suspicious: bool
    signals: List[str]
    warning_notification_sent: bool
    details: Dict[str, Any] = {}


def _parse_browser(user_agent: Optional[str]) -> str:
    if not user_agent:
        return "Unknown Browser"
    ua = user_agent.lower()
    if "edg" in ua:
        return "Edge"
    elif "chrome" in ua and "chromium" not in ua:
        return "Chrome"
    elif "firefox" in ua:
        return "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        return "Safari"
    elif "opera" in ua or "opr" in ua:
        return "Opera"
    return "Other Browser"


def _parse_device(user_agent: Optional[str]) -> str:
    if not user_agent:
        return "Unknown Device"
    ua = user_agent.lower()
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        return "Mobile Device"
    elif "ipad" in ua or "tablet" in ua:
        return "Tablet Device"
    elif "macintosh" in ua or "mac os" in ua:
        return "Mac Desktop"
    elif "windows" in ua:
        return "Windows Desktop"
    elif "linux" in ua:
        return "Linux Desktop"
    return "Desktop Device"


class SuspiciousLoginService:
    @classmethod
    def evaluate_login_attempt(
        cls,
        db: Session,
        email: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        user: Optional[User] = None,
        is_success: bool = True,
    ) -> SuspiciousLoginResult:
        signals: List[str] = []
        now = datetime.now(timezone.utc)
        user_id = user.id if user else None

        # -------------------------------------------------------------
        # 1. Check Rapid Login Attempts (< 5 seconds)
        # -------------------------------------------------------------
        five_sec_ago = now - timedelta(seconds=5)
        recent_attempts_stmt = select(func.count(AuditLog.id)).where(
            AuditLog.created_at >= five_sec_ago,
            or_(
                AuditLog.actor_id == user_id if user_id else False,
                AuditLog.request_path.contains("/auth/login"),
            ),
        )
        recent_count = db.scalar(recent_attempts_stmt) or 0
        if recent_count >= 2:
            signals.append("RAPID_LOGIN_ATTEMPTS")

        # -------------------------------------------------------------
        # 2. Check Multiple Failed Logins (>= 3 in last 15 minutes)
        # -------------------------------------------------------------
        fifteen_min_ago = now - timedelta(minutes=15)
        failed_stmt = select(func.count(AuditLog.id)).where(
            AuditLog.action == AuditAction.FAILED_LOGIN,
            AuditLog.created_at >= fifteen_min_ago,
            or_(
                AuditLog.actor_id == user_id if user_id else False,
                AuditLog.ip_address == ip_address if ip_address else False,
            ),
        )
        failed_count = db.scalar(failed_stmt) or 0
        if not is_success:
            failed_count += 1
        if failed_count >= 3:
            signals.append("MULTIPLE_FAILED_LOGINS")

        # -------------------------------------------------------------
        # For authenticated user, check historical login patterns
        # -------------------------------------------------------------
        if user_id:
            thirty_days_ago = now - timedelta(days=30)
            prior_successful_logins_stmt = select(AuditLog).where(
                AuditLog.actor_id == user_id,
                AuditLog.action == AuditAction.LOGIN,
                AuditLog.success.is_(True),
                AuditLog.created_at >= thirty_days_ago,
            )
            past_logins = list(db.scalars(prior_successful_logins_stmt))

            if past_logins:
                # 3. Check New Device
                current_device = _parse_device(user_agent)
                past_devices = {
                    _parse_device(l.user_agent) for l in past_logins if l.user_agent
                }
                if current_device not in past_devices:
                    signals.append("NEW_DEVICE")

                # 4. Check New Browser
                current_browser = _parse_browser(user_agent)
                past_browsers = {
                    _parse_browser(l.user_agent) for l in past_logins if l.user_agent
                }
                if current_browser not in past_browsers:
                    signals.append("NEW_BROWSER")

                # 5. Check Unusual Location / IP
                if ip_address:
                    past_ips = {l.ip_address for l in past_logins if l.ip_address}
                    if ip_address not in past_ips:
                        signals.append("UNUSUAL_LOCATION")

        is_suspicious = len(signals) > 0
        warning_sent = False

        if is_suspicious:
            # 1. Record Audit Log Entry
            AuditLogService.create_log(
                db=db,
                actor_id=user_id,
                action=AuditAction.SUSPICIOUS_LOGIN_ATTEMPT,
                entity_type="user_session",
                entity_id=str(user_id) if user_id else email,
                target_user_id=user_id,
                description=f"Suspicious login attempt detected (Signals: {', '.join(signals)}). IP: {ip_address or 'Unknown'}",
                ip_address=ip_address,
                user_agent=user_agent,
                metadata_info={
                    "signals": signals,
                    "email": email,
                    "is_success": is_success,
                },
                success=is_success,
            )
            db.commit()

            # 2. Dispatch Warning Notification if user exists
            if user_id:
                try:
                    NotificationService.notify(
                        db=db,
                        recipient_id=user_id,
                        sender_id=None,
                        type=NotificationType.SECURITY_ALERT,
                        title="Suspicious Login Activity Detected",
                        message=f"We detected a suspicious login attempt on your account from {ip_address or 'unknown location'} using {user_agent or 'unknown device'}. Signals: {', '.join(signals)}. If this was not you, please reset your password immediately.",
                        priority="urgent",
                    )
                    warning_sent = True
                except Exception:
                    pass

        return SuspiciousLoginResult(
            is_suspicious=is_suspicious,
            signals=signals,
            warning_notification_sent=warning_sent,
            details={
                "email": email,
                "ip_address": ip_address,
                "user_agent": user_agent,
            },
        )
