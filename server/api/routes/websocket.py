"""
WebSocket routes.
Real-time sector updates, combat events, production notifications.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import structlog
import asyncio
from typing import Set, Dict, Any
from datetime import datetime

from api.dependencies import validate_websocket_token

logger = structlog.get_logger()

router = APIRouter()

# Track active WebSocket connections and their subscriptions
# Key: WebSocket object, Value: set of subscribed sector_ids
active_connections: Dict[WebSocket, Set[int]] = {}


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


async def broadcast_sector_deltas(websocket: WebSocket, sector_id: int):
    """
    Background task to periodically send stub sector deltas.
    
    Phase C2a: Sends heartbeat ticks and fake entity moves every few seconds.
    Future: Subscribe to Redis pubsub and forward real ge-sim events.
    """
    tick_count = 0
    
    try:
        while True:
            await asyncio.sleep(5)  # Send delta every 5 seconds
            
            tick_count += 1
            
            # Stub delta: heartbeat + fake ship movement
            delta = {
                "type": "sector_delta",
                "sector_id": sector_id,
                "tick": tick_count,
                "timestamp": datetime.utcnow().isoformat(),
                "events": [
                    {
                        "event_type": "heartbeat",
                        "message": f"Tick {tick_count}"
                    },
                    {
                        "event_type": "ship_moved",
                        "ship_id": 201,
                        "old_position": {"x": 5, "y": 5},
                        "new_position": {"x": 5 + (tick_count % 3), "y": 5 + (tick_count % 2)},
                        "heading": 90.0,
                        "speed": 5.0
                    }
                ]
            }
            
            # Only send if still subscribed
            if websocket in active_connections and sector_id in active_connections[websocket]:
                await websocket.send_text(json.dumps(delta))
                logger.debug("sector_delta_sent", sector_id=sector_id, tick=tick_count)
            else:
                # Client unsubscribed or disconnected
                break
                
    except asyncio.CancelledError:
        logger.info("delta_broadcast_cancelled", sector_id=sector_id)
    except Exception as e:
        logger.error("delta_broadcast_error", sector_id=sector_id, error=str(e))


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """
    WebSocket connection for real-time sector updates.
    
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
                
                # Start broadcasting deltas for this sector
                if sector_id not in broadcast_tasks:
                    task = asyncio.create_task(broadcast_sector_deltas(websocket, sector_id))
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
