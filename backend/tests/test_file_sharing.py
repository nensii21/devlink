import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.main import app
from app.dependencies import get_database, get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.conversation_member import ConversationMember

DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="db_session")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="test_client")
def fixture_test_client(db_session):
    mock_user = User(
        first_name="Sender",
        last_name="User",
        username="sender_u",
        email="sender@devlink.io",
        is_active=True,
    )
    db_session.add(mock_user)
    db_session.commit()
    db_session.refresh(mock_user)

    def override_get_database():
        return db_session

    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


def test_upload_attachment_and_send_message(test_client, db_session):
    # 1. Test uploading a general file attachment (e.g. PDF document)
    file_content = b"PDF document dummy content"
    files = {"file": ("document.pdf", file_content, "application/pdf")}
    response = test_client.post("/api/media/upload-attachment", files=files)
    assert response.status_code == 201
    upload_data = response.json()
    assert upload_data["filename"] == "document.pdf"
    assert upload_data["mime_type"] == "application/pdf"
    assert upload_data["size"] == len(file_content)
    assert "url" in upload_data

    # 2. Create a conversation
    recipient = User(
        first_name="Recipient",
        last_name="User",
        username="recipient_u",
        email="recipient@devlink.io",
        is_active=True,
    )
    db_session.add(recipient)
    db_session.commit()
    db_session.refresh(recipient)

    conv = Conversation()
    db_session.add(conv)
    db_session.commit()

    sender = db_session.query(User).filter(User.username == "sender_u").first()
    m1 = ConversationMember(conversation_id=conv.id, user_id=sender.id)
    m2 = ConversationMember(conversation_id=conv.id, user_id=recipient.id)
    db_session.add_all([m1, m2])
    db_session.commit()

    # 3. Send a message with the attachment
    message_payload = {
        "conversation_id": str(conv.id),
        "content": "Sending project details ZIP",
        "type": "file",
        "attachment_url": upload_data["url"],
        "attachment_name": upload_data["filename"],
        "attachment_size": upload_data["size"],
        "mime_type": upload_data["mime_type"],
    }
    response = test_client.post("/api/messages/", json=message_payload)
    assert response.status_code == 201
    message_data = response.json()
    assert message_data["type"] == "file"
    assert message_data["attachment_name"] == "document.pdf"
    assert message_data["attachment_size"] == len(file_content)
    assert message_data["mime_type"] == "application/pdf"

    # 4. Check conversation thread
    response = test_client.get(f"/api/messages/conversation/{conv.id}")
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 1
    assert messages[0]["attachment_name"] == "document.pdf"
