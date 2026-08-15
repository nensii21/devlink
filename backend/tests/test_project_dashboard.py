from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project_member import ProjectMember, MemberRole
from app.models.activity import ActivityType


def test_project_dashboard_flow(client: TestClient, register_and_login, db: Session):
    # 1. Create users
    owner_id, owner_token = register_and_login("owner@dashboard.com", "dashboard_owner")
    member_id, member_token = register_and_login(
        "member@dashboard.com", "dashboard_member"
    )
    regular_id, regular_token = register_and_login(
        "regular@dashboard.com", "dashboard_regular"
    )
    non_member_id, non_member_token = register_and_login(
        "non@dashboard.com", "dashboard_non"
    )

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    member_headers = {"Authorization": f"Bearer {member_token}"}
    regular_headers = {"Authorization": f"Bearer {regular_token}"}
    non_member_headers = {"Authorization": f"Bearer {non_member_token}"}

    import uuid

    # 2. Create project
    proj_resp = client.post(
        "/api/projects/",
        json={
            "title": "Dashboard Project",
            "slug": "dashboard-proj",
            "description": "Project with team workspace dashboard",
            "stage": "idea",
            "visibility": "public",
        },
        headers=owner_headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    project_uuid = uuid.UUID(project_id)
    member_uuid = uuid.UUID(member_id)
    regular_uuid = uuid.UUID(regular_id)
    non_member_uuid = uuid.UUID(non_member_id)

    # 3. Add members
    # member_id -> Active MAINTAINER (has write permissions)
    # regular_id -> Active MEMBER (has read-only permissions)
    # non_member_id -> Is a pending invitation (is_active=False)

    db_member = ProjectMember(
        project_id=project_uuid,
        user_id=member_uuid,
        role=MemberRole.MAINTAINER,
        is_active=True,
    )
    db_regular = ProjectMember(
        project_id=project_uuid,
        user_id=regular_uuid,
        role=MemberRole.MEMBER,
        is_active=True,
    )
    db_invite = ProjectMember(
        project_id=project_uuid,
        user_id=non_member_uuid,
        role=MemberRole.MEMBER,
        is_active=False,
    )
    db.add_all([db_member, db_regular, db_invite])
    db.commit()

    # 4. Check dashboard view permissions (GET /projects/{project_id}/dashboard)
    # Owner should succeed
    resp = client.get(f"/api/projects/{project_id}/dashboard", headers=owner_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == project_id
    assert len(data["members"]) == 3  # Owner, member, regular
    assert len(data["pending_invitations"]) == 1
    assert data["pending_invitations"][0]["user_id"] == non_member_id

    # Active Member should succeed
    resp_member = client.get(
        f"/api/projects/{project_id}/dashboard", headers=member_headers
    )
    assert resp_member.status_code == 200

    # Active regular member should succeed
    resp_regular = client.get(
        f"/api/projects/{project_id}/dashboard", headers=regular_headers
    )
    assert resp_regular.status_code == 200

    # Non-member should fail (non_member_token has is_active=False, so is treated as non-member)
    resp_non = client.get(
        f"/api/projects/{project_id}/dashboard", headers=non_member_headers
    )
    assert resp_non.status_code == 403

    # 5. Create Milestones (POST /projects/{project_id}/milestones)
    # Non-member should fail
    milestone_payload = {
        "title": "Alpha Release",
        "description": "Deliver basic MVP functionality",
        "due_date": "2026-12-31T23:59:59Z",
    }
    resp_mile_non = client.post(
        f"/api/projects/{project_id}/milestones",
        json=milestone_payload,
        headers=non_member_headers,
    )
    assert resp_mile_non.status_code == 403

    # Standard Member should fail
    resp_mile_reg = client.post(
        f"/api/projects/{project_id}/milestones",
        json=milestone_payload,
        headers=regular_headers,
    )
    assert resp_mile_reg.status_code == 403

    # Maintainer should succeed
    resp_mile_maint = client.post(
        f"/api/projects/{project_id}/milestones",
        json=milestone_payload,
        headers=member_headers,
    )
    assert resp_mile_maint.status_code == 201
    milestone_id = resp_mile_maint.json()["id"]

    # 6. Post Announcement (POST /projects/{project_id}/announcements)
    announcement_payload = {
        "title": "Weekly Kickoff",
        "content": "Make sure to update your assigned tasks before Friday.",
    }
    # Standard Member should fail
    resp_ann_reg = client.post(
        f"/api/projects/{project_id}/announcements",
        json=announcement_payload,
        headers=regular_headers,
    )
    assert resp_ann_reg.status_code == 403

    # Maintainer should succeed
    resp_ann_maint = client.post(
        f"/api/projects/{project_id}/announcements",
        json=announcement_payload,
        headers=member_headers,
    )
    assert resp_ann_maint.status_code == 201
    announcement_id = resp_ann_maint.json()["id"]

    # 7. Complete Milestone (PATCH /projects/{project_id}/milestones/{milestone_id}/complete)
    # Maintainer completes it
    resp_comp = client.patch(
        f"/api/projects/{project_id}/milestones/{milestone_id}/complete?is_completed=true",
        headers=member_headers,
    )
    assert resp_comp.status_code == 200
    assert resp_comp.json()["is_completed"] is True

    # 8. Check Dashboard data again
    resp_dash = client.get(
        f"/api/projects/{project_id}/dashboard", headers=owner_headers
    )
    dash_data = resp_dash.json()

    assert len(dash_data["milestones"]) == 1
    assert dash_data["milestones"][0]["is_completed"] is True

    assert len(dash_data["announcements"]) == 1
    assert dash_data["announcements"][0]["title"] == "Weekly Kickoff"
    assert dash_data["announcements"][0]["author"]["id"] == member_id

    # Verify activities are tracked in dashboard
    assert len(dash_data["recent_activity"]) >= 3
    # Check that Activity Types match milestone created/completed and announcement posted
    types = [act["activity_type"] for act in dash_data["recent_activity"]]
    assert ActivityType.PROJECT_MILESTONE in types
    assert ActivityType.PROJECT_ANNOUNCEMENT in types
