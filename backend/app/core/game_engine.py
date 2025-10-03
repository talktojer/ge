"""
Galactic Empire - Core Game Engine

This module implements the main game engine that coordinates all core systems
including the tick system, movement physics, coordinate system, and galaxy map.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .coordinates import Coordinate, get_sector, same_sector, distance, bearing
from .movement import MovementState, MovementPhysics, ShipMovement, create_movement_state
from .tick_system import TickSystem, TickType
from .galaxy import GalaxyMap, GalaxySector, PlanetObject

logger = logging.getLogger(__name__)


@dataclass
class Ship:
    """Ship entity in the game"""
    ship_id: str
    user_id: str
    ship_name: str
    ship_class: int
    position: Coordinate
    heading: float
    speed: float
    max_speed: float
    max_acceleration: float
    energy: int
    shields: int
    max_shields: int
    damage: float
    status: str  # 'active', 'inactive', 'destroyed'
    team_id: Optional[str] = None
    last_update: datetime = None
    
    def __post_init__(self):
        if self.last_update is None:
            self.last_update = datetime.utcnow()


@dataclass
class GameState:
    """Current state of the game"""
    ships: Dict[str, Ship]
    galaxy_map: GalaxyMap
    tick_system: TickSystem
    game_time: datetime
    running: bool = False
    tick_number: int = 0  # Global game tick counter


class GameEngine:
    """Main game engine coordinator"""
    
    def __init__(self):
        self.game_state: Optional[GameState] = None
        self.movement_physics = MovementPhysics()
        self.ship_movement = ShipMovement(self.movement_physics)
        self._initialized = False
    
    async def initialize(self):
        """Initialize the game engine"""
        if self._initialized:
            return
        
        logger.info("Initializing Galactic Empire game engine...")
        
        # Create galaxy map
        galaxy_map = GalaxyMap()
        
        # Create tick system with callback to increment global game tick
        tick_system = TickSystem(tick_callback=self.increment_tick)
        
        # Initialize game state
        self.game_state = GameState(
            ships={},
            galaxy_map=galaxy_map,
            tick_system=tick_system,
            game_time=datetime.utcnow()
        )
        
        # Restore ships from database
        await self.restore_ships_from_database()
        
        # Start tick system
        await tick_system.start()
        
        self._initialized = True
        logger.info("Game engine initialized successfully")
    
    async def restore_ships_from_database(self):
        """Restore ships from database to game engine"""
        try:
            from ..core.database import get_db
            from ..models.ship import Ship as DBShip
            from sqlalchemy.orm import Session
            
            # Get database session
            db = next(get_db())
            
            # Get all active ships from database (status = 1 means active)
            db_ships = db.query(DBShip).filter(DBShip.status == 1).all()
            
            restored_count = 0
            for db_ship in db_ships:
                try:
                    # Create ship in game engine
                    ship = Ship(
                        ship_id=str(db_ship.id),
                        user_id=str(db_ship.user_id),
                        ship_name=db_ship.shipname,
                        ship_class=db_ship.shpclass,
                        position=Coordinate(db_ship.x_coord, db_ship.y_coord),
                        heading=db_ship.heading,
                        speed=db_ship.speed,
                        max_speed=50000.0,  # Default max speed
                        max_acceleration=2000.0,  # Default acceleration
                        energy=db_ship.energy,
                        shields=db_ship.shields,
                        max_shields=db_ship.max_shields,
                        damage=db_ship.damage,
                        status='active' if db_ship.status == 1 else 'inactive'
                    )
                    
                    self.game_state.ships[str(db_ship.id)] = ship
                    restored_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to restore ship {db_ship.id}: {e}")
            
            logger.info(f"Restored {restored_count} ships from database")
            
        except Exception as e:
            logger.error(f"Failed to restore ships from database: {e}")
    
    async def start_game(self):
        """Start the game"""
        if not self._initialized:
            await self.initialize()
        
        if self.game_state.running:
            return
        
        logger.info("Starting Galactic Empire game...")
        self.game_state.running = True
        self.game_state.game_time = datetime.utcnow()
        
        logger.info("Galactic Empire game started")
    
    async def stop_game(self):
        """Stop the game"""
        if not self.game_state or not self.game_state.running:
            return
        
        logger.info("Stopping Galactic Empire game...")
        
        # Stop tick system
        await self.game_state.tick_system.stop()
        
        self.game_state.running = False
        logger.info("Galactic Empire game stopped")
    
    def create_ship(self, ship_id: str, user_id: str, ship_name: str, 
                   ship_class: int, position: Optional[Coordinate] = None) -> Ship:
        """Create a new ship"""
        if not self.game_state:
            raise RuntimeError("Game engine not initialized")
        
        # Default position to neutral sector if not provided
        if position is None:
            position = Coordinate(0.0, 0.0)
        
        # Create ship with default values
        ship = Ship(
            ship_id=ship_id,
            user_id=user_id,
            ship_name=ship_name,
            ship_class=ship_class,
            position=position,
            heading=0.0,
            speed=0.0,
            max_speed=50000.0,  # Default max speed
            max_acceleration=2000.0,  # Default acceleration
            energy=50000,  # Default energy
            shields=0,
            max_shields=100,  # Default max shields
            damage=0.0,
            status='active'
        )
        
        self.game_state.ships[ship_id] = ship
        logger.info(f"Created ship {ship_name} ({ship_id}) for user {user_id}")
        
        return ship
    
    def get_ship(self, ship_id: str) -> Optional[Ship]:
        """Get a ship by ID"""
        if not self.game_state:
            return None
        return self.game_state.ships.get(ship_id)
    
    def update_ship_movement(self, ship_id: str, target_speed: Optional[float] = None,
                           target_heading: Optional[float] = None) -> bool:
        """Update ship movement"""
        ship = self.get_ship(ship_id)
        if not ship or ship.status != 'active':
            return False
        
        # Create movement state
        movement_state = create_movement_state(
            position=ship.position,
            heading=ship.heading,
            speed=ship.speed,
            max_speed=ship.max_speed,
            max_acceleration=ship.max_acceleration
        )
        
        # Apply movement updates
        if target_speed is not None:
            movement_state = self.ship_movement.accelerate_ship(movement_state, target_speed)
        
        if target_heading is not None:
            movement_state = self.ship_movement.rotate_ship(movement_state, target_heading)
        
        # Update ship position
        movement_state = self.ship_movement.move_ship(movement_state)
        
        # Update ship with new state
        ship.position = movement_state.position
        ship.heading = movement_state.heading
        ship.speed = movement_state.speed
        ship.last_update = datetime.utcnow()
        
        return True
    
    def get_sector_info(self, coord: Coordinate) -> Dict[str, Any]:
        """Get information about a sector"""
        if not self.game_state:
            return {}
        
        return self.game_state.galaxy_map.get_sector_info(coord)
    
    def get_planets_in_sector(self, coord: Coordinate) -> List[PlanetObject]:
        """Get planets in a sector"""
        if not self.game_state:
            return []
        
        return self.game_state.galaxy_map.get_planets_in_sector(coord)
    
    def get_ships_in_sector(self, coord: Coordinate) -> List[Ship]:
        """Get all ships in a sector"""
        if not self.game_state:
            return []
        
        sector = get_sector(coord)
        ships_in_sector = []
        
        for ship in self.game_state.ships.values():
            if ship.status == 'active' and same_sector(ship.position, coord):
                ships_in_sector.append(ship)
        
        return ships_in_sector
    
    def get_ship_distance(self, ship1_id: str, ship2_id: str) -> Optional[float]:
        """Get distance between two ships"""
        ship1 = self.get_ship(ship1_id)
        ship2 = self.get_ship(ship2_id)
        
        if not ship1 or not ship2:
            return None
        
        return distance(ship1.position, ship2.position)
    
    def get_ship_bearing(self, ship1_id: str, ship2_id: str) -> Optional[float]:
        """Get bearing from one ship to another"""
        ship1 = self.get_ship(ship1_id)
        ship2 = self.get_ship(ship2_id)
        
        if not ship1 or not ship2:
            return None
        
        return bearing(ship1.position, ship2.position, ship1.heading)
    
    def set_beacon_message(self, coord: Coordinate, message: str):
        """Set a beacon message for a sector"""
        if not self.game_state:
            return
        
        self.game_state.galaxy_map.set_beacon_message(coord, message)
    
    def increment_tick(self):
        """Increment the global game tick counter"""
        if self.game_state:
            self.game_state.tick_number += 1
            self.game_state.game_time = datetime.utcnow()
            logger.debug(f"Game tick incremented to {self.game_state.tick_number}")
    
    def get_current_tick(self) -> int:
        """Get the current game tick number"""
        if not self.game_state:
            return 0
        return self.game_state.tick_number
    
    def get_beacon_message(self, coord: Coordinate) -> Optional[str]:
        """Get beacon message for a sector"""
        if not self.game_state:
            return None
        
        return self.game_state.galaxy_map.get_beacon_message(coord)
    
    def get_game_statistics(self) -> Dict[str, Any]:
        """Get game statistics"""
        if not self.game_state:
            # Return default values when game engine is not initialized
            return {
                'total_ships': 0,
                'active_ships': 0,
                'game_running': False,
                'game_time': datetime.utcnow().isoformat(),
                'galaxy': {},
                'tick_system': {}
            }
        
        active_ships = sum(1 for ship in self.game_state.ships.values() 
                          if ship.status == 'active')
        
        galaxy_stats = self.game_state.galaxy_map.get_galaxy_statistics()
        tick_stats = self.game_state.tick_system.get_stats()
        
        return {
            'total_ships': len(self.game_state.ships),
            'active_ships': active_ships,
            'game_running': self.game_state.running,
            'game_time': self.game_state.game_time.isoformat(),
            'tick_number': self.game_state.tick_number,
            'galaxy': galaxy_stats,
            'tick_system': tick_stats
        }
    
    def get_ship_status(self, ship_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed ship status"""
        ship = self.get_ship(ship_id)
        if not ship:
            return None
        
        sector_info = self.get_sector_info(ship.position)
        
        return {
            'ship_id': ship.ship_id,
            'user_id': ship.user_id,
            'ship_name': ship.ship_name,
            'ship_class': ship.ship_class,
            'position': {
                'x': ship.position.x,
                'y': ship.position.y
            },
            'heading': ship.heading,
            'speed': ship.speed,
            'max_speed': ship.max_speed,
            'energy': ship.energy,
            'shields': ship.shields,
            'max_shields': ship.max_shields,
            'damage': ship.damage,
            'status': ship.status,
            'team_id': ship.team_id,
            'last_update': ship.last_update.isoformat(),
            'sector': sector_info
        }
    
    async def cleanup(self):
        """Cleanup game engine resources"""
        if self.game_state and self.game_state.running:
            await self.stop_game()
        
        self._initialized = False
        logger.info("Game engine cleaned up")


# Global game engine instance
game_engine = GameEngine()
