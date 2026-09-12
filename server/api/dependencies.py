"""
Shared FastAPI dependencies.
Authentication, database sessions, etc.
"""
from fastapi import HTTPException, Header, WebSocket
from typing import Optional
from jose import jwt, JWTError
import structlog
import os

logger = structlog.get_logger()

# JWT configuration (shared with auth.py)
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"


async def get_current_player(authorization: Optional[str] = Header(None)) -> str:
    """
    Dependency to extract and validate player_id from Bearer token.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(player_id: str = Depends(get_current_player)):
            # player_id is now validated
    
    Returns:
        player_id: Validated player ID from JWT
    
    Raises:
        HTTPException 401: Invalid or missing token
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
        
        logger.debug("auth_validated", player_id=player_id)
        return player_id
        
    except JWTError as e:
        logger.error("auth_failed", error=str(e), message="JWT validation failed")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def validate_websocket_token(token: str) -> Optional[str]:
    """
    Validate JWT token for WebSocket connections.
    
    Returns player_id if valid, None otherwise.
    Does NOT raise exceptions (WebSocket has different error handling).
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        player_id = payload.get("sub")
        
        if not player_id:
            return None
        
        logger.debug("ws_auth_validated", player_id=player_id)
        return player_id
        
    except JWTError as e:
        logger.error("ws_auth_failed", error=str(e))
        return None
