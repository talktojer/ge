"""
Planet-related background tasks

Implements planet production, taxation, and population growth based on
the original game's planetary economy system (plarti).
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from app.core.celery import celery_app
from app.core.database import get_db
from app.core.planetary_systems import PlanetaryEconomy, EnvironmentType, ResourceType, ProductionResult
from app.models.planet import Planet, PlanetItem
from app.models.item import Item
from app.models.user import User
from app.models.team import Team

logger = logging.getLogger(__name__)

# Production constants from original code
BASE_PRODUCTION_RATE = 10  # Base production rate per tick
POPULATION_GROWTH_RATE = 0.02  # Population growth rate per tick
TAX_COLLECTION_INTERVAL = 100  # Ticks between tax collections
MAX_POPULATION = 1000000  # Maximum planet population


@celery_app.task
def update_planet_production():
    """Update planet production and resources"""
    try:
        db = next(get_db())
        
        # Get all colonized planets
        planets = db.query(Planet).filter(
            Planet.owner_id.isnot(None),
            Planet.userid != ""
        ).all()
        
        logger.info(f"Processing production for {len(planets)} planets")
        
        for planet in planets:
            try:
                _process_planet_production(db, planet)
            except Exception as e:
                logger.error(f"Error processing production for planet {planet.name}: {e}")
                continue
        
        db.commit()
        logger.info("Planet production processing completed")
        
    except Exception as e:
        logger.error(f"Error in update_planet_production: {e}")
        db.rollback()
    finally:
        db.close()


def _process_planet_production(db: Session, planet: Planet) -> None:
    """Process production for a single planet"""
    
    # Get planet items
    planet_items = db.query(PlanetItem).filter(
        PlanetItem.planet_id == planet.id,
        PlanetItem.rate > 0  # Only items with production rates
    ).all()
    
    if not planet_items:
        return
    
    # Create planetary economy instance
    economy = PlanetaryEconomy()
    
    # Determine environment type from planet characteristics
    environment = EnvironmentType.NORMAL
    if planet.environment < 30:
        environment = EnvironmentType.HOSTILE
    elif planet.environment > 70:
        environment = EnvironmentType.BENIGN
    
    # Determine resource type
    resource = ResourceType.NORMAL
    if planet.resource < 30:
        resource = ResourceType.POOR
    elif planet.resource > 70:
        resource = ResourceType.RICH
    
    # Process production for each item
    for planet_item in planet_items:
        try:
            item = planet_item.item
            if not item:
                continue
            
            # Calculate production modifiers
            production_modifier = _calculate_production_modifier(planet, environment, resource)
            
            # Calculate actual production rate
            base_rate = planet_item.rate
            actual_rate = int(base_rate * production_modifier)
            
            if actual_rate <= 0:
                continue
            
            # Add some randomness to production
            random_factor = random.uniform(0.8, 1.2)
            actual_production = int(actual_rate * random_factor)
            
            # Update item quantity
            planet_item.quantity += actual_production
            
            # Log significant production
            if actual_production > 0:
                logger.debug(f"Planet {planet.name} produced {actual_production} {item.name}")
            
        except Exception as e:
            logger.error(f"Error processing item production for {planet.name}: {e}")
            continue


def _calculate_production_modifier(planet: Planet, environment: EnvironmentType, resource: ResourceType) -> float:
    """Calculate production modifier based on planet characteristics"""
    
    modifier = 1.0
    
    # Environment modifier
    if environment == EnvironmentType.HOSTILE:
        modifier *= 0.7  # Reduced production in hostile environments
    elif environment == EnvironmentType.BENIGN:
        modifier *= 1.2  # Increased production in benign environments
    
    # Resource modifier
    if resource == ResourceType.POOR:
        modifier *= 0.8  # Reduced production with poor resources
    elif resource == ResourceType.RICH:
        modifier *= 1.3  # Increased production with rich resources
    
    # Technology modifier
    tech_modifier = 1.0 + (planet.technology * 0.01)  # 1% per tech level
    modifier *= tech_modifier
    
    # Population modifier (more people = more production)
    population_factor = min(2.0, 1.0 + (planet.team_code / 100000.0))  # team_code used as population proxy
    modifier *= population_factor
    
    return modifier


@celery_app.task
def process_planet_taxes():
    """Process planet tax collection"""
    try:
        db = next(get_db())
        
        # Get all colonized planets with tax rates > 0
        planets = db.query(Planet).filter(
            Planet.owner_id.isnot(None),
            Planet.userid != "",
            Planet.tax_rate > 0
        ).all()
        
        logger.info(f"Processing taxes for {len(planets)} planets")
        
        for planet in planets:
            try:
                _process_planet_taxes(db, planet)
            except Exception as e:
                logger.error(f"Error processing taxes for planet {planet.name}: {e}")
                continue
        
        db.commit()
        logger.info("Planet tax processing completed")
        
    except Exception as e:
        logger.error(f"Error in process_planet_taxes: {e}")
        db.rollback()
    finally:
        db.close()


def _process_planet_taxes(db: Session, planet: Planet) -> None:
    """Process tax collection for a single planet"""
    
    # Only collect taxes periodically
    if planet.tick is None:
        planet.tick = 0
    
    if planet.tick % TAX_COLLECTION_INTERVAL != 0:
        planet.tick += 1
        return
    
    # Calculate tax base (based on planet value and population)
    tax_base = _calculate_tax_base(planet)
    
    # Calculate tax amount
    tax_rate = planet.tax_rate / 100.0  # Convert percentage to decimal
    tax_amount = int(tax_base * tax_rate)
    
    if tax_amount <= 0:
        return
    
    # Add tax to planet treasury
    planet.tax += tax_amount
    
    # Update planet cash (tax collected becomes planet cash)
    planet.cash += tax_amount
    
    logger.info(f"Planet {planet.name} collected {tax_amount} credits in taxes (rate: {planet.tax_rate}%)")
    
    # Increment tick counter
    planet.tick += 1


def _calculate_tax_base(planet: Planet) -> int:
    """Calculate tax base for planet"""
    
    # Base tax value from planet characteristics
    base_value = 1000
    
    # Environment modifier
    env_modifier = 1.0 + (planet.environment / 100.0)
    
    # Resource modifier
    resource_modifier = 1.0 + (planet.resource / 100.0)
    
    # Population modifier (using team_code as population proxy)
    population_modifier = 1.0 + (planet.team_code / 100000.0)
    
    # Technology modifier
    tech_modifier = 1.0 + (planet.technology * 0.1)
    
    # Calculate final tax base
    tax_base = int(base_value * env_modifier * resource_modifier * population_modifier * tech_modifier)
    
    return max(100, tax_base)  # Minimum tax base of 100


@celery_app.task
def update_planet_population():
    """Update planet population growth"""
    try:
        db = next(get_db())
        
        # Get all colonized planets
        planets = db.query(Planet).filter(
            Planet.owner_id.isnot(None),
            Planet.userid != ""
        ).all()
        
        logger.info(f"Processing population growth for {len(planets)} planets")
        
        for planet in planets:
            try:
                _process_planet_population(db, planet)
            except Exception as e:
                logger.error(f"Error processing population for planet {planet.name}: {e}")
                continue
        
        db.commit()
        logger.info("Planet population processing completed")
        
    except Exception as e:
        logger.error(f"Error in update_planet_population: {e}")
        db.rollback()
    finally:
        db.close()


def _process_planet_population(db: Session, planet: Planet) -> None:
    """Process population growth for a single planet"""
    
    # Use team_code as population proxy (original game design)
    current_population = planet.team_code
    if current_population <= 0:
        current_population = 1000  # Starting population
    
    # Calculate growth rate based on planet characteristics
    growth_rate = POPULATION_GROWTH_RATE
    
    # Environment affects growth
    if planet.environment < 30:
        growth_rate *= 0.5  # Hostile environment reduces growth
    elif planet.environment > 70:
        growth_rate *= 1.5  # Benign environment increases growth
    
    # Resource availability affects growth
    if planet.resource < 30:
        growth_rate *= 0.7  # Poor resources reduce growth
    elif planet.resource > 70:
        growth_rate *= 1.3  # Rich resources increase growth
    
    # Technology affects growth
    tech_growth_modifier = 1.0 + (planet.technology * 0.02)
    growth_rate *= tech_growth_modifier
    
    # Calculate population growth
    population_growth = int(current_population * growth_rate)
    
    # Apply growth with some randomness
    random_factor = random.uniform(0.5, 1.5)
    actual_growth = int(population_growth * random_factor)
    
    # Update population (with maximum limit)
    new_population = min(current_population + actual_growth, MAX_POPULATION)
    planet.team_code = new_population
    
    # Log significant population changes
    if actual_growth > 0:
        logger.debug(f"Planet {planet.name} population grew by {actual_growth} (total: {new_population})")


@celery_app.task
def process_planet_economy():
    """Process overall planet economy updates"""
    try:
        db = next(get_db())
        
        # Get all colonized planets
        planets = db.query(Planet).filter(
            Planet.owner_id.isnot(None),
            Planet.userid != ""
        ).all()
        
        logger.info(f"Processing economy for {len(planets)} planets")
        
        for planet in planets:
            try:
                _process_planet_economy(db, planet)
            except Exception as e:
                logger.error(f"Error processing economy for planet {planet.name}: {e}")
                continue
        
        db.commit()
        logger.info("Planet economy processing completed")
        
    except Exception as e:
        logger.error(f"Error in process_planet_economy: {e}")
        db.rollback()
    finally:
        db.close()


def _process_planet_economy(db: Session, planet: Planet) -> None:
    """Process economy updates for a single planet"""
    
    # Process debt interest (if planet has debt)
    if planet.debt > 0:
        interest_rate = 0.05  # 5% interest per tick
        interest = int(planet.debt * interest_rate)
        planet.debt += interest
        
        # Try to pay down debt from cash
        if planet.cash > interest:
            planet.cash -= interest
            planet.debt -= interest
        else:
            # Can't pay full interest, add to debt
            planet.debt += interest
    
    # Process resource depletion (poor resource planets)
    if planet.resource < 30:
        # Poor resource planets may lose some resources over time
        depletion_chance = 0.01  # 1% chance per tick
        if random.random() < depletion_chance:
            planet.resource = max(0, planet.resource - 1)
    
    # Process environmental changes (rare events)
    if random.random() < 0.001:  # 0.1% chance per tick
        env_change = random.randint(-2, 2)
        planet.environment = max(0, min(100, planet.environment + env_change))
        
        if env_change != 0:
            logger.info(f"Planet {planet.name} environment changed by {env_change} (new: {planet.environment})")
    
    # Update planet timestamp
    planet.updated_at = datetime.utcnow()


@celery_app.task
def cleanup_abandoned_planets():
    """Clean up planets that have been abandoned"""
    try:
        db = next(get_db())
        
        # Find planets without owners or with inactive owners
        cutoff_time = datetime.utcnow() - timedelta(days=30)  # 30 days inactive
        
        abandoned_planets = db.query(Planet).filter(
            Planet.owner_id.isnot(None),
            Planet.userid != "",
            Planet.last_attack < cutoff_time
        ).all()
        
        logger.info(f"Found {len(abandoned_planets)} potentially abandoned planets")
        
        for planet in abandoned_planets:
            try:
                # Check if owner is still active
                owner = db.query(User).filter(User.id == planet.owner_id).first()
                
                if not owner or owner.last_login < cutoff_time:
                    # Abandon the planet
                    _abandon_planet(db, planet)
                    
            except Exception as e:
                logger.error(f"Error processing abandoned planet {planet.name}: {e}")
                continue
        
        db.commit()
        logger.info("Abandoned planet cleanup completed")
        
    except Exception as e:
        logger.error(f"Error in cleanup_abandoned_planets: {e}")
        db.rollback()
    finally:
        db.close()


def _abandon_planet(db: Session, planet: Planet) -> None:
    """Abandon a planet (remove ownership)"""
    
    # Clear ownership
    planet.owner_id = None
    planet.userid = ""
    
    # Clear alliance password
    planet.password = ""
    
    # Reset some values
    planet.tax = 0
    planet.tax_rate = 0
    planet.warnings = 0
    planet.spy_owner = ""
    planet.beacon_message = ""
    
    logger.info(f"Planet {planet.name} has been abandoned")
