"""
Galactic Empire - Authentication Service

This module handles user authentication, JWT tokens, password hashing,
and session management for the Galactic Empire game.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..models.user import User, UserToken, UserSession
from ..core.config import settings
from ..models.base import get_db

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthService:
    """Authentication service for user management"""
    
    def __init__(self):
        self.pwd_context = pwd_context
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != token_type:
                return None
            return payload
        except JWTError:
            return None
    
    def authenticate_user(self, db: Session, userid: str, password: str) -> Optional[User]:
        """Authenticate a user with userid and password"""
        user = db.query(User).filter(User.userid == userid).first()
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user
    
    def authenticate_user_by_email(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user
    
    def create_user(self, db: Session, userid: str, email: str, password: str, **kwargs) -> User:
        """Create a new user"""
        # Check if userid or email already exists
        if db.query(User).filter(User.userid == userid).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID already registered"
            )
        
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user (auto-verify if not specified)
        hashed_password = self.get_password_hash(password)
        
        # Extract is_verified from kwargs to avoid duplicate parameter error
        is_verified = kwargs.pop('is_verified', True)
        
        user = User(
            userid=userid,
            email=email,
            password_hash=hashed_password,
            is_active=True,
            is_verified=is_verified,
            **kwargs
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def create_user_token(self, db: Session, user_id: int, token_type: str, expires_in_hours: int = 24) -> str:
        """Create a user token for email verification, password reset, etc."""
        # Generate random token
        token_value = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token_value.encode()).hexdigest()
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        # Create token record
        token = UserToken(
            user_id=user_id,
            token_type=token_type,
            token_hash=token_hash,
            expires_at=expires_at
        )
        
        db.add(token)
        db.commit()
        
        return token_value
    
    def verify_user_token(self, db: Session, token_value: str, token_type: str) -> Optional[User]:
        """Verify a user token and return the user"""
        token_hash = hashlib.sha256(token_value.encode()).hexdigest()
        
        token = db.query(UserToken).filter(
            UserToken.token_hash == token_hash,
            UserToken.token_type == token_type,
            UserToken.is_used == False,
            UserToken.expires_at > datetime.utcnow()
        ).first()
        
        if not token:
            return None
        
        # Mark token as used
        token.is_used = True
        token.used_at = datetime.utcnow()
        db.commit()
        
        return token.user
    
    def create_user_session(self, db: Session, user_id: int, ip_address: str = None, user_agent: str = None) -> str:
        """Create a user session"""
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        
        # Calculate expiration (7 days)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        # Create session
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
            last_activity=datetime.utcnow()
        )
        
        db.add(session)
        db.commit()
        
        return session_token
    
    def get_user_by_session(self, db: Session, session_token: str) -> Optional[User]:
        """Get user by session token"""
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        
        if not session:
            return None
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        db.commit()
        
        return session.user
    
    def invalidate_user_session(self, db: Session, session_token: str) -> bool:
        """Invalidate a user session"""
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        
        if not session:
            return False
        
        session.is_active = False
        db.commit()
        return True
    
    def invalidate_all_user_sessions(self, db: Session, user_id: int) -> int:
        """Invalidate all sessions for a user"""
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).all()
        
        count = 0
        for session in sessions:
            session.is_active = False
            count += 1
        
        db.commit()
        return count
    
    def update_user_password(self, db: Session, user_id: int, new_password: str) -> bool:
        """Update user password"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.password_hash = self.get_password_hash(new_password)
        user.last_password_change = datetime.utcnow()
        db.commit()
        
        return True
    
    def verify_user_email(self, db: Session, user_id: int) -> bool:
        """Verify user email"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_verified = True
        user.email_verified_at = datetime.utcnow()
        db.commit()
        
        return True
    
    def get_user_stats(self, user: User) -> Dict[str, Any]:
        """Get user statistics"""
        return {
            "id": user.id,
            "userid": user.userid,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "score": user.score,
            "kills": user.kills,
            "planets": user.planets,
            "cash": user.cash,
            "debt": user.debt,
            "population": user.population,
            "noships": user.noships,
            "teamcode": user.teamcode,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat()
        }


# Global auth service instance
auth_service = AuthService()

# Security instance for JWT token extraction
security = HTTPBearer()


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get current authenticated user"""
    token = credentials.credentials
    
    # Verify JWT token
    payload = auth_service.verify_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return {"id": user.id, "userid": user.userid, "user": user}
