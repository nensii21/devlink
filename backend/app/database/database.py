from sqlalchemy import create_engine

from app.core.config import settings

# --------------------------------------------------------------------
# SQLAlchemy Engine
# --------------------------------------------------------------------

engine_kwargs = {}
if "sqlite" not in settings.DATABASE_URL:
    engine_kwargs.update({"pool_size": 10, "max_overflow": 20})

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    echo=settings.DEBUG,
    **engine_kwargs,
)
