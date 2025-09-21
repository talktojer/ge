"""
Galactic Empire - Wormhole API

This module provides REST API endpoints for wormhole navigation and management.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from ..models.base import get_db
from ..core.auth import auth_service, get_current_user
from ..core.wormhole_service import wormhole_service

router = APIRouter(prefix="/wormholes", tags=["wormholes"])


# Pydantic models for API requests/responses
class WormholeTransitRequest(BaseModel):
    ship_id: int
    approach_speed: float


class WormholeGenerationRequest(BaseModel):
    x_sect: int
    y_sect: int


class WormholeTableRequest(BaseModel):
    x_coord: float
    y_coord: float
    dest_x_coord: float
    dest_y_coord: float


# Wormhole endpoints
@router.post("/generate", response_model=Dict[str, Any])
async def generate_wormhole(
    generation_data: WormholeGenerationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a wormhole in a sector (admin/system function)"""
    try:
        result = wormhole_service.generate_wormhole(
            db=db,
            x_sect=generation_data.x_sect,
            y_sect=generation_data.y_sect
        )
        
        if result is None:
            return {
                "message": "No wormhole generated (failed odds roll or max wormholes reached)",
                "generated": False
            }
        
        return {
            "message": "Wormhole generated successfully",
            "generated": True,
            "wormhole": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate wormhole"
        )


@router.get("/sector/{x_sect}/{y_sect}", response_model=List[Dict[str, Any]])
async def get_wormholes_in_sector(
    x_sect: int,
    y_sect: int,
    db: Session = Depends(get_db)
):
    """Get all wormholes in a specific sector"""
    try:
        result = wormhole_service.find_wormholes_in_sector(db=db, x_sect=x_sect, y_sect=y_sect)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sector wormholes"
        )


@router.get("/near/{x_coord}/{y_coord}", response_model=List[Dict[str, Any]])
async def get_wormholes_near_position(
    x_coord: float,
    y_coord: float,
    radius: float = Query(1000, ge=100, le=10000),
    db: Session = Depends(get_db)
):
    """Find wormholes near a specific position"""
    try:
        result = wormhole_service.find_wormholes_near_position(
            db=db,
            x_coord=x_coord,
            y_coord=y_coord,
            radius=radius
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find nearby wormholes"
        )


@router.post("/transit/{wormhole_id}", response_model=Dict[str, Any])
async def transit_wormhole(
    wormhole_id: int,
    transit_data: WormholeTransitRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Attempt to transit through a wormhole"""
    try:
        result = wormhole_service.attempt_wormhole_transit(
            db=db,
            user_id=current_user["id"],
            ship_id=transit_data.ship_id,
            wormhole_id=wormhole_id,
            approach_speed=transit_data.approach_speed
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transit wormhole"
        )


@router.get("/map", response_model=Dict[str, Any])
async def get_wormhole_map(
    db: Session = Depends(get_db)
):
    """Get a map of all wormholes in the galaxy"""
    try:
        result = wormhole_service.get_wormhole_map(db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get wormhole map"
        )


@router.post("/table", response_model=Dict[str, Any])
async def create_wormhole_table_entry(
    table_data: WormholeTableRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a wormhole table entry for navigation"""
    try:
        result = wormhole_service.create_wormhole_table_entry(
            db=db,
            x_coord=table_data.x_coord,
            y_coord=table_data.y_coord,
            dest_x_coord=table_data.dest_x_coord,
            dest_y_coord=table_data.dest_y_coord
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create wormhole table entry"
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_wormhole_statistics(
    db: Session = Depends(get_db)
):
    """Get wormhole system statistics"""
    try:
        result = wormhole_service.get_wormhole_statistics(db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get wormhole statistics"
        )
