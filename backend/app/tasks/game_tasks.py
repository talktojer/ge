"""
Game-related background tasks

Implements the main game tick processing and cleanup tasks based on
the original game's real-time tick system (warrti, plarti, autorti).
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.core.celery import celery_app
from app.core.database import get_db
from app.models.ship import Ship, ShipClass
from app.models.planet import Planet
from app.models.mine import Mine
from app.models.beacon import Beacon
from app.models.item import Item
from app.models.user import User
from app.models.team import Team
from app.models.mail import Mail
from app.models.game_config import GameConfig

logger = logging.getLogger(__name__)

# Game tick constants
GAME_TICK_INTERVAL = 10  # seconds between game ticks
CLEANUP_INTERVAL = 3600  # seconds between cleanup tasks
LEADERBOARD_UPDATE_INTERVAL = 300  # seconds between leaderboard updates


@celery_app.task
def game_tick():
    """Main game tick - processes all game events"""
    try:
        db = next(get_db())
        
        # Get current game time
        game_time = datetime.utcnow()
        
        logger.info(f"Starting game tick at {game_time}")
        
        # Process all game systems in order
        _process_ship_systems(db)
        _process_planet_systems(db)
        _process_ai_systems(db)
        _process_communication_systems(db)
        _update_game_time(db, game_time)
        
        db.commit()
        logger.info("Game tick completed successfully")
        
    except Exception as e:
        logger.error(f"Error in game_tick: {e}")
        db.rollback()
    finally:
        db.close()


def _process_ship_systems(db: Session) -> None:
    """Process all ship-related systems"""
    
    # Update ship positions and movement
    from app.tasks.ship_tasks import update_ship_positions, process_ship_combat, update_ship_systems
    
    # Execute ship tasks
    update_ship_positions()
    process_ship_combat()
    update_ship_systems()
    
    logger.debug("Ship systems processed")


def _process_planet_systems(db: Session) -> None:
    """Process all planet-related systems"""
    
    # Update planet production and economy
    from app.tasks.planet_tasks import (
        update_planet_production, 
        process_planet_taxes, 
        update_planet_population,
        process_planet_economy
    )
    
    # Execute planet tasks
    update_planet_production()
    process_planet_taxes()
    update_planet_population()
    process_planet_economy()
    
    logger.debug("Planet systems processed")


def _process_ai_systems(db: Session) -> None:
    """Process AI systems (Cyborgs and Droids)"""
    
    # Get all AI ships (Cyborgs and Droids)
    ai_ships = db.query(Ship).filter(
        Ship.user_id == 0,  # Assuming AI ships have user_id = 0
        Ship.status == 0,
        Ship.destruct == 0
    ).all()
    
    logger.debug(f"Processing {len(ai_ships)} AI ships")
    
    for ai_ship in ai_ships:
        try:
            _process_ai_ship_behavior(db, ai_ship)
        except Exception as e:
            logger.error(f"Error processing AI ship {ai_ship.shipname}: {e}")
            continue


def _process_ai_ship_behavior(db: Session, ai_ship: Ship) -> None:
    """Process AI ship behavior and decision making"""
    
    # Update AI ship tick counter
    ai_ship.tick += 1
    
    # Process Cyborg behavior
    if ai_ship.cyb_skill > 0:
        _process_cyborg_behavior(db, ai_ship)
    
    # Process Droid behavior
    if ai_ship.emulate:  # Droid emulation flag
        _process_droid_behavior(db, ai_ship)
    
    # Update AI ship systems
    _update_ai_ship_systems(ai_ship)


def _process_cyborg_behavior(db: Session, cyborg_ship: Ship) -> None:
    """Process Cyborg AI behavior"""
    
    # Cyborgs are more aggressive and tactical
    cyborg_ship.cyb_update += 1
    
    # Every 10 ticks, reassess targets and strategy
    if cyborg_ship.cyb_update % 10 == 0:
        _reassess_cyborg_targets(db, cyborg_ship)
    
    # Cyborgs can use advanced tactics
    if cyborg_ship.cyb_skill > 50:
        _execute_advanced_tactics(db, cyborg_ship)


def _process_droid_behavior(db: Session, droid_ship: Ship) -> None:
    """Process Droid AI behavior"""
    
    # Droids are more methodical and follow patterns
    droid_ship.tick += 1
    
    # Every 20 ticks, update droid behavior
    if droid_ship.tick % 20 == 0:
        _update_droid_patterns(db, droid_ship)
    
    # Droids can use special abilities
    if droid_ship.emulate:
        _execute_droid_abilities(db, droid_ship)


def _reassess_cyborg_targets(db: Session, cyborg_ship: Ship) -> None:
    """Reassess targets for Cyborg AI"""
    
    # Find potential targets in same sector
    sector_ships = db.query(Ship).filter(
        Ship.xsect == int(cyborg_ship.x_coord),
        Ship.ysect == int(cyborg_ship.y_coord),
        Ship.id != cyborg_ship.id,
        Ship.status == 0,
        Ship.user_id != 0  # Don't target other AI ships
    ).all()
    
    if sector_ships:
        # Select best target based on Cyborg skill level
        target = _select_cyborg_target(cyborg_ship, sector_ships)
        if target:
            cyborg_ship.lock = target.id  # Lock onto target


def _select_cyborg_target(cyborg_ship: Ship, potential_targets: List[Ship]) -> Optional[Ship]:
    """Select target for Cyborg AI"""
    
    # Cyborgs prefer weaker targets
    best_target = None
    best_score = float('inf')
    
    for target in potential_targets:
        # Calculate target score (lower is better)
        score = target.damage + (target.shield_charge / 10) + (target.energy / 100)
        
        if score < best_score:
            best_score = score
            best_target = target
    
    return best_target


def _execute_advanced_tactics(db: Session, cyborg_ship: Ship) -> None:
    """Execute advanced Cyborg tactics"""
    
    # High-skill Cyborgs can use cloaking
    if cyborg_ship.cyb_skill > 75 and cyborg_ship.energy > 500:
        if not cyborg_ship.cloak and random.random() < 0.1:  # 10% chance
            cyborg_ship.cloak = 30  # Cloak for 30 ticks
            cyborg_ship.energy -= 500
    
    # Advanced Cyborgs can lay mines strategically
    if cyborg_ship.cyb_skill > 60 and cyborg_ship.energy > 400:
        if random.random() < 0.05:  # 5% chance
            _lay_strategic_mine(db, cyborg_ship)


def _lay_strategic_mine(db: Session, cyborg_ship: Ship) -> None:
    """Lay mine at strategic location"""
    
    # Create mine at current position
    mine = Mine(
        xsect=int(cyborg_ship.x_coord),
        ysect=int(cyborg_ship.y_coord),
        x_coord=cyborg_ship.x_coord,
        y_coord=cyborg_ship.y_coord,
        owner_id=cyborg_ship.user_id,
        active=True,
        damage=200,
        created_at=datetime.utcnow()
    )
    
    db.add(mine)
    cyborg_ship.energy -= 400
    
    logger.info(f"Cyborg {cyborg_ship.shipname} laid strategic mine")


def _update_droid_patterns(db: Session, droid_ship: Ship) -> None:
    """Update Droid behavior patterns"""
    
    # Droids follow predictable patterns
    pattern = droid_ship.tick % 4
    
    if pattern == 0:
        # Patrol pattern
        _execute_patrol_pattern(droid_ship)
    elif pattern == 1:
        # Defend pattern
        _execute_defend_pattern(droid_ship)
    elif pattern == 2:
        # Hunt pattern
        _execute_hunt_pattern(db, droid_ship)
    else:
        # Rest pattern
        _execute_rest_pattern(droid_ship)


def _execute_patrol_pattern(droid_ship: Ship) -> None:
    """Execute patrol pattern for Droid"""
    
    # Move in a square pattern
    if droid_ship.hold_course <= 0:
        droid_ship.head2b = (droid_ship.heading + 90) % 360
        droid_ship.hold_course = 50  # Hold course for 50 ticks
        droid_ship.speed2b = 1000  # Patrol speed


def _execute_defend_pattern(droid_ship: Ship) -> None:
    """Execute defend pattern for Droid"""
    
    # Slow movement, high alert
    droid_ship.speed2b = 500
    droid_ship.shield_status = 1  # Raise shields


def _execute_hunt_pattern(db: Session, droid_ship: Ship) -> None:
    """Execute hunt pattern for Droid"""
    
    # Find nearest target
    targets = db.query(Ship).filter(
        Ship.status == 0,
        Ship.user_id != 0,
        Ship.id != droid_ship.id
    ).all()
    
    if targets:
        nearest_target = min(targets, key=lambda t: abs(t.x_coord - droid_ship.x_coord) + abs(t.y_coord - droid_ship.y_coord))
        droid_ship.lock = nearest_target.id


def _execute_rest_pattern(droid_ship: Ship) -> None:
    """Execute rest pattern for Droid"""
    
    # Stop and recharge
    droid_ship.speed2b = 0
    droid_ship.head2b = droid_ship.heading


def _execute_droid_abilities(db: Session, droid_ship: Ship) -> None:
    """Execute special Droid abilities"""
    
    # Droids can repair themselves
    if droid_ship.damage > 10 and droid_ship.energy > 300:
        if random.random() < 0.02:  # 2% chance per tick
            droid_ship.damage = max(0, droid_ship.damage - 5)
            droid_ship.energy -= 300
            logger.info(f"Droid {droid_ship.shipname} self-repaired")


def _update_ai_ship_systems(ai_ship: Ship) -> None:
    """Update AI ship systems"""
    
    # Energy recovery for AI ships
    if ai_ship.energy < 1000:
        ai_ship.energy += 10  # AI ships recover energy faster
    
    # Shield recovery
    if ai_ship.shield_status > 0 and ai_ship.shield_charge < 100:
        ai_ship.shield_charge += 5
    
    # Update last activity
    ai_ship.last_activity = datetime.utcnow()


def _process_communication_systems(db: Session) -> None:
    """Process communication systems (mail, beacons, etc.)"""
    
    # Process mail system
    _process_mail_system(db)
    
    # Process beacon system
    _process_beacon_system(db)
    
    logger.debug("Communication systems processed")


def _process_mail_system(db: Session) -> None:
    """Process mail system updates"""
    
    # Clean up old mail
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    old_mail = db.query(Mail).filter(Mail.created_at < cutoff_date).all()
    
    for mail in old_mail:
        db.delete(mail)
    
    if old_mail:
        logger.info(f"Cleaned up {len(old_mail)} old mail messages")


def _process_beacon_system(db: Session) -> None:
    """Process beacon system updates"""
    
    # Update beacon timestamps
    beacons = db.query(Beacon).filter(Beacon.active == True).all()
    
    for beacon in beacons:
        beacon.updated_at = datetime.utcnow()


def _update_game_time(db: Session, game_time: datetime) -> None:
    """Update game time and statistics"""
    
    # Get or create game config
    game_config = db.query(GameConfig).filter(GameConfig.key == "game_time").first()
    if not game_config:
        game_config = GameConfig(key="game_time", value="")
        db.add(game_config)
    
    game_config.value = game_time.isoformat()
    game_config.updated_at = game_time


@celery_app.task
def cleanup_expired_items():
    """Clean up expired items like mines, decoys, etc."""
    try:
        db = next(get_db())
        
        logger.info("Starting cleanup of expired items")
        
        # Clean up expired mines
        _cleanup_expired_mines(db)
        
        # Clean up expired beacons
        _cleanup_expired_beacons(db)
        
        # Clean up inactive ships
        _cleanup_inactive_ships(db)
        
        # Clean up old game logs
        _cleanup_old_logs(db)
        
        db.commit()
        logger.info("Cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_items: {e}")
        db.rollback()
    finally:
        db.close()


def _cleanup_expired_mines(db: Session) -> None:
    """Clean up expired mines"""
    
    # Mines expire after 24 hours
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    expired_mines = db.query(Mine).filter(
        Mine.active == True,
        Mine.created_at < cutoff_time
    ).all()
    
    for mine in expired_mines:
        mine.active = False
    
    if expired_mines:
        logger.info(f"Deactivated {len(expired_mines)} expired mines")


def _cleanup_expired_beacons(db: Session) -> None:
    """Clean up expired beacons"""
    
    # Beacons expire after 7 days
    cutoff_time = datetime.utcnow() - timedelta(days=7)
    expired_beacons = db.query(Beacon).filter(
        Beacon.active == True,
        Beacon.created_at < cutoff_time
    ).all()
    
    for beacon in expired_beacons:
        beacon.active = False
    
    if expired_beacons:
        logger.info(f"Deactivated {len(expired_beacons)} expired beacons")


def _cleanup_inactive_ships(db: Session) -> None:
    """Clean up inactive ships"""
    
    # Ships inactive for 7 days are marked as inactive
    cutoff_time = datetime.utcnow() - timedelta(days=7)
    inactive_ships = db.query(Ship).filter(
        Ship.status == 0,
        Ship.last_activity < cutoff_time,
        Ship.user_id != 0  # Don't cleanup AI ships
    ).all()
    
    for ship in inactive_ships:
        ship.status = -2  # Mark as inactive
        ship.speed = 0
        ship.speed2b = 0
    
    if inactive_ships:
        logger.info(f"Marked {len(inactive_ships)} ships as inactive")


def _cleanup_old_logs(db: Session) -> None:
    """Clean up old game logs and statistics"""
    
    # This would clean up old log entries if we had a logging table
    # For now, just log the cleanup
    logger.debug("Old logs cleanup completed")


@celery_app.task
def update_leaderboards():
    """Update player leaderboards and statistics"""
    try:
        db = next(get_db())
        
        logger.info("Updating leaderboards")
        
        # Update ship leaderboards
        _update_ship_leaderboards(db)
        
        # Update planet leaderboards
        _update_planet_leaderboards(db)
        
        # Update team leaderboards
        _update_team_leaderboards(db)
        
        db.commit()
        logger.info("Leaderboards updated successfully")
        
    except Exception as e:
        logger.error(f"Error in update_leaderboards: {e}")
        db.rollback()
    finally:
        db.close()


def _update_ship_leaderboards(db: Session) -> None:
    """Update ship-based leaderboards"""
    
    # Top ships by kills
    top_killers = db.query(Ship).filter(
        Ship.status == 0,
        Ship.kills > 0
    ).order_by(desc(Ship.kills)).limit(10).all()
    
    # Top ships by energy efficiency
    top_efficient = db.query(Ship).filter(
        Ship.status == 0,
        Ship.energy > 0
    ).order_by(desc(Ship.energy)).limit(10).all()
    
    logger.debug(f"Updated ship leaderboards: {len(top_killers)} top killers, {len(top_efficient)} most efficient")


def _update_planet_leaderboards(db: Session) -> None:
    """Update planet-based leaderboards"""
    
    # Top planets by production
    top_producers = db.query(Planet).filter(
        Planet.owner_id.isnot(None),
        Planet.team_code > 0
    ).order_by(desc(Planet.team_code)).limit(10).all()
    
    # Top planets by wealth
    top_wealthy = db.query(Planet).filter(
        Planet.owner_id.isnot(None),
        Planet.cash > 0
    ).order_by(desc(Planet.cash)).limit(10).all()
    
    logger.debug(f"Updated planet leaderboards: {len(top_producers)} top producers, {len(top_wealthy)} wealthiest")


def _update_team_leaderboards(db: Session) -> None:
    """Update team-based leaderboards"""
    
    # Top teams by total planets
    top_teams = db.query(Team).filter(
        Team.active == True
    ).order_by(desc(Team.planet_count)).limit(10).all()
    
    logger.debug(f"Updated team leaderboards: {len(top_teams)} top teams")


@celery_app.task
def process_game_events():
    """Process special game events and random occurrences"""
    try:
        db = next(get_db())
        
        # Random events have a small chance of occurring each tick
        if random.random() < 0.01:  # 1% chance per tick
            _trigger_random_event(db)
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error in process_game_events: {e}")
        db.rollback()
    finally:
        db.close()


def _trigger_random_event(db: Session) -> None:
    """Trigger a random game event"""
    
    event_types = [
        "resource_discovery",
        "environmental_change", 
        "technological_breakthrough",
        "space_anomaly",
        "trade_opportunity"
    ]
    
    event_type = random.choice(event_types)
    
    # Select random planet for event
    planets = db.query(Planet).filter(Planet.owner_id.isnot(None)).all()
    if planets:
        planet = random.choice(planets)
        _apply_random_event(db, planet, event_type)


def _apply_random_event(db: Session, planet: Planet, event_type: str) -> None:
    """Apply random event to planet"""
    
    if event_type == "resource_discovery":
        planet.resource = min(100, planet.resource + 5)
        logger.info(f"Resource discovery on planet {planet.name}")
    
    elif event_type == "environmental_change":
        change = random.randint(-3, 3)
        planet.environment = max(0, min(100, planet.environment + change))
        logger.info(f"Environmental change on planet {planet.name}: {change}")
    
    elif event_type == "technological_breakthrough":
        planet.technology += 1
        logger.info(f"Technological breakthrough on planet {planet.name}")
    
    elif event_type == "space_anomaly":
        # Create temporary beacon
        beacon = Beacon(
            xsect=planet.xsect,
            ysect=planet.ysect,
            x_coord=planet.x_coord,
            y_coord=planet.y_coord,
            message="Space anomaly detected in this sector",
            active=True,
            created_at=datetime.utcnow()
        )
        db.add(beacon)
        logger.info(f"Space anomaly detected near planet {planet.name}")
    
    elif event_type == "trade_opportunity":
        planet.cash += random.randint(1000, 5000)
        logger.info(f"Trade opportunity on planet {planet.name}")


# Periodic task scheduling
@celery_app.task
def schedule_periodic_tasks():
    """Schedule periodic background tasks"""
    
    # This would be called by a scheduler to ensure all tasks run
    # at appropriate intervals
    
    # Game tick (every 10 seconds)
    game_tick.apply_async(countdown=GAME_TICK_INTERVAL)
    
    # Cleanup (every hour)
    cleanup_expired_items.apply_async(countdown=CLEANUP_INTERVAL)
    
    # Leaderboards (every 5 minutes)
    update_leaderboards.apply_async(countdown=LEADERBOARD_UPDATE_INTERVAL)
    
    # Game events (every 30 seconds)
    process_game_events.apply_async(countdown=30)
    
    logger.info("Periodic tasks scheduled")
