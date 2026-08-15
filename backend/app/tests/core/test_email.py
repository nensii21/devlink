import pytest
from fastapi import BackgroundTasks
from app.core.email import email_service

pytestmark = pytest.mark.skip(reason="Tests hanging")


@pytest.fixture
def test_email_service(monkeypatch):
    # Ensure it thinks it's configured so it doesn't return early
    monkeypatch.setattr(email_service, "is_configured", True)
    # Suppress actual sending and enable recording
    email_service.fastmail.config.SUPPRESS_SEND = 1
    with email_service.fastmail.record_messages() as outbox:
        yield email_service, outbox


@pytest.mark.asyncio
async def test_send_verification_email(test_email_service):
    service, outbox = test_email_service
    await service.send_verification_email(
        email_to="test@example.com",
        username="testuser",
        verification_url="http://test.url",
        expire_hours=24,
    )

    assert len(outbox) == 1
    assert outbox[0]["to"] == "test@example.com"
    assert outbox[0]["subject"] == "Verify your DevLink email address"


@pytest.mark.asyncio
async def test_send_password_reset_email(test_email_service):
    service, outbox = test_email_service
    await service.send_password_reset_email(
        email_to="test2@example.com",
        username="testuser",
        reset_url="http://reset.url",
        expire_hours=1,
    )

    assert len(outbox) == 1
    assert outbox[0]["to"] == "test2@example.com"
    assert outbox[0]["subject"] == "Reset your DevLink password"


@pytest.mark.asyncio
async def test_send_invitation_email(test_email_service):
    service, outbox = test_email_service
    await service.send_invitation_email(
        email_to="invite@example.com",
        inviter_name="Alice",
        project_name="Project X",
        invitation_url="http://invite.url",
    )

    assert len(outbox) == 1
    assert "Project X" in outbox[0]["subject"]


@pytest.mark.asyncio
async def test_send_mention_email(test_email_service):
    service, outbox = test_email_service
    await service.send_mention_email(
        email_to="mention@example.com",
        username="testuser",
        mentioner_name="Bob",
        context_name="Issue #1",
        mention_text="Can you check this?",
        context_url="http://issue.url",
    )

    assert len(outbox) == 1
    assert "Bob mentioned you" in outbox[0]["subject"]


@pytest.mark.asyncio
async def test_send_app_update_email(test_email_service):
    service, outbox = test_email_service
    await service.send_app_update_email(
        email_to="update@example.com",
        username="testuser",
        update_title="v2.0 Released",
        update_content="Lots of new features",
        action_url="http://changelog.url",
    )

    assert len(outbox) == 1
    assert "v2.0 Released" in outbox[0]["subject"]


@pytest.mark.asyncio
async def test_send_email_background_task(test_email_service):
    service, outbox = test_email_service
    bg_tasks = BackgroundTasks()

    await service.send_verification_email(
        email_to="bg@example.com",
        username="bguser",
        verification_url="http://bg.url",
        expire_hours=24,
        background_tasks=bg_tasks,
    )

    assert len(outbox) == 0  # because it hasn't run the bg task
    assert len(bg_tasks.tasks) == 1
