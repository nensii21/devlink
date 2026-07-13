from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.repository import RepositoryProvider


class RepositoryCreate(BaseModel):
    project_id: uuid.UUID
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
    is_private: bool = False


class RepositoryUpdate(BaseModel):
    description: Optional[str] = None
    default_branch: Optional[str] = None
    clone_url: Optional[str] = None
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
    last_synced_at: Optional[datetime] = None


class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    connected_by: Optional[uuid.UUID] = None
    provider: RepositoryProvider
    repository_id: Optional[str] = None
    owner: str
    name: str
    full_name: str
    description: Optional[str] = None
    default_branch: str
    clone_url: Optional[str] = None
    html_url: str
    homepage: Optional[str] = None
    language: Optional[str] = None
    stars: int
    forks: int
    watchers: int
    open_issues: int
    contributors: int
    is_private: bool
    archived: bool
    synced: bool
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
