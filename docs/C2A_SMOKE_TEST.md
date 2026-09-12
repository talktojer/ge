# Phase C2a Smoke Test

Quick verification that the Map + Sector Presence API is working.

## Prerequisites

```bash
# Start the FastAPI server
cd server
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## REST API Tests

### 1. Get Session Token

```bash
curl -X POST http://localhost:8000/auth/exchange \
  -H "Content-Type: application/json" \
  -d '{"dev_token": "ge-dev-user-smoketest"}'
```

**Expected Response:**
```json
{
  "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "player_id": "smoketest",
  "expires_in": 3600
}
```

**Save the token:**
```bash
export TOKEN="<session_token_from_above>"
```

### 2. Get Galaxy Overview

```bash
curl -L http://localhost:8000/sectors \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
- `shard_id`: "alpha-1"
- `width`: 10, `height`: 10
- `sectors`: Array of 5 sectors (Core Sector, Nebula Expanse, Asteroid Belt Alpha, Safe Harbor Station, Frontier Outpost)

### 3. Get Sector Detail

```bash
curl http://localhost:8000/sectors/1 \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
- Sector ID 1 (Core Sector)
- 3 planets (Terra Prime, New Horizon, Mining Station 7)
- 2 ships (frigate, scout)

### 4. Test 404 on Invalid Sector

```bash
curl http://localhost:8000/sectors/999 \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:** HTTP 404 with error message

### 5. Test 401 Without Token

```bash
curl http://localhost:8000/sectors/1
```

**Expected Response:** HTTP 401 Unauthorized

## WebSocket Test

### Using Python Test Script

```bash
cd server
python3 test_websocket.py
```

**Expected Output:**
```
✓ Got session token: eyJhbGciOiJIUzI1NiIsInR5cCI6Ik...
✓ WebSocket connected
✓ Received: authenticated
✓ Sent subscribe message
✓ Received: subscribed
✓ Received: sector_snapshot
  Snapshot data: 2 ships, 2 planets
⏳ Waiting for sector delta (up to 6 seconds)...
✓ Received: sector_delta
  Delta tick: 1, events: 2
    - heartbeat
    - ship_moved
✓ Ping/pong: pong
✓ Received: unsubscribed

✓ All WebSocket tests passed!
```

### Manual WebSocket Test (with websocat)

**Install websocat:**
```bash
# macOS
brew install websocat

# Linux
cargo install websocat
```

**Connect and test:**
```bash
# 1. Get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/exchange \
  -H "Content-Type: application/json" \
  -d '{"dev_token": "ge-dev-user-manual"}' | jq -r .session_token)

# 2. Connect to WebSocket
websocat "ws://localhost:8000/ws/?token=$TOKEN"

# 3. You'll receive:
# {"type": "authenticated", "player_id": "manual"}

# 4. Type this message:
{"type": "subscribe", "sector_id": 1}

# 5. You'll receive:
# {"type": "subscribed", "sector_id": 1}
# {"type": "sector_snapshot", "sector_id": 1, ...}
# 
# Then every 5 seconds:
# {"type": "sector_delta", "sector_id": 1, "tick": N, ...}

# 6. Test ping:
{"type": "ping"}
# Response: {"type": "pong"}

# 7. Unsubscribe:
{"type": "unsubscribe", "sector_id": 1}
# Response: {"type": "unsubscribed", "sector_id": 1}
```

## Expected Behavior

### REST Endpoints
- ✅ All endpoints require Bearer token authentication
- ✅ Galaxy overview returns 5 stub sectors
- ✅ Sector detail returns hardcoded planets/ships
- ✅ Invalid sector IDs return 404
- ✅ Missing/invalid tokens return 401

### WebSocket
- ✅ Connects with token in query param
- ✅ Sends authenticated confirmation
- ✅ Subscribe returns confirmation + snapshot
- ✅ Deltas broadcast every 5 seconds (heartbeat + stub ship movement)
- ✅ Ping/pong works
- ✅ Unsubscribe stops deltas
- ✅ Connection cleanup on disconnect

## Stub Data Notes

This is Phase C2a - **stub implementation only**:
- Galaxy has 5 hardcoded sectors
- Sector details are static (no database)
- Deltas are fake (tick counter + random ship movement)
- No Redis pub/sub or ge-sim integration yet

Future phases will replace stubs with:
- Real galaxy data from database
- Live ge-sim events via Redis
- Actual ship movements, combat, production
