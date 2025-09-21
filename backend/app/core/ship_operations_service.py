"""
Galactic Empire - Ship Operations Service

This service integrates ship operations, combat systems, and ship management
into a comprehensive ship control interface.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.ship import Ship, ShipClass, ShipType
from ..models.user import User
from .ship_operations import (
    ShipOperations, NavigationCommand, ShipStatus, CargoManagement,
    ShieldStatus, CloakStatus, EnergySystem
)
from .combat_systems import (
    CombatController, WeaponStatus, CombatTarget, WeaponType, 
    TargetType, CombatResult
)
from .coordinates import Coordinate
from .movement import create_movement_state, MovementState
from .ship_service import ShipClassService

logger = logging.getLogger(__name__)


class ShipOperationsService:
    """Main service for ship operations and combat"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ship_operations = ShipOperations()
        self.combat_controller = CombatController()
        self.cargo_management = CargoManagement()
        self.ship_class_service = ShipClassService(db)
    
    def convert_ship_to_status(self, ship: Ship) -> ShipStatus:
        """Convert database Ship model to ShipStatus for operations"""
        return ShipStatus(
            ship_id=str(ship.id),
            energy=ship.energy,
            max_energy=50000.0,  # Base max energy, could be modified by ship class
            damage=ship.damage,
            shield_status=ShieldStatus(ship.shield_status),
            shield_charge=ship.shield_charge,
            shield_type=ship.shield_type,
            cloak_status=CloakStatus(ship.cloak),
            cloak_time=abs(ship.cloak) if ship.cloak > 0 else 0,
            phaser_strength=ship.phaser_strength,
            phaser_type=ship.phaser_type,
            tactical_damage=ship.tactical,
            helm_damage=ship.helm,
            fire_control_damage=ship.fire_control,
            repair_in_progress=ship.repair,
            hostile=ship.hostile,
            jammer_active=ship.jammer > 0,
            destruct_countdown=ship.destruct
        )
    
    def convert_status_to_ship(self, ship_status: ShipStatus, ship: Ship) -> Ship:
        """Update database Ship model from ShipStatus"""
        ship.energy = ship_status.energy
        ship.damage = ship_status.damage
        ship.shield_status = ship_status.shield_status.value
        ship.shield_charge = ship_status.shield_charge
        ship.shield_type = ship_status.shield_type
        ship.cloak = ship_status.cloak_status.value
        ship.phaser_strength = ship_status.phaser_strength
        ship.phaser_type = ship_status.phaser_type
        ship.tactical = ship_status.tactical_damage
        ship.helm = ship_status.helm_damage
        ship.fire_control = ship_status.fire_control_damage
        ship.repair = ship_status.repair_in_progress
        ship.hostile = ship_status.hostile
        ship.jammer = 1 if ship_status.jammer_active else 0
        ship.destruct = ship_status.destruct_countdown
        ship.last_activity = datetime.utcnow()
        return ship
    
    def create_movement_state_from_ship(self, ship: Ship) -> MovementState:
        """Create MovementState from database Ship model"""
        position = Coordinate(ship.x_coord, ship.y_coord)
        return create_movement_state(
            position=position,
            heading=ship.heading,
            speed=ship.speed,
            max_speed=ship.ship_class.max_warp * 1000,  # Convert warp to speed units
            max_acceleration=ship.ship_class.max_acceleration
        )
    
    def update_ship_from_movement_state(self, ship: Ship, movement_state: MovementState) -> Ship:
        """Update database Ship model from MovementState"""
        ship.x_coord = movement_state.position.x
        ship.y_coord = movement_state.position.y
        ship.heading = movement_state.heading
        ship.speed = movement_state.speed
        ship.speed2b = movement_state.target_speed
        ship.head2b = movement_state.target_heading
        return ship
    
    def execute_navigation_command(self, ship_id: int, command: NavigationCommand) -> Dict[str, Any]:
        """Execute navigation command for a ship"""
        try:
            # Get ship from database
            ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
            if not ship:
                return {"success": False, "message": "Ship not found"}
            
            # Convert to operational objects
            ship_status = self.convert_ship_to_status(ship)
            movement_state = self.create_movement_state_from_ship(ship)
            
            # Execute navigation command
            new_movement_state, result = self.ship_operations.execute_navigation_command(
                ship_status, movement_state, command
            )
            
            # Update ship status if energy was consumed
            if result.get("energy_consumed", 0) > 0:
                ship_status.energy -= result["energy_consumed"]
                ship = self.convert_status_to_ship(ship_status, ship)
            
            # Update ship position/movement
            ship = self.update_ship_from_movement_state(ship, new_movement_state)
            
            # Save changes
            self.db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing navigation command: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Navigation error: {str(e)}"}
    
    def manage_shields(self, ship_id: int, action: str, shield_type: Optional[int] = None) -> Dict[str, Any]:
        """Manage ship shield systems"""
        try:
            ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
            if not ship:
                return {"success": False, "message": "Ship not found"}
            
            ship_status = self.convert_ship_to_status(ship)
            
            # Execute shield management
            new_ship_status, result = self.ship_operations.manage_shields(
                ship_status, action, shield_type
            )
            
            # Update ship in database
            ship = self.convert_status_to_ship(new_ship_status, ship)
            self.db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error managing shields: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Shield error: {str(e)}"}
    
    def manage_cloaking(self, ship_id: int, action: str) -> Dict[str, Any]:
        """Manage ship cloaking device"""
        try:
            ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
            if not ship:
                return {"success": False, "message": "Ship not found"}
            
            # Check if ship has cloaking capability
            if not ship.ship_class.has_cloaking:
                return {"success": False, "message": "Ship does not have cloaking device"}
            
            ship_status = self.convert_ship_to_status(ship)
            
            # Execute cloaking management
            new_ship_status, result = self.ship_operations.manage_cloaking(ship_status, action)
            
            # Update ship in database
            ship = self.convert_status_to_ship(new_ship_status, ship)
            self.db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error managing cloaking: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Cloaking error: {str(e)}"}
    
    def execute_combat_action(self, ship_id: int, action_type: str, 
                            target_id: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """Execute combat action"""
        try:
            ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
            if not ship:
                return {"success": False, "message": "Ship not found"}
            
            ship_status = self.convert_ship_to_status(ship)
            
            # Get weapon status based on ship class and current condition
            weapon_status = self.get_weapon_status(ship, action_type)
            
            # Get target information if specified
            target = None
            if target_id:
                target = self.get_combat_target(target_id, ship)
            
            # Prepare ship status dict for combat controller
            ship_status_dict = {
                "energy": ship_status.energy,
                "fire_control_damage": ship_status.fire_control_damage,
                "torpedo_count": 10,  # TODO: Track actual torpedo count
                "missile_count": 10,  # TODO: Track actual missile count
                "decoy_count": 5,     # TODO: Track actual decoy count
                "mine_count": 5,      # TODO: Track actual mine count
                "jammer_active": ship_status.jammer_active
            }
            
            # Execute combat action
            result = self.combat_controller.execute_combat_action(
                action_type, weapon_status, target, ship_status_dict, **kwargs
            )
            
            # Update ship energy and status
            if result.energy_consumed > 0:
                ship_status.energy -= result.energy_consumed
                ship = self.convert_status_to_ship(ship_status, ship)
            
            # Update ammunition counts (TODO: implement proper tracking)
            
            self.db.commit()
            
            # Convert CombatResult to dict
            return {
                "success": result.success,
                "message": result.message,
                "damage_dealt": result.damage_dealt,
                "energy_consumed": result.energy_consumed,
                "ammunition_used": result.ammunition_used,
                "hit": result.hit,
                "critical_hit": result.critical_hit,
                "target_destroyed": result.target_destroyed,
                "effects": result.effects
            }
            
        except Exception as e:
            logger.error(f"Error executing combat action: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Combat error: {str(e)}"}
    
    def get_weapon_status(self, ship: Ship, weapon_type: str) -> WeaponStatus:
        """Get weapon status for ship based on ship class and current condition"""
        ship_class = ship.ship_class
        
        # Map action types to weapon types
        weapon_type_map = {
            "fire_phasers": WeaponType.PHASER,
            "fire_torpedo": WeaponType.TORPEDO,
            "fire_missile": WeaponType.MISSILE,
            "launch_decoy": WeaponType.DECOY,
            "activate_jammer": WeaponType.JAMMER,
            "lay_mine": WeaponType.MINE
        }
        
        weapon_enum = weapon_type_map.get(weapon_type, WeaponType.PHASER)
        
        # Determine availability based on ship class
        available = False
        if weapon_enum == WeaponType.PHASER:
            available = ship_class.max_phasers > 0
        elif weapon_enum == WeaponType.TORPEDO:
            available = ship_class.max_torpedoes > 0
        elif weapon_enum == WeaponType.MISSILE:
            available = ship_class.max_missiles > 0
        elif weapon_enum == WeaponType.DECOY:
            available = ship_class.has_decoy
        elif weapon_enum == WeaponType.JAMMER:
            available = ship_class.has_jammer
        elif weapon_enum == WeaponType.MINE:
            available = ship_class.has_mine
        
        # Factor in damage
        damage_modifier = 1.0 - (ship.damage / 200.0)  # Max 50% reduction
        
        return WeaponStatus(
            weapon_type=weapon_enum,
            available=available and not ship.fire_control,
            energy_level=ship.phaser_strength if weapon_enum == WeaponType.PHASER else 100.0,
            ammunition=10,  # TODO: Track actual ammunition
            cooldown_time=0,  # TODO: Implement cooldown tracking
            damage_modifier=damage_modifier,
            range_modifier=1.0
        )
    
    def get_combat_target(self, target_id: int, attacking_ship: Ship) -> Optional[CombatTarget]:
        """Get combat target information"""
        try:
            target_ship = self.db.query(Ship).filter(Ship.id == target_id).first()
            if not target_ship:
                return None
            
            # Calculate distance and bearing
            attacker_pos = Coordinate(attacking_ship.x_coord, attacking_ship.y_coord)
            target_pos = Coordinate(target_ship.x_coord, target_ship.y_coord)
            
            from .coordinates import distance, bearing
            target_distance = distance(attacker_pos, target_pos)
            target_bearing = bearing(attacker_pos, target_pos)
            
            # Determine target characteristics
            shield_status = target_ship.shield_status > 0
            cloak_status = target_ship.cloak == -1  # -1 means cloaked
            
            # Size factor based on ship class (larger ships easier to hit)
            size_factor = 50 + (target_ship.ship_class.class_number * 10)
            
            return CombatTarget(
                target_id=str(target_id),
                target_type=TargetType.SHIP,
                position=target_pos,
                distance=target_distance,
                bearing=target_bearing,
                shield_status=shield_status,
                cloak_status=cloak_status,
                size_factor=size_factor
            )
            
        except Exception as e:
            logger.error(f"Error getting combat target: {e}")
            return None
    
    def process_ship_tick(self, ship_id: int) -> Dict[str, Any]:
        """Process ship systems for one tick"""
        try:
            ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
            if not ship:
                return {"success": False, "message": "Ship not found"}
            
            ship_status = self.convert_ship_to_status(ship)
            
            # Process energy regeneration
            ship_status = self.ship_operations.process_energy_regeneration(ship_status)
            
            # Process system energy drain
            ship_status = self.ship_operations.process_system_drain(ship_status)
            
            # Process repairs if in progress
            repair_result = {}
            if ship_status.repair_in_progress:
                ship_status, repair_result = self.ship_operations.process_ship_repairs(ship_status)
            
            # Update ship in database
            ship = self.convert_status_to_ship(ship_status, ship)
            self.db.commit()
            
            return {
                "success": True,
                "energy": ship_status.energy,
                "damage": ship_status.damage,
                "repairs": repair_result.get("repairs_made", []),
                "shield_status": ship_status.shield_status.name,
                "cloak_status": ship_status.cloak_status.name
            }
            
        except Exception as e:
            logger.error(f"Error processing ship tick: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Tick processing error: {str(e)}"}
    
    def get_ship_status(self, ship_id: int) -> Dict[str, Any]:
        """Get comprehensive ship status"""
        try:
            ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
            if not ship:
                return {"success": False, "message": "Ship not found"}
            
            ship_status = self.convert_ship_to_status(ship)
            capabilities = self.ship_class_service.get_ship_capabilities(ship.ship_class)
            
            return {
                "success": True,
                "ship_info": {
                    "id": ship.id,
                    "name": ship.shipname,
                    "class": ship.ship_class.typename,
                    "class_number": ship.ship_class.class_number
                },
                "position": {
                    "x": ship.x_coord,
                    "y": ship.y_coord,
                    "heading": ship.heading,
                    "speed": ship.speed
                },
                "status": {
                    "energy": ship_status.energy,
                    "max_energy": ship_status.max_energy,
                    "damage": ship_status.damage,
                    "shield_status": ship_status.shield_status.name,
                    "shield_charge": ship_status.shield_charge,
                    "cloak_status": ship_status.cloak_status.name,
                    "phaser_strength": ship_status.phaser_strength,
                    "hostile": ship_status.hostile,
                    "repair_in_progress": ship_status.repair_in_progress
                },
                "capabilities": capabilities,
                "damage_reports": {
                    "tactical": ship_status.tactical_damage,
                    "helm": ship_status.helm_damage,
                    "fire_control": ship_status.fire_control_damage
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting ship status: {e}")
            return {"success": False, "message": f"Status error: {str(e)}"}
    
    def manage_cargo(self, ship_id: int, action: str, item_type: int, 
                    quantity: int) -> Dict[str, Any]:
        """Manage ship cargo operations"""
        try:
            ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
            if not ship:
                return {"success": False, "message": "Ship not found"}
            
            # TODO: Implement cargo tracking in ship model
            # For now, return placeholder
            current_cargo = {}  # This would come from ship cargo table
            
            if action == "load":
                can_carry = self.cargo_management.can_carry_cargo(
                    ship.ship_class.max_tons, current_cargo, item_type, quantity
                )
                if not can_carry:
                    return {"success": False, "message": "Insufficient cargo capacity"}
                
                new_cargo = self.cargo_management.add_cargo(current_cargo, item_type, quantity)
                # TODO: Update ship cargo in database
                
                return {
                    "success": True,
                    "message": f"Loaded {quantity} units of item type {item_type}",
                    "cargo": new_cargo
                }
                
            elif action == "unload":
                if current_cargo.get(item_type, 0) < quantity:
                    return {"success": False, "message": "Insufficient cargo to unload"}
                
                new_cargo = self.cargo_management.remove_cargo(current_cargo, item_type, quantity)
                # TODO: Update ship cargo in database
                
                return {
                    "success": True,
                    "message": f"Unloaded {quantity} units of item type {item_type}",
                    "cargo": new_cargo
                }
            
            else:
                return {"success": False, "message": f"Unknown cargo action: {action}"}
                
        except Exception as e:
            logger.error(f"Error managing cargo: {e}")
            return {"success": False, "message": f"Cargo error: {str(e)}"}
