from pydantic import BaseModel
from app.schemas.user import UserResponse
from app.schemas.project import ProjectResponse

class SearchResult(BaseModel):
    users: list[UserResponse] = []
    projects: list[ProjectResponse] = []
