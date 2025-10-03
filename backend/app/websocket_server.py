"""
WebSocket Server Implementation for Galactic Empire
Handles real-time communication using Socket.IO
"""

import socketio
from jose import jwt, JWTError
from typing import Dict, Any
import logging
from .core.config import settings
from .core.database import get_db
from .core.user_service import UserService
from .models.user import User
from sqlalchemy.orm import Session

# Configure logging
logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins=settings.cors_origins_list,
    async_mode='asgi',
    logger=True,
    engineio_logger=True
)

# Store connected clients
connected_clients: Dict[str, Dict[str, Any]] = {}

async def authenticate_user(token: str, db: Session) -> User:
    """Authenticate user from JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise ValueError("Invalid token payload")
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise ValueError("User not found")
        
        return user
    except JWTError:
        raise ValueError("Invalid JWT token")

@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    try:
        # Get token from auth data
        if not auth or 'token' not in auth:
            logger.warning(f"Connection rejected for {sid}: No auth token")
            await sio.disconnect(sid)
            return False
        
        token = auth['token']
        
        # Get database session
        db = next(get_db())
        try:
            user = await authenticate_user(token, db)
            
            # Ensure user has at least one ship
            user_service = UserService()
            user_service.ensure_user_has_ship(db, user.id)
            
            # Refresh user to get updated ships
            db.refresh(user)
            
            # Get user's active ship (if any)
            active_ship_id = None
            if user.ships:
                # Status is integer in ORM; treat 0 as normal/active
                active_ship = next((ship for ship in user.ships if getattr(ship, 'status', 0) == 0), None)
                if active_ship:
                    active_ship_id = active_ship.id
                elif user.ships:
                    # Fallback to first ship if no active ship found
                    active_ship_id = user.ships[0].id
            
            # Store client info
            connected_clients[sid] = {
                'user_id': user.id,
                'userid': user.userid,
                'ship_id': active_ship_id
            }
            
            logger.info(f"User {user.userid} connected with session {sid}")
            
            # Join user to their personal room
            await sio.enter_room(sid, f"user_{user.id}")
            
            # Join user to their ship room if they have a ship
            if active_ship_id:
                await sio.enter_room(sid, f"ship_{active_ship_id}")
            
            # Send connection success
            await sio.emit('connection_status', {
                'status': 'connected',
                'user_id': user.id,
                'userid': user.userid
            }, room=sid)
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Connection failed for {sid}: {e}")
        await sio.disconnect(sid)
        return False

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    if sid in connected_clients:
        user_info = connected_clients[sid]
        logger.info(f"User {user_info['userid']} disconnected (session {sid})")
        del connected_clients[sid]
    else:
        logger.info(f"Unknown client disconnected (session {sid})")

@sio.event
async def join_game_room(sid, data):
    """Join a game-specific room"""
    if sid not in connected_clients:
        return
    
    room_name = data.get('room')
    if room_name:
        await sio.enter_room(sid, room_name)
        logger.info(f"Client {sid} joined room {room_name}")

@sio.event
async def leave_game_room(sid, data):
    """Leave a game-specific room"""
    if sid not in connected_clients:
        return
    
    room_name = data.get('room')
    if room_name:
        await sio.leave_room(sid, room_name)
        logger.info(f"Client {sid} left room {room_name}")

# Game event handlers
@sio.event
async def game_action(sid, data):
    """Handle game actions from clients"""
    if sid not in connected_clients:
        return
    
    user_info = connected_clients[sid]
    action_type = data.get('type')
    
    logger.info(f"Game action from {user_info['userid']}: {action_type}")
    
    # Echo action back to confirm receipt
    await sio.emit('action_confirmed', {
        'action': action_type,
        'timestamp': data.get('timestamp')
    }, room=sid)

# Utility functions for broadcasting game updates
async def broadcast_game_update(update_data: Dict[str, Any], room: str = None):
    """Broadcast game update to all clients or specific room"""
    if room:
        await sio.emit('game_update', update_data, room=room)
    else:
        await sio.emit('game_update', update_data)

async def broadcast_ship_update(ship_data: Dict[str, Any], ship_id: int):
    """Broadcast ship update to ship-specific room"""
    await sio.emit('ship_update', ship_data, room=f"ship_{ship_id}")

async def broadcast_planet_update(planet_data: Dict[str, Any], sector_id: int = None):
    """Broadcast planet update to sector or all clients"""
    room = f"sector_{sector_id}" if sector_id else None
    await sio.emit('planet_update', planet_data, room=room)

async def send_message_to_user(user_id: int, message_data: Dict[str, Any]):
    """Send message to specific user"""
    await sio.emit('message', message_data, room=f"user_{user_id}")

async def broadcast_combat_event(combat_data: Dict[str, Any], sector_id: int):
    """Broadcast combat event to sector"""
    await sio.emit('combat_event', combat_data, room=f"sector_{sector_id}")

async def get_connected_users():
    """Get list of connected users"""
    return [
        {
            'user_id': info['user_id'],
            'userid': info['userid'],
            'ship_id': info['ship_id']
        }
        for info in connected_clients.values()
    ]

# Socket.IO server is exported for use in main.py
