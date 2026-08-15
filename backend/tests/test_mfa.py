import pytest
from uuid import uuid4

from app.models.user import User
from app.services.mfa_service import (
    generate_totp_secret,
    get_totp_token,
    verify_totp_token,
    MFAService,
)
from app.core.security import create_access_token, hash_password


@pytest.fixture
def mfa_user(db):
    user = User(
        id=uuid4(),
        first_name="MFA",
        last_name="Tester",
        username=f"mfa_{uuid4().hex[:6]}",
        email=f"mfa_{uuid4().hex[:6]}@example.com",
        password_hash=hash_password("Vermilion-Kestrel97!"),
        is_active=True,
        mfa_enabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def mfa_auth_headers(mfa_user):
    token = create_access_token(user_id=str(mfa_user.id))
    return {"Authorization": f"Bearer {token}"}


def test_totp_calculation():
    secret = generate_totp_secret()
    assert len(secret) == 32
    token = get_totp_token(secret)
    assert len(token) == 6
    assert token.isdigit()
    assert verify_totp_token(secret, token) is True


def test_mfa_status(client, mfa_auth_headers):
    res = client.get("/api/v1/auth/mfa/status", headers=mfa_auth_headers)
    assert res.status_code == 200
    assert res.json()["mfa_enabled"] is False


def test_mfa_setup_api(client, mfa_auth_headers):
    res = client.post("/api/v1/auth/mfa/setup", headers=mfa_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "secret" in data
    assert "otpauth://" in data["provisioning_uri"]


def test_mfa_enable_and_login_flow(client, db, mfa_user, mfa_auth_headers):
    # 1. Generate setup
    setup_res = client.post("/api/v1/auth/mfa/setup", headers=mfa_auth_headers)
    secret = setup_res.json()["secret"]

    # 2. Invalid code should fail
    bad_res = client.post(
        "/api/v1/auth/mfa/enable",
        json={"secret": secret, "code": "000000"},
        headers=mfa_auth_headers,
    )
    assert bad_res.status_code == 400

    # 3. Valid code enables MFA
    valid_code = get_totp_token(secret)
    enable_res = client.post(
        "/api/v1/auth/mfa/enable",
        json={"secret": secret, "code": valid_code},
        headers=mfa_auth_headers,
    )
    assert enable_res.status_code == 200
    enable_data = enable_res.json()
    assert enable_data["mfa_enabled"] is True
    assert len(enable_data["backup_codes"]) == 10

    db.refresh(mfa_user)
    assert mfa_user.mfa_enabled is True

    # 4. Login with password requires MFA
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": mfa_user.email, "password": "Vermilion-Kestrel97!"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["mfa_required"] is True
    mfa_token = login_data["mfa_token"]

    # 5. Verify MFA login with TOTP code
    current_code = get_totp_token(secret)
    verify_res = client.post(
        "/api/v1/auth/mfa/verify-login",
        json={"mfa_token": mfa_token, "code": current_code},
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert "access_token" in verify_data
    assert "refresh_token" in verify_data


def test_mfa_login_with_recovery_code(client, db, mfa_user):
    secret = generate_totp_secret()
    valid_code = get_totp_token(secret)

    # Enable MFA directly via service
    res = MFAService.enable_mfa(db=db, user=mfa_user, secret=secret, code=valid_code)
    backup_codes = res["backup_codes"]
    recovery_code = backup_codes[0]

    # Trigger password login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": mfa_user.email, "password": "Vermilion-Kestrel97!"},
    )
    mfa_token = login_res.json()["mfa_token"]

    # Complete 2FA login using recovery code
    verify_res = client.post(
        "/api/v1/auth/mfa/verify-login",
        json={"mfa_token": mfa_token, "code": recovery_code},
    )
    assert verify_res.status_code == 200
    assert "access_token" in verify_res.json()

    # Reuse of same recovery code should fail
    login_res2 = client.post(
        "/api/v1/auth/login",
        json={"email": mfa_user.email, "password": "Vermilion-Kestrel97!"},
    )
    mfa_token2 = login_res2.json()["mfa_token"]

    reuse_res = client.post(
        "/api/v1/auth/mfa/verify-login",
        json={"mfa_token": mfa_token2, "code": recovery_code},
    )
    assert reuse_res.status_code == 400


def test_disable_mfa_api(client, db, mfa_user, mfa_auth_headers):
    secret = generate_totp_secret()
    valid_code = get_totp_token(secret)
    MFAService.enable_mfa(db=db, user=mfa_user, secret=secret, code=valid_code)

    current_code = get_totp_token(secret)
    res = client.post(
        "/api/v1/auth/mfa/disable",
        json={"code": current_code},
        headers=mfa_auth_headers,
    )
    assert res.status_code == 200

    db.refresh(mfa_user)
    assert mfa_user.mfa_enabled is False
