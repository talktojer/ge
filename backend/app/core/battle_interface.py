"""
Galactic Empire - Battle Interface Systems

This module implements tactical display systems, range scanners, target locking,
battle status displays, and damage reporting for combat operations.
"""

import logging
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .coordinates import Coordinate, distance, bearing, get_sector
from .battle_mechanics import DamageReport, BattleState, SystemDamage

logger = logging.getLogger(__name__)


class ScannerType(Enum):
    """Types of scanners available"""
    SHORT_RANGE = "short_range"
    LONG_RANGE = "long_range"
    TACTICAL = "tactical"
    HYPERSPACE = "hyperspace"
    CLOAK_DETECTOR = "cloak_detector"


class TargetLockStatus(Enum):
    """Target lock status"""
    NO_LOCK = "no_lock"
    ACQUIRING = "acquiring"
    LOCKED = "locked"
    LOST = "lost"
    JAMMED = "jammed"


class TacticalDisplayMode(Enum):
    """Tactical display modes"""
    OVERVIEW = "overview"
    COMBAT = "combat"
    NAVIGATION = "navigation"
    DAMAGE_CONTROL = "damage_control"
    SCANNER = "scanner"


@dataclass
class ScanResult:
    """Result from scanner operation"""
    target_id: str
    target_type: str  # "ship", "planet", "mine", "beacon", "wormhole"
    name: str
    position: Coordinate
    distance: float
    bearing: float
    sector: Tuple[int, int]
    is_cloaked: bool
    is_hostile: bool
    confidence: float  # 0.0 to 1.0, how certain the scan is
    additional_data: Dict[str, Any]


@dataclass
class TargetLock:
    """Target lock information"""
    target_id: str
    lock_status: TargetLockStatus
    lock_strength: float  # 0.0 to 1.0
    lock_time: datetime
    time_to_acquire: int  # ticks remaining to full lock
    jammer_interference: float
    lock_range: float
    target_bearing: float


@dataclass
class TacticalDisplay:
    """Tactical display information"""
    display_mode: TacticalDisplayMode
    center_position: Coordinate
    display_range: float
    objects: List[Dict[str, Any]]
    grid_lines: List[Dict[str, Any]]
    threat_assessment: Dict[str, Any]
    navigation_data: Dict[str, Any]
    damage_status: Dict[str, Any]


class RangeScanner:
    """Range scanner system implementation"""
    
    def __init__(self):
        # Scanner ranges by type
        self.scanner_ranges = {
            ScannerType.SHORT_RANGE: 50000.0,
            ScannerType.LONG_RANGE: 200000.0,
            ScannerType.TACTICAL: 100000.0,
            ScannerType.HYPERSPACE: 500000.0,
            ScannerType.CLOAK_DETECTOR: 75000.0
        }
        
        # Scanner accuracy by type
        self.scanner_accuracy = {
            ScannerType.SHORT_RANGE: 0.95,
            ScannerType.LONG_RANGE: 0.80,
            ScannerType.TACTICAL: 0.90,
            ScannerType.HYPERSPACE: 0.70,
            ScannerType.CLOAK_DETECTOR: 0.85
        }
        
        # Energy costs per scan
        self.scanner_energy_cost = {
            ScannerType.SHORT_RANGE: 10,
            ScannerType.LONG_RANGE: 25,
            ScannerType.TACTICAL: 15,
            ScannerType.HYPERSPACE: 50,
            ScannerType.CLOAK_DETECTOR: 30
        }
    
    def perform_scan(self, scanner_type: ScannerType, ship_position: Coordinate,
                    ship_energy: int, scan_range: Optional[float] = None,
                    all_objects: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform scanner sweep"""
        try:
            # Check energy requirements
            energy_needed = self.scanner_energy_cost.get(scanner_type, 20)
            if ship_energy < energy_needed:
                return {
                    "success": False,
                    "message": "Insufficient energy for scanner operation",
                    "energy_required": energy_needed
                }
            
            # Determine scan range
            max_range = scan_range or self.scanner_ranges.get(scanner_type, 100000.0)
            accuracy = self.scanner_accuracy.get(scanner_type, 0.8)
            
            # Perform scan
            scan_results = []
            
            if all_objects:
                for obj in all_objects:
                    obj_position = Coordinate(obj.get("x", 0), obj.get("y", 0))
                    obj_distance = distance(ship_position, obj_position)
                    
                    if obj_distance <= max_range:
                        # Check if object is detectable
                        detection_chance = self._calculate_detection_chance(
                            scanner_type, obj, obj_distance, max_range, accuracy
                        )
                        
                        if math.random() < detection_chance:
                            scan_result = self._create_scan_result(
                                obj, ship_position, obj_position, obj_distance, accuracy
                            )
                            scan_results.append(scan_result)
            
            return {
                "success": True,
                "scanner_type": scanner_type.value,
                "scan_range": max_range,
                "energy_consumed": energy_needed,
                "objects_detected": len(scan_results),
                "scan_results": [self._scan_result_to_dict(sr) for sr in scan_results]
            }
            
        except Exception as e:
            logger.error(f"Error performing scan: {e}")
            return {
                "success": False,
                "message": f"Scanner error: {str(e)}"
            }
    
    def _calculate_detection_chance(self, scanner_type: ScannerType, obj: Dict[str, Any],
                                  obj_distance: float, max_range: float, base_accuracy: float) -> float:
        """Calculate chance of detecting an object"""
        try:
            # Base detection chance
            detection_chance = base_accuracy
            
            # Range affects detection
            range_factor = 1.0 - (obj_distance / max_range) * 0.3
            detection_chance *= range_factor
            
            # Object type affects detection
            obj_type = obj.get("type", "unknown")
            if obj_type == "ship":
                # Cloaked ships are harder to detect
                if obj.get("is_cloaked", False):
                    if scanner_type == ScannerType.CLOAK_DETECTOR:
                        detection_chance *= 0.8  # Cloak detector is better vs cloaked ships
                    else:
                        detection_chance *= 0.2  # Other scanners struggle
                
                # Ship size affects detection
                ship_class = obj.get("ship_class", 1)
                size_factor = 0.8 + (ship_class * 0.05)  # Larger ships easier to detect
                detection_chance *= size_factor
                
            elif obj_type == "planet":
                detection_chance = 1.0  # Planets always detectable
                
            elif obj_type == "mine":
                detection_chance *= 0.3  # Mines are hard to detect
                
            elif obj_type == "beacon":
                detection_chance = 1.0  # Beacons want to be detected
            
            return max(0.0, min(1.0, detection_chance))
            
        except Exception as e:
            logger.error(f"Error calculating detection chance: {e}")
            return 0.5
    
    def _create_scan_result(self, obj: Dict[str, Any], ship_pos: Coordinate,
                          obj_pos: Coordinate, obj_distance: float, accuracy: float) -> ScanResult:
        """Create scan result from detected object"""
        try:
            # Add some inaccuracy to readings
            distance_error = obj_distance * (1.0 - accuracy) * 0.1
            actual_distance = obj_distance + (math.random() - 0.5) * distance_error
            
            bearing_error = (1.0 - accuracy) * 10.0  # degrees
            actual_bearing = bearing(ship_pos, obj_pos) + (math.random() - 0.5) * bearing_error
            
            return ScanResult(
                target_id=str(obj.get("id", "unknown")),
                target_type=obj.get("type", "unknown"),
                name=obj.get("name", "Unknown"),
                position=obj_pos,
                distance=actual_distance,
                bearing=actual_bearing,
                sector=get_sector(obj_pos),
                is_cloaked=obj.get("is_cloaked", False),
                is_hostile=obj.get("is_hostile", False),
                confidence=accuracy,
                additional_data=obj.get("additional_data", {})
            )
            
        except Exception as e:
            logger.error(f"Error creating scan result: {e}")
            return ScanResult(
                target_id="error",
                target_type="unknown",
                name="Scan Error",
                position=obj_pos,
                distance=0.0,
                bearing=0.0,
                sector=(0, 0),
                is_cloaked=False,
                is_hostile=False,
                confidence=0.0,
                additional_data={}
            )
    
    def _scan_result_to_dict(self, scan_result: ScanResult) -> Dict[str, Any]:
        """Convert ScanResult to dictionary"""
        return {
            "target_id": scan_result.target_id,
            "target_type": scan_result.target_type,
            "name": scan_result.name,
            "position": {
                "x": scan_result.position.x,
                "y": scan_result.position.y
            },
            "distance": scan_result.distance,
            "bearing": scan_result.bearing,
            "sector": scan_result.sector,
            "is_cloaked": scan_result.is_cloaked,
            "is_hostile": scan_result.is_hostile,
            "confidence": scan_result.confidence,
            "additional_data": scan_result.additional_data
        }


class TargetLockingSystem:
    """Target locking system for weapons"""
    
    def __init__(self):
        self.active_locks: Dict[str, TargetLock] = {}
        self.base_lock_time = 5  # ticks to acquire lock
        self.lock_decay_rate = 0.1  # lock strength decay per tick without update
        self.max_lock_range = 150000.0
    
    def acquire_target_lock(self, ship_id: str, target_id: str, 
                          target_distance: float, target_bearing: float,
                          fire_control_damage: bool = False) -> Dict[str, Any]:
        """Begin target lock acquisition"""
        try:
            if target_distance > self.max_lock_range:
                return {
                    "success": False,
                    "message": "Target out of lock range"
                }
            
            # Check if already locking this target
            lock_key = f"{ship_id}_{target_id}"
            if lock_key in self.active_locks:
                return {
                    "success": False,
                    "message": "Already acquiring lock on this target"
                }
            
            # Calculate lock time based on conditions
            lock_time = self.base_lock_time
            
            # Fire control damage increases lock time
            if fire_control_damage:
                lock_time *= 2
            
            # Distance affects lock time
            distance_factor = target_distance / self.max_lock_range
            lock_time = int(lock_time * (1.0 + distance_factor))
            
            # Create target lock
            target_lock = TargetLock(
                target_id=target_id,
                lock_status=TargetLockStatus.ACQUIRING,
                lock_strength=0.0,
                lock_time=datetime.utcnow(),
                time_to_acquire=lock_time,
                jammer_interference=0.0,
                lock_range=target_distance,
                target_bearing=target_bearing
            )
            
            self.active_locks[lock_key] = target_lock
            
            return {
                "success": True,
                "message": f"Acquiring target lock on {target_id}",
                "time_to_acquire": lock_time,
                "lock_key": lock_key
            }
            
        except Exception as e:
            logger.error(f"Error acquiring target lock: {e}")
            return {
                "success": False,
                "message": f"Lock acquisition error: {str(e)}"
            }
    
    def update_target_lock(self, ship_id: str, target_id: str,
                         target_distance: float, target_bearing: float,
                         jammer_active: bool = False) -> Dict[str, Any]:
        """Update existing target lock"""
        try:
            lock_key = f"{ship_id}_{target_id}"
            if lock_key not in self.active_locks:
                return {
                    "success": False,
                    "message": "No active lock on this target"
                }
            
            target_lock = self.active_locks[lock_key]
            
            # Check if target moved out of range
            if target_distance > self.max_lock_range:
                target_lock.lock_status = TargetLockStatus.LOST
                target_lock.lock_strength = 0.0
                return {
                    "success": False,
                    "message": "Target moved out of lock range",
                    "lock_status": "lost"
                }
            
            # Update lock position
            target_lock.lock_range = target_distance
            target_lock.target_bearing = target_bearing
            
            # Handle jammer interference
            if jammer_active:
                target_lock.jammer_interference = min(1.0, target_lock.jammer_interference + 0.2)
                target_lock.lock_strength = max(0.0, target_lock.lock_strength - 0.3)
                if target_lock.lock_strength < 0.3:
                    target_lock.lock_status = TargetLockStatus.JAMMED
            else:
                target_lock.jammer_interference = max(0.0, target_lock.jammer_interference - 0.1)
            
            # Update lock acquisition
            if target_lock.lock_status == TargetLockStatus.ACQUIRING:
                target_lock.time_to_acquire -= 1
                target_lock.lock_strength = min(1.0, target_lock.lock_strength + 0.2)
                
                if target_lock.time_to_acquire <= 0:
                    target_lock.lock_status = TargetLockStatus.LOCKED
                    target_lock.lock_strength = 1.0
            
            return {
                "success": True,
                "lock_status": target_lock.lock_status.value,
                "lock_strength": target_lock.lock_strength,
                "time_to_acquire": max(0, target_lock.time_to_acquire),
                "jammer_interference": target_lock.jammer_interference
            }
            
        except Exception as e:
            logger.error(f"Error updating target lock: {e}")
            return {
                "success": False,
                "message": f"Lock update error: {str(e)}"
            }
    
    def break_target_lock(self, ship_id: str, target_id: str) -> Dict[str, Any]:
        """Break target lock"""
        try:
            lock_key = f"{ship_id}_{target_id}"
            if lock_key not in self.active_locks:
                return {
                    "success": False,
                    "message": "No active lock on this target"
                }
            
            del self.active_locks[lock_key]
            
            return {
                "success": True,
                "message": "Target lock broken"
            }
            
        except Exception as e:
            logger.error(f"Error breaking target lock: {e}")
            return {
                "success": False,
                "message": f"Lock break error: {str(e)}"
            }
    
    def get_target_lock_status(self, ship_id: str, target_id: str) -> Optional[Dict[str, Any]]:
        """Get current target lock status"""
        try:
            lock_key = f"{ship_id}_{target_id}"
            if lock_key not in self.active_locks:
                return None
            
            target_lock = self.active_locks[lock_key]
            
            return {
                "target_id": target_lock.target_id,
                "lock_status": target_lock.lock_status.value,
                "lock_strength": target_lock.lock_strength,
                "time_to_acquire": target_lock.time_to_acquire,
                "jammer_interference": target_lock.jammer_interference,
                "lock_range": target_lock.lock_range,
                "target_bearing": target_lock.target_bearing
            }
            
        except Exception as e:
            logger.error(f"Error getting target lock status: {e}")
            return None
    
    def process_lock_tick(self) -> List[Dict[str, Any]]:
        """Process all target locks for one tick"""
        try:
            results = []
            locks_to_remove = []
            
            for lock_key, target_lock in self.active_locks.items():
                # Decay lock strength over time
                if target_lock.lock_status == TargetLockStatus.LOCKED:
                    target_lock.lock_strength = max(0.0, target_lock.lock_strength - self.lock_decay_rate)
                    
                    if target_lock.lock_strength < 0.3:
                        target_lock.lock_status = TargetLockStatus.LOST
                        locks_to_remove.append(lock_key)
                
                results.append({
                    "lock_key": lock_key,
                    "target_id": target_lock.target_id,
                    "lock_status": target_lock.lock_status.value,
                    "lock_strength": target_lock.lock_strength
                })
            
            # Remove lost locks
            for lock_key in locks_to_remove:
                del self.active_locks[lock_key]
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing lock tick: {e}")
            return []


class TacticalDisplaySystem:
    """Tactical display and battle interface"""
    
    def __init__(self):
        self.scanner = RangeScanner()
        self.target_lock = TargetLockingSystem()
    
    def generate_tactical_display(self, ship_position: Coordinate, 
                                display_mode: TacticalDisplayMode,
                                display_range: float,
                                ship_data: Dict[str, Any],
                                nearby_objects: List[Dict[str, Any]]) -> TacticalDisplay:
        """Generate tactical display information"""
        try:
            # Filter objects by display range
            display_objects = []
            for obj in nearby_objects:
                obj_pos = Coordinate(obj.get("x", 0), obj.get("y", 0))
                obj_distance = distance(ship_position, obj_pos)
                
                if obj_distance <= display_range:
                    display_objects.append({
                        "id": obj.get("id"),
                        "type": obj.get("type"),
                        "name": obj.get("name", "Unknown"),
                        "position": {"x": obj_pos.x, "y": obj_pos.y},
                        "distance": obj_distance,
                        "bearing": bearing(ship_position, obj_pos),
                        "is_hostile": obj.get("is_hostile", False),
                        "is_cloaked": obj.get("is_cloaked", False)
                    })
            
            # Generate grid lines for display
            grid_lines = self._generate_grid_lines(ship_position, display_range)
            
            # Assess threats
            threat_assessment = self._assess_threats(display_objects, ship_data)
            
            # Navigation data
            navigation_data = {
                "current_position": {"x": ship_position.x, "y": ship_position.y},
                "current_sector": get_sector(ship_position),
                "heading": ship_data.get("heading", 0.0),
                "speed": ship_data.get("speed", 0.0)
            }
            
            # Damage status
            damage_status = self._get_damage_status(ship_data)
            
            return TacticalDisplay(
                display_mode=display_mode,
                center_position=ship_position,
                display_range=display_range,
                objects=display_objects,
                grid_lines=grid_lines,
                threat_assessment=threat_assessment,
                navigation_data=navigation_data,
                damage_status=damage_status
            )
            
        except Exception as e:
            logger.error(f"Error generating tactical display: {e}")
            return TacticalDisplay(
                display_mode=display_mode,
                center_position=ship_position,
                display_range=display_range,
                objects=[],
                grid_lines=[],
                threat_assessment={},
                navigation_data={},
                damage_status={}
            )
    
    def _generate_grid_lines(self, center: Coordinate, display_range: float) -> List[Dict[str, Any]]:
        """Generate grid lines for tactical display"""
        try:
            grid_lines = []
            grid_spacing = display_range / 10.0  # 10 grid divisions
            
            # Vertical lines
            for i in range(-5, 6):
                x = center.x + (i * grid_spacing)
                grid_lines.append({
                    "type": "vertical",
                    "x": x,
                    "y_start": center.y - display_range,
                    "y_end": center.y + display_range
                })
            
            # Horizontal lines
            for i in range(-5, 6):
                y = center.y + (i * grid_spacing)
                grid_lines.append({
                    "type": "horizontal",
                    "y": y,
                    "x_start": center.x - display_range,
                    "x_end": center.x + display_range
                })
            
            # Range circles
            for i in range(1, 4):
                radius = display_range * (i / 4.0)
                grid_lines.append({
                    "type": "circle",
                    "center_x": center.x,
                    "center_y": center.y,
                    "radius": radius
                })
            
            return grid_lines
            
        except Exception as e:
            logger.error(f"Error generating grid lines: {e}")
            return []
    
    def _assess_threats(self, objects: List[Dict[str, Any]], ship_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess threat level of nearby objects"""
        try:
            threats = []
            total_threat_level = 0.0
            
            for obj in objects:
                if obj.get("type") == "ship" and obj.get("is_hostile"):
                    threat_level = self._calculate_threat_level(obj, ship_data)
                    threats.append({
                        "id": obj["id"],
                        "name": obj["name"],
                        "distance": obj["distance"],
                        "threat_level": threat_level,
                        "threat_type": "hostile_ship"
                    })
                    total_threat_level += threat_level
                
                elif obj.get("type") == "mine":
                    threat_level = 0.7  # Mines are always a significant threat
                    threats.append({
                        "id": obj["id"],
                        "name": "Mine",
                        "distance": obj["distance"],
                        "threat_level": threat_level,
                        "threat_type": "mine"
                    })
                    total_threat_level += threat_level
            
            return {
                "total_threat_level": min(1.0, total_threat_level),
                "threat_count": len(threats),
                "threats": threats,
                "recommendation": self._get_threat_recommendation(total_threat_level)
            }
            
        except Exception as e:
            logger.error(f"Error assessing threats: {e}")
            return {"total_threat_level": 0.0, "threat_count": 0, "threats": []}
    
    def _calculate_threat_level(self, hostile_ship: Dict[str, Any], our_ship: Dict[str, Any]) -> float:
        """Calculate threat level of a hostile ship"""
        try:
            threat_level = 0.5  # Base threat
            
            # Distance factor (closer = more threatening)
            distance = hostile_ship.get("distance", 100000.0)
            if distance < 50000:
                threat_level += 0.3
            elif distance < 100000:
                threat_level += 0.2
            else:
                threat_level += 0.1
            
            # Ship class comparison (would need ship class data)
            # For now, assume equal threat
            
            # Cloaked ships are more threatening
            if hostile_ship.get("is_cloaked"):
                threat_level += 0.2
            
            return min(1.0, threat_level)
            
        except Exception as e:
            logger.error(f"Error calculating threat level: {e}")
            return 0.5
    
    def _get_threat_recommendation(self, total_threat: float) -> str:
        """Get tactical recommendation based on threat level"""
        if total_threat < 0.3:
            return "LOW_THREAT"
        elif total_threat < 0.6:
            return "MODERATE_THREAT"
        elif total_threat < 0.8:
            return "HIGH_THREAT"
        else:
            return "EXTREME_THREAT"
    
    def _get_damage_status(self, ship_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get ship damage status for display"""
        try:
            return {
                "hull_damage": ship_data.get("damage", 0.0),
                "shield_status": ship_data.get("shield_status", 0),
                "shield_charge": ship_data.get("shield_charge", 0),
                "energy_level": ship_data.get("energy", 0),
                "system_damage": {
                    "tactical": ship_data.get("tactical_damage", 0),
                    "helm": ship_data.get("helm_damage", 0),
                    "fire_control": ship_data.get("fire_control_damage", False)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting damage status: {e}")
            return {}
    
    def generate_damage_report(self, damage_report: DamageReport) -> Dict[str, Any]:
        """Generate formatted damage report for display"""
        try:
            return {
                "summary": {
                    "total_damage": damage_report.total_damage,
                    "shield_damage": damage_report.shield_damage,
                    "hull_damage": damage_report.hull_damage,
                    "ship_destroyed": damage_report.ship_destroyed
                },
                "weapon_info": {
                    "damage_type": damage_report.damage_type.value,
                    "weapon_effectiveness": damage_report.weapon_effectiveness,
                    "shield_effectiveness": damage_report.shield_effectiveness
                },
                "critical_effects": damage_report.critical_hits,
                "system_damage": {
                    system.value: damage for system, damage in damage_report.system_damage.items()
                },
                "systems_destroyed": [system.value for system in damage_report.systems_destroyed],
                "display_message": self._format_damage_message(damage_report)
            }
            
        except Exception as e:
            logger.error(f"Error generating damage report: {e}")
            return {"summary": {"total_damage": 0.0}, "display_message": "Damage report error"}
    
    def _format_damage_message(self, damage_report: DamageReport) -> str:
        """Format damage report into display message"""
        try:
            if damage_report.ship_destroyed:
                return "TARGET DESTROYED!"
            
            messages = []
            
            if damage_report.hull_damage > 50:
                messages.append("HEAVY DAMAGE")
            elif damage_report.hull_damage > 20:
                messages.append("MODERATE DAMAGE")
            elif damage_report.hull_damage > 0:
                messages.append("LIGHT DAMAGE")
            
            if damage_report.shield_damage > 0:
                messages.append(f"SHIELDS HIT ({damage_report.shield_damage:.1f})")
            
            if damage_report.critical_hits:
                messages.append("CRITICAL HIT!")
            
            if damage_report.systems_destroyed:
                messages.append("SYSTEMS DESTROYED")
            
            return " - ".join(messages) if messages else "NO EFFECT"
            
        except Exception as e:
            logger.error(f"Error formatting damage message: {e}")
            return "DAMAGE REPORT ERROR"
