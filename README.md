# Galactic Empire - Mobile Reimagine

A modern mobile reimagination of the classic Galactic Empire BBS door game, targeting iOS and Android with Unity 6000.4.10f1.

## 🎮 Project Vision

**Galactic Empire Mobile** brings the strategic depth of the 1990s MajorBBS classic to modern mobile platforms as a free-to-play MMO with cosmetic monetization and no pay-to-win mechanics.

### Core Experience
- **Mobile-First**: Native iOS/Android client built with Unity Editor 6000.4.10f1
- **Real-Time MMO**: Persistent 6-second tick system with 55-second orbital round-trip delay
- **Strategic Depth**: Space exploration, planetary conquest, economic empire building, tactical combat
- **Social**: Team alliances, diplomatic gameplay, in-game communications
- **Fair Play**: F2P with cosmetic monetization only - no pay-to-win

## 🏗️ Technical Architecture

### Client
- **Unity 6000.4.10f1**: iOS and Android builds
- **Firebase Auth**: Authentication and user management

### Backend
- **FastAPI**: Python asyncio-based game server
- **ge-sim**: Asyncio simulation engine (6s tick / 55s orbital mechanics)
- **PostgreSQL**: Persistent game state
- **Redis**: Session management and real-time state caching

### Monetization
- Free-to-play core experience
- Cosmetics only (ship skins, UI themes, effects)
- No gameplay advantages for payment

## 📚 Documentation

Phase 1 design documents are available in the `docs/` directory:

- [Phase 1A: Legacy System Map](docs/PHASE1A_LEGACY_SYSTEM_MAP.md) - Analysis of the original MajorBBS C implementation
- [Phase 1B: Game Design](docs/PHASE1B_GAME_DESIGN.md) - Mobile MMO game design vision
- [Phase 1B: Stack ADR](docs/PHASE1B_STACK_ADR.md) - Technical architecture decisions
- [Phase 1B: Client UX Vision](docs/PHASE1B_CLIENT_UX_VISION.md) - Mobile client UX/UI approach
- [Phase 1B: Screen Inventory](docs/PHASE1B_SCREEN_INVENTORY.md) - Complete screen-by-screen design

## 📂 Repository Structure

```
.
├── client/              # Unity 6000.4.10f1 mobile client (iOS + Android)
│   ├── Assets/         # Unity assets, scenes, scripts
│   ├── ProjectSettings/ # Unity project configuration
│   └── README_CLIENT.md # Client setup and architecture
│
├── server/              # FastAPI + ge-sim backend
│   ├── api/            # FastAPI REST + WebSocket endpoints
│   ├── ge_sim/         # Asyncio simulation engine (6s/55s ticks)
│   ├── database/       # SQLAlchemy models, Postgres connection
│   └── README_SERVER.md # Server setup and architecture
│
├── docs/               # Phase 1 design documents and ADRs
├── Original_Code/      # Original MajorBBS C source code (preservation)
├── docker-compose.dev.yml # Development environment (Postgres + Redis + API + ge-sim)
└── README.md           # This file
```

## 🚀 Quick Start

### Prerequisites

- **Client**: Unity Hub + Unity Editor 6000.4.10f1
- **Server**: Docker + Docker Compose (or Python 3.11+ for local development)

### Running the Backend (Development)

```bash
# Start Postgres, Redis, API, and ge-sim
docker-compose -f docker-compose.dev.yml up

# API available at http://localhost:8000
# Health check: http://localhost:8000/health
```

### Opening the Unity Client

1. Install Unity Hub and Unity Editor 6000.4.10f1
2. Open Unity Hub → Projects → Add → Select `client/` directory
3. Unity will recognize the project structure and open it

See [client/README_CLIENT.md](client/README_CLIENT.md) for detailed client setup.

See [server/README_SERVER.md](server/README_SERVER.md) for detailed server setup.

## 🎯 Phase B Scaffold Status

This branch contains the **Phase B scaffold**: directory structure, stub files, and architecture documentation. It is **not yet a runnable game**.

### What's Included

✅ **Client Structure**
- Unity project layout (Assets, ProjectSettings, Packages)
- 4-tab navigation stubs (Map, Fleet, Empire, Social)
- Core script stubs with TODO comments
- Firebase Auth placeholders
- WebSocket + REST client stubs

✅ **Server Structure**
- FastAPI application skeleton
- ge-sim asyncio engine with 6s/55s tick stubs
- SQLAlchemy database models
- WebSocket + REST endpoint stubs
- Docker Compose development environment
- .env.example (no secrets)

✅ **Documentation**
- README files for client and server
- Phase 1B design docs preserved
- Architecture decisions documented

### What's NOT Included

❌ Full Unity scenes/prefabs (requires Unity Editor on macOS for complete generation)  
❌ Implemented game logic (see TODO comments in files)  
❌ Firebase credentials (use .env.example and add your own)  
❌ Real database schema (migrations needed)  
❌ Runnable simulation (ge-sim stubs only)

## 🔒 Security Note

**Environment files removed**: Previously committed `.env` files have been removed from the repository and added to `.gitignore`. All `.env.example` files contain placeholder values only.

**Never commit secrets**: Firebase service account JSON, JWT secrets, database passwords, and API keys should NEVER be committed to the repository. Use environment variables or secure secret management.

## 🗂️ Archive Notice

The 2025 web port (React frontend, Celery-based tick system, Docker/Nginx deployment) has been archived. Full history is preserved on the [`archive/2025-web-port`](https://github.com/talktojer/ge/tree/archive/2025-web-port) branch. The project is now focused on the Unity mobile client direction described above.

## 🚧 Development Roadmap

**Phase A** ✅ Repository cleanup and architecture planning (complete)  
**Phase B** 🚧 Unity 6000.4.10f1 project scaffold + FastAPI + ge-sim stubs (this branch)  
**Phase C** ⏳ Core simulation implementation (6s/55s ticks, combat, production)  
**Phase D** ⏳ Unity client implementation (screens, networking, UI)  
**Phase E** ⏳ Firebase integration, authentication, deployment

## 🎮 Original Game

Galactic Empire by Mike Murdock - A classic MajorBBS door game from the 1990s where players commanded starships, colonized planets, formed alliances, and competed for galactic dominance.

## 📄 License

See the LICENSE file for details.

---

**Note**: This scaffold branch is for development setup and architecture review. It is NOT ready to merge into master. See inline TODO comments in each file for implementation tasks.
