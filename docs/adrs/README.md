# Architecture Decision Records (ADRs)

This directory indexes architecture decision records for the **Galactic Empire mobile MMO reimagine** project.

---

## Overview

ADRs document significant architectural choices, alternatives considered, and rationale. Each ADR follows a consistent structure:
- **Status**: Proposed / Accepted / Deprecated
- **Context**: Problem statement, requirements, constraints
- **Decision**: Chosen solution + summary table
- **Alternatives**: Options evaluated and rejected
- **Consequences**: Trade-offs, risks, open questions

---

## Index

### Phase 1: Foundation & Architecture

| ID | Title | Status | Date | Summary |
|----|-------|--------|------|---------|
| [Phase 1a](../PHASE1A_LEGACY_SYSTEM_MAP.md) | Legacy System Map – Galactic Empire (MajorBBS) | Accepted | 2026-09-11 | Analysis-only documentation of the 1988 BBS codebase: BBS ticks (6s ships, 55s planets), Btrieve persistence, single-threaded event loop, ship/planet entities, combat formulas, economy, offline vulnerability. Source of truth for modernization. |
| [Phase 1b](../PHASE1B_STACK_ADR.md) | Stack Architecture Decision – FastAPI + asyncio + Redis + Postgres | Proposed | 2026-09-11 | **Primary ADR.** Selects unified FastAPI + Python asyncio monorepo with Redis (pubsub), Postgres (authoritative state), Firebase Auth, WebSockets for realtime. Replaces BBS ticks with event-driven `ge-sim` service. Rejects Nakama (Lua fragmentation), Supabase Realtime (full-row broadcasts), Unity NGO (overkill for strategic cadence). Deployment: Fly.io + Neon + Upstash. |

---

## How to Use

1. **New to the project?** Read **Phase 1a** (legacy system) → **Phase 1b** (modern stack) in order.
2. **Implementing backend?** Phase 1b is your blueprint: FastAPI endpoints, WebSocket protocol, Postgres schema (implied), `ge-sim` tick schedulers.
3. **Implementing Unity client?** Phase 1b § 6 ("Client Integration") defines the REST + WebSocket contract you must implement.
4. **Proposing changes?** Create a new ADR (copy Phase 1b template), add to this index, open PR for review.

---

## ADR Template (Future ADRs)

```markdown
# Phase X: [Title]

**Status:** Proposed / Accepted / Deprecated  
**Date:** YYYY-MM-DD  
**Owners:** [Author(s)]  
**Context:** [Link to prior ADRs if relevant]

## Executive Summary
[2-3 sentence summary of decision]

## Context & Requirements
[Problem statement, constraints, prior art]

## Decision
[Chosen solution + rationale]

## Alternatives Considered
[Options A, B, C evaluated + why rejected]

## Consequences
[Trade-offs, risks, open questions]

## References
[Links to docs, specs, code]
```

---

## Contact

Questions on ADRs? Reach Empire Lead (Jeremy) or GE Stack Architect via project channels.

**Repository**: [talktojer/ge](https://github.com/talktojer/ge) (private)
