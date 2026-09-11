# Phase 1b: Stack Architecture Decision Record – Galactic Empire Mobile MMO

**Status:** Proposed  
**Date:** 2026-09-11  
**Owners:** GE Stack Architect (talktojer/ge)  
**Context:** [Phase 1a: Legacy System Map](./PHASE1A_LEGACY_SYSTEM_MAP.md)

---

## Executive Summary

This ADR documents the architectural stack selection for the **Galactic Empire mobile MMO reimagine**: a true live, persistent-galaxy, strategic fleet conquest game for Unity (iOS + Android) with FastAPI backend. The chosen stack replaces the 1988 MajorBBS single-threaded, Btrieve-backed, BBS-session architecture with a modern event-driven, cloud-native, horizontally-scalable system while **preserving** the strategic pacing (6s combat tick, 55s production cycle) and space conquest fantasy that made the original compelling.

**Primary decision:** We select a **unified FastAPI + asyncio Python monorepo architecture** with Redis for hot state, PostgreSQL for authoritative persistence, Firebase Auth for mobile identity, and WebSockets for realtime client updates. We explicitly **reject** full-featured game engines (Nakama, Supabase Realtime as primary orchestration, Unity Netcode for GameObjects) because GE's strategic cadence (not twitch FPS) and conquest loop (fleet positioning, planetary economy, turn-based combat resolution) do not require lobby-based matchmaking, dedicated relay servers, or sub-100ms input replication. Our stack optimizes for **event-driven world simulation** that pushes deltas to interested clients, not peer-to-peer action synchronization.

---

## Table of Contents

1. [Context & Requirements](#1-context--requirements)
2. [Decision: Chosen Stack](#2-decision-chosen-stack)
3. [Alternatives Considered](#3-alternatives-considered)
4. [Architecture Overview](#4-architecture-overview)
5. [Mapping Legacy → Modern](#5-mapping-legacy--modern)
6. [Client Integration (Unity)](#6-client-integration-unity)
7. [Security & Authentication](#7-security--authentication)
8. [Scalability Path](#8-scalability-path)
9. [Deployment Topology](#9-deployment-topology)
10. [Risks & Open Questions](#10-risks--open-questions)
11. [Out of Scope / Non-Goals](#11-out-of-scope--non-goals)

---

## 1. Context & Requirements

### 1.1 Source of Truth

The [Phase 1a Legacy System Map](./PHASE1A_LEGACY_SYSTEM_MAP.md) documents the 1988 MajorBBS Galactic Empire codebase:

- **BBS ticks:** `TICKTIME=6s` (ship movement, combat resolution), `PLANTIME=55s` (planetary production, taxes, spies)
- **Btrieve persistence:** `GEship.dat`, `GEuser.dat`, `GEplanet.dat`, `GEmail.dat` — flat 256b/512b fixed-record files with single-threaded record-level locking
- **Single-threaded event loop:** MajorBBS `rtkick()` timers call tick handlers sequentially; no parallel execution
- **Offline vulnerability:** Ships and planets remain in-world while player offline; subject to NPC attacks, player raids, ongoing production
- **Shared 30×15 galaxy:** All players in one persistent universe, 450 sectors, ~4000 planets max, no instancing, open PvP sandbox
- **Strategic fleet/conquest core loop:** Explore → claim planets → produce goods → sell for cash → upgrade ships → engage in ship-to-ship or planetary conquest → accumulate score

### 1.2 Locked Constraints

- **Client:** Unity Editor 6000.0.10f1, iOS + Android targets
- **Backend foundation:** FastAPI + supporting stack (documented here)
- **True live MMO:** One shared persistent galaxy (not instanced lobbies)
- **Strategic fleet/conquest core:** Preserve turn-based strategic pacing (6s combat resolution, 55s production cycles) as server-driven event cadence
- **Realtime skirmish combat:** OPTIONAL for later phases (Phase 2+)
- **Preserve GE space conquest fantasy:** Modernized UX, but same empire-building, fleet combat, planetary economy meta
- **New private repo:** `talktojer/ge` — this ADR and design docs only, NO Unity project scaffold, NO runnable game code

### 1.3 Key Design Tensions

1. **BBS "synchronous command, async world" hybrid** vs. **mobile always-online real-time:**  
   - Legacy: Player logs into BBS session, issues text commands (`imp`, `pha`, `buy`), commands execute blocking-style but effects apply on next tick boundary; world simulates continuously even when player offline.
   - Modern: Mobile client expects instant responsiveness (tap → immediate UI feedback), persistent connection (WebSocket), push notifications for offline events. Cannot block user input for 6s waiting for tick.

2. **Single-threaded tick polling** vs. **horizontally scalable event-driven services:**  
   - Legacy: One MajorBBS process polls all ships/planets sequentially every 6s/55s. Max ~100 concurrent users (BBS line limits).
   - Modern: 1,000–10,000 concurrent mobile clients require load-balanced API servers, async I/O, distributed state (Redis), ACID database (Postgres), and event-driven schedulers (no polling).

3. **Offline vulnerability** vs. **mobile safe-harbor expectations:**  
   - Legacy: Ship frozen in-world when player disconnects; cyborgs and rival players can destroy it. Hardcore sandbox.
   - Modern: Mobile players expect logout = pause/safe state (or explicit "retreat to safe zone" mechanic). Requires infrastructure for push notifications (FCM/APNs) to alert player of attacks, and game-design layer (not implemented here) for offline protection rules.

4. **Strategic pacing (6s combat, 55s production)** vs. **twitch realtime combat:**  
   - Legacy: Combat resolved server-side at tick boundaries; players issue commands, wait for next tick to see damage. Tactical depth (positioning, coordination) over APM spam.
   - Modern: Many mobile games expect instant gratification (tap → explosion). We **preserve** strategic pacing to differentiate GE from action shooters, but design must make the 6s cadence feel deliberate (animations, telegraphed attacks, fleet coordination) not laggy.

5. **Text command parser (`imp`, `pha`, `buy`)** vs. **touch UI:**  
   - Legacy: 3-letter abbreviations optimized for 1200-baud modem text efficiency.
   - Modern: Visual buttons, drag-to-aim phasors, tap-to-lock torpedoes, planet management dashboards. Text commands killed entirely (except optional power-user console).

---

## 2. Decision: Chosen Stack

We adopt a **unified FastAPI + Python asyncio monorepo** architecture with the following components:

| Layer | Technology | Role |
|-------|-----------|------|
| **Client** | Unity 6000.0.10f1 (iOS + Android) | 3D/2D client rendering, input handling, local prediction/interpolation. Communicates via HTTPS REST (auth, inventory, commands) + WebSockets (sector/fleet subscriptions, realtime deltas). Push notifications via **Firebase Cloud Messaging (FCM) + APNs** (routed through Firebase) for offline alerts. |
| **Edge/API** | **FastAPI** (Python 3.11+) | REST endpoints for: authentication session exchange (Firebase JWT → short-lived API token), player inventory (ships, items, cash), planet CRUD (claim, set production rates, view status), fleet commands (move, fire, dock, trade). **Starlette WebSockets** for: sector interest subscriptions (client subscribes to sector X,Y → receives ship/planet delta updates), fleet event streams (combat damage, torpedo tracking, energy recharge), command acknowledgments (immediate "action queued" response + eventual "action resolved" push). |
| **Auth** | **Firebase Authentication** | Sign in with Apple + Google. Unity client obtains Firebase ID token → sends to FastAPI `/auth/exchange` → receives short-lived JWT (1-hour TTL) + refresh token. FastAPI validates JWT via Firebase Admin SDK (caches public keys). Token refresh handled by Firebase SDK on device (no custom refresh endpoint). |
| **Authoritative DB** | **PostgreSQL 15+** | Replaces Btrieve `.dat` files. Tables: `users` (account, cash, kills, planets, team affiliation), `ships` (position, heading, speed, damage, energy, cargo, shield/cloak status), `sectors` (type, wormholes, planet count), `planets` (owner, treasury, tax rate, production rates, item stocks, spies), `teams` (name, members, score), `mail` (async notifications: attack alerts, production reports, spy intel, killmails), `economy_ledgers` (transaction history for audit/economy balance). Schema normalized (3NF), indexed on hot paths (ship lookups by user, sector spatial queries, planet owner scans). |
| **Hot State / Pubsub** | **Redis 7+** | Replaces in-memory BBS state. Use cases: **presence** (which users online, last-seen timestamps), **sector interest sets** (which clients subscribed to sector X,Y for WebSocket fan-out), **tick fan-out** (publish ship/planet delta events to interested WebSocket connections), **rate limits** (per-user command throttling: 10 cmds/sec to prevent spam), **short-lived combat locks** (mutex for ship damage updates during tick resolution to prevent race conditions in async environment). Ephemeral state only; on Redis failure, degrade gracefully (disable realtime updates, fall back to polling). |
| **World Simulation** | **`ge-sim` service** (Python asyncio, same monorepo) | Dedicated long-running process (separate container/systemd unit from API). Owns the authoritative tick schedulers: **6s ship tick** (process all active ships: apply movement physics, resolve combat damage, recharge shields/energy, track torpedo/missile positions, check mine proximity, kill ships at 100% damage) and **55s planet tick** (process all owned planets: run production multipliers, collect taxes, check spy discovery/intel, update population growth). Reads ship/planet state from Postgres, writes updated state back to Postgres (transactionally), publishes delta events to Redis (e.g., `sector:5:7:ship_moved`, `planet:42:production_ready`) → API WebSocket handlers consume from Redis and fan-out to subscribed clients. **Kills the single-threaded BBS `rtkick()` model:** `ge-sim` uses `asyncio.create_task()` for concurrent tick processing (all ships processed in parallel task pool, bounded concurrency), async Postgres driver (asyncpg), async Redis (aioredis). No polling; event-driven via `asyncio` schedulers (`call_later`, `create_task` loops). |
| **Matchmaking / Sharding** | **Phase 1:** None (single shared galaxy) | **Spatial interest management:** Clients subscribe to specific sectors (WebSocket `SUBSCRIBE sector:X:Y` message). API tracks subscriptions in Redis set `sector:X:Y:clients`. When `ge-sim` publishes ship movement in sector 5,7, API looks up `sector:5:7:clients` and pushes delta to those WebSocket connections only. **No instanced matchmaking** (GE is open-world sandbox, not lobby-based FPS). **No galaxy sharding** in Phase 1 (single Postgres + single `ge-sim` instance sufficient for 1,000–5,000 concurrent users). **Phase 2+ (future):** If player count exceeds single-galaxy capacity (~10,000 users), introduce **galaxy sharding** behind a gateway service (each galaxy = independent Postgres + `ge-sim` pair; players assigned to galaxy on signup; cross-galaxy raids/trade via async message queues). "Matchmaking" in GE context = **fleet engagement resolution** (which ships in same sector can fire on each other) and **sector interest management**, NOT FPS-style lobby matchmaking. |
| **Object/Asset CDN** | Cloud storage + CDN (Cloudflare R2 or AWS S3 + CloudFront) | **Unity Addressables:** Ship models, planet textures, UI atlases, cosmetic skins (Phase 2+). Static assets uploaded to S3/R2, served via CDN. Unity client fetches asset bundles on demand (catalog URL in API config response). **Not part of core game logic** (assets are presentational; server is authoritative for game state). Note only in this ADR; implementation deferred. |
| **Deployment** | **Fly.io** (or **Railway** fallback) for compute | Docker images for `api` (FastAPI + WebSocket handlers) and `ge-sim` (world tick services). Fly.io Machines (ephemeral, scale-to-zero capable, but run persistent for Phase 1). **Neon** (or **Supabase Postgres**) for managed Postgres (serverless Postgres with connection pooling). **Upstash Redis** for managed Redis (serverless, pay-per-request, global replication optional). **GitHub Actions** for CI (lint/test on PR, build Docker images on merge, deploy to Fly.io via `flyctl deploy`). Secrets via platform-native secret stores (Fly.io secrets, Neon connection strings, Firebase service account JSON). |
| **Observability** | Structured logs (JSON to stdout) + OpenTelemetry traces + Sentry errors | **Logs:** FastAPI access logs + application logs (Python `logging` with structlog) → Fly.io log aggregation (or forward to Grafana Cloud Loki). **Traces:** OpenTelemetry SDK in FastAPI (auto-instrument HTTP, Postgres, Redis) → export to Honeycomb or Grafana Tempo. **Errors:** Sentry SDK for Python (captures exceptions, attaches user context) → Sentry.io dashboard. **Metrics:** Prometheus `/metrics` endpoint (request latency, WebSocket connection count, tick duration, Postgres query time) → Grafana dashboards. |

### 2.1 Stack Rationale

**Why this stack wins for strategic (not twitch) live MMO:**

1. **FastAPI lock-in constraint:** FastAPI is project requirement. Choosing Nakama (Heroic, Lua/Go) or Supabase Realtime (Postgres triggers + Elixir) would fragment the stack (dual codebases: FastAPI for game logic, Nakama for realtime). Our stack keeps **one unified Python codebase** (FastAPI for API, asyncio for `ge-sim`) with shared models, utilities, and testing.

2. **Strategic cadence (6s/55s) ≠ realtime action (16ms frame sync):** Unity Netcode for GameObjects, Photon, Mirror, etc. optimize for **client-side prediction + rollback** for twitch FPS/fighting games (sub-100ms input → state replication). GE's 6s combat tick is **server-authoritative, turn-based resolution** (client sends command → server queues → resolves at tick boundary → pushes result). WebSockets provide sufficient latency (~50-200ms RTT) for "action queued" acknowledgment; no need for UDP, client-side prediction, or lag compensation. Heavyweight realtime engines are overkill (and costly: Photon PUN charges per CCU).

3. **Conquest/economy simulation >> realtime physics:** GE core loop is **planetary production (55s tick), fleet movement (6s tick), combat damage formulas (inverse-square falloff, shield absorption), trade transactions (instant)**, not rigid-body physics, character animation, or complex AI pathfinding. PostgreSQL + Redis + Python asyncio is **sufficient and cost-effective** for this workload. No need for Unreal Dedicated Server, Unity Game Server Hosting, or Kubernetes StatefulSets (yet).

4. **Firebase Auth:** Industry-standard mobile identity (Sign in with Apple required for iOS App Store, Google Sign-In for Android). Integrates seamlessly with Unity (Firebase Unity SDK). FastAPI validation via Firebase Admin SDK is trivial (10 lines of code). Avoids reinventing auth (password hashing, OAuth flows, account recovery).

5. **Postgres + Redis:** Battle-tested, horizontally scalable (Postgres read replicas, Redis Cluster), rich ecosystem (asyncpg for async Python, Redis pubsub for fan-out). Replaces Btrieve with ACID transactions (prevent double-spend exploits, ensure kill credit atomicity).

6. **Monorepo Python (FastAPI + ge-sim):** Shared data models (Pydantic schemas for `Ship`, `Planet`, `User`), shared business logic (damage formulas, production multipliers), single deployment pipeline (one Docker image with multiple entrypoints: `CMD ["uvicorn", "api.main:app"]` vs. `CMD ["python", "ge_sim/main.py"]`). Easier to refactor (move function from API to sim) than multi-language microservices.

7. **Fly.io / Railway:** Developer-friendly PaaS (simpler than AWS ECS/EKS, cheaper than Heroku for this scale). Fly.io Machines support **global distribution** (deploy API to 10+ regions, route clients to nearest edge, single Postgres primary in us-east with read replicas). Railway is fallback if Fly.io pricing/limits hit.

---

## 3. Alternatives Considered

We evaluated three alternative architectures before selecting the unified FastAPI + asyncio stack. Each alternative was **rejected** due to stack fragmentation, cost, or feature mismatch with GE's strategic cadence.

### 3.1 Alternative A: Nakama (Heroic) as Realtime/Match Core + FastAPI as Thin Game API

**Architecture:**
- **Nakama Open Source** (self-hosted, Go + Lua) as primary realtime orchestrator: manages player sessions, matchmaking (unused for GE), leaderboards, storage (Postgres or CockroachDB), realtime multiplayer (WebSocket + protobuf).
- **FastAPI** as thin wrapper: handles authentication (Firebase → Nakama session token exchange), external economy API (payment processing, analytics), administrative tools (ban users, reset scores).
- **Game logic split:** Ship combat, movement, planet production implemented as **Nakama Lua runtime modules** (server-side Lua functions called via RPC). FastAPI calls Nakama HTTP API for player data.

**Pros:**
- Nakama is **purpose-built for multiplayer games:** out-of-the-box leaderboards (GE scoreboard), storage (ships/planets as Nakama collections), presence (who's online), realtime (WebSocket built-in), matchmaking (unused but available).
- **Mature:** Used in production games (Heroic Labs portfolio). Scales to 100k CCU with cluster mode.
- **Reduces custom realtime code:** No need to build WebSocket subscription management (Nakama match join/leave).

**Cons (why rejected):**
1. **Stack fragmentation:** Game logic in Lua (Nakama runtime) + API logic in Python (FastAPI) = **two codebases**. Shared business logic (damage formulas, production multipliers) must be duplicated or communicated via RPC (slow, error-prone). Refactoring (e.g., move combat from Nakama to FastAPI) requires rewriting Lua → Python.
2. **Matchmaking mismatch:** Nakama matchmaking is **lobby-based** (players queue → matched into 2-16 player instances → match ends). GE is **open-world sandbox** (one persistent galaxy, no lobbies). Nakama's "match" concept doesn't map to GE's "sector" (sectors are permanent spatial regions, not ephemeral lobbies). We'd have to abuse Nakama's relayed multiplayer as a dumb pubsub bus (wasteful).
3. **Lua runtime limits:** Nakama Lua runtime has **CPU quotas per module execution** (prevents one module from monopolizing server). GE's 6s ship tick must process **all active ships** (potentially 1,000 ships) in one batch. Splitting into 1,000 Lua RPC calls hits quota limits and adds latency. Python asyncio task pool is cleaner.
4. **Operational complexity:** Nakama requires CockroachDB cluster (or Postgres) + Nakama cluster (3+ nodes for HA) + FastAPI cluster = **three services** to manage. Our stack is **two services** (FastAPI + `ge-sim`).
5. **Cost:** Heroic Cloud (managed Nakama) charges per MAU (monthly active user). Expensive at scale. Self-hosted Nakama adds ops burden (Go binary + Lua runtime + DB). Our stack uses commodity PaaS (Fly.io + Neon) with transparent pricing.

**Verdict:** Nakama is excellent for lobby-based action games (FPS, MOBA, racing). GE's strategic sandbox doesn't benefit from its matchmaking, and Lua runtime splits the codebase. **Rejected.**

---

### 3.2 Alternative B: Supabase Realtime + Postgres as Primary Realtime Bus + FastAPI Game Logic

**Architecture:**
- **Supabase** (hosted Postgres + Realtime) as primary data layer: ships, planets, users stored in Supabase Postgres tables. **Supabase Realtime** (Elixir Phoenix Channels) listens to Postgres WAL (write-ahead log) → broadcasts INSERT/UPDATE/DELETE events to subscribed WebSocket clients (Unity clients subscribe to `ships` table filtered by `sector_x = 5 AND sector_y = 7`).
- **FastAPI** as game logic server: REST endpoints for commands (move, fire, buy, sell). FastAPI writes to Supabase Postgres (via HTTP API or `psycopg`). Postgres triggers + Supabase Realtime automatically push updates to Unity clients.
- **World simulation:** FastAPI cron jobs (or separate Python worker) run tick logic every 6s/55s, batch-update Postgres rows → Realtime broadcasts changes.

**Pros:**
- **Zero custom WebSocket code:** Supabase Realtime handles subscription management, authentication (Postgres RLS policies), broadcasting. Unity client uses Supabase Unity SDK (community-maintained) to subscribe to tables.
- **Postgres as single source of truth:** No Redis (simpler architecture). All state in Postgres, realtime derived from WAL.
- **Generous free tier:** Supabase free tier includes 500MB DB, 2GB bandwidth, Realtime for up to 200 concurrent connections. Good for MVP/demo.

**Cons (why rejected):**
1. **Realtime is **table-level broadcast**, not game-event-level:** Supabase Realtime sends **entire row** on UPDATE (e.g., `ships` row is 500+ bytes: position, heading, speed, damage, energy, 14 items array, torpedoes array, etc.). If ship moves (X, Y change), Unity client receives full row (490 bytes wasted). GE needs **delta updates** (e.g., `{"ship_id": 42, "x": 5.2, "y": 7.8, "speed": 3.5}` = 50 bytes). Bandwidth explodes at 1,000 ships moving every 6s (1,000 rows × 500 bytes × 10 updates/min = 5 MB/min per client = 300 MB/hour). Mobile data cap exceeded in 3 hours.
2. **No control over broadcast logic:** Supabase Realtime broadcasts **every Postgres write**. If FastAPI updates ship energy (recharge tick) and position (movement tick) in two separate UPDATEs, client receives **two full rows**. Can't batch deltas. Can't prioritize (critical: torpedo hit, low-priority: energy +1%). Dumb pipe.
3. **Postgres RLS (Row-Level Security) for authorization, not spatial filtering:** RLS policies enforce "user can read own ships" (good), but **cannot efficiently filter by spatial interest** (e.g., "send updates only for ships in sectors 5,7 and 6,7 where client is present"). RLS is row-ownership, not pubsub topic routing. Redis sets (`sector:5:7:clients`) are cleaner for interest management.
4. **Tick resolution coupling:** FastAPI cron job updates 1,000 ships in Postgres → 1,000 WAL events → Supabase Realtime broadcasts 1,000 messages to **all subscribed clients** (even if client only cares about 5 ships in their sector). Redis pubsub lets `ge-sim` publish to **specific sector channels** (fan-out only to interested clients).
5. **Supabase Realtime scale limits:** Free tier = 200 concurrent connections, Pro tier ($25/mo) = 500 concurrent. Beyond that, must self-host Realtime (Elixir Phoenix) + manage Postgres replication. Our Redis + FastAPI WebSocket stack scales horizontally (add API nodes, share Redis).
6. **FastAPI as cron runner is awkward:** FastAPI is ASGI web framework (request/response, WebSocket). Running background tick loops in FastAPI (via `@app.on_event("startup")` + `asyncio.create_task`) works but is hacky (no supervision, no graceful shutdown of ticks on deploy). Dedicated `ge-sim` service is cleaner (systemd supervision, independent scaling: scale API for client load, scale `ge-sim` for world complexity).

**Verdict:** Supabase Realtime is brilliant for **admin dashboards** (show live DB rows) and **simple chat apps** (messages table → broadcast new messages). It's a **blunt instrument** for game state synchronization (wasteful full-row broadcasts, no delta compression, no spatial routing). **Rejected.**

---

### 3.3 Alternative C: Unity Netcode for GameObjects + Dedicated Unity Relay (Overkill for Strategic Cadence)

**Architecture:**
- **Unity Netcode for GameObjects (NGO)** as client-server netcode layer: authoritative server (Unity Dedicated Server build), clients (Unity iOS/Android) connect via **Unity Relay** (managed relay service, NAT traversal).
- **Server:** Headless Unity build (Linux) runs on Fly.io or Unity Game Server Hosting (Multiplay). Hosts `NetworkObject`s for ships, planets. Clients connect, spawn player ship, send `NetworkVariable` / `ServerRpc` commands (move, fire, buy). Server runs game logic in Unity C# (`FixedUpdate` at 6s intervals for tick), replicates state to clients via `NetworkVariable` sync.
- **FastAPI (optional):** Thin auth/matchmaking layer (create lobby, assign players to Unity Relay code). Game logic entirely in Unity C#.

**Pros:**
- **Unity-native:** One language (C#), one engine (Unity) for client and server. Shared codebase (ship physics, combat formulas). No Python.
- **Netcode for GameObjects:** Optimized for Unity (automatic `NetworkVariable` serialization, `ClientNetworkTransform` for position sync, `ServerRpc` for commands). Easier than raw WebSockets for Unity devs.
- **Unity Relay:** Handles NAT traversal, relay infrastructure (no self-hosted relay server). Pay-per-GB (first 1GB free, $0.49/GB after).

**Cons (why rejected):**
1. **Massive overkill for strategic (non-twitch) gameplay:** Unity NGO optimizes for **high-frequency state sync** (30-60 Hz tick rate, client-side prediction + reconciliation for movement, rollback for lag compensation). GE's **6s combat tick** means server sends updates **0.16 Hz** (once per 6 seconds). NGO's prediction/reconciliation is wasted overhead. GE clients can **interpolate** between server ticks (smooth animation of ship movement over 6s) without prediction (no rollback needed; strategic gameplay = player accepts 6s resolution delay).
2. **Unity Dedicated Server is **heavyweight:** Linux Unity headless build (~500 MB Docker image, 1-2 GB RAM per instance, CPU-bound for Unity engine overhead even if game logic is light). FastAPI + `ge-sim` (Python asyncio) is **50-100 MB Docker image, 256 MB RAM per instance** (10x lighter). GE server is **data processing** (update 1,000 ship positions per tick, query Postgres), not **physics simulation** (Unity's strength). Python + Postgres is faster and cheaper.
3. **No persistent MMO infrastructure:** Unity NGO + Relay is designed for **session-based matches** (lobby → play → lobby). GE is **persistent world** (24/7 galaxy, players drop in/out). Unity Relay sessions expire after inactivity. We'd need custom "eternal lobby" pattern (abuse Relay as permanent tunnel). Awkward.
4. **Database access from Unity C#:** Unity server must query Postgres for ship/planet state. C# Postgres libraries (Npgsql) exist but are **synchronous** (block Unity main thread) or require custom async wrappers. Python asyncpg is mature (10+ years). Unity → Postgres is friction. Unity → FastAPI → Postgres is worse (two hops).
5. **Operational cost:** Unity Game Server Hosting (Multiplay) charges **per-core-hour** ($0.10-0.50/hour depending on region). 1 dedicated server at 0.16 Hz tick (idle 99% of the time) costs $72-360/month. Fly.io shared-CPU instance ($5/month) can run `ge-sim` at 6s ticks for 1,000 ships. 10-70x cheaper.
6. **Unity Relay bandwidth cost:** Every ship position update (1,000 ships × 50 bytes × 10 updates/min × 60 min × 24 hours = 720 MB/day per client) goes through Unity Relay ($0.49/GB after 1GB free). 1,000 concurrent users = 700 GB/day = $343/day = $10,000/month. Our WebSocket stack (Fly.io bandwidth free, client pays mobile data) is zero relay cost.
7. **FastAPI constraint violated:** Project requires FastAPI backend. Unity Dedicated Server would replace FastAPI (game logic in C#, not Python). Stack fragmentation: Unity C# (game) + FastAPI (auth/admin) + Postgres (data). Rejected per requirements.

**Verdict:** Unity NGO + Relay is **world-class for realtime action games** (FPS, racing, fighting). GE's strategic cadence (6s ticks) doesn't leverage its strengths, and operational cost is prohibitive. Python asyncio is **10x cheaper and simpler** for turn-based simulation. **Rejected.**

---

### 3.4 Comparison Summary Table

| Criterion | **Chosen: FastAPI + asyncio + Redis** | Alternative A: Nakama + FastAPI | Alternative B: Supabase Realtime | Alternative C: Unity NGO + Relay |
|-----------|----------------------------------------|----------------------------------|-----------------------------------|-----------------------------------|
| **Stack unification** | ✅ One Python codebase (FastAPI + ge-sim) | ❌ Lua (Nakama) + Python (FastAPI) | ⚠️ Python (FastAPI) + Elixir (Realtime) | ❌ C# (Unity server) + Python (FastAPI) |
| **Strategic cadence fit (6s ticks)** | ✅ Event-driven, delta updates | ⚠️ Lua RPC per tick (quota limits) | ❌ Full-row broadcasts (wasteful) | ❌ Overkill (60 Hz → 0.16 Hz waste) |
| **Open-world sandbox (no lobbies)** | ✅ Persistent galaxy, sector interest | ⚠️ Abuse match system for sectors | ✅ Persistent Postgres | ❌ Session-based (Relay expires) |
| **Realtime delta efficiency** | ✅ Custom WebSocket (send only deltas) | ⚠️ Nakama protobuf (efficient but Lua RPC overhead) | ❌ Full Postgres rows (500 bytes/ship) | ⚠️ NetworkVariable (efficient but Unity overhead) |
| **Operational cost (1,000 CCU)** | ✅ $50-100/mo (Fly.io + Neon + Upstash) | ⚠️ $200-500/mo (Heroic Cloud or self-host) | ⚠️ $150-300/mo (Supabase Pro + overages) | ❌ $5,000-10,000/mo (Multiplay + Relay bandwidth) |
| **Database integration** | ✅ Native asyncpg (Python ↔ Postgres) | ⚠️ Postgres via Nakama API or direct | ✅ Native Supabase Postgres | ❌ C# Npgsql (sync-only or async pain) |
| **Scalability** | ✅ Horizontal (add API nodes, Redis Cluster) | ✅ Horizontal (Nakama cluster) | ⚠️ Vertical (Postgres + Realtime hard to shard) | ❌ Vertical (Unity server = stateful, hard to scale) |
| **Developer velocity** | ✅ Fast (one language, shared models) | ❌ Slow (Lua ↔ Python context switch) | ⚠️ Medium (Postgres schema = API contract) | ⚠️ Medium (Unity build slow, testing awkward) |
| **Meets FastAPI constraint** | ✅ FastAPI is primary API | ⚠️ FastAPI is thin wrapper (core in Lua) | ✅ FastAPI is game logic | ❌ FastAPI optional (core in Unity C#) |

**Conclusion:** The chosen stack (FastAPI + asyncio + Redis) is **uniquely optimized** for GE's strategic MMO requirements: unified Python codebase, efficient delta updates, persistent open-world, low operational cost, and native Postgres integration. Alternatives split the stack (Lua, Elixir, C#), waste bandwidth (full-row broadcasts, relay overhead), or cost 10-100x more (Nakama, Unity Relay).

---

## 4. Architecture Overview

### 4.1 System Components

```mermaid
graph TB
    subgraph "Mobile Clients (Unity)"
        UC[Unity iOS/Android<br/>Firebase SDK<br/>REST + WebSocket]
    end
    
    subgraph "Edge (Fly.io)"
        API[FastAPI API<br/>REST endpoints<br/>WebSocket handlers<br/>JWT validation]
    end
    
    subgraph "World Simulation"
        SIM[ge-sim Service<br/>6s ship tick<br/>55s planet tick<br/>Async task pool]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Authoritative state<br/>ships, planets, users)]
        REDIS[(Redis<br/>Presence, interest sets<br/>Pubsub, rate limits)]
    end
    
    subgraph "Auth"
        FB[Firebase Auth<br/>Apple + Google sign-in]
    end
    
    subgraph "Push Notifications"
        FCM[Firebase Cloud Messaging<br/>APNs relay]
    end
    
    UC -->|1. Sign in| FB
    FB -->|2. ID token| UC
    UC -->|3. POST /auth/exchange<br/>Firebase token| API
    API -->|4. Verify token| FB
    API -->|5. Return JWT| UC
    
    UC -->|6. REST commands<br/>Authorization: Bearer JWT| API
    UC -->|7. WebSocket subscribe<br/>sector:X:Y| API
    
    API -->|8. Read/Write| PG
    API -->|9. Publish events| REDIS
    API -->|10. Track interest sets| REDIS
    
    SIM -->|11. Read state| PG
    SIM -->|12. Write deltas| PG
    SIM -->|13. Publish events<br/>sector:X:Y:*| REDIS
    
    API -->|14. Subscribe to Redis channels| REDIS
    API -->|15. Fan-out to WebSocket clients| UC
    
    API -->|16. Send push via Firebase Admin SDK| FCM
    FCM -->|17. Deliver notification| UC
    
    style UC fill:#e1f5ff
    style API fill:#fff4e1
    style SIM fill:#ffe1f5
    style PG fill:#e1ffe1
    style REDIS fill:#ffe1e1
    style FB fill:#f5e1ff
    style FCM fill:#f5e1ff
```

### 4.2 Data Flow Examples

#### Example 1: Player Fires Phasor

```mermaid
sequenceDiagram
    participant U as Unity Client
    participant A as FastAPI
    participant R as Redis
    participant P as Postgres
    participant S as ge-sim
    participant U2 as Other Clients<br/>(subscribed to sector)
    
    U->>A: POST /ships/{id}/fire_phasor<br/>{target_id: 99, focus: 50}
    A->>P: BEGIN; SELECT ship, target FOR UPDATE
    A->>P: Validate: range, energy, lock status
    A->>P: INSERT INTO combat_queue (ship, target, weapon, focus)
    A->>P: COMMIT
    A->>U: 202 Accepted {action_id: "abc123", eta: "6s"}
    
    Note over S: 6s ship tick fires
    S->>P: SELECT * FROM combat_queue
    S->>S: Calculate damage (pdamage formula)
    S->>P: BEGIN; UPDATE ships SET damage=damage+50, energy=energy-500<br/>WHERE id=99
    S->>P: DELETE FROM combat_queue WHERE action_id='abc123'
    S->>P: COMMIT
    S->>R: PUBLISH sector:5:7:combat {ship: 42, target: 99, damage: 50}
    
    A->>R: SUBSCRIBE sector:5:7:*
    R->>A: Message: combat event
    A->>U2: WebSocket push: {type: "combat", ship: 42, target: 99, damage: 50}
    A->>U: WebSocket push: {type: "action_resolved", action_id: "abc123", result: "hit"}
```

**Key points:**
- Command is **queued** (Postgres `combat_queue` table), not executed immediately. Client receives `202 Accepted` instantly (no 6s blocking wait).
- `ge-sim` processes queue at next 6s tick boundary (server-authoritative resolution).
- Redis pubsub fans out result to **interested clients only** (those subscribed to sector 5,7).
- Original client receives `action_resolved` event (close-loop feedback: "your phasor hit").

#### Example 2: Planet Production Tick (55s)

```mermaid
sequenceDiagram
    participant S as ge-sim
    participant P as Postgres
    participant R as Redis
    participant A as FastAPI
    participant U as Unity Client<br/>(owns planet 42)
    participant F as Firebase Cloud Messaging
    
    Note over S: 55s planet tick fires
    S->>P: SELECT * FROM planets WHERE owner IS NOT NULL
    loop For each owned planet
        S->>S: Run multiply() formula:<br/>qty += rate × env × resource × tech
        S->>P: UPDATE planets SET items[0].qty = items[0].qty + 100<br/>WHERE id = 42
        S->>P: UPDATE planets SET tax = tax + (population × taxrate / 100)
        S->>P: Check spy discovery (RNG)
    end
    S->>P: COMMIT
    S->>R: PUBLISH planet:42:production {planet: 42, item: "men", qty_delta: +100}
    
    A->>R: SUBSCRIBE planet:42:*
    R->>A: Message: production event
    A->>U: WebSocket push (if client online):<br/>{type: "production", planet: 42, deltas: [{item: "men", qty: 100}]}
    
    alt Client offline
        A->>P: SELECT users.push_token WHERE user_id = (SELECT owner FROM planets WHERE id=42)
        A->>F: Send push notification via Firebase Admin SDK:<br/>"Planet Alpha produced 100 Men. Tax collected: 500 gold."
        F->>U: Deliver APNs/FCM notification
    end
```

**Key points:**
- `ge-sim` batch-processes all planets in one tick (async task pool: 100 planets in parallel).
- Publishes granular deltas to Redis (e.g., `planet:42:production`), not full planet state.
- FastAPI checks if client is online (active WebSocket). If yes, push via WebSocket. If no, send Firebase push notification (offline alert).
- Unity client wakes on notification tap → reconnects WebSocket → fetches full planet state via REST `GET /planets/42`.

#### Example 3: Sector Interest Management (Spatial Filtering)

```mermaid
sequenceDiagram
    participant U as Unity Client
    participant A as FastAPI
    participant R as Redis
    participant S as ge-sim
    
    U->>A: WebSocket SUBSCRIBE {type: "sector", x: 5, y: 7}
    A->>R: SADD sector:5:7:clients {client_id: "uuid-1234"}
    A->>U: ACK {subscribed: "sector:5:7"}
    
    Note over U: Client moves ship from sector 5,7 to 5,8
    U->>A: POST /ships/{id}/impulse {target_sector: {x:5, y:8}}
    A->>R: SREM sector:5:7:clients {client_id: "uuid-1234"}
    A->>R: SADD sector:5:8:clients {client_id: "uuid-1234"}
    
    Note over S: 6s ship tick: ship crosses sector boundary
    S->>R: PUBLISH sector:5:7:ship_left {ship: 42}
    S->>R: PUBLISH sector:5:8:ship_entered {ship: 42, x: 5.1, y: 8.0}
    
    A->>R: SMEMBERS sector:5:8:clients
    R->>A: ["uuid-1234", "uuid-5678"]
    A->>U: WebSocket push: {type: "ship_entered", ship: 42, x: 5.1, y: 8.0}
```

**Key points:**
- Clients explicitly subscribe to sectors (not global feed). Redis `SADD` tracks which clients care about sector 5,7.
- When ship moves (sector boundary crossing), `ge-sim` publishes to **both** old sector (`ship_left`) and new sector (`ship_entered`).
- FastAPI looks up `SMEMBERS sector:5:8:clients` and pushes event **only to those 2 clients**, not all 1,000 online users (bandwidth optimization).

---

## 5. Mapping Legacy → Modern

This section documents how the chosen stack **replaces** BBS-era assumptions (ticks, Btrieve, single-thread, offline vulnerability) from [Phase 1a](./PHASE1A_LEGACY_SYSTEM_MAP.md).

| Legacy System (MajorBBS) | Modern System (FastAPI + asyncio) | Rationale |
|--------------------------|-------------------------------------|-----------|
| **Btrieve `.dat` files** (512-byte fixed records, record-level locks) | **PostgreSQL** (relational tables, ACID transactions, row-level locks via `SELECT ... FOR UPDATE`) | Postgres provides: 1) **Normalization** (separate tables for ships, planets, users; join queries), 2) **Indexes** (B-tree on `user_id`, spatial index on `sector_x, sector_y`), 3) **Transactions** (atomicity for double-spend prevention: deduct cash + add items in one COMMIT), 4) **JSON columns** (flexible item arrays, no fixed 14-slot limit), 5) **Replication** (read replicas for scaling read-heavy queries like leaderboards). Btrieve is flat files (no joins, no complex queries, fragile to corruption). |
| **Single-threaded BBS event loop** (`rtkick()` polls tick handlers sequentially) | **Asyncio task pool** in `ge-sim` (concurrent tick processing: 1,000 ships processed in parallel via `asyncio.gather([process_ship(s) for s in ships])`) | Python `asyncio` allows **concurrent I/O** (Postgres queries, Redis publishes) without threads (GIL-free). One `ge-sim` process can handle 1,000–10,000 ships per tick (CPU-bound: damage calculations, RNG) on 2-4 cores (parallel via `ProcessPoolExecutor` if needed). No single-thread bottleneck. Legacy: 8-32 BBS lines × 1 ship/line = max 32 concurrent players. Modern: 1,000–10,000 CCU. |
| **Tick polling** (`TICKTIME=6s`, `PLANTIME=55s`: MajorBBS scheduler calls `warrti()`, `plarti()` on wall-clock intervals) | **Event-driven schedulers** (`asyncio.call_later(6.0, ship_tick)`, recursively reschedules after each tick completes) | No busy-wait polling. `ge-sim` uses `asyncio` timers (precision: ~10ms jitter, acceptable for 6s cadence). Tick skipping handled gracefully (if tick takes 7s to process 1,000 ships, next tick starts immediately, no drift). Metrics track tick duration (alert if exceeds 5s = approaching overload). Legacy: if tick exceeds `TICKTIME`, BBS blocks (input lag for all users). Modern: ticks run in background; API remains responsive (separate process). |
| **Blocking commands** (BBS session: `input() → parse → execute → output → input()`) | **Async REST + WebSocket** (client: `POST /command → 202 Accepted → WebSocket push on resolution`) | Client submits command, gets instant acknowledgment (`{"status": "queued", "eta": "6s"}`), continues interacting with UI (rotate ship, scan sector, chat). Server resolves at tick boundary, pushes result. **No blocking wait.** Legacy: player types `pha 42 50`, waits 6s for next tick, sees damage. Modern: player taps "Fire Phasor" button, sees "Phasor charging…" animation (6s countdown), receives "Hit for 50 damage" notification, animation plays impact. Feels responsive despite same 6s resolution. |
| **Offline vulnerability** (ship remains in world, cyborgs attack, player loses 50% cargo on death) | **Same** (ship persists in Postgres, `ge-sim` ticks continue, NPC AI can kill offline ships). **Infrastructure adds push notifications** (Firebase FCM/APNs) to alert player "Your ship Avenger is under attack in sector 5,7!" + deep link to open app. | **Design decision deferred:** Phase 1b (this ADR) provides **infrastructure** (push notifications, offline state tracking). **Game design** (Phase 2+) decides **policy**: Do offline ships get immunity shield? Must player "dock at citadel" before logout for safety? Do NPC patrols guard offline ships (hire mechanic)? This ADR enables **any** policy (push + deep link lets player respond to attacks; Redis tracks "last_seen" timestamp for "offline since" queries; Postgres `ships.offline_shield_expires_at` column reserves schema space). Legacy had **no choice** (offline = vulnerable, accept it). Modern infrastructure enables **choice** (can implement safe logout if game design demands). Current **Phase 1 stance:** Preserve hardcore offline vulnerability (GE's identity), but alert player via push (give them a chance to log in and flee). |
| **BBS line limits** (30 dial-in modems = max 30 concurrent sessions) | **WebSocket scale** (Fly.io: 10,000 concurrent WebSocket connections per 1GB RAM API instance; horizontal scaling: add instances behind load balancer; Redis pubsub fans out to all API instances → each pushes to its subset of clients) | One FastAPI instance (512 MB RAM) handles ~5,000 WebSockets (100 KB overhead per connection: subscription state, auth context). 10 API instances (5 GB total RAM) = 50,000 CCU. Redis Cluster pubsub (10 shards) handles 1M messages/sec (GE: 1,000 ships × 10 updates/min = 10K messages/min = 166/sec, 0.02% of Redis capacity). No hard limit (add instances as CCU grows). Cost: Fly.io shared-CPU $5/instance/month = $50/month for 50,000 CCU (assuming 1% CCU at peak, 500 peak = 1 instance). Legacy: 30 CCU max (hardware bottleneck: 30 modems). |
| **Btrieve record locks** (single-writer per record: `obtbtv()` locks ship row, other sessions block until release) | **Postgres row locks** (`BEGIN; SELECT ships WHERE id=42 FOR UPDATE; UPDATE ships SET damage=50; COMMIT;`) + **Redis locks for hot paths** (`SETNX ship:42:combat_lock 1 EX 1` = 1-second expiring mutex for tick resolution) | Postgres `FOR UPDATE` prevents concurrent damage updates (race: two phasors hit same ship, both read damage=50, both write damage=100 → correct is damage=150). Redis `SETNX` (set-if-not-exists) is lightweight mutex for **tick resolution only** (ship damage updates during 6s tick must serialize; commands queue into `combat_queue` table without locking ship row → avoids contention on hot ships). Legacy: Btrieve locks serialize all operations (reading ship blocks writer). Modern: Postgres MVCC allows concurrent reads + single writer (fast). Redis locks are opt-in (use for critical sections: damage, loot, kill credit). |
| **Mail system** (`GEmail.dat`: async notifications for attack alerts, production reports, spy intel) | **Postgres `mail` table** + **Firebase push notifications** (FCM/APNs) for offline alerts + **WebSocket push** for online alerts + **in-app inbox** (Unity UI fetches `GET /mail` on login) | Legacy: mail stored in Btrieve, read via separate BBS mail interface (external to GE module). Modern: 1) **Postgres mail table** (columns: `user_id`, `category` [attack, production, spy], `subject`, `body_json` [parameterized: `{attacker: "Zorg", ship: "Avenger", sector: {x:5, y:7}}`], `read_at` timestamp). 2) **Push notifications** (if user offline: `ge-sim` or API writes mail row → triggers Postgres `NOTIFY` → FastAPI listener calls Firebase Admin SDK `send(token, notification)` → Unity app wakes). 3) **WebSocket push** (if user online: API checks Redis `SISMEMBER online_users {user_id}` → sends `{type: "mail", mail_id: 123}` → Unity shows toast). 4) **In-app inbox** (Unity fetches `GET /mail?unread=true` on app open, displays list, marks read via `PATCH /mail/{id}`). Unified UX (no separate BBS mail). |
| **Universe state** (30×15 sectors, 450 total, fixed grid, stored in `GEplanet.dat` sectors + planets) | **Postgres `sectors` table** (columns: `x INT, y INT, type ENUM('normal', 'wormhole'), num_planets INT, wormhole_dest_x INT, wormhole_dest_y INT`) + **`planets` table** (columns: `id SERIAL PRIMARY KEY, sector_x INT, sector_y INT, planet_num INT (0-8), coord_x FLOAT, coord_y FLOAT, owner_id INT REFERENCES users(id), name VARCHAR(20), environment INT, resource INT, treasury BIGINT, tax_rate INT, production_rates JSONB, item_stocks JSONB, spy_owner_id INT, technology INT, team_id INT`) | Normalized schema (separate sectors and planets tables, foreign keys). Postgres spatial queries: `SELECT * FROM ships WHERE sector_x BETWEEN 5-2 AND 5+2 AND sector_y BETWEEN 7-2 AND 7+2` (hyper-scanner range). `JSONB` columns for flexible item arrays (no fixed 14-item limit: can add new items without schema migration). Indexed on `(sector_x, sector_y)` (B-tree for range scans) and `owner_id` (player's planets query). Legacy: Btrieve key=(x, y, plnum) composite key; must iterate all 450 sectors to find "all planets owned by user Zorg" (slow). Modern: `SELECT * FROM planets WHERE owner_id=42` (instant index lookup). |
| **Ship physics** (`moveship()`: `coord += speed * sin/cos(heading)` scaled by `TICKTIME`, wraps at universe boundaries) | **Same formula, ported to Python** in `ge-sim/physics.py`: `ship.x += ship.speed * math.cos(ship.heading_radians) * TICKTIME; if ship.x > UNIVMAX: ship.x -= UNIVMAX` (wrapping) | No change to physics model (preserve GE feel: acceleration costs energy, rotation costs energy, hyperspace disables combat). **Python port** of C formulas. Tested via unit tests (`test_physics.py`: assert ship at x=29.5, speed=1, heading=90° → after 6s tick → x=0.5 due to wrap). Metrics: track tick duration (if physics becomes bottleneck at 10,000 ships, profile and optimize: Cython, NumPy vectorization, or Rust PyO3 module). |
| **Combat damage formulas** (`pdamage()`, `tdamage()`, `attack_men()`: inverse-square falloff, shield absorption, RNG rolls) | **Same formulas, ported to Python** in `ge-sim/combat.py` | No change to game balance (preserve phasor range, torpedo tracking, shield effectiveness, planet conquest odds). **Python port** of C formulas. Example: `damage = base * (1 / (distance ** 2)) * (phasor_type / 2.5) / ton_factor; damage = max(damage, min_damage)`. Unit tests (`test_combat.py`: assert phasor type 5, distance 1000, target 100 tons → damage=X). Formulas are **authoritative on server** (clients cannot spoof damage; `ge-sim` is single source of truth). |
| **Cyborg/Droid AI** (`cyb_lives()`, `droidXlives()`: patrol sectors, target players based on skill, fire weapons, lay mines) | **Same AI logic, ported to Python** in `ge-sim/ai.py`. **Throttling removed** (`CYBMAXPERTICK=2` killed; all NPCs processed per tick). **AI state in Postgres** (cyborg ships are rows in `ships` table with `status='npc_cyborg'`, `npc_skill INT` column). | Legacy: AI throttled to 2 cyborgs/sec to avoid BBS lag (single-threaded). Modern: async task pool processes all NPCs in parallel (100 cyborgs × 10ms AI logic = 1 second total in asyncio pool, acceptable). AI behavior unchanged (skill-based targeting: low-skill cyborgs avoid high-kill players per `CYB_BE_NICE` threshold). NPCs are first-class ships (same schema as player ships; simplifies code: combat resolver doesn't care if attacker is NPC or player). |
| **Midnight reset** (`gemidnight()`: recalculate scores, send production reports, award team bonuses) | **Daily cron job** (FastAPI scheduled task or external cron: `0 0 * * * curl -X POST https://ge-api.fly.dev/admin/daily_reset -H "Authorization: Bearer $ADMIN_TOKEN"`) calls `/admin/daily_reset` endpoint → `ge-sim` pauses ticks, recalculates leaderboard (`UPDATE users SET score = kills*1000 + planets*5000 + cash + production_value`), sends mail, resumes ticks. | Configurable time zone (no hardcoded midnight EST; admin sets reset time in config: `DAILY_RESET_UTC_HOUR=0`). **Leaderboard persistence:** Postgres `leaderboard_snapshots` table (columns: `date DATE, user_id INT, rank INT, score BIGINT`) archives daily top 100 (historical stats). Metrics: track reset duration (must complete <10 seconds to avoid noticeable tick pause; if exceeds, optimize: batch-update queries, parallel score calculations). |

---

## 6. Client Integration (Unity)

This section describes **design-level** integration between Unity 6000.0.10f1 (iOS/Android) and the FastAPI + WebSocket backend. **No C# code files** (out of scope per requirements). This is the **contract** Unity client devs will implement.

### 6.1 Authentication Flow

1. **Unity Firebase SDK**: Player taps "Sign in with Apple" or "Sign in with Google" → Unity calls `Firebase.Auth.FirebaseAuth.DefaultInstance.SignInWithCredentialAsync(credential)` → receives `FirebaseUser` object + `IdToken` (JWT, 1-hour TTL).

2. **Token Exchange**: Unity sends `POST https://ge-api.fly.dev/auth/exchange` with body `{"firebase_token": "<IdToken>"}` → FastAPI validates token via Firebase Admin SDK (`firebase_admin.auth.verify_id_token(token)`) → returns `{"access_token": "<JWT>", "expires_in": 3600, "user_id": 123}`. Unity stores JWT in memory (do NOT persist to disk; refresh on expiry).

3. **Token Refresh**: Unity Firebase SDK auto-refreshes Firebase token (handles token expiry). On 401 Unauthorized from FastAPI (JWT expired), Unity calls `FirebaseUser.GetIdTokenAsync(forceRefresh=true)` → repeats exchange.

4. **Authorization Header**: All REST calls include `Authorization: Bearer <JWT>`. WebSocket initial handshake includes `?token=<JWT>` query param (or first message: `{"type": "auth", "token": "<JWT>"}`).

### 6.2 REST API Endpoints (Partial List)

Unity client calls these HTTPS REST endpoints (design contract; FastAPI implements):

| Endpoint | Method | Purpose | Request Body | Response |
|----------|--------|---------|--------------|----------|
| `/auth/exchange` | POST | Exchange Firebase token for API JWT | `{firebase_token: str}` | `{access_token: str, expires_in: int, user_id: int}` |
| `/users/me` | GET | Fetch current user profile | — | `{user_id, username, cash, kills, planets, team_id, score}` |
| `/ships` | GET | List user's ships | — | `[{ship_id, name, class, sector_x, sector_y, damage, energy, items}]` |
| `/ships/{id}` | GET | Fetch ship detail | — | `{ship_id, x, y, heading, speed, damage, energy, shields, cloak, items, torpedoes_locked_on: [...]}` |
| `/ships/{id}/impulse` | POST | Set impulse drive (target speed/heading) | `{target_speed: float, target_heading: float}` | `{action_id: str, eta: "6s"}` (202 Accepted) |
| `/ships/{id}/fire_phasor` | POST | Fire phasor at target | `{target_ship_id: int, focus_percent: int}` | `{action_id: str, eta: "6s"}` (202 Accepted) |
| `/ships/{id}/dock` | POST | Dock at planet | `{planet_id: int}` | `{status: "docked"}` (200 OK, instant) |
| `/ships/{id}/undock` | POST | Undock from planet | — | `{status: "undocked"}` (200 OK, instant) |
| `/planets` | GET | List user's planets | — | `[{planet_id, name, sector_x, sector_y, treasury, tax_rate, item_stocks}]` |
| `/planets/{id}` | GET | Fetch planet detail | — | `{planet_id, owner_id, name, environment, resource, treasury, production_rates, item_stocks, spy_owner_id}` |
| `/planets/{id}/set_production` | POST | Set production rates | `{rates: {men: 100, food: 50, ...}}` | `{status: "updated"}` (200 OK, instant) |
| `/planets/{id}/trade` | POST | Buy/sell items | `{action: "buy", item: "missiles", qty: 100}` | `{status: "success", new_ship_items, new_planet_stocks, new_cash}` (200 OK, instant, transactional) |
| `/sectors/{x}/{y}` | GET | Scan sector (ships, planets visible to player) | — | `{ships: [{ship_id, name, owner, x, y, heading, cloaked}], planets: [{planet_id, name, owner, x, y}]}` |
| `/mail` | GET | Fetch inbox | `?unread=true` | `[{mail_id, category, subject, body, created_at, read_at}]` |
| `/mail/{id}` | PATCH | Mark mail as read | — | `{status: "read"}` (200 OK) |

**Key patterns:**
- **Instant actions** (docking, trading, setting production rates): Return 200 OK, modify state immediately (Postgres transaction: deduct cash + add items atomically).
- **Queued actions** (fire phasor, launch torpedo, planet attack): Return 202 Accepted with `action_id` + `eta`. Client polls or waits for WebSocket push with `{type: "action_resolved", action_id, result}`.
- **Errors**: 400 Bad Request (validation: insufficient energy, out of range), 401 Unauthorized (JWT expired), 403 Forbidden (action not allowed: target cloaked, ship docked), 404 Not Found (ship/planet doesn't exist), 409 Conflict (ship already docked, planet under attack), 429 Too Many Requests (rate limit: 10 cmds/sec), 500 Internal Server Error (server bug; Sentry alert).

### 6.3 WebSocket Protocol

Unity opens persistent WebSocket connection to `wss://ge-api.fly.dev/ws?token=<JWT>`. Messages are JSON (text frames).

#### Client → Server Messages

| Type | Payload | Purpose |
|------|---------|---------|
| `subscribe` | `{type: "subscribe", channel: "sector", x: 5, y: 7}` | Subscribe to sector updates (ship movements, combat, planet events in sector 5,7) |
| `unsubscribe` | `{type: "unsubscribe", channel: "sector", x: 5, y: 7}` | Unsubscribe from sector |
| `subscribe_fleet` | `{type: "subscribe", channel: "fleet", ship_id: 42}` | Subscribe to specific ship updates (damage, energy, torpedoes locked on this ship) |
| `ping` | `{type: "ping"}` | Keep-alive (client sends every 30s; server responds `{type: "pong"}`) |

#### Server → Client Messages

| Type | Payload | Purpose |
|------|---------|---------|
| `sector_ship_moved` | `{type: "sector_ship_moved", ship_id: 42, x: 5.2, y: 7.8, heading: 90, speed: 3.5}` | Ship moved in subscribed sector (6s tick delta) |
| `sector_ship_entered` | `{type: "sector_ship_entered", ship_id: 99, owner: "Zorg", x: 5.0, y: 7.0, class: 3}` | New ship entered subscribed sector (first appearance) |
| `sector_ship_left` | `{type: "sector_ship_left", ship_id: 99}` | Ship left subscribed sector (crossed boundary or docked) |
| `sector_combat` | `{type: "sector_combat", attacker_id: 42, target_id: 99, weapon: "phasor", damage: 50}` | Combat event in subscribed sector |
| `sector_ship_destroyed` | `{type: "sector_ship_destroyed", ship_id: 99, killer_id: 42, loot: {gold: 5000, items: {...}}}` | Ship destroyed in subscribed sector (death, wreckage) |
| `fleet_damage` | `{type: "fleet_damage", ship_id: 42, damage_delta: 15, total_damage: 65, source: "phasor", attacker_id: 99}` | Ship took damage (subscribed via `subscribe_fleet`) |
| `fleet_energy` | `{type: "fleet_energy", ship_id: 42, energy_delta: -500, total_energy: 12000, reason: "phasor_fire"}` | Ship energy changed |
| `fleet_torpedo_locked` | `{type: "fleet_torpedo_locked", ship_id: 42, torpedo_id: "t123", attacker_id: 99, speed: 5000}` | Torpedo locked onto subscribed ship |
| `planet_production` | `{type: "planet_production", planet_id: 10, item_deltas: {men: +100, food: +50}, tax_collected: 500}` | Planet production tick (55s) |
| `action_resolved` | `{type: "action_resolved", action_id: "abc123", status: "success", result: {damage: 50, target_destroyed: false}}` | Queued action resolved (e.g., phasor fired at tick boundary) |
| `mail` | `{type: "mail", mail_id: 456, category: "attack", subject: "Your ship is under attack!", body: {...}}` | New mail (push if online) |
| `error` | `{type: "error", code: "rate_limit", message: "Too many commands. Wait 10s."}` | Error on subscription or command |
| `pong` | `{type: "pong"}` | Response to ping |

**Design notes:**
- **Delta updates only**: Server sends changed fields (e.g., `damage_delta: +15` not full ship state). Unity client maintains local ship state (received via REST `GET /ships/{id}` on initial load) and applies deltas (`ship.damage += 15`).
- **Sector subscription scope**: Unity subscribes to 1–5 sectors at a time (current sector + adjacent if near boundary for smooth transitions). Unsubscribe from far sectors to reduce bandwidth.
- **Reconnection**: If WebSocket disconnects (network blip, server deploy), Unity reconnects with exponential backoff (1s, 2s, 4s, max 30s). On reconnect, re-subscribe to previous sectors + fleet. Fetch full state via REST (`GET /ships/{id}`) to resync (server may have sent deltas while disconnected; local state is stale).
- **Message ordering**: Within one channel (e.g., `sector:5:7`), messages are ordered (Redis pubsub preserves publish order). Across channels, no ordering guarantee (ship moved in sector 5,7 and planet produced in sector 6,8 may arrive out-of-order; Unity handles independently).

### 6.4 Local Prediction / Interpolation

Unity client implements **client-side interpolation** (not prediction) for smooth animations:

- **Movement**: Server sends ship position every 6s (tick boundary). Unity interpolates between last position and new position over 6s (linear or ease-out curve). Example: Server says ship at (5.0, 7.0) at T=0, then (5.5, 7.2) at T=6. Unity renders smooth movement from (5.0, 7.0) → (5.5, 7.2) over 6 seconds (60 FPS × 6s = 360 frames).

- **Energy recharge**: Server sends `energy_delta: +100` every 6s (recharge tick). Unity interpolates `energy += (100 / 6.0) * deltaTime` per frame (smooth bar fill, not stepwise jump).

- **Combat animations**: On `sector_combat` event, Unity plays phasor beam effect (5-second animation: charge → fire → beam → impact). Animation duration (~5s) fits within 6s tick window (feels instant to player despite server resolving at tick boundary).

**No client-side prediction** (client does NOT move ship locally before server confirms). Why: Strategic cadence (6s) is slow enough that 50-200ms WebSocket RTT is negligible (player perceives instant response). Prediction adds complexity (rollback on server rejection: "you tried to fire phasor but server says insufficient energy → rewind animation"). Not worth it for GE's pacing.

### 6.5 Push Notifications (Offline Alerts)

Unity registers for push notifications via Firebase Cloud Messaging (FCM) SDK:

1. **Registration**: On app launch, Unity calls `Firebase.Messaging.FirebaseMessaging.GetTokenAsync()` → receives FCM registration token (device-specific, ~150-char string).

2. **Token upload**: Unity sends `POST /users/me/push_token` with body `{token: "<FCM_token>", platform: "ios"}` → FastAPI stores in Postgres `users.fcm_token` column.

3. **Token refresh**: FCM token can change (app reinstall, iOS token rotation). Unity listens to `Firebase.Messaging.FirebaseMessaging.TokenReceived` event → uploads new token.

4. **Notification delivery**: When `ge-sim` detects event requiring offline alert (e.g., ship under attack, player offline for >5 minutes), calls `send_push_notification(user_id, title, body, data)` → FastAPI queries `users.fcm_token` → calls Firebase Admin SDK `messaging.send(Message(token=fcm_token, notification=Notification(title, body), data={deep_link: "/ships/42"}))` → Firebase delivers to device via APNs (iOS) or FCM (Android).

5. **Deep link handling**: Notification payload includes `data: {deep_link: "/ships/42"}`. User taps notification → iOS/Android OS opens app → Unity parses deep link → navigates to ship detail view + reconnects WebSocket + fetches ship state (`GET /ships/42`).

**Notification categories** (game design; infrastructure supports):
- **Under attack**: "Your ship Avenger is under attack by Zorg in sector 5,7! [Defend Now]"
- **Ship destroyed**: "Your ship Avenger was destroyed. 50% cargo lost. [Respawn]"
- **Planet attacked**: "Your planet Alpha is under assault! [Defend]"
- **Planet conquered**: "Planet Alpha was conquered by Zorg. Treasury looted: 50,000 gold."
- **Production ready**: "Planet Beta produced 500 Missiles. [Collect]"
- **Spy intel**: "Your spy on planet Gamma reports: 10,000 gold in treasury, 200 fighters."
- **Team message**: "Your team leader issued rally: Attack sector 10,5 at 20:00 UTC."

**Rate limiting**: Max 1 push/user/5min (avoid spam if ship takes 10 hits in 30 seconds). Aggregate: "Your ship took 10 hits (-500 damage total) in the last 5 minutes."

---

## 7. Security & Authentication

### 7.1 Authentication Chain

```
Mobile Device → Firebase Auth (Apple/Google) → Firebase ID Token (JWT) →
Unity Client → FastAPI /auth/exchange → Verify via Firebase Admin SDK →
FastAPI issues short-lived JWT (1 hour TTL) → Client stores in memory →
All API calls include Authorization: Bearer <JWT> → FastAPI validates JWT
```

**Security properties:**
- **User identity from trusted provider**: Firebase Auth is OAuth2 provider (Apple, Google). FastAPI trusts Firebase's identity assertions (no password storage, no account takeover via weak passwords).
- **Short-lived API JWT**: 1-hour TTL limits blast radius if token stolen (attacker has 1 hour to abuse). Refresh handled by Firebase SDK (Unity re-exchanges on expiry).
- **JWT signed by FastAPI secret**: API JWT is signed with `HS256` (HMAC-SHA256) using secret key (stored in Fly.io secrets, rotated quarterly). FastAPI validates signature on every request (stateless; no session DB lookup).
- **Token in memory only**: Unity NEVER persists JWT to disk (PlayerPrefs, file). On app restart, user re-authenticates (Firebase SDK caches Firebase token securely in iOS Keychain / Android Keystore).

### 7.2 Authorization (Row-Level Permissions)

FastAPI enforces **ownership checks** on every mutating operation:

- **Ship commands**: `POST /ships/{id}/fire_phasor` → FastAPI queries `SELECT owner_id FROM ships WHERE id={id}` → asserts `owner_id == jwt.user_id` (403 Forbidden if mismatch).
- **Planet operations**: `POST /planets/{id}/set_production` → assert `planet.owner_id == jwt.user_id`.
- **Trade**: `POST /planets/{id}/trade` → assert `ship.owner_id == jwt.user_id AND (planet.owner_id == jwt.user_id OR planet.password_matches(jwt.user_input))` (allies can dock with password).
- **Admin endpoints**: `/admin/daily_reset`, `/admin/ban_user` → assert `jwt.is_admin == true` (admin flag in Postgres `users.is_admin BOOLEAN`).

**No client-side trust**: Unity client can send malicious requests (`POST /ships/999/fire_phasor` targeting ship 999 owned by rival player Zorg). FastAPI rejects (403 Forbidden). All authority on server.

### 7.3 Rate Limiting

**Redis-based rate limits** (prevent spam, DoS):

- **Commands**: 10 commands/user/second (sliding window: Redis key `ratelimit:user:{user_id}:commands`, `INCR` + `EXPIRE 1`). Exceeding → 429 Too Many Requests (`Retry-After: 1` header).
- **WebSocket messages**: 20 messages/user/second (subscriptions, pings). Exceeding → disconnect WebSocket with `{type: "error", code: "rate_limit"}`.
- **Auth attempts**: 5 `/auth/exchange` calls/IP/minute (prevent token brute-force). Exceeding → 429 + 10-minute cooldown.

**Postgres query quotas** (prevent expensive queries):

- **Scan sector**: `GET /sectors/{x}/{y}` limited to 1 call/user/second (sector scans are read-heavy: join ships + planets). Client caches scan results (5-second TTL), refreshes via WebSocket deltas.

### 7.4 Input Validation

FastAPI + Pydantic models enforce **schema validation**:

- **Type checks**: `target_speed: float` → reject if string, NaN, Infinity.
- **Range checks**: `focus_percent: int` → assert `1 <= focus <= 100`. `sector_x: int` → assert `0 <= x < 30` (universe bounds).
- **Item checks**: `item: str` → assert `item in ["men", "missiles", "torpedoes", ...]` (enum).
- **Quantity checks**: `qty: int` → assert `qty > 0`, `qty <= ship.items[item]` (cannot sell more than owned).

**SQL injection prevention**: Use parameterized queries (asyncpg `$1`, `$2` placeholders). NEVER string interpolation (`f"SELECT * FROM ships WHERE id={ship_id}"` ← vulnerable). FastAPI ORM (SQLAlchemy or Tortoise ORM) auto-escapes.

**XSS prevention**: API returns JSON (no HTML rendering). Unity client sanitizes player-submitted text (ship names, planet names, chat messages) before rendering (strip `<script>`, `<iframe>` tags; use Unity `TextMeshPro` with rich text disabled for untrusted input).

### 7.5 Secrets Management

- **Firebase service account JSON**: Stored in Fly.io secrets (`fly secrets set FIREBASE_SERVICE_ACCOUNT="$(cat firebase-adminsdk.json)"`). Loaded by FastAPI on startup (`firebase_admin.initialize_app(credential=credentials.Certificate(json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])))`). NEVER committed to git.
- **Postgres connection string**: Stored in Fly.io secrets (`DATABASE_URL=postgres://user:pass@neon.tech/gedb`). Injected as env var.
- **Redis connection string**: Stored in Fly.io secrets (`REDIS_URL=redis://upstash.io:6379`).
- **JWT signing key**: Stored in Fly.io secrets (`JWT_SECRET=<random 64-char hex>`). Generated via `openssl rand -hex 32`. Rotated quarterly (requires re-issuing all JWTs; acceptable with 1-hour TTL: rotation causes 1 hour of 401s, clients refresh).
- **Admin API keys**: Stored in Fly.io secrets (`ADMIN_API_KEY=<random>`). Used for `/admin/*` endpoints (internal only: triggered by cron, not exposed to Unity client).

**Secret rotation policy**: Quarterly rotation for JWT secret, API keys. Firebase service account rotated annually (Firebase console). Postgres password rotated on suspected breach (Neon auto-rotates on vulnerability disclosures).

---

## 8. Scalability Path

### 8.1 Phase 1 Capacity (Single Galaxy)

**Target**: 1,000–5,000 concurrent users (CCU), 10,000–50,000 monthly active users (MAU).

**Infrastructure**:
- **API**: 2× Fly.io shared-CPU instances (2 vCPU, 2 GB RAM each) = $10/month. Each handles 2,500 WebSocket connections + 100 req/sec REST. Fly.io load balancer distributes clients (round-robin or latency-based).
- **ge-sim**: 1× Fly.io shared-CPU instance (2 vCPU, 4 GB RAM) = $10/month. Processes 5,000 ships × 6s tick (tick duration: ~2 seconds on 2 vCPU). Single instance (no horizontal scaling yet; `ge-sim` is stateful: owns tick schedulers).
- **Postgres**: Neon Serverless Postgres, $25/month (scale-to-zero, 1 GB storage, 100 GB bandwidth). 1 primary (us-east), 1 read replica (us-west for low-latency reads).
- **Redis**: Upstash Serverless Redis, $10/month (10k commands/sec, 256 MB storage). Single-region (us-east). Ephemeral state only (no persistence; on crash, clients resubscribe).
- **Total**: ~$60/month for 5,000 CCU. Cost per CCU: $0.012/month (1.2 cents).

**Bottleneck analysis**:
- **WebSocket connections**: 2 API instances × 2,500 connections = 5,000 max. Add 1 instance per +2,500 CCU ($5/month).
- **Postgres writes**: `ge-sim` writes 5,000 ships × 6s tick = ~800 writes/sec (ship position, damage, energy). Neon handles 1,000 writes/sec on $25 plan. Headroom: 20%. At 6,000 ships, upgrade to Neon $50 plan (2,500 writes/sec).
- **Redis pubsub**: 5,000 ships × 10 updates/min = 50K updates/min = 833/sec. Upstash handles 10K commands/sec. Headroom: 90%. At 100K ships, upgrade to Upstash $50 plan (100K commands/sec).
- **ge-sim CPU**: Tick duration scales linearly with ship count (O(N) for position updates, O(N²) for combat in same sector but rare: avg 5 ships/sector × 450 sectors = pessimistic O(5² × 450) = O(11K) pairwise checks, optimized via spatial index). At 10,000 ships, tick duration ~4 seconds (approaching 6s limit; danger of tick skipping). Mitigation: optimize (spatial hash grid for combat queries) or scale horizontally (see Phase 2).

### 8.2 Phase 2: Horizontal Scaling (Sharded Galaxies)

**Trigger**: >10,000 CCU or tick duration >5 seconds (approaching 6s tick window; risk of lag).

**Architecture**:

```
                          ┌─────────────────┐
                          │  Gateway Service │ (assigns players to galaxies)
                          └────────┬─────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
   ┌──────▼──────┐         ┌──────▼──────┐         ┌──────▼──────┐
   │ Galaxy 1    │         │ Galaxy 2    │         │ Galaxy 3    │
   │ API + ge-sim│         │ API + ge-sim│         │ API + ge-sim│
   │ Postgres    │         │ Postgres    │         │ Postgres    │
   │ Redis       │         │ Redis       │         │ Redis       │
   └─────────────┘         └─────────────┘         └─────────────┘
```

**Sharding strategy**:
- **Galaxy per 5,000 players**: Each galaxy = independent Postgres + Redis + `ge-sim` instance. Players assigned to galaxy on signup (random or geo-based: NA players → Galaxy 1 US-East, EU players → Galaxy 2 EU-West).
- **Cross-galaxy raids** (optional): Players can "warp" to other galaxies (costs rare item: Warp Gate Pass, $0.99 IAP?). Gateway service brokers cross-galaxy attacks (async message queue: attacker in Galaxy 1 fires at target in Galaxy 2 → Gateway publishes event to Galaxy 2 Redis → Galaxy 2 `ge-sim` processes).
- **Galaxy merging**: If Galaxy 3 drops to <500 players (underpopulated), merge into Galaxy 1 (Postgres dump + restore; preserve player state).

**API scaling**: 10 API instances (50,000 CCU) behind Fly.io load balancer. Each API instance connects to **one galaxy's Redis** (no cross-galaxy pubsub; clients connect to their galaxy's API). Gateway service routes clients to correct API instance (via DNS or HTTP redirect: `gateway.fly.dev → galaxy1.fly.dev` vs `galaxy2.fly.dev`).

**ge-sim scaling**: One `ge-sim` per galaxy. No horizontal scaling of `ge-sim` within one galaxy (tick schedulers are inherently stateful: must process all ships/planets in galaxy atomically). Vertical scaling: `ge-sim` can run on 8 vCPU, 16 GB RAM ($100/month) to handle 20,000 ships per galaxy.

### 8.3 Database Scaling

**Read scaling** (Phase 1):
- Neon read replicas (1-2 replicas per region). FastAPI routes: writes → primary, reads (leaderboards, planet scans) → replicas. `asyncpg` supports read replica URLs (`REPLICA_DATABASE_URL=postgres://replica.neon.tech`).
- Caching: Redis for hot queries (leaderboard top 100: cache 60 seconds, user profile: cache 5 minutes). FastAPI checks Redis before Postgres.

**Write scaling** (Phase 2):
- Postgres partitioning: `ships` table partitioned by `sector_x, sector_y` (range partition: 6 partitions for 30 sectors = 5 sectors/partition). Query: `SELECT * FROM ships WHERE sector_x BETWEEN 5 AND 9` hits 1 partition (faster).
- Batch writes: `ge-sim` batches tick updates (1,000 ship positions → 1 `UPDATE` with `unnest()` array, not 1,000 individual `UPDATE`s). Reduces Postgres write amplification.

**Database size**:
- **Phase 1**: 50,000 MAU × 10 ships/user = 500K ships × 512 bytes = 256 MB. 4,000 planets × 512 bytes = 2 MB. 50,000 users × 256 bytes = 12.8 MB. Mail archive (retain 30 days): 1M mails × 256 bytes = 256 MB. **Total: ~530 MB** (fits Neon $25 plan's 1 GB).
- **Phase 2**: 500,000 MAU × 10 ships = 5M ships = 2.5 GB. Planets: 40,000 (expanded universe) = 20 MB. Users: 128 MB. Mail: 2.5 GB (archive 90 days). **Total: ~5.2 GB** (Neon $50 plan's 10 GB).

---

## 9. Deployment Topology

### 9.1 Fly.io Deployment

**API service** (`fly.toml`):
```toml
app = "ge-api"
primary_region = "iad" # us-east
[build]
  image = "ghcr.io/talktojer/ge-api:latest"
[[services]]
  internal_port = 8000 # FastAPI uvicorn
  protocol = "tcp"
  [[services.ports]]
    port = 80
    handlers = ["http"]
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
[http_service]
  force_https = true
[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory_mb = 2048
[scaling]
  min_machines = 2
  max_machines = 10 # auto-scale based on CPU (>80% for 5 min → add instance)
```

**ge-sim service** (`fly-sim.toml`):
```toml
app = "ge-sim"
primary_region = "iad"
[build]
  image = "ghcr.io/talktojer/ge-sim:latest"
[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory_mb = 4096
[scaling]
  min_machines = 1
  max_machines = 1 # no auto-scale (stateful: single instance per galaxy)
```

**Deployment commands**:
```bash
# Build and push Docker images (GitHub Actions on merge to main)
docker build -t ghcr.io/talktojer/ge-api:latest -f Dockerfile.api .
docker push ghcr.io/talktojer/ge-api:latest

docker build -t ghcr.io/talktojer/ge-sim:latest -f Dockerfile.sim .
docker push ghcr.io/talktojer/ge-sim:latest

# Deploy to Fly.io (GitHub Actions calls flyctl)
flyctl deploy --config fly.toml --image ghcr.io/talktojer/ge-api:latest
flyctl deploy --config fly-sim.toml --image ghcr.io/talktojer/ge-sim:latest
```

**Zero-downtime deploys**:
- **API**: Fly.io rolling restart (spin up new instance, wait for health check, route traffic, terminate old). 10-second overlap.
- **ge-sim**: Graceful shutdown (catch SIGTERM, finish current tick, flush Postgres writes, exit). Fly.io waits 30 seconds for clean exit, then SIGKILL. New instance starts, resumes ticks (no data loss; ticks are idempotent: if tick N completes but crash before Redis publish, tick N+1 recalculates deltas from Postgres state).

### 9.2 CI/CD Pipeline (GitHub Actions)

**`.github/workflows/deploy.yml`** (conceptual; not implemented):
```yaml
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: poetry install
      - run: pytest tests/ # unit tests (combat formulas, physics, auth)
      - run: mypy src/ # type checking
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: docker build -t ghcr.io/talktojer/ge-api:${{ github.sha }} -f Dockerfile.api .
      - run: docker push ghcr.io/talktojer/ge-api:${{ github.sha }}
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: flyctl deploy --image ghcr.io/talktojer/ge-api:${{ github.sha }}
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

**Stages**:
1. **Lint**: `ruff check src/` (Python linting), `black --check src/` (formatting).
2. **Test**: `pytest tests/` (unit tests: 80%+ coverage target for `combat.py`, `physics.py`, `auth.py`). Integration tests: spin up Postgres + Redis (Docker Compose), run API, test REST endpoints.
3. **Build**: Docker images (multi-stage: builder stage installs Poetry deps, final stage copies venv only; 50 MB final image).
4. **Deploy**: `flyctl deploy` (atomic: new version deploys, health check passes, old version terminates).

**Rollback**: `flyctl releases list` + `flyctl deploy --image ghcr.io/talktojer/ge-api:<previous-sha>` (manual; trigger on Sentry error spike).

### 9.3 Monitoring & Alerts

**Metrics** (Prometheus `/metrics` endpoint):
- `http_requests_total{method, path, status}`: Request count (by endpoint, status code).
- `http_request_duration_seconds{method, path}`: Latency histogram (p50, p95, p99).
- `websocket_connections_active`: Current WebSocket count.
- `tick_duration_seconds{type}`: Histogram for 6s ship tick, 55s planet tick (alert if p99 >5s).
- `db_query_duration_seconds{query}`: Postgres query latency (alert if >100ms).
- `redis_commands_total{command}`: Redis command count (PUBLISH, SADD, SMEMBERS).

**Dashboards** (Grafana):
- **Overview**: CCU (WebSocket count), req/sec, avg latency, error rate (5xx).
- **Tick health**: Tick duration over time (detect degradation), ships processed per tick.
- **Database**: Postgres CPU/memory, slow queries (log queries >1s), connection pool saturation.

**Alerts** (PagerDuty):
- **Critical**: API 5xx rate >1% for 5 min (Sentry alert → PagerDuty).
- **Critical**: `ge-sim` tick duration >5s for 3 consecutive ticks (approaching 6s limit; risk of tick skipping).
- **Warning**: Postgres connection pool >80% for 5 min (scale up connections or add read replica).
- **Warning**: Redis memory >90% (evict old keys or upgrade plan).

**Logging** (structured JSON):
```json
{"timestamp": "2026-09-11T18:00:00Z", "level": "info", "event": "ship_tick_complete", "ships_processed": 1234, "duration_ms": 2340, "trace_id": "abc123"}
```
Logs shipped to Grafana Cloud Loki (or Fly.io built-in logs). Searchable by `trace_id` (OpenTelemetry: propagate `trace_id` from REST request → Postgres query → Redis publish → WebSocket push; full request trace).

---

## 10. Risks & Open Questions

### 10.1 Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **`ge-sim` tick duration exceeds 6s** (too many ships, tick skipping) | High: combat/movement lag, bad UX | Medium (if CCU >10K without optimization) | 1. Profile tick hot paths (cProfile), optimize (spatial hash grid for combat, Cython for physics). 2. Horizontal scaling (shard galaxies at 5K players). 3. Increase tick window to 10s (game design trade-off: slower pacing). |
| **Postgres write bottleneck** (800 writes/sec × 10 galaxies = 8K writes/sec, Neon limit 2.5K writes/sec on $50 plan) | Medium: tick delay, eventual consistency lag | Low (Phase 2 only; 10 galaxies = 50K CCU) | 1. Batch writes (`unnest()` array updates). 2. Write sharding (partition `ships` table by `sector_x`). 3. Upgrade to dedicated Postgres (RDS, self-hosted) with 10K writes/sec. |
| **Redis pubsub message loss** (Redis restart, network partition) | Low: clients miss deltas, stale UI state | Low (Upstash 99.9% uptime SLA) | 1. Clients periodically refetch full state via REST (`GET /ships/{id}` every 60s). 2. Redis pubsub is **best-effort** (acknowledge this: deltas are optimization, not authoritative). 3. On reconnect, client queries "deltas since timestamp X" (Postgres `ship_history` table logs changes with timestamp; fallback if Redis missed). |
| **Firebase Auth outage** (no new logins) | High: players cannot sign in | Very Low (Firebase 99.95% uptime SLA) | 1. Existing players unaffected (JWT valid for 1 hour; refresh extends session). 2. Fallback: email/password auth (Phase 2; requires custom auth table). 3. Monitor Firebase status page (auto-alert on degraded). |
| **WebSocket connection storms** (10K clients reconnect simultaneously after deploy) | Medium: API CPU spike, rate limit kicks in | Medium (on every deploy) | 1. Exponential backoff on client reconnect (1s, 2s, 4s jitter). 2. Fly.io auto-scaling (add API instances on CPU >80%). 3. Rolling deploy (10% of clients affected at a time). |
| **Malicious client exploits** (send fake damage reports, forge JWT, SQL injection) | Critical: economy破坏, unfair advantage | Low (if input validation strict) | 1. Server-authoritative (client NEVER sends damage values; only commands: "fire phasor"). 2. Pydantic validation (reject out-of-range inputs). 3. Parameterized queries (no string interpolation). 4. Penetration test (hire security audit before launch). |

### 10.2 Open Questions for Jeremy / Empire Lead

1. **Offline vulnerability policy**: Phase 1b provides push notifications (infrastructure). **Game design** decides: Do offline ships get immunity? Must player dock at citadel before logout? Hire NPC guards? **Decision needed:** Hard-core (offline = vulnerable, notify only) vs. casual-friendly (offline = immune after 10 min AFK)?

2. **Universe size**: Legacy 30×15 = 450 sectors. Sufficient for 1,000 players (~2 players/sector), but crowded at 5,000 (11 players/sector = constant PvP). **Decision needed:** Expand to 100×50 (5,000 sectors) or keep 30×15 (intimate, high conflict)? Affects map generation, spatial queries, sector subscription load.

3. **Combat pacing**: Keep 6s tick (strategic, coordination-heavy) or reduce to 2s (faster, more action)? **Recommendation:** Keep 6s for Phase 1 (differentiate from twitch shooters), A/B test 2s in Phase 2 (opt-in "blitz mode" sector?).

4. **Realtime skirmish combat** (twitch, joystick-driven dogfights): Phase 1 = strategic turn-based (6s ticks). Phase 2+ = optional realtime skirmish (Unity Netcode, dedicated relay). **Decision needed:** Priority? Budget? (Realtime adds $10K+ dev time: client-side prediction, lag compensation, cheat detection). **Recommendation:** Defer to Phase 3+ (validate strategic loop first; 80% of retention is empire-building, not dogfights).

5. **Monetization impact on stack**: F2P + cosmetics (ship skins, planet themes) requires asset CDN (Cloudflare R2, $0.015/GB storage, $0.01/GB egress). F2P + time-savers (speed up production, extra ship slots) requires Postgres schema (`users.premium_tier`, `production_boost_expires_at`). **Decision needed:** Business model? Affects Phase 1b infra (asset pipeline, payment webhooks: Stripe, Apple IAP).

6. **Team size / alliance cap**: Legacy `MAXTEAMS=50`, no member limit. Modern: 50 teams × 100 members/team = 5,000 players in teams (reasonable for 10K MAU). **Decision needed:** Keep 50 team limit or increase? Alliance wars (team vs. team tournaments) require matchmaking layer (outside Phase 1b scope; note for Phase 2).

7. **Push notification frequency**: Max 1 push/5min to avoid spam. But what if player's 5 planets are attacked simultaneously (5 attackers)? Send 1 aggregated push ("5 planets under attack!") or 5 separate (user annoyed, disables notifications)? **Decision needed:** Aggregation rules (1 push/event-type/5min? 1 push/sector/5min?).

8. **Data retention**: Mail retained 30 days, kill logs 90 days, leaderboard snapshots 1 year, ship movement logs never (privacy). **Decision needed:** Compliance (GDPR: user requests data deletion → purge user, ships, planets within 30 days). Affects Postgres schema (`users.deleted_at`, cascading deletes).

---

## 11. Out of Scope / Non-Goals

This ADR is **design documentation only**. The following are explicitly **OUT OF SCOPE** for Phase 1b:

### 11.1 Not Delivered (Deferred or Never)

- ❌ **Unity project scaffold** (no `.unityproject`, no C# code files, no scene files): Unity client implementation is separate effort (Phase 1c: Client MVP). This ADR defines the **contract** (REST API, WebSocket protocol) Unity devs implement against.

- ❌ **Runnable game server code** (no FastAPI `main.py`, no `ge-sim` tick scheduler Python files, no Docker Compose, no deployment scripts): Phase 1b = **architecture design only**. Implementation is Phase 1d (Backend MVP). This ADR is the **blueprint** backend devs code against.

- ❌ **Database schema SQL** (no Postgres `CREATE TABLE` DDL, no migrations): Schema is implied by architecture (tables: `users`, `ships`, `planets`, `mail`, `teams`, `sectors`), but exact columns, indexes, constraints are Phase 1d deliverable.

- ❌ **Game design details** (offline protection policy, combat damage tuning, economy balance, progression curves, tutorial flow, cosmetics catalog): Phase 1b = **infrastructure stack** (how backend is built). **Game design** (what rules, what balance) is separate doc (Phase 1e: Game Design Document). This ADR notes **open questions** for game design (e.g., offline policy) but doesn't decide them.

- ❌ **Realtime skirmish combat** (Unity Netcode, joystick controls, client-side prediction): Explicitly deferred to Phase 2+. Phase 1 = strategic turn-based (6s ticks). Realtime combat is **optional later** (if user testing shows demand).

- ❌ **Admin dashboard** (web UI for banning users, viewing leaderboards, triggering resets): Infrastructure supports (`/admin/*` REST endpoints), but UI is Phase 2+. Phase 1: admin actions via `curl` or Postman.

- ❌ **Payment integration** (Stripe webhooks, Apple IAP receipt validation, premium subscriptions): Monetization deferred to Phase 2. Phase 1 = free beta (no IAP). Stack supports (Postgres `users.premium_tier`, API `/payments/webhook`), but implementation later.

- ❌ **Analytics / telemetry** (Mixpanel events, Amplitude funnels, BigQuery data warehouse): Phase 1 logs to stdout (JSON structured logs). Analytics pipeline (ETL logs → data warehouse → dashboards) is Phase 2+.

- ❌ **Localization** (multi-language support: i18n, translated strings, region-specific content): Phase 1 = English only. i18n deferred to Phase 3+ (once core loop validated in one language).

- ❌ **Voice chat** (Vivox, Agora): Text chat only (WebSocket messages). Voice deferred to Phase 3+ (if team coordination requires; may integrate Discord instead of custom voice).

### 11.2 Assumptions (Requirements for Later Phases)

These are **locked in** by this ADR (later phases must comply):

- ✅ **FastAPI as primary API framework**: Phase 1d backend implementation MUST use FastAPI (not Django, Flask, Express). This ADR's architecture assumes FastAPI's async capabilities (Starlette WebSockets, async route handlers).

- ✅ **Postgres as authoritative database**: Phase 1d MUST use Postgres 15+ (not MongoDB, MySQL, DynamoDB). Schema design (Phase 1d) MUST normalize (3NF) and index hot paths (ship lookups, sector scans).

- ✅ **Firebase Auth for identity**: Phase 1c Unity client MUST integrate Firebase Auth (Sign in with Apple + Google). No custom username/password auth (unless Phase 2 adds as fallback).

- ✅ **WebSockets for realtime updates** (not polling, not SSE, not long-polling): Phase 1c Unity client MUST open persistent WebSocket connection for sector/fleet subscriptions. REST is for commands, WebSocket is for deltas.

- ✅ **6s combat tick, 55s production tick** (strategic pacing): Phase 1d `ge-sim` MUST implement tick schedulers at these intervals (can tune ±1s for perf, but order-of-magnitude same: not 100ms twitch, not 5-minute turn-based).

- ✅ **Server-authoritative simulation**: Phase 1d MUST compute all game logic (combat damage, movement, production) on server. Unity client is **presentation layer** (interpolates, animates). No client-side prediction (deferred to Phase 2 realtime skirmish if ever).

- ✅ **Monorepo Python (FastAPI + ge-sim)**: Phase 1d MUST implement both API and world sim in one repo (shared models, single deployment pipeline). Do NOT split into separate repos (loses shared code, complicates refactoring).

---

## Appendix A: Glossary

- **ADR**: Architecture Decision Record. This document.
- **BBS**: Bulletin Board System. 1980s-1990s dial-up online services. GE's original platform.
- **Btrieve**: 1980s flat-file database (Novell). Legacy GE storage layer (replaced by Postgres).
- **CCU**: Concurrent users. Number of players online simultaneously.
- **FastAPI**: Python async web framework (Starlette + Pydantic). GE's REST + WebSocket API layer.
- **Firebase Auth**: Google identity platform (OAuth2). GE's authentication (Apple, Google sign-in).
- **FCM**: Firebase Cloud Messaging. Push notifications for Android (and iOS via APNs relay).
- **Fly.io**: PaaS (Platform-as-a-Service). GE's compute deployment (Docker containers).
- **ge-sim**: GE's world simulation service (Python asyncio). Runs 6s/55s tick schedulers.
- **MAU**: Monthly active users. Number of unique players who logged in within 30 days.
- **Neon**: Serverless Postgres provider. GE's database hosting (alternative: Supabase Postgres).
- **NGO**: Netcode for GameObjects. Unity's built-in client-server netcode (rejected for GE).
- **Postgres**: PostgreSQL relational database. GE's authoritative state store.
- **Redis**: In-memory key-value store. GE's pubsub, presence, rate limits, hot state.
- **Upstash**: Serverless Redis provider. GE's Redis hosting.
- **WebSocket**: Persistent bidirectional TCP connection over HTTP. GE's realtime delta push to Unity clients.

---

## Appendix B: References

- **Phase 1a: Legacy System Map**: [docs/PHASE1A_LEGACY_SYSTEM_MAP.md](./PHASE1A_LEGACY_SYSTEM_MAP.md) (source of truth for BBS ticks, Btrieve, combat formulas, ship physics, planetary production).
- **FastAPI docs**: https://fastapi.tiangolo.com/ (async route handlers, WebSockets, Pydantic validation).
- **Firebase Auth Unity SDK**: https://firebase.google.com/docs/auth/unity/start (Sign in with Apple, Google, token exchange).
- **Postgres async driver (asyncpg)**: https://github.com/MagicStack/asyncpg (Python async Postgres client; 10x faster than psycopg2).
- **Redis pubsub**: https://redis.io/docs/manual/pubsub/ (publish/subscribe messaging for sector deltas).
- **Fly.io deployment**: https://fly.io/docs/ (Docker deploy, secrets, scaling).
- **Neon Postgres**: https://neon.tech/docs (serverless Postgres, connection pooling, read replicas).
- **Upstash Redis**: https://upstash.com/docs/redis (serverless Redis, pubsub, rate limiting).
- **OpenTelemetry Python**: https://opentelemetry.io/docs/instrumentation/python/ (distributed tracing for FastAPI + Postgres + Redis).
- **Sentry Python SDK**: https://docs.sentry.io/platforms/python/ (error tracking, performance monitoring).

---

**End of Phase 1b Stack ADR.**  
**Next step:** Review with Jeremy / Empire Lead → address open questions → proceed to Phase 1c (Unity Client contract) or Phase 1d (Backend implementation) per project roadmap.
