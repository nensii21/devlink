import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.activity import Activity, ActivityType


def test_create_activity(client: TestClient, db: Session, register_and_login):
    user_id, token = register_and_login("test1@example.com", "test1")
    target_id = uuid.uuid4()
    activity_data = {
        "actor_id": str(user_id),
        "activity_type": ActivityType.PROJECT_CREATED.value,
        "title": "New Project",
        "description": "Created a cool new project",
        "target_id": str(target_id),
        "target_type": "project",
        "metadata": {"foo": "bar"}
    }
    
    response = client.post(
        "/activities/",
        json=activity_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 201:
        print("ERROR:", response.json())
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Project"
    assert data["target_id"] == str(target_id)
    assert data["target_type"] == "project"
    assert data["metadata"]["foo"] == "bar"
    assert data["actor_id"] == str(user_id)


def test_list_activities_cursor_pagination(client: TestClient, db: Session, register_and_login):
    # Seed activities
    user_id_str, token = register_and_login("test2@example.com", "test2")
    actor_id = uuid.UUID(user_id_str)
    now = datetime.now(timezone.utc)

    # Create 5 activities with decreasing created_at times (so [4] is oldest, [0] is newest)
    activities = []
    for i in range(5):
        act = Activity(
            actor_id=actor_id,
            activity_type=ActivityType.SYSTEM,
            title=f"Activity {i}",
            created_at=now - timedelta(minutes=i),
        )
        db.add(act)
        activities.append(act)
    db.commit()

    # Page 1: limit 2
    response1 = client.get("/activities/?limit=2")
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1) == 2
    assert data1[0]["title"] == "Activity 0"
    assert data1[1]["title"] == "Activity 1"

    # Page 2: pass cursor
    cursor = data1[1]["created_at"]
    response2 = client.get(f"/activities/?limit=2&cursor={cursor}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) == 2
    assert data2[0]["title"] == "Activity 2"
    assert data2[1]["title"] == "Activity 3"


def test_list_activities_filters(client: TestClient, db: Session, register_and_login):
    user_id_str, token = register_and_login("test3@example.com", "test3")
    actor_id = uuid.UUID(user_id_str)

    # Seed specific activities
    db.add(
        Activity(
            actor_id=actor_id,
            activity_type=ActivityType.PROJECT_CREATED,
            title="P1",
            target_type="project",
        )
    )
    db.add(
        Activity(
            actor_id=actor_id,
            activity_type=ActivityType.FOLLOWED_USER,
            title="F1",
            target_type="user",
        )
    )
    db.commit()

    # Filter by target_type
    res_type = client.get("/activities/?target_type=project")
    data_type = res_type.json()
    assert len(data_type) == 1
    assert data_type[0]["title"] == "P1"

    # Filter by activity_types
    res_act = client.get("/activities/?activity_types=followed_user")
    data_act = res_act.json()
    assert len(data_act) == 1
    assert data_act[0]["title"] == "F1"
