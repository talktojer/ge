"""
Cheat Prevention Service

This service provides comprehensive cheat detection and prevention
for the Galactic Empire game to maintain fair play and game integrity.
"""

import json
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..models.user import User
from ..models.ship import Ship
from ..models.planet import Planet
from ..core.audit_service import audit_service, AuditEventType, AuditSeverity


@dataclass
class CheatDetectionResult:
    """Result of cheat detection analysis"""
    is_suspicious: bool
    confidence_score: float  # 0.0 to 1.0
    violations: List[str]
    metadata: Dict[str, Any]


@dataclass
class GameStateSnapshot:
    """Snapshot of game state for validation"""
    timestamp: datetime
    user_id: int
    ships: List[Dict[str, Any]]
    planets: List[Dict[str, Any]]
    resources: Dict[str, int]
    score: int


class CheatPreventionService:
    """Service for detecting and preventing cheating"""
    
    def __init__(self):
        # Thresholds for suspicious activity
        self.thresholds = {
            'max_speed_multiplier': 1.5,  # Max allowed speed above ship class limit
            'max_energy_gain_per_tick': 1000,  # Max energy gain per tick
            'max_resource_gain_per_tick': 10000,  # Max resource gain per tick
            'max_score_gain_per_hour': 100000,  # Max score gain per hour
            'max_ships_per_hour': 5,  # Max ships created per hour
            'max_planets_per_hour': 10,  # Max planets colonized per hour
            'min_travel_time': 0.1,  # Minimum time between movements (seconds)
            'max_simultaneous_actions': 3,  # Max simultaneous actions per user
        }
        
        # Track user activity for pattern analysis
        self.user_activity: Dict[int, List[Dict[str, Any]]] = {}
        self.game_state_history: Dict[int, List[GameStateSnapshot]] = {}
        
        # Known cheat patterns
        self.cheat_patterns = {
            'resource_multiplication': self._detect_resource_multiplication,
            'speed_hacking': self._detect_speed_hacking,
            'teleportation': self._detect_teleportation,
            'energy_manipulation': self._detect_energy_manipulation,
            'score_manipulation': self._detect_score_manipulation,
            'time_manipulation': self._detect_time_manipulation,
            'duplicate_actions': self._detect_duplicate_actions,
        }
    
    def validate_user_action(self, db: Session, user_id: int, action: str, data: Dict[str, Any]) -> CheatDetectionResult:
        """Validate a user action for potential cheating"""
        violations = []
        confidence_score = 0.0
        metadata = {'action': action, 'timestamp': datetime.utcnow().isoformat()}
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return CheatDetectionResult(True, 1.0, ['Invalid user'], metadata)
        
        # Record action for pattern analysis
        self._record_user_action(user_id, action, data)
        
        # Run all cheat detection patterns
        for pattern_name, detection_func in self.cheat_patterns.items():
            try:
                result = detection_func(db, user_id, action, data)
                if result.is_suspicious:
                    violations.extend(result.violations)
                    confidence_score = max(confidence_score, result.confidence_score)
                    metadata[pattern_name] = result.metadata
            except Exception as e:
                # Log error but don't fail validation
                metadata[f'{pattern_name}_error'] = str(e)
        
        is_suspicious = len(violations) > 0
        
        # Log suspicious activity
        if is_suspicious:
            audit_service.log_event(
                db=db,
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                description=f"Suspicious activity detected: {', '.join(violations)}",
                user_id=user_id,
                severity=AuditSeverity.HIGH,
                metadata={
                    'action': action,
                    'violations': violations,
                    'confidence_score': confidence_score,
                    'data': data
                }
            )
        
        return CheatDetectionResult(is_suspicious, confidence_score, violations, metadata)
    
    def validate_ship_movement(self, db: Session, ship: Ship, new_x: float, new_y: float, time_delta: float) -> CheatDetectionResult:
        """Validate ship movement for speed hacking and teleportation"""
        violations = []
        confidence_score = 0.0
        metadata = {}
        
        if not ship:
            return CheatDetectionResult(True, 1.0, ['Invalid ship'], metadata)
        
        # Calculate distance moved
        distance = math.sqrt((new_x - ship.x) ** 2 + (new_y - ship.y) ** 2)
        metadata['distance'] = distance
        metadata['time_delta'] = time_delta
        
        if time_delta <= 0:
            violations.append('Invalid time delta')
            confidence_score = 1.0
        else:
            # Calculate speed
            speed = distance / time_delta
            metadata['calculated_speed'] = speed
            
            # Get ship class max speed
            max_speed = ship.ship_class.max_speed if ship.ship_class else 100
            metadata['max_speed'] = max_speed
            
            # Check for speed hacking
            if speed > max_speed * self.thresholds['max_speed_multiplier']:
                violations.append(f'Speed hacking: {speed:.2f} > {max_speed * self.thresholds["max_speed_multiplier"]:.2f}')
                confidence_score = max(confidence_score, 0.9)
            
            # Check for teleportation (instant movement over large distance)
            if distance > 1000 and time_delta < self.thresholds['min_travel_time']:
                violations.append(f'Teleportation detected: {distance:.2f} units in {time_delta:.3f} seconds')
                confidence_score = max(confidence_score, 0.95)
        
        return CheatDetectionResult(len(violations) > 0, confidence_score, violations, metadata)
    
    def validate_resource_change(self, db: Session, user_id: int, resource_type: str, old_value: int, new_value: int, time_delta: float) -> CheatDetectionResult:
        """Validate resource changes for manipulation"""
        violations = []
        confidence_score = 0.0
        metadata = {
            'resource_type': resource_type,
            'old_value': old_value,
            'new_value': new_value,
            'change': new_value - old_value,
            'time_delta': time_delta
        }
        
        change = new_value - old_value
        
        # Check for impossible resource gains
        if change > 0 and time_delta > 0:
            gain_rate = change / time_delta
            max_gain = self.thresholds['max_resource_gain_per_tick']
            
            if gain_rate > max_gain:
                violations.append(f'Impossible {resource_type} gain: {gain_rate:.2f}/sec > {max_gain}/sec')
                confidence_score = max(confidence_score, 0.8)
        
        # Check for negative resources (shouldn't be possible)
        if new_value < 0:
            violations.append(f'Negative {resource_type}: {new_value}')
            confidence_score = max(confidence_score, 0.7)
        
        # Check for unrealistic resource amounts
        if resource_type == 'cash' and new_value > 1000000000:  # 1 billion
            violations.append(f'Unrealistic {resource_type} amount: {new_value}')
            confidence_score = max(confidence_score, 0.6)
        
        return CheatDetectionResult(len(violations) > 0, confidence_score, violations, metadata)
    
    def validate_game_state_integrity(self, db: Session, user_id: int) -> CheatDetectionResult:
        """Validate overall game state integrity for a user"""
        violations = []
        confidence_score = 0.0
        metadata = {}
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return CheatDetectionResult(True, 1.0, ['Invalid user'], metadata)
        
        # Validate user statistics consistency
        ships = db.query(Ship).filter(Ship.user_id == user_id).all()
        planets = db.query(Planet).filter(Planet.owner_id == user_id).all()
        
        # Check ship count consistency
        actual_ship_count = len(ships)
        if user.noships != actual_ship_count:
            violations.append(f'Ship count mismatch: user.noships={user.noships}, actual={actual_ship_count}')
            confidence_score = max(confidence_score, 0.7)
        
        # Check planet count consistency
        actual_planet_count = len(planets)
        if user.planets != actual_planet_count:
            violations.append(f'Planet count mismatch: user.planets={user.planets}, actual={actual_planet_count}')
            confidence_score = max(confidence_score, 0.7)
        
        # Validate score components
        calculated_score = user.klscore + user.plscore
        if abs(user.score - calculated_score) > 1000:  # Allow small discrepancy
            violations.append(f'Score calculation error: {user.score} vs calculated {calculated_score}')
            confidence_score = max(confidence_score, 0.6)
        
        # Check for impossible coordinates
        for ship in ships:
            if abs(ship.x) > 10000 or abs(ship.y) > 10000:
                violations.append(f'Ship {ship.id} at impossible coordinates: ({ship.x}, {ship.y})')
                confidence_score = max(confidence_score, 0.8)
        
        for planet in planets:
            if abs(planet.x) > 10000 or abs(planet.y) > 10000:
                violations.append(f'Planet {planet.id} at impossible coordinates: ({planet.x}, {planet.y})')
                confidence_score = max(confidence_score, 0.8)
        
        metadata.update({
            'user_id': user_id,
            'ship_count': actual_ship_count,
            'planet_count': actual_planet_count,
            'score': user.score,
            'calculated_score': calculated_score
        })
        
        return CheatDetectionResult(len(violations) > 0, confidence_score, violations, metadata)
    
    # Internal detection methods
    def _detect_resource_multiplication(self, db: Session, user_id: int, action: str, data: Dict[str, Any]) -> CheatDetectionResult:
        """Detect resource multiplication cheats"""
        violations = []
        confidence_score = 0.0
        metadata = {}
        
        if action in ['buy_item', 'sell_item', 'transfer_resources']:
            # Check for impossible resource changes
            if 'old_amount' in data and 'new_amount' in data:
                old_amount = data['old_amount']
                new_amount = data['new_amount']
                
                # Check for multiplication patterns (e.g., 1000 -> 1000000)
                if old_amount > 0 and new_amount > old_amount * 100:
                    violations.append('Possible resource multiplication detected')
                    confidence_score = 0.8
                    metadata['multiplication_factor'] = new_amount / old_amount
        
        return CheatDetectionResult(len(violations) > 0, confidence_score, violations, metadata)
    
    def _detect_speed_hacking(self, db: Session, user_id: int, action: str, data: Dict[str, Any]) -> CheatDetectionResult:
        """Detect speed hacking"""
        violations = []
        confidence_score = 0.0
        metadata = {}
        
        if action == 'move_ship' and 'ship_id' in data:
            ship = db.query(Ship).filter(Ship.id == data['ship_id']).first()
            if ship and 'new_x' in data and 'new_y' in data and 'time_delta' in data:
                result = self.validate_ship_movement(
                    db, ship, data['new_x'], data['new_y'], data['time_delta']
                )
                return result
        
        return CheatDetectionResult(len(violations) > 0, confidence_score, violations, metadata)
    
    def _detect_teleportation(self, db: Session, user_id: int, action: str, data: Dict[str, Any]) -> CheatDetectionResult:
        """Detect teleportation cheats"""
        # This is handled by _detect_speed_hacking
        return CheatDetectionResult(False, 0.0, [], {})
    
    def _detect_energy_manipulation(self, db: Session, user_id: int, action: str, data: Dict[str, Any]) -> CheatDetectionResult:
        """Detect energy manipulation"""
        violations = []
        confidence_score = 0.0
        metadata = {}
        
        if action in ['ship_action'] and 'energy_change' in data:
            energy_change = data['energy_change']
            time_delta = data.get('time_delta', 1.0)
            
            if energy_change > self.thresholds['max_energy_gain_per_tick'] * time_delta:
                violations.append(f'Impossible energy gain: {energy_change} in {time_delta} seconds')
                confidence_score = 0.9
        
        return CheatDetectionResult(len(violations) > 0, confidence_score, violations, metadata)
    
    def _detect_score_manipulation(self, db: Session, user_id: int, action: str, data: Dict[str, Any]) -> CheatDetectionResult:
        """Detect score manipulation"""
        violations = []
        confidence_score = 0.0
        metadata = {}
        
        if action == 'score_update' and 'score_change' in data:
            score_change = data['score_change']
            time_delta = data.get('time_delta', 3600)  # Default 1 hour
            
            if score_change > self.thresholds['max_score_gain_per_hour'] * (time_delta / 3600):
                violations.append(f'Impossible score gain: {score_change} in {time_delta} seconds')
                confidence_score = 0.8
        
        return CheatDetectionResult(len(violations) > 0, confidence_score, violations, metadata)
    
    def _detect_time_manipulation(self, db: Session, user_id: int, action: str, data: Dict[str, Any]) -> CheatDetectionResult:
        """Detect time manipulation (e.g., clock speed changes)"""
        violations = []
        confidence_score = 0.0
        metadata = {}
        
        # Check for actions happening too quickly
        current_time = time.time()
        user_actions = self.user_activity.get(user_id, [])
        
        if len(user_actions) > 0:
            last_action_time = user_actions[-1].get('timestamp', current_time)
            time_diff = current_time - last_action_time
            
            if time_diff < self.thresholds['min_travel_time']:
                violations.append(f'Actions too fast: {time_diff:.3f} seconds between actions')
                confidence_score = 0.7
        
        return CheatDetectionResult(len(violations) > 0, confidence_score, violations, metadata)
    
    def _detect_duplicate_actions(self, db: Session, user_id: int, action: str, data: Dict[str, Any]) -> CheatDetectionResult:
        """Detect duplicate actions (replay attacks)"""
        violations = []
        confidence_score = 0.0
        metadata = {}
        
        user_actions = self.user_activity.get(user_id, [])
        
        # Check for identical actions in short time frame
        current_time = time.time()
        recent_actions = [
            a for a in user_actions 
            if current_time - a.get('timestamp', 0) < 60  # Last minute
        ]
        
        # Look for exact duplicates
        current_action_key = f"{action}:{hash(str(sorted(data.items())))}"
        duplicate_count = sum(1 for a in recent_actions if a.get('action_key') == current_action_key)
        
        if duplicate_count > 0:
            violations.append(f'Duplicate action detected: {action}')
            confidence_score = 0.6
            metadata['duplicate_count'] = duplicate_count
        
        return CheatDetectionResult(len(violations) > 0, confidence_score, violations, metadata)
    
    def _record_user_action(self, user_id: int, action: str, data: Dict[str, Any]):
        """Record user action for pattern analysis"""
        if user_id not in self.user_activity:
            self.user_activity[user_id] = []
        
        action_record = {
            'action': action,
            'data': data,
            'timestamp': time.time(),
            'action_key': f"{action}:{hash(str(sorted(data.items())))}"
        }
        
        self.user_activity[user_id].append(action_record)
        
        # Keep only recent actions (last 24 hours)
        cutoff_time = time.time() - 86400
        self.user_activity[user_id] = [
            a for a in self.user_activity[user_id] 
            if a['timestamp'] > cutoff_time
        ]
    
    # Administrative functions
    def get_suspicious_users(self, db: Session, hours: int = 24, min_confidence: float = 0.7) -> List[Dict[str, Any]]:
        """Get list of users with suspicious activity"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        suspicious_logs = db.query(audit_service.AuditLog).filter(
            audit_service.AuditLog.event_type == AuditEventType.SUSPICIOUS_ACTIVITY.value,
            audit_service.AuditLog.timestamp >= since
        ).all()
        
        user_suspicion = {}
        for log in suspicious_logs:
            user_id = log.user_id
            if user_id not in user_suspicion:
                user_suspicion[user_id] = {
                    'user_id': user_id,
                    'violations': [],
                    'max_confidence': 0.0,
                    'incident_count': 0
                }
            
            metadata = json.loads(log.metadata) if log.metadata else {}
            confidence = metadata.get('confidence_score', 0.0)
            
            user_suspicion[user_id]['violations'].extend(metadata.get('violations', []))
            user_suspicion[user_id]['max_confidence'] = max(user_suspicion[user_id]['max_confidence'], confidence)
            user_suspicion[user_id]['incident_count'] += 1
        
        # Filter by minimum confidence
        return [
            data for data in user_suspicion.values() 
            if data['max_confidence'] >= min_confidence
        ]
    
    def reset_user_activity(self, user_id: int = None):
        """Reset user activity tracking"""
        if user_id:
            if user_id in self.user_activity:
                del self.user_activity[user_id]
        else:
            self.user_activity.clear()


# Global cheat prevention service instance
cheat_prevention_service = CheatPreventionService()
