from sqlalchemy import create_engine

from app.core.config import settings

# --------------------------------------------------------------------
# SQLAlchemy Engine
# --------------------------------------------------------------------

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    future=True,
    echo=settings.DEBUG,
)
