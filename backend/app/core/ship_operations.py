"""
Galactic Empire - Ship Operations System

This module implements all ship operations including navigation commands,
shield management, cloaking, energy management, and cargo systems.
Based on the original game's ship operation functions.
"""

import logging
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .coordinates import Coordinate, distance, bearing
from .movement import MovementState, MovementPhysics, ShipMovement

logger = logging.getLogger(__name__)


class ShieldStatus(Enum):
    """Shield status enumeration"""
    DOWN = 0
    UP = 1
    CHARGING = 2
    DAMAGED = 3


class CloakStatus(Enum):
    """Cloaking status enumeration"""
    DOWN = 0
    UP = -1
    CHARGING = 1  # Positive values indicate charging time


class EnergySystem(Enum):
    """Ship energy systems"""
    SHIELDS = "shields"
    PHASERS = "phasers"
    TORPEDOES = "torpedoes"
    MISSILES = "missiles"
    ENGINES = "engines"
    CLOAKING = "cloaking"
    LIFE_SUPPORT = "life_support"


@dataclass
class ShipStatus:
    """Complete ship status information"""
    ship_id: str
    energy: float
    max_energy: float
    damage: float
    shield_status: ShieldStatus
    shield_charge: int
    shield_type: int
    cloak_status: CloakStatus
    cloak_time: int
    phaser_strength: float
    phaser_type: int
    tactical_damage: int
    helm_damage: int
    fire_control_damage: bool
    repair_in_progress: bool
    hostile: bool
    jammer_active: bool
    destruct_countdown: int


@dataclass
class NavigationCommand:
    """Navigation command structure"""
    command_type: str  # "warp", "impulse", "rotate", "stop"
    target_speed: Optional[float] = None
    target_heading: Optional[float] = None
    warp_factor: Optional[int] = None
    impulse_power: Optional[int] = None


class ShipOperations:
    """Main ship operations controller"""
    
    def __init__(self):
        self.movement_physics = MovementPhysics()
        self.ship_movement = ShipMovement(self.movement_physics)
        
        # Energy consumption rates (per tick)
        self.energy_consumption = {
            EnergySystem.SHIELDS: 10,
            EnergySystem.PHASERS: 5,
            EnergySystem.TORPEDOES: 20,
            EnergySystem.MISSILES: 15,
            EnergySystem.ENGINES: 1,
            EnergySystem.CLOAKING: 50,
            EnergySystem.LIFE_SUPPORT: 2
        }
        
        # Maximum energy levels
        self.max_energy_base = 50000
        self.energy_recharge_rate = 100  # per tick
    
    def execute_navigation_command(self, ship_status: ShipStatus, 
                                 movement_state: MovementState,
                                 command: NavigationCommand) -> Tuple[MovementState, Dict[str, Any]]:
        """
        Execute navigation command - equivalent to navigation functions in original
        """
        result = {"success": False, "message": "", "energy_consumed": 0}
        
        # Check if helm is damaged
        if ship_status.helm_damage > 0:
            damage_factor = ship_status.helm_damage / 100.0
            if damage_factor > 0.5:
                result["message"] = "Helm control severely damaged - navigation impaired"
                return movement_state, result
        
        try:
            if command.command_type == "warp":
                if command.warp_factor is None or command.warp_factor < 1:
                    result["message"] = "Invalid warp factor"
                    return movement_state, result
                
                # Check energy requirements
                energy_needed = command.warp_factor * 100
                if ship_status.energy < energy_needed:
                    result["message"] = "Insufficient energy for warp"
                    return movement_state, result
                
                # Execute warp
                new_state = self.ship_movement.set_warp(movement_state, command.warp_factor)
                result["success"] = True
                result["message"] = f"Warp {command.warp_factor} engaged"
                result["energy_consumed"] = energy_needed
                
            elif command.command_type == "impulse":
                if command.impulse_power is None or command.impulse_power < 1:
                    result["message"] = "Invalid impulse power"
                    return movement_state, result
                
                # Check energy requirements
                energy_needed = command.impulse_power * 10
                if ship_status.energy < energy_needed:
                    result["message"] = "Insufficient energy for impulse"
                    return movement_state, result
                
                # Execute impulse
                new_state = self.ship_movement.set_impulse(movement_state, command.impulse_power)
                result["success"] = True
                result["message"] = f"Impulse power {command.impulse_power} engaged"
                result["energy_consumed"] = energy_needed
                
            elif command.command_type == "rotate":
                if command.target_heading is None:
                    result["message"] = "No target heading specified"
                    return movement_state, result
                
                # Execute rotation
                new_state = self.ship_movement.rotate_ship(movement_state, command.target_heading)
                result["success"] = True
                result["message"] = f"Rotating to heading {command.target_heading}"
                result["energy_consumed"] = 5
                
            elif command.command_type == "stop":
                # Execute stop
                new_state = self.ship_movement.stop_ship(movement_state)
                result["success"] = True
                result["message"] = "All stop"
                result["energy_consumed"] = 0
                
            else:
                result["message"] = f"Unknown navigation command: {command.command_type}"
                return movement_state, result
            
            return new_state, result
            
        except Exception as e:
            logger.error(f"Error executing navigation command: {e}")
            result["message"] = f"Navigation system error: {str(e)}"
            return movement_state, result
    
    def manage_shields(self, ship_status: ShipStatus, action: str, 
                      shield_type: Optional[int] = None) -> Tuple[ShipStatus, Dict[str, Any]]:
        """
        Shield management system - equivalent to shieldstat() in original
        """
        result = {"success": False, "message": "", "energy_consumed": 0}
        
        try:
            if action == "up":
                if ship_status.shield_status == ShieldStatus.UP:
                    result["message"] = "Shields already up"
                    return ship_status, result
                
                # Check energy requirements
                energy_needed = 500
                if ship_status.energy < energy_needed:
                    result["message"] = "Insufficient energy to raise shields"
                    return ship_status, result
                
                # Raise shields
                ship_status.shield_status = ShieldStatus.CHARGING
                ship_status.shield_charge = 0
                result["success"] = True
                result["message"] = "Shields coming up"
                result["energy_consumed"] = energy_needed
                
            elif action == "down":
                if ship_status.shield_status == ShieldStatus.DOWN:
                    result["message"] = "Shields already down"
                    return ship_status, result
                
                # Lower shields
                ship_status.shield_status = ShieldStatus.DOWN
                ship_status.shield_charge = 0
                result["success"] = True
                result["message"] = "Shields down"
                
            elif action == "charge":
                if ship_status.shield_status != ShieldStatus.UP:
                    result["message"] = "Shields must be up to charge"
                    return ship_status, result
                
                # Check energy requirements
                energy_needed = 100
                if ship_status.energy < energy_needed:
                    result["message"] = "Insufficient energy to charge shields"
                    return ship_status, result
                
                # Charge shields
                max_charge = 100  # Based on shield type
                if ship_status.shield_charge < max_charge:
                    ship_status.shield_charge = min(max_charge, ship_status.shield_charge + 10)
                    result["success"] = True
                    result["message"] = f"Shields charging: {ship_status.shield_charge}%"
                    result["energy_consumed"] = energy_needed
                else:
                    result["message"] = "Shields at maximum charge"
                
            elif action == "set_type":
                if shield_type is None or shield_type < 0 or shield_type > 19:
                    result["message"] = "Invalid shield type"
                    return ship_status, result
                
                ship_status.shield_type = shield_type
                result["success"] = True
                result["message"] = f"Shield type set to {shield_type}"
                
            else:
                result["message"] = f"Unknown shield action: {action}"
            
            return ship_status, result
            
        except Exception as e:
            logger.error(f"Error managing shields: {e}")
            result["message"] = f"Shield system error: {str(e)}"
            return ship_status, result
    
    def manage_cloaking(self, ship_status: ShipStatus, action: str) -> Tuple[ShipStatus, Dict[str, Any]]:
        """
        Cloaking system management - equivalent to cloakstat() in original
        """
        result = {"success": False, "message": "", "energy_consumed": 0}
        
        try:
            if action == "engage":
                if ship_status.cloak_status == CloakStatus.UP:
                    result["message"] = "Cloaking device already engaged"
                    return ship_status, result
                
                # Check energy requirements
                energy_needed = 1000
                if ship_status.energy < energy_needed:
                    result["message"] = "Insufficient energy for cloaking device"
                    return ship_status, result
                
                # Engage cloaking
                ship_status.cloak_status = CloakStatus.CHARGING
                ship_status.cloak_time = 10  # Charging time in ticks
                result["success"] = True
                result["message"] = "Cloaking device engaging"
                result["energy_consumed"] = energy_needed
                
            elif action == "disengage":
                if ship_status.cloak_status == CloakStatus.DOWN:
                    result["message"] = "Cloaking device already disengaged"
                    return ship_status, result
                
                # Disengage cloaking
                ship_status.cloak_status = CloakStatus.DOWN
                ship_status.cloak_time = 0
                result["success"] = True
                result["message"] = "Cloaking device disengaged"
                
            else:
                result["message"] = f"Unknown cloaking action: {action}"
            
            return ship_status, result
            
        except Exception as e:
            logger.error(f"Error managing cloaking: {e}")
            result["message"] = f"Cloaking system error: {str(e)}"
            return ship_status, result
    
    def manage_energy(self, ship_status: ShipStatus, 
                     system: EnergySystem, amount: int) -> Tuple[ShipStatus, Dict[str, Any]]:
        """
        Energy management system - distribute power to ship systems
        """
        result = {"success": False, "message": ""}
        
        try:
            if amount < 0:
                result["message"] = "Cannot allocate negative energy"
                return ship_status, result
            
            if ship_status.energy < amount:
                result["message"] = "Insufficient energy available"
                return ship_status, result
            
            # Allocate energy to system
            if system == EnergySystem.SHIELDS:
                if ship_status.shield_status == ShieldStatus.UP:
                    max_charge = 100
                    energy_used = min(amount, max_charge - ship_status.shield_charge)
                    ship_status.shield_charge += energy_used
                    ship_status.energy -= energy_used
                    result["success"] = True
                    result["message"] = f"Energy allocated to shields: {energy_used}"
                else:
                    result["message"] = "Shields must be up to allocate energy"
                    
            elif system == EnergySystem.PHASERS:
                max_strength = 100
                energy_used = min(amount, max_strength - ship_status.phaser_strength)
                ship_status.phaser_strength += energy_used
                ship_status.energy -= energy_used
                result["success"] = True
                result["message"] = f"Energy allocated to phasers: {energy_used}"
                
            else:
                # Generic energy allocation
                ship_status.energy -= amount
                result["success"] = True
                result["message"] = f"Energy allocated to {system.value}: {amount}"
            
            return ship_status, result
            
        except Exception as e:
            logger.error(f"Error managing energy: {e}")
            result["message"] = f"Energy system error: {str(e)}"
            return ship_status, result
    
    def process_ship_repairs(self, ship_status: ShipStatus) -> Tuple[ShipStatus, Dict[str, Any]]:
        """
        Process ship repair systems - equivalent to repairship() in original
        """
        result = {"repairs_made": [], "energy_consumed": 0}
        
        try:
            if not ship_status.repair_in_progress:
                return ship_status, result
            
            # Check energy for repairs
            energy_needed = 50
            if ship_status.energy < energy_needed:
                result["message"] = "Insufficient energy for repairs"
                return ship_status, result
            
            repairs_made = []
            
            # Repair hull damage
            if ship_status.damage > 0:
                repair_amount = min(5.0, ship_status.damage)
                ship_status.damage -= repair_amount
                repairs_made.append(f"Hull damage repaired: {repair_amount}%")
            
            # Repair tactical systems
            if ship_status.tactical_damage > 0:
                repair_amount = min(10, ship_status.tactical_damage)
                ship_status.tactical_damage -= repair_amount
                repairs_made.append(f"Tactical systems repaired: {repair_amount}%")
            
            # Repair helm control
            if ship_status.helm_damage > 0:
                repair_amount = min(10, ship_status.helm_damage)
                ship_status.helm_damage -= repair_amount
                repairs_made.append(f"Helm control repaired: {repair_amount}%")
            
            # Repair fire control
            if ship_status.fire_control_damage:
                # 10% chance to repair fire control each tick
                if math.random() < 0.1:
                    ship_status.fire_control_damage = False
                    repairs_made.append("Fire control systems repaired")
            
            if repairs_made:
                ship_status.energy -= energy_needed
                result["repairs_made"] = repairs_made
                result["energy_consumed"] = energy_needed
            
            # Check if all repairs are complete
            if (ship_status.damage == 0 and 
                ship_status.tactical_damage == 0 and 
                ship_status.helm_damage == 0 and 
                not ship_status.fire_control_damage):
                ship_status.repair_in_progress = False
                repairs_made.append("All repairs complete")
            
            return ship_status, result
            
        except Exception as e:
            logger.error(f"Error processing repairs: {e}")
            result["message"] = f"Repair system error: {str(e)}"
            return ship_status, result
    
    def process_energy_regeneration(self, ship_status: ShipStatus) -> ShipStatus:
        """
        Process energy regeneration each tick
        """
        try:
            # Base energy regeneration
            energy_gain = self.energy_recharge_rate
            
            # Reduce regeneration based on damage
            if ship_status.damage > 0:
                damage_factor = 1.0 - (ship_status.damage / 200.0)  # Max 50% reduction
                energy_gain = int(energy_gain * damage_factor)
            
            # Apply energy regeneration
            ship_status.energy = min(ship_status.max_energy, ship_status.energy + energy_gain)
            
            return ship_status
            
        except Exception as e:
            logger.error(f"Error processing energy regeneration: {e}")
            return ship_status
    
    def process_system_drain(self, ship_status: ShipStatus) -> ShipStatus:
        """
        Process energy drain from active systems
        """
        try:
            total_drain = 0
            
            # Life support always drains energy
            total_drain += self.energy_consumption[EnergySystem.LIFE_SUPPORT]
            
            # Shield drain
            if ship_status.shield_status == ShieldStatus.UP:
                total_drain += self.energy_consumption[EnergySystem.SHIELDS]
            
            # Cloaking drain
            if ship_status.cloak_status == CloakStatus.UP:
                total_drain += self.energy_consumption[EnergySystem.CLOAKING]
            
            # Phaser system drain
            if ship_status.phaser_strength > 0:
                total_drain += self.energy_consumption[EnergySystem.PHASERS]
            
            # Apply energy drain
            ship_status.energy = max(0, ship_status.energy - total_drain)
            
            # If energy is critically low, shut down non-essential systems
            if ship_status.energy < 100:
                if ship_status.cloak_status == CloakStatus.UP:
                    ship_status.cloak_status = CloakStatus.DOWN
                    ship_status.cloak_time = 0
                
                if ship_status.shield_status == ShieldStatus.UP:
                    ship_status.shield_status = ShieldStatus.DOWN
                    ship_status.shield_charge = 0
            
            return ship_status
            
        except Exception as e:
            logger.error(f"Error processing system drain: {e}")
            return ship_status


class CargoManagement:
    """Ship cargo management system"""
    
    def __init__(self):
        self.item_weights = {
            # Based on original game item weights
            1: 1000,   # Food
            2: 800,    # Medicine
            3: 1200,   # Fuel
            4: 500,    # Equipment
            5: 2000,   # Ore
            6: 1500,   # Weapons
            7: 300,    # Luxury items
            8: 1000,   # Supplies
            9: 2500,   # Heavy machinery
            10: 100,   # Electronics
            11: 3000,  # Raw materials
            12: 600,   # Chemicals
            13: 400,   # Textiles
            14: 200    # Information
        }
    
    def calculate_cargo_weight(self, cargo_items: Dict[int, int]) -> int:
        """Calculate total cargo weight"""
        total_weight = 0
        for item_type, quantity in cargo_items.items():
            weight_per_unit = self.item_weights.get(item_type, 1000)
            total_weight += weight_per_unit * quantity
        return total_weight
    
    def can_carry_cargo(self, max_tons: int, current_cargo: Dict[int, int], 
                       new_item_type: int, new_quantity: int) -> bool:
        """Check if ship can carry additional cargo"""
        current_weight = self.calculate_cargo_weight(current_cargo)
        new_weight = self.item_weights.get(new_item_type, 1000) * new_quantity
        return (current_weight + new_weight) <= (max_tons * 1000)  # Convert tons to kg
    
    def add_cargo(self, current_cargo: Dict[int, int], 
                 item_type: int, quantity: int) -> Dict[int, int]:
        """Add cargo to ship"""
        new_cargo = current_cargo.copy()
        if item_type in new_cargo:
            new_cargo[item_type] += quantity
        else:
            new_cargo[item_type] = quantity
        return new_cargo
    
    def remove_cargo(self, current_cargo: Dict[int, int], 
                    item_type: int, quantity: int) -> Dict[int, int]:
        """Remove cargo from ship"""
        new_cargo = current_cargo.copy()
        if item_type in new_cargo:
            new_cargo[item_type] = max(0, new_cargo[item_type] - quantity)
            if new_cargo[item_type] == 0:
                del new_cargo[item_type]
        return new_cargo
