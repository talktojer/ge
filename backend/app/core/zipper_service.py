"""
Galactic Empire - Zipper Service

This module handles the zipper weapon system for mine triggering and teleportation
mechanisms including boundary teleportation and mine field disruption.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
import random
import math

from ..models.user import User
from ..models.ship import Ship
from ..models.mine import Mine
from ..core.coordinates import calculate_distance


class ZipperService:
    """Service for zipper operations"""
    
    def __init__(self):
        self.zipper_range = 5000  # Range for zipper mine triggering
        self.teleport_damage = 10  # TELEDAM from original code
        self.universe_max = 195000  # UNIVMAX from original code (30*65000)
        self.boundary_margin = 2000  # Safety margin from universe boundaries
    
    def fire_zipper(self, db: Session, user_id: int, ship_id: int) -> Dict[str, Any]:
        """
        Fire zipper weapon to trigger nearby mines
        """
        # Get user and ship
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        ship = db.query(Ship).filter(Ship.id == ship_id, Ship.owner_id == user_id).first()
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ship not found"
            )
        
        # Check if ship has zipper capability
        if not hasattr(ship, 'has_zipper') or not ship.has_zipper:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ship does not have zipper launching system"
            )
        
        # Find mines within zipper range
        mines = db.query(Mine).filter(
            Mine.is_active == True,
            Mine.is_armed == True
        ).all()
        
        triggered_mines = []
        for mine in mines:
            distance = calculate_distance(ship.x_coord, ship.y_coord, mine.x_coord, mine.y_coord)
            if distance <= self.zipper_range:
                triggered_mines.append(mine)
        
        # Trigger all mines in range
        mine_results = []
        for mine in triggered_mines:
            # Calculate damage to ship (original game: mines damage the ship that triggers them)
            damage = self._calculate_mine_damage(mine, ship)
            
            # Apply damage to ship
            shield_damage = min(damage, ship.shields)
            hull_damage = damage - shield_damage
            
            ship.shields = max(0, ship.shields - shield_damage)
            ship.hull = max(0, ship.hull - hull_damage)
            
            # Deactivate mine
            mine.is_active = False
            mine.is_armed = False
            mine.exploded_at = datetime.utcnow()
            
            mine_results.append({
                "mine_id": mine.id,
                "mine_type": mine.mine_type,
                "distance": distance,
                "damage_dealt": damage,
                "shield_damage": shield_damage,
                "hull_damage": hull_damage,
                "exploded": True
            })
        
        db.commit()
        
        return {
            "message": f"Zipper fired! Triggered {len(triggered_mines)} mines",
            "ship_name": ship.ship_name,
            "zipper_range": self.zipper_range,
            "mines_triggered": len(triggered_mines),
            "mine_results": mine_results,
            "ship_damage": {
                "total_damage": sum(result["damage_dealt"] for result in mine_results),
                "shields_remaining": ship.shields,
                "hull_remaining": ship.hull
            }
        }
    
    def check_boundary_teleport(self, db: Session, ship_id: int) -> Dict[str, Any]:
        """
        Check if ship is out of bounds and needs teleportation
        """
        ship = db.query(Ship).filter(Ship.id == ship_id).first()
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ship not found"
            )
        
        teleported = False
        teleport_reason = ""
        
        # Check X boundaries
        if ship.x_coord > self.universe_max:
            ship.x_coord = self.universe_max - self.boundary_margin
            teleported = True
            teleport_reason = "exceeded positive X boundary"
        elif ship.x_coord < -self.universe_max:
            ship.x_coord = -self.universe_max + self.boundary_margin
            teleported = True
            teleport_reason = "exceeded negative X boundary"
        
        # Check Y boundaries
        if ship.y_coord > self.universe_max:
            ship.y_coord = self.universe_max - self.boundary_margin
            teleported = True
            teleport_reason = "exceeded positive Y boundary"
        elif ship.y_coord < -self.universe_max:
            ship.y_coord = -self.universe_max + self.boundary_margin
            teleported = True
            teleport_reason = "exceeded negative Y boundary"
        
        if teleported:
            # Apply teleportation damage
            ship.hull = max(0, ship.hull - self.teleport_damage)
            
            # Stop ship movement
            ship.speed = 0.0
            ship.speed2b = 0.0
            
            # Clear any active weapons/torpedoes
            ship.locked_target = None
            ship.torpedoes_locked = 0
            ship.missiles_locked = 0
            
            db.commit()
            
            return {
                "teleported": True,
                "reason": teleport_reason,
                "new_position": {
                    "x_coord": ship.x_coord,
                    "y_coord": ship.y_coord
                },
                "damage_taken": self.teleport_damage,
                "hull_remaining": ship.hull,
                "ship_stopped": True
            }
        
        return {
            "teleported": False,
            "message": "Ship is within universe boundaries"
        }
    
    def emergency_teleport(self, db: Session, user_id: int, ship_id: int, 
                          target_x: float = None, target_y: float = None) -> Dict[str, Any]:
        """
        Emergency teleportation to a specific location or random location
        """
        # Get user and ship
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        ship = db.query(Ship).filter(Ship.id == ship_id, Ship.owner_id == user_id).first()
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ship not found"
            )
        
        # Check if ship has emergency teleport capability (expensive equipment)
        if not hasattr(ship, 'has_emergency_teleport') or not ship.has_emergency_teleport:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ship does not have emergency teleportation system"
            )
        
        # Generate target coordinates if not provided
        if target_x is None or target_y is None:
            # Random teleportation within safe boundaries
            safe_range = self.universe_max - self.boundary_margin
            target_x = random.uniform(-safe_range, safe_range)
            target_y = random.uniform(-safe_range, safe_range)
        
        # Validate target coordinates
        if (abs(target_x) > self.universe_max or abs(target_y) > self.universe_max):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target coordinates are outside universe boundaries"
            )
        
        old_position = {
            "x_coord": ship.x_coord,
            "y_coord": ship.y_coord
        }
        
        # Teleport ship
        ship.x_coord = target_x
        ship.y_coord = target_y
        
        # Apply teleportation damage (higher for emergency teleport)
        emergency_damage = self.teleport_damage * 2
        ship.hull = max(0, ship.hull - emergency_damage)
        
        # Stop ship movement
        ship.speed = 0.0
        ship.speed2b = 0.0
        
        # Clear any active weapons/torpedoes
        ship.locked_target = None
        ship.torpedoes_locked = 0
        ship.missiles_locked = 0
        
        db.commit()
        
        return {
            "message": "Emergency teleportation successful",
            "ship_name": ship.ship_name,
            "old_position": old_position,
            "new_position": {
                "x_coord": ship.x_coord,
                "y_coord": ship.y_coord
            },
            "damage_taken": emergency_damage,
            "hull_remaining": ship.hull,
            "ship_stopped": True,
            "teleport_type": "emergency"
        }
    
    def get_zipper_statistics(self, db: Session) -> Dict[str, Any]:
        """Get zipper system statistics"""
        # Count ships with zipper capability
        ships_with_zipper = db.query(Ship).filter(
            Ship.has_zipper == True,
            Ship.is_active == True
        ).count()
        
        # Count mines that could be affected by zipper
        active_mines = db.query(Mine).filter(
            Mine.is_active == True,
            Mine.is_armed == True
        ).count()
        
        # Count ships with emergency teleport
        ships_with_emergency_teleport = db.query(Ship).filter(
            Ship.has_emergency_teleport == True,
            Ship.is_active == True
        ).count()
        
        return {
            "zipper_range": self.zipper_range,
            "teleport_damage": self.teleport_damage,
            "universe_boundaries": {
                "max_x": self.universe_max,
                "max_y": self.universe_max,
                "min_x": -self.universe_max,
                "min_y": -self.universe_max
            },
            "ships_with_zipper": ships_with_zipper,
            "ships_with_emergency_teleport": ships_with_emergency_teleport,
            "active_mines_vulnerable": active_mines,
            "boundary_margin": self.boundary_margin
        }
    
    def _calculate_mine_damage(self, mine: Mine, ship: Ship) -> int:
        """Calculate damage dealt by a triggered mine"""
        base_damage = mine.damage_potential
        
        # Modify damage based on mine type
        type_damage_modifiers = {
            0: 1.0,    # Standard
            1: 1.2,    # Proximity - more damage
            2: 0.8,    # Magnetic - less damage
            3: 1.1,    # Thermal - slightly more
            4: 1.3,    # Gravimetric - much more damage
            5: 0.0,    # Decoy - no damage
            6: 1.5,    # Cluster - lots of damage
            7: 0.5,    # EMP - less damage but disables systems
            8: 1.0,    # Stealth - normal damage
            9: 0.7     # Anti-Fighter - less damage to capital ships
        }
        
        damage_modifier = type_damage_modifiers.get(mine.mine_type, 1.0)
        
        # Apply some randomness
        random_factor = random.uniform(0.8, 1.2)
        
        final_damage = int(base_damage * damage_modifier * random_factor)
        return max(1, final_damage)  # Minimum 1 damage


# Global zipper service instance
zipper_service = ZipperService()
