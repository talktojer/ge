"""
Command routes.
Move, fire, claim, etc.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

router = APIRouter()

class MoveCommand(BaseModel):
    ship_id: int
    target_x: int
    target_y: int

class FireCommand(BaseModel):
    ship_id: int
    weapon_type: str  # "phasor" | "torpedo" | "missile"
    target_id: int

class ClaimCommand(BaseModel):
    ship_id: int
    planet_id: int

@router.post("/move")
async def move_ship(command: MoveCommand):
    """
    Move ship to target sector.
    TODO: Validate player owns ship
    TODO: Check if ship has energy for travel
    TODO: Queue command for next ge-sim tick
    TODO: Return optimistic ETA
    """
    logger.info("command_move", ship_id=command.ship_id, target=(command.target_x, command.target_y))
    raise HTTPException(status_code=501, detail="Not implemented (Phase B scaffold)")

@router.post("/fire")
async def fire_weapon(command: FireCommand):
    """
    Fire weapon at target.
    TODO: Validate player owns ship
    TODO: Check weapon cooldown, energy cost
    TODO: Queue command for next 6s combat tick
    TODO: Return optimistic "firing" status
    """
    logger.info("command_fire", ship_id=command.ship_id, weapon=command.weapon_type, target=command.target_id)
    raise HTTPException(status_code=501, detail="Not implemented (Phase B scaffold)")

@router.post("/claim")
async def claim_planet(command: ClaimCommand):
    """
    Claim unowned planet.
    TODO: Validate player owns ship
    TODO: Check ship is at planet location
    TODO: Check planet is unowned
    TODO: Assign planet to player
    TODO: Return planet data
    """
    logger.info("command_claim", ship_id=command.ship_id, planet_id=command.planet_id)
    raise HTTPException(status_code=501, detail="Not implemented (Phase B scaffold)")
