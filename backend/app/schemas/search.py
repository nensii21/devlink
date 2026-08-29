from pydantic import BaseModel, ConfigDict, Field
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
    icon: Optional[str] = None  # Will map logo_url if any
    tagline: Optional[str] = None


class SearchSuggestionOrganization(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    slug: str
    logo_url: Optional[str] = None
    organization_type: Optional[str] = None
    verified: bool = False


class SearchSuggestionSkill(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    category: Optional[str] = None


class SearchSuggestionTag(BaseModel):
    name: str
    project_count: int = 0


class SearchAutocompleteResponse(BaseModel):
    users: List[SearchSuggestionUser] = []
    projects: List[SearchSuggestionProject] = []
    organizations: List[SearchSuggestionOrganization] = []
    skills: List[SearchSuggestionSkill] = []
    tags: List[SearchSuggestionTag] = []


class SearchResultUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    username: str
    role: Optional[str] = None
    headline: Optional[str] = None
    profile_image: Optional[str] = None
    location: Optional[str] = None
    is_verified: bool = False
    premium: bool = False
    experience_level: Optional[str] = None
    company: Optional[str] = None
    open_to_work: bool = True
    skills: List[str] = []


class SearchResultProject(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    slug: str
    tagline: Optional[str] = None
    description: str = ""
    logo_url: Optional[str] = None
    stage: Optional[str] = None
    stars: int = 0
    tags: List[str] = []


class SearchResultOrganization(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    organization_type: Optional[str] = None
    location: Optional[str] = None
    members_count: int = 0
    verified: bool = False
    hiring: bool = False


class SearchResultSkill(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    slug: str
    category: Optional[str] = None
    description: Optional[str] = None


class SearchResultTag(BaseModel):
    name: str
    project_count: int = 0


class SearchCounts(BaseModel):
    developers: int = 0
    projects: int = 0
    organizations: int = 0
    skills: int = 0
    tags: int = 0
    total: int = 0


# --- Semantic Search Models ---


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    types: Optional[List[str]] = Field(
        default=["projects", "profiles", "discussions", "skills"],
        description="Types of entities to search across",
    )
    limit: int = Field(default=10, ge=1, le=50)


class SearchResponse(BaseModel):
    query: str
    users: List[SearchResultUser] = []
    projects: List[SearchResultProject] = []
    organizations: List[SearchResultOrganization] = []
    skills: List[SearchResultSkill] = []
    tags: List[SearchResultTag] = []
    counts: SearchCounts = Field(default_factory=SearchCounts)
    search_method: str = Field(
        ..., description="Either 'semantic' or 'keyword_fallback'"
    )
    search_method: str = Field(
        ..., description="Either 'semantic' or 'keyword_fallback'"
    )
