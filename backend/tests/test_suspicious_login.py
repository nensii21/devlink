import pytest
from uuid import uuid4

from app.models.user import User
from app.models.audit_log import AuditLog, AuditAction
from app.models.notification import Notification, NotificationType
from app.services.suspicious_login_service import SuspiciousLoginService
from app.core.security import hash_password


@pytest.fixture
def security_user(db):
    user = User(
        id=uuid4(),
        first_name="SecUser",
        last_name="Test",
        username=f"secuser_{uuid4().hex[:6]}",
        email=f"secuser_{uuid4().hex[:6]}@example.com",
        password_hash=hash_password("SuperSecret123!"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_detect_new_device_and_browser_signal(client, db, security_user):
    # 1. Establish baseline successful login
    client.post(
        "/api/v1/auth/login",
        json={"email": security_user.email, "password": "SuperSecret123!"},
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"
        },
    )

    # 2. Login from new device / browser (e.g. iPhone Safari)
    res = SuspiciousLoginService.evaluate_login_attempt(
        db=db,
        email=security_user.email,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
        user=security_user,
        is_success=True,
    )

    assert res.is_suspicious is True
    assert "NEW_DEVICE" in res.signals or "NEW_BROWSER" in res.signals
    assert res.warning_notification_sent is True


def test_detect_unusual_location_signal(client, db, security_user):
    # Establish baseline login from IP 10.0.0.1
    client.post(
        "/api/v1/auth/login",
        json={"email": security_user.email, "password": "SuperSecret123!"},
        headers={"User-Agent": "Mozilla/5.0 Chrome/120.0"},
    )

    # Login from unusual IP 203.0.113.45
    res = SuspiciousLoginService.evaluate_login_attempt(
        db=db,
        email=security_user.email,
        ip_address="203.0.113.45",
        user_agent="Mozilla/5.0 Chrome/120.0",
        user=security_user,
        is_success=True,
    )

    assert res.is_suspicious is True
    assert "UNUSUAL_LOCATION" in res.signals


def test_detect_multiple_failed_logins(client, db, security_user):
    # Perform 3 failed logins
    for _ in range(3):
        client.post(
            "/api/v1/auth/login",
            json={"email": security_user.email, "password": "WrongPassword!"},
        )

    # Check audit log and suspicious detection for failed logins
    failed_logs = db.scalars(
        db.query(AuditLog).filter(
            AuditLog.actor_id == security_user.id,
            AuditLog.action == AuditAction.FAILED_LOGIN,
        )
    ).all()
    assert len(list(failed_logs)) >= 3

    # Check security alert notification was generated
    notifs = db.scalars(
        db.query(Notification).filter(
            Notification.recipient_id == security_user.id,
            Notification.type == NotificationType.SECURITY_ALERT,
        )
    ).all()
    assert len(list(notifs)) >= 1


def test_detect_rapid_login_attempts(db, security_user):
    # Log 2 audit entries within last 5 seconds to simulate rapid login attempts
    from app.services.audit_log_service import AuditLogService

    for _ in range(2):
        AuditLogService.create_log(
            db=db,
            actor_id=security_user.id,
            action=AuditAction.LOGIN,
            entity_type="user_session",
            entity_id=str(security_user.id),
            request_path="/api/v1/auth/login",
            description="Login attempt",
        )
    db.commit()

    res = SuspiciousLoginService.evaluate_login_attempt(
        db=db,
        email=security_user.email,
        ip_address="127.0.0.1",
        user_agent="TestAgent",
        user=security_user,
        is_success=True,
    )

    assert res.is_suspicious is True
    assert "RAPID_LOGIN_ATTEMPTS" in res.signals


def test_warning_notification_and_audit_log_generation(client, db, security_user):
    # Establish baseline login
    client.post(
        "/api/v1/auth/login",
        json={"email": security_user.email, "password": "SuperSecret123!"},
        headers={"User-Agent": "Mozilla/5.0 Chrome/120.0"},
    )

    # Perform suspicious login from new browser/device via HTTP login API
    res = client.post(
        "/api/v1/auth/login",
        json={"email": security_user.email, "password": "SuperSecret123!"},
        headers={"User-Agent": "Mozilla/5.0 (Android 14; Mobile) Firefox/121.0"},
    )
    assert res.status_code == 200

    # Verify audit log recorded
    from sqlalchemy import select

    suspicious_logs = list(
        db.scalars(
            select(AuditLog).where(
                AuditLog.actor_id == security_user.id,
                AuditLog.action == AuditAction.SUSPICIOUS_LOGIN_ATTEMPT,
            )
        )
    )
    assert len(suspicious_logs) >= 1
    assert (
        "NEW_DEVICE" in suspicious_logs[0].description
        or "NEW_BROWSER" in suspicious_logs[0].description
    )
