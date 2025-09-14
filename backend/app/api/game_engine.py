"""
Galactic Empire - Game Engine API

This module provides REST API endpoints for interacting with the game engine.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging

from ..core.game_engine import game_engine
from ..core.coordinates import Coordinate
from ..tasks.game_engine_tasks import (
    process_ship_tick, process_movement_tick, process_planet_tick,
    process_cybertron_tick, update_ship_movement, get_ship_status,
    get_sector_info
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/game-engine", tags=["game-engine"])


# Pydantic models for API requests/responses
class CoordinateModel(BaseModel):
    x: float
    y: float


class ShipCreateRequest(BaseModel):
    ship_id: str
    user_id: str
    ship_name: str
    ship_class: int
    position: Optional[CoordinateModel] = None


class ShipMovementRequest(BaseModel):
    target_speed: Optional[float] = None
    target_heading: Optional[float] = None


class BeaconMessageRequest(BaseModel):
    message: str


class ShipResponse(BaseModel):
    ship_id: str
    user_id: str
    ship_name: str
    ship_class: int
    position: CoordinateModel
    heading: float
    speed: float
    max_speed: float
    energy: int
    shields: int
    max_shields: int
    damage: float
    status: str
    team_id: Optional[str] = None
    last_update: str


class SectorInfoResponse(BaseModel):
    sector_x: int
    sector_y: int
    sector_type: str
    num_planets: int
    planets: List[Dict[str, Any]]
    beacon_message: Optional[str] = None
    owner: Optional[str] = None


class GameStatsResponse(BaseModel):
    total_ships: int
    active_ships: int
    game_running: bool
    game_time: str
    galaxy: Dict[str, Any]
    tick_system: Dict[str, Any]


@router.post("/initialize")
async def initialize_game_engine():
    """Initialize the game engine"""
    try:
        await game_engine.initialize()
        return {"message": "Game engine initialized successfully"}
    except Exception as e:
        logger.error(f"Error initializing game engine: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_game():
    """Start the game"""
    try:
        await game_engine.start_game()
        return {"message": "Game started successfully"}
    except Exception as e:
        logger.error(f"Error starting game: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_game():
    """Stop the game"""
    try:
        await game_engine.stop_game()
        return {"message": "Game stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping game: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_game_status():
    """Get game status and statistics"""
    try:
        stats = game_engine.get_game_statistics()
        return GameStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting game status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ships", response_model=ShipResponse)
async def create_ship(ship_data: ShipCreateRequest):
    """Create a new ship"""
    try:
        position = None
        if ship_data.position:
            position = Coordinate(ship_data.position.x, ship_data.position.y)
        
        ship = game_engine.create_ship(
            ship_id=ship_data.ship_id,
            user_id=ship_data.user_id,
            ship_name=ship_data.ship_name,
            ship_class=ship_data.ship_class,
            position=position
        )
        
        return ShipResponse(
            ship_id=ship.ship_id,
            user_id=ship.user_id,
            ship_name=ship.ship_name,
            ship_class=ship.ship_class,
            position=CoordinateModel(x=ship.position.x, y=ship.position.y),
            heading=ship.heading,
            speed=ship.speed,
            max_speed=ship.max_speed,
            energy=ship.energy,
            shields=ship.shields,
            max_shields=ship.max_shields,
            damage=ship.damage,
            status=ship.status,
            team_id=ship.team_id,
            last_update=ship.last_update.isoformat()
        )
    except Exception as e:
        logger.error(f"Error creating ship: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ships/{ship_id}", response_model=Dict[str, Any])
async def get_ship(ship_id: str):
    """Get ship status"""
    try:
        status = game_engine.get_ship_status(ship_id)
        if not status:
            raise HTTPException(status_code=404, detail="Ship not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ship: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/ships/{ship_id}/movement")
async def update_ship_movement(ship_id: str, movement_data: ShipMovementRequest):
    """Update ship movement"""
    try:
        success = game_engine.update_ship_movement(
            ship_id=ship_id,
            target_speed=movement_data.target_speed,
            target_heading=movement_data.target_heading
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Ship not found or inactive")
        
        return {"message": "Ship movement updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ship movement: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors/{x}/{y}", response_model=SectorInfoResponse)
async def get_sector(x: float, y: float):
    """Get sector information"""
    try:
        coord = Coordinate(x, y)
        sector_info = game_engine.get_sector_info(coord)
        
        return SectorInfoResponse(**sector_info)
    except Exception as e:
        logger.error(f"Error getting sector info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors/{x}/{y}/ships")
async def get_ships_in_sector(x: float, y: float):
    """Get all ships in a sector"""
    try:
        coord = Coordinate(x, y)
        ships = game_engine.get_ships_in_sector(coord)
        
        return {
            "sector": {"x": x, "y": y},
            "ships": [
                {
                    "ship_id": ship.ship_id,
                    "ship_name": ship.ship_name,
                    "user_id": ship.user_id,
                    "position": {"x": ship.position.x, "y": ship.position.y},
                    "heading": ship.heading,
                    "speed": ship.speed,
                    "status": ship.status
                }
                for ship in ships
            ]
        }
    except Exception as e:
        logger.error(f"Error getting ships in sector: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ships/{ship_id}/distance/{other_ship_id}")
async def get_ship_distance(ship_id: str, other_ship_id: str):
    """Get distance between two ships"""
    try:
        distance = game_engine.get_ship_distance(ship_id, other_ship_id)
        if distance is None:
            raise HTTPException(status_code=404, detail="One or both ships not found")
        
        return {
            "ship1_id": ship_id,
            "ship2_id": other_ship_id,
            "distance": distance
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ship distance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ships/{ship_id}/bearing/{other_ship_id}")
async def get_ship_bearing(ship_id: str, other_ship_id: str):
    """Get bearing from one ship to another"""
    try:
        bearing = game_engine.get_ship_bearing(ship_id, other_ship_id)
        if bearing is None:
            raise HTTPException(status_code=404, detail="One or both ships not found")
        
        return {
            "from_ship_id": ship_id,
            "to_ship_id": other_ship_id,
            "bearing": bearing
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ship bearing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sectors/{x}/{y}/beacon")
async def set_beacon_message(x: float, y: float, beacon_data: BeaconMessageRequest):
    """Set beacon message for a sector"""
    try:
        coord = Coordinate(x, y)
        game_engine.set_beacon_message(coord, beacon_data.message)
        
        return {"message": "Beacon message set successfully"}
    except Exception as e:
        logger.error(f"Error setting beacon message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors/{x}/{y}/beacon")
async def get_beacon_message(x: float, y: float):
    """Get beacon message for a sector"""
    try:
        coord = Coordinate(x, y)
        message = game_engine.get_beacon_message(coord)
        
        return {
            "sector": {"x": x, "y": y},
            "beacon_message": message
        }
    except Exception as e:
        logger.error(f"Error getting beacon message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tick/ship")
async def trigger_ship_tick(background_tasks: BackgroundTasks, ship_data: List[Dict[str, Any]]):
    """Trigger ship tick processing"""
    try:
        # Queue the task for background processing
        task = process_ship_tick.delay(ship_data)
        
        return {
            "message": "Ship tick processing queued",
            "task_id": task.id
        }
    except Exception as e:
        logger.error(f"Error triggering ship tick: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tick/movement")
async def trigger_movement_tick(background_tasks: BackgroundTasks, 
                               ship_data: List[Dict[str, Any]], 
                               clicker: int = 0):
    """Trigger movement tick processing"""
    try:
        # Queue the task for background processing
        task = process_movement_tick.delay(ship_data, clicker)
        
        return {
            "message": "Movement tick processing queued",
            "task_id": task.id
        }
    except Exception as e:
        logger.error(f"Error triggering movement tick: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tick/planet")
async def trigger_planet_tick(background_tasks: BackgroundTasks, planet_data: List[Dict[str, Any]]):
    """Trigger planet tick processing"""
    try:
        # Queue the task for background processing
        task = process_planet_tick.delay(planet_data)
        
        return {
            "message": "Planet tick processing queued",
            "task_id": task.id
        }
    except Exception as e:
        logger.error(f"Error triggering planet tick: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tick/cybertron")
async def trigger_cybertron_tick(background_tasks: BackgroundTasks, 
                                cybertron_data: List[Dict[str, Any]]):
    """Trigger Cybertron tick processing"""
    try:
        # Queue the task for background processing
        task = process_cybertron_tick.delay(cybertron_data)
        
        return {
            "message": "Cybertron tick processing queued",
            "task_id": task.id
        }
    except Exception as e:
        logger.error(f"Error triggering Cybertron tick: {e}")
        raise HTTPException(status_code=500, detail=str(e))
