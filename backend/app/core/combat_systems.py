"""
Galactic Empire - Combat Systems

This module implements all combat systems including phasers, torpedoes,
missiles, ion cannons, decoys, jammers, and mine laying systems.
Based on the original game's combat functions.
"""

import logging
import math
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .coordinates import Coordinate, distance, bearing

logger = logging.getLogger(__name__)


class WeaponType(Enum):
    """Weapon type enumeration"""
    PHASER = "phaser"
    HYPER_PHASER = "hyper_phaser"
    TORPEDO = "torpedo"
    MISSILE = "missile"
    ION_CANNON = "ion_cannon"
    DECOY = "decoy"
    JAMMER = "jammer"
    MINE = "mine"


class TargetType(Enum):
    """Target type enumeration"""
    SHIP = "ship"
    PLANET = "planet"
    MINE = "mine"
    COORDINATES = "coordinates"


@dataclass
class WeaponStatus:
    """Weapon system status"""
    weapon_type: WeaponType
    available: bool
    energy_level: float
    ammunition: int
    cooldown_time: int
    damage_modifier: float
    range_modifier: float


@dataclass
class CombatTarget:
    """Combat target information"""
    target_id: str
    target_type: TargetType
    position: Coordinate
    distance: float
    bearing: float
    shield_status: bool
    cloak_status: bool
    size_factor: float  # Affects hit probability


@dataclass
class CombatResult:
    """Result of combat action"""
    success: bool
    damage_dealt: float
    energy_consumed: int
    ammunition_used: int
    hit: bool
    critical_hit: bool
    target_destroyed: bool
    message: str
    effects: List[str]


class CombatCalculations:
    """Combat calculation utilities"""
    
    @staticmethod
    def calculate_hit_probability(weapon_range: float, target_distance: float,
                                weapon_accuracy: float, target_size: float,
                                fire_control_damage: bool) -> float:
        """Calculate probability of hitting target"""
        # Base hit probability
        base_probability = 0.8
        
        # Range factor
        if target_distance > weapon_range:
            return 0.0  # Out of range
        
        range_factor = 1.0 - (target_distance / weapon_range) * 0.3
        
        # Accuracy factor
        accuracy_factor = weapon_accuracy / 100.0
        
        # Target size factor (larger targets easier to hit)
        size_factor = min(1.0, target_size / 100.0)
        
        # Fire control damage penalty
        fire_control_factor = 0.5 if fire_control_damage else 1.0
        
        # Calculate final probability
        hit_probability = (base_probability * range_factor * 
                          accuracy_factor * size_factor * fire_control_factor)
        
        return max(0.0, min(1.0, hit_probability))
    
    @staticmethod
    def calculate_damage(base_damage: float, weapon_strength: float,
                        target_shields: int, shield_type: int,
                        critical_hit: bool) -> Tuple[float, float]:
        """Calculate damage to shields and hull"""
        # Base weapon damage
        weapon_damage = base_damage * (weapon_strength / 100.0)
        
        # Critical hit multiplier
        if critical_hit:
            weapon_damage *= 2.0
        
        # Shield absorption
        shield_absorption = 0.0
        if target_shields > 0:
            # Shield effectiveness based on type and charge
            shield_effectiveness = min(1.0, target_shields / 100.0)
            shield_type_modifier = 1.0 + (shield_type * 0.05)  # Better shields absorb more
            shield_absorption = weapon_damage * shield_effectiveness * shield_type_modifier
            shield_absorption = min(shield_absorption, weapon_damage)
        
        # Remaining damage goes to hull
        hull_damage = max(0.0, weapon_damage - shield_absorption)
        
        return shield_absorption, hull_damage
    
    @staticmethod
    def is_critical_hit() -> bool:
        """Determine if attack is a critical hit (10% chance)"""
        return random.random() < 0.1


class PhaserSystem:
    """Phaser weapon system"""
    
    def __init__(self):
        self.base_damage = 50.0
        self.max_range = 100000.0  # Standard phaser range
        self.energy_per_shot = 100
        self.accuracy = 85.0
        
        # Hyper-phaser specifications
        self.hyper_base_damage = 100.0
        self.hyper_max_range = 150000.0
        self.hyper_energy_per_shot = 500
        self.hyper_accuracy = 90.0
        self.hyper_cooldown = 10  # ticks
    
    def fire_phasers(self, weapon_status: WeaponStatus, target: CombatTarget,
                    ship_energy: float, fire_control_damage: bool,
                    hyper_phasers: bool = False) -> CombatResult:
        """Fire phaser weapons"""
        result = CombatResult(
            success=False, damage_dealt=0.0, energy_consumed=0,
            ammunition_used=0, hit=False, critical_hit=False,
            target_destroyed=False, message="", effects=[]
        )
        
        try:
            # Select phaser type
            if hyper_phasers:
                base_damage = self.hyper_base_damage
                max_range = self.hyper_max_range
                energy_needed = self.hyper_energy_per_shot
                accuracy = self.hyper_accuracy
                weapon_name = "Hyper-phasers"
            else:
                base_damage = self.base_damage
                max_range = self.max_range
                energy_needed = self.energy_per_shot
                accuracy = self.accuracy
                weapon_name = "Phasers"
            
            # Check weapon availability
            if not weapon_status.available:
                result.message = f"{weapon_name} offline"
                return result
            
            # Check energy requirements
            if ship_energy < energy_needed:
                result.message = f"Insufficient energy for {weapon_name.lower()}"
                return result
            
            # Check range
            if target.distance > max_range:
                result.message = f"Target out of {weapon_name.lower()} range"
                return result
            
            # Check if target is cloaked
            if target.cloak_status:
                result.message = "Cannot target cloaked vessel"
                return result
            
            # Calculate hit probability
            hit_probability = CombatCalculations.calculate_hit_probability(
                max_range, target.distance, accuracy, target.size_factor, fire_control_damage
            )
            
            # Determine if shot hits
            hit = random.random() < hit_probability
            critical_hit = CombatCalculations.is_critical_hit() if hit else False
            
            # Consume energy
            result.energy_consumed = energy_needed
            
            if hit:
                # Calculate damage (this would need target shield info)
                damage = base_damage * (weapon_status.energy_level / 100.0)
                if critical_hit:
                    damage *= 2.0
                    result.effects.append("Critical hit!")
                
                result.hit = True
                result.critical_hit = critical_hit
                result.damage_dealt = damage
                result.success = True
                result.message = f"{weapon_name} hit for {damage:.1f} damage"
                
                # Check for target destruction (would need target status)
                if damage > 200:  # Arbitrary destruction threshold
                    result.target_destroyed = True
                    result.effects.append("Target destroyed!")
            else:
                result.success = True
                result.message = f"{weapon_name} missed target"
            
            return result
            
        except Exception as e:
            logger.error(f"Error firing phasers: {e}")
            result.message = f"Phaser system error: {str(e)}"
            return result


class TorpedoSystem:
    """Torpedo weapon system"""
    
    def __init__(self):
        self.base_damage = 150.0
        self.max_range = 200000.0
        self.energy_per_shot = 200
        self.accuracy = 75.0
        self.travel_time = 5  # ticks to reach target
    
    def fire_torpedo(self, weapon_status: WeaponStatus, target: CombatTarget,
                    ship_energy: float, torpedo_count: int,
                    fire_control_damage: bool) -> CombatResult:
        """Fire torpedo at target"""
        result = CombatResult(
            success=False, damage_dealt=0.0, energy_consumed=0,
            ammunition_used=0, hit=False, critical_hit=False,
            target_destroyed=False, message="", effects=[]
        )
        
        try:
            # Check weapon availability
            if not weapon_status.available:
                result.message = "Torpedo system offline"
                return result
            
            # Check ammunition
            if torpedo_count <= 0:
                result.message = "No torpedoes available"
                return result
            
            # Check energy requirements
            energy_needed = self.energy_per_shot
            if ship_energy < energy_needed:
                result.message = "Insufficient energy for torpedo launch"
                return result
            
            # Check range
            if target.distance > self.max_range:
                result.message = "Target out of torpedo range"
                return result
            
            # Torpedoes can track cloaked targets better than phasers
            cloak_penalty = 0.5 if target.cloak_status else 1.0
            
            # Calculate hit probability
            hit_probability = CombatCalculations.calculate_hit_probability(
                self.max_range, target.distance, self.accuracy * cloak_penalty,
                target.size_factor, fire_control_damage
            )
            
            # Consume resources
            result.energy_consumed = energy_needed
            result.ammunition_used = 1
            
            # Torpedo always launches successfully
            result.success = True
            result.message = "Torpedo launched"
            result.effects.append(f"Torpedo will reach target in {self.travel_time} ticks")
            
            # For immediate resolution (simplified):
            hit = random.random() < hit_probability
            if hit:
                critical_hit = CombatCalculations.is_critical_hit()
                damage = self.base_damage * (weapon_status.energy_level / 100.0)
                if critical_hit:
                    damage *= 2.0
                    result.effects.append("Critical hit!")
                
                result.hit = True
                result.critical_hit = critical_hit
                result.damage_dealt = damage
                result.message = f"Torpedo hit for {damage:.1f} damage"
                
                if damage > 300:
                    result.target_destroyed = True
                    result.effects.append("Target destroyed!")
            else:
                result.message = "Torpedo missed target"
            
            return result
            
        except Exception as e:
            logger.error(f"Error firing torpedo: {e}")
            result.message = f"Torpedo system error: {str(e)}"
            return result


class MissileSystem:
    """Missile weapon system"""
    
    def __init__(self):
        self.base_damage = 100.0
        self.max_range = 150000.0
        self.energy_per_shot = 150
        self.accuracy = 80.0
        self.tracking_ability = 0.9  # Better tracking than torpedoes
    
    def fire_missile(self, weapon_status: WeaponStatus, target: CombatTarget,
                    ship_energy: float, missile_count: int,
                    fire_control_damage: bool) -> CombatResult:
        """Fire missile at target"""
        result = CombatResult(
            success=False, damage_dealt=0.0, energy_consumed=0,
            ammunition_used=0, hit=False, critical_hit=False,
            target_destroyed=False, message="", effects=[]
        )
        
        try:
            # Check weapon availability
            if not weapon_status.available:
                result.message = "Missile system offline"
                return result
            
            # Check ammunition
            if missile_count <= 0:
                result.message = "No missiles available"
                return result
            
            # Check energy requirements
            energy_needed = self.energy_per_shot
            if ship_energy < energy_needed:
                result.message = "Insufficient energy for missile launch"
                return result
            
            # Check range
            if target.distance > self.max_range:
                result.message = "Target out of missile range"
                return result
            
            # Missiles have good tracking vs cloaked targets
            cloak_penalty = 0.8 if target.cloak_status else 1.0
            
            # Calculate hit probability with tracking bonus
            base_hit_probability = CombatCalculations.calculate_hit_probability(
                self.max_range, target.distance, self.accuracy * cloak_penalty,
                target.size_factor, fire_control_damage
            )
            
            # Apply tracking bonus
            hit_probability = min(0.95, base_hit_probability * self.tracking_ability)
            
            # Consume resources
            result.energy_consumed = energy_needed
            result.ammunition_used = 1
            result.success = True
            
            # Determine hit
            hit = random.random() < hit_probability
            if hit:
                critical_hit = CombatCalculations.is_critical_hit()
                damage = self.base_damage * (weapon_status.energy_level / 100.0)
                if critical_hit:
                    damage *= 2.0
                    result.effects.append("Critical hit!")
                
                result.hit = True
                result.critical_hit = critical_hit
                result.damage_dealt = damage
                result.message = f"Missile hit for {damage:.1f} damage"
                
                if damage > 250:
                    result.target_destroyed = True
                    result.effects.append("Target destroyed!")
            else:
                result.message = "Missile missed target"
            
            return result
            
        except Exception as e:
            logger.error(f"Error firing missile: {e}")
            result.message = f"Missile system error: {str(e)}"
            return result


class CountermeasureSystems:
    """Decoy and jammer systems"""
    
    def __init__(self):
        self.decoy_energy_cost = 300
        self.jammer_energy_cost = 200
        self.jammer_effectiveness = 0.7  # Reduces incoming weapon accuracy
    
    def launch_decoy(self, ship_energy: float, decoy_count: int) -> CombatResult:
        """Launch decoy countermeasure"""
        result = CombatResult(
            success=False, damage_dealt=0.0, energy_consumed=0,
            ammunition_used=0, hit=False, critical_hit=False,
            target_destroyed=False, message="", effects=[]
        )
        
        try:
            # Check ammunition
            if decoy_count <= 0:
                result.message = "No decoys available"
                return result
            
            # Check energy
            if ship_energy < self.decoy_energy_cost:
                result.message = "Insufficient energy for decoy launch"
                return result
            
            # Launch decoy
            result.success = True
            result.energy_consumed = self.decoy_energy_cost
            result.ammunition_used = 1
            result.message = "Decoy launched"
            result.effects.append("Decoy will confuse incoming weapons for 30 seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"Error launching decoy: {e}")
            result.message = f"Decoy system error: {str(e)}"
            return result
    
    def activate_jammer(self, ship_energy: float, jammer_active: bool) -> CombatResult:
        """Activate/deactivate jammer system"""
        result = CombatResult(
            success=False, damage_dealt=0.0, energy_consumed=0,
            ammunition_used=0, hit=False, critical_hit=False,
            target_destroyed=False, message="", effects=[]
        )
        
        try:
            if not jammer_active:
                # Activate jammer
                if ship_energy < self.jammer_energy_cost:
                    result.message = "Insufficient energy for jammer activation"
                    return result
                
                result.success = True
                result.energy_consumed = self.jammer_energy_cost
                result.message = "Jammer activated"
                result.effects.append("Jammer reduces enemy weapon accuracy")
            else:
                # Deactivate jammer
                result.success = True
                result.message = "Jammer deactivated"
                result.effects.append("Jammer systems offline")
            
            return result
            
        except Exception as e:
            logger.error(f"Error with jammer: {e}")
            result.message = f"Jammer system error: {str(e)}"
            return result


class MineSystem:
    """Mine laying and detection system"""
    
    def __init__(self):
        self.mine_energy_cost = 400
        self.mine_damage = 200.0
        self.mine_detection_range = 50000.0
        self.mine_trigger_range = 10000.0
    
    def lay_mine(self, position: Coordinate, ship_energy: float, 
                mine_count: int) -> CombatResult:
        """Lay mine at current position"""
        result = CombatResult(
            success=False, damage_dealt=0.0, energy_consumed=0,
            ammunition_used=0, hit=False, critical_hit=False,
            target_destroyed=False, message="", effects=[]
        )
        
        try:
            # Check ammunition
            if mine_count <= 0:
                result.message = "No mines available"
                return result
            
            # Check energy
            if ship_energy < self.mine_energy_cost:
                result.message = "Insufficient energy to lay mine"
                return result
            
            # Lay mine
            result.success = True
            result.energy_consumed = self.mine_energy_cost
            result.ammunition_used = 1
            result.message = f"Mine laid at coordinates ({position.x:.0f}, {position.y:.0f})"
            result.effects.append("Mine is now active and armed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error laying mine: {e}")
            result.message = f"Mine system error: {str(e)}"
            return result
    
    def detect_mines(self, position: Coordinate, scan_range: float) -> List[Dict[str, Any]]:
        """Detect mines in range"""
        # This would query the database for mines in range
        # For now, return empty list
        return []


class CombatController:
    """Main combat system controller"""
    
    def __init__(self):
        self.phaser_system = PhaserSystem()
        self.torpedo_system = TorpedoSystem()
        self.missile_system = MissileSystem()
        self.countermeasures = CountermeasureSystems()
        self.mine_system = MineSystem()
    
    def execute_combat_action(self, action_type: str, weapon_status: WeaponStatus,
                            target: Optional[CombatTarget], ship_status: Dict[str, Any],
                            **kwargs) -> CombatResult:
        """Execute combat action"""
        try:
            if action_type == "fire_phasers":
                return self.phaser_system.fire_phasers(
                    weapon_status, target, ship_status.get("energy", 0),
                    ship_status.get("fire_control_damage", False),
                    kwargs.get("hyper_phasers", False)
                )
            
            elif action_type == "fire_torpedo":
                return self.torpedo_system.fire_torpedo(
                    weapon_status, target, ship_status.get("energy", 0),
                    ship_status.get("torpedo_count", 0),
                    ship_status.get("fire_control_damage", False)
                )
            
            elif action_type == "fire_missile":
                return self.missile_system.fire_missile(
                    weapon_status, target, ship_status.get("energy", 0),
                    ship_status.get("missile_count", 0),
                    ship_status.get("fire_control_damage", False)
                )
            
            elif action_type == "launch_decoy":
                return self.countermeasures.launch_decoy(
                    ship_status.get("energy", 0),
                    ship_status.get("decoy_count", 0)
                )
            
            elif action_type == "activate_jammer":
                return self.countermeasures.activate_jammer(
                    ship_status.get("energy", 0),
                    ship_status.get("jammer_active", False)
                )
            
            elif action_type == "lay_mine":
                return self.mine_system.lay_mine(
                    kwargs.get("position"),
                    ship_status.get("energy", 0),
                    ship_status.get("mine_count", 0)
                )
            
            else:
                result = CombatResult(
                    success=False, damage_dealt=0.0, energy_consumed=0,
                    ammunition_used=0, hit=False, critical_hit=False,
                    target_destroyed=False, message=f"Unknown combat action: {action_type}",
                    effects=[]
                )
                return result
                
        except Exception as e:
            logger.error(f"Error executing combat action {action_type}: {e}")
            result = CombatResult(
                success=False, damage_dealt=0.0, energy_consumed=0,
                ammunition_used=0, hit=False, critical_hit=False,
                target_destroyed=False, message=f"Combat system error: {str(e)}",
                effects=[]
            )
            return result
