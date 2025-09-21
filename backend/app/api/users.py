"""
Galactic Empire - User Management API

This module provides REST API endpoints for user management including
registration, login, profile management, and ship operations.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
import logging

from ..models.base import get_db
from ..core.auth import auth_service, get_current_user
from ..core.user_service import user_service
from ..core.coordinates import Coordinate
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer()


# Pydantic models for API requests/responses
class UserRegistrationRequest(BaseModel):
    userid: str
    email: EmailStr
    password: str


class UserLoginRequest(BaseModel):
    userid: str
    password: str


class UserPreferencesRequest(BaseModel):
    scan_names: Optional[bool] = None
    scan_home: Optional[bool] = None
    scan_full: Optional[bool] = None
    msg_filter: Optional[bool] = None
    preferred_ship_class: Optional[int] = None
    auto_repair: Optional[bool] = None
    auto_shield: Optional[bool] = None


class ShipCreateRequest(BaseModel):
    ship_name: str
    ship_class: int


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str


class UserResponse(BaseModel):
    id: int
    userid: str
    email: str
    is_active: bool
    is_verified: bool
    score: int
    kills: int
    planets: int
    cash: int
    debt: int
    population: int
    noships: int
    teamcode: int
    last_login: Optional[str] = None
    created_at: str


class ShipResponse(BaseModel):
    id: int
    ship_name: str
    ship_class: int
    status: str
    position: Dict[str, float]
    heading: float
    speed: float
    energy: int
    shields: int
    max_shields: int
    damage: float
    created_at: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    session_token: str
    token_type: str
    user: UserResponse


# User registration and authentication endpoints
@router.post("/register", response_model=Dict[str, Any])
async def register_user(
    user_data: UserRegistrationRequest,
    db: Session = Depends(get_db)
):
    """Register a new user (email verification disabled for now)"""
    try:
        result = user_service.register_user(
            db=db,
            userid=user_data.userid,
            email=user_data.email,
            password=user_data.password
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/verify-email", response_model=Dict[str, Any])
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify user email with token (placeholder - email system not implemented)"""
    try:
        result = user_service.verify_email(db=db, token=token)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: UserLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login user"""
    try:
        # Get client IP and user agent
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        result = user_service.login_user(
            db=db,
            userid=login_data.userid,
            password=login_data.password,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return LoginResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout", response_model=Dict[str, Any])
async def logout_user(
    session_token: str,
    db: Session = Depends(get_db)
):
    """Logout user"""
    try:
        result = user_service.logout_user(db=db, session_token=session_token)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


# User profile and management endpoints
@router.get("/profile", response_model=Dict[str, Any])
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile"""
    try:
        result = user_service.get_user_profile(db=db, user_id=current_user["id"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )


@router.put("/preferences", response_model=Dict[str, Any])
async def update_user_preferences(
    preferences: UserPreferencesRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences"""
    try:
        # Convert to dict, excluding None values
        prefs_dict = {k: v for k, v in preferences.dict().items() if v is not None}
        
        result = user_service.update_user_preferences(
            db=db,
            user_id=current_user["id"],
            preferences=prefs_dict
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update preferences error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_user_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics"""
    try:
        result = user_service.get_user_statistics(db=db, user_id=current_user["id"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )


# Ship management endpoints
@router.post("/ships", response_model=Dict[str, Any])
async def create_ship(
    ship_data: ShipCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new ship"""
    try:
        result = user_service.create_ship(
            db=db,
            user_id=current_user["id"],
            ship_name=ship_data.ship_name,
            ship_class=ship_data.ship_class
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create ship error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ship"
        )


@router.get("/ships", response_model=List[ShipResponse])
async def get_user_ships(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user ships"""
    try:
        result = user_service.get_user_ships(db=db, user_id=current_user["id"])
        return [ShipResponse(**ship) for ship in result]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get ships error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ships"
        )


@router.post("/ships/{ship_id}/select", response_model=Dict[str, Any])
async def select_ship(
    ship_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Select a ship as active"""
    try:
        result = user_service.select_ship(
            db=db,
            user_id=current_user["id"],
            ship_id=ship_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Select ship error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to select ship"
        )


# Password management endpoints
@router.put("/password", response_model=Dict[str, Any])
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        result = user_service.change_password(
            db=db,
            user_id=current_user["id"],
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/password-reset", response_model=Dict[str, Any])
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset (placeholder - email system not implemented)"""
    try:
        result = user_service.request_password_reset(
            db=db,
            email=reset_data.email
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request password reset"
        )


@router.post("/password-reset/confirm", response_model=Dict[str, Any])
async def confirm_password_reset(
    reset_data: PasswordResetConfirmRequest,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token (placeholder - email system not implemented)"""
    try:
        result = user_service.reset_password(
            db=db,
            token=reset_data.token,
            new_password=reset_data.new_password
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirm error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


# Public endpoints (no authentication required)
@router.get("/leaderboard", response_model=List[Dict[str, Any]])
async def get_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get user leaderboard by score"""
    try:
        from ..models.user import User
        
        # Get top users by score
        users = db.query(User).filter(
            User.is_active == True,
            User.is_verified == True
        ).order_by(User.score.desc()).limit(limit).all()
        
        leaderboard = []
        for i, user in enumerate(users, 1):
            leaderboard.append({
                "rank": i,
                "userid": user.userid,
                "score": user.score,
                "kills": user.kills,
                "planets": user.planets,
                "cash": user.cash
            })
        
        return leaderboard
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get leaderboard"
        )
