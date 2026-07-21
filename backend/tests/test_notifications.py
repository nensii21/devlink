import pytest
import uuid
from fastapi.testclient import TestClient


def test_create_notification(client: TestClient, register_and_login):
    uid1, token1 = register_and_login("notif1@example.com", "notif1")
    uid2, token2 = register_and_login("notif2@example.com", "notif2")

    response = client.post(
        "/api/notifications/",
        json={
            "recipient_id": uid2,
            "type": "message",
            "title": "New Message",
            "message": "Hello!",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert response.status_code == 201
    assert response.json()["title"] == "New Message"
    assert response.json()["recipient_id"] == uid2


def test_get_notification(client: TestClient, register_and_login):
    uid1, token1 = register_and_login("getnotif1@example.com", "gn1")
    uid2, token2 = register_and_login("getnotif2@example.com", "gn2")

    c = client.post(
        "/api/notifications/",
        json={
            "recipient_id": uid2,
            "type": "message",
            "title": "T",
            "message": "M" + str(uuid.uuid4()),
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    nid = c.json()["id"]

    response = client.get(
        f"/api/notifications/{nid}", headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "T"


def test_get_notification_not_found(client: TestClient, register_and_login):
    _, token = register_and_login("gnnf@example.com", "gnnf")
    response = client.get(
        f"/api/notifications/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_list_notifications(client: TestClient, register_and_login):
    uid1, token1 = register_and_login("listn1@example.com", "ln1")
    uid2, token2 = register_and_login("listn2@example.com", "ln2")

    client.post(
        "/api/notifications/",
        json={
            "recipient_id": uid2,
            "type": "message",
            "title": "T1",
            "message": "M" + str(uuid.uuid4()),
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    client.post(
        "/api/notifications/",
        json={
            "recipient_id": uid2,
            "type": "follow",
            "title": "T2",
            "message": "M" + str(uuid.uuid4()),
        },
        headers={"Authorization": f"Bearer {token1}"},
    )

    response = client.get(
        "/api/notifications/", headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_unread_notifications(client: TestClient, register_and_login):
    uid1, token1 = register_and_login("un1@example.com", "un1")
    uid2, token2 = register_and_login("un2@example.com", "un2")

    client.post(
        "/api/notifications/",
        json={
            "recipient_id": uid2,
            "type": "message",
            "title": "T1",
            "message": "M" + str(uuid.uuid4()),
        },
        headers={"Authorization": f"Bearer {token1}"},
    )

    response = client.get(
        "/api/notifications/unread", headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["is_read"] is False


def test_unread_count(client: TestClient, register_and_login):
    uid1, token1 = register_and_login("unc1@example.com", "unc1")
    uid2, token2 = register_and_login("unc2@example.com", "unc2")

    client.post(
        "/api/notifications/",
        json={"recipient_id": uid2, "type": "message", "title": "T1", "message": "M1"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    client.post(
        "/api/notifications/",
        json={"recipient_id": uid2, "type": "follow", "title": "T2", "message": "M2"},
        headers={"Authorization": f"Bearer {token1}"},
    )

    response = client.get(
        "/api/notifications/unread/count", headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 200
    assert response.json()["count"] >= 2


def test_mark_as_read(client: TestClient, register_and_login):
    uid1, token1 = register_and_login("mar1@example.com", "mar1")
    uid2, token2 = register_and_login("mar2@example.com", "mar2")

    c = client.post(
        "/api/notifications/",
        json={
            "recipient_id": uid2,
            "type": "message",
            "title": "T1",
            "message": "M" + str(uuid.uuid4()),
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    nid = c.json()["id"]

    response = client.patch(
        f"/api/notifications/{nid}/read", headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 200
    assert response.json()["is_read"] is True


def test_mark_as_read_not_found(client: TestClient, register_and_login):
    _, token = register_and_login("marnf@example.com", "marnf")
    response = client.patch(
        f"/api/notifications/{uuid.uuid4()}/read",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_mark_all_as_read(client: TestClient, register_and_login):
    uid1, token1 = register_and_login("maar1@example.com", "maar1")
    uid2, token2 = register_and_login("maar2@example.com", "maar2")

    client.post(
        "/api/notifications/",
        json={
            "recipient_id": uid2,
            "type": "message",
            "title": "T1",
            "message": "M" + str(uuid.uuid4()),
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    client.post(
        "/api/notifications/",
        json={
            "recipient_id": uid2,
            "type": "follow",
            "title": "T2",
            "message": "M" + str(uuid.uuid4()),
        },
        headers={"Authorization": f"Bearer {token1}"},
    )

    response = client.patch(
        "/api/notifications/read-all", headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 200

    unread = client.get(
        "/api/notifications/unread/count", headers={"Authorization": f"Bearer {token2}"}
    )
    assert unread.json()["count"] == 0


def test_update_notification(client: TestClient, register_and_login):
    uid1, token1 = register_and_login("updn1@example.com", "updn1")
    uid2, token2 = register_and_login("updn2@example.com", "updn2")

    c = client.post(
        "/api/notifications/",
        json={
            "recipient_id": uid2,
            "type": "message",
            "title": "T1",
            "message": "M" + str(uuid.uuid4()),
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    nid = c.json()["id"]

    response = client.put(
        f"/api/notifications/{nid}",
        json={"is_read": True},
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert response.status_code == 200
    assert response.json()["is_read"] is True


def test_update_notification_not_found(client: TestClient, register_and_login):
    _, token = register_and_login("updnnf@example.com", "updnnf")
    response = client.put(
        f"/api/notifications/{uuid.uuid4()}",
        json={"is_read": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_delete_notification(client: TestClient, register_and_login):
    uid1, token1 = register_and_login("deln1@example.com", "deln1")
    uid2, token2 = register_and_login("deln2@example.com", "deln2")

    c = client.post(
        "/api/notifications/",
        json={
            "recipient_id": uid2,
            "type": "message",
            "title": "T1",
            "message": "M" + str(uuid.uuid4()),
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    nid = c.json()["id"]

    response = client.delete(
        f"/api/notifications/{nid}", headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 204

    get_resp = client.get(
        f"/api/notifications/{nid}", headers={"Authorization": f"Bearer {token1}"}
    )
    assert get_resp.status_code == 404


def test_delete_notification_not_found(client: TestClient, register_and_login):
    _, token = register_and_login("delnnf@example.com", "delnnf")
    response = client.delete(
        f"/api/notifications/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
