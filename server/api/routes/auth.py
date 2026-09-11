"""
Authentication routes.
Firebase JWT -> Session token exchange.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

router = APIRouter()

class FirebaseTokenRequest(BaseModel):
    firebase_token: str

class SessionTokenResponse(BaseModel):
    session_token: str
    player_id: str
    expires_in: int  # seconds

@router.post("/exchange", response_model=SessionTokenResponse)
async def exchange_firebase_token(request: FirebaseTokenRequest):
    """
    Exchange Firebase ID token for session JWT.
    
    TODO:
    1. Validate Firebase token with Firebase Admin SDK
    2. Extract user ID from token
    3. Create/update user in Postgres
    4. Generate session JWT (1-hour TTL)
    5. Return session token + player ID
    """
    logger.info("auth_exchange", message="Token exchange requested")
    
    # TODO: Implement Firebase token validation
    # from firebase_admin import auth
    # decoded_token = auth.verify_id_token(request.firebase_token)
    # user_id = decoded_token['uid']
    
    # TODO: Create/update user in database
    # player = await get_or_create_player(user_id)
    
    # TODO: Generate session JWT
    # from jose import jwt
    # session_token = jwt.encode({"sub": player.id, "exp": ...}, JWT_SECRET)
    
    raise HTTPException(
        status_code=501,
        detail="Authentication not implemented (Phase B scaffold)"
    )
