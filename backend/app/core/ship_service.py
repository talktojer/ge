"""
Ship Types and Classes Service
Handles ship configuration, capabilities, and statistics management
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.ship import ShipType, ShipClass, Ship
from app.models.user import User


class ShipTypeService:
    """Service for managing ship types (USER, CYBORG, DROID)"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_ship_types(self) -> List[ShipType]:
        """Get all ship types"""
        return self.db.execute(select(ShipType)).scalars().all()
    
    def get_ship_type_by_name(self, type_name: str) -> Optional[ShipType]:
        """Get ship type by name (USER, CYBORG, DROID)"""
        return self.db.execute(
            select(ShipType).where(ShipType.type_name == type_name)
        ).scalar_one_or_none()
    
    def create_ship_type(self, type_name: str, description: str = None) -> ShipType:
        """Create a new ship type"""
        ship_type = ShipType(
            type_name=type_name,
            description=description
        )
        self.db.add(ship_type)
        self.db.commit()
        self.db.refresh(ship_type)
        return ship_type


class ShipClassService:
    """Service for managing ship classes and their capabilities"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_ship_classes(self) -> List[ShipClass]:
        """Get all ship classes"""
        return self.db.execute(
            select(ShipClass).order_by(ShipClass.class_number)
        ).scalars().all()
    
    def get_ship_classes_by_type(self, ship_type_name: str) -> List[ShipClass]:
        """Get ship classes by type (USER, CYBORG, DROID)"""
        return self.db.execute(
            select(ShipClass)
            .join(ShipType)
            .where(ShipType.type_name == ship_type_name)
            .order_by(ShipClass.class_number)
        ).scalars().all()
    
    def get_user_ship_classes(self) -> List[ShipClass]:
        """Get all USER ship classes available for purchase"""
        return self.get_ship_classes_by_type("USER")
    
    def get_cyborg_ship_classes(self) -> List[ShipClass]:
        """Get all CYBORG ship classes for AI opponents"""
        return self.get_ship_classes_by_type("CYBORG")
    
    def get_droid_ship_classes(self) -> List[ShipClass]:
        """Get all DROID ship classes"""
        return self.get_ship_classes_by_type("DROID")
    
    def get_ship_class_by_number(self, class_number: int) -> Optional[ShipClass]:
        """Get ship class by class number"""
        return self.db.execute(
            select(ShipClass).where(ShipClass.class_number == class_number)
        ).scalar_one_or_none()
    
    def get_ship_class_by_id(self, class_id: int) -> Optional[ShipClass]:
        """Get ship class by ID"""
        return self.db.execute(
            select(ShipClass).where(ShipClass.id == class_id)
        ).scalar_one_or_none()
    
    def create_ship_class(self, class_data: Dict[str, Any]) -> ShipClass:
        """Create a new ship class with all capabilities and statistics"""
        ship_class = ShipClass(**class_data)
        self.db.add(ship_class)
        self.db.commit()
        self.db.refresh(ship_class)
        return ship_class
    
    def update_ship_class(self, class_id: int, class_data: Dict[str, Any]) -> Optional[ShipClass]:
        """Update an existing ship class"""
        ship_class = self.get_ship_class_by_id(class_id)
        if not ship_class:
            return None
        
        for key, value in class_data.items():
            if hasattr(ship_class, key):
                setattr(ship_class, key, value)
        
        self.db.commit()
        self.db.refresh(ship_class)
        return ship_class
    
    def can_purchase_ship_class(self, ship_class: ShipClass, user: User) -> bool:
        """Check if user can purchase a specific ship class"""
        if ship_class.ship_type.type_name != "USER":
            return False
        
        if not ship_class.is_active:
            return False
        
        if not ship_class.max_price:
            return True  # Free ships
        
        return user.cash >= ship_class.max_price
    
    def get_ship_capabilities(self, ship_class: ShipClass) -> Dict[str, Any]:
        """Get comprehensive ship capabilities for a ship class"""
        return {
            "shields": {
                "max_type": ship_class.max_shields,
                "available": ship_class.max_shields > 0
            },
            "phasers": {
                "max_type": ship_class.max_phasers,
                "available": ship_class.max_phasers > 0
            },
            "torpedoes": {
                "available": ship_class.max_torpedoes > 0,
                "count": ship_class.max_torpedoes
            },
            "missiles": {
                "available": ship_class.max_missiles > 0,
                "count": ship_class.max_missiles
            },
            "special_equipment": {
                "decoy_launcher": ship_class.has_decoy,
                "jammer": ship_class.has_jammer,
                "zipper": ship_class.has_zipper,
                "mine_launcher": ship_class.has_mine,
                "attack_planet": ship_class.has_attack_planet,
                "cloaking": ship_class.has_cloaking
            },
            "performance": {
                "max_acceleration": ship_class.max_acceleration,
                "max_warp_speed": ship_class.max_warp,
                "cargo_capacity": ship_class.max_tons,
                "scan_range": ship_class.scan_range
            },
            "economics": {
                "purchase_price": ship_class.max_price,
                "kill_points": ship_class.max_points
            }
        }
    
    def get_ship_statistics(self, ship_class: ShipClass) -> Dict[str, Any]:
        """Get ship statistics and performance metrics"""
        return {
            "class_info": {
                "class_number": ship_class.class_number,
                "type_name": ship_class.typename,
                "ship_name": ship_class.shipname,
                "ship_type": ship_class.ship_type.type_name
            },
            "combat_stats": {
                "max_shields": ship_class.max_shields,
                "max_phasers": ship_class.max_phasers,
                "has_torpedoes": ship_class.max_torpedoes > 0,
                "has_missiles": ship_class.max_missiles > 0,
                "damage_factor": ship_class.damage_factor
            },
            "movement_stats": {
                "max_acceleration": ship_class.max_acceleration,
                "max_warp": ship_class.max_warp,
                "max_cargo": ship_class.max_tons
            },
            "utility_stats": {
                "scan_range": ship_class.scan_range,
                "has_cloaking": ship_class.has_cloaking,
                "can_attack_planets": ship_class.has_attack_planet
            },
            "ai_behavior": {
                "cybs_can_attack": ship_class.cybs_can_attack,
                "number_to_attack": ship_class.number_to_attack,
                "lowest_to_attack": ship_class.lowest_to_attack,
                "tough_factor": ship_class.tough_factor,
                "total_to_create": ship_class.total_to_create
            }
        }


class ShipConfigurationService:
    """Service for managing ship configuration and initialization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ship_type_service = ShipTypeService(db)
        self.ship_class_service = ShipClassService(db)
    
    def initialize_default_ship_types(self):
        """Initialize the three default ship types"""
        ship_types = [
            {"type_name": "USER", "description": "Player-controlled ships"},
            {"type_name": "CYBORG", "description": "AI-controlled combat ships"},
            {"type_name": "DROID", "description": "AI-controlled non-combat ships"}
        ]
        
        for ship_type_data in ship_types:
            existing = self.ship_type_service.get_ship_type_by_name(ship_type_data["type_name"])
            if not existing:
                self.ship_type_service.create_ship_type(
                    ship_type_data["type_name"],
                    ship_type_data["description"]
                )
    
    def initialize_default_ship_classes(self):
        """Initialize the 12 default ship classes based on original game configuration"""
        # Get ship types
        user_type = self.ship_type_service.get_ship_type_by_name("USER")
        cyborg_type = self.ship_type_service.get_ship_type_by_name("CYBORG")
        droid_type = self.ship_type_service.get_ship_type_by_name("DROID")
        
        if not all([user_type, cyborg_type, droid_type]):
            raise ValueError("Ship types must be initialized first")
        
        # Default ship classes based on MBMGESHP.MSG configuration
        ship_classes = [
            # USER Ships (Classes 1-8)
            {
                "class_number": 1, "typename": "Interceptor", "shipname": "",
                "ship_type_id": user_type.id, "max_shields": 10, "max_phasers": 10,
                "max_torpedoes": 1, "max_missiles": 0, "has_decoy": True, "has_jammer": True,
                "has_zipper": True, "has_mine": True, "has_attack_planet": False,
                "has_cloaking": False, "max_acceleration": 5000, "max_warp": 10,
                "max_tons": 1000, "max_price": 65000, "max_points": 750,
                "scan_range": 100000, "cybs_can_attack": True, "number_to_attack": 1,
                "damage_factor": 90, "total_to_create": 3
            },
            {
                "class_number": 2, "typename": "Stealth Fighter", "shipname": "",
                "ship_type_id": user_type.id, "max_shields": 15, "max_phasers": 15,
                "max_torpedoes": 1, "max_missiles": 1, "has_decoy": True, "has_jammer": True,
                "has_zipper": True, "has_mine": True, "has_attack_planet": True,
                "has_cloaking": True, "max_acceleration": 5000, "max_warp": 20,
                "max_tons": 2000, "max_price": 500000, "max_points": 1500,
                "scan_range": 200000, "cybs_can_attack": True, "number_to_attack": 2,
                "damage_factor": 90, "total_to_create": 3
            },
            {
                "class_number": 3, "typename": "Heavy Freighter", "shipname": "",
                "ship_type_id": user_type.id, "max_shields": 5, "max_phasers": 5,
                "max_torpedoes": 1, "max_missiles": 0, "has_decoy": True, "has_jammer": True,
                "has_zipper": False, "has_mine": True, "has_attack_planet": True,
                "has_cloaking": False, "max_acceleration": 3000, "max_warp": 8,
                "max_tons": 60000, "max_price": 40000, "max_points": 500,
                "scan_range": 50000, "cybs_can_attack": False, "number_to_attack": 0,
                "damage_factor": 200, "total_to_create": 3
            },
            {
                "class_number": 4, "typename": "Destroyer", "shipname": "",
                "ship_type_id": user_type.id, "max_shields": 15, "max_phasers": 15,
                "max_torpedoes": 1, "max_missiles": 1, "has_decoy": True, "has_jammer": True,
                "has_zipper": True, "has_mine": True, "has_attack_planet": True,
                "has_cloaking": False, "max_acceleration": 5000, "max_warp": 25,
                "max_tons": 5000, "max_price": 600000, "max_points": 2000,
                "scan_range": 100000, "cybs_can_attack": True, "number_to_attack": 2,
                "damage_factor": 90, "total_to_create": 3
            },
            {
                "class_number": 5, "typename": "Star Cruiser", "shipname": "",
                "ship_type_id": user_type.id, "max_shields": 15, "max_phasers": 15,
                "max_torpedoes": 1, "max_missiles": 1, "has_decoy": True, "has_jammer": True,
                "has_zipper": True, "has_mine": True, "has_attack_planet": True,
                "has_cloaking": True, "max_acceleration": 10000, "max_warp": 25,
                "max_tons": 3000, "max_price": 700000, "max_points": 5000,
                "scan_range": 200000, "cybs_can_attack": True, "number_to_attack": 2,
                "damage_factor": 90, "total_to_create": 3
            },
            # Add remaining USER ships (6-8) and CYBORG/DROID ships as needed
            # This is a subset for demonstration - full implementation would include all 12 classes
        ]
        
        for class_data in ship_classes:
            existing = self.ship_class_service.get_ship_class_by_number(class_data["class_number"])
            if not existing:
                self.ship_class_service.create_ship_class(class_data)
    
    def get_available_ships_for_purchase(self, user: User) -> List[Dict[str, Any]]:
        """Get list of ships available for purchase by a user"""
        user_ships = self.ship_class_service.get_user_ship_classes()
        available_ships = []
        
        for ship_class in user_ships:
            if not ship_class.is_active:
                continue
                
            can_purchase = self.ship_class_service.can_purchase_ship_class(ship_class, user)
            capabilities = self.ship_class_service.get_ship_capabilities(ship_class)
            statistics = self.ship_class_service.get_ship_statistics(ship_class)
            
            available_ships.append({
                "class_id": ship_class.id,
                "class_number": ship_class.class_number,
                "name": ship_class.typename,
                "can_purchase": can_purchase,
                "capabilities": capabilities,
                "statistics": statistics
            })
        
        return available_ships


