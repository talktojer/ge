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

- `Original_Code/` - Original MajorBBS C source code (preservation and reference)
- `docs/` - Phase 1 design documents and architecture decisions

## 🔒 Security Note

**Environment files removed**: Previously committed `.env` files have been removed from the repository and added to `.gitignore`. If you previously had access to this repository with committed secrets, please rotate any credentials that may have been exposed.

## 🗂️ Archive Notice

The 2025 web port (React frontend, Celery-based tick system, Docker/Nginx deployment) has been archived. Full history is preserved on the [`archive/2025-web-port`](https://github.com/talktojer/ge/tree/archive/2025-web-port) branch. The project is now focused on the Unity mobile client direction described above.

## 🚧 Current Status

**Phase A**: Repository cleanup and architecture planning (complete)
**Phase B**: Unity 6000.4.10f1 project scaffold + FastAPI + ge-sim implementation (upcoming)

---

## 🎮 Original Game

Galactic Empire by Mike Murdock - A classic MajorBBS door game from the 1990s where players commanded starships, colonized planets, formed alliances, and competed for galactic dominance.

## 📄 License

See the LICENSE file for details.
