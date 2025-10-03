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
from ..models.ship import Ship, ShipClass

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer()


# Pydantic models for API requests/responses
class UserRegistrationRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str


class UserLoginRequest(BaseModel):
    username: str
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
    energy: float
    shields: int
    max_shields: int
    damage: float
    created_at: str


class GameStateResponse(BaseModel):
    current_user: Optional[UserResponse] = None
    selected_ship: Optional[ShipResponse] = None
    selected_planet: Optional[Dict[str, Any]] = None
    game_time: str
    tick_number: int
    is_connected: bool


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
        # Validate password confirmation
        if user_data.password != user_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        # Use username as userid (they can be the same in this system)
        result = user_service.register_user(
            db=db,
            userid=user_data.username,
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
            userid=login_data.username,
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


@router.get("/game-state", response_model=GameStateResponse)
async def get_user_game_state(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's game state including profile, selected ship, and game info"""
    try:
        # Get user profile
        user_profile_data = user_service.get_user_profile(db=db, user_id=current_user["id"])
        user_data = user_profile_data["user"]  # Extract user data from nested structure
        
        # Ensure user has at least one ship (create starter ship if needed)
        user_ships = user_service.get_user_ships(db=db, user_id=current_user["id"])
        
        # If user has no ships, create a starter ship
        if not user_ships:
            logger.info(f"User {current_user['userid']} has no ships, creating starter ship...")
            try:
                starter_ship_result = user_service.create_ship(
                    db=db,
                    user_id=current_user["id"],
                    ship_name=f"{current_user['userid']}'s Starter Ship",
                    ship_class=1  # Ship class 1 - Interceptor
                )
                logger.info(f"Created starter ship for user {current_user['userid']}")
                # Refresh user ships after creation
                user_ships = user_service.get_user_ships(db=db, user_id=current_user["id"])
            except Exception as e:
                logger.error(f"Failed to create starter ship for user {current_user['userid']}: {e}")
        
        selected_ship = None
        if user_ships:
            # For now, just select the first ship as the active one
            # In the future, this should be based on user preference or last selected ship
            ship_data = user_ships[0]
            # Map database field names to ShipResponse field names
            ship_response_data = {
                "id": ship_data["id"],
                "ship_name": ship_data["ship_name"],
                "ship_class": ship_data["ship_class"],
                "status": "active" if ship_data["status"] == 1 else "inactive",
                "position": ship_data["position"],
                "heading": ship_data["heading"],
                "speed": ship_data["speed"],
                "energy": ship_data["energy"],
                "shields": ship_data["shields"],
                "max_shields": ship_data["max_shields"],
                "damage": ship_data["damage"],
                "created_at": ship_data.get("created_at", "").isoformat() if ship_data.get("created_at") else ""
            }
            selected_ship = ShipResponse(**ship_response_data)
        
        # Get current game time from game engine
        from ..core.game_engine import game_engine
        game_stats = game_engine.get_game_statistics()
        game_time = game_stats.get('game_time', '')
        tick_number = game_stats.get('tick_number', 0)
        
        return GameStateResponse(
            current_user=UserResponse(**user_data),
            selected_ship=selected_ship,
            selected_planet=None,  # TODO: Implement planet selection
            game_time=game_time,
            tick_number=tick_number,
            is_connected=True  # TODO: Implement actual connection status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get game state error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get game state"
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


@router.get("/ships", response_model=Dict[str, Any])
async def get_user_ships(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user ships"""
    try:
        ships = user_service.get_user_ships(db=db, user_id=current_user["id"])
        return {
            "items": ships,
            "page": 1,
            "per_page": len(ships),
            "total": len(ships),
            "pages": 1
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get ships error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ships"
        )


@router.get("/ships/{ship_id}", response_model=Dict[str, Any])
async def get_ship_details(
    ship_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed ship information"""
    try:
        ship = db.query(Ship).filter(
            Ship.id == ship_id,
            Ship.user_id == current_user["id"]
        ).first()
        
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ship not found"
            )
        
        # Get ship class information
        ship_class = db.query(ShipClass).filter(ShipClass.id == ship.ship_class_id).first()
        
        return {
            "id": ship.id,
            "name": ship.shipname,
            "owner_id": ship.user_id,
            "ship_type": ship_class.name if ship_class else "Unknown",
            "ship_class": ship.shpclass,
            "x": ship.x_coord,
            "y": ship.y_coord,
            "z": 0.0,
            "sector": 1,
            "heading": ship.heading,
            "speed": ship.speed,
            "hull_points": 100 - ship.damage,
            "max_hull_points": 100,
            "shields": ship.shield_charge,
            "max_shields": 100,
            "fuel": ship.energy,
            "max_fuel": 50000,
            "cargo_capacity": 1000,
            "cargo_used": 0,
            "weapons": ["Phaser"],
            "is_active": (ship.status or 0) == 0,
            "created_at": ship.created_at.isoformat() if ship.created_at else "2025-01-01T00:00:00Z",
            "last_updated": ship.updated_at.isoformat() if ship.updated_at else "2025-01-01T00:00:00Z",
            "status": "active" if (ship.status or 0) == 0 else "inactive",
            "damage": ship.damage,
            "energy": ship.energy,
            "kills": ship.kills,
            "phaser_strength": ship.phaser_strength,
            "shield_status": ship.shield_status,
            "cloak": ship.cloak,
            "hostile": ship.hostile
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get ship details error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ship details"
        )


@router.post("/ships/{ship_id}/move", response_model=Dict[str, Any])
async def move_ship(
    ship_id: int,
    movement_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Move ship to new coordinates"""
    try:
        ship = db.query(Ship).filter(
            Ship.id == ship_id,
            Ship.user_id == current_user["id"]
        ).first()
        
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ship not found"
            )
        
        # Update ship position
        ship.x_coord = movement_data.get("x", ship.x_coord)
        ship.y_coord = movement_data.get("y", ship.y_coord)
        ship.heading = movement_data.get("heading", ship.heading)
        ship.speed = movement_data.get("speed", ship.speed)
        
        db.commit()
        
        return {
            "message": "Ship moved successfully",
            "new_position": {
                "x": ship.x_coord,
                "y": ship.y_coord
            },
            "heading": ship.heading,
            "speed": ship.speed
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Move ship error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to move ship"
        )


@router.post("/ships/{ship_id}/repair", response_model=Dict[str, Any])
async def repair_ship(
    ship_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Repair ship damage"""
    try:
        ship = db.query(Ship).filter(
            Ship.id == ship_id,
            Ship.user_id == current_user["id"]
        ).first()
        
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ship not found"
            )
        
        # Repair ship (reduce damage)
        repair_amount = 25.0  # Repair 25% damage
        ship.damage = max(0.0, ship.damage - repair_amount)
        
        db.commit()
        
        return {
            "message": "Ship repaired successfully",
            "damage_remaining": ship.damage,
            "hull_points": 100 - ship.damage
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Repair ship error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to repair ship"
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
