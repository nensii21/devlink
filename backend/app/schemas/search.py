from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid

class SearchSuggestionUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    username: str
    role: Optional[str] = None
    profile_image: Optional[str] = None

class SearchSuggestionProject(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    icon: Optional[str] = None # Will map logo_url if any

class SearchSuggestionSkill(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str

class SearchAutocompleteResponse(BaseModel):
    users: List[SearchSuggestionUser]
    projects: List[SearchSuggestionProject]
    skills: List[SearchSuggestionSkill]
