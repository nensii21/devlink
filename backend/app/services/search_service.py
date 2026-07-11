from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.models.project import Project
from app.models.skill import Skill
from app.models.builder_flare import BuilderFlare
from app.schemas.search import SearchResult

class SearchService:
    @staticmethod
    def search(db: Session, query: str) -> SearchResult:
        if not query or len(query.strip()) == 0:
            return SearchResult(users=[], projects=[], skills=[], flares=[])
            
        q = query.strip()
        search_pattern = f"%{q}%"
        
        users = (
            db.query(User)
            .filter(
                or_(
                    User.username.ilike(search_pattern),
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern),
                    User.headline.ilike(search_pattern)
                )
            )
            .limit(10)
            .all()
        )
        
        projects = (
            db.query(Project)
            .filter(
                or_(
                    Project.title.ilike(search_pattern),
                    Project.description.ilike(search_pattern),
                    Project.tagline.ilike(search_pattern)
                )
            )
            .limit(10)
            .all()
        )

        skills = (
            db.query(Skill)
            .filter(
                or_(
                    Skill.name.ilike(search_pattern),
                    Skill.category.ilike(search_pattern),
                    Skill.description.ilike(search_pattern)
                )
            )
            .limit(10)
            .all()
        )

        flares = (
            db.query(BuilderFlare)
            .filter(
                or_(
                    BuilderFlare.title.ilike(search_pattern),
                    BuilderFlare.description.ilike(search_pattern),
                    BuilderFlare.role.ilike(search_pattern)
                )
            )
            .limit(10)
            .all()
        )
        
        return SearchResult(users=users, projects=projects, skills=skills, flares=flares)

