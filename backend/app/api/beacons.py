"""
Galactic Empire - Beacon API

This module provides REST API endpoints for beacon deployment and communication.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from ..models.base import get_db
from ..core.auth import auth_service
from ..core.beacon_service import beacon_service
from ..api.users import get_current_user

router = APIRouter(prefix="/beacons", tags=["beacons"])


# Pydantic models for API requests/responses
class BeaconDeployRequest(BaseModel):
    x_coord: float
    y_coord: float
    message: str
    beacon_type: int = 0
    priority: int = 0
    is_public: bool = True
    expires_hours: Optional[int] = None


class BeaconUpdateRequest(BaseModel):
    new_message: str


class BeaconBroadcastRequest(BaseModel):
    message: str
    beacon_type: int = 0
    priority: int = 5


# Beacon endpoints
@router.post("/deploy", response_model=Dict[str, Any])
async def deploy_beacon(
    deploy_data: BeaconDeployRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deploy a beacon at specified coordinates"""
    try:
        result = beacon_service.deploy_beacon(
            db=db,
            user_id=current_user["id"],
            x_coord=deploy_data.x_coord,
            y_coord=deploy_data.y_coord,
            message=deploy_data.message,
            beacon_type=deploy_data.beacon_type,
            priority=deploy_data.priority,
            is_public=deploy_data.is_public,
            expires_hours=deploy_data.expires_hours
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deploy beacon"
        )


@router.get("/range/{x_coord}/{y_coord}", response_model=List[Dict[str, Any]])
async def get_beacons_in_range(
    x_coord: float,
    y_coord: float,
    range_limit: float = Query(5000, ge=100, le=20000),
    beacon_type: Optional[int] = Query(None, ge=0, le=9),
    db: Session = Depends(get_db)
):
    """Find beacons within range of a position"""
    try:
        result = beacon_service.find_beacons_in_range(
            db=db,
            x_coord=x_coord,
            y_coord=y_coord,
            range_limit=range_limit,
            beacon_type=beacon_type
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find beacons in range"
        )


@router.get("/message/{x_coord}/{y_coord}", response_model=Dict[str, Any])
async def get_beacon_message(
    x_coord: float,
    y_coord: float,
    db: Session = Depends(get_db)
):
    """Get beacon message at specific coordinates"""
    try:
        result = beacon_service.get_beacon_message(db=db, x_coord=x_coord, y_coord=y_coord)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get beacon message"
        )


@router.put("/update/{beacon_id}", response_model=Dict[str, Any])
async def update_beacon_message(
    beacon_id: int,
    update_data: BeaconUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update beacon message (owner only)"""
    try:
        result = beacon_service.update_beacon_message(
            db=db,
            beacon_id=beacon_id,
            user_id=current_user["id"],
            new_message=update_data.new_message
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update beacon message"
        )


@router.delete("/remove/{beacon_id}", response_model=Dict[str, Any])
async def remove_beacon(
    beacon_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a beacon (owner only)"""
    try:
        result = beacon_service.remove_beacon(
            db=db,
            beacon_id=beacon_id,
            user_id=current_user["id"]
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove beacon"
        )


@router.get("/my-beacons", response_model=List[Dict[str, Any]])
async def get_my_beacons(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all beacons owned by current user"""
    try:
        result = beacon_service.get_user_beacons(db=db, user_id=current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user beacons"
        )


@router.post("/broadcast", response_model=Dict[str, Any])
async def broadcast_message(
    broadcast_data: BeaconBroadcastRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Broadcast a message to all nearby beacons"""
    try:
        result = beacon_service.broadcast_message(
            db=db,
            user_id=current_user["id"],
            message=broadcast_data.message,
            beacon_type=broadcast_data.beacon_type,
            priority=broadcast_data.priority
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast message"
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_beacon_statistics(
    db: Session = Depends(get_db)
):
    """Get beacon system statistics"""
    try:
        result = beacon_service.get_beacon_statistics(db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get beacon statistics"
        )


@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_expired_beacons(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove expired beacons (admin/system function)"""
    try:
        result = beacon_service.cleanup_expired_beacons(db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired beacons"
        )
