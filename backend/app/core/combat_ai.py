"""
Galactic Empire - Combat AI Systems

This module implements AI systems for Cybertron and Droid ships including
combat decision making, attack patterns, and strategic behaviors.
Based on GECYBS.C and GEDROIDS.C from the original game.
"""

import logging
import math
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .coordinates import Coordinate, distance, bearing
from .battle_mechanics import DamageType
from .battle_interface import ScannerType

logger = logging.getLogger(__name__)


class AIPersonality(Enum):
    """AI personality types"""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    BALANCED = "balanced"
    COWARD = "coward"
    BERSERKER = "berserker"
    TACTICAL = "tactical"


class AIState(Enum):
    """AI state machine states"""
    IDLE = "idle"
    PATROL = "patrol"
    HUNT = "hunt"
    ATTACK = "attack"
    RETREAT = "retreat"
    DEFEND = "defend"
    REPAIR = "repair"
    RESUPPLY = "resupply"


class AITarget(Enum):
    """AI target priorities"""
    ENEMY_SHIP = "enemy_ship"
    ENEMY_PLANET = "enemy_planet"
    RESOURCE = "resource"
    STRATEGIC_POINT = "strategic_point"
    THREAT = "threat"


@dataclass
class AIShipData:
    """AI ship data and state"""
    ship_id: str
    ship_class: int
    ai_type: str  # "CYBORG" or "DROID"
    personality: AIPersonality
    current_state: AIState
    position: Coordinate
    heading: float
    speed: float
    energy: int
    damage: float
    shields: int
    target_id: Optional[str]
    last_action: datetime
    decision_cooldown: int
    skill_level: int  # 0-100
    aggression: float  # 0.0-1.0
    caution: float    # 0.0-1.0


@dataclass
class AIDecision:
    """AI decision result"""
    action_type: str
    target_id: Optional[str]
    parameters: Dict[str, Any]
    priority: float
    reasoning: str


class CombatAI:
    """Base combat AI system"""
    
    def __init__(self):
        # AI parameters
        self.scan_frequency = 5  # ticks between scans
        self.decision_frequency = 3  # ticks between decisions
        self.engagement_range = 150000.0
        self.retreat_threshold = 0.8  # retreat when damage > 80%
        
        # Personality modifiers
        self.personality_modifiers = {
            AIPersonality.AGGRESSIVE: {
                "aggression": 0.9,
                "caution": 0.2,
                "engagement_range": 1.2,
                "retreat_threshold": 0.9
            },
            AIPersonality.DEFENSIVE: {
                "aggression": 0.3,
                "caution": 0.8,
                "engagement_range": 0.8,
                "retreat_threshold": 0.6
            },
            AIPersonality.BALANCED: {
                "aggression": 0.6,
                "caution": 0.5,
                "engagement_range": 1.0,
                "retreat_threshold": 0.8
            },
            AIPersonality.COWARD: {
                "aggression": 0.1,
                "caution": 0.9,
                "engagement_range": 0.6,
                "retreat_threshold": 0.4
            },
            AIPersonality.BERSERKER: {
                "aggression": 1.0,
                "caution": 0.1,
                "engagement_range": 1.5,
                "retreat_threshold": 1.0
            },
            AIPersonality.TACTICAL: {
                "aggression": 0.7,
                "caution": 0.6,
                "engagement_range": 1.1,
                "retreat_threshold": 0.7
            }
        }
    
    def make_decision(self, ai_ship: AIShipData, 
                     nearby_objects: List[Dict[str, Any]],
                     game_state: Dict[str, Any]) -> AIDecision:
        """Make AI decision based on current situation"""
        try:
            # Apply personality modifiers
            modifiers = self.personality_modifiers.get(ai_ship.personality, {})
            effective_aggression = ai_ship.aggression * modifiers.get("aggression", 1.0)
            effective_caution = ai_ship.caution * modifiers.get("caution", 1.0)
            
            # Assess current situation
            situation = self._assess_situation(ai_ship, nearby_objects)
            
            # State machine logic
            if ai_ship.current_state == AIState.IDLE:
                return self._decide_idle_action(ai_ship, situation, effective_aggression)
            
            elif ai_ship.current_state == AIState.PATROL:
                return self._decide_patrol_action(ai_ship, situation, effective_aggression)
            
            elif ai_ship.current_state == AIState.HUNT:
                return self._decide_hunt_action(ai_ship, situation, effective_aggression)
            
            elif ai_ship.current_state == AIState.ATTACK:
                return self._decide_attack_action(ai_ship, situation, effective_caution)
            
            elif ai_ship.current_state == AIState.RETREAT:
                return self._decide_retreat_action(ai_ship, situation)
            
            elif ai_ship.current_state == AIState.REPAIR:
                return self._decide_repair_action(ai_ship, situation)
            
            else:
                # Default to patrol
                ai_ship.current_state = AIState.PATROL
                return self._decide_patrol_action(ai_ship, situation, effective_aggression)
                
        except Exception as e:
            logger.error(f"Error in AI decision making: {e}")
            return AIDecision(
                action_type="patrol",
                target_id=None,
                parameters={},
                priority=0.1,
                reasoning="AI error - defaulting to patrol"
            )
    
    def _assess_situation(self, ai_ship: AIShipData, 
                         nearby_objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess current tactical situation"""
        try:
            enemies = []
            allies = []
            threats = []
            resources = []
            
            for obj in nearby_objects:
                obj_distance = distance(ai_ship.position, 
                                      Coordinate(obj.get("x", 0), obj.get("y", 0)))
                
                if obj.get("type") == "ship":
                    if obj.get("is_hostile", False):
                        enemies.append({
                            "id": obj["id"],
                            "distance": obj_distance,
                            "threat_level": self._calculate_threat_level(obj, ai_ship)
                        })
                    else:
                        allies.append({
                            "id": obj["id"],
                            "distance": obj_distance
                        })
                
                elif obj.get("type") == "mine":
                    threats.append({
                        "id": obj["id"],
                        "type": "mine",
                        "distance": obj_distance,
                        "threat_level": 0.7
                    })
                
                elif obj.get("type") == "planet":
                    if obj.get("is_hostile", False):
                        enemies.append({
                            "id": obj["id"],
                            "type": "planet",
                            "distance": obj_distance,
                            "threat_level": 0.3
                        })
                    else:
                        resources.append({
                            "id": obj["id"],
                            "type": "planet",
                            "distance": obj_distance
                        })
            
            return {
                "enemies": enemies,
                "allies": allies,
                "threats": threats,
                "resources": resources,
                "enemy_count": len(enemies),
                "threat_level": sum([e.get("threat_level", 0) for e in enemies + threats]),
                "closest_enemy": min(enemies, key=lambda x: x["distance"]) if enemies else None
            }
            
        except Exception as e:
            logger.error(f"Error assessing situation: {e}")
            return {"enemies": [], "allies": [], "threats": [], "resources": [], 
                   "enemy_count": 0, "threat_level": 0.0, "closest_enemy": None}
    
    def _calculate_threat_level(self, enemy: Dict[str, Any], ai_ship: AIShipData) -> float:
        """Calculate threat level of an enemy"""
        try:
            threat_level = 0.5  # Base threat
            
            # Ship class comparison
            enemy_class = enemy.get("ship_class", 1)
            class_ratio = enemy_class / ai_ship.ship_class
            threat_level *= class_ratio
            
            # Distance factor
            enemy_distance = enemy.get("distance", 100000.0)
            if enemy_distance < 50000:
                threat_level += 0.3
            elif enemy_distance < 100000:
                threat_level += 0.1
            
            # Enemy damage affects threat (damaged enemies less threatening)
            enemy_damage = enemy.get("damage", 0.0)
            damage_factor = 1.0 - (enemy_damage / 200.0)  # Max 50% reduction
            threat_level *= damage_factor
            
            return min(1.0, max(0.1, threat_level))
            
        except Exception as e:
            logger.error(f"Error calculating threat level: {e}")
            return 0.5
    
    def _decide_idle_action(self, ai_ship: AIShipData, situation: Dict[str, Any], 
                           aggression: float) -> AIDecision:
        """Decide action when idle"""
        if situation["enemy_count"] > 0 and aggression > 0.3:
            ai_ship.current_state = AIState.HUNT
            return AIDecision(
                action_type="hunt",
                target_id=situation["closest_enemy"]["id"] if situation["closest_enemy"] else None,
                parameters={},
                priority=0.8,
                reasoning="Enemies detected - switching to hunt mode"
            )
        else:
            ai_ship.current_state = AIState.PATROL
            return AIDecision(
                action_type="patrol",
                target_id=None,
                parameters={"patrol_radius": 100000.0},
                priority=0.3,
                reasoning="No immediate threats - beginning patrol"
            )
    
    def _decide_patrol_action(self, ai_ship: AIShipData, situation: Dict[str, Any], 
                             aggression: float) -> AIDecision:
        """Decide action when patrolling"""
        if situation["enemy_count"] > 0:
            if aggression > 0.5:
                ai_ship.current_state = AIState.HUNT
                return AIDecision(
                    action_type="hunt",
                    target_id=situation["closest_enemy"]["id"] if situation["closest_enemy"] else None,
                    parameters={},
                    priority=0.7,
                    reasoning="Enemy contact - engaging hunt mode"
                )
            else:
                # Continue patrolling but be alert
                return AIDecision(
                    action_type="patrol_alert",
                    target_id=None,
                    parameters={"alert_level": 0.8},
                    priority=0.5,
                    reasoning="Enemy detected but maintaining defensive posture"
                )
        
        return AIDecision(
            action_type="patrol",
            target_id=None,
            parameters={"patrol_radius": 150000.0},
            priority=0.3,
            reasoning="Continuing patrol sweep"
        )
    
    def _decide_hunt_action(self, ai_ship: AIShipData, situation: Dict[str, Any], 
                           aggression: float) -> AIDecision:
        """Decide action when hunting"""
        if not situation["closest_enemy"]:
            ai_ship.current_state = AIState.PATROL
            return AIDecision(
                action_type="patrol",
                target_id=None,
                parameters={},
                priority=0.4,
                reasoning="No targets found - returning to patrol"
            )
        
        closest_enemy = situation["closest_enemy"]
        
        # Check if in attack range
        if closest_enemy["distance"] < self.engagement_range:
            ai_ship.current_state = AIState.ATTACK
            ai_ship.target_id = closest_enemy["id"]
            return AIDecision(
                action_type="engage",
                target_id=closest_enemy["id"],
                parameters={"engagement_range": self.engagement_range},
                priority=0.9,
                reasoning="Target in range - engaging"
            )
        
        # Continue hunting
        return AIDecision(
            action_type="pursue",
            target_id=closest_enemy["id"],
            parameters={"max_pursuit_range": 300000.0},
            priority=0.6,
            reasoning="Pursuing target"
        )
    
    def _decide_attack_action(self, ai_ship: AIShipData, situation: Dict[str, Any], 
                             caution: float) -> AIDecision:
        """Decide action when attacking"""
        # Check if we should retreat
        if ai_ship.damage > (self.retreat_threshold * 100):
            ai_ship.current_state = AIState.RETREAT
            return AIDecision(
                action_type="retreat",
                target_id=None,
                parameters={"retreat_distance": 200000.0},
                priority=0.9,
                reasoning="Heavy damage - retreating"
            )
        
        # Check if target still exists and is in range
        if not ai_ship.target_id:
            ai_ship.current_state = AIState.HUNT
            return AIDecision(
                action_type="hunt",
                target_id=None,
                parameters={},
                priority=0.5,
                reasoning="Lost target - resuming hunt"
            )
        
        # Continue attack
        weapon_choice = self._choose_weapon(ai_ship, situation)
        return AIDecision(
            action_type="attack",
            target_id=ai_ship.target_id,
            parameters={
                "weapon_type": weapon_choice,
                "attack_pattern": self._choose_attack_pattern(ai_ship)
            },
            priority=1.0,
            reasoning="Continuing attack on target"
        )
    
    def _decide_retreat_action(self, ai_ship: AIShipData, 
                              situation: Dict[str, Any]) -> AIDecision:
        """Decide action when retreating"""
        # If damage is low enough, consider re-engaging
        if ai_ship.damage < (self.retreat_threshold * 50):  # Half the retreat threshold
            if situation["enemy_count"] == 0:
                ai_ship.current_state = AIState.PATROL
                return AIDecision(
                    action_type="patrol",
                    target_id=None,
                    parameters={},
                    priority=0.4,
                    reasoning="Damage repaired and no enemies - resuming patrol"
                )
        
        # Continue retreating
        return AIDecision(
            action_type="retreat",
            target_id=None,
            parameters={"retreat_speed": "maximum"},
            priority=0.8,
            reasoning="Continuing tactical withdrawal"
        )
    
    def _decide_repair_action(self, ai_ship: AIShipData, 
                             situation: Dict[str, Any]) -> AIDecision:
        """Decide action when repairing"""
        if ai_ship.damage < 20.0:  # Repairs complete
            ai_ship.current_state = AIState.PATROL
            return AIDecision(
                action_type="patrol",
                target_id=None,
                parameters={},
                priority=0.4,
                reasoning="Repairs complete - resuming operations"
            )
        
        return AIDecision(
            action_type="repair",
            target_id=None,
            parameters={"repair_priority": "hull"},
            priority=0.7,
            reasoning="Continuing repairs"
        )
    
    def _choose_weapon(self, ai_ship: AIShipData, situation: Dict[str, Any]) -> str:
        """Choose optimal weapon for current situation"""
        try:
            # Simple weapon selection logic
            if ai_ship.energy > 500:
                return "phasers"
            elif ai_ship.energy > 200:
                return "torpedoes"
            else:
                return "missiles"
                
        except Exception as e:
            logger.error(f"Error choosing weapon: {e}")
            return "phasers"
    
    def _choose_attack_pattern(self, ai_ship: AIShipData) -> str:
        """Choose attack pattern based on AI personality"""
        try:
            if ai_ship.personality == AIPersonality.AGGRESSIVE:
                return "frontal_assault"
            elif ai_ship.personality == AIPersonality.TACTICAL:
                return "flanking_maneuver"
            elif ai_ship.personality == AIPersonality.DEFENSIVE:
                return "defensive_fire"
            else:
                return "standard_attack"
                
        except Exception as e:
            logger.error(f"Error choosing attack pattern: {e}")
            return "standard_attack"


class CybertronAI(CombatAI):
    """Cybertron AI system - aggressive combat AI"""
    
    def __init__(self):
        super().__init__()
        self.ai_type = "CYBORG"
        self.default_personality = AIPersonality.AGGRESSIVE
        self.skill_base = 75  # Cyborgs are skilled fighters
        
        # Cybertron-specific parameters
        self.update_frequency = 3  # Update every 3 ticks
        self.memory_duration = 100  # Remember targets for 100 ticks
        self.coordination_range = 200000.0  # Coordinate with other cyborgs in range
    
    def create_cybertron_ship(self, ship_id: str, ship_class: int, 
                             position: Coordinate, skill_level: Optional[int] = None) -> AIShipData:
        """Create a new Cybertron AI ship"""
        try:
            # Determine personality based on ship class
            if ship_class >= 9:  # High-end cyborg ships
                personality = AIPersonality.TACTICAL
                aggression = 0.8
                caution = 0.4
            else:
                personality = AIPersonality.AGGRESSIVE
                aggression = 0.9
                caution = 0.2
            
            # Skill level affects AI effectiveness
            effective_skill = skill_level or (self.skill_base + random.randint(-10, 15))
            
            return AIShipData(
                ship_id=ship_id,
                ship_class=ship_class,
                ai_type=self.ai_type,
                personality=personality,
                current_state=AIState.PATROL,
                position=position,
                heading=random.uniform(0, 360),
                speed=0.0,
                energy=50000,
                damage=0.0,
                shields=0,
                target_id=None,
                last_action=datetime.utcnow(),
                decision_cooldown=0,
                skill_level=effective_skill,
                aggression=aggression,
                caution=caution
            )
            
        except Exception as e:
            logger.error(f"Error creating Cybertron ship: {e}")
            return None
    
    def process_cybertron_coordination(self, cyborg_ships: List[AIShipData]) -> List[AIDecision]:
        """Process coordination between Cybertron ships"""
        try:
            coordination_decisions = []
            
            # Group cyborgs by proximity
            groups = self._group_cyborgs_by_proximity(cyborg_ships)
            
            for group in groups:
                if len(group) > 1:
                    # Coordinate group tactics
                    group_decision = self._coordinate_group_tactics(group)
                    if group_decision:
                        coordination_decisions.extend(group_decision)
            
            return coordination_decisions
            
        except Exception as e:
            logger.error(f"Error processing Cybertron coordination: {e}")
            return []
    
    def _group_cyborgs_by_proximity(self, cyborg_ships: List[AIShipData]) -> List[List[AIShipData]]:
        """Group cyborg ships by proximity for coordination"""
        try:
            groups = []
            ungrouped = cyborg_ships.copy()
            
            while ungrouped:
                current_ship = ungrouped.pop(0)
                current_group = [current_ship]
                
                # Find nearby cyborgs
                to_remove = []
                for other_ship in ungrouped:
                    if distance(current_ship.position, other_ship.position) <= self.coordination_range:
                        current_group.append(other_ship)
                        to_remove.append(other_ship)
                
                # Remove grouped ships from ungrouped list
                for ship in to_remove:
                    ungrouped.remove(ship)
                
                groups.append(current_group)
            
            return groups
            
        except Exception as e:
            logger.error(f"Error grouping cyborgs: {e}")
            return []
    
    def _coordinate_group_tactics(self, group: List[AIShipData]) -> List[AIDecision]:
        """Coordinate tactics for a group of cyborgs"""
        try:
            decisions = []
            
            # Assign roles based on ship capabilities
            leader = max(group, key=lambda s: s.skill_level)
            
            for ship in group:
                if ship == leader:
                    # Leader coordinates and calls targets
                    decisions.append(AIDecision(
                        action_type="coordinate",
                        target_id=None,
                        parameters={"role": "leader", "group_size": len(group)},
                        priority=0.6,
                        reasoning="Acting as group leader"
                    ))
                else:
                    # Followers support leader
                    decisions.append(AIDecision(
                        action_type="support",
                        target_id=leader.ship_id,
                        parameters={"role": "support", "leader": leader.ship_id},
                        priority=0.5,
                        reasoning="Supporting group leader"
                    ))
            
            return decisions
            
        except Exception as e:
            logger.error(f"Error coordinating group tactics: {e}")
            return []


class DroidAI(CombatAI):
    """Droid AI system - specialized task-focused AI"""
    
    def __init__(self):
        super().__init__()
        self.ai_type = "DROID"
        self.default_personality = AIPersonality.DEFENSIVE
        self.skill_base = 40  # Droids are less combat-capable
        
        # Droid-specific parameters
        self.update_frequency = 5  # Update every 5 ticks (slower than cyborgs)
        self.task_focus = 0.8  # Droids focus on their assigned tasks
        self.combat_avoidance = 0.7  # Droids prefer to avoid combat
    
    def create_droid_ship(self, ship_id: str, ship_class: int, 
                         position: Coordinate, task_type: str = "mining") -> AIShipData:
        """Create a new Droid AI ship"""
        try:
            # Determine personality based on task
            if task_type == "mining":
                personality = AIPersonality.COWARD  # Mining droids avoid combat
                aggression = 0.1
                caution = 0.9
            elif task_type == "scout":
                personality = AIPersonality.DEFENSIVE  # Scout droids are cautious
                aggression = 0.2
                caution = 0.8
            else:
                personality = AIPersonality.DEFENSIVE
                aggression = 0.3
                caution = 0.7
            
            skill_level = self.skill_base + random.randint(-15, 10)
            
            return AIShipData(
                ship_id=ship_id,
                ship_class=ship_class,
                ai_type=self.ai_type,
                personality=personality,
                current_state=AIState.IDLE,
                position=position,
                heading=random.uniform(0, 360),
                speed=0.0,
                energy=30000,  # Droids have less energy
                damage=0.0,
                shields=0,
                target_id=None,
                last_action=datetime.utcnow(),
                decision_cooldown=0,
                skill_level=skill_level,
                aggression=aggression,
                caution=caution
            )
            
        except Exception as e:
            logger.error(f"Error creating Droid ship: {e}")
            return None
    
    def process_droid_task(self, droid: AIShipData, task_type: str, 
                          task_parameters: Dict[str, Any]) -> AIDecision:
        """Process droid-specific task"""
        try:
            if task_type == "mining":
                return self._process_mining_task(droid, task_parameters)
            elif task_type == "scout":
                return self._process_scout_task(droid, task_parameters)
            elif task_type == "transport":
                return self._process_transport_task(droid, task_parameters)
            else:
                return AIDecision(
                    action_type="idle",
                    target_id=None,
                    parameters={},
                    priority=0.1,
                    reasoning="Unknown task type"
                )
                
        except Exception as e:
            logger.error(f"Error processing droid task: {e}")
            return AIDecision(
                action_type="idle",
                target_id=None,
                parameters={},
                priority=0.1,
                reasoning="Task processing error"
            )
    
    def _process_mining_task(self, droid: AIShipData, parameters: Dict[str, Any]) -> AIDecision:
        """Process mining droid task"""
        # Mining droids look for planets with resources
        target_planet = parameters.get("target_planet")
        
        if target_planet:
            return AIDecision(
                action_type="mine_resources",
                target_id=target_planet,
                parameters={"mining_efficiency": droid.skill_level / 100.0},
                priority=0.8,
                reasoning="Continuing mining operations"
            )
        else:
            return AIDecision(
                action_type="search_resources",
                target_id=None,
                parameters={"search_radius": 200000.0},
                priority=0.6,
                reasoning="Searching for mining opportunities"
            )
    
    def _process_scout_task(self, droid: AIShipData, parameters: Dict[str, Any]) -> AIDecision:
        """Process scout droid task"""
        # Scout droids explore and report back
        return AIDecision(
            action_type="scout_area",
            target_id=None,
            parameters={
                "scout_radius": 300000.0,
                "stealth_mode": True,
                "report_frequency": 10
            },
            priority=0.7,
            reasoning="Conducting reconnaissance mission"
        )
    
    def _process_transport_task(self, droid: AIShipData, parameters: Dict[str, Any]) -> AIDecision:
        """Process transport droid task"""
        # Transport droids move cargo between locations
        destination = parameters.get("destination")
        
        if destination:
            return AIDecision(
                action_type="transport_cargo",
                target_id=destination,
                parameters={"cargo_priority": "high"},
                priority=0.8,
                reasoning="Delivering cargo to destination"
            )
        else:
            return AIDecision(
                action_type="await_cargo",
                target_id=None,
                parameters={},
                priority=0.3,
                reasoning="Waiting for cargo assignment"
            )


class AIManager:
    """Main AI management system"""
    
    def __init__(self):
        self.cybertron_ai = CybertronAI()
        self.droid_ai = DroidAI()
        self.active_ai_ships: Dict[str, AIShipData] = {}
        self.ai_decisions: Dict[str, AIDecision] = {}
    
    def create_ai_ship(self, ship_id: str, ship_class: int, ai_type: str,
                      position: Coordinate, **kwargs) -> bool:
        """Create a new AI-controlled ship"""
        try:
            if ai_type == "CYBORG":
                ai_ship = self.cybertron_ai.create_cybertron_ship(
                    ship_id, ship_class, position, kwargs.get("skill_level")
                )
            elif ai_type == "DROID":
                ai_ship = self.droid_ai.create_droid_ship(
                    ship_id, ship_class, position, kwargs.get("task_type", "mining")
                )
            else:
                logger.error(f"Unknown AI type: {ai_type}")
                return False
            
            if ai_ship:
                self.active_ai_ships[ship_id] = ai_ship
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error creating AI ship: {e}")
            return False
    
    def process_ai_tick(self, nearby_objects_by_ship: Dict[str, List[Dict[str, Any]]],
                       game_state: Dict[str, Any]) -> Dict[str, AIDecision]:
        """Process AI decisions for all AI ships"""
        try:
            new_decisions = {}
            
            # Process individual AI decisions
            for ship_id, ai_ship in self.active_ai_ships.items():
                if ai_ship.decision_cooldown <= 0:
                    nearby_objects = nearby_objects_by_ship.get(ship_id, [])
                    
                    if ai_ship.ai_type == "CYBORG":
                        decision = self.cybertron_ai.make_decision(ai_ship, nearby_objects, game_state)
                        ai_ship.decision_cooldown = self.cybertron_ai.update_frequency
                    else:  # DROID
                        decision = self.droid_ai.make_decision(ai_ship, nearby_objects, game_state)
                        ai_ship.decision_cooldown = self.droid_ai.update_frequency
                    
                    new_decisions[ship_id] = decision
                    ai_ship.last_action = datetime.utcnow()
                else:
                    ai_ship.decision_cooldown -= 1
            
            # Process Cybertron coordination
            cyborg_ships = [ship for ship in self.active_ai_ships.values() 
                          if ship.ai_type == "CYBORG"]
            if cyborg_ships:
                coordination_decisions = self.cybertron_ai.process_cybertron_coordination(cyborg_ships)
                # Apply coordination decisions (simplified)
                for decision in coordination_decisions:
                    if decision.target_id and decision.target_id in self.active_ai_ships:
                        # Update coordination parameters
                        pass
            
            self.ai_decisions.update(new_decisions)
            return new_decisions
            
        except Exception as e:
            logger.error(f"Error processing AI tick: {e}")
            return {}
    
    def get_ai_ship_status(self, ship_id: str) -> Optional[Dict[str, Any]]:
        """Get AI ship status"""
        try:
            if ship_id not in self.active_ai_ships:
                return None
            
            ai_ship = self.active_ai_ships[ship_id]
            current_decision = self.ai_decisions.get(ship_id)
            
            return {
                "ship_id": ai_ship.ship_id,
                "ai_type": ai_ship.ai_type,
                "personality": ai_ship.personality.value,
                "current_state": ai_ship.current_state.value,
                "skill_level": ai_ship.skill_level,
                "target_id": ai_ship.target_id,
                "last_decision": {
                    "action_type": current_decision.action_type,
                    "priority": current_decision.priority,
                    "reasoning": current_decision.reasoning
                } if current_decision else None
            }
            
        except Exception as e:
            logger.error(f"Error getting AI ship status: {e}")
            return None
    
    def remove_ai_ship(self, ship_id: str) -> bool:
        """Remove AI ship from management"""
        try:
            if ship_id in self.active_ai_ships:
                del self.active_ai_ships[ship_id]
            if ship_id in self.ai_decisions:
                del self.ai_decisions[ship_id]
            return True
            
        except Exception as e:
            logger.error(f"Error removing AI ship: {e}")
            return False
