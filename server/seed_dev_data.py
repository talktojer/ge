#!/usr/bin/env python3
"""
Seed script for Phase C3b development data.
Populates database with ships and planets matching C3a in-memory stores.
"""
import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from database.models import Base, Ship, Planet, Sector, User
import structlog

logger = structlog.get_logger()


async def seed_database():
    """Seed database with development data for testing commands."""
    
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:dev@localhost:5432/galactic_empire")
    
    logger.info("seed_start", database_url=database_url.split("@")[1] if "@" in database_url else "local")
    
    engine = create_async_engine(database_url, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("tables_created_or_verified")
        
        async with async_session_maker() as session:
            # Check if data already exists
            result = await session.execute(select(Ship).where(Ship.id == 201))
            existing_ship = result.scalar_one_or_none()
            
            if existing_ship:
                logger.info("seed_data_already_exists", message="Skipping seed (ship 201 exists)")
                return
            
            # Seed users first (no FK dependencies)
            users = [
                User(id="player_1", username="TestPlayer1", cash=10000, kills=0, planets_owned=0),
                User(id="player_2", username="TestPlayer2", cash=10000, kills=0, planets_owned=0),
                User(id="player_3", username="TestPlayer3", cash=10000, kills=0, planets_owned=0),
            ]
            
            for user in users:
                session.add(user)
            
            await session.flush()  # Flush users before sectors (no dependencies between them, but good practice)
            logger.info("users_seeded", count=len(users))
            
            # Seed sectors (no FK dependencies except optional self-reference)
            sectors = [
                Sector(id=1, shard_id="main", x=0, y=0, type="normal", planet_count=3),
                Sector(id=2, shard_id="main", x=1, y=0, type="normal", planet_count=0),
                Sector(id=3, shard_id="main", x=0, y=1, type="normal", planet_count=0),
            ]
            
            for sector in sectors:
                session.add(sector)
            
            await session.flush()  # Flush sectors before planets/ships (they depend on sectors)
            logger.info("sectors_seeded", count=len(sectors))
            
            # Seed planets (depend on sectors via sector_id FK)
            planets = [
                Planet(
                    id=101,
                    sector_id=1,
                    owner_id="player_1",
                    name="Terra Prime",
                    treasury=0,
                    tax_rate=10.0,
                    population=0,
                ),
                Planet(
                    id=102,
                    sector_id=1,
                    owner_id=None,  # Unowned, available for claiming
                    name="New Horizon",
                    treasury=0,
                    tax_rate=10.0,
                    population=0,
                ),
                Planet(
                    id=103,
                    sector_id=1,
                    owner_id="player_2",
                    name="Mining Station 7",
                    treasury=0,
                    tax_rate=10.0,
                    population=0,
                ),
            ]
            
            for planet in planets:
                session.add(planet)
            
            logger.info("planets_seeded", count=len(planets))
            
            # Seed ships (depend on sectors via sector_id FK, matching C3a in-memory stores)
            ships = [
                Ship(
                    id=201,
                    owner_id="player_1",
                    name="Test Frigate",
                    class_type="frigate",
                    position_x=5,
                    position_y=5,
                    heading=90.0,
                    speed=5.0,
                    damage=0.0,
                    energy=100.0,
                    shields=100.0,
                ),
                Ship(
                    id=202,
                    owner_id="player_3",
                    name="Scout Alpha",
                    class_type="scout",
                    position_x=5,
                    position_y=5,
                    heading=180.0,
                    speed=3.0,
                    damage=0.0,
                    energy=100.0,
                    shields=100.0,
                ),
                Ship(
                    id=203,
                    owner_id="player_1",
                    name="Mining Vessel",
                    class_type="miner",
                    position_x=6,
                    position_y=5,
                    heading=0.0,
                    speed=2.0,
                    damage=0.0,
                    energy=100.0,
                    shields=100.0,
                ),
            ]
            
            # Assign sector_id based on position (ships 201, 202 in sector 1; ship 203 in sector 3)
            ships[0].sector_id = 1  # ship 201
            ships[1].sector_id = 1  # ship 202
            ships[2].sector_id = 3  # ship 203
            
            for ship in ships:
                session.add(ship)
            
            logger.info("ships_seeded", count=len(ships))
            
            # Commit all changes (after FK dependencies are satisfied)
            await session.commit()
            logger.info("seed_complete", message="Database seeded successfully")
            
    except Exception as e:
        logger.error("seed_failed", error=str(e))
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
