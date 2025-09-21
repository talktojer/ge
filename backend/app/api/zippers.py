"""
Galactic Empire - Zipper API

This module provides REST API endpoints for zipper weapon operations and teleportation.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from ..models.base import get_db
from ..core.auth import auth_service
from ..core.zipper_service import zipper_service
from ..api.users import get_current_user

router = APIRouter(prefix="/zippers", tags=["zippers"])


# Pydantic models for API requests/responses
class ZipperFireRequest(BaseModel):
    ship_id: int


class EmergencyTeleportRequest(BaseModel):
    ship_id: int
    target_x: Optional[float] = None
    target_y: Optional[float] = None


class BoundaryCheckRequest(BaseModel):
    ship_id: int


# Zipper endpoints
@router.post("/fire", response_model=Dict[str, Any])
async def fire_zipper(
    zipper_data: ZipperFireRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fire zipper weapon to trigger nearby mines"""
    try:
        result = zipper_service.fire_zipper(
            db=db,
            user_id=current_user["id"],
            ship_id=zipper_data.ship_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fire zipper"
        )


@router.post("/emergency-teleport", response_model=Dict[str, Any])
async def emergency_teleport(
    teleport_data: EmergencyTeleportRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Emergency teleportation to a specific location or random location"""
    try:
        result = zipper_service.emergency_teleport(
            db=db,
            user_id=current_user["id"],
            ship_id=teleport_data.ship_id,
            target_x=teleport_data.target_x,
            target_y=teleport_data.target_y
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform emergency teleportation"
        )


@router.post("/check-boundary", response_model=Dict[str, Any])
async def check_boundary_teleport(
    boundary_data: BoundaryCheckRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if ship is out of bounds and needs teleportation"""
    try:
        result = zipper_service.check_boundary_teleport(
            db=db,
            ship_id=boundary_data.ship_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check boundary teleportation"
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_zipper_statistics(
    db: Session = Depends(get_db)
):
    """Get zipper system statistics"""
    try:
        result = zipper_service.get_zipper_statistics(db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get zipper statistics"
        )
