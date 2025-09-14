"""
Base database model and configuration
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

# Lazy initialization of engine and session
_engine = None
_SessionLocal = None

def get_engine():
    """Get database engine, initializing if needed"""
    global _engine
    if _engine is None:
        from app.core.config import settings
        _engine = create_engine(
            settings.database_url,
            echo=settings.environment == "development",
            pool_pre_ping=True,
            pool_recycle=300,
        )
    return _engine

def get_session_factory():
    """Get session factory, initializing if needed"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

def get_db():
    """Dependency to get database session"""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
