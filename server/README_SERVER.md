# Galactic Empire - Backend Server

FastAPI + ge-sim asyncio backend for mobile MMO.

## Architecture

Per `docs/PHASE1B_STACK_ADR.md`:
- **FastAPI**: REST endpoints + WebSocket for real-time updates
- **ge-sim**: Asyncio world simulation service (6s ship tick, 55s planet tick)
- **PostgreSQL**: Authoritative persistent state
- **Redis**: Hot state, pubsub, presence, sector subscriptions
- **Firebase Auth**: Mobile authentication (Sign in with Apple/Google)

## Directory Structure

```
server/
├── api/                    # FastAPI application
│   ├── main.py            # FastAPI app entry point
│   ├── routes/            # REST + WebSocket endpoints
│   │   ├── auth.py        # POST /auth/exchange (Firebase JWT -> session token)
│   │   ├── player.py      # GET /player/profile, /player/ships, /player/planets
│   │   ├── commands.py    # POST /commands/move, /commands/fire, /commands/claim
│   │   └── websocket.py   # WebSocket /ws (sector subscriptions, real-time updates)
│   ├── models/            # Pydantic models (TODO)
│   ├── middleware/        # Auth, CORS, rate limiting (TODO)
│   └── services/          # Business logic (TODO)
│
├── ge_sim/                # World simulation service
│   ├── __main__.py        # Entry point for python -m ge_sim
│   ├── sim_engine.py      # Main asyncio simulation loop
│   ├── ship_tick.py       # 6s tick: ship movement, combat, shields, energy
│   ├── planet_tick.py     # 55s tick: production, taxes, spies, population
│   └── event_publisher.py # Publish deltas to Redis for WebSocket fan-out
│
├── database/              # Database schema
│   └── models.py          # SQLAlchemy models (users, ships, planets, sectors, teams)
│
├── tests/                 # Pytest tests (stubs)
│   └── test_api.py        # API tests (TODO)
│
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template (NO secrets)
├── Dockerfile.api         # API container image
├── Dockerfile.ge-sim      # ge-sim container image
└── README_SERVER.md       # This file
```

## Installation

```bash
# Install Python 3.11+
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (see .env.example)
cp .env.example .env
# Edit .env with your Firebase credentials, Postgres URL, Redis URL
```

## Running Locally

### Option 1: Docker Compose (recommended)

```bash
# From workspace root
docker-compose -f docker-compose.dev.yml up

# API available at http://localhost:8000
# ge-sim runs in background
# Postgres on localhost:5432
# Redis on localhost:6379
```

### Option 2: Manual

```bash
# Terminal 1: Start Postgres + Redis
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:15
docker run -d -p 6379:6379 redis:7

# Terminal 2: Run API
cd server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Run ge-sim
cd server
python -m ge_sim
```

## API Endpoints

### Authentication
- `POST /auth/exchange` - Exchange Firebase JWT for session token (DEV mode: use dev_token)
- `GET /auth/me` - Get current authenticated player info

### Galaxy & Sectors (Phase C2a ✅)
- `GET /sectors` - Galaxy overview with all sector stubs
- `GET /sectors/{id}` - Detailed sector data (planets, ships)

**Phase C2a Status**: Implemented with stub data. See [docs/PHASE_C2A_MAP_API.md](../docs/PHASE_C2A_MAP_API.md) for full API documentation and testing examples.

### Player (Stub)
- `GET /player/profile` - Get player profile
- `GET /player/ships` - List player ships
- `GET /player/planets` - List player planets

### Commands (Stub, require auth)
- `POST /commands/move` - Move ship to sector
- `POST /commands/fire` - Fire weapons at target
- `POST /commands/claim` - Claim planet

### Trade (Not yet implemented)
- `POST /trade/buy` - Buy items at docked planet
- `POST /trade/sell` - Sell cargo at docked planet

### WebSocket (Phase C2a ✅)
- `WS /ws` - Real-time sector updates
  - Auth: Query param `?token=<jwt>` or message `{"type": "auth", "token": "..."}`
  - Subscribe: `{"type": "subscribe", "sector_id": 1}`
  - Unsubscribe: `{"type": "unsubscribe", "sector_id": 1}`
  - Snapshot: Server sends full sector state on subscribe
  - Deltas: Periodic updates (heartbeat, ship movements) every 5s
  
**Phase C2a Status**: Implemented with stub deltas. See [docs/PHASE_C2A_MAP_API.md](../docs/PHASE_C2A_MAP_API.md) for WebSocket protocol details.

## ge-sim Simulation Engine

### 6-Second Ship Tick

Processes all active ships:
- Apply movement physics (position += velocity * 6s)
- Resolve combat damage (phasor/torpedo hits)
- Recharge shields, energy (per ship stats)
- Track torpedo/missile positions
- Check mine proximity
- Kill ships at 100% damage
- Publish ship deltas to Redis

### 55-Second Planet Tick

Processes all owned planets:
- Run production multipliers (Men, Fighters, Gold, Food per rates)
- Collect taxes from population
- Check spy discovery/intel
- Update population growth
- Send push notifications (production ready, stockpile full)
- Publish planet deltas to Redis

### Event Publishing

ge-sim writes to Redis pubsub:
- `sector:{x}:{y}:ship_moved` - Ship position update
- `sector:{x}:{y}:combat_damage` - Damage dealt
- `planet:{id}:production_ready` - Production cycle complete

API WebSocket handlers subscribe to Redis channels and fan-out to connected clients.

## Database Schema

### Tables (simplified)
- `users` - account, cash, kills, planets_owned, team_id
- `ships` - owner_id, position_x, position_y, heading, speed, damage, energy, cargo
- `sectors` - x, y, type, wormhole_target_id, planet_count
- `planets` - sector_id, owner_id, treasury, tax_rate, production_rates, item_stocks
- `teams` - name, members, score
- `mail` - recipient_id, type (attack/production/spy), content, read_at

## Authentication

### Phase C1 Implementation (DEV Bypass)

**Default mode on ge.jersweb.net: DEV BYPASS**

POST /auth/exchange accepts a dev token instead of Firebase JWT:
- Body: `{"dev_token": "ge-dev-user-123"}` 
- OR Header: `X-GE-Dev-Token: ge-dev-user-123`
- Format: `ge-dev-user-{any_id}` where `any_id` becomes the player_id
- Returns session JWT valid for 1 hour

GET /auth/me returns player stub (requires Bearer token):
- Header: `Authorization: Bearer {session_token}`
- Returns: `{player_id, display_name, cash, kills, planets_owned}`

### Firebase Auth Integration (Future)

1. Unity client: User signs in with Apple/Google → obtains Firebase ID token
2. Client: POST /auth/exchange with Firebase token
3. Backend: Validates token with Firebase Admin SDK
4. Backend: Creates/updates user in Postgres, generates session JWT (1-hour TTL)
5. Client: Uses session JWT for all API calls
6. Client: Firebase SDK auto-refreshes ID token (no custom refresh endpoint needed)

## Environment Variables

See `.env.example`:
- `FIREBASE_PROJECT_ID` - Firebase project ID
- `FIREBASE_CREDENTIALS_JSON` - Firebase service account JSON (base64 or path)
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET` - Secret key for session JWT signing
- `ENVIRONMENT` - dev/staging/production

## Development Status

**Phase B Scaffold**: Directory structure + stub files with TODO comments.
No implementation code yet. See inline TODOs in each file for next steps.

## Combat Pacing

~6 second strategic tick (not twitch):
- Commands queued instantly (optimistic client response)
- Server resolves on next tick boundary
- Encourages strategic positioning, coordination over APM spam

## Offline Protection

Per `PHASE1B_GAME_DESIGN.md` §8.2:
- Safe Harbor: Dock at NPC citadel (invulnerable, costs rent)
- Insurance: Pay premium to recover 75% cargo on death
- Push notifications: Alert player of attacks while offline

## Monetization

**F2P + Cosmetics ONLY** (LOCKED by Empire Lead):
- Ship skins, planet themes, flags, VFX, emotes
- **NO P2W**: Zero production speedups, combat power, energy refills
- Cosmetic shop endpoints (future Phase 2+)

## Testing

```bash
# Run tests
pytest tests/

# Run specific test file
pytest tests/test_api.py -v

# Coverage
pytest --cov=api --cov=ge_sim tests/
```

## Deployment

See `PHASE1B_STACK_ADR.md` §2 for Fly.io deployment:
- `flyctl deploy --config fly.api.toml` - Deploy API
- `flyctl deploy --config fly.ge-sim.toml` - Deploy ge-sim
- Postgres: Neon or Supabase managed Postgres
- Redis: Upstash Redis

## Resources

- Stack ADR: `../docs/PHASE1B_STACK_ADR.md`
- Game Design: `../docs/PHASE1B_GAME_DESIGN.md`
- UX Vision: `../docs/PHASE1B_CLIENT_UX_VISION.md`
