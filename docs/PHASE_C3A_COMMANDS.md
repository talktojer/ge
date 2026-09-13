# Phase C3a: Real Command Path (Replace Stubs)

**Status:** Implemented  
**Date:** 2026-09-13  
**Dependencies:** Phase C2a (REST/WebSocket), Phase C2c (ge-sim Redis pub/sub)

---

## Executive Summary

Phase C3a implements session-gated player commands that affect world state and publish events to the existing WebSocket sector delta path. Commands validate player ownership, update authoritative state, and publish events to Redis so subscribed WebSocket clients immediately see the results.

**Endpoints Implemented:**
- `POST /commands/move` - Move own ship to/within sector
- `POST /commands/fire` - Fire weapon at target ship
- `POST /commands/claim` - Claim unowned planet

**Architecture:** Commands → State Update → Redis Pub/Sub → WebSocket Clients

**Hardening:** Each endpoint accepts both trailing-slash variants (e.g., `/commands/move` and `/commands/move/`) to prevent HTTPS→HTTP 307 redirects, mirroring the pattern used in `/sectors` (Phase C2d).

---

## Implementation Overview

### Command Flow

```
1. Unity Client → POST /commands/{action} (with Bearer token)
2. API validates session via get_current_player dependency
3. API validates ownership and business rules
4. API updates state (in-memory for Phase C3a; TODO: Postgres)
5. API publishes event to Redis sector:{id}:delta channel
6. WebSocket handlers forward Redis event to subscribed clients
7. Unity clients receive delta and update game state
```

### State Storage

**Phase C3a:** In-memory dictionaries with clear TODOs for Postgres migration.

```python
_ship_store: Dict[int, Dict[str, Any]]    # Ship positions, ownership
_planet_store: Dict[int, Dict[str, Any]]  # Planet ownership
```

**Future (Phase C3b+):** Replace with Postgres queries using SQLAlchemy models from `database/models.py`.

### Redis Event Publishing

All commands publish to the same `sector:{id}:delta` channel used by ge-sim, ensuring:
- WebSocket clients see instant feedback (no 6s tick delay for commands)
- Consistent event format with ge-sim tick deltas
- Events include `event_type` for client-side dispatch

---

## Endpoints

### POST /commands/move

Move own ship toward/to a sector or within sector.

**Request:**
```bash
curl -X POST http://localhost:8000/commands/move \
  -H "Authorization: Bearer <session_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "ship_id": 201,
    "target_x": 6,
    "target_y": 5
  }'
```

**Request Body:**
```json
{
  "ship_id": 201,
  "target_x": 6,
  "target_y": 5
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "ship_id": 201,
  "new_position": {"x": 6, "y": 5},
  "event_published": true
}
```

**Errors:**
- `401 Unauthorized`: Missing or invalid Bearer token
- `403 Forbidden`: Player does not own ship
- `404 Not Found`: Ship not found

**Redis Event Published:**

Channel: `sector:{sector_id}:delta`

```json
{
  "type": "sector_delta",
  "sector_id": 1,
  "events": [
    {
      "event_type": "ship_moved",
      "ship_id": 201,
      "old_position": {"x": 5, "y": 5},
      "new_position": {"x": 6, "y": 5},
      "heading": 90.0,
      "speed": 5.0,
      "timestamp": "2026-09-13T15:30:00.123456"
    }
  ]
}
```

---

### POST /commands/fire

Fire weapon at target ship in same sector.

**Request:**
```bash
curl -X POST http://localhost:8000/commands/fire \
  -H "Authorization: Bearer <session_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "ship_id": 201,
    "weapon_type": "phasor",
    "target_id": 202
  }'
```

**Request Body:**
```json
{
  "ship_id": 201,
  "weapon_type": "phasor",
  "target_id": 202
}
```

**Weapon Types:**
- `phasor` (stub damage: 15)
- `torpedo` (stub damage: 35)
- `missile` (stub damage: 25)

**Response (200 OK):**
```json
{
  "success": true,
  "ship_id": 201,
  "target_id": 202,
  "weapon_type": "phasor",
  "damage": 15.0,
  "event_published": true
}
```

**Errors:**
- `401 Unauthorized`: Missing or invalid Bearer token
- `403 Forbidden`: Player does not own ship
- `404 Not Found`: Ship or target not found

**Redis Event Published:**

Channel: `sector:{sector_id}:delta`

```json
{
  "type": "sector_delta",
  "sector_id": 1,
  "events": [
    {
      "event_type": "combat",
      "attacker_id": 201,
      "target_id": 202,
      "weapon_type": "phasor",
      "damage": 15.0,
      "timestamp": "2026-09-13T15:30:05.123456"
    }
  ]
}
```

**Phase C3a Limitations:**
- Damage is stub calculation (real damage will be computed by ge-sim tick resolver)
- No same-sector validation yet
- No weapon range, cooldown, or energy cost checks
- Combat not queued for 6s tick (instant publish for demo purposes)

---

### POST /commands/claim

Claim an unowned planet in sector.

**Request:**
```bash
curl -X POST http://localhost:8000/commands/claim \
  -H "Authorization: Bearer <session_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "ship_id": 201,
    "planet_id": 102
  }'
```

**Request Body:**
```json
{
  "ship_id": 201,
  "planet_id": 102
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "planet_id": 102,
  "planet_name": "New Horizon",
  "owner_id": "player_1",
  "event_published": true
}
```

**Errors:**
- `401 Unauthorized`: Missing or invalid Bearer token
- `403 Forbidden`: Player does not own ship, or planet already owned
- `404 Not Found`: Ship or planet not found

**Redis Event Published:**

Channel: `sector:{sector_id}:delta`

```json
{
  "type": "sector_delta",
  "sector_id": 1,
  "events": [
    {
      "event_type": "planet_claimed",
      "planet_id": 102,
      "planet_name": "New Horizon",
      "owner_id": "player_1",
      "timestamp": "2026-09-13T15:30:10.123456"
    }
  ]
}
```

---

## Authentication

All command endpoints require Bearer token authentication via the `get_current_player` FastAPI dependency.

**Get Session Token:**
```bash
curl -X POST http://localhost:8000/auth/exchange \
  -H "Content-Type: application/json" \
  -d '{"dev_token": "ge-dev-user-player_1"}'
```

**Response:**
```json
{
  "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "player_id": "player_1",
  "expires_in": 3600
}
```

**Use Token in Commands:**
```bash
export TOKEN="<session_token>"
curl -X POST http://localhost:8000/commands/move \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ship_id": 201, "target_x": 6, "target_y": 5}'
```

---

## Smoke Testing

### Prerequisites

1. Docker Compose running (Postgres + Redis + API + ge-sim)
2. Valid DEV token for player_1 (owns ship 201)

### Test 1: Move Command + WebSocket Delta

**Terminal 1: Start services**
```bash
docker-compose -f docker-compose.dev.yml up
```

**Terminal 2: WebSocket client (subscribe to sector 1)**
```bash
# Get token for player_1
export TOKEN=$(curl -s -X POST http://localhost:8000/auth/exchange \
  -H "Content-Type: application/json" \
  -d '{"dev_token": "ge-dev-user-player_1"}' | jq -r .session_token)

# Connect WebSocket and subscribe
websocat "ws://localhost:8000/ws?token=$TOKEN"

# Send (type in terminal):
{"type": "subscribe", "sector_id": 1}

# You'll receive:
# 1. {"type": "subscribed", "sector_id": 1}
# 2. {"type": "sector_snapshot", ...}
# 3. Periodic deltas every ~6s from ge-sim
```

**Terminal 3: Issue move command**
```bash
export TOKEN=$(curl -s -X POST http://localhost:8000/auth/exchange \
  -H "Content-Type: application/json" \
  -d '{"dev_token": "ge-dev-user-player_1"}' | jq -r .session_token)

curl -X POST http://localhost:8000/commands/move \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ship_id": 201, "target_x": 6, "target_y": 5}' | jq
```

**Expected in Terminal 2 (WebSocket):**

Immediately after move command, you should receive:
```json
{
  "type": "sector_delta",
  "sector_id": 1,
  "events": [
    {
      "event_type": "ship_moved",
      "ship_id": 201,
      "old_position": {"x": 5, "y": 5},
      "new_position": {"x": 6, "y": 5},
      "heading": 90.0,
      "speed": 5.0,
      "timestamp": "2026-09-13T15:30:00.123456"
    }
  ]
}
```

---

### Test 2: Fire Command

**Terminal 3: Issue fire command**
```bash
curl -X POST http://localhost:8000/commands/fire \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ship_id": 201,
    "weapon_type": "phasor",
    "target_id": 202
  }' | jq
```

**Expected Response:**
```json
{
  "success": true,
  "ship_id": 201,
  "target_id": 202,
  "weapon_type": "phasor",
  "damage": 15.0,
  "event_published": true
}
```

**Expected in Terminal 2 (WebSocket):**
```json
{
  "type": "sector_delta",
  "sector_id": 1,
  "events": [
    {
      "event_type": "combat",
      "attacker_id": 201,
      "target_id": 202,
      "weapon_type": "phasor",
      "damage": 15.0,
      "timestamp": "2026-09-13T15:30:05.123456"
    }
  ]
}
```

---

### Test 3: Claim Planet

**Terminal 3: Issue claim command**
```bash
curl -X POST http://localhost:8000/commands/claim \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ship_id": 201,
    "planet_id": 102
  }' | jq
```

**Expected Response:**
```json
{
  "success": true,
  "planet_id": 102,
  "planet_name": "New Horizon",
  "owner_id": "player_1",
  "event_published": true
}
```

**Expected in Terminal 2 (WebSocket):**
```json
{
  "type": "sector_delta",
  "sector_id": 1,
  "events": [
    {
      "event_type": "planet_claimed",
      "planet_id": 102,
      "planet_name": "New Horizon",
      "owner_id": "player_1",
      "timestamp": "2026-09-13T15:30:10.123456"
    }
  ]
}
```

---

### Test 4: Verify Planet Claimed (REST)

```bash
curl http://localhost:8000/sectors/1 \
  -H "Authorization: Bearer $TOKEN" | jq '.planets'
```

**Expected:**
Planet 102 now shows `"owner_id": "player_1"` (in-memory state updated).

---

### Test 5: Authorization Tests

**Test 5a: Missing token**
```bash
curl -X POST http://localhost:8000/commands/move \
  -H "Content-Type: application/json" \
  -d '{"ship_id": 201, "target_x": 6, "target_y": 5}'
```

**Expected:** `401 Unauthorized`

**Test 5b: Wrong player tries to move another player's ship**
```bash
# Get token for player_3
export TOKEN_P3=$(curl -s -X POST http://localhost:8000/auth/exchange \
  -H "Content-Type: application/json" \
  -d '{"dev_token": "ge-dev-user-player_3"}' | jq -r .session_token)

# Try to move player_1's ship (201)
curl -X POST http://localhost:8000/commands/move \
  -H "Authorization: Bearer $TOKEN_P3" \
  -H "Content-Type: application/json" \
  -d '{"ship_id": 201, "target_x": 6, "target_y": 5}'
```

**Expected:** `403 Forbidden` with message "You do not own this ship"

**Test 5c: Claim already-owned planet**
```bash
# Planet 101 is owned by player_1
curl -X POST http://localhost:8000/commands/claim \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ship_id": 201, "planet_id": 101}'
```

**Expected:** `403 Forbidden` with message "Planet 101 is already owned"

---

## Stub Data

### Ships (In-Memory Store)

| ship_id | owner_id | sector_id | position_x | position_y | class_type |
|---------|----------|-----------|------------|------------|------------|
| 201     | player_1 | 1         | 5          | 5          | frigate    |
| 202     | player_3 | 1         | 5          | 5          | scout      |
| 203     | player_1 | 3         | 6          | 5          | miner      |

### Planets (In-Memory Store)

| planet_id | name              | owner_id | sector_id |
|-----------|-------------------|----------|-----------|
| 101       | Terra Prime       | player_1 | 1         |
| 102       | New Horizon       | None     | 1         |
| 103       | Mining Station 7  | player_2 | 1         |

---

## What's Included (Phase C3a)

✅ **Session-gated commands**
- All endpoints require Bearer token via `get_current_player` dependency
- 401 for missing/invalid tokens
- 403 for ownership violations

✅ **State updates**
- In-memory dictionaries for ships/planets
- Clear TODOs for Postgres migration
- State persists across requests (until server restart)

✅ **Redis event publishing**
- All commands publish to `sector:{id}:delta` channel
- Events match ge-sim event format (consistent with Phase C2c)
- WebSocket clients receive instant feedback

✅ **Ownership validation**
- Players can only move/fire their own ships
- Players can only claim unowned planets

✅ **WebSocket integration**
- Events flow through existing C2c Redis pub/sub path
- No code changes needed in websocket.py

---

## What's NOT Included (Future Phases)

❌ **Postgres persistence**
- State updates are in-memory (restart clears state)
- TODO comments mark where to add DB queries
- Schema exists in `database/models.py` (Ship, Planet tables)

❌ **ge-sim tick integration**
- Commands publish instantly (no 6s tick queuing)
- Real combat damage should be computed by ge-sim resolver
- Future: Commands queue actions, ge-sim processes on next tick

❌ **Business rule validation**
- No same-sector checks for fire/claim
- No weapon range, cooldown, or energy cost validation
- No ship speed/heading physics
- No planet production initialization on claim

❌ **Multi-sector movement**
- Move command updates position but doesn't handle sector transitions
- No warp mechanics or energy cost for cross-sector travel

❌ **Transactional integrity**
- No rollback if Redis publish fails
- Future: Use database transactions + outbox pattern

---

## Differences from Phase C2a/C2c Stubs

| Aspect               | C2a/C2c (Stubs)          | C3a (Real Commands)                |
|----------------------|--------------------------|------------------------------------|
| **Command endpoints** | Returned 501 Not Implemented | Fully functional, publish events  |
| **Authentication**   | Not enforced on commands | Required via Bearer token          |
| **State updates**    | None                     | In-memory ship/planet stores       |
| **Event source**     | ge-sim ticks only        | Commands + ge-sim ticks (both)     |
| **Ownership checks** | None                     | Validates player owns ship/planet  |

---

## Integration with Existing Components

### Phase C2a REST/WebSocket
- Commands use same `get_current_player` dependency as `/sectors` endpoints
- Events publish to same `sector:{id}:delta` Redis channels
- No changes needed to `websocket.py` or `sectors.py`

### Phase C2c ge-sim Deltas
- Commands publish to same channels as ge-sim (6s/55s ticks)
- WebSocket clients receive both command events and tick events
- Event format is consistent (`event_type`, timestamp, etc.)

### Redis Pub/Sub Bridge
- Commands reuse `get_redis()` helper from `websocket.py` pattern
- Connection is lazily initialized
- TODO: Add Redis cleanup in `main.py` shutdown for commands module

---

## Future Work

**Phase C3b:** Postgres Integration
- Replace in-memory stores with SQLAlchemy queries
- Use `database/models.py` Ship/Planet models
- Add database transaction handling
- Implement outbox pattern for event publishing (atomicity)

**Phase C3c:** ge-sim Command Queue
- Commands publish to Redis `command_queue` channel
- ge-sim processes commands on next 6s tick (not instant)
- Real combat damage formulas
- Movement physics (energy cost, speed, heading)

**Phase D:** Advanced Business Rules
- Same-sector validation for fire/claim
- Weapon range, cooldown, energy checks
- Planet production initialization on claim
- Multi-sector warp mechanics
- Safe Harbor invulnerability checks

**Phase E:** Optimistic Client Updates
- Return predicted state changes in command responses
- Client applies optimistic update, rollback on server rejection
- Reduce perceived latency for player actions

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  Unity Client                                                   │
│                                                                 │
│  User Action → POST /commands/{action} (Bearer token)          │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI (api/routes/commands.py)                               │
│                                                                 │
│  1. Validate token (get_current_player dependency)              │
│  2. Validate ownership (ship belongs to player)                 │
│  3. Update state (in-memory _ship_store / _planet_store)        │
│  4. Publish event to Redis                                      │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Redis PUBLISH
                         │ channel: sector:{id}:delta
                         ▼
              ┌──────────────┐
              │ Redis Pub/Sub│
              └──────┬───────┘
                     │
                     │ Redis SUBSCRIBE (from Phase C2c)
                     │
   ┌─────────────────┼────────────────────────────────────┐
   │  FastAPI        │                                    │
   │  (websocket.py) ▼                                    │
   │  ┌────────────────────────────────────┐             │
   │  │ subscribe_to_redis_sector()        │             │
   │  │ Forwards Redis msgs → WebSocket    │             │
   │  └────────┬───────────────────────────┘             │
   │           │                                          │
   └───────────┼──────────────────────────────────────────┘
               │
               │ WebSocket SEND (JSON)
               ▼
       ┌──────────────┐
       │ Unity Client │
       │ (subscribed  │
       │  to sector)  │
       └──────────────┘
```

---

## Key Files Changed

| File | Changes |
|------|---------|
| `api/routes/commands.py` | Replaced 501 stubs with real implementations, added auth, Redis publishing |
| `docs/PHASE_C3A_COMMANDS.md` | This document |

---

## Verification Checklist

- [x] All command endpoints require Bearer token authentication
- [x] Commands validate player ownership (403 for violations)
- [x] Commands update in-memory state stores
- [x] Commands publish events to Redis `sector:{id}:delta` channel
- [x] Events visible to WebSocket clients subscribed to sector
- [x] Clear TODOs for Postgres migration
- [x] Consistent event format with ge-sim deltas
- [x] 401/403/404 error handling
- [x] Smoke test instructions included

---

## Contact

Questions? Reach Empire Lead (Jeremy) or GE Stack Architect via project channels.

**Repository:** [talktojer/ge](https://github.com/talktojer/ge) (private)
