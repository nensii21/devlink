from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.connection import ConnectionStatus


class ConnectionRequest(BaseModel):
    recipient_id: uuid.UUID


class ConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requester_id: uuid.UUID
    recipient_id: uuid.UUID
    status: ConnectionStatus
    created_at: datetime
    updated_at: datetime


class ConnectionStatusResponse(BaseModel):
    status: ConnectionStatus | None
    connection_id: uuid.UUID | None
    is_connected: bool
    sent_by_me: bool


class MutualConnectionsResponse(BaseModel):
    mutual_count: int
    mutual_users: list[uuid.UUID]


class ConnectionActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requester_id: uuid.UUID
    recipient_id: uuid.UUID
    status: ConnectionStatus
    updated_at: datetime
    message: str
