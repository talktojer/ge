"""
Galactic Empire - Mine Field API

This module provides REST API endpoints for advanced mine field operations.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from ..models.base import get_db
from ..core.auth import auth_service, get_current_user
from ..core.mine_service import mine_service

router = APIRouter(prefix="/mines", tags=["mines"])


# Pydantic models for API requests/responses
class MineLayRequest(BaseModel):
    ship_id: int
    x_coord: float
    y_coord: float
    mine_type: int = 0
    damage_potential: Optional[int] = None
    is_visible: bool = False


class MineFieldRequest(BaseModel):
    ship_id: int
    center_x: float
    center_y: float
    field_size: int
    mine_count: int
    mine_type: int = 0
    pattern: str = "grid"


class MineTriggerRequest(BaseModel):
    ship_id: int


# Mine endpoints
@router.post("/lay", response_model=Dict[str, Any])
async def lay_mine(
    mine_data: MineLayRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lay a mine at specified coordinates"""
    try:
        result = mine_service.lay_mine(
            db=db,
            user_id=current_user["id"],
            ship_id=mine_data.ship_id,
            x_coord=mine_data.x_coord,
            y_coord=mine_data.y_coord,
            mine_type=mine_data.mine_type,
            damage_potential=mine_data.damage_potential,
            is_visible=mine_data.is_visible
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to lay mine"
        )


@router.post("/field", response_model=Dict[str, Any])
async def lay_mine_field(
    field_data: MineFieldRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lay a mine field with multiple mines in a pattern"""
    try:
        result = mine_service.lay_mine_field(
            db=db,
            user_id=current_user["id"],
            ship_id=field_data.ship_id,
            center_x=field_data.center_x,
            center_y=field_data.center_y,
            field_size=field_data.field_size,
            mine_count=field_data.mine_count,
            mine_type=field_data.mine_type,
            pattern=field_data.pattern
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to lay mine field"
        )


@router.get("/detect/{x_coord}/{y_coord}", response_model=List[Dict[str, Any]])
async def detect_mines(
    x_coord: float,
    y_coord: float,
    detection_range: float = Query(10000, ge=1000, le=20000),
    ship_class: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Detect mines in range"""
    try:
        result = mine_service.detect_mines(
            db=db,
            x_coord=x_coord,
            y_coord=y_coord,
            detection_range=detection_range,
            ship_class=ship_class
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect mines"
        )


@router.post("/trigger/{mine_id}", response_model=Dict[str, Any])
async def trigger_mine(
    mine_id: int,
    trigger_data: MineTriggerRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger a mine and calculate damage"""
    try:
        result = mine_service.trigger_mine(
            db=db,
            mine_id=mine_id,
            ship_id=trigger_data.ship_id,
            user_id=current_user["id"]
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger mine"
        )


@router.post("/disarm/{mine_id}", response_model=Dict[str, Any])
async def disarm_mine(
    mine_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Attempt to disarm a mine"""
    try:
        result = mine_service.disarm_mine(
            db=db,
            mine_id=mine_id,
            user_id=current_user["id"]
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disarm mine"
        )


@router.get("/my-mines", response_model=List[Dict[str, Any]])
async def get_my_mines(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all mines owned by current user"""
    try:
        result = mine_service.get_user_mines(db=db, user_id=current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user mines"
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_mine_statistics(
    db: Session = Depends(get_db)
):
    """Get mine field system statistics"""
    try:
        result = mine_service.get_mine_field_statistics(db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get mine statistics"
        )
