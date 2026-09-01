import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


settings = get_settings()

engine = create_engine(
    settings.sync_database_url,
    pool_pre_ping=True,
    pool_recycle=300,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> dict[str, object]:
    """Verify connectivity to the configured database and return status metadata."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            return {
                "online": True if result == 1 else False,
                "status": "connected",
            }
    except Exception as exc:
        logger.warning("Database connectivity check failed: %s", exc)
        return {
            "online": False,
            "status": "disconnected",
            "error": str(exc),
        }

