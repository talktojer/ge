"""
Game engine integration tasks

Tasks that integrate with the main game engine for real-time updates
and WebSocket communication.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from app.core.celery import celery_app
from app.core.database import get_db
from app.core.game_engine import GameEngine
from app.models.ship import Ship
from app.models.planet import Planet

logger = logging.getLogger(__name__)


@celery_app.task
def broadcast_game_state():
    """Broadcast current game state to all connected WebSocket clients"""
    try:
        # Get game engine instance
        game_engine = GameEngine()
        
        # Get current game state
        game_state = {
            "timestamp": datetime.utcnow().isoformat(),
            "ships": game_engine.get_all_ships_info(),
            "planets": game_engine.get_all_planets_info(),
            "statistics": game_engine.get_game_statistics()
        }
        
        # Broadcast via WebSocket (would need Socket.IO integration)
        # socketio.emit('game_state_update', game_state, broadcast=True)
        
        logger.debug("Game state broadcasted to WebSocket clients")
        
    except Exception as e:
        logger.error(f"Error broadcasting game state: {e}")


@celery_app.task
def update_websocket_clients():
    """Update WebSocket clients with real-time game data"""
    try:
        # This would integrate with Socket.IO to push updates
        # to connected clients about ship movements, combat, etc.
        
        # For now, just log the update
        logger.debug("WebSocket clients updated")
        
    except Exception as e:
        logger.error(f"Error updating WebSocket clients: {e}")


@celery_app.task
def process_real_time_events():
    """Process real-time events that need immediate client updates"""
    try:
        db = next(get_db())
        
        # Get recent events that need broadcasting
        recent_ships = db.query(Ship).filter(
            Ship.updated_at > datetime.utcnow() - timedelta(seconds=5)
        ).all()
        
        recent_planets = db.query(Planet).filter(
            Planet.updated_at > datetime.utcnow() - timedelta(seconds=5)
        ).all()
        
        # Process real-time events
        events = []
        
        for ship in recent_ships:
            events.append({
                "type": "ship_update",
                "ship_id": ship.id,
                "data": {
                    "position": {"x": ship.x_coord, "y": ship.y_coord},
                    "heading": ship.heading,
                    "speed": ship.speed,
                    "damage": ship.damage,
                    "energy": ship.energy,
                    "shield_charge": ship.shield_charge
                }
            })
        
        for planet in recent_planets:
            events.append({
                "type": "planet_update", 
                "planet_id": planet.id,
                "data": {
                    "owner": planet.userid,
                    "cash": planet.cash,
                    "population": planet.team_code,
                    "beacon_message": planet.beacon_message
                }
            })
        
        # Broadcast events to WebSocket clients
        if events:
            # socketio.emit('real_time_events', events, broadcast=True)
            logger.debug(f"Broadcasted {len(events)} real-time events")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error processing real-time events: {e}")


@celery_app.task
def sync_game_engine_state():
    """Synchronize game engine state with database"""
    try:
        game_engine = GameEngine()
        
        # Refresh game engine state from database
        game_engine.refresh_state()
        
        logger.debug("Game engine state synchronized with database")
        
    except Exception as e:
        logger.error(f"Error synchronizing game engine state: {e}")


@celery_app.task
def cleanup_game_engine_cache():
    """Clean up game engine cache and temporary data"""
    try:
        game_engine = GameEngine()
        
        # Clear any cached data
        game_engine.clear_cache()
        
        logger.debug("Game engine cache cleaned up")
        
    except Exception as e:
        logger.error(f"Error cleaning up game engine cache: {e}")