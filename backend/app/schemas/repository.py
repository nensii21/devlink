from __future__ import annotations
# pyrefly: ignore [missing-import]
import uuid
from datetime import datetime
from typing import Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict
from app.models.repository import RepositoryProvider

class RepositoryBase(BaseModel):
    provider: RepositoryProvider
    repository_id: Optional[str] = None
    owner: str
    name: str
    full_name: str
    description: Optional[str] = None
    default_branch: str = "main"
    clone_url: Optional[str] = None
    html_url: str
    homepage: Optional[str] = None
    language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    open_issues: int = 0
    contributors: int = 0
    is_private: bool = False
    archived: bool = False

class RepositoryCreate(RepositoryBase):
    project_id: uuid.UUID

class RepositoryUpdate(BaseModel):
    provider: Optional[RepositoryProvider] = None
    repository_id: Optional[str] = None
    owner: Optional[str] = None
    name: Optional[str] = None
    full_name: Optional[str] = None
    description: Optional[str] = None
    default_branch: Optional[str] = None
    clone_url: Optional[str] = None
    html_url: Optional[str] = None
    homepage: Optional[str] = None
    language: Optional[str] = None
    stars: Optional[int] = None
    forks: Optional[int] = None
    watchers: Optional[int] = None
    open_issues: Optional[int] = None
    contributors: Optional[int] = None
    is_private: Optional[bool] = None
    archived: Optional[bool] = None
    synced: Optional[bool] = None

class RepositoryResponse(RepositoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    connected_by: Optional[uuid.UUID] = None
    synced: bool
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
