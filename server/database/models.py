"""
Database models and connection.
SQLAlchemy async models for Postgres.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime
import structlog

logger = structlog.get_logger()

Base = declarative_base()

class User(Base):
    """Player account."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)  # Firebase UID
    username = Column(String, unique=True, nullable=False)
    cash = Column(Integer, default=10000)  # Starting cash per game design
    kills = Column(Integer, default=0)
    planets_owned = Column(Integer, default=0)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    created_at = Column(DateTime)
    
    # TODO: Add relationships (ships, planets, mail)

class Ship(Base):
    """Player ship."""
    __tablename__ = "ships"
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    class_type = Column(String, nullable=False)  # "scout", "frigate", "battleship"
    position_x = Column(Integer, nullable=False)
    position_y = Column(Integer, nullable=False)
    heading = Column(Float, default=0.0)
    speed = Column(Float, default=0.0)
    damage = Column(Float, default=0.0)  # 0.0 to 100.0 (100 = destroyed)
    energy = Column(Float, default=100.0)
    shields = Column(Float, default=100.0)
    cargo = Column(JSON, default={})  # {item_type: quantity}
    
    # TODO: Add equipment slots, status flags (cloaked, docked)

class Sector(Base):
    """Galaxy sector."""
    __tablename__ = "sectors"
    
    id = Column(Integer, primary_key=True)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    type = Column(String, default="normal")  # "normal", "nebula", "asteroid"
    wormhole_target_id = Column(Integer, ForeignKey("sectors.id"), nullable=True)
    planet_count = Column(Integer, default=0)
    
    # TODO: Add unique constraint on (x, y)

class Planet(Base):
    """Planet."""
    __tablename__ = "planets"
    
    id = Column(Integer, primary_key=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    treasury = Column(Integer, default=0)
    tax_rate = Column(Float, default=10.0)  # Percentage
    production_rates = Column(JSON, default={})  # {Men: 40, Fighters: 30, Gold: 30}
    item_stocks = Column(JSON, default={})  # {item_type: quantity}
    population = Column(Integer, default=0)
    
    # TODO: Add production caps, spy count, defender NPC config

class Team(Base):
    """Alliance/team."""
    __tablename__ = "teams"
    
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    score = Column(Integer, default=0)
    created_at = Column(DateTime)
    
    # TODO: Add members relationship

# TODO: Add Mail, CombatLog, TradeHistory tables

# Database connection pool
async def create_db_pool(database_url: str):
    """
    Create async Postgres connection pool.
    TODO: Use asyncpg driver
    TODO: Configure pool size, timeouts
    TODO: Return engine and session maker
    """
    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # TODO: Create tables if not exist (or use Alembic migrations)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    logger.info("database_connected", url=database_url)
    return engine, async_session
