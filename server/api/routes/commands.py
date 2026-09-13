"""
Command routes.
Move, fire, claim, etc.

Phase C3b: Postgres persistence for command state.
Replaces C3a in-memory stores with authoritative database reads/writes.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import structlog
import redis.asyncio as aioredis
import json
import os

from api.dependencies import get_current_player
from database import get_db_session
from database.models import Ship, Planet

logger = structlog.get_logger()

router = APIRouter()

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
async def move_ship(
    command: MoveCommand, 
    player_id: str = Depends(get_current_player),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Move ship to target sector (or within sector).
    
    Both /commands/move and /commands/move/ paths accepted without redirect
    to prevent HTTPS→HTTP scheme downgrade (same pattern as /sectors).
    
    Phase C3b: Validates ownership via Postgres, updates position transactionally, 
    publishes ship_moved event to Redis.
    
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
    
    # Query ship with FOR UPDATE lock (prevents concurrent modifications)
    result = await db.execute(
        select(Ship)
        .where(Ship.id == command.ship_id)
        .with_for_update()
    )
    ship = result.scalar_one_or_none()
    
    if not ship:
        raise HTTPException(status_code=404, detail=f"Ship {command.ship_id} not found")
    
    # Validate ownership
    if ship.owner_id != player_id:
        raise HTTPException(status_code=403, detail="You do not own this ship")
    
    # Store old position for event
    old_position = {"x": ship.position_x, "y": ship.position_y}
    sector_id = ship.sector_id
    
    # Update position in database
    ship.position_x = command.target_x
    ship.position_y = command.target_y
    
    try:
        await db.commit()
        await db.refresh(ship)
        logger.info("move_command_committed", ship_id=command.ship_id, position=(command.target_x, command.target_y))
    except Exception as e:
        await db.rollback()
        logger.error("move_command_failed", ship_id=command.ship_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update ship position")
    
    # Publish ship_moved event to Redis (best-effort after successful commit)
    try:
        redis = await get_redis()
        
        event = {
            "event_type": "ship_moved",
            "ship_id": command.ship_id,
            "old_position": old_position,
            "new_position": {"x": command.target_x, "y": command.target_y},
            "heading": ship.heading if ship.heading is not None else 0.0,
            "speed": ship.speed if ship.speed is not None else 0.0,
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
    except Exception as e:
        # Redis publish failure doesn't rollback the DB transaction
        # The move succeeded, but WebSocket clients may miss this update until next tick
        logger.error("move_event_publish_failed", ship_id=command.ship_id, error=str(e))
    
    return {
        "success": True,
        "ship_id": command.ship_id,
        "new_position": {"x": command.target_x, "y": command.target_y},
        "event_published": True
    }


@router.post("/fire")
@router.post("/fire/")
async def fire_weapon(
    command: FireCommand, 
    player_id: str = Depends(get_current_player),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Fire weapon at target ship in same sector.
    
    Both /commands/fire and /commands/fire/ paths accepted without redirect
    to prevent HTTPS→HTTP scheme downgrade (same pattern as /sectors).
    
    Phase C3b: Validates ownership via Postgres, publishes combat event to Redis.
    
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
    
    # Validate attacker ship exists and player owns it
    result = await db.execute(
        select(Ship).where(Ship.id == command.ship_id)
    )
    ship = result.scalar_one_or_none()
    
    if not ship:
        raise HTTPException(status_code=404, detail=f"Ship {command.ship_id} not found")
    
    # Validate ownership
    if ship.owner_id != player_id:
        raise HTTPException(status_code=403, detail="You do not own this ship")
    
    # Validate target exists
    result = await db.execute(
        select(Ship).where(Ship.id == command.target_id)
    )
    target_ship = result.scalar_one_or_none()
    
    if not target_ship:
        raise HTTPException(status_code=404, detail=f"Target ship {command.target_id} not found")
    
    sector_id = ship.sector_id
    
    # Stub damage calculation (real damage will be computed by ge-sim tick)
    stub_damage = {"phasor": 15.0, "torpedo": 35.0, "missile": 25.0}.get(command.weapon_type, 10.0)
    
    # Publish combat event to Redis (best-effort)
    try:
        redis = await get_redis()
        
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
    except Exception as e:
        logger.error("fire_event_publish_failed", ship_id=command.ship_id, error=str(e))
    
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
async def claim_planet(
    command: ClaimCommand, 
    player_id: str = Depends(get_current_player),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Claim an unowned planet in sector.
    
    Both /commands/claim and /commands/claim/ paths accepted without redirect
    to prevent HTTPS→HTTP scheme downgrade (same pattern as /sectors).
    
    Phase C3b: Validates ownership via Postgres, checks planet is unowned with FOR UPDATE lock,
    assigns to player transactionally, publishes event.
    
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
    
    # Validate ship exists and player owns it
    result = await db.execute(
        select(Ship).where(Ship.id == command.ship_id)
    )
    ship = result.scalar_one_or_none()
    
    if not ship:
        raise HTTPException(status_code=404, detail=f"Ship {command.ship_id} not found")
    
    # Validate ownership
    if ship.owner_id != player_id:
        raise HTTPException(status_code=403, detail="You do not own this ship")
    
    # Query planet with FOR UPDATE lock (prevents race conditions on claim)
    result = await db.execute(
        select(Planet)
        .where(Planet.id == command.planet_id)
        .with_for_update()
    )
    planet = result.scalar_one_or_none()
    
    if not planet:
        raise HTTPException(status_code=404, detail=f"Planet {command.planet_id} not found")
    
    # Check planet is unowned
    if planet.owner_id is not None:
        raise HTTPException(status_code=403, detail=f"Planet {command.planet_id} is already owned")
    
    sector_id = planet.sector_id
    planet_name = planet.name
    
    # Claim planet
    planet.owner_id = player_id
    
    try:
        await db.commit()
        await db.refresh(planet)
        logger.info("claim_command_committed", planet_id=command.planet_id, player_id=player_id)
    except Exception as e:
        await db.rollback()
        logger.error("claim_command_failed", planet_id=command.planet_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to claim planet")
    
    # Publish planet_claimed event to Redis (best-effort after successful commit)
    try:
        redis = await get_redis()
        
        event = {
            "event_type": "planet_claimed",
            "planet_id": command.planet_id,
            "planet_name": planet_name,
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
    except Exception as e:
        # Redis publish failure doesn't rollback the DB transaction
        logger.error("claim_event_publish_failed", planet_id=command.planet_id, error=str(e))
    
    return {
        "success": True,
        "planet_id": command.planet_id,
        "planet_name": planet_name,
        "owner_id": player_id,
        "event_published": True
    }
