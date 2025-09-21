"""
Galactic Empire - Game Balance Service

This module provides game balance calculations and adjustments based on
configuration parameters, ensuring fair and competitive gameplay.
"""

from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import logging
import math
from app.core.game_config import game_config, ConfigCategory

logger = logging.getLogger(__name__)


class BalanceFactor(Enum):
    """Balance factors that can be adjusted"""
    ENERGY_EFFICIENCY = "energy_efficiency"
    WEAPON_DAMAGE = "weapon_damage"
    SHIELD_EFFECTIVENESS = "shield_effectiveness"
    ECONOMIC_RATES = "economic_rates"
    COMBAT_SPEED = "combat_speed"
    RESOURCE_AVAILABILITY = "resource_availability"


@dataclass
class BalanceMetrics:
    """Represents balance metrics for analysis"""
    factor: BalanceFactor
    current_value: float
    target_value: float
    deviation_percent: float
    recommendation: str
    impact_level: str  # "low", "medium", "high", "critical"


@dataclass
class ShipClassBalance:
    """Ship class balance analysis"""
    ship_class: str
    energy_efficiency: float
    combat_effectiveness: float
    economic_value: float
    strategic_value: float
    balance_score: float
    recommendations: List[str]


class GameBalanceService:
    """Service for managing game balance calculations and adjustments"""
    
    def __init__(self):
        self._balance_history: List[Dict[str, Any]] = []
        self._ship_balance_cache: Dict[str, ShipClassBalance] = {}
    
    def calculate_energy_consumption(self, ship_class: str, operation: str, 
                                   base_consumption: int) -> int:
        """Calculate energy consumption with balance modifiers"""
        energy_efficiency = self.get_energy_efficiency_factor(ship_class)
        operation_modifier = self.get_operation_modifier(operation)
        
        # Apply balance factors
        consumption = int(base_consumption * energy_efficiency * operation_modifier)
        
        # Ensure minimum consumption
        return max(consumption, 1)
    
    def calculate_weapon_damage(self, weapon_type: str, base_damage: int, 
                               range_factor: float = 1.0, 
                               target_ship_class: str = "Fighter") -> int:
        """Calculate weapon damage with balance modifiers"""
        weapon_factor = self.get_weapon_damage_factor(weapon_type)
        range_modifier = self.get_range_modifier(range_factor)
        target_modifier = self.get_target_modifier(weapon_type, target_ship_class)
        
        # Calculate final damage
        damage = int(base_damage * weapon_factor * range_modifier * target_modifier)
        
        # Apply maximum damage limits
        max_damage = game_config.get_config(f"{weapon_type.lower()}_max_damage")
        return min(damage, max_damage)
    
    def calculate_shield_effectiveness(self, shield_type: int, shield_charge: int,
                                     incoming_damage: int) -> Tuple[int, int]:
        """Calculate shield effectiveness with balance modifiers"""
        shield_factor = self.get_shield_effectiveness_factor(shield_type)
        
        # Calculate absorption
        absorption = int(incoming_damage * shield_factor * (shield_charge / 10.0))
        
        # Calculate energy drain
        energy_drain = int(absorption * 0.1)  # 10% of absorbed damage as energy drain
        
        # Remaining damage after shield absorption
        remaining_damage = max(0, incoming_damage - absorption)
        
        return remaining_damage, energy_drain
    
    def calculate_economic_rates(self, item_type: str, planet_environment: int,
                               planet_population: int) -> Dict[str, float]:
        """Calculate economic rates with balance modifiers"""
        base_production_rate = game_config.get_config("item_production_base_rate")
        economic_factor = self.get_economic_factor()
        
        # Environment modifier
        env_modifier = 0.5 + (planet_environment / 100.0)  # 0.5 to 1.5 range
        
        # Population modifier
        pop_modifier = 0.8 + (planet_population / 10000.0)  # 0.8 to 1.8 range
        
        # Calculate rates
        production_rate = base_production_rate * economic_factor * env_modifier * pop_modifier
        tax_rate = game_config.get_config("planet_tax_rate") * economic_factor
        
        # Trading rates
        markup_min = game_config.get_config("trade_markup_min") * economic_factor
        markup_max = game_config.get_config("trade_markup_max") * economic_factor
        
        return {
            "production_rate": max(0.01, production_rate),
            "tax_rate": max(0.001, min(0.5, tax_rate)),
            "markup_min": max(0.01, markup_min),
            "markup_max": max(markup_min, markup_max)
        }
    
    def calculate_scoring_multipliers(self, player_stats: Dict[str, Any]) -> Dict[str, float]:
        """Calculate scoring multipliers based on player performance"""
        base_multiplier = 1.0
        
        # Performance-based adjustments
        if player_stats.get("kill_ratio", 0) > 2.0:
            base_multiplier *= 1.2  # Reward high kill ratio
        elif player_stats.get("kill_ratio", 0) < 0.5:
            base_multiplier *= 0.8  # Reduce score for poor performance
        
        # Team coordination bonus
        if player_stats.get("team_activities", 0) > 10:
            team_bonus = game_config.get_config("team_coordination_bonus")
            base_multiplier *= (1.0 + team_bonus)
        
        # Planet control bonus
        planet_count = player_stats.get("planets_controlled", 0)
        if planet_count > 5:
            base_multiplier *= (1.0 + (planet_count - 5) * 0.1)
        
        return {
            "kill_multiplier": base_multiplier,
            "planet_multiplier": base_multiplier,
            "team_multiplier": base_multiplier
        }
    
    def analyze_game_balance(self) -> List[BalanceMetrics]:
        """Analyze current game balance and provide recommendations"""
        metrics = []
        
        # Energy efficiency analysis
        energy_metrics = self._analyze_energy_balance()
        metrics.extend(energy_metrics)
        
        # Combat balance analysis
        combat_metrics = self._analyze_combat_balance()
        metrics.extend(combat_metrics)
        
        # Economic balance analysis
        economic_metrics = self._analyze_economic_balance()
        metrics.extend(economic_metrics)
        
        return metrics
    
    def _analyze_energy_balance(self) -> List[BalanceMetrics]:
        """Analyze energy system balance"""
        metrics = []
        
        # Check energy regeneration vs consumption
        regen_rate = game_config.get_config("energy_recharge_rate")
        avg_consumption = (
            game_config.get_config("shield_energy_cost") +
            game_config.get_config("phaser_energy_cost") +
            game_config.get_config("movement_energy_cost")
        ) / 3
        
        efficiency_ratio = regen_rate / avg_consumption
        target_ratio = 0.1  # 10% of consumption should be regenerated per tick
        
        if efficiency_ratio < target_ratio * 0.5:
            metrics.append(BalanceMetrics(
                factor=BalanceFactor.ENERGY_EFFICIENCY,
                current_value=efficiency_ratio,
                target_value=target_ratio,
                deviation_percent=((target_ratio - efficiency_ratio) / target_ratio) * 100,
                recommendation="Increase energy recharge rate or decrease consumption costs",
                impact_level="high"
            ))
        
        return metrics
    
    def _analyze_combat_balance(self) -> List[BalanceMetrics]:
        """Analyze combat system balance"""
        metrics = []
        
        # Check weapon damage vs shield effectiveness
        avg_weapon_damage = (
            game_config.get_config("torpedo_max_damage") +
            game_config.get_config("missile_max_damage") +
            game_config.get_config("ion_cannon_max_damage")
        ) / 3
        
        shield_effectiveness = self.get_shield_effectiveness_factor(5)  # Standard shield
        
        combat_ratio = avg_weapon_damage * shield_effectiveness
        target_ratio = 50.0  # Balanced damage vs protection
        
        if abs(combat_ratio - target_ratio) > target_ratio * 0.3:
            metrics.append(BalanceMetrics(
                factor=BalanceFactor.WEAPON_DAMAGE,
                current_value=combat_ratio,
                target_value=target_ratio,
                deviation_percent=((target_ratio - combat_ratio) / target_ratio) * 100,
                recommendation="Adjust weapon damage or shield effectiveness for better balance",
                impact_level="medium"
            ))
        
        return metrics
    
    def _analyze_economic_balance(self) -> List[BalanceMetrics]:
        """Analyze economic system balance"""
        metrics = []
        
        # Check production vs consumption rates
        production_rate = game_config.get_config("item_production_base_rate")
        start_cash = game_config.get_config("start_cash")
        
        # Economic health indicator
        economic_ratio = production_rate * (start_cash / 1000000)
        target_ratio = 2.0  # Balanced economy
        
        if economic_ratio < target_ratio * 0.7:
            metrics.append(BalanceMetrics(
                factor=BalanceFactor.ECONOMIC_RATES,
                current_value=economic_ratio,
                target_value=target_ratio,
                deviation_percent=((target_ratio - economic_ratio) / target_ratio) * 100,
                recommendation="Increase production rates or starting resources",
                impact_level="medium"
            ))
        
        return metrics
    
    def get_ship_class_balance(self, ship_class: str) -> ShipClassBalance:
        """Get balance analysis for a specific ship class"""
        if ship_class in self._ship_balance_cache:
            return self._ship_balance_cache[ship_class]
        
        # Calculate balance metrics
        energy_efficiency = self.get_energy_efficiency_factor(ship_class)
        combat_effectiveness = self.get_combat_effectiveness_factor(ship_class)
        economic_value = self.get_economic_value_factor(ship_class)
        strategic_value = self.get_strategic_value_factor(ship_class)
        
        # Calculate overall balance score
        balance_score = (energy_efficiency + combat_effectiveness + 
                        economic_value + strategic_value) / 4
        
        # Generate recommendations
        recommendations = []
        if energy_efficiency < 0.8:
            recommendations.append("Consider reducing energy consumption")
        if combat_effectiveness < 0.8:
            recommendations.append("Consider increasing weapon effectiveness")
        if economic_value < 0.8:
            recommendations.append("Consider reducing ship cost or increasing cargo capacity")
        if strategic_value < 0.8:
            recommendations.append("Consider adding special abilities or improving speed")
        
        balance = ShipClassBalance(
            ship_class=ship_class,
            energy_efficiency=energy_efficiency,
            combat_effectiveness=combat_effectiveness,
            economic_value=economic_value,
            strategic_value=strategic_value,
            balance_score=balance_score,
            recommendations=recommendations
        )
        
        self._ship_balance_cache[ship_class] = balance
        return balance
    
    def get_energy_efficiency_factor(self, ship_class: str) -> float:
        """Get energy efficiency factor for ship class"""
        # Base efficiency by ship class
        efficiency_map = {
            "Interceptor": 1.2,  # Fast and efficient
            "Scout": 1.1,        # Good efficiency
            "Fighter": 1.0,      # Standard
            "Destroyer": 0.9,    # Slightly less efficient
            "Cruiser": 0.8,      # Less efficient
            "Battleship": 0.7,   # Heavy ship, less efficient
            "Dreadnought": 0.6,  # Very heavy, less efficient
            "Flagship": 0.5,     # Massive ship, least efficient
            "Cyborg": 1.3,       # AI efficiency bonus
            "Droid": 1.4         # Best efficiency
        }
        return efficiency_map.get(ship_class, 1.0)
    
    def get_weapon_damage_factor(self, weapon_type: str) -> float:
        """Get weapon damage factor"""
        weapon_factors = {
            "phaser": 1.0,
            "hyper_phaser": 1.5,
            "torpedo": game_config.get_config("torpedo_damage_factor"),
            "missile": game_config.get_config("missile_damage_factor"),
            "ion_cannon": 1.0,
            "mine": 1.0
        }
        return weapon_factors.get(weapon_type.lower(), 1.0)
    
    def get_shield_effectiveness_factor(self, shield_type: int) -> float:
        """Get shield effectiveness factor"""
        # Shield types 0-19 with varying effectiveness
        if shield_type <= 5:
            return 0.3  # Basic shields
        elif shield_type <= 10:
            return 0.5  # Standard shields
        elif shield_type <= 15:
            return 0.7  # Advanced shields
        else:
            return 0.9  # Elite shields
    
    def get_economic_factor(self) -> float:
        """Get economic balance factor"""
        # Can be adjusted based on game state
        return 1.0
    
    def get_operation_modifier(self, operation: str) -> float:
        """Get operation-specific modifier"""
        modifiers = {
            "rotation": 1.0,
            "acceleration": 1.0,
            "movement": 1.0,
            "phaser_fire": 1.0,
            "hyper_phaser_fire": 1.5,
            "torpedo_fire": 1.2,
            "missile_fire": 1.2,
            "shield_up": 1.0,
            "cloaking": 2.0,
            "scanning": 0.5
        }
        return modifiers.get(operation, 1.0)
    
    def get_range_modifier(self, range_factor: float) -> float:
        """Get range-based damage modifier"""
        # Damage decreases with range
        if range_factor <= 0.5:
            return 1.0  # Close range, full damage
        elif range_factor <= 0.8:
            return 0.8  # Medium range, reduced damage
        else:
            return 0.5  # Long range, significantly reduced damage
    
    def get_target_modifier(self, weapon_type: str, target_ship_class: str) -> float:
        """Get target-specific damage modifier"""
        # Different weapons are more effective against different targets
        effectiveness_matrix = {
            "phaser": {"Interceptor": 1.2, "Scout": 1.1, "Fighter": 1.0, 
                      "Destroyer": 0.9, "Cruiser": 0.8, "Battleship": 0.7,
                      "Dreadnought": 0.6, "Flagship": 0.5},
            "torpedo": {"Interceptor": 0.8, "Scout": 0.9, "Fighter": 1.0,
                       "Destroyer": 1.2, "Cruiser": 1.3, "Battleship": 1.4,
                       "Dreadnought": 1.5, "Flagship": 1.6},
            "missile": {"Interceptor": 1.1, "Scout": 1.0, "Fighter": 1.2,
                       "Destroyer": 1.0, "Cruiser": 0.9, "Battleship": 0.8,
                       "Dreadnought": 0.7, "Flagship": 0.6}
        }
        
        weapon_effectiveness = effectiveness_matrix.get(weapon_type.lower(), {})
        return weapon_effectiveness.get(target_ship_class, 1.0)
    
    def get_combat_effectiveness_factor(self, ship_class: str) -> float:
        """Get combat effectiveness factor for ship class"""
        effectiveness_map = {
            "Interceptor": 0.6,   # Fast but lightly armed
            "Scout": 0.4,         # Not designed for combat
            "Fighter": 0.8,       # Good combat ship
            "Destroyer": 1.0,     # Standard combat effectiveness
            "Cruiser": 1.2,       # Above average
            "Battleship": 1.4,    # Strong combat ship
            "Dreadnought": 1.6,   # Very strong
            "Flagship": 1.8,      # Most powerful
            "Cyborg": 1.3,        # AI combat bonus
            "Droid": 0.7          # Moderate combat ability
        }
        return effectiveness_map.get(ship_class, 1.0)
    
    def get_economic_value_factor(self, ship_class: str) -> float:
        """Get economic value factor for ship class"""
        # Based on cost vs capabilities
        value_map = {
            "Interceptor": 1.2,   # Good value
            "Scout": 1.0,         # Standard value
            "Fighter": 1.1,       # Good value
            "Destroyer": 1.0,     # Standard value
            "Cruiser": 0.9,       # Slightly expensive
            "Battleship": 0.8,    # Expensive
            "Dreadnought": 0.7,   # Very expensive
            "Flagship": 0.6,      # Most expensive
            "Cyborg": 0.8,        # AI ships are expensive
            "Droid": 1.1          # Good value for AI
        }
        return value_map.get(ship_class, 1.0)
    
    def get_strategic_value_factor(self, ship_class: str) -> float:
        """Get strategic value factor for ship class"""
        strategic_map = {
            "Interceptor": 1.3,   # High strategic value (speed)
            "Scout": 1.4,         # Highest strategic value (information)
            "Fighter": 0.9,       # Standard strategic value
            "Destroyer": 1.0,     # Standard strategic value
            "Cruiser": 1.1,       # Good strategic value
            "Battleship": 1.2,    # High strategic value
            "Dreadnought": 1.3,   # Very high strategic value
            "Flagship": 1.5,      # Highest strategic value
            "Cyborg": 1.0,        # Standard for AI
            "Droid": 0.8          # Lower strategic value for AI
        }
        return strategic_map.get(ship_class, 1.0)
    
    def log_balance_adjustment(self, adjustment_type: str, old_value: Any, 
                              new_value: Any, reason: str, admin_user: str):
        """Log balance adjustment for audit trail"""
        adjustment_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": adjustment_type,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
            "admin_user": admin_user
        }
        self._balance_history.append(adjustment_record)
        
        # Keep only last 500 adjustments
        if len(self._balance_history) > 500:
            self._balance_history = self._balance_history[-500:]
        
        logger.info(f"Balance adjustment: {adjustment_type} changed from {old_value} to {new_value} by {admin_user}")
    
    def get_balance_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get balance adjustment history"""
        return self._balance_history[-limit:]


# Global balance service instance
balance_service = GameBalanceService()


def get_balance_service() -> GameBalanceService:
    """Get the global balance service instance"""
    return balance_service
