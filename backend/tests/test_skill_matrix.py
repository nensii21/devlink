import pytest
from app.models.user_skill import UserSkill, SkillLevel
from app.models.skill import Skill

def test_get_skill_matrix(client, register_and_login):
    _, token = register_and_login("skillmatrix1@example.com", "skillmatrix1")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/skills-matrix/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "skills_by_category" in data
    assert "total_skills" in data
    assert "Languages" in data["skills_by_category"]
    assert "Frameworks" in data["skills_by_category"]
    assert "Databases" in data["skills_by_category"]
    assert "Cloud" in data["skills_by_category"]
    assert "DevOps" in data["skills_by_category"]
    assert "AI/ML" in data["skills_by_category"]
    assert "Design" in data["skills_by_category"]

def test_update_skill_matrix(client, register_and_login):
    _, token = register_and_login("skillmatrix2@example.com", "skillmatrix2")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "skills": [
            {
                "name": "Python",
                "category": "Languages",
                "level": "expert",
                "years_of_experience": 5
            },
            {
                "name": "React",
                "category": "Frameworks",
                "level": "advanced",
                "years_of_experience": 3
            },
            {
                "name": "PostgreSQL",
                "category": "Databases",
                "level": "intermediate",
                "years_of_experience": 2
            },
            {
                "name": "AWS",
                "category": "Cloud",
                "level": "beginner",
                "years_of_experience": 1
            },
            {
                "name": "Docker",
                "category": "DevOps",
                "level": "intermediate",
                "years_of_experience": 2
            },
            {
                "name": "PyTorch",
                "category": "AI/ML",
                "level": "beginner",
                "years_of_experience": 1
            },
            {
                "name": "Figma",
                "category": "Design",
                "level": "intermediate",
                "years_of_experience": 2
            }
        ]
    }

    res = client.put("/api/skills-matrix/me", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_skills"] == 7
    assert len(data["skills_by_category"]["Languages"]) == 1
    assert data["skills_by_category"]["Languages"][0]["name"] == "Python"
    assert data["skills_by_category"]["Languages"][0]["level"] == "Expert"
