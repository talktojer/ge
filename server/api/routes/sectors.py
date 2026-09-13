"""
Galaxy and Sector routes.
REST endpoints for Map client to load galaxy overview and sector details.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import structlog
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

from api.dependencies import get_current_player
from database.models import Ship, Planet, Sector, User

logger = structlog.get_logger()

router = APIRouter()

# Use get_db_session from C3b database module
from database import get_db_session


# Response models
class SectorStub(BaseModel):
    """Minimal sector info for galaxy overview."""
    id: int
    x: int
    y: int
    name: str
    sector_type: str = Field(description="normal, nebula, asteroid, safe_harbor")
    planet_count: int
    ship_count: int = Field(description="Visible ships in sector (stub)")


class ShipStub(BaseModel):
    """Minimal ship info visible in sector."""
    id: int
    owner_id: str
    owner_name: str
    class_type: str
    position_x: int
    position_y: int
    is_docked: bool


class PlanetStub(BaseModel):
    """Minimal planet info visible in sector."""
    id: int
    name: str
    owner_id: Optional[str]
    owner_name: Optional[str]
    is_safe_harbor: bool


class SectorDetail(BaseModel):
    """Full sector detail for Map client."""
    id: int
    x: int
    y: int
    name: str
    sector_type: str
    planet_count: int
    planets: List[PlanetStub]
    ships: List[ShipStub]


class GalaxyOverview(BaseModel):
    """Galaxy map overview."""
    shard_id: str = Field(description="Galaxy shard identifier")
    width: int = Field(description="Galaxy width in sectors")
    height: int = Field(description="Galaxy height in sectors")
    sectors: List[SectorStub]


# Stub data (hardcoded for Phase C2a)
STUB_GALAXY = {
    "shard_id": "alpha-1",
    "width": 10,
    "height": 10,
    "sectors": [
        {"id": 1, "x": 5, "y": 5, "name": "Core Sector", "sector_type": "normal", "planet_count": 3, "ship_count": 2},
        {"id": 2, "x": 5, "y": 6, "name": "Nebula Expanse", "sector_type": "nebula", "planet_count": 1, "ship_count": 0},
        {"id": 3, "x": 6, "y": 5, "name": "Asteroid Belt Alpha", "sector_type": "asteroid", "planet_count": 0, "ship_count": 1},
        {"id": 4, "x": 4, "y": 5, "name": "Safe Harbor Station", "sector_type": "safe_harbor", "planet_count": 1, "ship_count": 5},
        {"id": 5, "x": 5, "y": 4, "name": "Frontier Outpost", "sector_type": "normal", "planet_count": 2, "ship_count": 1},
    ]
}

STUB_SECTOR_DETAILS = {
    1: {
        "id": 1,
        "x": 5,
        "y": 5,
        "name": "Core Sector",
        "sector_type": "normal",
        "planet_count": 3,
        "planets": [
            {"id": 101, "name": "Terra Prime", "owner_id": "player_1", "owner_name": "Player_1", "is_safe_harbor": False},
            {"id": 102, "name": "New Horizon", "owner_id": None, "owner_name": None, "is_safe_harbor": False},
            {"id": 103, "name": "Mining Station 7", "owner_id": "player_2", "owner_name": "Player_2", "is_safe_harbor": False},
        ],
        "ships": [
            {"id": 201, "owner_id": "player_1", "owner_name": "Player_1", "class_type": "frigate", "position_x": 5, "position_y": 5, "is_docked": False},
            {"id": 202, "owner_id": "player_3", "owner_name": "Player_3", "class_type": "scout", "position_x": 5, "position_y": 5, "is_docked": False},
        ]
    },
    2: {
        "id": 2,
        "x": 5,
        "y": 6,
        "name": "Nebula Expanse",
        "sector_type": "nebula",
        "planet_count": 1,
        "planets": [
            {"id": 104, "name": "Hidden Base", "owner_id": "player_2", "owner_name": "Player_2", "is_safe_harbor": False},
        ],
        "ships": []
    },
    3: {
        "id": 3,
        "x": 6,
        "y": 5,
        "name": "Asteroid Belt Alpha",
        "sector_type": "asteroid",
        "planet_count": 0,
        "planets": [],
        "ships": [
            {"id": 203, "owner_id": "player_1", "owner_name": "Player_1", "class_type": "miner", "position_x": 6, "position_y": 5, "is_docked": False},
        ]
    },
    4: {
        "id": 4,
        "x": 4,
        "y": 5,
        "name": "Safe Harbor Station",
        "sector_type": "safe_harbor",
        "planet_count": 1,
        "planets": [
            {"id": 105, "name": "Safe Harbor Alpha", "owner_id": None, "owner_name": None, "is_safe_harbor": True},
        ],
        "ships": [
            {"id": 204, "owner_id": "player_1", "owner_name": "Player_1", "class_type": "frigate", "position_x": 4, "position_y": 5, "is_docked": True},
            {"id": 205, "owner_id": "player_2", "owner_name": "Player_2", "class_type": "battleship", "position_x": 4, "position_y": 5, "is_docked": True},
            {"id": 206, "owner_id": "player_3", "owner_name": "Player_3", "class_type": "scout", "position_x": 4, "position_y": 5, "is_docked": True},
            {"id": 207, "owner_id": "player_4", "owner_name": "Player_4", "class_type": "frigate", "position_x": 4, "position_y": 5, "is_docked": True},
            {"id": 208, "owner_id": "player_5", "owner_name": "Player_5", "class_type": "scout", "position_x": 4, "position_y": 5, "is_docked": True},
        ]
    },
    5: {
        "id": 5,
        "x": 5,
        "y": 4,
        "name": "Frontier Outpost",
        "sector_type": "normal",
        "planet_count": 2,
        "planets": [
            {"id": 106, "name": "Frontier Alpha", "owner_id": "player_1", "owner_name": "Player_1", "is_safe_harbor": False},
            {"id": 107, "name": "Outpost Beta", "owner_id": None, "owner_name": None, "is_safe_harbor": False},
        ],
        "ships": [
            {"id": 209, "owner_id": "player_2", "owner_name": "Player_2", "class_type": "frigate", "position_x": 5, "position_y": 4, "is_docked": False},
        ]
    },
}


@router.get("/", response_model=GalaxyOverview)
async def get_galaxy_overview(player_id: str = Depends(get_current_player)):
    """
    GET /sectors - Galaxy overview with all sector stubs.
    
    Returns:
        GalaxyOverview: shard_id, dimensions, and list of sector stubs
    
    Requires: Bearer token authentication
    
    Phase C2a: Stub implementation with hardcoded small galaxy.
    Future: Query database for real galaxy data.
    """
    logger.info("galaxy_overview_requested", player_id=player_id)
    
    return GalaxyOverview(**STUB_GALAXY)


@router.get("/{sector_id}", response_model=SectorDetail)
async def get_sector_detail(
    sector_id: int,
    player_id: str = Depends(get_current_player)
):
    """
    GET /sectors/{sector_id} - Detailed sector data.
    
    Returns:
        SectorDetail: Full sector info including planets and ships
    
    Requires: Bearer token authentication
    
    Phase C3: Query database for real-time sector state.
    """
    logger.info("sector_detail_requested", sector_id=sector_id, player_id=player_id)
    
    async with async_session_maker() as session:
        # Load sector
        sector_result = await session.execute(
            select(Sector).where(Sector.id == sector_id)
        )
        sector = sector_result.scalar_one_or_none()
        
        if not sector:
            # Fall back to stub data if sector not in DB
            if sector_id not in STUB_SECTOR_DETAILS:
                raise HTTPException(
                    status_code=404,
                    detail=f"Sector {sector_id} not found"
                )
            return SectorDetail(**STUB_SECTOR_DETAILS[sector_id])
        
        # Load ships in this sector
        ships_result = await session.execute(
            select(Ship, User.username).join(User, Ship.owner_id == User.id)
            .where(Ship.position_x == sector.x)
            .where(Ship.position_y == sector.y)
        )
        ships_data = ships_result.all()
        
        ships = [
            ShipStub(
                id=ship.id,
                owner_id=ship.owner_id,
                owner_name=username or "Unknown",
                class_type=ship.class_type,
                position_x=ship.position_x,
                position_y=ship.position_y,
                is_docked=bool(ship.is_docked)
            )
            for ship, username in ships_data
        ]
        
        # Load planets in this sector
        planets_result = await session.execute(
            select(Planet, User.username)
            .outerjoin(User, Planet.owner_id == User.id)
            .where(Planet.sector_id == sector_id)
        )
        planets_data = planets_result.all()
        
        planets = [
            PlanetStub(
                id=planet.id,
                name=planet.name,
                owner_id=planet.owner_id,
                owner_name=username,
                is_safe_harbor=bool(planet.is_safe_harbor)
            )
            for planet, username in planets_data
        ]
        
        return SectorDetail(
            id=sector.id,
            x=sector.x,
            y=sector.y,
            name=f"Sector ({sector.x}, {sector.y})",
            sector_type=sector.type or "normal",
            planet_count=len(planets),
            planets=planets,
            ships=ships
        )
