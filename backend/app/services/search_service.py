from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.models.project import Project
from app.schemas.search import SearchResult

class SearchService:
    @staticmethod
    def search(db: Session, query: str) -> SearchResult:
        if not query or len(query.strip()) == 0:
            return SearchResult(users=[], projects=[])
            
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
        
        return SearchResult(users=users, projects=projects)
