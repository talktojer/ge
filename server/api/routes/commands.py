"""
Command routes.
Move, fire, claim, etc.

Phase C3a: Real command path that publishes events to Redis for WebSocket deltas.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Optional, Any
import structlog
import redis.asyncio as aioredis
import json
import os

from api.dependencies import get_current_player

logger = structlog.get_logger()

router = APIRouter()

# In-memory state stores (Phase C3a)
# TODO: Replace with Postgres queries when schema is fully migrated
# These stub stores demonstrate the command→event flow for Phase C3a
_ship_store: Dict[int, Dict[str, Any]] = {
    201: {"id": 201, "owner_id": "player_1", "sector_id": 1, "position_x": 5, "position_y": 5, "heading": 90.0, "speed": 5.0, "class_type": "frigate"},
    202: {"id": 202, "owner_id": "player_3", "sector_id": 1, "position_x": 5, "position_y": 5, "heading": 180.0, "speed": 3.0, "class_type": "scout"},
    203: {"id": 203, "owner_id": "player_1", "sector_id": 3, "position_x": 6, "position_y": 5, "heading": 0.0, "speed": 2.0, "class_type": "miner"},
}

_planet_store: Dict[int, Dict[str, Any]] = {
    101: {"id": 101, "name": "Terra Prime", "owner_id": "player_1", "sector_id": 1},
    102: {"id": 102, "name": "New Horizon", "owner_id": None, "sector_id": 1},
    103: {"id": 103, "name": "Mining Station 7", "owner_id": "player_2", "sector_id": 1},
}

# Redis connection for event publishing
_redis_client: Optional[aioredis.Redis] = None

async def get_redis():
    """Get or create Redis connection."""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = await aioredis.from_url(redis_url, decode_responses=True)
        logger.info("commands_redis_connected", redis_url=redis_url)
    return _redis_client


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
@router.post("/move/")
async def move_ship(command: MoveCommand, player_id: str = Depends(get_current_player)):
    """
    Move ship to target sector (or within sector).
    
    Both /commands/move and /commands/move/ paths accepted without redirect
    to prevent HTTPS→HTTP scheme downgrade (same pattern as /sectors).
    
    Phase C3a: Validates ownership, updates position, publishes ship_moved event to Redis.
    
    Returns:
        Ship movement confirmation with new position
    
    Errors:
        401: Unauthorized (invalid token)
        403: Forbidden (player does not own ship)
        404: Ship not found
    """
    logger.info("command_move", 
                ship_id=command.ship_id, 
                target=(command.target_x, command.target_y),
                player_id=player_id)
    
    # Validate ship exists
    ship = _ship_store.get(command.ship_id)
    if not ship:
        raise HTTPException(status_code=404, detail=f"Ship {command.ship_id} not found")
    
    # Validate ownership
    if ship["owner_id"] != player_id:
        raise HTTPException(status_code=403, detail="You do not own this ship")
    
    # Store old position for event
    old_position = {"x": ship["position_x"], "y": ship["position_y"]}
    
    # Update position (in-memory for Phase C3a)
    # TODO: Replace with Postgres UPDATE ships SET position_x=?, position_y=? WHERE id=?
    ship["position_x"] = command.target_x
    ship["position_y"] = command.target_y
    _ship_store[command.ship_id] = ship
    
    # Publish ship_moved event to Redis
    redis = await get_redis()
    sector_id = ship["sector_id"]
    
    event = {
        "event_type": "ship_moved",
        "ship_id": command.ship_id,
        "old_position": old_position,
        "new_position": {"x": command.target_x, "y": command.target_y},
        "heading": ship.get("heading", 0.0),
        "speed": ship.get("speed", 0.0),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Wrap in sector_delta format for WebSocket clients
    sector_delta = {
        "type": "sector_delta",
        "sector_id": sector_id,
        "events": [event]
    }
    
    channel = f"sector:{sector_id}:delta"
    await redis.publish(channel, json.dumps(sector_delta))
    
    logger.info("move_command_published", 
                ship_id=command.ship_id,
                sector_id=sector_id,
                channel=channel)
    
    return {
        "success": True,
        "ship_id": command.ship_id,
        "new_position": {"x": command.target_x, "y": command.target_y},
        "event_published": True
    }


@router.post("/fire")
@router.post("/fire/")
async def fire_weapon(command: FireCommand, player_id: str = Depends(get_current_player)):
    """
    Fire weapon at target ship in same sector.
    
    Both /commands/fire and /commands/fire/ paths accepted without redirect
    to prevent HTTPS→HTTP scheme downgrade (same pattern as /sectors).
    
    Phase C3a: Validates ownership, queues combat action, publishes combat event to Redis.
    
    Returns:
        Combat action confirmation
    
    Errors:
        401: Unauthorized (invalid token)
        403: Forbidden (player does not own ship)
        404: Ship or target not found
    """
    logger.info("command_fire", 
                ship_id=command.ship_id,
                weapon=command.weapon_type,
                target=command.target_id,
                player_id=player_id)
    
    # Validate attacker ship exists
    ship = _ship_store.get(command.ship_id)
    if not ship:
        raise HTTPException(status_code=404, detail=f"Ship {command.ship_id} not found")
    
    # Validate ownership
    if ship["owner_id"] != player_id:
        raise HTTPException(status_code=403, detail="You do not own this ship")
    
    # Validate target exists
    target_ship = _ship_store.get(command.target_id)
    if not target_ship:
        raise HTTPException(status_code=404, detail=f"Target ship {command.target_id} not found")
    
    # TODO: Validate same sector, weapon range, energy cost
    # TODO: Queue for next 6s tick via ge-sim combat resolver
    
    # Publish combat event to Redis (stub damage for Phase C3a)
    redis = await get_redis()
    sector_id = ship["sector_id"]
    
    # Stub damage calculation (real damage will be computed by ge-sim tick)
    stub_damage = {"phasor": 15.0, "torpedo": 35.0, "missile": 25.0}.get(command.weapon_type, 10.0)
    
    event = {
        "event_type": "combat",
        "attacker_id": command.ship_id,
        "target_id": command.target_id,
        "weapon_type": command.weapon_type,
        "damage": stub_damage,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Wrap in sector_delta format
    sector_delta = {
        "type": "sector_delta",
        "sector_id": sector_id,
        "events": [event]
    }
    
    channel = f"sector:{sector_id}:delta"
    await redis.publish(channel, json.dumps(sector_delta))
    
    logger.info("fire_command_published",
                ship_id=command.ship_id,
                target_id=command.target_id,
                weapon=command.weapon_type,
                damage=stub_damage,
                channel=channel)
    
    return {
        "success": True,
        "ship_id": command.ship_id,
        "target_id": command.target_id,
        "weapon_type": command.weapon_type,
        "damage": stub_damage,
        "event_published": True
    }


@router.post("/claim")
@router.post("/claim/")
async def claim_planet(command: ClaimCommand, player_id: str = Depends(get_current_player)):
    """
    Claim an unowned planet in sector.
    
    Both /commands/claim and /commands/claim/ paths accepted without redirect
    to prevent HTTPS→HTTP scheme downgrade (same pattern as /sectors).
    
    Phase C3a: Validates ownership, checks planet is unowned, assigns to player, publishes event.
    
    Returns:
        Planet claim confirmation
    
    Errors:
        401: Unauthorized (invalid token)
        403: Forbidden (player does not own ship, or planet already owned)
        404: Ship or planet not found
    """
    logger.info("command_claim",
                ship_id=command.ship_id,
                planet_id=command.planet_id,
                player_id=player_id)
    
    # Validate ship exists
    ship = _ship_store.get(command.ship_id)
    if not ship:
        raise HTTPException(status_code=404, detail=f"Ship {command.ship_id} not found")
    
    # Validate ownership
    if ship["owner_id"] != player_id:
        raise HTTPException(status_code=403, detail="You do not own this ship")
    
    # Validate planet exists
    planet = _planet_store.get(command.planet_id)
    if not planet:
        raise HTTPException(status_code=404, detail=f"Planet {command.planet_id} not found")
    
    # Check planet is unowned
    if planet["owner_id"] is not None:
        raise HTTPException(status_code=403, detail=f"Planet {command.planet_id} is already owned")
    
    # TODO: Validate ship is in same sector as planet
    # TODO: Replace with Postgres UPDATE planets SET owner_id=? WHERE id=?
    
    # Claim planet (in-memory for Phase C3a)
    planet["owner_id"] = player_id
    _planet_store[command.planet_id] = planet
    
    # Publish planet_claimed event to Redis
    redis = await get_redis()
    sector_id = planet["sector_id"]
    
    event = {
        "event_type": "planet_claimed",
        "planet_id": command.planet_id,
        "planet_name": planet["name"],
        "owner_id": player_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Wrap in sector_delta format
    sector_delta = {
        "type": "sector_delta",
        "sector_id": sector_id,
        "events": [event]
    }
    
    channel = f"sector:{sector_id}:delta"
    await redis.publish(channel, json.dumps(sector_delta))
    
    logger.info("claim_command_published",
                planet_id=command.planet_id,
                player_id=player_id,
                channel=channel)
    
    return {
        "success": True,
        "planet_id": command.planet_id,
        "planet_name": planet["name"],
        "owner_id": player_id,
        "event_published": True
    }
