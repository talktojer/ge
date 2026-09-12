# Phase C2a: Map + Sector Presence API

Session-gated REST and WebSocket APIs for Unity Map client to load galaxy/sector data and subscribe to live sector deltas.

**Note:** Phase C2c has superseded the 5-second stub timer with real ge-sim-driven deltas at 6s/55s intervals via Redis pub/sub. See [PHASE_C2C_GESIM_DELTAS.md](PHASE_C2C_GESIM_DELTAS.md).

**WebSocket Path:** Both `/ws` and `/ws/` are accepted. Use `wss://ge.jersweb.net/ws/` (with trailing slash) for live deployment.

## Overview

**Ticket**: Phase C2a - First ticket of C2+ initiative  
**Goal**: Minimal server APIs so Unity Map client can:
1. Fetch galaxy overview and sector details (REST)
2. Subscribe to live sector updates (WebSocket)
3. Receive periodic deltas (heartbeat ticks, entity movements)

**Status**: Phase C2a implementation complete (stub data, no full ge-sim integration)

## Authentication

All endpoints require Bearer token authentication using the existing `/auth/exchange` DEV token flow.

### Get Session Token

```bash
curl -X POST http://localhost:8000/auth/exchange \
  -H "Content-Type: application/json" \
  -d '{"dev_token": "ge-dev-user-123"}'
```

**Response:**
```json
{
  "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "player_id": "123",
  "expires_in": 3600
}
```

Use the `session_token` in all subsequent API calls:
```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## REST Endpoints

### GET /sectors - Galaxy Overview

Fetch the galaxy map with all sector stubs.

**Request:**
```bash
curl http://localhost:8000/sectors \
  -H "Authorization: Bearer <session_token>"
```

**Response:**
```json
{
  "shard_id": "alpha-1",
  "width": 10,
  "height": 10,
  "sectors": [
    {
      "id": 1,
      "x": 5,
      "y": 5,
      "name": "Core Sector",
      "sector_type": "normal",
      "planet_count": 3,
      "ship_count": 2
    },
    {
      "id": 2,
      "x": 5,
      "y": 6,
      "name": "Nebula Expanse",
      "sector_type": "nebula",
      "planet_count": 1,
      "ship_count": 0
    },
    {
      "id": 3,
      "x": 6,
      "y": 5,
      "name": "Asteroid Belt Alpha",
      "sector_type": "asteroid",
      "planet_count": 0,
      "ship_count": 1
    },
    {
      "id": 4,
      "x": 4,
      "y": 5,
      "name": "Safe Harbor Station",
      "sector_type": "safe_harbor",
      "planet_count": 1,
      "ship_count": 5
    },
    {
      "id": 5,
      "x": 5,
      "y": 4,
      "name": "Frontier Outpost",
      "sector_type": "normal",
      "planet_count": 2,
      "ship_count": 1
    }
  ]
}
```

**Fields:**
- `shard_id`: Galaxy shard identifier (for future multi-shard support)
- `width`, `height`: Galaxy dimensions in sectors
- `sectors`: Array of sector stubs with minimal info for map rendering
  - `sector_type`: `normal`, `nebula`, `asteroid`, `safe_harbor`
  - `ship_count`: Visible ships in sector (stub count)

### GET /sectors/{id} - Sector Detail

Fetch detailed sector data including planets and ships.

**Request:**
```bash
curl http://localhost:8000/sectors/1 \
  -H "Authorization: Bearer <session_token>"
```

**Response:**
```json
{
  "id": 1,
  "x": 5,
  "y": 5,
  "name": "Core Sector",
  "sector_type": "normal",
  "planet_count": 3,
  "planets": [
    {
      "id": 101,
      "name": "Terra Prime",
      "owner_id": "player_1",
      "owner_name": "Player_1",
      "is_safe_harbor": false
    },
    {
      "id": 102,
      "name": "New Horizon",
      "owner_id": null,
      "owner_name": null,
      "is_safe_harbor": false
    },
    {
      "id": 103,
      "name": "Mining Station 7",
      "owner_id": "player_2",
      "owner_name": "Player_2",
      "is_safe_harbor": false
    }
  ],
  "ships": [
    {
      "id": 201,
      "owner_id": "player_1",
      "owner_name": "Player_1",
      "class_type": "frigate",
      "position_x": 5,
      "position_y": 5,
      "is_docked": false
    },
    {
      "id": 202,
      "owner_id": "player_3",
      "owner_name": "Player_3",
      "class_type": "scout",
      "position_x": 5,
      "position_y": 5,
      "is_docked": false
    }
  ]
}
```

**Errors:**
- `401 Unauthorized`: Missing or invalid token
- `404 Not Found`: Sector ID not found

## WebSocket API

Real-time sector updates via WebSocket at `/ws`.

### Connection

Connect to `ws://localhost:8000/ws` with authentication via query parameter:

```
ws://localhost:8000/ws?token=<session_token>
```

**OR** authenticate after connection with auth message (see below).

### Message Schemas

#### Client -> Server Messages

**1. Authenticate (if token not in query param)**
```json
{
  "type": "auth",
  "token": "<session_token>"
}
```

**2. Subscribe to Sector**
```json
{
  "type": "subscribe",
  "sector_id": 1
}
```

**3. Unsubscribe from Sector**
```json
{
  "type": "unsubscribe",
  "sector_id": 1
}
```

**4. Ping**
```json
{
  "type": "ping"
}
```

#### Server -> Client Messages

**1. Authenticated**
```json
{
  "type": "authenticated",
  "player_id": "123"
}
```

**2. Subscribed**
```json
{
  "type": "subscribed",
  "sector_id": 1
}
```

**3. Sector Snapshot (sent immediately on subscribe)**
```json
{
  "type": "sector_snapshot",
  "sector_id": 1,
  "timestamp": "2026-09-12T17:30:00.000000",
  "data": {
    "id": 1,
    "x": 5,
    "y": 5,
    "ships": [
      {
        "id": 201,
        "owner_id": "player_1",
        "x": 5,
        "y": 5,
        "heading": 90.0,
        "speed": 5.0
      },
      {
        "id": 202,
        "owner_id": "player_3",
        "x": 5,
        "y": 5,
        "heading": 180.0,
        "speed": 3.0
      }
    ],
    "planets": [
      {
        "id": 101,
        "name": "Terra Prime",
        "owner_id": "player_1"
      },
      {
        "id": 102,
        "name": "New Horizon",
        "owner_id": null
      }
    ]
  }
}
```

**4. Sector Delta (periodic updates every ~5 seconds)**
```json
{
  "type": "sector_delta",
  "sector_id": 1,
  "tick": 42,
  "timestamp": "2026-09-12T17:30:05.000000",
  "events": [
    {
      "event_type": "heartbeat",
      "message": "Tick 42"
    },
    {
      "event_type": "ship_moved",
      "ship_id": 201,
      "old_position": {"x": 5, "y": 5},
      "new_position": {"x": 6, "y": 5},
      "heading": 90.0,
      "speed": 5.0
    }
  ]
}
```

**5. Unsubscribed**
```json
{
  "type": "unsubscribed",
  "sector_id": 1
}
```

**6. Pong**
```json
{
  "type": "pong"
}
```

**7. Error**
```json
{
  "type": "error",
  "message": "Authentication required"
}
```

### WebSocket Example Flow

**1. Connect with token in query param:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws?token=' + sessionToken);

ws.onopen = () => {
  console.log('Connected');
  // Server will send {"type": "authenticated", "player_id": "123"}
};
```

**2. OR connect and authenticate with message:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: sessionToken
  }));
  // Server will send {"type": "authenticated", "player_id": "123"}
};
```

**3. Subscribe to sector:**
```javascript
ws.send(JSON.stringify({
  type: 'subscribe',
  sector_id: 1
}));

// Server responds:
// 1. {"type": "subscribed", "sector_id": 1}
// 2. {"type": "sector_snapshot", ...} - immediate snapshot
// 3. {"type": "sector_delta", ...} - periodic deltas every 5s
```

**4. Receive updates:**
```javascript
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  switch(msg.type) {
    case 'authenticated':
      console.log('Authenticated as', msg.player_id);
      break;
    case 'sector_snapshot':
      console.log('Sector snapshot:', msg.data);
      // Initialize map with snapshot data
      break;
    case 'sector_delta':
      console.log('Sector update tick', msg.tick, msg.events);
      // Apply delta to map (ship movements, etc.)
      break;
    case 'error':
      console.error('Error:', msg.message);
      break;
  }
};
```

**5. Unsubscribe when done:**
```javascript
ws.send(JSON.stringify({
  type: 'unsubscribe',
  sector_id: 1
}));
// Server responds: {"type": "unsubscribed", "sector_id": 1}
```

## Testing with curl and websocat

### 1. Get Session Token
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/exchange \
  -H "Content-Type: application/json" \
  -d '{"dev_token": "ge-dev-user-test"}' | jq -r .session_token)

echo "Session token: $TOKEN"
```

### 2. Test REST Endpoints
```bash
# Galaxy overview
curl http://localhost:8000/sectors \
  -H "Authorization: Bearer $TOKEN" | jq

# Sector detail
curl http://localhost:8000/sectors/1 \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 3. Test WebSocket (requires websocat)

Install websocat:
```bash
# macOS
brew install websocat

# Linux
cargo install websocat
```

Connect and test:
```bash
# Connect with token in query param
websocat "ws://localhost:8000/ws?token=$TOKEN"

# Then send messages (one per line):
{"type": "subscribe", "sector_id": 1}
# You'll receive sector_snapshot immediately, then deltas every 5s

{"type": "unsubscribe", "sector_id": 1}

{"type": "ping"}
# Response: {"type": "pong"}
```

## Phase C2a Implementation Notes

### What's Included

✅ **REST Endpoints**
- `GET /sectors` - Galaxy overview with 5 stub sectors
- `GET /sectors/{id}` - Sector detail with hardcoded planets/ships
- Bearer token authentication (required)

✅ **WebSocket**
- `/ws` endpoint with token auth (query param or message)
- Subscribe/unsubscribe to sectors by ID
- Sector snapshot sent immediately on subscribe
- Periodic deltas (heartbeat + fake ship moves every 5s)
- Connection tracking and cleanup

✅ **Authentication**
- Shared JWT validation via `api/dependencies.py`
- Consistent with existing `/auth/exchange` flow
- 401 responses for invalid/missing tokens

### What's NOT Included (Future Phases)

❌ **Database Integration**
- Stub data only (5 sectors, fixed planets/ships)
- No Postgres queries
- No persistence

❌ **Redis Pub/Sub**
- WebSocket deltas are stub data (hardcoded events)
- No actual ge-sim event subscription
- No multi-client fan-out via Redis

❌ **Full ge-sim Integration**
- No 6s ship tick or 55s planet tick
- No real combat events
- No production notifications
- Deltas are fake (stub heartbeat + movement)

❌ **Unity Map Client**
- Server-side only
- Client implementation is separate ticket

### Future Work

**Next Phase (ge-sim integration)**:
1. Connect ge-sim tick engine to publish real events to Redis
2. WebSocket subscribes to Redis pubsub channels per sector
3. Fan-out real combat/movement/production events to clients
4. Database queries for real sector/ship/planet data

**Later Phases**:
- Galaxy generation and persistence
- Multi-shard support
- Player-specific fog of war (sensor range)
- Combat resolution events
- Production completion notifications

## CORS and Deployment

CORS is configured for development (`allow_origins=["*"]`). 

**Production TODO**: Restrict to Unity client domains in `server/api/main.py`:
```python
allow_origins=[
    "https://ge-unity-client.jersweb.net",
    "capacitor://localhost",  # iOS/Android WebView
]
```

## API Documentation

FastAPI auto-generates OpenAPI docs:
- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

Use these for exploring endpoint schemas and testing with the built-in Swagger UI.

---

**Last Updated**: 2026-09-12  
**Status**: Phase C2a complete, ready for review
