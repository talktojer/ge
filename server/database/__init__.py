"""
Database initialization and session management.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import structlog
import os

logger = structlog.get_logger()

Base = declarative_base()

# Global engine and session maker
_engine = None
_async_session_maker = None


def get_database_url() -> str:
    """Get database URL from environment."""
    return os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:dev@localhost:5432/galactic_empire")


async def init_db():
    """Initialize database connection pool."""
    global _engine, _async_session_maker
    
    if _engine is not None:
        return _engine, _async_session_maker
    
    database_url = get_database_url()
    _engine = create_async_engine(
        database_url,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        pool_size=10,
        max_overflow=20,
    )
    
    _async_session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    logger.info("database_initialized", url=database_url.split("@")[1] if "@" in database_url else "local")
    
    return _engine, _async_session_maker


async def get_db_session() -> AsyncSession:
    """
    Dependency for FastAPI routes to get database session.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(Ship).where(Ship.id == 1))
    """
    global _async_session_maker
    
    if _async_session_maker is None:
        await init_db()
    
    async with _async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db():
    """Close database connection pool."""
    global _engine
    
    if _engine:
        await _engine.dispose()
        logger.info("database_closed")
