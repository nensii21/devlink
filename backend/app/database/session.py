from typing import Generator

from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.database.database import engine

# --------------------------------------------------------------------
# Session Factory
# --------------------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# --------------------------------------------------------------------
# Dependency
# --------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency.

    Example:

        @router.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()