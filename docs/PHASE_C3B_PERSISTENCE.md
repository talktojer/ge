# Phase C3b: Postgres Persistence for Command State

**Status:** Implemented (Draft PR)  
**Date:** 2026-09-13  
**Dependencies:** Phase C3a (Commands + Redis Events)

---

## Executive Summary

Phase C3b replaces C3a's in-memory `_ship_store` / `_planet_store` dictionaries with authoritative Postgres reads and writes. Command effects now survive process restarts and support multi-worker deployments. All C3a behavior is preserved: session auth, ownership validation, and Redis event publishing.

**Key Changes:**
- Commands query and update `ships` / `planets` tables via SQLAlchemy
- Transactional updates with `SELECT ... FOR UPDATE` for race condition safety
- Redis publish is best-effort after successful database commit
- Dev seed script for test data (ships 201-203, planets 101-103)

---

## Architecture Changes

### Before (Phase C3a)
```python
# In-memory dictionaries
_ship_store: Dict[int, Dict[str, Any]] = {
    201: {"id": 201, "owner_id": "player_1", ...},
    ...
}

ship = _ship_store.get(ship_id)
ship["position_x"] = target_x
_ship_store[ship_id] = ship
```

### After (Phase C3b)
```python
# Postgres with SQLAlchemy async
result = await db.execute(
    select(Ship)
    .where(Ship.id == ship_id)
    .with_for_update()  # Row-level lock
)
ship = result.scalar_one_or_none()
ship.position_x = target_x
await db.commit()
```

---

## Database Setup

### 1. Connection Configuration

**Environment Variable:**
```bash
DATABASE_URL=postgresql+asyncpg://postgres:dev@localhost:5432/galactic_empire
```

**Connection Pool:**
- Initialized on API startup in `api/main.py`
- Pool size: 10, max overflow: 20
- Async driver: `asyncpg`

### 2. Database Session Dependency

New dependency in `database/__init__.py`:
```python
async def get_db_session() -> AsyncSession:
    """Provides async database session to FastAPI routes."""
```

**Usage in commands:**
```python
@router.post("/move")
async def move_ship(
    command: MoveCommand,
    player_id: str = Depends(get_current_player),
    db: AsyncSession = Depends(get_db_session)  # Inject DB session
):
    # Query and update database
    result = await db.execute(select(Ship).where(Ship.id == command.ship_id))
    ship = result.scalar_one_or_none()
    ...
```

---

## Schema Requirements

### Ships Table
Required columns for move/fire commands:
- `id` (Integer, PK)
- `owner_id` (String, FK to users.id)
- `sector_id` (Integer, FK to sectors.id)
- `position_x` (Integer)
- `position_y` (Integer)
- `heading` (Float, nullable)
- `speed` (Float, nullable)

### Planets Table
Required columns for claim command:
- `id` (Integer, PK)
- `name` (String)
- `owner_id` (String, FK to users.id, nullable)
- `sector_id` (Integer, FK to sectors.id)

Schema already defined in `database/models.py` (inherited from earlier phases).

---

## Dev Data Seeding

### Seed Script: `server/seed_dev_data.py`

Populates database with test data matching C3a in-memory stores:

**Ships:**
| ID  | Owner    | Sector | Position | Class   |
|-----|----------|--------|----------|---------|
| 201 | player_1 | 1      | (5, 5)   | frigate |
| 202 | player_3 | 1      | (5, 5)   | scout   |
| 203 | player_1 | 3      | (6, 5)   | miner   |

**Planets:**
| ID  | Name             | Owner    | Sector |
|-----|------------------|----------|--------|
| 101 | Terra Prime      | player_1 | 1      |
| 102 | New Horizon      | None     | 1      |
| 103 | Mining Station 7 | player_2 | 1      |

**Run Seed:**
```bash
cd server
DATABASE_URL=postgresql+asyncpg://... python seed_dev_data.py
```

**Idempotent:** Script skips seeding if ship 201 already exists.

---

## Command Implementation Details

### 1. Move Command

**Transactional Update:**
```python
# Lock row to prevent concurrent modifications
result = await db.execute(
    select(Ship)
    .where(Ship.id == command.ship_id)
    .with_for_update()
)
ship = result.scalar_one_or_none()

# Update position
ship.position_x = command.target_x
ship.position_y = command.target_y

# Commit to database
await db.commit()
await db.refresh(ship)
```

**Rollback on Error:**
```python
try:
    await db.commit()
except Exception as e:
    await db.rollback()
    raise HTTPException(status_code=500, detail="Failed to update ship position")
```

**Redis Publish (Best-Effort):**
- Publishes after successful commit
- Failure logged but doesn't rollback DB transaction
- Clients receive update on next ge-sim tick if publish fails

### 2. Fire Command

**Read-Only Validation:**
- No database writes (combat damage will be computed by ge-sim tick in future phase)
- Validates attacker and target exist in database
- Validates ownership via `ship.owner_id`

**No Transaction Needed:**
```python
# Simple SELECT (no lock needed, read-only)
result = await db.execute(select(Ship).where(Ship.id == command.ship_id))
ship = result.scalar_one_or_none()
```

### 3. Claim Command

**Transactional Claim with Race Condition Prevention:**
```python
# Lock planet row to prevent double-claim
result = await db.execute(
    select(Planet)
    .where(Planet.id == command.planet_id)
    .with_for_update()
)
planet = result.scalar_one_or_none()

# Check unowned (within transaction)
if planet.owner_id is not None:
    raise HTTPException(status_code=403, detail="Planet already owned")

# Claim planet
planet.owner_id = player_id
await db.commit()
```

**Why `FOR UPDATE`?**
- Prevents two concurrent claims from both seeing `owner_id = None`
- First transaction to acquire lock wins
- Second transaction sees updated `owner_id` and fails validation

---

## Error Handling

### Database Transaction Failures
```python
try:
    await db.commit()
    logger.info("command_committed", ...)
except Exception as e:
    await db.rollback()
    logger.error("command_failed", error=str(e))
    raise HTTPException(status_code=500, detail="Database operation failed")
```

### Redis Publish Failures
```python
try:
    await redis.publish(channel, json.dumps(sector_delta))
    logger.info("event_published", ...)
except Exception as e:
    # Log but don't rollback database commit
    logger.error("event_publish_failed", error=str(e))
```

**Failure Mode Documentation:**
- **DB commit succeeds, Redis publish fails:** Command effects persist in database. WebSocket clients miss instant update but receive state on next ge-sim tick or manual refresh.
- **DB commit fails, Redis publish not attempted:** Command returns 500 error, no state change persists.

---

## Smoke Testing

### Prerequisites

1. **Postgres running:**
   ```bash
   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=galactic_empire postgres:15
   ```

2. **Seed database:**
   ```bash
   cd server
   DATABASE_URL=postgresql+asyncpg://postgres:dev@localhost:5432/galactic_empire \
     python seed_dev_data.py
   ```

3. **Redis running:**
   ```bash
   docker run -d -p 6379:6379 redis:7
   ```

4. **Start API:**
   ```bash
   cd server
   DATABASE_URL=postgresql+asyncpg://postgres:dev@localhost:5432/galactic_empire \
   REDIS_URL=redis://localhost:6379/0 \
   uvicorn api.main:app --reload
   ```

### Run Smoke Test

```bash
cd server
./test_commands_c3b.sh
```

**Expected Output:**
```
✅ Move command successful (Postgres updated)
✅ Fire command successful
✅ Claim command successful (Postgres planet updated)
✅ Planet 102 ownership verified in Postgres
✅ Authorization check passed (403 Forbidden)
✅ Double-claim prevention passed (403 Forbidden)
```

### Manual Verification

**Query ship position after move:**
```bash
docker exec -it <postgres_container> psql -U postgres -d galactic_empire \
  -c "SELECT id, owner_id, position_x, position_y FROM ships WHERE id = 201;"
```

**Expected:** `position_x = 6` (updated from 5)

**Query planet ownership after claim:**
```bash
docker exec -it <postgres_container> psql -U postgres -d galactic_empire \
  -c "SELECT id, name, owner_id FROM planets WHERE id = 102;"
```

**Expected:** `owner_id = 'player_1'` (updated from `NULL`)

---

## Performance Considerations

### Connection Pool
- **Pool size 10:** Handles 10 concurrent requests
- **Max overflow 20:** Bursts up to 30 total connections
- **Adjust for production:** Scale based on expected load

### Row Locking
- `SELECT ... FOR UPDATE` blocks concurrent transactions
- **Move command:** Locks ship row (low contention)
- **Claim command:** Locks planet row (higher contention for popular planets)
- **Fire command:** No locks (read-only)

### Index Recommendations
```sql
-- Primary keys already indexed
-- Add composite index for common queries:
CREATE INDEX idx_ships_owner_sector ON ships(owner_id, sector_id);
CREATE INDEX idx_planets_sector_owner ON planets(sector_id, owner_id);
```

---

## Migration Notes

### From C3a to C3b

**What Changed:**
- Removed `_ship_store` / `_planet_store` dictionaries
- Added `db: AsyncSession = Depends(get_db_session)` to all commands
- Replaced dict lookups with `await db.execute(select(...))`
- Replaced dict updates with `ship.field = value` + `await db.commit()`

**What Stayed the Same:**
- Session auth via `get_current_player`
- Ownership validation (403 on mismatch)
- Redis publish to `sector:{id}:delta`
- Event format (unchanged, WebSocket clients compatible)
- HTTP response format (unchanged, Unity client compatible)

**Breaking Changes:**
- **None** (external API contracts preserved)

### Deployment Checklist

1. **Database schema:** Run migrations or seed script
2. **Environment:** Set `DATABASE_URL` in production
3. **Seed data:** Run `seed_dev_data.py` (dev only) or import production data
4. **Test:** Run `test_commands_c3b.sh` against staging
5. **Monitor:** Check logs for DB connection errors (`database_initialized`, `command_committed`, `command_failed`)

---

## Known Limitations (C3b)

**Still TODO (Future Phases):**

- ❌ Same-sector validation (fire/claim can target any sector)
- ❌ Weapon range, cooldown, energy cost checks
- ❌ Ship speed/heading physics for movement
- ❌ Planet production initialization on claim
- ❌ Multi-sector warp mechanics
- ❌ ge-sim command queue integration (commands execute instantly, not queued for 6s tick)
- ❌ Real combat damage formulas (stub damage used)
- ❌ Alembic migrations (seed script uses `create_all`)

---

## Differences from C3a

| Aspect              | C3a (In-Memory)                     | C3b (Postgres)                        |
|---------------------|-------------------------------------|---------------------------------------|
| **State storage**   | Python dicts (lost on restart)      | Postgres tables (persistent)          |
| **Concurrency**     | Not thread-safe                     | Row-level locks (`FOR UPDATE`)        |
| **Multi-worker**    | Fails (each worker has own state)   | Works (shared database)               |
| **Query syntax**    | `_ship_store.get(id)`               | `await db.execute(select(Ship)...)`   |
| **Update syntax**   | `_ship_store[id] = ship`            | `ship.field = val; await db.commit()` |
| **Seed data**       | Hardcoded in routes file            | `seed_dev_data.py` script             |
| **Redis publish**   | After dict update (always succeeds) | After DB commit (best-effort)         |
| **Rollback**        | Not applicable                      | Automatic on exception                |

---

## Files Changed

| File                            | Changes                                                    |
|---------------------------------|------------------------------------------------------------|
| `api/routes/commands.py`        | Replaced in-memory stores with Postgres queries            |
| `database/__init__.py`          | Added session management, pool initialization              |
| `database/models.py`            | Removed obsolete `create_db_pool` function                 |
| `api/main.py`                   | Initialize DB pool on startup, close on shutdown           |
| `server/seed_dev_data.py`       | New dev seed script                                        |
| `server/test_commands_c3b.sh`   | Updated smoke test with persistence verification           |
| `docs/PHASE_C3B_PERSISTENCE.md` | This document                                              |

---

## Verification Checklist

- [x] Commands use Postgres for reads/writes
- [x] Session auth preserved (Bearer token required)
- [x] Ownership validation preserved (403 for violations)
- [x] Redis event publishing preserved (sector delta format)
- [x] Transactional updates with rollback on error
- [x] Row-level locking for claim/move (race condition safe)
- [x] Dev seed script provided
- [x] Smoke test updated with persistence checks
- [x] Error handling for DB and Redis failures
- [x] Logging for commit/rollback/publish events
- [x] Database pool initialized on startup
- [x] Database pool closed on shutdown

---

## Contact

Questions? Reach Empire Lead (Jeremy) or GE Stack Architect via project channels.

**Repository:** [talktojer/ge](https://github.com/talktojer/ge) (private)
