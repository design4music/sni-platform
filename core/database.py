"""SNI-v2 Database Connection and Session Management"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from loguru import logger

from .config import get_config

# Base class for SQLAlchemy models
Base = declarative_base()

# Global engine and session factory
_engine = None
_SessionLocal = None


def init_database():
    """Initialize database connection"""
    global _engine, _SessionLocal
    
    config = get_config()
    
    _engine = create_engine(
        config.database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=config.debug
    )
    
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    
    logger.info(f"Database initialized: {config.db_name}")


def get_engine():
    """Get the SQLAlchemy engine"""
    if _engine is None:
        init_database()
    return _engine


def get_session_factory():
    """Get the session factory"""
    if _SessionLocal is None:
        init_database()
    return _SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup"""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def create_tables():
    """Create all database tables"""
    
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


def drop_tables():
    """Drop all database tables (use with caution!)"""
    
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    logger.warning("Database tables dropped")


def check_database_connection() -> bool:
    """Test database connection"""
    try:
        with get_db_session() as session:
            result = session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def get_database_stats() -> dict:
    """Get basic database statistics"""
    with get_db_session() as session:
        stats = {}
        
        # Check if tables exist and get counts
        table_queries = {
            "feeds": "SELECT COUNT(*) FROM feeds",
            "titles": "SELECT COUNT(*) FROM titles", 
            "clusters": "SELECT COUNT(*) FROM clusters",
            "narratives": "SELECT COUNT(*) FROM narratives"
        }
        
        for table, query in table_queries.items():
            try:
                result = session.execute(text(query))
                stats[table] = result.scalar()
            except Exception:
                stats[table] = "N/A (table not found)"
        
        return stats