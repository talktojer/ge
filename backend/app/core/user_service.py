"""
Galactic Empire - User Service

This module handles user management operations including registration,
profile management, preferences, and statistics.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from ..models.user import User, UserAccount, UserSession
from ..models.ship import Ship
from ..models.team import Team
from ..models.planet import Planet
from ..core.auth import auth_service
from ..core.game_engine import game_engine


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
        
        # Get user's ships
        ships = db.query(Ship).filter(Ship.user_id == user_id).all()
        
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
                    "ship_name": ship.ship_name,
                    "ship_class": ship.ship_class,
                    "status": ship.status,
                    "position": {"x": ship.position_x, "y": ship.position_y},
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
        
        # Create ship in database
        ship = Ship(
            user_id=user_id,
            ship_name=ship_name,
            ship_class=ship_class,
            position_x=0.0,  # Start in neutral sector
            position_y=0.0,
            heading=0.0,
            speed=0.0,
            energy=50000,
            shields=0,
            max_shields=100,
            damage=0.0,
            status="active"
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
                "ship_name": ship.ship_name,
                "ship_class": ship.ship_class,
                "status": ship.status,
                "position": {"x": ship.position_x, "y": ship.position_y},
                "heading": ship.heading,
                "speed": ship.speed,
                "energy": ship.energy,
                "shields": ship.shields
            }
        }
    
    def get_user_ships(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Get all ships for a user"""
        ships = db.query(Ship).filter(Ship.user_id == user_id).all()
        
        return [
            {
                "id": ship.id,
                "ship_name": ship.ship_name,
                "ship_class": ship.ship_class,
                "status": ship.status,
                "position": {"x": ship.position_x, "y": ship.position_y},
                "heading": ship.heading,
                "speed": ship.speed,
                "energy": ship.energy,
                "shields": ship.shields,
                "max_shields": ship.max_shields,
                "damage": ship.damage,
                "created_at": ship.created_at.isoformat()
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
                "ship_name": ship.ship_name,
                "ship_class": ship.ship_class,
                "status": ship.status,
                "position": {"x": ship.position_x, "y": ship.position_y},
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
