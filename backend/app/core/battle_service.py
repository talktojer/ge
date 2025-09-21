"""
Galactic Empire - Battle Service

This service integrates all combat and battle systems including battle mechanics,
battle interface, and combat AI into a comprehensive battle management system.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.ship import Ship, ShipClass
from ..models.user import User
from .battle_mechanics import (
    BattleManager, AdvancedCombatMechanics, SelfDestructSystem,
    DamageType, DamageReport, BattleState
)
from .battle_interface import (
    TacticalDisplaySystem, RangeScanner, TargetLockingSystem,
    ScannerType, TacticalDisplayMode, TargetLockStatus
)
from .combat_ai import AIManager, AIShipData, AIDecision
from .coordinates import Coordinate, distance, bearing

logger = logging.getLogger(__name__)


class BattleService:
    """Main service for battle operations and combat management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.battle_manager = BattleManager()
        self.tactical_display = TacticalDisplaySystem()
        self.ai_manager = AIManager()
        
        # Combat systems
        self.combat_mechanics = AdvancedCombatMechanics()
        self.scanner = RangeScanner()
        self.target_lock = TargetLockingSystem()
    
    def initiate_combat(self, attacker_ship_id: int, defender_ship_id: int) -> Dict[str, Any]:
        """Initiate combat between two ships"""
        try:
            # Get ships from database
            attacker = self.db.query(Ship).filter(Ship.id == attacker_ship_id).first()
            defender = self.db.query(Ship).filter(Ship.id == defender_ship_id).first()
            
            if not attacker or not defender:
                return {"success": False, "message": "One or both ships not found"}
            
            # Calculate distance between ships
            attacker_pos = Coordinate(attacker.x_coord, attacker.y_coord)
            defender_pos = Coordinate(defender.x_coord, defender.y_coord)
            combat_range = distance(attacker_pos, defender_pos)
            
            # Start battle
            battle_result = self.battle_manager.start_battle(
                str(attacker_ship_id), str(defender_ship_id), combat_range
            )
            
            if battle_result["success"]:
                # Mark ships as hostile
                attacker.hostile = True
                defender.hostile = True
                self.db.commit()
                
                return {
                    "success": True,
                    "message": f"Combat initiated between {attacker.shipname} and {defender.shipname}",
                    "battle_key": battle_result["battle_key"],
                    "combat_range": combat_range,
                    "attacker": {
                        "id": attacker.id,
                        "name": attacker.shipname,
                        "class": attacker.ship_class.typename
                    },
                    "defender": {
                        "id": defender.id,
                        "name": defender.shipname,
                        "class": defender.ship_class.typename
                    }
                }
            else:
                return battle_result
                
        except Exception as e:
            logger.error(f"Error initiating combat: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Combat initiation error: {str(e)}"}
    
    def execute_weapon_attack(self, attacker_ship_id: int, target_ship_id: int,
                             weapon_type: str, **kwargs) -> Dict[str, Any]:
        """Execute weapon attack between ships"""
        try:
            # Get ships
            attacker = self.db.query(Ship).filter(Ship.id == attacker_ship_id).first()
            target = self.db.query(Ship).filter(Ship.id == target_ship_id).first()
            
            if not attacker or not target:
                return {"success": False, "message": "Ships not found"}
            
            # Create battle key
            battle_key = f"{attacker_ship_id}_{target_ship_id}"
            
            # Prepare ship data for combat calculations
            attacker_data = self._prepare_ship_combat_data(attacker)
            target_data = self._prepare_ship_combat_data(target)
            
            # Determine weapon damage
            weapon_damage = self._calculate_weapon_damage(attacker, weapon_type, kwargs)
            
            # Map weapon type to DamageType enum
            damage_type_map = {
                "phasers": DamageType.PHASER,
                "torpedoes": DamageType.TORPEDO,
                "missiles": DamageType.MISSILE,
                "ion_cannon": DamageType.ION_CANNON
            }
            damage_type = damage_type_map.get(weapon_type, DamageType.PHASER)
            
            # Process battle action
            battle_result = self.battle_manager.process_battle_action(
                battle_key, attacker_data, target_data, damage_type, weapon_damage
            )
            
            if battle_result["success"]:
                damage_report = battle_result["damage_report"]
                
                # Apply damage to target ship
                self._apply_damage_to_ship(target, damage_report)
                
                # Consume attacker energy/ammunition
                self._consume_weapon_resources(attacker, weapon_type, kwargs)
                
                # Generate tactical display update
                tactical_update = self._generate_combat_display_update(
                    attacker, target, damage_report
                )
                
                self.db.commit()
                
                return {
                    "success": True,
                    "attacker_id": attacker_ship_id,
                    "target_id": target_ship_id,
                    "weapon_type": weapon_type,
                    "damage_report": self.tactical_display.generate_damage_report(damage_report),
                    "tactical_update": tactical_update,
                    "battle_continues": battle_result["battle_continues"],
                    "target_destroyed": damage_report.ship_destroyed
                }
            else:
                return battle_result
                
        except Exception as e:
            logger.error(f"Error executing weapon attack: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Attack execution error: {str(e)}"}
    
    def perform_scanner_sweep(self, ship_id: int, scanner_type: str,
                             scan_range: Optional[float] = None) -> Dict[str, Any]:
        """Perform scanner sweep for a ship"""
        try:
            ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
            if not ship:
                return {"success": False, "message": "Ship not found"}
            
            # Check energy requirements
            scanner_enum = ScannerType(scanner_type)
            
            # Get all objects in scan range
            all_objects = self._get_objects_for_scan(ship)
            
            # Perform scan
            scan_result = self.scanner.perform_scan(
                scanner_enum,
                Coordinate(ship.x_coord, ship.y_coord),
                int(ship.energy),
                scan_range,
                all_objects
            )
            
            if scan_result["success"]:
                # Consume energy
                ship.energy -= scan_result["energy_consumed"]
                self.db.commit()
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Error performing scanner sweep: {e}")
            return {"success": False, "message": f"Scanner error: {str(e)}"}
    
    def acquire_target_lock(self, ship_id: int, target_ship_id: int) -> Dict[str, Any]:
        """Acquire target lock on another ship"""
        try:
            ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
            target = self.db.query(Ship).filter(Ship.id == target_ship_id).first()
            
            if not ship or not target:
                return {"success": False, "message": "Ships not found"}
            
            # Calculate target distance and bearing
            ship_pos = Coordinate(ship.x_coord, ship.y_coord)
            target_pos = Coordinate(target.x_coord, target.y_coord)
            target_distance = distance(ship_pos, target_pos)
            target_bearing = bearing(ship_pos, target_pos)
            
            # Attempt target lock
            lock_result = self.target_lock.acquire_target_lock(
                str(ship_id), str(target_ship_id),
                target_distance, target_bearing,
                ship.fire_control
            )
            
            return lock_result
            
        except Exception as e:
            logger.error(f"Error acquiring target lock: {e}")
            return {"success": False, "message": f"Target lock error: {str(e)}"}
    
    def generate_tactical_display(self, ship_id: int, display_mode: str,
                                display_range: float = 150000.0) -> Dict[str, Any]:
        """Generate tactical display for a ship"""
        try:
            ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
            if not ship:
                return {"success": False, "message": "Ship not found"}
            
            # Get ship position
            ship_pos = Coordinate(ship.x_coord, ship.y_coord)
            
            # Get nearby objects
            nearby_objects = self._get_objects_for_scan(ship, display_range)
            
            # Prepare ship data
            ship_data = self._prepare_ship_combat_data(ship)
            
            # Generate display
            display_mode_enum = TacticalDisplayMode(display_mode)
            tactical_display = self.tactical_display.generate_tactical_display(
                ship_pos, display_mode_enum, display_range, ship_data, nearby_objects
            )
            
            return {
                "success": True,
                "display_mode": tactical_display.display_mode.value,
                "center_position": {
                    "x": tactical_display.center_position.x,
                    "y": tactical_display.center_position.y
                },
                "display_range": tactical_display.display_range,
                "objects": tactical_display.objects,
                "grid_lines": tactical_display.grid_lines,
                "threat_assessment": tactical_display.threat_assessment,
                "navigation_data": tactical_display.navigation_data,
                "damage_status": tactical_display.damage_status
            }
            
        except Exception as e:
            logger.error(f"Error generating tactical display: {e}")
            return {"success": False, "message": f"Tactical display error: {str(e)}"}
    
    def initiate_self_destruct(self, ship_id: int, user_id: int) -> Dict[str, Any]:
        """Initiate self-destruct sequence"""
        try:
            ship = self.db.query(Ship).filter(
                Ship.id == ship_id, Ship.user_id == user_id
            ).first()
            
            if not ship:
                return {"success": False, "message": "Ship not found or not owned by user"}
            
            # Get ship class data for blast calculations
            ship_class_data = {
                "max_points": ship.ship_class.max_points,
                "max_tons": ship.ship_class.max_tons
            }
            
            # Initiate self-destruct
            result = self.battle_manager.self_destruct.initiate_self_destruct(
                str(ship_id), str(user_id), ship_class_data
            )
            
            if result["success"]:
                # Mark ship as self-destructing
                ship.destruct = result["countdown"]
                self.db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error initiating self-destruct: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Self-destruct error: {str(e)}"}
    
    def abort_self_destruct(self, ship_id: int, user_id: int, abort_code: str) -> Dict[str, Any]:
        """Abort self-destruct sequence"""
        try:
            ship = self.db.query(Ship).filter(
                Ship.id == ship_id, Ship.user_id == user_id
            ).first()
            
            if not ship:
                return {"success": False, "message": "Ship not found or not owned by user"}
            
            # Abort self-destruct
            result = self.battle_manager.self_destruct.abort_self_destruct(
                str(ship_id), abort_code
            )
            
            if result["success"]:
                ship.destruct = 0
                self.db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error aborting self-destruct: {e}")
            return {"success": False, "message": f"Abort error: {str(e)}"}
    
    def process_ai_ships(self, nearby_objects_by_ship: Dict[str, List[Dict[str, Any]]],
                        game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Process AI ship decisions and actions"""
        try:
            # Process AI tick
            ai_decisions = self.ai_manager.process_ai_tick(nearby_objects_by_ship, game_state)
            
            # Execute AI decisions
            executed_actions = []
            for ship_id, decision in ai_decisions.items():
                action_result = self._execute_ai_decision(ship_id, decision)
                if action_result:
                    executed_actions.append(action_result)
            
            return {
                "success": True,
                "ai_ships_processed": len(ai_decisions),
                "actions_executed": len(executed_actions),
                "decisions": {ship_id: {
                    "action_type": decision.action_type,
                    "target_id": decision.target_id,
                    "priority": decision.priority,
                    "reasoning": decision.reasoning
                } for ship_id, decision in ai_decisions.items()},
                "executed_actions": executed_actions
            }
            
        except Exception as e:
            logger.error(f"Error processing AI ships: {e}")
            return {"success": False, "message": f"AI processing error: {str(e)}"}
    
    def process_battle_tick(self) -> Dict[str, Any]:
        """Process all battle systems for one tick"""
        try:
            # Process active battles
            battle_results = self.battle_manager.process_battle_tick()
            
            # Process target locks
            lock_results = self.target_lock.process_lock_tick()
            
            # Process self-destructs (handled by battle manager)
            
            return {
                "success": True,
                "battles_processed": len(battle_results),
                "locks_processed": len(lock_results),
                "battle_results": battle_results,
                "lock_results": lock_results
            }
            
        except Exception as e:
            logger.error(f"Error processing battle tick: {e}")
            return {"success": False, "message": f"Battle tick error: {str(e)}"}
    
    def get_battle_status(self, ship_id: int) -> Optional[Dict[str, Any]]:
        """Get current battle status for a ship"""
        try:
            battle_status = self.battle_manager.get_battle_status(str(ship_id))
            if battle_status:
                return battle_status
            
            # Check for self-destruct status
            self_destruct_status = self.battle_manager.self_destruct.get_self_destruct_status(str(ship_id))
            if self_destruct_status:
                return {
                    "type": "self_destruct",
                    "status": self_destruct_status
                }
            
            # Check for AI status
            ai_status = self.ai_manager.get_ai_ship_status(str(ship_id))
            if ai_status:
                return {
                    "type": "ai_controlled",
                    "status": ai_status
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting battle status: {e}")
            return None
    
    def _prepare_ship_combat_data(self, ship: Ship) -> Dict[str, Any]:
        """Prepare ship data for combat calculations"""
        return {
            "ship_id": ship.id,
            "ship_class": ship.ship_class.class_number,
            "damage_factor": ship.ship_class.damage_factor,
            "max_shields": ship.ship_class.max_shields,
            "shield_type": ship.shield_type,
            "shield_charge": ship.shield_charge,
            "damage": ship.damage,
            "energy": ship.energy,
            "tactical_damage": ship.tactical,
            "helm_damage": ship.helm,
            "fire_control_damage": ship.fire_control,
            "optimal_range": 100000.0,  # Could be based on ship class
            "position": {"x": ship.x_coord, "y": ship.y_coord}
        }
    
    def _calculate_weapon_damage(self, ship: Ship, weapon_type: str, kwargs: Dict[str, Any]) -> float:
        """Calculate weapon damage based on ship and weapon type"""
        try:
            base_damage = 50.0
            
            if weapon_type == "phasers":
                base_damage = ship.phaser_strength * 2.0
                if kwargs.get("hyper_phasers", False):
                    base_damage *= 2.0
            elif weapon_type == "torpedoes":
                base_damage = 150.0
            elif weapon_type == "missiles":
                base_damage = 100.0
            elif weapon_type == "ion_cannon":
                base_damage = 200.0
            
            return base_damage
            
        except Exception as e:
            logger.error(f"Error calculating weapon damage: {e}")
            return 50.0
    
    def _apply_damage_to_ship(self, ship: Ship, damage_report: DamageReport):
        """Apply damage report to ship in database"""
        try:
            # Apply hull damage
            ship.damage = min(100.0, ship.damage + damage_report.hull_damage)
            
            # Apply shield damage
            if damage_report.shield_damage > 0:
                ship.shield_charge = max(0, ship.shield_charge - int(damage_report.shield_damage))
            
            # Apply system damage
            for system, damage in damage_report.system_damage.items():
                if system.value == "tactical":
                    ship.tactical = min(100, ship.tactical + int(damage))
                elif system.value == "helm":
                    ship.helm = min(100, ship.helm + int(damage))
                elif system.value == "fire_control":
                    if damage > 50:
                        ship.fire_control = True
            
            # Check if ship is destroyed
            if damage_report.ship_destroyed:
                ship.status = 2  # Destroyed status
                
        except Exception as e:
            logger.error(f"Error applying damage to ship: {e}")
    
    def _consume_weapon_resources(self, ship: Ship, weapon_type: str, kwargs: Dict[str, Any]):
        """Consume energy/ammunition for weapon use"""
        try:
            if weapon_type == "phasers":
                energy_cost = 100
                if kwargs.get("hyper_phasers", False):
                    energy_cost = 500
                ship.energy = max(0, ship.energy - energy_cost)
                
            elif weapon_type == "torpedoes":
                ship.energy = max(0, ship.energy - 200)
                # TODO: Implement torpedo ammunition tracking
                
            elif weapon_type == "missiles":
                ship.energy = max(0, ship.energy - 150)
                # TODO: Implement missile ammunition tracking
                
            elif weapon_type == "ion_cannon":
                ship.energy = max(0, ship.energy - 400)
                
        except Exception as e:
            logger.error(f"Error consuming weapon resources: {e}")
    
    def _get_objects_for_scan(self, ship: Ship, max_range: float = 200000.0) -> List[Dict[str, Any]]:
        """Get all objects within scan range of ship"""
        try:
            objects = []
            ship_pos = Coordinate(ship.x_coord, ship.y_coord)
            
            # Get other ships
            other_ships = self.db.query(Ship).filter(Ship.id != ship.id).all()
            for other_ship in other_ships:
                other_pos = Coordinate(other_ship.x_coord, other_ship.y_coord)
                dist = distance(ship_pos, other_pos)
                
                if dist <= max_range:
                    objects.append({
                        "id": other_ship.id,
                        "type": "ship",
                        "name": other_ship.shipname,
                        "x": other_ship.x_coord,
                        "y": other_ship.y_coord,
                        "is_cloaked": other_ship.cloak == -1,
                        "is_hostile": other_ship.hostile,
                        "ship_class": other_ship.ship_class.class_number,
                        "damage": other_ship.damage
                    })
            
            # TODO: Add planets, mines, beacons, etc.
            
            return objects
            
        except Exception as e:
            logger.error(f"Error getting objects for scan: {e}")
            return []
    
    def _generate_combat_display_update(self, attacker: Ship, target: Ship,
                                      damage_report: DamageReport) -> Dict[str, Any]:
        """Generate tactical display update for combat"""
        try:
            return {
                "combat_event": {
                    "attacker": attacker.shipname,
                    "target": target.shipname,
                    "weapon_used": damage_report.damage_type.value,
                    "damage_dealt": damage_report.total_damage,
                    "critical_hit": len(damage_report.critical_hits) > 0,
                    "target_destroyed": damage_report.ship_destroyed
                },
                "target_status": {
                    "hull_damage": target.damage,
                    "shield_charge": target.shield_charge,
                    "systems_damaged": damage_report.systems_destroyed
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating combat display update: {e}")
            return {}
    
    def _execute_ai_decision(self, ship_id: str, decision: AIDecision) -> Optional[Dict[str, Any]]:
        """Execute an AI decision"""
        try:
            # This is a simplified implementation
            # In a full implementation, this would execute the actual AI actions
            return {
                "ship_id": ship_id,
                "action_executed": decision.action_type,
                "target_id": decision.target_id,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error executing AI decision: {e}")
            return None
