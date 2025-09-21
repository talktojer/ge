"""
Galactic Empire - Spy API

This module provides REST API endpoints for spy operations and intelligence gathering.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from ..models.base import get_db
from ..core.auth import auth_service, get_current_user
from ..core.spy_service import spy_service

router = APIRouter(prefix="/spies", tags=["spies"])


# Pydantic models for API requests/responses
class SpyDeployRequest(BaseModel):
    ship_id: int
    planet_id: int


class SpyPlanetInfoRequest(BaseModel):
    planet_id: int


# Spy endpoints
@router.post("/deploy", response_model=Dict[str, Any])
async def deploy_spy(
    deploy_data: SpyDeployRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deploy a spy on an enemy planet"""
    try:
        result = spy_service.deploy_spy(
            db=db,
            user_id=current_user["id"],
            ship_id=deploy_data.ship_id,
            planet_id=deploy_data.planet_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deploy spy"
        )


@router.get("/status", response_model=Dict[str, Any])
async def get_spy_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get spy deployment status for current user"""
    try:
        result = spy_service.get_spy_status(db=db, user_id=current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get spy status"
        )


@router.get("/planet/{planet_id}", response_model=Dict[str, Any])
async def get_planet_spy_info(
    planet_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get spy information for a specific planet"""
    try:
        result = spy_service.get_planet_spy_info(
            db=db,
            planet_id=planet_id,
            user_id=current_user["id"]
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get planet spy info"
        )


@router.post("/process/{planet_id}", response_model=Dict[str, Any])
async def process_spy_activities(
    planet_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process spy activities on a planet (admin/system function)"""
    try:
        result = spy_service.process_spy_activities(db=db, planet_id=planet_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process spy activities"
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_spy_statistics(
    db: Session = Depends(get_db)
):
    """Get spy system statistics"""
    try:
        result = spy_service.get_spy_statistics(db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get spy statistics"
        )
