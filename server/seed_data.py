"""
Seed database with initial test data for Phase C3.
Run this after migrations to populate ships, planets, sectors, and users.
"""
import asyncio
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models import Base, User, Ship, Planet, Sector, Team

async def seed_database():
    """Seed the database with test data."""
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:dev@localhost:5432/galactic_empire")
    
    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create teams
        team1 = Team(
            id="team_alpha",
            name="Alpha Squad",
            score=1000,
            created_at=datetime.utcnow()
        )
        session.add(team1)
        
        # Create users
        users_data = [
            {"id": "player_1", "username": "Player_1", "cash": 10000, "kills": 5, "team_id": "team_alpha"},
            {"id": "player_2", "username": "Player_2", "cash": 8500, "kills": 3, "team_id": None},
            {"id": "player_3", "username": "Player_3", "cash": 12000, "kills": 7, "team_id": "team_alpha"},
        ]
        
        for user_data in users_data:
            user = User(
                id=user_data["id"],
                username=user_data["username"],
                cash=user_data["cash"],
                kills=user_data["kills"],
                planets_owned=0,
                team_id=user_data["team_id"],
                created_at=datetime.utcnow()
            )
            session.add(user)
        
        # Create sectors
        sectors_data = [
            {"id": 1, "x": 5, "y": 5, "type": "normal", "name": "Core Sector"},
            {"id": 2, "x": 5, "y": 6, "type": "nebula", "name": "Nebula Expanse"},
            {"id": 3, "x": 6, "y": 5, "type": "asteroid", "name": "Asteroid Belt Alpha"},
            {"id": 4, "x": 4, "y": 5, "type": "safe_harbor", "name": "Safe Harbor Station"},
            {"id": 5, "x": 5, "y": 4, "type": "normal", "name": "Frontier Outpost"},
        ]
        
        for sector_data in sectors_data:
            sector = Sector(
                id=sector_data["id"],
                shard_id="alpha-1",
                x=sector_data["x"],
                y=sector_data["y"],
                type=sector_data["type"],
                planet_count=0
            )
            session.add(sector)
        
        await session.flush()
        
        # Create planets
        planets_data = [
            {
                "id": 101,
                "sector_id": 1,
                "owner_id": "player_1",
                "name": "Terra Prime",
                "treasury": 5000,
                "tax_rate": 10.0,
                "production_rates": {"men": 40, "fighters": 30, "gold": 30},
                "item_stocks": {"men": 1000, "fighters": 500, "gold": 2000},
                "population": 10000
            },
            {
                "id": 102,
                "sector_id": 1,
                "owner_id": None,
                "name": "New Horizon",
                "treasury": 0,
                "tax_rate": 0.0,
                "production_rates": {},
                "item_stocks": {},
                "population": 0
            },
            {
                "id": 103,
                "sector_id": 1,
                "owner_id": "player_2",
                "name": "Mining Station 7",
                "treasury": 3000,
                "tax_rate": 8.0,
                "production_rates": {"men": 20, "food": 50},
                "item_stocks": {"men": 500, "food": 1500},
                "population": 5000
            },
        ]
        
        for planet_data in planets_data:
            planet = Planet(
                id=planet_data["id"],
                sector_id=planet_data["sector_id"],
                owner_id=planet_data["owner_id"],
                name=planet_data["name"],
                treasury=planet_data["treasury"],
                tax_rate=planet_data["tax_rate"],
                production_rates=planet_data["production_rates"],
                item_stocks=planet_data["item_stocks"],
                population=planet_data["population"],
                is_safe_harbor=0,
                safe_harbor_rent=0,
                npc_defender_count=0,
                npc_defender_strength=0.0
            )
            session.add(planet)
        
        # Update planet counts
        await session.execute(
            "UPDATE sectors SET planet_count = (SELECT COUNT(*) FROM planets WHERE planets.sector_id = sectors.id)"
        )
        
        # Create ships
        ships_data = [
            {
                "id": 201,
                "owner_id": "player_1",
                "sector_id": 1,  # Core Sector (5,5)
                "name": "USS Enterprise",
                "class_type": "frigate",
                "position_x": 5,
                "position_y": 5,
                "heading": 90.0,
                "speed": 5.0,
                "damage": 0.0,
                "energy": 80.0,
                "shields": 75.0,
                "is_docked": 0
            },
            {
                "id": 202,
                "owner_id": "player_3",
                "sector_id": 1,  # Core Sector (5,5)
                "name": "Scout Alpha",
                "class_type": "scout",
                "position_x": 5,
                "position_y": 5,
                "heading": 180.0,
                "speed": 8.0,
                "damage": 10.0,
                "energy": 90.0,
                "shields": 60.0,
                "is_docked": 0
            },
            {
                "id": 203,
                "owner_id": "player_2",
                "sector_id": 3,  # Asteroid Belt Alpha (6,5)
                "name": "Dreadnought",
                "class_type": "battleship",
                "position_x": 6,
                "position_y": 5,
                "heading": 270.0,
                "speed": 3.0,
                "damage": 5.0,
                "energy": 95.0,
                "shields": 100.0,
                "is_docked": 0
            },
        ]
        
        for ship_data in ships_data:
            ship = Ship(
                id=ship_data["id"],
                owner_id=ship_data["owner_id"],
                sector_id=ship_data["sector_id"],
                name=ship_data["name"],
                class_type=ship_data["class_type"],
                position_x=ship_data["position_x"],
                position_y=ship_data["position_y"],
                heading=ship_data["heading"],
                speed=ship_data["speed"],
                damage=ship_data["damage"],
                energy=ship_data["energy"],
                shields=ship_data["shields"],
                cargo={},
                is_docked=ship_data["is_docked"],
                docked_planet_id=None,
                insurance_active=0,
                insurance_expiry=None
            )
            session.add(ship)
        
        await session.commit()
        print("✅ Database seeded successfully!")
        print(f"   - Created {len(users_data)} users")
        print(f"   - Created {len(sectors_data)} sectors")
        print(f"   - Created {len(planets_data)} planets")
        print(f"   - Created {len(ships_data)} ships")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_database())
