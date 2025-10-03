"""
Ship Types, Classes, and Operations API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.core.ship_service import ShipTypeService, ShipClassService, ShipConfigurationService
from app.core.ship_operations_service import ShipOperationsService
from app.core.ship_operations import NavigationCommand
from app.models.ship import ShipType, ShipClass, Ship
from app.core.auth import get_current_user
from app.models.user import User
from app.websocket_events import game_broadcaster
import asyncio

router = APIRouter()


# Pydantic models for request/response
class NavigationRequest(BaseModel):
    command_type: str  # "warp", "impulse", "rotate", "stop"
    target_speed: Optional[float] = None
    target_heading: Optional[float] = None
    warp_factor: Optional[int] = None
    impulse_power: Optional[int] = None


class ShieldRequest(BaseModel):
    action: str  # "up", "down", "charge", "set_type"
    shield_type: Optional[int] = None


class CloakingRequest(BaseModel):
    action: str  # "engage", "disengage"


class CombatRequest(BaseModel):
    action_type: str  # "fire_phasers", "fire_torpedo", etc.
    target_id: Optional[int] = None
    hyper_phasers: Optional[bool] = False


class CargoRequest(BaseModel):
    action: str  # "load", "unload"
    item_type: int
    quantity: int


@router.get("/ship-types", response_model=List[Dict[str, Any]])
async def get_ship_types(db: Session = Depends(get_db)):
    """Get all ship types (USER, CYBORG, DROID)"""
    ship_type_service = ShipTypeService(db)
    ship_types = ship_type_service.get_all_ship_types()
    
    return [
        {
            "id": ship_type.id,
            "type_name": ship_type.type_name,
            "description": ship_type.description,
            "created_at": ship_type.created_at
        }
        for ship_type in ship_types
    ]


@router.get("/ship-classes", response_model=List[Dict[str, Any]])
async def get_ship_classes(
    ship_type: str = None,
    db: Session = Depends(get_db)
):
    """Get ship classes, optionally filtered by ship type"""
    ship_class_service = ShipClassService(db)
    
    if ship_type:
        ship_classes = ship_class_service.get_ship_classes_by_type(ship_type.upper())
    else:
        ship_classes = ship_class_service.get_all_ship_classes()
    
    return [
        {
            "id": ship_class.id,
            "class_number": ship_class.class_number,
            "typename": ship_class.typename,
            "shipname": ship_class.shipname,
            "ship_type": ship_class.ship_type.type_name,
            "max_shields": ship_class.max_shields,
            "max_phasers": ship_class.max_phasers,
            "max_torpedoes": ship_class.max_torpedoes,
            "max_missiles": ship_class.max_missiles,
            "has_decoy": ship_class.has_decoy,
            "has_jammer": ship_class.has_jammer,
            "has_zipper": ship_class.has_zipper,
            "has_mine": ship_class.has_mine,
            "has_attack_planet": ship_class.has_attack_planet,
            "has_cloaking": ship_class.has_cloaking,
            "max_acceleration": ship_class.max_acceleration,
            "max_warp": ship_class.max_warp,
            "max_tons": ship_class.max_tons,
            "max_price": ship_class.max_price,
            "max_points": ship_class.max_points,
            "scan_range": ship_class.scan_range,
            "is_active": ship_class.is_active
        }
        for ship_class in ship_classes
    ]


@router.get("/ship-classes/user", response_model=List[Dict[str, Any]])
async def get_user_ship_classes(db: Session = Depends(get_db)):
    """Get all USER ship classes available for purchase"""
    ship_class_service = ShipClassService(db)
    ship_classes = ship_class_service.get_user_ship_classes()
    
    return [
        {
            "id": ship_class.id,
            "class_number": ship_class.class_number,
            "typename": ship_class.typename,
            "max_shields": ship_class.max_shields,
            "max_phasers": ship_class.max_phasers,
            "max_torpedoes": ship_class.max_torpedoes,
            "max_missiles": ship_class.max_missiles,
            "special_equipment": {
                "decoy_launcher": ship_class.has_decoy,
                "jammer": ship_class.has_jammer,
                "zipper": ship_class.has_zipper,
                "mine_launcher": ship_class.has_mine,
                "attack_planet": ship_class.has_attack_planet,
                "cloaking": ship_class.has_cloaking
            },
            "performance": {
                "max_acceleration": ship_class.max_acceleration,
                "max_warp_speed": ship_class.max_warp,
                "cargo_capacity": ship_class.max_tons,
                "scan_range": ship_class.scan_range
            },
            "economics": {
                "purchase_price": ship_class.max_price,
                "kill_points": ship_class.max_points
            },
            "is_active": ship_class.is_active
        }
        for ship_class in ship_classes
    ]


@router.get("/ship-classes/{class_id}", response_model=Dict[str, Any])
async def get_ship_class_details(
    class_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific ship class"""
    ship_class_service = ShipClassService(db)
    ship_class = ship_class_service.get_ship_class_by_id(class_id)
    
    if not ship_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ship class not found"
        )
    
    capabilities = ship_class_service.get_ship_capabilities(ship_class)
    statistics = ship_class_service.get_ship_statistics(ship_class)
    
    return {
        "id": ship_class.id,
        "class_number": ship_class.class_number,
        "typename": ship_class.typename,
        "shipname": ship_class.shipname,
        "ship_type": ship_class.ship_type.type_name,
        "capabilities": capabilities,
        "statistics": statistics,
        "is_active": ship_class.is_active,
        "help_message": ship_class.help_message
    }


@router.get("/ship-classes/{class_id}/capabilities", response_model=Dict[str, Any])
async def get_ship_class_capabilities(
    class_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed capabilities for a specific ship class"""
    ship_class_service = ShipClassService(db)
    ship_class = ship_class_service.get_ship_class_by_id(class_id)
    
    if not ship_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ship class not found"
        )
    
    return ship_class_service.get_ship_capabilities(ship_class)


@router.get("/available-ships", response_model=List[Dict[str, Any]])
async def get_available_ships_for_purchase(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ships available for purchase by the current user"""
    ship_config_service = ShipConfigurationService(db)
    return ship_config_service.get_available_ships_for_purchase(current_user)


@router.post("/ship-classes/{class_id}/can-purchase")
async def check_can_purchase_ship_class(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if the current user can purchase a specific ship class"""
    ship_class_service = ShipClassService(db)
    ship_class = ship_class_service.get_ship_class_by_id(class_id)
    
    if not ship_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ship class not found"
        )
    
    can_purchase = ship_class_service.can_purchase_ship_class(ship_class, current_user)
    
    return {
        "class_id": class_id,
        "class_name": ship_class.typename,
        "can_purchase": can_purchase,
        "required_cash": ship_class.max_price,
        "user_cash": current_user.cash,
        "reason": "Insufficient funds" if not can_purchase and ship_class.max_price > current_user.cash else "Available"
    }


@router.post("/initialize-ship-system")
async def initialize_ship_system(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initialize the ship types and classes system (admin only)"""
    # TODO: Add admin check
    try:
        ship_config_service = ShipConfigurationService(db)
        ship_config_service.initialize_default_ship_types()
        ship_config_service.initialize_default_ship_classes()
        
        return {
            "message": "Ship system initialized successfully",
            "ship_types_created": 3,
            "ship_classes_created": 5  # This would be 12 in full implementation
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize ship system: {str(e)}"
        )


@router.get("/ship-classes/{class_number}/by-number", response_model=Dict[str, Any])
async def get_ship_class_by_number(
    class_number: int,
    db: Session = Depends(get_db)
):
    """Get ship class by class number (S01, S02, etc.)"""
    ship_class_service = ShipClassService(db)
    ship_class = ship_class_service.get_ship_class_by_number(class_number)
    
    if not ship_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ship class {class_number} not found"
        )
    
    capabilities = ship_class_service.get_ship_capabilities(ship_class)
    statistics = ship_class_service.get_ship_statistics(ship_class)
    
    return {
        "id": ship_class.id,
        "class_number": ship_class.class_number,
        "typename": ship_class.typename,
        "shipname": ship_class.shipname,
        "ship_type": ship_class.ship_type.type_name,
        "capabilities": capabilities,
        "statistics": statistics,
        "is_active": ship_class.is_active
    }


# Ship Operations Endpoints

@router.get("/ships/{ship_id}/status", response_model=Dict[str, Any])
async def get_ship_status(
    ship_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive ship status"""
    ship_ops_service = ShipOperationsService(db)
    
    # Verify ship ownership
    ship = db.query(Ship).filter(Ship.id == ship_id, Ship.user_id == current_user.id).first()
    if not ship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ship not found or not owned by user"
        )
    
    return ship_ops_service.get_ship_status(ship_id)


@router.post("/ships/{ship_id}/navigation", response_model=Dict[str, Any])
async def execute_navigation_command(
    ship_id: int,
    nav_request: NavigationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute navigation command for ship"""
    ship_ops_service = ShipOperationsService(db)
    
    # Verify ship ownership
    ship = db.query(Ship).filter(Ship.id == ship_id, Ship.user_id == current_user.id).first()
    if not ship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ship not found or not owned by user"
        )
    
    # Convert request to NavigationCommand
    command = NavigationCommand(
        command_type=nav_request.command_type,
        target_speed=nav_request.target_speed,
        target_heading=nav_request.target_heading,
        warp_factor=nav_request.warp_factor,
        impulse_power=nav_request.impulse_power
    )
    
    result = ship_ops_service.execute_navigation_command(ship_id, command)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Navigation command failed")
        )
    
    # Broadcast ship movement update via WebSocket
    if result.get("success", False) and result.get("ship_data"):
        ship_data = result.get("ship_data", {})
        ship_data["timestamp"] = result.get("timestamp")
        
        # Run WebSocket broadcast in background
        asyncio.create_task(game_broadcaster.ship_moved(ship_id, ship_data))
    
    return result


@router.post("/ships/{ship_id}/shields", response_model=Dict[str, Any])
async def manage_shields(
    ship_id: int,
    shield_request: ShieldRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manage ship shield systems"""
    ship_ops_service = ShipOperationsService(db)
    
    # Verify ship ownership
    ship = db.query(Ship).filter(Ship.id == ship_id, Ship.user_id == current_user.id).first()
    if not ship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ship not found or not owned by user"
        )
    
    result = ship_ops_service.manage_shields(ship_id, shield_request.action, shield_request.shield_type)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Shield operation failed")
        )
    
    return result


@router.post("/ships/{ship_id}/combat", response_model=Dict[str, Any])
async def execute_combat_action(
    ship_id: int,
    combat_request: CombatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute combat action"""
    ship_ops_service = ShipOperationsService(db)
    
    # Verify ship ownership
    ship = db.query(Ship).filter(Ship.id == ship_id, Ship.user_id == current_user.id).first()
    if not ship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ship not found or not owned by user"
        )
    
    result = ship_ops_service.execute_combat_action(
        ship_id, 
        combat_request.action_type,
        combat_request.target_id,
        hyper_phasers=combat_request.hyper_phasers
    )
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Combat action failed")
        )
    
    return result


