"""
Database models and connection.
SQLAlchemy async models for Postgres.
"""
from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime
from database import Base
import structlog

logger = structlog.get_logger()

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
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=False)
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
    
    # Safe Harbor & Insurance (per PHASE1B_GAME_DESIGN.md §8.2, §8.6)
    is_docked = Column(Integer, default=0)  # Boolean: docked at Safe Harbor (invulnerable)
    docked_planet_id = Column(Integer, ForeignKey("planets.id"), nullable=True)
    insurance_active = Column(Integer, default=0)  # Boolean: has active insurance policy
    insurance_expiry = Column(DateTime, nullable=True)  # When insurance expires
    
    # TODO: Add equipment slots, status flags (cloaked)

class Sector(Base):
    """Galaxy sector."""
    __tablename__ = "sectors"
    
    id = Column(Integer, primary_key=True)
    shard_id = Column(String, nullable=False)  # Galaxy shard identifier (per PHASE1B_GAME_DESIGN.md §8.1)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    type = Column(String, default="normal")  # "normal", "nebula", "asteroid", "safe_harbor"
    wormhole_target_id = Column(Integer, ForeignKey("sectors.id"), nullable=True)
    planet_count = Column(Integer, default=0)
    
    # TODO: Add unique constraint on (shard_id, x, y)

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
    
    # Safe Harbor & NPC Defenders (per PHASE1B_GAME_DESIGN.md §8.2)
    is_safe_harbor = Column(Integer, default=0)  # Boolean: NPC citadel with docking protection
    safe_harbor_rent = Column(Integer, default=100)  # Cost per hour to dock (invulnerable)
    npc_defender_count = Column(Integer, default=0)  # NPC defense fleet count
    npc_defender_strength = Column(Float, default=0.0)  # Total NPC defender combat power
    
    # TODO: Add production caps, spy count

class Team(Base):
    """Alliance/team."""
    __tablename__ = "teams"
    
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    score = Column(Integer, default=0)
    created_at = Column(DateTime)
    
    # TODO: Add members relationship

# TODO: Add Mail, CombatLog, TradeHistory tables

# Database connection and session management now in database/__init__.py
