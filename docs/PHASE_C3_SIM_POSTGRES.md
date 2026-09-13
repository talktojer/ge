# Phase C3: Postgres-Backed Sector State (ge-sim Integration)

**Status:** Implemented (Draft PR)  
**Date:** 2026-09-13  
**Dependencies:** Phase C2c (PR #17, commit 85b2966)

---

## Executive Summary

Phase C3 replaces ge-sim's hardcoded stub data with **Postgres-backed state persistence**. Ships and planets now read/write to the database on each tick (6s ship tick, 55s planet tick), and WebSocket `sector_delta` events reflect real DB state changes.

### Key Changes

- ✅ **Alembic migrations** for database schema (users, teams, sectors, planets, ships)
- ✅ **ge-sim reads ship/planet state from Postgres** on each tick
- ✅ **ge-sim writes updated state back to Postgres** after processing
- ✅ **Sector snapshots (REST API)** now query DB for real-time state
- ✅ **Seed data script** to populate test data
- ✅ **Deltas only published when state changes** (visible across ticks)

**Scope:** Sector 1 minimum; multi-sector support works if data exists. Simple stub updates (energy recharge, position drift) demonstrate DB round-trip. Full combat/physics reserved for later phases.

---

## Architecture Changes

### Before (Phase C2c)

```
ge-sim tick loops
  └─> Hardcoded stub data
      └─> Publish fake events to Redis
          └─> WebSocket forwards to clients

Sector REST API
  └─> Return hardcoded STUB_SECTOR_DETAILS
```

### After (Phase C3)

```
ge-sim tick loops
  └─> SELECT ships/planets FROM Postgres
      └─> Apply simple updates (energy, position, production)
          └─> UPDATE ships/planets in Postgres
              └─> Publish REAL deltas to Redis (only changed fields)
                  └─> WebSocket forwards to clients

Sector REST API
  └─> SELECT sector, ships, planets FROM Postgres
      └─> Return live state (or fall back to stub if missing)
```

---

## Database Schema

**Migration:** `e671003de52c_initial_schema_for_ships_planets_.py`

### Tables Created

1. **teams** - Alliances (id, name, score, created_at)
2. **users** - Player accounts (id, username, cash, kills, planets_owned, team_id, created_at)
3. **sectors** - Galaxy sectors (id, shard_id, x, y, type, wormhole_target_id, planet_count)
4. **planets** - Planets (id, sector_id, owner_id, name, treasury, tax_rate, production_rates, item_stocks, population, is_safe_harbor, npc_defender_count, etc.)
5. **ships** - Ships (id, owner_id, name, class_type, position_x, position_y, heading, speed, damage, energy, shields, cargo, is_docked, docked_planet_id, insurance_active, insurance_expiry)

### Running Migrations

```bash
# From server/ directory
export DATABASE_URL="postgresql+asyncpg://postgres:dev@localhost:5432/galactic_empire"

# Run migrations (requires Postgres running)
PYTHONPATH=/workspace/server python3 -m alembic upgrade head
```

---

## ge-sim Changes

**File:** `server/ge_sim/sim_engine.py`

### Ship Tick (6s)

1. **Load active ships** from Postgres (not docked, damage < 100)
2. **Apply simple updates:**
   - Energy recharge: +5% per tick (cap 100)
   - Shield recharge: +3% per tick (cap 100)
   - Position drift: simple periodic movement (stub for real physics)
3. **Write updated state** back to Postgres
4. **Publish deltas** to Redis `sector:{id}:delta` **only for ships that moved or changed**

### Planet Tick (55s)

1. **Load owned planets** from Postgres (owner_id IS NOT NULL)
2. **Apply simple production:**
   - Add items based on `production_rates` (e.g., {"men": 40, "food": 50})
   - Collect taxes: `tax_rate%` of population → treasury
   - Update `item_stocks` JSON field
3. **Write updated state** back to Postgres
4. **Publish deltas** to Redis `sector:{id}:delta` and `planet:{id}:production_ready`

### Database Connection

- Uses `asyncpg` driver (async Postgres)
- Connection pool initialized in `start()`, disposed in `stop()`
- URL from `DATABASE_URL` env var (defaults to localhost:5432)

---

## Sector REST API Changes

**File:** `server/api/routes/sectors.py`

### GET /sectors/{sector_id}

**Before:** Returned hardcoded `STUB_SECTOR_DETAILS[sector_id]`

**After:** 
1. Query `Sector` from DB by ID
2. Query `Ship` entities where position_x/y matches sector coordinates
3. Query `Planet` entities where sector_id matches
4. Join with `User` table to get owner names
5. Return `SectorDetail` with live data
6. Fall back to stub data if sector not found in DB (graceful degradation)

---

## Seed Data

**File:** `server/seed_data.py`

Run this script to populate the database with test data:

```bash
cd server/
export DATABASE_URL="postgresql+asyncpg://postgres:dev@localhost:5432/galactic_empire"
PYTHONPATH=/workspace/server python3 seed_data.py
```

### Seeded Data

- **1 team:** Alpha Squad
- **3 users:** Player_1, Player_2, Player_3
- **5 sectors:** Core Sector (5,5), Nebula Expanse (5,6), Asteroid Belt (6,5), Safe Harbor (4,5), Frontier Outpost (5,4)
- **3 planets:** Terra Prime (owned by Player_1), New Horizon (unclaimed), Mining Station 7 (owned by Player_2)
- **3 ships:** USS Enterprise (Player_1), Scout Alpha (Player_3), Dreadnought (Player_2)

All ships start in sector (5,5) or (6,5) with energy/shields ready for ticking.

---

## Smoke Testing

### Prerequisites

1. **Docker Compose running** (Postgres + Redis)
2. **Migrations applied** (`alembic upgrade head`)
3. **Database seeded** (`python seed_data.py`)
4. **ge-sim + API running**

### Test 1: Verify Ship State Changes Across Ticks

```bash
# Terminal 1: Watch ge-sim logs
docker logs -f ge-sim-dev

# Look for:
# ship_tick_start tick=1
# ships_loaded count=3
# ship_tick_complete tick=1 ships_processed=3 events_published=X

# Verify ships are loaded from DB (count=3 matches seeded ships)
```

### Test 2: Query Sector 1 Before and After Ticks

```bash
# Get DEV token
export TOKEN="ge-dev-user-alice"

# Query sector 1 snapshot (initial state)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/sectors/1 | jq '.ships[] | {id, position_x, position_y, energy, shields}'

# Wait 6+ seconds for a ship tick

# Query again (should see position or energy/shields changed)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/sectors/1 | jq '.ships[] | {id, position_x, position_y, energy, shields}'
```

**Expected:** Energy/shields increase (recharge), position may drift slightly (stub movement).

### Test 3: WebSocket Receives DB-Driven Deltas

```bash
# Terminal 1: Connect WebSocket
export TOKEN="ge-dev-user-alice"
websocat "ws://localhost:8000/ws?token=$TOKEN"

# Send subscribe message
{"type": "subscribe", "sector_id": 1}

# Expected responses:
# 1. {"type": "subscribed", "sector_id": 1}
# 2. {"type": "sector_snapshot", ...} with live ship/planet data from DB
# 3. Every ~6s: {"type": "sector_delta", "events": [...]} with ship_moved events
#    - Events should show actual energy/shields values from DB
#    - Position changes should match DB state
```

### Test 4: Planet Production Tick

```bash
# Query planet 101 (Terra Prime) before tick
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/sectors/1 | jq '.planets[] | select(.id == 101)'

# Wait 55+ seconds for a planet tick

# Query again
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/sectors/1 | jq '.planets[] | select(.id == 101)'

# Check ge-sim logs for planet_tick_complete
docker logs ge-sim-dev | grep planet_tick_complete

# Expected: planet_events_published > 0 (if any planets have production_rates)
```

**Note:** Planet `item_stocks` is JSON in DB; REST API may not expose it yet (out of scope). Check logs for production confirmation.

### Test 5: Verify Deltas Only When State Changes

```bash
# Set a ship to speed=0 (no movement stub) directly in DB
docker exec -it ge-postgres-dev psql -U postgres -d galactic_empire -c "UPDATE ships SET speed = 0 WHERE id = 202;"

# Watch WebSocket deltas for sector 1
# Ship 202 should NOT appear in ship_moved events (no position change)
# Ship 201 and 203 (with speed > 0) should still appear
```

---

## Out of Scope (Phase C3)

Phase C3 proves the DB integration pipeline. The following are **intentionally stub/incomplete:**

- ❌ **Full combat resolution:** No phasor damage, torpedo tracking (stub recharge only)
- ❌ **Real movement physics:** Position drift is periodic stub, not velocity-based
- ❌ **Production formulas:** Simple rate addition, no population growth, spy mechanics
- ❌ **Multi-sector routing:** Sectors 2-5 exist in DB but may not have ships/planets
- ❌ **Command persistence:** C3b work (if done separately) handles command row writes
- ❌ **Celery/background jobs:** Synchronous tick loops only
- ❌ **React/Unity Map redesign:** Client reads deltas; no UI changes required

**Next phases** will implement real combat, physics, and economy. C3 proves the **DB round-trip works**.

---

## Key Files Changed

| File | Changes |
|------|---------|
| `server/requirements.txt` | Added `alembic==1.13.3` |
| `server/alembic.ini` | Alembic config (URL from env) |
| `server/migrations/env.py` | Import models, set target_metadata |
| `server/migrations/versions/e671003de52c_*.py` | Initial schema migration |
| `server/ge_sim/sim_engine.py` | Added DB connection, SELECT ships/planets, UPDATE state, publish real deltas |
| `server/api/routes/sectors.py` | Added DB queries for GET /sectors/{id}, fall back to stubs |
| `server/seed_data.py` | Seed script for test data |
| `docs/PHASE_C3_SIM_POSTGRES.md` | This document |

---

## Verification Checklist

- [x] Alembic migrations created and documented
- [x] ge-sim connects to Postgres on startup
- [x] Ship tick loads ships from DB (visible in logs)
- [x] Ship tick writes updated state back to DB
- [x] Planet tick loads planets from DB (visible in logs)
- [x] Planet tick writes production results to DB
- [x] Sector REST API queries DB for live state
- [x] Seed data script creates test users/ships/planets
- [x] WebSocket deltas reflect DB changes (not hardcoded stubs)
- [x] Deltas only published when state changes (energy, position, production)
- [x] Smoke tests documented with curl + websocat examples
- [x] Documentation complete

---

## Docker Compose Integration

No changes to `docker-compose.dev.yml` required. Existing config already provides:
- Postgres connection string via `DATABASE_URL` env var
- Redis connection string via `REDIS_URL` env var
- Health checks for Postgres/Redis startup ordering

### First-Time Setup

```bash
# Start services
docker-compose -f docker-compose.dev.yml up -d

# Wait for Postgres to be ready
docker exec ge-postgres-dev pg_isready -U postgres

# Run migrations
docker exec ge-api-dev python3 -m alembic upgrade head

# Seed data (one-time)
docker exec ge-api-dev python3 seed_data.py

# Restart ge-sim to pick up fresh DB
docker-compose -f docker-compose.dev.yml restart ge-sim
```

---

## Coordination with C3b (Command Persistence)

If C3b work lands separately:

- **Shared models:** Both PRs use `database/models.py`; merge conflicts resolved by keeping both sets of columns
- **Shared migrations:** C3b should create its own migration for command tables; Alembic will apply both in order
- **Redis envelope:** C3 does not change command event structure; both can publish to `sector:{id}:delta`

**No conflict expected** as long as:
- C3b adds new tables (e.g., `commands`) without modifying existing tables
- C3b publishes command events with `event_type: "command_issued"` (distinct from `ship_moved`, `planet_production`)

---

## Future Work

**Phase C4+:** Implement real game logic
- Real movement physics: `position += velocity * dt`
- Combat damage formulas: phasor range, torpedo tracking
- Production caps: stockpile limits, population growth
- Multi-sector tick coverage: iterate all sectors with activity
- Command queue processing: consume queued player commands from DB/Redis

**Phase D:** Unity client
- Parse `sector_delta` events with DB-driven field values
- Interpolate ship movement over 6s intervals
- Display planet production counters

**Phase E:** Production deployment
- Connection pooling tuning (asyncpg pool size)
- Read replicas for REST API (writes go to primary)
- Monitoring: tick duration, DB query latency, Redis pub/sub lag

---

## Contact

Questions? Reach Empire Lead (Jeremy) or GE Stack Architect via project channels.

**Repository:** [talktojer/ge](https://github.com/talktojer/ge) (private)
