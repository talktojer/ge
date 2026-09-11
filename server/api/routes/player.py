"""
Player routes.
Profile, ships, planets.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import structlog

logger = structlog.get_logger()

router = APIRouter()

class PlayerProfile(BaseModel):
    player_id: str
    username: str
    cash: int
    kills: int
    planets_owned: int
    team_id: str | None

class Ship(BaseModel):
    ship_id: int
    name: str
    position_x: int
    position_y: int
    damage: float
    energy: float
    cargo: dict

class Planet(BaseModel):
    planet_id: int
    name: str
    sector_x: int
    sector_y: int
    owner_id: str
    treasury: int
    production_rates: dict

@router.get("/profile", response_model=PlayerProfile)
async def get_player_profile():
    """
    Get player profile.
    TODO: Extract player_id from JWT
    TODO: Query Postgres for player data
    TODO: Return profile
    """
    raise HTTPException(status_code=501, detail="Not implemented (Phase B scaffold)")

@router.get("/ships", response_model=List[Ship])
async def get_player_ships():
    """
    Get player ships.
    TODO: Extract player_id from JWT
    TODO: Query Postgres for player ships
    TODO: Return ship list
    """
    raise HTTPException(status_code=501, detail="Not implemented (Phase B scaffold)")

@router.get("/planets", response_model=List[Planet])
async def get_player_planets():
    """
    Get player planets.
    TODO: Extract player_id from JWT
    TODO: Query Postgres for player planets
    TODO: Return planet list
    """
    raise HTTPException(status_code=501, detail="Not implemented (Phase B scaffold)")
