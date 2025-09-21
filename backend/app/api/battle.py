"""
Galactic Empire - Battle API endpoints

This module provides API endpoints for combat operations including
battle initiation, weapon attacks, tactical displays, and AI management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..core.database import get_db
from ..core.auth import get_current_user
from ..core.battle_service import BattleService
from ..models.user import User
from ..models.ship import Ship

router = APIRouter()


# Pydantic models for requests
class CombatInitiationRequest(BaseModel):
    target_ship_id: int


class WeaponAttackRequest(BaseModel):
    target_ship_id: int
    weapon_type: str  # "phasers", "torpedoes", "missiles", "ion_cannon"
    hyper_phasers: Optional[bool] = False


class ScannerRequest(BaseModel):
    scanner_type: str  # "short_range", "long_range", "tactical", "hyperspace", "cloak_detector"
    scan_range: Optional[float] = None


class TargetLockRequest(BaseModel):
    target_ship_id: int


class TacticalDisplayRequest(BaseModel):
    display_mode: str  # "overview", "combat", "navigation", "damage_control", "scanner"
    display_range: Optional[float] = 150000.0


class SelfDestructRequest(BaseModel):
    confirmation: str  # User must type "CONFIRM" to initiate


class SelfDestructAbortRequest(BaseModel):
    abort_code: str


# Combat Operations Endpoints

@router.post("/combat/initiate", response_model=Dict[str, Any])
async def initiate_combat(
    combat_request: CombatInitiationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate combat between user's ship and target ship"""
    battle_service = BattleService(db)
    
    # Get user's active ship
    user_ship = db.query(Ship).filter(
        Ship.user_id == current_user.id,
        Ship.status == 0  # Active status
    ).first()
    
    if not user_ship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active ship found"
        )
    
    # Verify target ship exists
    target_ship = db.query(Ship).filter(Ship.id == combat_request.target_ship_id).first()
    if not target_ship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target ship not found"
        )
    
    # Can't attack own ship
    if target_ship.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot attack your own ship"
        )
    
    result = battle_service.initiate_combat(user_ship.id, combat_request.target_ship_id)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Combat initiation failed")
        )
    
    return result


@router.post("/combat/attack", response_model=Dict[str, Any])
async def execute_weapon_attack(
    attack_request: WeaponAttackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute weapon attack on target ship"""
    battle_service = BattleService(db)
    
    # Get user's active ship
    user_ship = db.query(Ship).filter(
        Ship.user_id == current_user.id,
        Ship.status == 0
    ).first()
    
    if not user_ship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active ship found"
        )
    
    # Verify target ship exists
    target_ship = db.query(Ship).filter(Ship.id == attack_request.target_ship_id).first()
    if not target_ship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target ship not found"
        )
    
    result = battle_service.execute_weapon_attack(
        user_ship.id,
        attack_request.target_ship_id,
        attack_request.weapon_type,
        hyper_phasers=attack_request.hyper_phasers
    )
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Weapon attack failed")
        )
    
    return result


@router.post("/combat/self-destruct", response_model=Dict[str, Any])
async def initiate_self_destruct(
    destruct_request: SelfDestructRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate self-destruct sequence"""
    if destruct_request.confirmation != "CONFIRM":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-destruct requires confirmation. Type 'CONFIRM' to proceed."
        )
    
    battle_service = BattleService(db)
    
    # Get user's active ship
    user_ship = db.query(Ship).filter(
        Ship.user_id == current_user.id,
        Ship.status == 0
    ).first()
    
    if not user_ship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active ship found"
        )
    
    result = battle_service.initiate_self_destruct(user_ship.id, current_user.id)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Self-destruct initiation failed")
        )
    
    return result


@router.post("/combat/abort-self-destruct", response_model=Dict[str, Any])
async def abort_self_destruct(
    abort_request: SelfDestructAbortRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Abort self-destruct sequence"""
    battle_service = BattleService(db)
    
    # Get user's active ship
    user_ship = db.query(Ship).filter(
        Ship.user_id == current_user.id,
        Ship.status == 0
    ).first()
    
    if not user_ship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active ship found"
        )
    
    result = battle_service.abort_self_destruct(
        user_ship.id, current_user.id, abort_request.abort_code
    )
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Self-destruct abort failed")
        )
    
    return result


# Tactical Systems Endpoints

@router.post("/tactical/scan", response_model=Dict[str, Any])
async def perform_scanner_sweep(
    scan_request: ScannerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform scanner sweep"""
    battle_service = BattleService(db)
    
    # Get user's active ship
    user_ship = db.query(Ship).filter(
        Ship.user_id == current_user.id,
        Ship.status == 0
    ).first()
    
    if not user_ship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active ship found"
        )
    
    result = battle_service.perform_scanner_sweep(
        user_ship.id,
        scan_request.scanner_type,
        scan_request.scan_range
    )
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Scanner sweep failed")
        )
    
    return result


@router.post("/tactical/target-lock", response_model=Dict[str, Any])
async def acquire_target_lock(
    lock_request: TargetLockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acquire target lock on another ship"""
    battle_service = BattleService(db)
    
    # Get user's active ship
    user_ship = db.query(Ship).filter(
        Ship.user_id == current_user.id,
        Ship.status == 0
    ).first()
    
    if not user_ship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active ship found"
        )
    
    # Verify target ship exists
    target_ship = db.query(Ship).filter(Ship.id == lock_request.target_ship_id).first()
    if not target_ship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target ship not found"
        )
    
    result = battle_service.acquire_target_lock(user_ship.id, lock_request.target_ship_id)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Target lock acquisition failed")
        )
    
    return result


@router.post("/tactical/display", response_model=Dict[str, Any])
async def generate_tactical_display(
    display_request: TacticalDisplayRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate tactical display"""
    battle_service = BattleService(db)
    
    # Get user's active ship
    user_ship = db.query(Ship).filter(
        Ship.user_id == current_user.id,
        Ship.status == 0
    ).first()
    
    if not user_ship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active ship found"
        )
    
    result = battle_service.generate_tactical_display(
        user_ship.id,
        display_request.display_mode,
        display_request.display_range
    )
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Tactical display generation failed")
        )
    
    return result


# Battle Status and Information Endpoints

@router.get("/battle/status", response_model=Dict[str, Any])
async def get_battle_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current battle status for user's ship"""
    battle_service = BattleService(db)
    
    # Get user's active ship
    user_ship = db.query(Ship).filter(
        Ship.user_id == current_user.id,
        Ship.status == 0
    ).first()
    
    if not user_ship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active ship found"
        )
    
    battle_status = battle_service.get_battle_status(user_ship.id)
    
    return {
        "ship_id": user_ship.id,
        "ship_name": user_ship.shipname,
        "battle_status": battle_status,
        "in_combat": battle_status is not None
    }


@router.get("/battle/nearby-targets", response_model=List[Dict[str, Any]])
async def get_nearby_targets(
    max_range: float = Query(200000.0, ge=10000.0, le=500000.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get nearby ships that can be targeted"""
    # Get user's active ship
    user_ship = db.query(Ship).filter(
        Ship.user_id == current_user.id,
        Ship.status == 0
    ).first()
    
    if not user_ship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active ship found"
        )
    
    # Get nearby ships
    from ..core.coordinates import Coordinate, distance
    
    user_pos = Coordinate(user_ship.x_coord, user_ship.y_coord)
    nearby_ships = []
    
    other_ships = db.query(Ship).filter(
        Ship.id != user_ship.id,
        Ship.status == 0  # Active ships only
    ).all()
    
    for ship in other_ships:
        ship_pos = Coordinate(ship.x_coord, ship.y_coord)
        ship_distance = distance(user_pos, ship_pos)
        
        if ship_distance <= max_range:
            nearby_ships.append({
                "id": ship.id,
                "name": ship.shipname,
                "owner": ship.user.userid,
                "class": ship.ship_class.typename,
                "distance": ship_distance,
                "bearing": 0.0,  # Would calculate actual bearing
                "is_hostile": ship.hostile,
                "is_cloaked": ship.cloak == -1,
                "damage": ship.damage,
                "can_target": ship.user_id != current_user.id
            })
    
    # Sort by distance
    nearby_ships.sort(key=lambda x: x["distance"])
    
    return nearby_ships


@router.get("/battle/combat-log", response_model=List[Dict[str, Any]])
async def get_combat_log(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent combat log entries"""
    # This would retrieve combat log entries from database
    # For now, return placeholder
    return [
        {
            "timestamp": "2024-01-01T12:00:00Z",
            "event_type": "weapon_attack",
            "attacker": "USS Enterprise",
            "target": "Klingon Warbird",
            "weapon": "phasers",
            "damage": 45.5,
            "result": "hit"
        }
    ]


# AI and Automation Endpoints

@router.post("/battle/ai/process-tick", response_model=Dict[str, Any])
async def process_ai_battle_tick(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process AI battle systems for one tick (admin/debug endpoint)"""
    # This would typically be called by the game engine, not directly by users
    # For now, return placeholder
    battle_service = BattleService(db)
    
    result = battle_service.process_battle_tick()
    
    return result


@router.get("/battle/ai/status", response_model=Dict[str, Any])
async def get_ai_battle_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI battle system status"""
    # Return status of AI-controlled ships in the area
    return {
        "ai_ships_active": 0,
        "cyborg_ships": 0,
        "droid_ships": 0,
        "active_battles": 0,
        "ai_decisions_last_tick": 0
    }


# Damage and Repair Endpoints

@router.get("/battle/damage-report", response_model=Dict[str, Any])
async def get_damage_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed damage report for user's ship"""
    # Get user's active ship
    user_ship = db.query(Ship).filter(
        Ship.user_id == current_user.id,
        Ship.status == 0
    ).first()
    
    if not user_ship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active ship found"
        )
    
    return {
        "ship_id": user_ship.id,
        "ship_name": user_ship.shipname,
        "hull_damage": user_ship.damage,
        "shield_status": {
            "type": user_ship.shield_type,
            "status": user_ship.shield_status,
            "charge": user_ship.shield_charge
        },
        "system_damage": {
            "tactical": user_ship.tactical,
            "helm": user_ship.helm,
            "fire_control": user_ship.fire_control
        },
        "energy_level": user_ship.energy,
        "repair_status": user_ship.repair,
        "overall_condition": "CRITICAL" if user_ship.damage > 80 else 
                           "HEAVY" if user_ship.damage > 60 else
                           "MODERATE" if user_ship.damage > 30 else
                           "LIGHT" if user_ship.damage > 10 else "GOOD"
    }


@router.post("/battle/emergency-repair", response_model=Dict[str, Any])
async def initiate_emergency_repair(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate emergency repair sequence"""
    # Get user's active ship
    user_ship = db.query(Ship).filter(
        Ship.user_id == current_user.id,
        Ship.status == 0
    ).first()
    
    if not user_ship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active ship found"
        )
    
    if user_ship.repair:
        return {
            "success": False,
            "message": "Repairs already in progress"
        }
    
    if user_ship.energy < 1000:
        return {
            "success": False,
            "message": "Insufficient energy for emergency repairs"
        }
    
    # Start repairs
    user_ship.repair = True
    user_ship.energy -= 1000
    db.commit()
    
    return {
        "success": True,
        "message": "Emergency repair sequence initiated",
        "energy_consumed": 1000,
        "estimated_repair_time": "10 ticks"
    }
