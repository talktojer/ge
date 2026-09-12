# Phase C2c: ge-sim → WebSocket Deltas via Redis

**Status:** Implemented  
**Date:** 2026-09-12  
**Dependencies:** Phase C2a (PR #15, commit c1ea2ea)

---

## Executive Summary

Phase C2c implements the real-time tick→delta pipeline from ge-sim to WebSocket clients, replacing the Phase C2a stub 5-second timer with actual ge-sim-driven events at ADR-specified intervals:
- **Ship tick:** 6.0 seconds
- **Planet tick:** 55.0 seconds

Events flow: **ge-sim** (publishes) → **Redis pub/sub** → **API WebSocket** (subscribes & fans out) → **Unity clients**.

---

## Implementation Overview

### 1. ge-sim Event Publishing

**File:** `server/ge_sim/event_publisher.py`

- `EventPublisher` now connects to Redis and publishes real events
- Implements channel pattern: `sector:{id}:delta`, `planet:{id}:production_ready`
- All `publish_*` methods are fully functional (no more TODOs)

**File:** `server/ge_sim/sim_engine.py`

- Ship tick interval: **6.0s** (configurable via `SHIP_TICK_INTERVAL` env var)
- Planet tick interval: **55.0s** (configurable via `PLANET_TICK_INTERVAL` env var)
- `process_ship_tick()` publishes stub sector deltas every 6s
- `process_planet_tick()` publishes stub planet production every 55s
- Logs include tick counts, timing warnings if processing exceeds target interval

### 2. API WebSocket Redis Integration

**File:** `server/api/routes/websocket.py`

**Removed:** `broadcast_sector_deltas()` with `asyncio.sleep(5)` stub timer

**Added:** `subscribe_to_redis_sector()` 
- Opens Redis pub/sub connection per subscribed sector
- Listens on `sector:{id}:delta` channel
- Forwards Redis messages directly to WebSocket client
- Unsubscribes on client disconnect or unsubscribe

**Redis Connection Management:**
- Lazy initialization via `get_redis()`
- Cleanup in `api/main.py` shutdown event

### 3. Tick Cadence Verification

| Component | Interval | Source | Override |
|-----------|----------|--------|----------|
| Ship tick | 6.0s | ADR Phase 1b | `SHIP_TICK_INTERVAL` env var |
| Planet tick | 55.0s | ADR Phase 1b | `PLANET_TICK_INTERVAL` env var |
| ~~Stub timer~~ | ~~5.0s~~ | ~~C2a~~ | **Removed** |

Defaults match ADR. Environment variable overrides are supported for testing but not required.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  ge-sim (separate process)                                      │
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                    │
│  │ Ship Tick    │ 6.0s    │ Planet Tick  │ 55.0s              │
│  │ Loop         ├────────►│ Loop         ├──────────┐         │
│  └──────┬───────┘         └──────┬───────┘          │         │
│         │                        │                  │         │
│         │ publish events         │ publish events   │         │
│         ▼                        ▼                  ▼         │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ EventPublisher                                       │    │
│  │  - publish_sector_delta(sector_id, events)          │    │
│  │  - publish_planet_production_complete(planet_id)    │    │
│  └──────────────────┬───────────────────────────────────┘    │
│                     │                                          │
└─────────────────────┼──────────────────────────────────────────┘
                      │
                      │ Redis PUBLISH
                      │ channels: sector:{id}:delta
                      │           planet:{id}:production_ready
                      ▼
              ┌──────────────┐
              │ Redis Pub/Sub│
              └──────┬───────┘
                     │ Redis SUBSCRIBE
                     │
   ┌─────────────────┼────────────────────────────────────┐
   │  FastAPI (api)  │                                    │
   │                 ▼                                    │
   │  ┌────────────────────────────────────┐             │
   │  │ WebSocket Handler                  │             │
   │  │  - subscribe_to_redis_sector()     │             │
   │  │  - forwards Redis msgs → WebSocket │             │
   │  └────────┬───────────────────────────┘             │
   │           │                                          │
   └───────────┼──────────────────────────────────────────┘
               │ WebSocket SEND
               │ JSON messages
               ▼
       ┌──────────────┐
       │ Unity Client │
       │ (subscribed  │
       │  to sector)  │
       └──────────────┘
```

---

## Event Types

### Sector Delta (6s ship tick)

**Channel:** `sector:{sector_id}:delta`

**Published by:** `ge-sim` ship tick loop (every 6s)

**Example payload:**
```json
{
  "type": "sector_delta",
  "sector_id": 1,
  "events": [
    {
      "event_type": "heartbeat",
      "tick": 42,
      "timestamp": "2026-09-12T17:45:30.123456",
      "message": "Ship tick 42 (6s interval)"
    },
    {
      "event_type": "ship_moved",
      "ship_id": 201,
      "old_position": {"x": 5, "y": 5},
      "new_position": {"x": 6, "y": 5},
      "heading": 90.0,
      "speed": 5.0,
      "timestamp": "2026-09-12T17:45:30.123456"
    }
  ]
}
```

### Planet Production (55s planet tick)

**Channel:** `planet:{planet_id}:production_ready`

**Published by:** `ge-sim` planet tick loop (every 55s)

**Example payload:**
```json
{
  "planet_id": 101,
  "tick": 5,
  "timestamp": "2026-09-12T17:46:25.123456",
  "item_deltas": {
    "men": 100,
    "food": 50,
    "missiles": 10
  },
  "tax_collected": 500
}
```

Also published to sector delta channel for the sector containing the planet.

---

## Smoke Testing

### Prerequisites

1. Docker Compose running (Postgres + Redis + API + ge-sim)
2. Valid DEV token (from Phase C2a)

### Test 1: Verify ge-sim Tick Intervals

**Expected:** Ship tick logs every ~6s, planet tick logs every ~55s

```bash
# Terminal 1: Watch ge-sim logs
docker logs -f ge-sim-dev

# Look for:
# ship_tick_start tick=1 time=2026-09-12T17:45:30.123456
# ship_tick_complete tick=1 events_published=2
# [wait ~6 seconds]
# ship_tick_start tick=2 time=2026-09-12T17:45:36.123456

# [wait ~55 seconds from start]
# planet_tick_start tick=1 time=2026-09-12T17:46:25.123456
# planet_tick_complete tick=1 planet_events_published=1
```

### Test 2: WebSocket Receives ge-sim Deltas

**Use websocat or Python test client:**

```bash
# Install websocat: https://github.com/vi/websocat
# Or use Python script from server/test_websocket.py

# Terminal 1: Start services
docker-compose -f docker-compose.dev.yml up

# Terminal 2: Connect WebSocket with DEV token
export TOKEN="ge-dev-user-alice"
websocat "ws://localhost:8000/ws?token=$TOKEN"

# Send subscribe message:
{"type": "subscribe", "sector_id": 1}

# Expected responses:
# 1. Immediate: {"type": "subscribed", "sector_id": 1}
# 2. Immediate: {"type": "sector_snapshot", "sector_id": 1, "data": {...}}
# 3. After ~6s: {"type": "sector_delta", "sector_id": 1, "events": [{"event_type": "heartbeat", ...}, {"event_type": "ship_moved", ...}]}
# 4. After ~12s: Another sector_delta (tick 2)
# 5. After ~55s: sector_delta with planet_production event
```

**Verify timing:**
- Deltas arrive at **~6 second intervals** (not 5 seconds from C2a stub)
- Planet production appears at **~55 second intervals**

### Test 3: Python Test Script

```bash
cd server
python test_websocket.py

# Expected output:
# Connected to WebSocket
# Authenticated as ge-dev-user-alice
# Subscribed to sector 1
# Received snapshot: {...}
# [~6s] Received delta with tick=1
# [~6s] Received delta with tick=2
# [~6s] Received delta with tick=3
# [continues every ~6s]
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SHIP_TICK_INTERVAL` | `6.0` | Ship tick interval (seconds) |
| `PLANET_TICK_INTERVAL` | `55.0` | Planet tick interval (seconds) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |

### Docker Compose

Already configured in `docker-compose.dev.yml`:

```yaml
ge-sim:
  environment:
    SHIP_TICK_INTERVAL: 6.0      # ADR-specified
    PLANET_TICK_INTERVAL: 55.0   # ADR-specified
    REDIS_URL: redis://redis:6379/0

api:
  environment:
    REDIS_URL: redis://redis:6379/0
```

---

## Differences from Phase C2a

| Aspect | C2a (Stub) | C2c (Real) |
|--------|------------|------------|
| **Delta source** | Per-connection `asyncio.sleep(5)` timer | ge-sim ticks via Redis |
| **Tick interval** | 5 seconds (hardcoded) | 6s ship / 55s planet (configurable) |
| **Event fanout** | Direct broadcast in WebSocket handler | Redis pub/sub → multiple API instances |
| **Ship tick** | Fake, incremental position changes | Real ge-sim loop (stub data for now) |
| **Planet tick** | Not implemented | Real 55s production tick |
| **Scalability** | One timer per connection (wasteful) | Shared Redis subscription (efficient) |

---

## Out of Scope

**Phase C2c focuses on the tick→delta pipeline.** The following are intentionally **stub/incomplete:**

- ❌ **Real ship state:** Ships not loaded from Postgres; stub data published
- ❌ **Real planet state:** Planets not loaded from Postgres; stub data published
- ❌ **Combat resolution:** No actual phasor damage calculations
- ❌ **Movement physics:** No real ship position updates based on velocity
- ❌ **Database queries:** No Postgres reads/writes (TODOs remain)
- ❌ **Multi-sector support:** Only sector ID 1 receives events (stub)
- ❌ **Push notifications:** Offline player alerts not implemented

**Next phases** (C3, D, E) will implement actual game logic. C2c proves the **infrastructure** works.

---

## Key Files Changed

| File | Changes |
|------|---------|
| `ge_sim/event_publisher.py` | Added Redis connection, implemented all publish methods, added `publish_sector_delta()` |
| `ge_sim/sim_engine.py` | Added EventPublisher integration, publish stub events at 6s/55s, tick counters, timing warnings |
| `api/routes/websocket.py` | Removed 5s stub timer, added `subscribe_to_redis_sector()`, Redis pub/sub forwarding |
| `api/main.py` | Added Redis cleanup on shutdown |
| `docs/PHASE_C2C_GESIM_DELTAS.md` | This document |

---

## Verification Checklist

- [x] ge-sim connects to Redis on startup
- [x] Ship tick interval = 6.0s (configurable via env)
- [x] Planet tick interval = 55.0s (configurable via env)
- [x] EventPublisher publishes to Redis channels
- [x] WebSocket subscribes to Redis `sector:{id}:delta` channel
- [x] WebSocket forwards Redis messages to clients
- [x] 5s stub timer removed from WebSocket handler
- [x] Deltas observable via websocat/Python at ~6s intervals
- [x] Planet production events observable at ~55s intervals
- [x] Logs show tick counts and timing info
- [x] Docker Compose configuration includes Redis
- [x] Documentation complete

---

## Future Work

**Phase C3+:** Implement real game state
- Load ships/planets from Postgres in tick loops
- Apply movement physics (position += velocity × dt)
- Resolve combat damage formulas
- Multi-sector event publishing (iterate all sectors with activity)
- Handle disconnected ships (docked, destroyed, offline)

**Phase D:** Unity client
- Parse `sector_delta` events
- Interpolate ship movement over 6s
- Render planet production updates
- Subscribe to multiple sectors (viewport + adjacent)

**Phase E:** Production deployment
- Multiple API instances (horizontal scaling)
- Redis Cluster (if needed for high throughput)
- Metrics (tick duration, Redis pub/sub lag, WebSocket message rate)
- Alerts (tick duration > 5s, Redis unavailable)

---

## Contact

Questions? Reach Empire Lead (Jeremy) or GE Stack Architect via project channels.

**Repository:** [talktojer/ge](https://github.com/talktojer/ge) (private)
