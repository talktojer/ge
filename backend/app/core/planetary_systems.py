"""
Galactic Empire - Planetary Management Systems

This module implements planet colonization, resource management, economy,
population, taxation, and beacon systems based on the original game.
"""

import logging
import math
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..models.planet import Planet, PlanetItem, Sector
from ..models.item import ItemType
from ..models.user import User

logger = logging.getLogger(__name__)


class PlanetStatus(Enum):
    """Planet status enumeration"""
    UNCOLONIZED = "uncolonized"
    COLONIZED = "colonized"
    UNDER_ATTACK = "under_attack"
    DEFENDED = "defended"
    ABANDONED = "abandoned"


class ResourceType(Enum):
    """Resource type enumeration"""
    POOR = 1
    FAIR = 2
    GOOD = 3
    EXCELLENT = 4
    SUPERIOR = 5


class EnvironmentType(Enum):
    """Environment type enumeration"""
    HOSTILE = 1
    POOR = 2
    FAIR = 3
    GOOD = 4
    EXCELLENT = 5


@dataclass
class PlanetStats:
    """Planet statistics and characteristics"""
    planet_id: int
    name: str
    owner_id: Optional[int]
    position: Tuple[float, float]
    sector: Tuple[int, int]
    environment: EnvironmentType
    resource: ResourceType
    population: int
    cash: int
    debt: int
    tax_rate: int
    tax_collected: int
    technology_level: int
    beacon_message: str
    last_attack: Optional[datetime]


@dataclass
class ProductionResult:
    """Result of planet production processing"""
    planet_id: int
    items_produced: Dict[int, int]  # item_type_id -> quantity
    population_change: int
    cash_generated: int
    tax_collected: int
    total_production_value: int


@dataclass
class ColonizationResult:
    """Result of planet colonization attempt"""
    success: bool
    planet_id: Optional[int]
    message: str
    cost: int
    population_sent: int


class PlanetaryEconomy:
    """Planetary economy and production system"""
    
    def __init__(self):
        # Base production rates per environment type
        self.environment_modifiers = {
            EnvironmentType.HOSTILE: 0.5,
            EnvironmentType.POOR: 0.7,
            EnvironmentType.FAIR: 1.0,
            EnvironmentType.GOOD: 1.3,
            EnvironmentType.EXCELLENT: 1.6
        }
        
        # Base resource extraction rates per resource type
        self.resource_modifiers = {
            ResourceType.POOR: 0.6,
            ResourceType.FAIR: 0.8,
            ResourceType.GOOD: 1.0,
            ResourceType.EXCELLENT: 1.4,
            ResourceType.SUPERIOR: 1.8
        }
        
        # Item production base rates (per 1000 population per tick)
        self.base_production_rates = {
            1: 10,   # Food
            2: 5,    # Medicine
            3: 8,    # Fuel
            4: 6,    # Equipment
            5: 12,   # Ore
            6: 4,    # Weapons
            7: 3,    # Luxury items
            8: 7,    # Supplies
            9: 2,    # Heavy machinery
            10: 5,   # Electronics
            11: 15,  # Raw materials
            12: 6,   # Chemicals
            13: 8,   # Textiles
            14: 1    # Information
        }
        
        # Tax rates and population growth
        self.max_tax_rate = 50  # Maximum tax rate percentage
        self.base_population_growth = 0.02  # 2% per tick under ideal conditions
        self.colonization_cost_base = 100000
        self.min_colonization_population = 1000
    
    def calculate_production(self, planet: Planet, planet_items: List[PlanetItem], 
                           population: int) -> ProductionResult:
        """Calculate planet production for one tick"""
        try:
            items_produced = {}
            total_value = 0
            
            # Get environment and resource modifiers
            env_modifier = self.environment_modifiers.get(
                EnvironmentType(planet.environment), 1.0
            )
            resource_modifier = self.resource_modifiers.get(
                ResourceType(planet.resource), 1.0
            )
            
            # Calculate population factor (production per 1000 people)
            population_factor = population / 1000.0
            
            # Process each item type being produced
            for planet_item in planet_items:
                if planet_item.rate <= 0:
                    continue
                
                item_type_id = planet_item.item_id
                production_rate = planet_item.rate
                
                # Calculate base production
                base_rate = self.base_production_rates.get(item_type_id, 5)
                
                # Apply all modifiers
                actual_production = (base_rate * production_rate * 
                                   population_factor * env_modifier * 
                                   resource_modifier)
                
                # Add some randomness (±20%)
                random_factor = random.uniform(0.8, 1.2)
                final_production = int(actual_production * random_factor)
                
                if final_production > 0:
                    items_produced[item_type_id] = final_production
                    # Estimate value (would need item prices)
                    total_value += final_production * 100  # Placeholder value
            
            # Calculate population growth
            growth_rate = self.base_population_growth * env_modifier
            # Tax rate affects population growth negatively
            tax_penalty = (planet.tax_rate / 100.0) * 0.5
            actual_growth_rate = max(0.001, growth_rate - tax_penalty)
            
            population_change = int(population * actual_growth_rate)
            
            # Calculate cash generation and tax collection
            cash_per_person = 10 * env_modifier * resource_modifier
            gross_income = int(population * cash_per_person)
            tax_collected = int(gross_income * (planet.tax_rate / 100.0))
            cash_generated = gross_income - tax_collected
            
            return ProductionResult(
                planet_id=planet.id,
                items_produced=items_produced,
                population_change=population_change,
                cash_generated=cash_generated,
                tax_collected=tax_collected,
                total_production_value=total_value
            )
            
        except Exception as e:
            logger.error(f"Error calculating production for planet {planet.id}: {e}")
            return ProductionResult(
                planet_id=planet.id,
                items_produced={},
                population_change=0,
                cash_generated=0,
                tax_collected=0,
                total_production_value=0
            )
    
    def calculate_colonization_cost(self, planet: Planet, population_to_send: int) -> int:
        """Calculate cost to colonize a planet"""
        try:
            # Base cost
            base_cost = self.colonization_cost_base
            
            # Environment affects cost
            env_modifier = {
                EnvironmentType.HOSTILE: 2.0,
                EnvironmentType.POOR: 1.5,
                EnvironmentType.FAIR: 1.0,
                EnvironmentType.GOOD: 0.8,
                EnvironmentType.EXCELLENT: 0.6
            }.get(EnvironmentType(planet.environment), 1.0)
            
            # Population cost
            population_cost = population_to_send * 50
            
            # Distance cost (would need to calculate from ship position)
            distance_cost = 10000  # Placeholder
            
            total_cost = int((base_cost + population_cost + distance_cost) * env_modifier)
            
            return total_cost
            
        except Exception as e:
            logger.error(f"Error calculating colonization cost: {e}")
            return self.colonization_cost_base
    
    def calculate_item_prices(self, planet: Planet, item_type_id: int, 
                            base_price: int, quantity_available: int) -> Dict[str, int]:
        """Calculate buy/sell prices for items on planet"""
        try:
            # Supply and demand affects prices
            supply_factor = 1.0
            if quantity_available > 1000:
                supply_factor = 0.8  # Lots of supply = lower prices
            elif quantity_available < 100:
                supply_factor = 1.5  # Low supply = higher prices
            
            # Environment affects prices
            env_modifier = {
                EnvironmentType.HOSTILE: 1.4,
                EnvironmentType.POOR: 1.2,
                EnvironmentType.FAIR: 1.0,
                EnvironmentType.GOOD: 0.9,
                EnvironmentType.EXCELLENT: 0.8
            }.get(EnvironmentType(planet.environment), 1.0)
            
            # Calculate final prices
            buy_price = int(base_price * supply_factor * env_modifier * 0.8)  # Buy for less
            sell_price = int(base_price * supply_factor * env_modifier * 1.2)  # Sell for more
            
            return {
                "buy_price": buy_price,
                "sell_price": sell_price,
                "base_price": base_price,
                "supply_factor": supply_factor,
                "environment_modifier": env_modifier
            }
            
        except Exception as e:
            logger.error(f"Error calculating item prices: {e}")
            return {
                "buy_price": base_price,
                "sell_price": base_price,
                "base_price": base_price,
                "supply_factor": 1.0,
                "environment_modifier": 1.0
            }


class PlanetaryDefense:
    """Planetary defense and attack systems"""
    
    def __init__(self):
        # Defense factors
        self.base_defense_strength = 100
        self.population_defense_factor = 0.1  # Defense per 1000 population
        self.technology_defense_factor = 10   # Defense per tech level
        
        # Attack factors
        self.ship_attack_base = 50
        self.weapon_multipliers = {
            "phasers": 1.0,
            "torpedoes": 1.5,
            "missiles": 1.3,
            "ion_cannon": 2.0
        }
        
        # Troop and fighter factors
        self.troop_effectiveness = 5
        self.fighter_effectiveness = 3
    
    def calculate_defense_strength(self, planet: Planet, population: int, 
                                 troops: int = 0, fighters: int = 0) -> int:
        """Calculate planet defense strength"""
        try:
            # Base defense
            defense = self.base_defense_strength
            
            # Population contributes to defense
            population_defense = (population / 1000.0) * self.population_defense_factor
            defense += population_defense
            
            # Technology level contributes
            tech_defense = planet.technology * self.technology_defense_factor
            defense += tech_defense
            
            # Troops and fighters
            defense += troops * self.troop_effectiveness
            defense += fighters * self.fighter_effectiveness
            
            # Environment affects defense
            env_modifier = {
                EnvironmentType.HOSTILE: 1.3,  # Hostile environment helps defense
                EnvironmentType.POOR: 1.1,
                EnvironmentType.FAIR: 1.0,
                EnvironmentType.GOOD: 0.9,
                EnvironmentType.EXCELLENT: 0.8
            }.get(EnvironmentType(planet.environment), 1.0)
            
            final_defense = int(defense * env_modifier)
            
            return max(1, final_defense)
            
        except Exception as e:
            logger.error(f"Error calculating defense strength: {e}")
            return self.base_defense_strength
    
    def calculate_attack_damage(self, attacking_ship_class: Dict[str, Any], 
                              weapon_strength: Dict[str, float]) -> int:
        """Calculate attack damage from ship"""
        try:
            total_damage = self.ship_attack_base
            
            # Add weapon damage
            for weapon_type, strength in weapon_strength.items():
                multiplier = self.weapon_multipliers.get(weapon_type, 1.0)
                weapon_damage = strength * multiplier
                total_damage += weapon_damage
            
            # Ship class affects damage
            class_modifier = attacking_ship_class.get("damage_factor", 100) / 100.0
            total_damage *= class_modifier
            
            # Add some randomness (±30%)
            random_factor = random.uniform(0.7, 1.3)
            final_damage = int(total_damage * random_factor)
            
            return max(1, final_damage)
            
        except Exception as e:
            logger.error(f"Error calculating attack damage: {e}")
            return self.ship_attack_base
    
    def resolve_planetary_attack(self, attack_damage: int, defense_strength: int,
                               population: int) -> Dict[str, Any]:
        """Resolve planetary attack"""
        try:
            # Calculate damage ratio
            damage_ratio = attack_damage / defense_strength
            
            # Determine attack outcome
            if damage_ratio < 0.5:
                # Attack repelled
                population_loss = int(population * 0.01)  # 1% casualties
                result = "repelled"
                message = "Planetary defenses successfully repelled the attack"
                
            elif damage_ratio < 1.0:
                # Partial success
                population_loss = int(population * 0.05)  # 5% casualties
                result = "partial"
                message = "Attack caused significant damage but was ultimately repelled"
                
            elif damage_ratio < 2.0:
                # Successful attack
                population_loss = int(population * 0.15)  # 15% casualties
                result = "successful"
                message = "Attack successful - significant planetary damage"
                
            else:
                # Devastating attack
                population_loss = int(population * 0.30)  # 30% casualties
                result = "devastating"
                message = "Devastating attack - planet severely damaged"
            
            # Calculate infrastructure damage
            infrastructure_damage = min(50, int(damage_ratio * 20))
            
            return {
                "result": result,
                "message": message,
                "population_loss": population_loss,
                "infrastructure_damage": infrastructure_damage,
                "damage_ratio": damage_ratio,
                "attack_damage": attack_damage,
                "defense_strength": defense_strength
            }
            
        except Exception as e:
            logger.error(f"Error resolving planetary attack: {e}")
            return {
                "result": "error",
                "message": f"Attack resolution error: {str(e)}",
                "population_loss": 0,
                "infrastructure_damage": 0,
                "damage_ratio": 0,
                "attack_damage": attack_damage,
                "defense_strength": defense_strength
            }


class PlanetManagement:
    """Main planet management system"""
    
    def __init__(self):
        self.economy = PlanetaryEconomy()
        self.defense = PlanetaryDefense()
    
    def colonize_planet(self, planet: Planet, colonizer: User, 
                       population_to_send: int) -> ColonizationResult:
        """Attempt to colonize a planet"""
        try:
            # Check if planet is already colonized
            if planet.owner_id is not None:
                return ColonizationResult(
                    success=False,
                    planet_id=None,
                    message="Planet is already colonized",
                    cost=0,
                    population_sent=0
                )
            
            # Check minimum population requirement
            if population_to_send < self.economy.min_colonization_population:
                return ColonizationResult(
                    success=False,
                    planet_id=None,
                    message=f"Minimum {self.economy.min_colonization_population} population required",
                    cost=0,
                    population_sent=0
                )
            
            # Calculate colonization cost
            cost = self.economy.calculate_colonization_cost(planet, population_to_send)
            
            # Check if user can afford it
            if colonizer.cash < cost:
                return ColonizationResult(
                    success=False,
                    planet_id=None,
                    message=f"Insufficient funds. Cost: {cost}, Available: {colonizer.cash}",
                    cost=cost,
                    population_sent=0
                )
            
            # Check if user has enough population
            if colonizer.population < population_to_send:
                return ColonizationResult(
                    success=False,
                    planet_id=None,
                    message=f"Insufficient population. Required: {population_to_send}, Available: {colonizer.population}",
                    cost=cost,
                    population_sent=0
                )
            
            # Successful colonization
            return ColonizationResult(
                success=True,
                planet_id=planet.id,
                message=f"Successfully colonized {planet.name} with {population_to_send} colonists",
                cost=cost,
                population_sent=population_to_send
            )
            
        except Exception as e:
            logger.error(f"Error in planet colonization: {e}")
            return ColonizationResult(
                success=False,
                planet_id=None,
                message=f"Colonization error: {str(e)}",
                cost=0,
                population_sent=0
            )
    
    def process_planet_tick(self, planet: Planet, planet_items: List[PlanetItem],
                          population: int) -> ProductionResult:
        """Process planet systems for one tick"""
        return self.economy.calculate_production(planet, planet_items, population)
    
    def set_tax_rate(self, planet: Planet, new_tax_rate: int) -> Dict[str, Any]:
        """Set planet tax rate"""
        try:
            if new_tax_rate < 0 or new_tax_rate > self.economy.max_tax_rate:
                return {
                    "success": False,
                    "message": f"Tax rate must be between 0 and {self.economy.max_tax_rate}%"
                }
            
            old_rate = planet.tax_rate
            # Tax rate would be updated in the database by the service layer
            
            return {
                "success": True,
                "message": f"Tax rate changed from {old_rate}% to {new_tax_rate}%",
                "old_rate": old_rate,
                "new_rate": new_tax_rate
            }
            
        except Exception as e:
            logger.error(f"Error setting tax rate: {e}")
            return {
                "success": False,
                "message": f"Error setting tax rate: {str(e)}"
            }
    
    def set_beacon_message(self, planet: Planet, message: str) -> Dict[str, Any]:
        """Set planet beacon message"""
        try:
            if len(message) > 75:
                return {
                    "success": False,
                    "message": "Beacon message too long (max 75 characters)"
                }
            
            # Message would be updated in the database by the service layer
            return {
                "success": True,
                "message": "Beacon message updated",
                "new_message": message
            }
            
        except Exception as e:
            logger.error(f"Error setting beacon message: {e}")
            return {
                "success": False,
                "message": f"Error setting beacon message: {str(e)}"
            }
    
    def get_planet_status(self, planet: Planet, population: int) -> PlanetStats:
        """Get comprehensive planet status"""
        try:
            return PlanetStats(
                planet_id=planet.id,
                name=planet.name,
                owner_id=planet.owner_id,
                position=(planet.x_coord, planet.y_coord),
                sector=(planet.xsect, planet.ysect),
                environment=EnvironmentType(planet.environment),
                resource=ResourceType(planet.resource),
                population=population,
                cash=planet.cash,
                debt=planet.debt,
                tax_rate=planet.tax_rate,
                tax_collected=planet.tax,
                technology_level=planet.technology,
                beacon_message=planet.beacon_message,
                last_attack=planet.last_attack
            )
            
        except Exception as e:
            logger.error(f"Error getting planet status: {e}")
            return PlanetStats(
                planet_id=planet.id,
                name=planet.name or "Unknown",
                owner_id=planet.owner_id,
                position=(0.0, 0.0),
                sector=(0, 0),
                environment=EnvironmentType.FAIR,
                resource=ResourceType.FAIR,
                population=0,
                cash=0,
                debt=0,
                tax_rate=0,
                tax_collected=0,
                technology_level=0,
                beacon_message="",
                last_attack=None
            )
