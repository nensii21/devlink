from app.models.user import User
from app.services.project_service import ProjectService


def test_project_sorting_options(client, db, register_and_login):
    headers = register_and_login("sort_owner@example.com", "sort_owner")
    user = db.query(User).filter(User.email == "sort_owner@example.com").first()

    p1 = ProjectService.create_project(
        db,
        owner_id=user.id,
        project=type(
            "ProjectCreateMock",
            (),
            {
                "title": "Alpha Project",
                "description": "First project created for test",
                "slug": "alpha-proj-sort",
                "language": "Python",
                "experience": "Beginner",
                "is_remote": True,
                "is_paid": False,
                "is_open_source": True,
                "tech_stack": "Python, FastAPI",
                "repository_url": None,
                "demo_url": None,
            },
        )(),
    )

    # Test API sorting endpoints
    sort_options = [
        "newest",
        "oldest",
        "most_active",
        "most_bookmarked",
        "most_applications",
        "recently_updated",
        "ai_match_score",
    ]

    for sort_option in sort_options:
        response = client.get(f"/api/projects/?sort_by={sort_option}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
