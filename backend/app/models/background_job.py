from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class BackgroundJob(Base):
    """
    Background Job Monitoring Model
    """

    __tablename__ = "background_jobs"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )

    task_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    status: Mapped[JobStatus] = mapped_column(
        SqlEnum(JobStatus),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
    )

    payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    queue: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    worker: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    retries: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    processing_time: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self):
        return f"<BackgroundJob(id='{self.id}', name='{self.task_name}', status='{self.status.value}')>"
