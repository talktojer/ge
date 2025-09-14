"""
Galactic Empire - Team Management API

This module provides REST API endpoints for team management including
team creation, joining, leaving, and member management.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.auth import auth_service
from ..core.team_service import team_service
from ..api.users import get_current_user

router = APIRouter(prefix="/teams", tags=["teams"])


# Pydantic models for API requests/responses
class TeamCreateRequest(BaseModel):
    team_name: str
    password: Optional[str] = None
    secret: Optional[str] = None


class TeamJoinRequest(BaseModel):
    team_code: int
    password: Optional[str] = None


class TeamPasswordUpdateRequest(BaseModel):
    new_password: str


class TeamSecretUpdateRequest(BaseModel):
    new_secret: str


class TeamResponse(BaseModel):
    id: int
    team_name: str
    team_code: int
    teamcount: int
    teamscore: int
    flag: int
    created_at: str


class TeamMemberResponse(BaseModel):
    id: int
    userid: str
    score: int
    kills: int
    planets: int
    cash: int
    last_login: Optional[str] = None


class TeamInfoResponse(BaseModel):
    team: TeamResponse
    members: List[TeamMemberResponse]


# Team management endpoints
@router.post("/create", response_model=Dict[str, Any])
async def create_team(
    team_data: TeamCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new team"""
    try:
        result = team_service.create_team(
            db=db,
            user_id=current_user["id"],
            team_name=team_data.team_name,
            password=team_data.password,
            secret=team_data.secret
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create team"
        )


@router.post("/join", response_model=Dict[str, Any])
async def join_team(
    join_data: TeamJoinRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join an existing team"""
    try:
        result = team_service.join_team(
            db=db,
            user_id=current_user["id"],
            team_code=join_data.team_code,
            password=join_data.password
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join team"
        )


@router.post("/leave", response_model=Dict[str, Any])
async def leave_team(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Leave current team"""
    try:
        result = team_service.leave_team(
            db=db,
            user_id=current_user["id"]
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to leave team"
        )


@router.get("/my-team", response_model=TeamInfoResponse)
async def get_my_team(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's team information"""
    try:
        from ..models.user import User
        
        user = db.query(User).filter(User.id == current_user["id"]).first()
        if not user or not user.team_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not in a team"
            )
        
        result = team_service.get_team_info(db=db, team_id=user.team_id)
        return TeamInfoResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get team information"
        )


@router.get("/{team_id}", response_model=TeamInfoResponse)
async def get_team_info(
    team_id: int,
    db: Session = Depends(get_db)
):
    """Get team information by ID"""
    try:
        result = team_service.get_team_info(db=db, team_id=team_id)
        return TeamInfoResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get team information"
        )


@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_team_members(
    team_id: int,
    db: Session = Depends(get_db)
):
    """Get team members"""
    try:
        result = team_service.get_team_members(db=db, team_id=team_id)
        return [TeamMemberResponse(**member) for member in result]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get team members"
        )


@router.put("/password", response_model=Dict[str, Any])
async def update_team_password(
    password_data: TeamPasswordUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update team password (team leader only)"""
    try:
        from ..models.user import User
        
        user = db.query(User).filter(User.id == current_user["id"]).first()
        if not user or not user.team_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not in a team"
            )
        
        result = team_service.update_team_password(
            db=db,
            team_id=user.team_id,
            user_id=current_user["id"],
            new_password=password_data.new_password
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update team password"
        )


@router.put("/secret", response_model=Dict[str, Any])
async def update_team_secret(
    secret_data: TeamSecretUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update team secret (team leader only)"""
    try:
        from ..models.user import User
        
        user = db.query(User).filter(User.id == current_user["id"]).first()
        if not user or not user.team_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not in a team"
            )
        
        result = team_service.update_team_secret(
            db=db,
            team_id=user.team_id,
            user_id=current_user["id"],
            new_secret=secret_data.new_secret
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update team secret"
        )


# Public endpoints
@router.get("/leaderboard", response_model=List[Dict[str, Any]])
async def get_team_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get team leaderboard by score"""
    try:
        result = team_service.get_team_leaderboard(db=db, limit=limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get team leaderboard"
        )


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_teams(
    q: str = Query(..., min_length=1, max_length=50),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Search for teams by name"""
    try:
        result = team_service.search_teams(db=db, query=q, limit=limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search teams"
        )
