# Phase C2c Smoke Test Guide

Quick verification that ge-sim ticks drive WebSocket deltas at correct intervals (6s/55s).

## Prerequisites

- Docker Compose installed
- `websocat` installed (or use Python test client)
- Services running: `docker-compose -f docker-compose.dev.yml up`

## Test 1: Verify ge-sim Tick Intervals

**Goal:** Confirm ship ticks fire every ~6s, planet ticks every ~55s.

```bash
# Watch ge-sim logs
docker logs -f ge-sim-dev | grep tick

# Expected output pattern:
# ship_tick_start tick=1 time=2026-09-12T17:45:30.123456
# ship_tick_complete tick=1 events_published=2
# [~6 second gap]
# ship_tick_start tick=2 time=2026-09-12T17:45:36.123456
# ship_tick_complete tick=2 events_published=2
# [~6 second gap]
# ship_tick_start tick=3 time=2026-09-12T17:45:42.123456

# [~55 seconds from start]
# planet_tick_start tick=1 time=2026-09-12T17:46:25.123456
# planet_tick_complete tick=1 planet_events_published=1
```

**Verification:**
- ✅ Ship ticks increment every ~6 seconds
- ✅ Planet ticks increment every ~55 seconds
- ✅ No errors logged

## Test 2: WebSocket Receives Real Deltas

**Goal:** Confirm WebSocket clients receive ge-sim events (not 5s stub timer).

### Option A: Using websocat

```bash
# Install websocat (if not installed)
# macOS: brew install websocat
# Linux: cargo install websocat

# Terminal 1: Start services
docker-compose -f docker-compose.dev.yml up

# Terminal 2: Connect WebSocket
export TOKEN="ge-dev-user-alice"
websocat -v "ws://localhost:8000/ws?token=$TOKEN"

# Type and press Enter:
{"type": "subscribe", "sector_id": 1}

# Expected responses:
# 1. Immediate: {"type":"authenticated","player_id":"alice"}
# 2. Immediate: {"type":"subscribed","sector_id":1}
# 3. Immediate: {"type":"sector_snapshot","sector_id":1,"data":{...}}
# 4. After ~6s: {"type":"sector_delta","sector_id":1,"events":[...]}
# 5. After ~12s: Another sector_delta (tick 2)
# 6. After ~18s: Another sector_delta (tick 3)
# 7. After ~55s: sector_delta with planet_production event
```

### Option B: Using Python test client

```bash
cd server
python test_websocket.py

# Expected output:
# Connected to WebSocket
# Authenticated as ge-dev-user-alice
# Sent subscribe request for sector 1
# Subscribed to sector 1
# Received sector_snapshot: {...}
# [~6s] Received sector_delta with tick=1
# [~6s] Received sector_delta with tick=2
# [~6s] Received sector_delta with tick=3
# [continues every ~6s]
```

**Verification:**
- ✅ Deltas arrive at **~6 second intervals** (NOT 5 seconds)
- ✅ Delta messages include `"tick"` field incrementing (1, 2, 3, ...)
- ✅ Delta messages include `"event_type": "heartbeat"` and `"ship_moved"`
- ✅ After ~55 seconds, receive `"event_type": "planet_production"`

## Test 3: Multiple Clients (Fan-out)

**Goal:** Verify Redis pub/sub enables fan-out to multiple clients.

```bash
# Terminal 1: Start services
docker-compose -f docker-compose.dev.yml up

# Terminal 2: Client A
export TOKEN="ge-dev-user-alice"
websocat "ws://localhost:8000/ws?token=$TOKEN"
{"type": "subscribe", "sector_id": 1}

# Terminal 3: Client B (different user)
export TOKEN="ge-dev-user-bob"
websocat "ws://localhost:8000/ws?token=$TOKEN"
{"type": "subscribe", "sector_id": 1}

# Both clients should receive the same deltas at the same time
# Verify timestamps in delta messages are identical or within 1ms
```

**Verification:**
- ✅ Both clients receive deltas simultaneously
- ✅ ge-sim logs show "events_published=2" per tick (one publish, two subscribers)
- ✅ No duplicate Redis publishes (efficient fan-out)

## Test 4: Redis Pub/Sub Directly

**Goal:** Confirm ge-sim publishes to Redis, independent of WebSocket.

```bash
# Terminal 1: Start services
docker-compose -f docker-compose.dev.yml up

# Terminal 2: Subscribe to Redis channel directly
docker exec -it ge-redis-dev redis-cli
SUBSCRIBE sector:1:delta

# Expected output every ~6 seconds:
# 1) "message"
# 2) "sector:1:delta"
# 3) "{\"type\":\"sector_delta\",\"sector_id\":1,\"events\":[...]}"

# After ~55 seconds:
# 1) "message"
# 2) "sector:1:delta"
# 3) "{\"type\":\"sector_delta\",\"sector_id\":1,\"events\":[{\"event_type\":\"planet_production\",...}]}"
```

**Verification:**
- ✅ Redis receives messages every ~6 seconds
- ✅ Messages are valid JSON
- ✅ Planet production events arrive after ~55 seconds

## Test 5: Timing Precision

**Goal:** Verify tick intervals are accurate (not drifting).

```bash
# Watch ge-sim logs with timestamps
docker logs -f ge-sim-dev | grep ship_tick_start

# Expected pattern (example):
# ship_tick_start tick=1 time=2026-09-12T17:45:30.123456
# ship_tick_start tick=2 time=2026-09-12T17:45:36.123456  (diff: 6.0s)
# ship_tick_start tick=3 time=2026-09-12T17:45:42.123456  (diff: 6.0s)
# ship_tick_start tick=4 time=2026-09-12T17:45:48.123456  (diff: 6.0s)
```

**Calculate interval manually:**
```bash
# Capture timestamps
T1="2026-09-12T17:45:30.123456"
T2="2026-09-12T17:45:36.123456"

# Python one-liner to compute diff:
python3 -c "from datetime import datetime; t1 = datetime.fromisoformat('$T1'); t2 = datetime.fromisoformat('$T2'); print((t2 - t1).total_seconds())"

# Expected: 6.0 (or 5.999-6.001 due to processing time)
```

**Verification:**
- ✅ Interval between ticks is 6.0s ± 0.1s (small variance due to processing)
- ✅ No drift over 10+ ticks (e.g., tick 10 is at ~60s, not 62s)
- ✅ ge-sim logs no "ship_tick_slow" warnings (processing < 6s)

## Test 6: Environment Variable Override

**Goal:** Confirm tick intervals can be overridden (for testing).

```bash
# Edit docker-compose.dev.yml:
# ge-sim:
#   environment:
#     SHIP_TICK_INTERVAL: 3.0      # Test: 3s instead of 6s
#     PLANET_TICK_INTERVAL: 10.0   # Test: 10s instead of 55s

# Restart services
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up

# Watch logs - ship ticks should now fire every ~3s, planet every ~10s
docker logs -f ge-sim-dev | grep tick
```

**Verification:**
- ✅ Ship ticks fire at custom interval (3s)
- ✅ Planet ticks fire at custom interval (10s)
- ✅ WebSocket clients receive deltas at new intervals
- ✅ Restore to 6.0/55.0 after test (ADR defaults)

## Common Issues

### Issue: Deltas still arriving every 5 seconds

**Cause:** C2a stub timer still running (code not updated).

**Fix:** Verify `api/routes/websocket.py` removed `asyncio.sleep(5)` and uses `subscribe_to_redis_sector()`.

### Issue: No deltas received (WebSocket silent)

**Cause:** Redis not running or ge-sim not connected.

**Diagnosis:**
```bash
# Check Redis is up
docker ps | grep redis
docker exec -it ge-redis-dev redis-cli ping  # Should return PONG

# Check ge-sim logs for Redis connection
docker logs ge-sim-dev | grep redis

# Expected: "event_publisher_connected redis_url=redis://redis:6379/0"
```

**Fix:** Ensure Redis service started before ge-sim in docker-compose.

### Issue: ge-sim logs "ship_tick_slow" warnings

**Cause:** Processing taking longer than 6s (approaching tick budget).

**Impact:** Acceptable for stub implementation (no real state processing yet). Will need optimization in Phase C3+.

**Diagnosis:**
```bash
docker logs ge-sim-dev | grep ship_tick_slow

# Example:
# ship_tick_slow tick=5 elapsed_seconds=6.2 target_interval=6.0
```

**Fix:** Phase C3+ will optimize (batch Postgres writes, spatial indexing). For now, expected with heavy logging.

## Success Criteria

All tests pass:
- ✅ ge-sim ship tick interval = 6.0s
- ✅ ge-sim planet tick interval = 55.0s
- ✅ WebSocket clients receive deltas every ~6s (not 5s)
- ✅ Planet production events arrive every ~55s
- ✅ Redis pub/sub forwarding works
- ✅ Multiple clients receive same deltas (fan-out)
- ✅ No errors in ge-sim or API logs

---

**Phase C2c smoke test complete!** 🎉

Next: Implement real ship/planet state in Phase C3.
