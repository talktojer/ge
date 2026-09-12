"""
Authentication routes.
Firebase JWT -> Session token exchange.
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError
import structlog
import os

logger = structlog.get_logger()

router = APIRouter()

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 1

class FirebaseTokenRequest(BaseModel):
    firebase_token: Optional[str] = None
    dev_token: Optional[str] = Field(None, description="DEV bypass token (ge-dev-user-{id})")

class SessionTokenResponse(BaseModel):
    session_token: str
    player_id: str
    expires_in: int  # seconds

@router.post("/exchange", response_model=SessionTokenResponse)
async def exchange_firebase_token(
    request: FirebaseTokenRequest,
    x_ge_dev_token: Optional[str] = Header(None, description="DEV bypass header")
):
    """
    Exchange Firebase ID token for session JWT.
    
    DEV BYPASS MODE (default on ge.jersweb.net):
    - Send dev_token in body: {"dev_token": "ge-dev-user-123"}
    - Or send X-GE-Dev-Token header: "ge-dev-user-123"
    - Format: "ge-dev-user-{any_id}" where any_id becomes the player_id
    
    FIREBASE MODE (not yet implemented):
    - Send firebase_token in body: {"firebase_token": "firebase_jwt_here"}
    - Backend validates with Firebase Admin SDK
    - Creates/updates user in database
    
    Returns session JWT valid for 1 hour.
    """
    logger.info("auth_exchange", message="Token exchange requested")
    
    # Check DEV bypass first (header or body)
    dev_token = x_ge_dev_token or request.dev_token
    
    if dev_token:
        # DEV bypass mode
        if not dev_token.startswith("ge-dev-user-"):
            raise HTTPException(
                status_code=400,
                detail="Invalid dev_token format. Expected: ge-dev-user-{id}"
            )
        
        player_id = dev_token.replace("ge-dev-user-", "")
        logger.info("auth_exchange_dev", player_id=player_id, message="DEV bypass auth")
        
    elif request.firebase_token:
        # Firebase mode (not yet implemented)
        raise HTTPException(
            status_code=501,
            detail="Firebase authentication not yet implemented. Use dev_token for now."
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Either firebase_token or dev_token is required"
        )
    
    # Generate session JWT
    now = datetime.utcnow()
    expiration = now + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload = {
        "sub": player_id,  # Subject = player ID
        "iat": now,
        "exp": expiration,
        "type": "session"
    }
    
    session_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return SessionTokenResponse(
        session_token=session_token,
        player_id=player_id,
        expires_in=JWT_EXPIRATION_HOURS * 3600
    )

@router.get("/me")
async def get_current_player(authorization: Optional[str] = Header(None)):
    """
    Get current authenticated player info.
    
    Requires: Authorization header with "Bearer {session_token}"
    
    Returns minimal player stub (id, display_name).
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected: Bearer {token}"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        player_id = payload.get("sub")
        
        if not player_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        logger.info("auth_me", player_id=player_id, message="Player authenticated")
        
        # Return minimal player stub (no database query for now)
        return {
            "player_id": player_id,
            "display_name": f"Player_{player_id}",
            "cash": 1000,
            "kills": 0,
            "planets_owned": 0
        }
        
    except JWTError as e:
        logger.error("auth_me_failed", error=str(e), message="JWT validation failed")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
