"""
Galactic Empire - Advanced Battle Mechanics

This module implements comprehensive battle mechanics including damage calculations,
shield hit mechanics, weapon effectiveness, critical hits, and self-destruct systems.
Based on the original game's combat calculations.
"""

import logging
import math
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .coordinates import Coordinate, distance, bearing
from .combat_systems import CombatResult, WeaponType, TargetType

logger = logging.getLogger(__name__)


class DamageType(Enum):
    """Type of damage being dealt"""
    PHASER = "phaser"
    TORPEDO = "torpedo"
    MISSILE = "missile"
    ION_CANNON = "ion_cannon"
    MINE = "mine"
    COLLISION = "collision"
    SELF_DESTRUCT = "self_destruct"
    SYSTEM_FAILURE = "system_failure"


class ShieldType(Enum):
    """Shield type enumeration from original game"""
    TYPE_0 = 0   # No shields
    TYPE_1 = 1   # Basic shields
    TYPE_2 = 2   # Standard shields
    TYPE_3 = 3   # Advanced shields
    TYPE_4 = 4   # Military shields
    TYPE_5 = 5   # Heavy shields
    TYPE_10 = 10 # Class 10 shields
    TYPE_15 = 15 # Class 15 shields
    TYPE_19 = 19 # Maximum shields


class SystemDamage(Enum):
    """Ship system that can be damaged"""
    HULL = "hull"
    SHIELDS = "shields"
    PHASERS = "phasers"
    TORPEDOES = "torpedoes"
    MISSILES = "missiles"
    ENGINES = "engines"
    HELM = "helm"
    TACTICAL = "tactical"
    FIRE_CONTROL = "fire_control"
    CLOAKING = "cloaking"
    LIFE_SUPPORT = "life_support"


@dataclass
class DamageReport:
    """Detailed damage report from combat"""
    total_damage: float
    shield_damage: float
    hull_damage: float
    system_damage: Dict[SystemDamage, float]
    critical_hits: List[str]
    systems_destroyed: List[SystemDamage]
    ship_destroyed: bool
    damage_type: DamageType
    weapon_effectiveness: float
    shield_effectiveness: float


@dataclass
class BattleState:
    """Current state of a battle between ships"""
    attacker_id: str
    defender_id: str
    battle_start: datetime
    battle_duration: int  # in ticks
    attacker_damage_dealt: float
    defender_damage_dealt: float
    battle_range: float
    last_action: datetime
    is_active: bool


@dataclass
class SelfDestructState:
    """Self-destruct system state"""
    ship_id: str
    countdown: int  # ticks remaining
    initiated_by: str
    can_abort: bool
    abort_code: Optional[str]
    blast_radius: float
    blast_damage: float


class AdvancedCombatMechanics:
    """Advanced combat mechanics and damage calculations"""
    
    def __init__(self):
        # Shield effectiveness by type
        self.shield_effectiveness = {
            ShieldType.TYPE_0: 0.0,
            ShieldType.TYPE_1: 0.1,
            ShieldType.TYPE_2: 0.2,
            ShieldType.TYPE_3: 0.3,
            ShieldType.TYPE_4: 0.4,
            ShieldType.TYPE_5: 0.5,
            ShieldType.TYPE_10: 0.75,
            ShieldType.TYPE_15: 0.90,
            ShieldType.TYPE_19: 0.95
        }
        
        # Weapon damage multipliers vs different shield types
        self.weapon_vs_shield_modifiers = {
            DamageType.PHASER: {
                ShieldType.TYPE_1: 0.8,
                ShieldType.TYPE_5: 0.9,
                ShieldType.TYPE_10: 0.95,
                ShieldType.TYPE_19: 0.98
            },
            DamageType.TORPEDO: {
                ShieldType.TYPE_1: 1.2,
                ShieldType.TYPE_5: 1.1,
                ShieldType.TYPE_10: 1.0,
                ShieldType.TYPE_19: 0.9
            },
            DamageType.ION_CANNON: {
                ShieldType.TYPE_1: 1.5,
                ShieldType.TYPE_5: 1.3,
                ShieldType.TYPE_10: 1.1,
                ShieldType.TYPE_19: 0.95
            }
        }
        
        # Critical hit probabilities
        self.critical_hit_base_chance = 0.1  # 10% base chance
        self.critical_hit_multiplier = 2.5
        
        # System damage probabilities
        self.system_damage_chance = 0.15  # 15% chance per hit
        self.system_destruction_threshold = 80.0  # 80% damage destroys system
        
        # Self-destruct parameters
        self.self_destruct_countdown_ticks = 10
        self.self_destruct_base_damage = 500.0
        self.self_destruct_base_radius = 50000.0  # 50k distance units
    
    def calculate_weapon_effectiveness(self, weapon_type: DamageType, 
                                     weapon_strength: float, ship_class_modifier: float,
                                     range_to_target: float, optimal_range: float) -> float:
        """Calculate weapon effectiveness based on multiple factors"""
        try:
            # Base effectiveness from weapon strength
            base_effectiveness = weapon_strength / 100.0
            
            # Ship class modifier (different ships have different weapon systems)
            class_effectiveness = base_effectiveness * ship_class_modifier
            
            # Range effectiveness (weapons are less effective at longer ranges)
            if range_to_target <= optimal_range:
                range_effectiveness = 1.0
            else:
                # Falloff after optimal range
                range_ratio = range_to_target / optimal_range
                range_effectiveness = max(0.1, 1.0 / (range_ratio ** 0.5))
            
            # Final effectiveness
            final_effectiveness = class_effectiveness * range_effectiveness
            
            return max(0.0, min(2.0, final_effectiveness))  # Cap between 0 and 200%
            
        except Exception as e:
            logger.error(f"Error calculating weapon effectiveness: {e}")
            return 0.5  # Default effectiveness
    
    def calculate_shield_absorption(self, shield_type: ShieldType, shield_charge: int,
                                  damage_type: DamageType, incoming_damage: float) -> Tuple[float, float]:
        """Calculate how much damage shields absorb vs passes through"""
        try:
            if shield_charge <= 0:
                return 0.0, incoming_damage  # No shields = no absorption
            
            # Base shield effectiveness
            base_effectiveness = self.shield_effectiveness.get(shield_type, 0.0)
            
            # Shield charge affects effectiveness (0-100%)
            charge_modifier = shield_charge / 100.0
            actual_effectiveness = base_effectiveness * charge_modifier
            
            # Weapon vs shield type modifier
            weapon_modifier = self.weapon_vs_shield_modifiers.get(damage_type, {}).get(
                shield_type, 1.0
            )
            
            # Calculate absorption
            absorption_rate = actual_effectiveness * weapon_modifier
            absorbed_damage = incoming_damage * absorption_rate
            penetrating_damage = incoming_damage - absorbed_damage
            
            return absorbed_damage, max(0.0, penetrating_damage)
            
        except Exception as e:
            logger.error(f"Error calculating shield absorption: {e}")
            return 0.0, incoming_damage
    
    def apply_critical_hit_effects(self, base_damage: float, target_ship_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Apply critical hit effects and return modified damage and effects"""
        try:
            effects = []
            final_damage = base_damage
            
            # Check for critical hit
            critical_chance = self.critical_hit_base_chance
            
            # Tactical system damage increases critical hit chance
            if target_ship_data.get("tactical_damage", 0) > 50:
                critical_chance *= 1.5
            
            if random.random() < critical_chance:
                # Critical hit!
                final_damage *= self.critical_hit_multiplier
                effects.append("Critical hit!")
                
                # Additional critical effects
                crit_roll = random.random()
                if crit_roll < 0.1:  # 10% chance
                    effects.append("Fire control systems damaged!")
                elif crit_roll < 0.2:  # 10% chance
                    effects.append("Helm control damaged!")
                elif crit_roll < 0.3:  # 10% chance
                    effects.append("Tactical systems damaged!")
                elif crit_roll < 0.4:  # 10% chance
                    effects.append("Engine systems damaged!")
            
            return final_damage, effects
            
        except Exception as e:
            logger.error(f"Error applying critical hit effects: {e}")
            return base_damage, []
    
    def calculate_system_damage(self, hull_damage: float, current_damage: float) -> Dict[SystemDamage, float]:
        """Calculate damage to specific ship systems"""
        try:
            system_damage = {}
            
            # Only calculate system damage if significant hull damage occurred
            if hull_damage < 10.0:
                return system_damage
            
            # Higher hull damage increases chance of system damage
            damage_factor = min(1.0, hull_damage / 100.0)
            system_chance = self.system_damage_chance * damage_factor
            
            # Check each system for damage
            systems_to_check = [
                SystemDamage.HELM,
                SystemDamage.TACTICAL,
                SystemDamage.FIRE_CONTROL,
                SystemDamage.ENGINES,
                SystemDamage.PHASERS,
                SystemDamage.SHIELDS
            ]
            
            for system in systems_to_check:
                if random.random() < system_chance:
                    # System takes damage
                    damage_amount = random.uniform(5.0, 25.0)
                    system_damage[system] = damage_amount
            
            return system_damage
            
        except Exception as e:
            logger.error(f"Error calculating system damage: {e}")
            return {}
    
    def process_combat_damage(self, attacker_data: Dict[str, Any], 
                            defender_data: Dict[str, Any],
                            weapon_type: DamageType, weapon_damage: float,
                            combat_range: float) -> DamageReport:
        """Process complete combat damage calculation"""
        try:
            # Get defender shield information
            shield_type = ShieldType(defender_data.get("shield_type", 0))
            shield_charge = defender_data.get("shield_charge", 0)
            current_hull_damage = defender_data.get("damage", 0.0)
            
            # Calculate weapon effectiveness
            attacker_class_modifier = attacker_data.get("damage_factor", 100) / 100.0
            optimal_range = attacker_data.get("optimal_range", 100000.0)
            
            weapon_effectiveness = self.calculate_weapon_effectiveness(
                weapon_type, weapon_damage, attacker_class_modifier, 
                combat_range, optimal_range
            )
            
            # Apply weapon effectiveness to base damage
            effective_damage = weapon_damage * weapon_effectiveness
            
            # Apply critical hit effects
            final_damage, critical_effects = self.apply_critical_hit_effects(
                effective_damage, defender_data
            )
            
            # Calculate shield absorption
            shield_absorbed, hull_damage = self.calculate_shield_absorption(
                shield_type, shield_charge, weapon_type, final_damage
            )
            
            # Calculate system damage
            system_damage = self.calculate_system_damage(hull_damage, current_hull_damage)
            
            # Check for system destruction
            systems_destroyed = []
            for system, damage in system_damage.items():
                if damage > self.system_destruction_threshold:
                    systems_destroyed.append(system)
            
            # Check if ship is destroyed
            total_hull_damage = current_hull_damage + hull_damage
            ship_destroyed = total_hull_damage >= 100.0
            
            # Calculate shield effectiveness for reporting
            shield_effectiveness = (shield_absorbed / final_damage) if final_damage > 0 else 0.0
            
            return DamageReport(
                total_damage=final_damage,
                shield_damage=shield_absorbed,
                hull_damage=hull_damage,
                system_damage=system_damage,
                critical_hits=critical_effects,
                systems_destroyed=systems_destroyed,
                ship_destroyed=ship_destroyed,
                damage_type=weapon_type,
                weapon_effectiveness=weapon_effectiveness,
                shield_effectiveness=shield_effectiveness
            )
            
        except Exception as e:
            logger.error(f"Error processing combat damage: {e}")
            return DamageReport(
                total_damage=0.0,
                shield_damage=0.0,
                hull_damage=0.0,
                system_damage={},
                critical_hits=[],
                systems_destroyed=[],
                ship_destroyed=False,
                damage_type=weapon_type,
                weapon_effectiveness=0.0,
                shield_effectiveness=0.0
            )


class SelfDestructSystem:
    """Self-destruct system implementation"""
    
    def __init__(self):
        self.active_destructs: Dict[str, SelfDestructState] = {}
        self.base_countdown = 10  # ticks
        self.abort_time_limit = 5  # can abort within first 5 ticks
    
    def initiate_self_destruct(self, ship_id: str, initiated_by: str, 
                             ship_class_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate self-destruct sequence"""
        try:
            if ship_id in self.active_destructs:
                return {
                    "success": False,
                    "message": "Self-destruct already in progress"
                }
            
            # Calculate blast parameters based on ship class
            base_damage = 200.0 + (ship_class_data.get("max_points", 0) / 10.0)
            base_radius = 30000.0 + (ship_class_data.get("max_tons", 0) * 2.0)
            
            # Generate abort code
            abort_code = f"{random.randint(1000, 9999)}"
            
            # Create self-destruct state
            destruct_state = SelfDestructState(
                ship_id=ship_id,
                countdown=self.base_countdown,
                initiated_by=initiated_by,
                can_abort=True,
                abort_code=abort_code,
                blast_radius=base_radius,
                blast_damage=base_damage
            )
            
            self.active_destructs[ship_id] = destruct_state
            
            return {
                "success": True,
                "message": f"Self-destruct initiated. {self.base_countdown} ticks to detonation.",
                "countdown": self.base_countdown,
                "abort_code": abort_code,
                "can_abort": True
            }
            
        except Exception as e:
            logger.error(f"Error initiating self-destruct: {e}")
            return {
                "success": False,
                "message": f"Self-destruct error: {str(e)}"
            }
    
    def abort_self_destruct(self, ship_id: str, abort_code: str) -> Dict[str, Any]:
        """Abort self-destruct sequence"""
        try:
            if ship_id not in self.active_destructs:
                return {
                    "success": False,
                    "message": "No self-destruct in progress"
                }
            
            destruct_state = self.active_destructs[ship_id]
            
            if not destruct_state.can_abort:
                return {
                    "success": False,
                    "message": "Self-destruct cannot be aborted - too late!"
                }
            
            if abort_code != destruct_state.abort_code:
                return {
                    "success": False,
                    "message": "Invalid abort code"
                }
            
            # Abort successful
            del self.active_destructs[ship_id]
            
            return {
                "success": True,
                "message": "Self-destruct aborted"
            }
            
        except Exception as e:
            logger.error(f"Error aborting self-destruct: {e}")
            return {
                "success": False,
                "message": f"Abort error: {str(e)}"
            }
    
    def process_self_destruct_tick(self) -> List[Dict[str, Any]]:
        """Process self-destruct countdowns for all ships"""
        try:
            explosions = []
            ships_to_remove = []
            
            for ship_id, destruct_state in self.active_destructs.items():
                # Countdown
                destruct_state.countdown -= 1
                
                # Check if abort window has closed
                if destruct_state.countdown <= self.abort_time_limit:
                    destruct_state.can_abort = False
                
                # Check for detonation
                if destruct_state.countdown <= 0:
                    # BOOM!
                    explosions.append({
                        "ship_id": ship_id,
                        "blast_damage": destruct_state.blast_damage,
                        "blast_radius": destruct_state.blast_radius,
                        "initiated_by": destruct_state.initiated_by
                    })
                    ships_to_remove.append(ship_id)
            
            # Remove exploded ships
            for ship_id in ships_to_remove:
                del self.active_destructs[ship_id]
            
            return explosions
            
        except Exception as e:
            logger.error(f"Error processing self-destruct ticks: {e}")
            return []
    
    def get_self_destruct_status(self, ship_id: str) -> Optional[Dict[str, Any]]:
        """Get current self-destruct status for a ship"""
        try:
            if ship_id not in self.active_destructs:
                return None
            
            destruct_state = self.active_destructs[ship_id]
            
            return {
                "countdown": destruct_state.countdown,
                "can_abort": destruct_state.can_abort,
                "initiated_by": destruct_state.initiated_by,
                "blast_radius": destruct_state.blast_radius,
                "blast_damage": destruct_state.blast_damage
            }
            
        except Exception as e:
            logger.error(f"Error getting self-destruct status: {e}")
            return None


class BattleManager:
    """Manages active battles between ships"""
    
    def __init__(self):
        self.active_battles: Dict[str, BattleState] = {}
        self.combat_mechanics = AdvancedCombatMechanics()
        self.self_destruct = SelfDestructSystem()
        
        # Battle parameters
        self.max_battle_range = 200000.0  # Maximum range for combat
        self.battle_timeout = 50  # ticks of inactivity before battle ends
    
    def start_battle(self, attacker_id: str, defender_id: str, 
                    initial_range: float) -> Dict[str, Any]:
        """Start a battle between two ships"""
        try:
            battle_key = f"{attacker_id}_{defender_id}"
            
            if battle_key in self.active_battles:
                return {
                    "success": False,
                    "message": "Battle already in progress"
                }
            
            if initial_range > self.max_battle_range:
                return {
                    "success": False,
                    "message": "Target out of combat range"
                }
            
            # Create battle state
            battle_state = BattleState(
                attacker_id=attacker_id,
                defender_id=defender_id,
                battle_start=datetime.utcnow(),
                battle_duration=0,
                attacker_damage_dealt=0.0,
                defender_damage_dealt=0.0,
                battle_range=initial_range,
                last_action=datetime.utcnow(),
                is_active=True
            )
            
            self.active_battles[battle_key] = battle_state
            
            return {
                "success": True,
                "message": f"Battle commenced between {attacker_id} and {defender_id}",
                "battle_key": battle_key,
                "range": initial_range
            }
            
        except Exception as e:
            logger.error(f"Error starting battle: {e}")
            return {
                "success": False,
                "message": f"Battle start error: {str(e)}"
            }
    
    def process_battle_action(self, battle_key: str, attacker_data: Dict[str, Any],
                            defender_data: Dict[str, Any], weapon_type: DamageType,
                            weapon_damage: float) -> Dict[str, Any]:
        """Process a battle action (attack)"""
        try:
            if battle_key not in self.active_battles:
                return {
                    "success": False,
                    "message": "No active battle found"
                }
            
            battle_state = self.active_battles[battle_key]
            
            # Process damage
            damage_report = self.combat_mechanics.process_combat_damage(
                attacker_data, defender_data, weapon_type, weapon_damage,
                battle_state.battle_range
            )
            
            # Update battle state
            battle_state.attacker_damage_dealt += damage_report.total_damage
            battle_state.last_action = datetime.utcnow()
            battle_state.battle_duration += 1
            
            # Check if battle should end
            if damage_report.ship_destroyed:
                battle_state.is_active = False
                del self.active_battles[battle_key]
            
            return {
                "success": True,
                "damage_report": damage_report,
                "battle_continues": battle_state.is_active,
                "battle_duration": battle_state.battle_duration
            }
            
        except Exception as e:
            logger.error(f"Error processing battle action: {e}")
            return {
                "success": False,
                "message": f"Battle action error: {str(e)}"
            }
    
    def end_battle(self, battle_key: str, reason: str = "manual") -> Dict[str, Any]:
        """End an active battle"""
        try:
            if battle_key not in self.active_battles:
                return {
                    "success": False,
                    "message": "No active battle found"
                }
            
            battle_state = self.active_battles[battle_key]
            battle_duration = (datetime.utcnow() - battle_state.battle_start).total_seconds()
            
            battle_summary = {
                "attacker_id": battle_state.attacker_id,
                "defender_id": battle_state.defender_id,
                "duration_seconds": battle_duration,
                "duration_ticks": battle_state.battle_duration,
                "attacker_damage_dealt": battle_state.attacker_damage_dealt,
                "defender_damage_dealt": battle_state.defender_damage_dealt,
                "end_reason": reason
            }
            
            del self.active_battles[battle_key]
            
            return {
                "success": True,
                "message": f"Battle ended: {reason}",
                "battle_summary": battle_summary
            }
            
        except Exception as e:
            logger.error(f"Error ending battle: {e}")
            return {
                "success": False,
                "message": f"Battle end error: {str(e)}"
            }
    
    def process_battle_tick(self) -> List[Dict[str, Any]]:
        """Process all active battles for one tick"""
        try:
            results = []
            battles_to_end = []
            
            current_time = datetime.utcnow()
            
            for battle_key, battle_state in self.active_battles.items():
                # Check for timeout
                time_since_action = (current_time - battle_state.last_action).total_seconds()
                if time_since_action > (self.battle_timeout * 2):  # Assuming 2 seconds per tick
                    battles_to_end.append((battle_key, "timeout"))
                    continue
                
                # Update battle duration
                battle_state.battle_duration += 1
                
                results.append({
                    "battle_key": battle_key,
                    "attacker_id": battle_state.attacker_id,
                    "defender_id": battle_state.defender_id,
                    "duration": battle_state.battle_duration,
                    "range": battle_state.battle_range
                })
            
            # End timed out battles
            for battle_key, reason in battles_to_end:
                self.end_battle(battle_key, reason)
            
            # Process self-destruct ticks
            explosions = self.self_destruct.process_self_destruct_tick()
            
            return results + [{"explosions": explosions}] if explosions else results
            
        except Exception as e:
            logger.error(f"Error processing battle tick: {e}")
            return []
    
    def get_battle_status(self, ship_id: str) -> Optional[Dict[str, Any]]:
        """Get battle status for a ship"""
        try:
            for battle_key, battle_state in self.active_battles.items():
                if ship_id in [battle_state.attacker_id, battle_state.defender_id]:
                    return {
                        "battle_key": battle_key,
                        "is_attacker": ship_id == battle_state.attacker_id,
                        "opponent_id": battle_state.defender_id if ship_id == battle_state.attacker_id else battle_state.attacker_id,
                        "battle_range": battle_state.battle_range,
                        "duration": battle_state.battle_duration,
                        "damage_dealt": battle_state.attacker_damage_dealt if ship_id == battle_state.attacker_id else battle_state.defender_damage_dealt
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting battle status: {e}")
            return None
