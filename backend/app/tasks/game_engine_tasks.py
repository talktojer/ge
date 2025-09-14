"""
Galactic Empire - Game Engine Celery Tasks

This module implements Celery tasks for the game engine processing,
providing asynchronous processing of game events and real-time updates.
"""

from celery import current_task
from celery.exceptions import Retry
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..core.game_engine import game_engine
from ..core.tick_system import TickType
from . import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='game_engine.process_ship_tick')
def process_ship_tick(self, ship_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process ship tick - equivalent to warrtia() in original code
    Handles shields, cloaking, repairs, flux systems, etc.
    """
    try:
        logger.debug(f"Processing ship tick for {len(ship_data)} ships")
        
        # Ensure game engine is initialized
        if not game_engine._initialized:
            game_engine.initialize()
        
        results = []
        
        for ship_info in ship_data:
            ship_id = ship_info.get('ship_id')
            if not ship_id:
                continue
            
            # Get ship from game engine
            ship = game_engine.get_ship(ship_id)
            if not ship or ship.status != 'active':
                continue
            
            # Process ship systems
            ship_result = _process_ship_systems(ship, ship_info)
            results.append(ship_result)
        
        return {
            'processed_ships': len(results),
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error in ship tick processing: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(bind=True, name='game_engine.process_movement_tick')
def process_movement_tick(self, ship_data: List[Dict[str, Any]], 
                         clicker: int = 0) -> Dict[str, Any]:
    """
    Process movement tick - equivalent to warrti2a() in original code
    Handles ship movement, rotation, acceleration, self-destruct
    """
    try:
        logger.debug(f"Processing movement tick for {len(ship_data)} ships")
        
        if not game_engine._initialized:
            game_engine.initialize()
        
        results = []
        batch_size = 3  # Process ships in batches of 3
        
        # Process ships in batches (original used clicker % 3)
        for i in range(clicker, len(ship_data), batch_size):
            ship_info = ship_data[i]
            ship_id = ship_info.get('ship_id')
            
            if not ship_id:
                continue
            
            ship = game_engine.get_ship(ship_id)
            if not ship or ship.status != 'active':
                continue
            
            # Process ship movement
            movement_result = _process_ship_movement(ship, ship_info)
            results.append(movement_result)
        
        # Update clicker for next tick
        next_clicker = (clicker + 1) % batch_size
        
        return {
            'processed_ships': len(results),
            'next_clicker': next_clicker,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error in movement tick processing: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(bind=True, name='game_engine.process_planet_tick')
def process_planet_tick(self, planet_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process planet tick - equivalent to plarti() in original code
    Handles planet resource generation, population growth, etc.
    """
    try:
        logger.debug(f"Processing planet tick for {len(planet_data)} planets")
        
        if not game_engine._initialized:
            game_engine.initialize()
        
        results = []
        
        for planet_info in planet_data:
            planet_id = planet_info.get('planet_id')
            if not planet_id:
                continue
            
            # Process planet systems
            planet_result = _process_planet_systems(planet_info)
            results.append(planet_result)
        
        return {
            'processed_planets': len(results),
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error in planet tick processing: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(bind=True, name='game_engine.process_cybertron_tick')
def process_cybertron_tick(self, cybertron_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process Cybertron AI tick - equivalent to autortia() in original code
    Handles AI decision making, attack patterns, etc.
    """
    try:
        logger.debug(f"Processing Cybertron tick for {len(cybertron_data)} ships")
        
        if not game_engine._initialized:
            game_engine.initialize()
        
        results = []
        
        for ship_info in cybertron_data:
            ship_id = ship_info.get('ship_id')
            if not ship_id:
                continue
            
            ship = game_engine.get_ship(ship_id)
            if not ship or ship.status != 'active':
                continue
            
            # Process Cybertron AI
            ai_result = _process_cybertron_ai(ship, ship_info)
            results.append(ai_result)
        
        return {
            'processed_cybertron': len(results),
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error in Cybertron tick processing: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(name='game_engine.update_ship_movement')
def update_ship_movement(ship_id: str, target_speed: Optional[float] = None,
                        target_heading: Optional[float] = None) -> Dict[str, Any]:
    """
    Update ship movement asynchronously
    """
    try:
        if not game_engine._initialized:
            game_engine.initialize()
        
        success = game_engine.update_ship_movement(ship_id, target_speed, target_heading)
        
        return {
            'success': success,
            'ship_id': ship_id,
            'target_speed': target_speed,
            'target_heading': target_heading,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error updating ship movement: {exc}")
        return {
            'success': False,
            'error': str(exc),
            'ship_id': ship_id,
            'timestamp': datetime.utcnow().isoformat()
        }


@celery_app.task(name='game_engine.get_ship_status')
def get_ship_status(ship_id: str) -> Dict[str, Any]:
    """
    Get ship status asynchronously
    """
    try:
        if not game_engine._initialized:
            game_engine.initialize()
        
        status = game_engine.get_ship_status(ship_id)
        
        return {
            'success': status is not None,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error getting ship status: {exc}")
        return {
            'success': False,
            'error': str(exc),
            'ship_id': ship_id,
            'timestamp': datetime.utcnow().isoformat()
        }


@celery_app.task(name='game_engine.get_sector_info')
def get_sector_info(x: float, y: float) -> Dict[str, Any]:
    """
    Get sector information asynchronously
    """
    try:
        if not game_engine._initialized:
            game_engine.initialize()
        
        from ..core.coordinates import Coordinate
        coord = Coordinate(x, y)
        sector_info = game_engine.get_sector_info(coord)
        
        return {
            'success': True,
            'sector_info': sector_info,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error getting sector info: {exc}")
        return {
            'success': False,
            'error': str(exc),
            'x': x,
            'y': y,
            'timestamp': datetime.utcnow().isoformat()
        }


def _process_ship_systems(ship, ship_info: Dict[str, Any]) -> Dict[str, Any]:
    """Process individual ship systems"""
    # This would implement the actual ship system processing
    # For now, return basic status
    
    return {
        'ship_id': ship.ship_id,
        'processed': True,
        'energy': ship.energy,
        'shields': ship.shields,
        'damage': ship.damage,
        'timestamp': datetime.utcnow().isoformat()
    }


def _process_ship_movement(ship, ship_info: Dict[str, Any]) -> Dict[str, Any]:
    """Process individual ship movement"""
    # This would implement the actual movement processing
    # For now, return basic movement status
    
    return {
        'ship_id': ship.ship_id,
        'movement_processed': True,
        'position': {'x': ship.position.x, 'y': ship.position.y},
        'heading': ship.heading,
        'speed': ship.speed,
        'timestamp': datetime.utcnow().isoformat()
    }


def _process_planet_systems(planet_info: Dict[str, Any]) -> Dict[str, Any]:
    """Process individual planet systems"""
    # This would implement the actual planet processing
    # For now, return basic status
    
    return {
        'planet_id': planet_info.get('planet_id'),
        'processed': True,
        'timestamp': datetime.utcnow().isoformat()
    }


def _process_cybertron_ai(ship, ship_info: Dict[str, Any]) -> Dict[str, Any]:
    """Process Cybertron AI decision making"""
    # This would implement the actual AI processing
    # For now, return basic AI status
    
    return {
        'ship_id': ship.ship_id,
        'ai_processed': True,
        'timestamp': datetime.utcnow().isoformat()
    }
