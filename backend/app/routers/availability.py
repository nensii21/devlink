import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database
from app.models.user import User
from app.models.user_availability import UserAvailability
from app.schemas.availability import AvailabilityResponse, AvailabilityUpdate

router = APIRouter(tags=["Availability"])


@router.get("/me", response_model=AvailabilityResponse)
def get_my_availability(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """
    Get the current user's availability settings.
    Creates default settings if none exist.
    """
    availability = (
        db.query(UserAvailability)
        .filter(UserAvailability.user_id == current_user.id)
        .first()
    )
    if not availability:
        availability = UserAvailability(user_id=current_user.id)
        db.add(availability)
        db.commit()
        db.refresh(availability)

    # We must construct working_hours if it's a string from db or empty
    return availability


@router.put("/me", response_model=AvailabilityResponse)
def update_my_availability(
    update_data: AvailabilityUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """
    Update the current user's availability settings.
    """
    availability = (
        db.query(UserAvailability)
        .filter(UserAvailability.user_id == current_user.id)
        .first()
    )
    if not availability:
        availability = UserAvailability(user_id=current_user.id)
        db.add(availability)

    availability.timezone = update_data.timezone
    # The JSONB field expects python dict which is dumped to JSON implicitly by SQLAlchemy
    working_hours_dict = {}
    for day, slots in update_data.working_hours.items():
        working_hours_dict[day] = [slot.model_dump() for slot in slots]

    availability.working_hours = working_hours_dict
    availability.meeting_duration = update_data.meeting_duration
    availability.vacation_mode = update_data.vacation_mode
    availability.vacation_start = update_data.vacation_start
    availability.vacation_end = update_data.vacation_end

    db.commit()
    db.refresh(availability)
    return availability


@router.get("/{username}", response_model=AvailabilityResponse)
def get_user_availability(
    username: str,
    db: Session = Depends(get_database),
):
    """
    Get the public availability settings for a user.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    availability = (
        db.query(UserAvailability).filter(UserAvailability.user_id == user.id).first()
    )
    if not availability:
        # Return defaults if none
        return AvailabilityResponse(
            id=uuid.uuid4(),
            user_id=user.id,
            timezone="UTC",
            working_hours={},
            meeting_duration=30,
            vacation_mode=False,
        )
    return availability
