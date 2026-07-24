from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.session import get_db
from app.dependencies import get_database
from app.models.user import User
from app.models.project import Project
from app.models.skill import Skill
from app.schemas.search import (
    SearchAutocompleteResponse,
    SearchSuggestionUser,
    SearchSuggestionProject,
    SearchSuggestionSkill,
)

router = APIRouter()

@router.get("/autocomplete", response_model=SearchAutocompleteResponse, summary="Global search autocomplete")
def autocomplete(
    q: str = Query("", min_length=0, max_length=100),
    db: Session = Depends(get_database),
):
    if not q or not q.strip():
        return SearchAutocompleteResponse(users=[], projects=[], skills=[])
        
    query_str = f"%{q.strip()}%"

    # Search Users
    users = db.query(User).filter(
        or_(
            User.username.ilike(query_str),
            User.first_name.ilike(query_str),
            User.last_name.ilike(query_str),
            User.role.ilike(query_str),
        )
    ).limit(3).all()
    
    # Format Users (name combination)
    formatted_users = [
        SearchSuggestionUser(
            id=u.id,
            name=f"{u.first_name} {u.last_name}".strip(),
            username=u.username,
            role=u.role,
            profile_image=u.profile_image
        )
        for u in users
    ]

    # Search Projects
    projects = db.query(Project).filter(
        or_(
            Project.title.ilike(query_str),
            Project.tagline.ilike(query_str),
            Project.description.ilike(query_str),
        )
    ).limit(3).all()
    
    formatted_projects = [
        SearchSuggestionProject(
            id=p.id,
            title=p.title,
            icon=p.logo_url or "🚀"  # Fallback to emoji or logo_url
        )
        for p in projects
    ]

    # Search Skills
    skills = db.query(Skill).filter(
        Skill.name.ilike(query_str)
    ).limit(3).all()
    
    formatted_skills = [
        SearchSuggestionSkill(
            id=s.id,
            name=s.name,
        )
        for s in skills
    ]

    return SearchAutocompleteResponse(
        users=formatted_users,
        projects=formatted_projects,
        skills=formatted_skills,
    )
