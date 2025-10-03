"""
Ship-related background tasks

Implements ship movement, combat processing, and system updates based on
the original game's real-time tick processing (warrti, warrti2, warrti3).
"""

import logging
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from app.core.celery import celery_app
from app.core.database import get_db
from app.core.coordinates import Coordinate, distance, bearing, wrap_coordinate, clamp_to_galaxy
from app.core.combat_systems import CombatController, WeaponType, TargetType, CombatTarget, WeaponStatus
from app.models.ship import Ship
from app.models.planet import Planet
from app.models.mine import Mine
from app.models.beacon import Beacon
from app.models.item import Item
from app.models.user import User

logger = logging.getLogger(__name__)

# Movement constants from original code
MAX_ACCELERATION = 100  # Maximum acceleration rate
MAX_SPEED = 50000       # Maximum speed in parsecs per tick
ENERGY_RECOVERY_RATE = 5  # Energy recovery per tick
SHIELD_RECOVERY_RATE = 2  # Shield recovery per tick


@celery_app.task
def update_ship_positions():
    """Update ship positions and movement based on current heading and speed"""
    try:
        db = next(get_db())
        
        # Get all active ships
        ships = db.query(Ship).filter(
            Ship.status == 0,  # Active status
            Ship.destruct == 0  # Not self-destructing
        ).all()
        
        logger.info(f"Processing movement for {len(ships)} ships")
        
        for ship in ships:
            try:
                _process_ship_movement(db, ship)
            except Exception as e:
                logger.error(f"Error processing movement for ship {ship.shipname}: {e}")
                continue
        
        db.commit()
        logger.info("Ship movement processing completed")
        
    except Exception as e:
        logger.error(f"Error in update_ship_positions: {e}")
        db.rollback()
    finally:
        db.close()


def _process_ship_movement(db: Session, ship: Ship) -> None:
    """Process movement for a single ship"""
    
    # Skip if ship is not moving
    if ship.speed <= 0 and ship.speed2b <= 0:
        return
    
    # Calculate acceleration/deceleration towards target speed
    speed_diff = ship.speed2b - ship.speed
    if abs(speed_diff) > 0:
        if speed_diff > 0:
            # Accelerating
            acceleration = min(speed_diff, MAX_ACCELERATION)
        else:
            # Decelerating
            acceleration = max(speed_diff, -MAX_ACCELERATION)
        
        new_speed = ship.speed + acceleration
        ship.speed = max(0, min(new_speed, MAX_SPEED))
    
    # Calculate heading change towards target heading
    heading_diff = ship.head2b - ship.heading
    if abs(heading_diff) > 0:
        # Normalize heading difference
        if heading_diff > 180:
            heading_diff -= 360
        elif heading_diff < -180:
            heading_diff += 360
        
        # Apply heading change (max 10 degrees per tick)
        max_heading_change = 10.0
        if abs(heading_diff) > max_heading_change:
            heading_diff = max_heading_change if heading_diff > 0 else -max_heading_change
        
        ship.heading += heading_diff
        
        # Normalize heading to 0-360 range
        while ship.heading < 0:
            ship.heading += 360
        while ship.heading >= 360:
            ship.heading -= 360
    
    # Calculate movement based on current heading and speed
    if ship.speed > 0:
        # Convert heading to radians
        heading_rad = math.radians(ship.heading)
        
        # Calculate movement vector
        dx = ship.speed * math.cos(heading_rad)
        dy = ship.speed * math.sin(heading_rad)
        
        # Update position
        new_x = ship.x_coord + dx
        new_y = ship.y_coord + dy
        
        # Apply galaxy wrapping
        new_coord = wrap_coordinate(Coordinate(new_x, new_y))
        
        ship.x_coord = new_coord.x
        ship.y_coord = new_coord.y
        
        # Update last activity
        ship.last_activity = datetime.utcnow()
    
    # Update ship tick counter
    ship.tick += 1


@celery_app.task
def process_ship_combat():
    """Process ship-to-ship combat and mine encounters"""
    try:
        db = next(get_db())
        
        # Get all active ships
        ships = db.query(Ship).filter(
            Ship.status == 0,
            Ship.destruct == 0
        ).all()
        
        logger.info(f"Processing combat for {len(ships)} ships")
        
        # Process mine encounters first
        _process_mine_encounters(db, ships)
        
        # Process ship-to-ship combat
        _process_ship_combat(db, ships)
        
        # Process weapon cooldowns
        _process_weapon_cooldowns(db, ships)
        
        db.commit()
        logger.info("Ship combat processing completed")
        
    except Exception as e:
        logger.error(f"Error in process_ship_combat: {e}")
        db.rollback()
    finally:
        db.close()


def _process_mine_encounters(db: Session, ships: List[Ship]) -> None:
    """Process ship encounters with mines"""
    
    for ship in ships:
        try:
            # Get mines in the same sector
            mines = db.query(Mine).filter(
                Mine.xsect == int(ship.x_coord),
                Mine.ysect == int(ship.y_coord),
                Mine.active == True
            ).all()
            
            for mine in mines:
                # Calculate distance to mine
                mine_coord = Coordinate(mine.x_coord, mine.y_coord)
                ship_coord = Coordinate(ship.x_coord, ship.y_coord)
                dist = distance(ship_coord, mine_coord)
                
                # Check if ship is within mine trigger range (10,000 parsecs)
                if dist <= 10000:
                    _trigger_mine(db, ship, mine)
        
        except Exception as e:
            logger.error(f"Error processing mine encounters for ship {ship.shipname}: {e}")


def _trigger_mine(db: Session, ship: Ship, mine: Mine) -> None:
    """Handle mine explosion"""
    
    # Calculate damage (200 base damage)
    damage = 200.0
    
    # Apply shield absorption
    shield_damage = 0.0
    hull_damage = damage
    
    if ship.shield_status > 0 and ship.shield_charge > 0:
        shield_absorption = min(damage, ship.shield_charge)
        shield_damage = shield_absorption
        hull_damage = damage - shield_absorption
        
        ship.shield_charge -= shield_damage
        if ship.shield_charge < 0:
            ship.shield_charge = 0
    
    # Apply hull damage
    if hull_damage > 0:
        ship.damage += hull_damage
        if ship.damage > 100:
            ship.damage = 100
    
    # Deactivate mine
    mine.active = False
    
    # Set mines nearby flag
    ship.mines_near = True
    
    logger.info(f"Mine exploded near {ship.shipname}: {damage:.1f} damage (Shield: {shield_damage:.1f}, Hull: {hull_damage:.1f})")


def _process_ship_combat(db: Session, ships: List[Ship]) -> None:
    """Process ship-to-ship combat"""
    
    # Group ships by sector for combat processing
    sectors = {}
    for ship in ships:
        sector_key = (int(ship.x_coord), int(ship.y_coord))
        if sector_key not in sectors:
            sectors[sector_key] = []
        sectors[sector_key].append(ship)
    
    # Process combat in each sector
    for sector_ships in sectors.values():
        if len(sector_ships) < 2:
            continue
        
        _process_sector_combat(db, sector_ships)


def _process_sector_combat(db: Session, ships: List[Ship]) -> None:
    """Process combat between ships in the same sector"""
    
    # Only process combat for AI ships (Cyborgs and Droids)
    ai_ships = [s for s in ships if s.user_id == 0]  # Assuming AI ships have user_id = 0
    
    for ai_ship in ai_ships:
        try:
            # Find potential targets
            targets = [s for s in ships if s.id != ai_ship.id and _can_attack(ai_ship, s)]
            
            if not targets:
                continue
            
            # Select best target
            target = _select_best_target(ai_ship, targets)
            if not target:
                continue
            
            # Execute attack
            _execute_ai_attack(db, ai_ship, target)
            
        except Exception as e:
            logger.error(f"Error processing AI combat for ship {ai_ship.shipname}: {e}")


def _can_attack(attacker: Ship, target: Ship) -> bool:
    """Check if attacker can attack target"""
    
    # Can't attack cloaked ships
    if target.cloak > 0:
        return False
    
    # Can't attack if attacker is cloaked
    if attacker.cloak > 0:
        return False
    
    # Check distance (within 100,000 parsecs for combat)
    attacker_coord = Coordinate(attacker.x_coord, attacker.y_coord)
    target_coord = Coordinate(target.x_coord, target.y_coord)
    dist = distance(attacker_coord, target_coord)
    
    if dist > 100000:
        return False
    
    # Check if target is in same team (would need team logic)
    # For now, allow all attacks
    
    return True


def _select_best_target(attacker: Ship, targets: List[Ship]) -> Optional[Ship]:
    """Select the best target for AI ship"""
    
    if not targets:
        return None
    
    # Simple target selection: closest ship
    attacker_coord = Coordinate(attacker.x_coord, attacker.y_coord)
    
    best_target = None
    best_distance = float('inf')
    
    for target in targets:
        target_coord = Coordinate(target.x_coord, target.y_coord)
        dist = distance(attacker_coord, target_coord)
        
        if dist < best_distance:
            best_distance = dist
            best_target = target
    
    return best_target


def _execute_ai_attack(db: Session, attacker: Ship, target: Ship) -> None:
    """Execute AI ship attack"""
    
    # Check if attacker has enough energy and weapons
    if attacker.energy < 100 or attacker.phaser_strength <= 0:
        return
    
    # Create combat target
    attacker_coord = Coordinate(attacker.x_coord, attacker.y_coord)
    target_coord = Coordinate(target.x_coord, target.y_coord)
    dist = distance(attacker_coord, target_coord)
    
    combat_target = CombatTarget(
        target_id=str(target.id),
        target_type=TargetType.SHIP,
        position=target_coord,
        distance=dist,
        bearing=bearing(attacker_coord, target_coord, attacker.heading),
        shield_status=target.shield_status > 0,
        cloak_status=target.cloak > 0,
        size_factor=100.0  # Assume standard ship size
    )
    
    # Create weapon status
    weapon_status = WeaponStatus(
        weapon_type=WeaponType.PHASER,
        available=attacker.phaser_strength > 0,
        energy_level=attacker.phaser_strength,
        ammunition=0,
        cooldown_time=0,
        damage_modifier=1.0,
        range_modifier=1.0
    )
    
    # Execute phaser attack
    combat_controller = CombatController()
    result = combat_controller.execute_combat_action(
        "fire_phasers",
        weapon_status,
        combat_target,
        {
            "energy": attacker.energy,
            "fire_control_damage": attacker.fire_control
        }
    )
    
    if result.success and result.hit:
        # Apply damage to target
        _apply_combat_damage(target, result.damage_dealt)
        
        # Consume energy from attacker
        attacker.energy -= result.energy_consumed
        
        # Update kill count if target destroyed
        if result.target_destroyed:
            attacker.kills += 1
            target.status = -1  # Mark as destroyed
        
        # Update last fired
        attacker.last_fired = target.user_id
        
        logger.info(f"{attacker.shipname} attacked {target.shipname}: {result.damage_dealt:.1f} damage")


def _apply_combat_damage(target: Ship, damage: float) -> None:
    """Apply combat damage to target ship"""
    
    # Apply shield absorption first
    shield_damage = 0.0
    hull_damage = damage
    
    if target.shield_status > 0 and target.shield_charge > 0:
        shield_absorption = min(damage, target.shield_charge)
        shield_damage = shield_absorption
        hull_damage = damage - shield_absorption
        
        target.shield_charge -= shield_damage
        if target.shield_charge < 0:
            target.shield_charge = 0
    
    # Apply hull damage
    if hull_damage > 0:
        target.damage += hull_damage
        if target.damage > 100:
            target.damage = 100


def _process_weapon_cooldowns(db: Session, ships: List[Ship]) -> None:
    """Process weapon system cooldowns and recovery"""
    
    for ship in ships:
        # Process hyper-phaser cooldown
        if ship.hypha:  # Hyper-phasers cooling
            # Reduce cooldown timer
            ship.hypha = False  # Simplified: cooldown complete after one tick


@celery_app.task
def update_ship_systems():
    """Update ship systems (shields, energy, etc.)"""
    try:
        db = next(get_db())
        
        # Get all active ships
        ships = db.query(Ship).filter(
            Ship.status == 0,
            Ship.destruct == 0
        ).all()
        
        logger.info(f"Updating systems for {len(ships)} ships")
        
        for ship in ships:
            try:
                _update_ship_systems(db, ship)
            except Exception as e:
                logger.error(f"Error updating systems for ship {ship.shipname}: {e}")
                continue
        
        db.commit()
        logger.info("Ship system updates completed")
        
    except Exception as e:
        logger.error(f"Error in update_ship_systems: {e}")
        db.rollback()
    finally:
        db.close()


def _update_ship_systems(db: Session, ship: Ship) -> None:
    """Update systems for a single ship"""
    
    # Energy recovery (if not cloaked and not in hyperspace)
    if ship.cloak <= 0 and ship.where == 0:
        max_energy = 1000  # Would get from ship class
        if ship.energy < max_energy:
            ship.energy += ENERGY_RECOVERY_RATE
            ship.energy = min(ship.energy, max_energy)
    
    # Shield recovery (if shields are up)
    if ship.shield_status > 0:
        max_shields = 100  # Would get from ship class
        if ship.shield_charge < max_shields:
            ship.shield_charge += SHIELD_RECOVERY_RATE
            ship.shield_charge = min(ship.shield_charge, max_shields)
    
    # Cloak timer countdown
    if ship.cloak > 0:
        ship.cloak -= 1
    
    # Update warning counters
    if ship.warn_counter > 0:
        ship.warn_counter -= 1
    
    # Update hold course counter
    if ship.hold_course > 0:
        ship.hold_course -= 1
    
    # Update mines near flag (reset after some time)
    if ship.mines_near:
        ship.mines_near = False
    
    # Process self-destruct countdown
    if ship.destruct > 0:
        ship.destruct -= 1
        if ship.destruct <= 0:
            # Self-destruct triggered
            ship.status = -1  # Mark as destroyed
            ship.damage = 100  # Complete destruction
            logger.info(f"Ship {ship.shipname} self-destructed")
    
    # Update last activity
    ship.last_activity = datetime.utcnow()
