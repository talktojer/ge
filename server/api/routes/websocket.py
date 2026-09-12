"""
WebSocket routes.
Real-time sector updates, combat events, production notifications.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import structlog
import asyncio
import redis.asyncio as aioredis
import os
from typing import Set, Dict, Any, Optional
from datetime import datetime

from api.dependencies import validate_websocket_token

logger = structlog.get_logger()

router = APIRouter()

# Track active WebSocket connections and their subscriptions
# Key: WebSocket object, Value: set of subscribed sector_ids
active_connections: Dict[WebSocket, Set[int]] = {}

# Global Redis connection for pub/sub
redis_client: Optional[aioredis.Redis] = None


async def get_redis():
    """Get or create Redis connection."""
    global redis_client
    if redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = await aioredis.from_url(redis_url, decode_responses=True)
        logger.info("websocket_redis_connected", redis_url=redis_url)
    return redis_client


async def send_sector_snapshot(websocket: WebSocket, sector_id: int, player_id: str):
    """
    Send initial sector snapshot when client subscribes.
    
    Phase C2a: Stub implementation with hardcoded data.
    Future: Query database for real sector state.
    """
    # Stub sector snapshot (matches STUB_SECTOR_DETAILS from sectors.py)
    snapshot = {
        "type": "sector_snapshot",
        "sector_id": sector_id,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "id": sector_id,
            "x": 5,
            "y": 5,
            "ships": [
                {"id": 201, "owner_id": "player_1", "x": 5, "y": 5, "heading": 90.0, "speed": 5.0},
                {"id": 202, "owner_id": "player_3", "x": 5, "y": 5, "heading": 180.0, "speed": 3.0},
            ],
            "planets": [
                {"id": 101, "name": "Terra Prime", "owner_id": "player_1"},
                {"id": 102, "name": "New Horizon", "owner_id": None},
            ]
        }
    }
    
    await websocket.send_text(json.dumps(snapshot))
    logger.info("sector_snapshot_sent", sector_id=sector_id, player_id=player_id)


async def subscribe_to_redis_sector(websocket: WebSocket, sector_id: int):
    """
    Subscribe to Redis pub/sub for a sector and forward events to WebSocket.
    
    Phase C2c: Real Redis pub/sub from ge-sim ticks (6s/55s).
    Replaces the Phase C2a stub 5s timer.
    """
    redis = await get_redis()
    pubsub = redis.pubsub()
    channel = f"sector:{sector_id}:delta"
    
    try:
        await pubsub.subscribe(channel)
        logger.info("redis_sector_subscribed", 
                   sector_id=sector_id,
                   channel=channel)
        
        # Listen for messages from Redis
        async for message in pubsub.listen():
            if message["type"] == "message":
                # Forward Redis message to WebSocket client
                data = message["data"]
                
                # Only send if still subscribed
                if websocket in active_connections and sector_id in active_connections[websocket]:
                    await websocket.send_text(data)
                    logger.debug("sector_delta_forwarded", 
                               sector_id=sector_id,
                               data_preview=data[:100] if len(data) > 100 else data)
                else:
                    # Client unsubscribed or disconnected
                    break
                    
    except asyncio.CancelledError:
        logger.info("redis_subscription_cancelled", sector_id=sector_id)
    except Exception as e:
        logger.error("redis_subscription_error", 
                    sector_id=sector_id,
                    error=str(e))
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        logger.info("redis_sector_unsubscribed",
                   sector_id=sector_id,
                   channel=channel)


@router.websocket("/")
@router.websocket("")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """
    WebSocket connection for real-time sector updates.
    
    Accepts both /ws and /ws/ paths (trailing slash handling for live deployment).
    
    Authentication:
    - Pass token as query parameter: /ws?token=<session_jwt>
    - OR send auth message first: {"type": "auth", "token": "<session_jwt>"}
    - Connection is rejected if token is invalid
    
    Message types from client:
    - {"type": "auth", "token": "<session_jwt>"}  # If not provided as query param
    - {"type": "subscribe", "sector_id": 1}
    - {"type": "unsubscribe", "sector_id": 1}
    - {"type": "ping"}
    
    Message types to client:
    - {"type": "authenticated", "player_id": "123"}
    - {"type": "subscribed", "sector_id": 1}
    - {"type": "unsubscribed", "sector_id": 1}
    - {"type": "sector_snapshot", "sector_id": 1, "data": {...}}
    - {"type": "sector_delta", "sector_id": 1, "tick": 42, "events": [...]}
    - {"type": "pong"}
    - {"type": "error", "message": "..."}
    
    Phase C2a Implementation:
    - Token auth via query param or first message
    - Subscribe/unsubscribe to sectors by ID
    - Send initial sector snapshot on subscribe
    - Broadcast stub deltas (heartbeat + fake moves every 5s)
    
    Future:
    - Subscribe to Redis pubsub for real ge-sim events
    - Fan-out Redis events to subscribed clients
    """
    await websocket.accept()
    logger.info("websocket_connected", message="Client connected")
    
    player_id = None
    broadcast_tasks: Dict[int, asyncio.Task] = {}  # sector_id -> broadcast task
    
    try:
        # Authenticate via query param if provided
        if token:
            player_id = validate_websocket_token(token)
            if not player_id:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid or expired token"
                }))
                await websocket.close(code=1008)  # Policy violation
                return
            
            await websocket.send_text(json.dumps({
                "type": "authenticated",
                "player_id": player_id
            }))
            logger.info("websocket_authenticated", player_id=player_id)
        
        # Track this connection
        active_connections[websocket] = set()
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            logger.info("websocket_message", type=msg_type, player_id=player_id)
            
            # Handle authentication if not already done
            if msg_type == "auth":
                if player_id:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Already authenticated"
                    }))
                    continue
                
                token = message.get("token")
                if not token:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Missing token"
                    }))
                    continue
                
                player_id = validate_websocket_token(token)
                if not player_id:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid or expired token"
                    }))
                    await websocket.close(code=1008)
                    return
                
                await websocket.send_text(json.dumps({
                    "type": "authenticated",
                    "player_id": player_id
                }))
                logger.info("websocket_authenticated", player_id=player_id)
            
            # Require authentication for all other message types
            elif not player_id:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Authentication required. Send {\"type\": \"auth\", \"token\": \"...\"}"
                }))
                continue
            
            elif msg_type == "subscribe":
                sector_id = message.get("sector_id")
                if not sector_id:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Missing sector_id"
                    }))
                    continue
                
                # Add to subscriptions
                active_connections[websocket].add(sector_id)
                
                # Send subscribed confirmation first
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "sector_id": sector_id
                }))
                logger.info("sector_subscribed", sector_id=sector_id, player_id=player_id)
                
                # Send initial sector snapshot
                await send_sector_snapshot(websocket, sector_id, player_id)
                
                # Start Redis subscription for this sector (replaces 5s stub timer)
                if sector_id not in broadcast_tasks:
                    task = asyncio.create_task(subscribe_to_redis_sector(websocket, sector_id))
                    broadcast_tasks[sector_id] = task
            
            elif msg_type == "unsubscribe":
                sector_id = message.get("sector_id")
                if not sector_id:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Missing sector_id"
                    }))
                    continue
                
                # Remove from subscriptions
                active_connections[websocket].discard(sector_id)
                
                # Cancel broadcast task if no longer subscribed
                if sector_id in broadcast_tasks:
                    broadcast_tasks[sector_id].cancel()
                    del broadcast_tasks[sector_id]
                
                await websocket.send_text(json.dumps({
                    "type": "unsubscribed",
                    "sector_id": sector_id
                }))
                logger.info("sector_unsubscribed", sector_id=sector_id, player_id=player_id)
            
            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                }))
    
    except WebSocketDisconnect:
        logger.info("websocket_disconnected", player_id=player_id)
    except Exception as e:
        logger.error("websocket_error", error=str(e), player_id=player_id)
        try:
            await websocket.close()
        except:
            pass
    finally:
        # Clean up subscriptions and tasks
        if websocket in active_connections:
            del active_connections[websocket]
        
        for task in broadcast_tasks.values():
            task.cancel()
        
        logger.info("websocket_cleanup_complete", player_id=player_id)
