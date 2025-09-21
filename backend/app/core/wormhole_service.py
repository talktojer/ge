"""
Galactic Empire - Wormhole Service

This module handles wormhole navigation and management operations including
wormhole discovery, navigation, and system damage calculations.
"""

from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
import random
import math

from ..models.wormhole import Wormhole, WormholeTable, WormholeConstants
from ..models.user import User
from ..models.ship import Ship
from ..core.coordinates import calculate_distance, calculate_bearing


class WormholeService:
    """Service for wormhole operations"""
    
    def __init__(self):
        self.wormhole_odds = WormholeConstants.WORM_ODDS  # 6% chance of wormhole generation
        self.max_wormholes = WormholeConstants.MAX_WORMHOLES
        self.wormhole_damage_chance = 0.3  # 30% chance of system damage
        self.wormhole_damage_range = (5, 25)  # 5-25% damage range
        self.approach_speed_limit = 0.25  # 1/4 impulse speed limit for approach
        self.wormhole_radius = 1000  # Radius for wormhole detection
    
    def generate_wormhole(self, db: Session, x_sect: int, y_sect: int) -> Optional[Dict[str, Any]]:
        """
        Generate a wormhole in a sector based on odds
        Returns wormhole data if generated, None otherwise
        """
        # Check if wormhole should be generated (6% chance)
        if random.randint(1, 100) > self.wormhole_odds:
            return None
        
        # Check if we've reached max wormholes
        existing_count = db.query(Wormhole).filter(Wormhole.is_active == True).count()
        if existing_count >= self.max_wormholes:
            return None
        
        # Generate random coordinates within the sector
        sector_size = 10000  # Standard sector size
        x_coord = x_sect * sector_size + random.randint(1000, sector_size - 1000)
        y_coord = y_sect * sector_size + random.randint(1000, sector_size - 1000)
        
        # Generate destination coordinates (different sector)
        dest_x_sect = random.randint(0, 29)  # Galaxy is 30x15
        dest_y_sect = random.randint(0, 14)
        
        # Make sure destination is different from origin
        while dest_x_sect == x_sect and dest_y_sect == y_sect:
            dest_x_sect = random.randint(0, 29)
            dest_y_sect = random.randint(0, 14)
        
        dest_x_coord = dest_x_sect * sector_size + random.randint(1000, sector_size - 1000)
        dest_y_coord = dest_y_sect * sector_size + random.randint(1000, sector_size - 1000)
        
        # Create wormhole
        wormhole = Wormhole(
            xsect=x_sect,
            ysect=y_sect,
            plnum=0,  # Not planet-based
            type=WormholeConstants.PLTYPE_WORM,
            x_coord=x_coord,
            y_coord=y_coord,
            dest_x_coord=dest_x_coord,
            dest_y_coord=dest_y_coord,
            visible=True,
            name=f"Wormhole-{random.randint(1000, 9999)}",
            is_active=True,
            is_stable=True,
            energy_required=random.randint(50, 200)
        )
        
        db.add(wormhole)
        db.commit()
        db.refresh(wormhole)
        
        return {
            "id": wormhole.id,
            "name": wormhole.name,
            "x_coord": wormhole.x_coord,
            "y_coord": wormhole.y_coord,
            "dest_x_coord": wormhole.dest_x_coord,
            "dest_y_coord": wormhole.dest_y_coord,
            "energy_required": wormhole.energy_required,
            "visible": wormhole.visible
        }
    
    def find_wormholes_in_sector(self, db: Session, x_sect: int, y_sect: int) -> List[Dict[str, Any]]:
        """Find all wormholes in a specific sector"""
        wormholes = db.query(Wormhole).filter(
            Wormhole.xsect == x_sect,
            Wormhole.ysect == y_sect,
            Wormhole.is_active == True
        ).all()
        
        return [
            {
                "id": wormhole.id,
                "name": wormhole.name,
                "x_coord": wormhole.x_coord,
                "y_coord": wormhole.y_coord,
                "dest_x_coord": wormhole.dest_x_coord,
                "dest_y_coord": wormhole.dest_y_coord,
                "energy_required": wormhole.energy_required,
                "visible": wormhole.visible,
                "is_stable": wormhole.is_stable,
                "usage_count": wormhole.usage_count,
                "last_used": wormhole.last_used.isoformat() if wormhole.last_used else None
            }
            for wormhole in wormholes
        ]
    
    def find_wormholes_near_position(self, db: Session, x_coord: float, y_coord: float, radius: float = None) -> List[Dict[str, Any]]:
        """Find wormholes near a specific position"""
        if radius is None:
            radius = self.wormhole_radius
        
        # Find all active wormholes
        wormholes = db.query(Wormhole).filter(Wormhole.is_active == True).all()
        
        nearby_wormholes = []
        for wormhole in wormholes:
            distance = calculate_distance(x_coord, y_coord, wormhole.x_coord, wormhole.y_coord)
            if distance <= radius:
                nearby_wormholes.append({
                    "id": wormhole.id,
                    "name": wormhole.name,
                    "x_coord": wormhole.x_coord,
                    "y_coord": wormhole.y_coord,
                    "dest_x_coord": wormhole.dest_x_coord,
                    "dest_y_coord": wormhole.dest_y_coord,
                    "energy_required": wormhole.energy_required,
                    "visible": wormhole.visible,
                    "is_stable": wormhole.is_stable,
                    "distance": distance,
                    "bearing": calculate_bearing(x_coord, y_coord, wormhole.x_coord, wormhole.y_coord),
                    "usage_count": wormhole.usage_count
                })
        
        # Sort by distance
        nearby_wormholes.sort(key=lambda x: x["distance"])
        
        return nearby_wormholes
    
    def attempt_wormhole_transit(self, db: Session, user_id: int, ship_id: int, wormhole_id: int, approach_speed: float) -> Dict[str, Any]:
        """
        Attempt to transit through a wormhole
        Returns transit result with damage information
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
        
        # Get wormhole
        wormhole = db.query(Wormhole).filter(Wormhole.id == wormhole_id).first()
        if not wormhole or not wormhole.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wormhole not found or inactive"
            )
        
        # Check if ship has enough energy
        if ship.energy < wormhole.energy_required:
            return {
                "success": False,
                "message": f"Insufficient energy. Requires {wormhole.energy_required} energy units.",
                "energy_required": wormhole.energy_required,
                "current_energy": ship.energy
            }
        
        # Check approach speed (must be around 1/4 impulse)
        if abs(approach_speed - 0.25) > 0.1:  # Allow some tolerance
            return {
                "success": False,
                "message": "Approach speed too fast or too slow. Must approach at approximately 1/4 impulse speed.",
                "recommended_speed": 0.25,
                "current_speed": approach_speed
            }
        
        # Calculate system damage
        damage_percentage = 0
        damage_message = ""
        
        if random.random() < self.wormhole_damage_chance:
            damage_percentage = random.randint(*self.wormhole_damage_range)
            
            # Apply damage to ship systems
            shield_damage = int(ship.max_shields * damage_percentage / 100)
            phaser_damage = int(ship.max_phasers * damage_percentage / 100)
            torpedo_damage = int(ship.max_torpedoes * damage_percentage / 100)
            
            ship.shields = max(0, ship.shields - shield_damage)
            ship.phasers = max(0, ship.phasers - phaser_damage)
            ship.torpedoes = max(0, ship.torpedoes - torpedo_damage)
            
            damage_message = f"Wormhole transit caused {damage_percentage}% system damage. Shields: -{shield_damage}, Phasers: -{phaser_damage}, Torpedoes: -{torpedo_damage}"
        
        # Consume energy
        ship.energy -= wormhole.energy_required
        
        # Update ship position
        ship.x_coord = wormhole.dest_x_coord
        ship.y_coord = wormhole.dest_y_coord
        
        # Update wormhole statistics
        wormhole.usage_count += 1
        wormhole.last_used = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully transited through {wormhole.name}",
            "new_position": {
                "x_coord": wormhole.dest_x_coord,
                "y_coord": wormhole.dest_y_coord
            },
            "energy_consumed": wormhole.energy_required,
            "damage_percentage": damage_percentage,
            "damage_message": damage_message,
            "wormhole_name": wormhole.name,
            "usage_count": wormhole.usage_count
        }
    
    def get_wormhole_map(self, db: Session) -> Dict[str, Any]:
        """Get a map of all wormholes in the galaxy"""
        wormholes = db.query(Wormhole).filter(Wormhole.is_active == True).all()
        
        wormhole_map = {}
        for wormhole in wormholes:
            origin_sector = f"{wormhole.xsect},{wormhole.ysect}"
            dest_sector = f"{int(wormhole.dest_x_coord // 10000)},{int(wormhole.dest_y_coord // 10000)}"
            
            if origin_sector not in wormhole_map:
                wormhole_map[origin_sector] = []
            
            wormhole_map[origin_sector].append({
                "id": wormhole.id,
                "name": wormhole.name,
                "dest_sector": dest_sector,
                "dest_coords": {
                    "x_coord": wormhole.dest_x_coord,
                    "y_coord": wormhole.dest_y_coord
                },
                "energy_required": wormhole.energy_required,
                "visible": wormhole.visible,
                "is_stable": wormhole.is_stable,
                "usage_count": wormhole.usage_count,
                "last_used": wormhole.last_used.isoformat() if wormhole.last_used else None
            })
        
        return {
            "wormhole_count": len(wormholes),
            "active_wormholes": wormhole_map,
            "total_usage": sum(w.usage_count for w in wormholes)
        }
    
    def create_wormhole_table_entry(self, db: Session, x_coord: float, y_coord: float, dest_x_coord: float, dest_y_coord: float) -> Dict[str, Any]:
        """Create a wormhole table entry for navigation purposes"""
        wormhole_entry = WormholeTable(
            x_coord=x_coord,
            y_coord=y_coord,
            dest_x_coord=dest_x_coord,
            dest_y_coord=dest_y_coord,
            is_active=True
        )
        
        db.add(wormhole_entry)
        db.commit()
        db.refresh(wormhole_entry)
        
        return {
            "id": wormhole_entry.id,
            "x_coord": wormhole_entry.x_coord,
            "y_coord": wormhole_entry.y_coord,
            "dest_x_coord": wormhole_entry.dest_x_coord,
            "dest_y_coord": wormhole_entry.dest_y_coord,
            "is_active": wormhole_entry.is_active
        }
    
    def get_wormhole_statistics(self, db: Session) -> Dict[str, Any]:
        """Get wormhole system statistics"""
        total_wormholes = db.query(Wormhole).filter(Wormhole.is_active == True).count()
        total_usage = db.query(Wormhole).filter(Wormhole.is_active == True).with_entities(
            db.func.sum(Wormhole.usage_count)
        ).scalar() or 0
        
        stable_wormholes = db.query(Wormhole).filter(
            Wormhole.is_active == True,
            Wormhole.is_stable == True
        ).count()
        
        recent_usage = db.query(Wormhole).filter(
            Wormhole.is_active == True,
            Wormhole.last_used.isnot(None)
        ).count()
        
        return {
            "total_wormholes": total_wormholes,
            "stable_wormholes": stable_wormholes,
            "total_transits": total_usage,
            "recently_used": recent_usage,
            "max_wormholes": self.max_wormholes,
            "generation_odds": self.wormhole_odds
        }


# Global wormhole service instance
wormhole_service = WormholeService()
