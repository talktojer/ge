"""
Galactic Empire - User Service

This module handles user management operations including registration,
profile management, preferences, and statistics.
"""

from typing import Dict, List, Optional, Any
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from ..models.user import User, UserAccount, UserSession
from ..models.ship import Ship, ShipClass
from ..models.team import Team
from ..models.planet import Planet
from ..core.auth import auth_service
from ..core.game_engine import game_engine

# Module logger
logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations"""
    
    def __init__(self):
        self.auth_service = auth_service
    
    def register_user(self, db: Session, userid: str, email: str, password: str, **kwargs) -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Create user (auto-verify for now since no email system)
            user = self.auth_service.create_user(
                db=db,
                userid=userid,
                email=email,
                password=password,
                is_verified=True,  # Auto-verify for now
                **kwargs
            )
            
            # Create user account
            user_account = UserAccount(
                user_id=user.id,
                is_admin=False,
                is_sysop=False
            )
            db.add(user_account)
            db.commit()
            
            # Create starter ship for new user (ship class 1 - Interceptor)
            try:
                starter_ship = self.create_ship(
                    db=db,
                    user_id=user.id,
                    ship_name=f"{userid}'s First Ship",
                    ship_class=1  # Interceptor class
                )
            except Exception as ship_error:
                # Log the error but don't fail registration
                logger.warning(f"Failed to create starter ship for user {userid}: {ship_error}")
                # Continue with registration even if ship creation fails
            
            return {
                "user": {
                    "id": user.id,
                    "userid": user.userid,
                    "email": user.email,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "created_at": user.created_at.isoformat()
                },
                "message": "User registered successfully. Email verification is disabled for now."
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )
    
    def verify_email(self, db: Session, token: str) -> Dict[str, Any]:
        """Verify user email with token (placeholder - email system not implemented)"""
        # Placeholder for future email verification
        return {
            "message": "Email verification is not implemented yet. Users are auto-verified on registration.",
            "note": "This endpoint is a placeholder for future email verification functionality."
        }
    
    def login_user(self, db: Session, userid: str, password: str, ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """Login user and create session"""
        # Authenticate user
        user = self.auth_service.authenticate_user(db, userid, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Note: Email verification is disabled for now, so we don't check is_verified
        
        # Create session
        session_token = self.auth_service.create_user_session(
            db=db,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Create JWT tokens
        access_token = self.auth_service.create_access_token(
            data={"sub": str(user.id), "userid": user.userid}
        )
        refresh_token = self.auth_service.create_refresh_token(
            data={"sub": str(user.id), "userid": user.userid}
        )
        
        # Ensure user has at least one ship
        self.ensure_user_has_ship(db, user.id)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session_token": session_token,
            "token_type": "bearer",
            "user": self.auth_service.get_user_stats(user)
        }
    
    def logout_user(self, db: Session, session_token: str) -> Dict[str, Any]:
        """Logout user and invalidate session"""
        success = self.auth_service.invalidate_user_session(db, session_token)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session token"
            )
        
        return {"message": "Logged out successfully"}
    
    def get_user_profile(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get user profile information"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user account
        user_account = db.query(UserAccount).filter(UserAccount.user_id == user_id).first()
        
        # Get user's ships with ship class information
        ships = db.query(Ship).join(ShipClass).filter(Ship.user_id == user_id).all()
        
        # Get team information
        team = None
        if user.team_id:
            team = db.query(Team).filter(Team.id == user.team_id).first()
        
        return {
            "user": self.auth_service.get_user_stats(user),
            "account": {
                "is_admin": user_account.is_admin if user_account else False,
                "is_sysop": user_account.is_sysop if user_account else False,
                "preferred_ship_class": user_account.preferred_ship_class if user_account else 1,
                "auto_repair": user_account.auto_repair if user_account else False,
                "auto_shield": user_account.auto_shield if user_account else False
            },
            "ships": [
                {
                    "id": ship.id,
                    "ship_name": ship.shipname,
                    "ship_class": ship.ship_class_id,
                    "ship_class_name": ship.ship_class.name if ship.ship_class else "Unknown",
                    "status": ship.status,
                    "position": {"x": ship.x_coord, "y": ship.y_coord},
                    "heading": ship.heading,
                    "speed": ship.speed
                }
                for ship in ships
            ],
            "team": {
                "id": team.id,
                "team_name": team.team_name,
                "team_code": team.team_code
            } if team else None
        }
    
    def update_user_preferences(self, db: Session, user_id: int, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences and options"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user options
        if "scan_names" in preferences:
            user.scan_names = preferences["scan_names"]
        if "scan_home" in preferences:
            user.scan_home = preferences["scan_home"]
        if "scan_full" in preferences:
            user.scan_full = preferences["scan_full"]
        if "msg_filter" in preferences:
            user.msg_filter = preferences["msg_filter"]
        
        # Update user account preferences
        user_account = db.query(UserAccount).filter(UserAccount.user_id == user_id).first()
        if not user_account:
            user_account = UserAccount(user_id=user_id)
            db.add(user_account)
        
        if "preferred_ship_class" in preferences:
            user_account.preferred_ship_class = preferences["preferred_ship_class"]
        if "auto_repair" in preferences:
            user_account.auto_repair = preferences["auto_repair"]
        if "auto_shield" in preferences:
            user_account.auto_shield = preferences["auto_shield"]
        
        db.commit()
        
        return {
            "message": "Preferences updated successfully",
            "preferences": {
                "scan_names": user.scan_names,
                "scan_home": user.scan_home,
                "scan_full": user.scan_full,
                "msg_filter": user.msg_filter,
                "preferred_ship_class": user_account.preferred_ship_class,
                "auto_repair": user_account.auto_repair,
                "auto_shield": user_account.auto_shield
            }
        }
    
    def create_ship(self, db: Session, user_id: int, ship_name: str, ship_class: int) -> Dict[str, Any]:
        """Create a new ship for user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check ship limit (if any)
        existing_ships = db.query(Ship).filter(Ship.user_id == user_id).count()
        max_ships = 5  # Default limit, could be configurable
        
        if existing_ships >= max_ships:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum number of ships ({max_ships}) reached"
            )
        
        # Resolve ship class id and display class number
        ship_class_row = db.query(ShipClass).filter(ShipClass.id == ship_class).first()
        if not ship_class_row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ship class"
            )
        
        # Generate next ship number for user
        next_shipno = (user.topshipno or 0) + 1
        
        # Create ship in database (align with ORM fields)
        ship = Ship(
            user_id=user_id,
            shipno=next_shipno,
            shipname=ship_name,
            ship_class_id=ship_class_row.id,
            shpclass=ship_class_row.class_number,
            heading=0.0,
            head2b=0.0,
            speed=0.0,
            speed2b=0.0,
            x_coord=0.0,  # Start in neutral sector
            y_coord=0.0,
            damage=0.0,
            energy=50000.0,
            phaser_strength=0.0,
            phaser_type=0,
            kills=0,
            last_fired=0,
            shield_type=0,
            shield_status=0,
            shield_charge=0,
            cloak=0,
            tactical=0,
            helm=0,
            train=0,
            where=0,
            jammer=0,
            freq_subspace=0,
            freq_hyperspace=0,
            freq_planetary=0,
            hostile=False,
            cant_exit=0,
            repair=False,
            hypha=False,
            fire_control=False,
            destruct=0,
            status=0,  # 0 = active/normal
            cyb_mine=False,
            cyb_skill=0,
            cyb_update=0,
            tick=0,
            emulate=False,
            mines_near=False,
            lock=0,
            hold_course=0,
            top_speed=0,
            warn_counter=0
        )
        
        db.add(ship)
        db.commit()
        db.refresh(ship)
        
        # Create ship in game engine
        try:
            game_engine.create_ship(
                ship_id=str(ship.id),
                user_id=user.userid,
                ship_name=ship_name,
                ship_class=ship_class
            )
        except Exception as e:
            # Rollback database if game engine fails
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create ship in game engine: {str(e)}"
            )
        
        # Update user ship count
        user.noships += 1
        user.topshipno = max(user.topshipno, ship.id)
        db.commit()
        
        return {
            "message": "Ship created successfully",
            "ship": {
                "id": ship.id,
                "ship_name": ship.shipname,
                "ship_class": ship.shpclass,
                "status": ship.status
            }
        }
    
    def ensure_user_has_ship(self, db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        """Ensure user has at least one ship, create one if missing"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Check if user has any ships
        existing_ships = db.query(Ship).filter(Ship.user_id == user_id).count()
        
        if existing_ships == 0:
            # Create a starter ship
            try:
                return self.create_ship(
                    db=db,
                    user_id=user_id,
                    ship_name=f"{user.userid}'s Ship",
                    ship_class=1  # Interceptor class
                )
            except Exception as e:
                logger.error(f"Failed to create starter ship for user {user_id}: {e}")
                return None
        
        return None
    
    def get_user_ships(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Get all ships for a user"""
        ships = db.query(Ship).filter(Ship.user_id == user_id).all()
        
        return [
            {
                "id": ship.id,
                "name": ship.shipname,
                "owner_id": ship.user_id,
                "ship_type": "Interceptor",  # Default ship type
                "ship_class": ship.shpclass,
                "x": ship.x_coord,
                "y": ship.y_coord,
                "z": 0.0,  # Default z coordinate
                "sector": 1,  # Default sector
                "hull_points": 100 - ship.damage,  # Calculate hull points from damage
                "max_hull_points": 100,
                "shields": ship.shield_charge,
                "max_shields": 100,
                "fuel": ship.energy,  # Use energy as fuel
                "max_fuel": 50000,
                "cargo_capacity": 1000,  # Default cargo capacity
                "cargo_used": 0,  # Default empty cargo
                "weapons": ["Phaser"],  # Default weapon
                "is_active": (ship.status or 0) == 0,
                "created_at": ship.created_at.isoformat() if ship.created_at else "2025-01-01T00:00:00Z",
                "last_updated": ship.updated_at.isoformat() if ship.updated_at else "2025-01-01T00:00:00Z"
            }
            for ship in ships
        ]
    
    def select_ship(self, db: Session, user_id: int, ship_id: int) -> Dict[str, Any]:
        """Select a ship as active"""
        ship = db.query(Ship).filter(
            Ship.id == ship_id,
            Ship.user_id == user_id
        ).first()
        
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ship not found"
            )
        
        if ship.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ship is not active"
            )
        
        # Update user's current ship (if we add that field)
        # For now, just return ship info
        return {
            "message": "Ship selected successfully",
            "ship": {
                "id": ship.id,
                "ship_name": ship.shipname,
                "ship_class": ship.ship_class,
                "status": ship.status,
                "position": {"x": ship.x_coord, "y": ship.y_coord},
                "heading": ship.heading,
                "speed": ship.speed,
                "energy": ship.energy,
                "shields": ship.shields
            }
        }
    
    def get_user_statistics(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get detailed user statistics"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Ensure user has at least one ship
        self.ensure_user_has_ship(db, user.id)
        
        # Get ship statistics
        ships = db.query(Ship).filter(Ship.user_id == user_id).all()
        active_ships = len([s for s in ships if s.status == "active"])
        
        # Get planet statistics
        planets_owned = db.query(Planet).filter(Planet.owner_id == user_id).count()
        
        return {
            "user": {
                "userid": user.userid,
                "score": user.score,
                "kills": user.kills,
                "planets": user.planets,
                "cash": user.cash,
                "debt": user.debt,
                "population": user.population,
                "plscore": user.plscore,
                "klscore": user.klscore
            },
            "ships": {
                "total": len(ships),
                "active": active_ships,
                "inactive": len(ships) - active_ships
            },
            "planets": {
                "owned": planets_owned,
                "total_population": sum(p.population for p in db.query(Planet).filter(Planet.owner_id == user_id).all())
            },
            "team": {
                "teamcode": user.teamcode,
                "team_id": user.team_id
            }
        }
    
    def change_password(self, db: Session, user_id: int, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not self.auth_service.verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        success = self.auth_service.update_user_password(db, user_id, new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        # Invalidate all sessions
        self.auth_service.invalidate_all_user_sessions(db, user_id)
        
        return {"message": "Password changed successfully. Please log in again."}
    
    def request_password_reset(self, db: Session, email: str) -> Dict[str, Any]:
        """Request password reset (placeholder - email system not implemented)"""
        # Placeholder for future password reset functionality
        return {
            "message": "Password reset is not implemented yet. Email system not available.",
            "note": "This endpoint is a placeholder for future password reset functionality.",
            "suggestion": "Contact an administrator for password reset assistance."
        }
    
    def reset_password(self, db: Session, token: str, new_password: str) -> Dict[str, Any]:
        """Reset password with token (placeholder - email system not implemented)"""
        # Placeholder for future password reset functionality
        return {
            "message": "Password reset is not implemented yet. Email system not available.",
            "note": "This endpoint is a placeholder for future password reset functionality.",
            "suggestion": "Contact an administrator for password reset assistance."
        }


# Global user service instance
user_service = UserService()
