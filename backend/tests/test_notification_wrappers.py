import uuid
from unittest.mock import patch
from app.services.notification_service import NotificationService
from app.models.notification import NotificationType


def test_create_project_invitation():
    with patch.object(NotificationService, "enqueue") as mock_enqueue:
        recipient_id = uuid.uuid4()
        actor_id = uuid.uuid4()
        project_id = uuid.uuid4()

        NotificationService.create_project_invitation(
            db=None,
            recipient_id=recipient_id,
            actor_id=actor_id,
            project_id=project_id,
        )

        mock_enqueue.assert_called_once_with(
            db=None,
            recipient_id=recipient_id,
            sender_id=actor_id,
            type=NotificationType.PROJECT_INVITE,
            title="New project invitation",
            message="You have been invited to join a project",
            project_id=project_id,
            action_url=None,
            image_url=None,
        )


def test_create_message_notification():
    with patch.object(NotificationService, "enqueue") as mock_enqueue:
        recipient_id = uuid.uuid4()
        actor_id = uuid.uuid4()
        conversation_id = uuid.uuid4()

        NotificationService.create_message_notification(
            db=None,
            recipient_id=recipient_id,
            actor_id=actor_id,
            conversation_id=conversation_id,
            title="Custom Title",
        )

        mock_enqueue.assert_called_once_with(
            db=None,
            recipient_id=recipient_id,
            sender_id=actor_id,
            type=NotificationType.MESSAGE,
            title="Custom Title",
            message="You received a new message",
            conversation_id=conversation_id,
            message_id=None,
            action_url=None,
            image_url=None,
        )


def test_create_follow_notification():
    with patch.object(NotificationService, "enqueue") as mock_enqueue:
        recipient_id = uuid.uuid4()
        actor_id = uuid.uuid4()

        NotificationService.create_follow_notification(
            db=None,
            recipient_id=recipient_id,
            actor_id=actor_id,
            action_url="/user/123",
        )

        mock_enqueue.assert_called_once_with(
            db=None,
            recipient_id=recipient_id,
            sender_id=actor_id,
            type=NotificationType.FOLLOW,
            title="New follower",
            message="Someone started following you",
            action_url="/user/123",
            image_url=None,
        )


def test_create_connection_notification():
    with patch.object(NotificationService, "enqueue") as mock_enqueue:
        recipient_id = uuid.uuid4()
        actor_id = uuid.uuid4()

        NotificationService.create_connection_notification(
            db=None,
            recipient_id=recipient_id,
            actor_id=actor_id,
        )

        mock_enqueue.assert_called_once_with(
            db=None,
            recipient_id=recipient_id,
            sender_id=actor_id,
            type=NotificationType.FOLLOW,
            title="New connection request",
            message="Someone wants to connect with you",
            action_url=None,
            image_url=None,
        )


def test_create_project_activity_notification():
    with patch.object(NotificationService, "enqueue") as mock_enqueue:
        recipient_id = uuid.uuid4()
        actor_id = uuid.uuid4()
        project_id = uuid.uuid4()

        NotificationService.create_project_activity_notification(
            db=None,
            recipient_id=recipient_id,
            actor_id=actor_id,
            project_id=project_id,
        )

        mock_enqueue.assert_called_once_with(
            db=None,
            recipient_id=recipient_id,
            sender_id=actor_id,
            type=NotificationType.PROJECT_UPDATE,
            title="Project activity",
            message="There is new activity in your project",
            project_id=project_id,
            action_url=None,
            image_url=None,
        )
