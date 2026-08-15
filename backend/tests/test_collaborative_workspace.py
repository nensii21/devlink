import pytest
from uuid import uuid4

from app.models.project import Project, ProjectStage, ProjectVisibility
from app.models.user import User
from app.services.project_document_service import ProjectDocumentService


@pytest.fixture
def test_user(db):
    user = User(
        id=uuid4(),
        first_name="Collab",
        last_name="User",
        email=f"collab_{uuid4().hex[:6]}@example.com",
        username=f"collabuser_{uuid4().hex[:6]}",
        password_hash="hashed_password",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_project(db, test_user):
    project = Project(
        id=uuid4(),
        title="Collab Test Project",
        slug=f"collab-project-{uuid4().hex[:6]}",
        description="Collaborative workspace test project",
        owner_id=test_user.id,
        stage=ProjectStage.IDEA,
        visibility=ProjectVisibility.PUBLIC,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def test_create_and_get_workspace_document(db, test_project, test_user):
    doc = ProjectDocumentService.create_document(
        db,
        project_id=test_project.id,
        user_id=test_user.id,
        title="Architecture Specs",
        content="# Realtime Collab Specs",
    )

    assert doc.id is not None
    assert doc.title == "Architecture Specs"
    assert doc.content == "# Realtime Collab Specs"
    assert doc.version == 1
    assert doc.created_by_id == test_user.id

    fetched = ProjectDocumentService.get_document(db, doc.id)
    assert fetched.id == doc.id
    assert fetched.title == "Architecture Specs"


def test_list_workspace_documents(db, test_project, test_user):
    doc1 = ProjectDocumentService.create_document(
        db,
        project_id=test_project.id,
        user_id=test_user.id,
        title="Doc 1",
    )
    doc2 = ProjectDocumentService.create_document(
        db,
        project_id=test_project.id,
        user_id=test_user.id,
        title="Doc 2",
    )

    docs = ProjectDocumentService.list_project_documents(db, test_project.id)
    assert len(docs) >= 2
    doc_ids = [d.id for d in docs]
    assert doc1.id in doc_ids
    assert doc2.id in doc_ids


def test_update_workspace_document_without_conflict(db, test_project, test_user):
    doc = ProjectDocumentService.create_document(
        db,
        project_id=test_project.id,
        user_id=test_user.id,
        title="Initial Title",
        content="Initial Content",
    )

    updated, conflict = ProjectDocumentService.update_document(
        db,
        doc_id=doc.id,
        user_id=test_user.id,
        title="Updated Title",
        content="Updated Content",
        base_version=1,
    )

    assert conflict is False
    assert updated.title == "Updated Title"
    assert updated.content == "Updated Content"
    assert updated.version == 2


def test_update_workspace_document_with_conflict(db, test_project, test_user):
    doc = ProjectDocumentService.create_document(
        db,
        project_id=test_project.id,
        user_id=test_user.id,
        title="Version 1",
        content="First Version",
    )

    # User A updates to Version 2
    ProjectDocumentService.update_document(
        db,
        doc_id=doc.id,
        user_id=test_user.id,
        content="Second Version by User A",
        base_version=1,
    )

    # User B updates based on outdated base_version 1
    updated_b, conflict_b = ProjectDocumentService.update_document(
        db,
        doc_id=doc.id,
        user_id=test_user.id,
        content="Third Version by User B",
        base_version=1,
    )

    assert conflict_b is True
    assert updated_b.version == 3
    assert (
        "Conflict Resolved" in updated_b.content
        or "Third Version by User B" in updated_b.content
    )


def test_delete_workspace_document(db, test_project, test_user):
    doc = ProjectDocumentService.create_document(
        db,
        project_id=test_project.id,
        user_id=test_user.id,
        title="Temp Doc",
    )

    ProjectDocumentService.delete_document(db, doc.id)

    with pytest.raises(Exception):
        ProjectDocumentService.get_document(db, doc.id)


from app.core.security import create_access_token


@pytest.fixture
def token_headers():
    def _headers(user):
        token = create_access_token(user_id=str(user.id))
        return {"Authorization": f"Bearer {token}"}

    return _headers


def test_rest_api_workspace_docs_endpoints(
    client, test_project, test_user, token_headers
):
    # Create doc via REST API
    res = client.post(
        f"/api/v1/projects/{test_project.id}/workspace/docs",
        json={"title": "API Doc", "content": "API Content"},
        headers=token_headers(test_user),
    )
    assert res.status_code == 201
    data = res.json()
    doc_id = data["id"]
    assert data["title"] == "API Doc"
    assert data["version"] == 1

    # List docs
    res_list = client.get(
        f"/api/v1/projects/{test_project.id}/workspace/docs",
        headers=token_headers(test_user),
    )
    assert res_list.status_code == 200
    assert res_list.json()["total"] >= 1

    # Update doc
    res_update = client.put(
        f"/api/v1/projects/{test_project.id}/workspace/docs/{doc_id}",
        json={
            "title": "Updated API Doc",
            "content": "New API Content",
            "base_version": 1,
        },
        headers=token_headers(test_user),
    )
    assert res_update.status_code == 200
    assert res_update.json()["version"] == 2
    assert res_update.json()["conflict"] is False

    # Delete doc
    res_del = client.delete(
        f"/api/v1/projects/{test_project.id}/workspace/docs/{doc_id}",
        headers=token_headers(test_user),
    )
    assert res_del.status_code == 204
