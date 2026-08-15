from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.project import Project, ProjectStage, ProjectVisibility
from app.models.user import User
from app.services.project_analytics_service import ProjectAnalyticsService


@pytest.fixture
def analytics_data(db: Session):
    owner = User(
        id=uuid.uuid4(),
        email="analytics_owner@example.com",
        username="analytics_owner",
        first_name="Analytics",
        last_name="Owner",
        password_hash="hashed_password",
        is_active=True,
    )
    viewer = User(
        id=uuid.uuid4(),
        email="analytics_viewer@example.com",
        username="analytics_viewer",
        first_name="Analytics",
        last_name="Viewer",
        password_hash="hashed_password",
        is_active=True,
    )
    project = Project(
        id=uuid.uuid4(),
        owner_id=owner.id,
        title="Analytics Test Project",
        slug="analytics-test-project",
        description="Testing project page view analytics",
        stage=ProjectStage.MVP,
        visibility=ProjectVisibility.PUBLIC,
        views=0,
    )
    db.add_all([owner, viewer, project])
    db.commit()
    return owner, viewer, project


def test_record_view_service(db: Session, analytics_data):
    _, viewer, project = analytics_data

    # Record 2 views for project
    v1 = ProjectAnalyticsService.record_view(
        db,
        project_id=project.id,
        viewer_id=viewer.id,
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
    )
    v2 = ProjectAnalyticsService.record_view(
        db,
        project_id=project.id,
        viewer_id=None,
        ip_address="192.168.1.2",
        user_agent="Safari/14.0",
    )

    assert v1 is not None
    assert v2 is not None

    analytics = ProjectAnalyticsService.get_analytics(db, project.id, days=7)
    assert analytics.project_id == project.id
    assert analytics.total_views >= 2
    assert analytics.unique_viewers >= 2
    assert len(analytics.daily_views) == 7


def test_project_get_endpoint_records_view(
    client: TestClient, db: Session, analytics_data
):
    owner, viewer, project = analytics_data
    token = create_access_token(str(viewer.id))
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch project endpoint
    res = client.get(f"/api/projects/{project.id}", headers=headers)
    assert res.status_code == 200

    # Check analytics endpoint
    res = client.get(f"/api/projects/{project.id}/analytics?days=14")
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == str(project.id)
    assert data["total_views"] >= 1
    assert data["unique_viewers"] >= 1
    assert len(data["daily_views"]) == 14
    today_metric = data["daily_views"][-1]
    assert today_metric["views"] >= 1


def test_project_analytics_not_found(client: TestClient):
    random_id = uuid.uuid4()
    res = client.get(f"/api/projects/{random_id}/analytics")
    assert res.status_code == 404
