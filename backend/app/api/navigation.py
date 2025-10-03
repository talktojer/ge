"""
Galactic Empire - Navigation API endpoints

This module provides API endpoints for navigation commands including
sector navigation, jettison, and other missing commands from the original game.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..core.database import get_db
from ..core.auth import get_current_user
from ..core.coordinates import Coordinate, get_sector, distance
from ..core.navigation_service import NavigationService
from ..models.user import User
from ..models.ship import Ship

router = APIRouter(prefix="/api/navigation", tags=["navigation"])


# Pydantic models for requests
class NavigateRequest(BaseModel):
    sector_x: int
    sector_y: int


class JettisonRequest(BaseModel):
    item_type: str  # "men", "tro", "mis", "tor", "ion", "flu", "foo", "fig", "dec", "min", "jam", "zip", "gol"
    quantity: Optional[int] = None  # None means jettison all


class MaintenanceRequest(BaseModel):
    planet_id: Optional[int] = None  # If None, use current planet


class NewShipRequest(BaseModel):
    ship_type: str  # "shield", "ship", "phaser"
    class_number: int


class SellRequest(BaseModel):
    item_type: str
    quantity: int


class FrequencyRequest(BaseModel):
    channel: str  # "A", "B", "C"
    frequency: Optional[str] = None  # None means set to "hail"


class WhoRequest(BaseModel):
    show_all: bool = False


@router.post("/navigate")
async def navigate_to_sector(
    request: NavigateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Navigate to a specific sector (NAV command)"""
    try:
        nav_service = NavigationService(db)
        
        # Get user's current ship
        ship = db.query(Ship).filter(
            Ship.user_id == current_user.id,
            Ship.status == 1  # Active
        ).first()
        
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active ship found"
            )
        
        # Calculate navigation information
        current_sector = get_sector(Coordinate(ship.x_coord, ship.y_coord))
        target_sector = Coordinate(request.sector_x * 10000, request.sector_y * 10000)
        
        # Calculate bearing and distance
        nav_info = nav_service.calculate_navigation(
            Coordinate(ship.x_coord, ship.y_coord),
            target_sector
        )
        
        return {
            "success": True,
            "current_sector": {
                "x": current_sector.x,
                "y": current_sector.y
            },
            "target_sector": {
                "x": request.sector_x,
                "y": request.sector_y
            },
            "bearing": nav_info["bearing"],
            "distance": nav_info["distance"],
            "estimated_time": nav_info["estimated_time"],
            "message": f"Bearing {nav_info['bearing']:.1f}°, Distance {nav_info['distance']:.0f} parsecs"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Navigation calculation failed: {str(e)}"
        )


@router.post("/jettison")
async def jettison_cargo(
    request: JettisonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Jettison cargo to free up space (JET command)"""
    try:
        nav_service = NavigationService(db)
        
        # Get user's current ship
        ship = db.query(Ship).filter(
            Ship.user_id == current_user.id,
            Ship.status == 1  # Active
        ).first()
        
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active ship found"
            )
        
        # Jettison the specified items
        result = nav_service.jettison_cargo(ship.id, request.item_type, request.quantity)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": result["message"],
            "jettisoned": result["jettisoned"],
            "remaining": result["remaining"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Jettison failed: {str(e)}"
        )


@router.post("/maintenance")
async def request_maintenance(
    request: MaintenanceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request ship maintenance (MAINT command)"""
    try:
        nav_service = NavigationService(db)
        
        # Get user's current ship
        ship = db.query(Ship).filter(
            Ship.user_id == current_user.id,
            Ship.status == 1  # Active
        ).first()
        
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active ship found"
            )
        
        # Request maintenance
        result = nav_service.request_maintenance(ship.id, request.planet_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": result["message"],
            "cost": result["cost"],
            "repair_time": result["repair_time"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Maintenance request failed: {str(e)}"
        )


@router.post("/new")
async def purchase_new_equipment(
    request: NewShipRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Purchase new ship, shield, or phaser system (NEW command)"""
    try:
        nav_service = NavigationService(db)
        
        # Get user's current ship
        ship = db.query(Ship).filter(
            Ship.user_id == current_user.id,
            Ship.status == 1  # Active
        ).first()
        
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active ship found"
            )
        
        # Purchase new equipment
        result = nav_service.purchase_new_equipment(
            ship.id, 
            request.ship_type, 
            request.class_number
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": result["message"],
            "cost": result["cost"],
            "new_equipment": result["new_equipment"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Purchase failed: {str(e)}"
        )


@router.post("/sell")
async def sell_goods(
    request: SellRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sell goods back to Zygor (SELL command)"""
    try:
        nav_service = NavigationService(db)
        
        # Get user's current ship
        ship = db.query(Ship).filter(
            Ship.user_id == current_user.id,
            Ship.status == 1  # Active
        ).first()
        
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active ship found"
            )
        
        # Sell goods
        result = nav_service.sell_goods(ship.id, request.item_type, request.quantity)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": result["message"],
            "sold": result["sold"],
            "payment": result["payment"],
            "transfer_tax": result["transfer_tax"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sell failed: {str(e)}"
        )


@router.post("/frequency")
async def set_communication_frequency(
    request: FrequencyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set communication channel frequency (FREQ command)"""
    try:
        nav_service = NavigationService(db)
        
        # Set frequency
        result = nav_service.set_communication_frequency(
            current_user.id,
            request.channel,
            request.frequency
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": result["message"],
            "channel": request.channel,
            "frequency": result["frequency"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Frequency setting failed: {str(e)}"
        )


@router.get("/who")
async def list_online_players(
    show_all: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List online players (WHO command)"""
    try:
        nav_service = NavigationService(db)
        
        # Get online players
        players = nav_service.get_online_players(show_all)
        
        return {
            "success": True,
            "players": players,
            "total_count": len(players)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get online players: {str(e)}"
        )


@router.post("/clear-screen")
async def clear_screen(
    current_user: User = Depends(get_current_user)
):
    """Clear screen command (CLS command)"""
    # This is primarily a frontend command, but we can log it
    return {
        "success": True,
        "message": "Screen cleared",
        "timestamp": "2024-12-19T00:00:00Z"
    }


@router.get("/help/{command}")
async def get_command_help(
    command: str,
    current_user: User = Depends(get_current_user)
):
    """Get help for a specific command (HELP command)"""
    help_texts = {
        "navigate": "Navigate to a specific sector. Usage: navigate <sector_x> <sector_y>",
        "jettison": "Jettison cargo to free up space. Usage: jettison [ALL/<number>] [item_type]",
        "maintenance": "Request ship maintenance. Usage: maintenance [planet_id]",
        "new": "Purchase new ship, shield, or phaser system. Usage: new <type> <class>",
        "sell": "Sell goods back to Zygor. Usage: sell <quantity> <item_type>",
        "frequency": "Set communication channel frequency. Usage: freq <channel> [frequency/hail]",
        "who": "List online players. Usage: who [all]",
        "cls": "Clear screen. Usage: cls"
    }
    
    if command not in help_texts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Help not found for command: {command}"
        )
    
    return {
        "success": True,
        "command": command,
        "help_text": help_texts[command]
    }
