# pyrefly: ignore [missing-import]
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    """

    pass

# Import all models so SQLAlchemy registers them
import app.models