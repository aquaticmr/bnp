import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.db.models import Base

logger = logging.getLogger(__name__)


def create_resilient_engine():
    """
    Attempts to connect to configured PostgreSQL instance.
    Falls back gracefully to SQLite if PostgreSQL is unreachable.
    """
    try:
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3},
        )
        with engine.connect() as conn:
            pass
        logger.info("Connected successfully to PostgreSQL database.")
        return engine
    except Exception as exc:
        logger.warning(
            "Primary PostgreSQL connection unavailable (%s). Falling back to local SQLite engine.",
            str(exc),
        )
        engine = create_engine(
            settings.SQLITE_FALLBACK_URL,
            connect_args={"check_same_thread": False},
        )
        return engine


engine = create_resilient_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
