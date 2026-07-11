import uuid
from app.database.session import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.skill import Skill
from app.models.builder_flare import BuilderFlare

def test_search_empty_query(client):
    response = client.get("/search/?q=xyz")
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "projects" in data
    assert "skills" in data
    assert "flares" in data
    assert type(data["users"]) is list
    assert type(data["projects"]) is list
    assert type(data["skills"]) is list
    assert type(data["flares"]) is list

def test_search_with_results(client):
    db = SessionLocal()
    # Create test objects with unique names
    unique_suffix = str(uuid.uuid4())[:8]
    
    test_user = User(
        first_name=f"TestFirst_{unique_suffix}",
        last_name="TestLast",
        username=f"testuser_{unique_suffix}",
        email=f"testuser_{unique_suffix}@example.com",
        password_hash="fakehash",
        headline=f"Headline search_match_{unique_suffix}"
    )
    
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    test_project = Project(
        title=f"Project search_match_{unique_suffix}",
        slug=f"project-slug-{unique_suffix}",
        description="This is a test project description",
        owner_id=test_user.id
    )
    
    test_skill = Skill(
        name=f"Skill search_match_{unique_suffix}",
        slug=f"skill-slug-{unique_suffix}",
        category="TestCategory",
        description="Test skill description"
    )
    
    db.add(test_project)
    db.add(test_skill)
    db.commit()
    db.refresh(test_project)
    db.refresh(test_skill)
    
    test_flare = BuilderFlare(
        title=f"Flare search_match_{unique_suffix}",
        description="We need builders for this project",
        role="Frontend Engineer",
        project_id=test_project.id,
        created_by=test_user.id
    )
    
    db.add(test_flare)
    db.commit()
    db.refresh(test_flare)
    
    try:
        # Perform query matching "search_match_<unique_suffix>"
        response = client.get(f"/search/?q=search_match_{unique_suffix}")
        assert response.status_code == 200
        data = response.json()
        
        # Check matching User
        assert len(data["users"]) == 1
        assert data["users"][0]["first_name"] == f"TestFirst_{unique_suffix}"
        
        # Check matching Project
        assert len(data["projects"]) == 1
        assert data["projects"][0]["title"] == f"Project search_match_{unique_suffix}"
        
        # Check matching Skill
        assert len(data["skills"]) == 1
        assert data["skills"][0]["name"] == f"Skill search_match_{unique_suffix}"
        
        # Check matching Flare
        assert len(data["flares"]) == 1
        assert data["flares"][0]["title"] == f"Flare search_match_{unique_suffix}"
        
    finally:
        # Cleanup
        db.delete(test_flare)
        db.delete(test_skill)
        db.delete(test_project)
        db.delete(test_user)
        db.commit()
        db.close()

