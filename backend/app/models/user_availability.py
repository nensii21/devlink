import uuid
from datetime import date
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserAvailability(Base):
    """
    User availability scheduling table.
    """

    __tablename__ = "user_availability"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One availability setting per user
    )

    timezone: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="UTC",
    )

    working_hours: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )

    meeting_duration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        server_default="30",
    )

    vacation_mode: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    vacation_start: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    vacation_end: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    user = relationship("User", back_populates="availability_setting")

    def __repr__(self) -> str:
        return (
            f"<UserAvailability(user_id='{self.user_id}', timezone='{self.timezone}')>"
        )
