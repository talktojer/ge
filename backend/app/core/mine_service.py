"""
Galactic Empire - Advanced Mine Field Service

This module handles advanced mine laying, detection, and field management operations
including mine deployment, field patterns, and tactical mine warfare.
"""

from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import random
import math

from ..models.mine import Mine, MineConstants
from ..models.user import User
from ..models.ship import Ship
from ..core.coordinates import calculate_distance, calculate_bearing


class MineService:
    """Service for advanced mine operations"""
    
    def __init__(self):
        self.max_mines = MineConstants.NUM_MINES  # 20 mines max
        self.mine_range = MineConstants.MINERANGE  # 10000 units
        self.decoy_time = MineConstants.DECOYTIME  # 15 ticks
        self.mine_damage_max = MineConstants.MINE_DAMAGE_MAX  # 100 damage
        
        self.mine_types = {
            0: "Standard",     # Standard proximity mine
            1: "Proximity",    # Enhanced proximity detection
            2: "Magnetic",     # Magnetic field detection
            3: "Thermal",      # Heat signature detection
            4: "Gravimetric",  # Mass detection
            5: "Decoy",        # Decoy mine (fake)
            6: "Cluster",      # Cluster mine (explodes into multiple)
            7: "EMP",          # EMP mine (disables systems)
            8: "Stealth",      # Stealth mine (harder to detect)
            9: "Anti-Fighter"  # Specialized anti-fighter mine
        }
    
    def lay_mine(self, db: Session, user_id: int, ship_id: int, x_coord: float, y_coord: float,
                mine_type: int = 0, damage_potential: int = None, is_visible: bool = False) -> Dict[str, Any]:
        """
        Lay a mine at specified coordinates
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
        
        # Check if user has reached mine limit
        user_mines = db.query(Mine).filter(
            Mine.owner_id == user_id,
            Mine.is_active == True
        ).count()
        
        if user_mines >= self.max_mines:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum mine limit reached ({self.max_mines} mines)"
            )
        
        # Validate mine type
        if mine_type not in self.mine_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mine type. Valid types: {list(self.mine_types.keys())}"
            )
        
        # Set default damage potential
        if damage_potential is None:
            damage_potential = random.randint(50, self.mine_damage_max)
        
        # Generate unique channel for mine
        channel = self._generate_mine_channel(db)
        
        # Create mine
        mine = Mine(
            channel=channel,
            timer=0,  # Timer for decoy mines
            x_coord=x_coord,
            y_coord=y_coord,
            owner_id=user_id,
            is_active=True,
            damage_potential=damage_potential,
            mine_type=mine_type,
            is_armed=True,
            is_visible=is_visible,
            armed_at=datetime.utcnow()
        )
        
        db.add(mine)
        db.commit()
        db.refresh(mine)
        
        return {
            "id": mine.id,
            "channel": mine.channel,
            "x_coord": mine.x_coord,
            "y_coord": mine.y_coord,
            "mine_type": mine.mine_type,
            "mine_type_name": self.mine_types[mine.mine_type],
            "damage_potential": mine.damage_potential,
            "is_visible": mine.is_visible,
            "is_armed": mine.is_armed,
            "armed_at": mine.armed_at.isoformat(),
            "total_mines": user_mines + 1
        }
    
    def lay_mine_field(self, db: Session, user_id: int, ship_id: int, center_x: float, center_y: float,
                      field_size: int, mine_count: int, mine_type: int = 0, 
                      pattern: str = "grid") -> Dict[str, Any]:
        """
        Lay a mine field with multiple mines in a pattern
        """
        if mine_count > self.max_mines:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot lay more than {self.max_mines} mines"
            )
        
        if mine_count <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mine count must be positive"
            )
        
        # Generate mine positions based on pattern
        positions = self._generate_mine_field_positions(center_x, center_y, field_size, mine_count, pattern)
        
        laid_mines = []
        failed_count = 0
        
        for x_coord, y_coord in positions:
            try:
                result = self.lay_mine(db, user_id, ship_id, x_coord, y_coord, mine_type)
                laid_mines.append(result)
            except HTTPException:
                failed_count += 1
                if failed_count >= 3:  # Stop after 3 failures
                    break
        
        return {
            "message": f"Laid {len(laid_mines)} mines in field",
            "field_center": {
                "x_coord": center_x,
                "y_coord": center_y
            },
            "field_size": field_size,
            "pattern": pattern,
            "requested_mines": mine_count,
            "laid_mines": len(laid_mines),
            "failed_mines": failed_count,
            "mines": laid_mines
        }
    
    def detect_mines(self, db: Session, x_coord: float, y_coord: float, 
                    detection_range: float = None, ship_class: str = None) -> List[Dict[str, Any]]:
        """
        Detect mines in range with detection effectiveness based on ship class
        """
        if detection_range is None:
            detection_range = self.mine_range
        
        # Find mines in range
        mines = db.query(Mine).filter(Mine.is_active == True, Mine.is_armed == True).all()
        
        detected_mines = []
        for mine in mines:
            distance = calculate_distance(x_coord, y_coord, mine.x_coord, mine.y_coord)
            if distance <= detection_range:
                # Calculate detection probability based on mine type and ship class
                detection_probability = self._calculate_detection_probability(
                    mine.mine_type, ship_class, distance, detection_range
                )
                
                # Roll for detection
                if random.random() < detection_probability:
                    detected_mines.append({
                        "id": mine.id,
                        "channel": mine.channel,
                        "x_coord": mine.x_coord,
                        "y_coord": mine.y_coord,
                        "distance": distance,
                        "bearing": calculate_bearing(x_coord, y_coord, mine.x_coord, mine.y_coord),
                        "mine_type": mine.mine_type,
                        "mine_type_name": self.mine_types[mine.mine_type],
                        "damage_potential": mine.damage_potential,
                        "is_visible": mine.is_visible,
                        "detection_confidence": detection_probability,
                        "armed_at": mine.armed_at.isoformat() if mine.armed_at else None
                    })
        
        # Sort by distance
        detected_mines.sort(key=lambda x: x["distance"])
        
        return detected_mines
    
    def trigger_mine(self, db: Session, mine_id: int, ship_id: int, user_id: int) -> Dict[str, Any]:
        """
        Trigger a mine and calculate damage
        """
        mine = db.query(Mine).filter(
            Mine.id == mine_id,
            Mine.is_active == True,
            Mine.is_armed == True
        ).first()
        
        if not mine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mine not found or not armed"
            )
        
        ship = db.query(Ship).filter(Ship.id == ship_id, Ship.owner_id == user_id).first()
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ship not found"
            )
        
        # Calculate damage based on mine type and ship characteristics
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
        
        db.commit()
        
        return {
            "message": f"Mine triggered! {self.mine_types[mine.mine_type]} mine exploded",
            "mine_type": mine.mine_type,
            "mine_type_name": self.mine_types[mine.mine_type],
            "total_damage": damage,
            "shield_damage": shield_damage,
            "hull_damage": hull_damage,
            "ship_shields_remaining": ship.shields,
            "ship_hull_remaining": ship.hull,
            "mine_location": {
                "x_coord": mine.x_coord,
                "y_coord": mine.y_coord
            }
        }
    
    def disarm_mine(self, db: Session, mine_id: int, user_id: int) -> Dict[str, Any]:
        """
        Attempt to disarm a mine (requires skill/equipment)
        """
        mine = db.query(Mine).filter(
            Mine.id == mine_id,
            Mine.is_active == True,
            Mine.is_armed == True
        ).first()
        
        if not mine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mine not found or not armed"
            )
        
        # Check if user owns the mine
        if mine.owner_id == user_id:
            # Owner can always disarm their own mines
            mine.is_armed = False
            db.commit()
            
            return {
                "message": "Mine disarmed successfully",
                "mine_id": mine.id,
                "mine_type": self.mine_types[mine.mine_type],
                "disarmed_by": "owner"
            }
        
        # For enemy mines, calculate disarm probability
        disarm_probability = self._calculate_disarm_probability(mine)
        
        if random.random() < disarm_probability:
            # Successfully disarmed
            mine.is_armed = False
            db.commit()
            
            return {
                "message": "Mine disarmed successfully",
                "mine_id": mine.id,
                "mine_type": self.mine_types[mine.mine_type],
                "disarmed_by": "enemy",
                "disarm_probability": disarm_probability
            }
        else:
            # Failed to disarm - mine might explode
            if random.random() < 0.3:  # 30% chance of explosion
                mine.is_active = False
                mine.is_armed = False
                mine.exploded_at = datetime.utcnow()
                db.commit()
                
                return {
                    "message": "Disarm attempt failed - mine exploded!",
                    "mine_id": mine.id,
                    "mine_type": self.mine_types[mine.mine_type],
                    "exploded": True
                }
            else:
                return {
                    "message": "Disarm attempt failed",
                    "mine_id": mine.id,
                    "mine_type": self.mine_types[mine.mine_type],
                    "exploded": False,
                    "disarm_probability": disarm_probability
                }
    
    def get_user_mines(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Get all mines owned by a user"""
        mines = db.query(Mine).filter(
            Mine.owner_id == user_id,
            Mine.is_active == True
        ).order_by(Mine.armed_at.desc()).all()
        
        return [
            {
                "id": mine.id,
                "channel": mine.channel,
                "x_coord": mine.x_coord,
                "y_coord": mine.y_coord,
                "mine_type": mine.mine_type,
                "mine_type_name": self.mine_types[mine.mine_type],
                "damage_potential": mine.damage_potential,
                "is_armed": mine.is_armed,
                "is_visible": mine.is_visible,
                "armed_at": mine.armed_at.isoformat() if mine.armed_at else None,
                "exploded_at": mine.exploded_at.isoformat() if mine.exploded_at else None
            }
            for mine in mines
        ]
    
    def get_mine_field_statistics(self, db: Session) -> Dict[str, Any]:
        """Get mine field system statistics"""
        total_mines = db.query(Mine).filter(Mine.is_active == True).count()
        armed_mines = db.query(Mine).filter(
            Mine.is_active == True,
            Mine.is_armed == True
        ).count()
        
        exploded_mines = db.query(Mine).filter(
            Mine.exploded_at.isnot(None)
        ).count()
        
        # Count by type
        type_counts = {}
        for mine_type, type_name in self.mine_types.items():
            count = db.query(Mine).filter(
                Mine.mine_type == mine_type,
                Mine.is_active == True
            ).count()
            type_counts[type_name] = count
        
        # Recent mines (last 24 hours)
        recent_mines = db.query(Mine).filter(
            Mine.is_active == True,
            Mine.armed_at > datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        return {
            "total_mines": total_mines,
            "armed_mines": armed_mines,
            "exploded_mines": exploded_mines,
            "mines_by_type": type_counts,
            "recent_mines_24h": recent_mines,
            "max_mines_per_user": self.max_mines,
            "mine_detection_range": self.mine_range
        }
    
    def _generate_mine_channel(self, db: Session) -> int:
        """Generate a unique channel for a mine"""
        while True:
            channel = random.randint(1000, 9999)
            existing = db.query(Mine).filter(Mine.channel == channel).first()
            if not existing:
                return channel
    
    def _generate_mine_field_positions(self, center_x: float, center_y: float, 
                                     field_size: int, mine_count: int, pattern: str) -> List[Tuple[float, float]]:
        """Generate mine positions based on pattern"""
        positions = []
        
        if pattern == "grid":
            # Grid pattern
            grid_size = int(math.sqrt(mine_count))
            spacing = field_size / grid_size
            
            for i in range(mine_count):
                x = center_x + (i % grid_size - grid_size // 2) * spacing
                y = center_y + (i // grid_size - grid_size // 2) * spacing
                positions.append((x, y))
        
        elif pattern == "circular":
            # Circular pattern
            radius = field_size / 2
            for i in range(mine_count):
                angle = (2 * math.pi * i) / mine_count
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                positions.append((x, y))
        
        elif pattern == "random":
            # Random pattern
            for i in range(mine_count):
                x = center_x + random.uniform(-field_size/2, field_size/2)
                y = center_y + random.uniform(-field_size/2, field_size/2)
                positions.append((x, y))
        
        return positions
    
    def _calculate_detection_probability(self, mine_type: int, ship_class: str, 
                                       distance: float, max_range: float) -> float:
        """Calculate mine detection probability"""
        base_probability = 0.8  # 80% base detection
        
        # Reduce probability based on distance
        distance_factor = 1.0 - (distance / max_range)
        
        # Modify based on mine type
        type_modifiers = {
            0: 1.0,    # Standard - normal detection
            1: 0.9,    # Proximity - slightly harder
            2: 0.8,    # Magnetic - harder
            3: 0.7,    # Thermal - much harder
            4: 0.6,    # Gravimetric - very hard
            5: 1.0,    # Decoy - easy to detect (it's fake)
            6: 0.8,    # Cluster - harder
            7: 0.7,    # EMP - harder
            8: 0.3,    # Stealth - very hard to detect
            9: 0.9     # Anti-Fighter - slightly harder
        }
        
        type_modifier = type_modifiers.get(mine_type, 1.0)
        
        # Ship class modifiers (if available)
        ship_modifiers = {
            "Interceptor": 1.2,    # Better sensors
            "Destroyer": 1.1,      # Good sensors
            "Cruiser": 1.0,        # Normal sensors
            "Freighter": 0.8,      # Poor sensors
            "Fighter": 1.3         # Excellent sensors
        }
        
        ship_modifier = ship_modifiers.get(ship_class, 1.0)
        
        final_probability = base_probability * distance_factor * type_modifier * ship_modifier
        return max(0.1, min(1.0, final_probability))  # Clamp between 10% and 100%
    
    def _calculate_mine_damage(self, mine: Mine, ship: Ship) -> int:
        """Calculate damage dealt by mine to ship"""
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
    
    def _calculate_disarm_probability(self, mine: Mine) -> float:
        """Calculate probability of successfully disarming a mine"""
        base_probability = 0.6  # 60% base chance
        
        # Modify based on mine type
        type_modifiers = {
            0: 1.0,    # Standard - normal difficulty
            1: 0.8,    # Proximity - harder
            2: 0.9,    # Magnetic - slightly harder
            3: 0.7,    # Thermal - harder
            4: 0.5,    # Gravimetric - very hard
            5: 1.0,    # Decoy - easy (it's fake)
            6: 0.6,    # Cluster - harder
            7: 0.8,    # EMP - harder
            8: 0.4,    # Stealth - very hard
            9: 0.7     # Anti-Fighter - harder
        }
        
        type_modifier = type_modifiers.get(mine.mine_type, 1.0)
        
        return base_probability * type_modifier


# Global mine service instance
mine_service = MineService()
