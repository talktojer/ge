# Phase 1b: Mobile Client UX Vision – Galactic Empire

**Date:** 2026-09-11  
**Source of Truth:** `docs/PHASE1B_GAME_DESIGN.md` (PR #2, Designer-locked systems) + `docs/PHASE1A_LEGACY_SYSTEM_MAP.md` (PR #1, legacy analysis)  
**Target Platform:** iOS + Android (Unity Editor 6000.4.10f1)  
**Scope:** Design documentation only; no implementation.

---

## Executive Summary

Galactic Empire Mobile transforms a 1988 BBS text-command space conquest game into a **modern mobile-first strategic MMO** while preserving its tactical fleet/conquest depth. Players command ships through a sharded persistent galaxy (~100×50 sectors, 500-1k players/shard), claim and manage planets, engage in strategic combat (~6s resolution), and build alliances — all from a phone.

**North Star (Aligned with Game Design §2.2):** "Command an empire, not a joystick" — thumb-first, glanceable territory management, strategic depth without BBS friction or twitch reflex requirements.

**Core Fantasy:** Year 3250. You pilot a starship through uncharted space, claiming planets, building production empires, upgrading fleets, and crushing rivals in strategic combat. Your empire persists 24/7 in a shared galaxy with thousands of players.

**UX Pillars:**
1. **Thumb-Zone Primary** — All critical actions within one-handed reach; destructive actions require confirmation
2. **Glanceable Status** — See empire health (wealth, threats, production) at a glance on HUD
3. **Strategic Pacing** — Preserve legacy's 6s combat tick and 55s production cycles; instant UI response with async server resolution
4. **Session Flexibility** — Support micro (2-5 min: harvest, check alerts), standard (10-20 min: travel, trade, combat prep), and deep (30-45 min: conquest campaigns) sessions
5. **Safe Harbor** — Explicit offline protection via docking/citadel retreat; no surprise raids while AFK

**Primary UX Transformation:** Replace BBS 3-letter text commands (`imp`, `pha`, `buy`) with contextual touch UI (tap ship → radial menu; swipe to navigate; drag to aim). Preserve strategic timing (6s combat cadence feels tactical, not twitch) but make actions feel instant via optimistic UI updates and smooth client-side interpolation between server ticks.

**Key Design Decisions (Aligned with Game Design §8 & §9):**
- **Bottom tab navigation** (4 tabs per §9.1 Mobile UX Contract): **Map**, **Fleet**, **Empire**, **Social**
- **HUD design** for local space (§9.1): Top bar (cash, energy, ship, alliance), center contextual action button, minimap (10% bottom-right), bottom nav bar
- **Universe**: Instanced shards (~100×50 sectors, 5000 total, 500-1k players/shard per §8.1)
- **Combat pacing**: ~6-second strategic tick (§8.3) — instant UI input, deliberate server resolution, time to coordinate
- **Production cycles**: 55-second tick (§6.2) — masked with progress bars and push notifications
- **Onboarding flow**: 90-second interactive tutorial (§9.4 anti-pattern: avoid >3min forced tutorial)
- **Offline protection**: Safe Harbor docking (invulnerable at NPC citadels, costs rent) + optional NPC planet defenders (§8.2)
- **Death penalty**: Insurance system (§8.6) — pay premium to recover 75% cargo, uninsured loses 50%
- **Monetization**: F2P + cosmetics only, NO P2W (§8.4 LOCKED by Empire Lead/Jeremy) — cosmetic shop/skins entry points only, zero production speedups or combat-power IAP

---

## Document Alignment & Authority

**This UX Vision aligns with and extends `docs/PHASE1B_GAME_DESIGN.md` (PR #2, Designer-led systems design).** All product decisions (universe shards, offline protection, combat pacing, monetization, PvE/PvP balance, death penalty, identity) are **locked** per Game Design §8. This document translates those decisions into mobile UX patterns, screen flows, and interaction design.

**Mobile UX Contract (Game Design §9):** This vision implements the Designer's mandatory HUD elements, deep screen requirements, push triggers, and anti-patterns. Where the Game Design doc specifies "must-haves" (e.g., 4-tab nav, specific HUD layout), this document matches exactly. Where the Game Design doc delegates to Client UX (e.g., wireframe details, animation budgets, visual style), this document proposes solutions.

**Hierarchy of Authority:**
1. **Game Design §8 (locked product decisions)** — immutable for Phase 1b
2. **Game Design §9 (Mobile UX Contract)** — Client UX must implement as specified
3. **This UX Vision (screen flows, interactions, wireframes)** — extends Game Design with mobile-specific detail
4. **Phase 1a Legacy System Map (PR #1)** — referenced for mechanics grounding (14 item types, 6s/55s ticks, combat formulas, etc.)

**Conflict Resolution:** If this document contradicts Game Design §8 or §9, Game Design wins. Flag contradictions to Designer for resolution.

---

## 1. Information Architecture

### 1.1 Primary Navigation (Bottom Tab Bar)

**Design Rationale (Per Game Design §9.1 Mobile UX Contract):** 4-tab bottom nav within thumb zone. Each tab represents a major play surface, not nested submenus. Matches Designer spec exactly.

| Tab | Icon | Primary Goal | Entry State |
|-----|------|--------------|-------------|
| **Map** | 🌌 Galaxy | Navigate space, claim planets, wormholes, sector exploration | Opens to last zoom level (Galaxy/Sector/Local); defaults to Local space if mid-session, galaxy overview if fresh login |
| **Fleet** | 🚀 Ship | Ship roster, loadout, travel, combat history | Opens to active ship card; swipe for ship list if player owns multiple (up to 10 ships per Game Design §4.1) |
| **Empire** | 👑 Crown | Planet list, production dashboard, trade routes, treasury | Opens to Empire Home with attention queue (planets needing action: under attack, production maxed, food shortage) |
| **Social** | 👥 Team | Alliance chat, inbox (notifications history), leaderboard | Opens to alliance tab if in alliance, otherwise leaderboard; includes settings via top-right gear icon |

**Overflow Access (Top Bar):** Settings gear icon (top-right of HUD per §9.1), contextual menus (long-press, swipe actions)

**Global Overlays (not tabs):**
- **Command Sheet** — Contextual action modal (e.g., tap enemy ship → shows Attack/Scan/Lock/Retreat options)
- **Safe Harbor Status Chip** — Persistent floating indicator (top-right or near minimap): "Safe" (green) / "In Danger" (red pulse) / "Docked" (blue anchor icon). Tappable to see Safe Harbor explainer + emergency retreat button.
- **Push Threat Banner** — Slide-down alert when planet under attack or ship engaged in combat while user in different tab

### 1.2 Screen Hierarchy

```
Root
├── Boot / Auth / Character Select
│   ├── Splash (logo, load assets)
│   ├── Login (email/pass or social OAuth)
│   └── Character Select (if multiple commanders per account; future)
│
├── Onboarding (first-time user flow)
│   ├── Intro Cinematic (skippable, 15s: year 3250 hook)
│   ├── Create Commander (name, avatar)
│   ├── Name Starter Ship
│   └── Guided Tutorial (5 steps: Scan, Claim, Produce, Trade, Combat intro)
│
├── Galaxy Tab (Map / Navigation)
│   ├── Galaxy Overview (strategic map, 30×15 sectors or larger if expanded)
│   ├── Sector Grid View (zoom level 2: show sector contents, planets, contacts)
│   ├── Local Space HUD (zoom level 3: tactical view, ship + nearby contacts)
│   ├── Target Sheet (tap contact → details, actions)
│   ├── Combat Radial (tap Fire → weapon picker)
│   ├── Travel Order Sheet (set destination, select drive mode)
│   └── Wormhole Transit (discovery flow)
│
├── Empire Tab (Planets / Production)
│   ├── Empire Home (networth, planet count, threats, attention queue)
│   ├── Planet List (sortable: value, production, threats)
│   ├── Planet Detail (single planet view)
│   ├── Production Editor (set rates, taxes, reserve/markup)
│   ├── Trade Dock Sheet (buy/sell when docked at planet)
│   └── Treasury Summary (cash flow, tax collection)
│
├── Fleet Tab (Ships / Hangar)
│   ├── Active Ship Card (current ship status, loadout, cargo)
│   ├── Ship List (if multiple ships owned)
│   ├── Ship Detail (full stats, upgrade preview)
│   ├── Loadout Editor (equip phasors, shields, items)
│   ├── Hangar (dock/repair, purchase new ship class)
│   └── Travel Orders (current destination, ETA, cancel)
│
├── Intel Tab (Messages / Alerts)
│   ├── Inbox (unread badge, filter: threats/reports/social)
│   ├── Alert Detail (planet under attack, production maxed)
│   ├── Spy Report (enemy planet intel)
│   ├── Killmail (combat recap, loot summary)
│   └── Threat Dashboard (current dangers: locked missiles, nearby enemies)
│
├── Social Tab (Team / Leaderboard)
│   ├── Team Home (alliance info, members, team score)
│   ├── Alliance Chat (text chat, optional voice)
│   ├── Sector Chat (local proximity chat)
│   ├── Leaderboard (weekly/monthly/all-time, filter by team)
│   ├── Team Management (invite, kick, set password)
│   └── Settings (nested: account, notifications, audio, accessibility)
│
└── Overlays
    ├── Command Sheet (contextual actions, swipe up from bottom)
    ├── Safe Harbor Explainer (tap status chip)
    ├── Push Threat Banner (slide down from top)
    ├── Confirmation Dialogs (destructive actions: sell ship, attack planet)
    └── Loading / Error States (spinner, retry, offline mode)
```

---

## 2. Core User Experience Flows

### 2.1 Galaxy Navigation (Map Hierarchy)

**Three Zoom Levels** (preserve Phase 1a's 30×15 sector universe structure, scale UI for potential expansion):

#### Level 1: Galaxy Overview (Strategic Map)
- **View:** Top-down grid showing all sectors (30 columns × 15 rows, or larger if universe expanded per Phase 1a §9.1)
- **Interaction:** Pinch to zoom in; tap sector to jump to Sector Grid View; long-press sector for intel peek (planet count, ownership tint, threat heat)
- **Visual Design:**
  - Sectors color-tinted by dominant ownership (self=blue, ally=green, enemy=red, neutral=gray)
  - Optional toggle: "Threat Heat" overlay (red intensity = enemy fleet density)
  - Bookmarks/pins: Star icon on owned planets, flag icon on team strongholds
  - Fog of war: Unexplored sectors dimmed (Phase 1a scan mechanics preserved)
- **Empty State:** Fresh player sees mostly gray (unexplored fog) + tutorial sector highlighted
- **Performance:** Virtualized rendering (only visible sectors drawn); lazy-load sector data on pan

#### Level 2: Sector Grid View (Sector Contents)
- **View:** Zoomed into single sector (e.g., sector 12,5); shows 0-9 planetary objects (Phase 1a `MAXPLANETS=9`) + ship contacts
- **Interaction:** Tap planet to see detail card; tap ship contact to open Target Sheet; double-tap planet to enter orbit (if in range); pinch out to zoom to Local Space
- **Visual Design:**
  - Planets rendered as spheres with environment/resource color coding (green=lush, red=volcanic, blue=ice, brown=barren)
  - Wormholes as swirling portal icons (distinct from planets)
  - Ship contacts as chevron icons with ownership color + class icon (frigate/cruiser/dreadnought silhouette)
  - Range rings around player ship (scan range, weapon range)
- **Contextual Info Overlays:**
  - Planet name badges on tap
  - Distance readout to selected object
  - "In range" / "Out of range" for actions
- **Empty State:** "Unexplored sector — Scan to reveal" (first-time entry)

#### Level 3: Local Space HUD (Tactical Combat View)
- **View:** Fully zoomed in; player ship at center (or slightly offset for readability), local contacts within ~10k unit range (Phase 1a weapon ranges)
- **Interaction:** Tap contact to select target; drag to pan camera (ship stays centered); swipe right edge for action stack
- **Visual Design (see §3 HUD Design for full detail):**
  - Center canvas: 3D ship model + particle effects (engine trails, shield shimmer, weapon fire)
  - Minimap (bottom-left corner): Sector pip showing player position, fog boundary, contact count
  - Contextual action buttons (right edge): Scan, Fire (opens radial), Shields, Cloak, Orbit/Dock (when near planet)
  - Bottom sheet: Selected target card (name, class, range, shield %, threat level)

**Navigation Gestures:**
- **Pinch in/out:** Zoom between Galaxy ↔ Sector ↔ Local
- **Double-tap sector (in Galaxy view):** Jump to Sector Grid
- **Double-tap planet (in Sector view):** Enter orbit (if in range) or open Planet Detail
- **Long-press:** Peek intel (show tooltip without navigating away)
- **Two-finger rotate (Local Space):** Rotate camera around ship (optional; default locked to heading)

**Travel Flow:**
1. Player taps destination planet/sector on map
2. Travel Order Sheet slides up:
   - Destination name, distance (in sectors or units)
   - ETA (calculated from current speed, Phase 1a physics: acceleration over 6s ticks → client shows human-readable "Arrives in 3 min 24s")
   - Drive mode selector: **Impulse** (normal speed, ~9 warp), **Hyperspace** (faster, no combat allowed per Phase 1a), **Warp Zipper** (instant teleport, consumes item)
   - Confirm button
3. Auto-pilot engages: Ship moves toward destination, ETA chip floats near minimap, updates each tick
4. Interrupt on threat: Banner alerts "Enemy contact! Autopilot paused" → player can Engage or Retreat
5. Arrival: Haptic + notification "Arrived at [Planet Name]" → context switches to orbit/dock options

**Wormhole Discovery:**
- Wormholes (Phase 1a `GALWORM`) hidden until player enters sector with `visible=false` flag
- On first entry: "Unknown anomaly detected" → Scan action → reveals wormhole destination
- Post-discovery: Wormhole marked on map, tap to transit instantly (dialog: "Enter wormhole to [Sector X,Y]?")

**Map Search & Bookmarks:**
- Search bar (top of Galaxy view): Type planet/player/sector name → jumps to location
- Bookmark system: Star icon on owned planets, long-press any location → "Add Bookmark" → custom label (e.g., "Trade Hub", "Enemy HQ")
- "My Empire" quick jump: Tap empire icon → list of owned planets → tap one → fly to Planet Detail and orbit/dock option

**Accessibility:**
- Map supports pinch-to-zoom with Dynamic Type scaling (planet labels remain readable)
- VoiceOver: "Sector 12, 5. Contains 3 planets. Ownership: Neutral. Threat level: Low."
- Color not sole signal for ownership: Combine tint + shape/icon (ally=circle, enemy=triangle, self=square outline)

---

### 2.2 Combat Presentation

**Design Principle:** Preserve Phase 1a's **6-second tactical tick** cadence (feels strategic, not twitch) while making actions feel instant via optimistic UI and visual feedback.

#### Ship-to-Ship Combat Flow

**Engagement Setup:**
1. Player in Local Space HUD, enemy ship in range
2. Tap enemy contact → Target Sheet slides up from bottom:
   - Ship name, class, owner name
   - Distance (in units, updates live)
   - Shield % (estimated via client-side interpolation, server authoritative)
   - Damage % (if scanned)
   - Threat level badge: "Novice" / "Veteran" / "Deadly" (based on kills, from Phase 1a `WARUSR.kills`)
   - Action buttons: **Scan** (reveals full stats), **Lock Target** (for torpedoes/missiles), **Retreat** (emergency exit), **Fire** (opens radial)
3. Player taps **Fire** → Combat Radial appears (see §2.2.1)

**Combat Radial (Weapon Selector):**
- Radial menu centered on target ship
- 4-6 weapon options (based on ship loadout):
  - **Phasor** (primary, infinite ammo, requires charge per Phase 1a)
  - **Torpedo** (lock-on, consumes item)
  - **Missile** (faster lock-on, consumes item + more energy)
  - **Hyper-Phasor** (wide beam, ignores cloak, high energy cost)
  - **Mine** (deploy proximity trap, not direct fire)
  - **Decoy** (deploy distraction, not weapon)
- Each option shows:
  - Icon (weapon silhouette)
  - Ammo count (if consumable: "12" torpedoes)
  - Charge status (phasor: circular progress ring, 0-100%)
  - Disabled state if insufficient energy/ammo (grayed out, shake animation on tap)

**Firing Interaction (Phasor Example):**
1. Player selects **Phasor** from radial
2. Auto-aim default: Client calculates optimal angle, tap "Fire" button → queues action to server
3. Optional precision mode (for skill players): Drag radial to adjust aim offset (±degrees from auto-aim) → bonus damage for manual hits (Phase 1a `pdamage()` formula rewards accuracy)
4. Optimistic UI: Immediate visual feedback (phasor beam particle effect, sound), ship shake/recoil animation
5. Server resolution (6s tick): Damage calculated server-side (Phase 1a `pdamage()` formula: `base * (1 / dist²) * phasortype / 2.5 / ton_factor`), sent to client
6. Damage numbers float above target (e.g., "-342" in red), shield absorb FX (blue ripple if shields up), damage % bar updates

**Lock-On Weapons (Torpedo/Missile):**
1. Player taps **Lock Target** in Target Sheet (if not already locked)
2. Targeting reticle animates on target for 1-2s (client-side fluff; instant server lock per Phase 1a)
3. Select Torpedo/Missile from radial → Confirm
4. Projectile launches: 3D model flies from player ship to target at `torpsped` (Phase 1a config, e.g., 500 units/tick) with trail particles
5. Client interpolates smooth motion between 6s ticks (server sends position updates each tick)
6. Impact: Explosion VFX, damage numbers, shield absorb if applicable
7. Evasion mechanics: Decoys (Phase 1a `MAXDECOY=10`) can confuse lock-on → show "Target Evaded!" message, torpedo veers off

**Shield & Cloak Toggles:**
- **Shields** (right-edge HUD button, always visible):
  - Tap to toggle Up/Down
  - Status: Shield icon glows blue (up), gray (down), red (damaged per Phase 1a `shieldstat=3`)
  - Energy drain indicator: "-100 energy/tick" tooltip on long-press (Phase 1a `SHENGUSE=100`)
  - Shield absorb visual: Blue energy dome flickers on hit, damage numbers show "(absorbed)" in cyan
- **Cloak** (right-edge button, if ship equipped):
  - Tap to engage → ship fades translucent, enemy targeting breaks (Phase 1a: cloaked ships invisible to scans)
  - Energy drain heavy: "-500 energy/tick" (Phase 1a `clenguse` config)
  - Cooldown after decloak: Timer ring on button (Phase 1a `cloak > 0` = cooldown ticks)
  - Restriction: Cannot fire while cloaked (per Phase 1a combat checks)

**Death & Killmail:**
1. Ship damage reaches 100% (Phase 1a `killem()` trigger)
2. Explosion animation: Ship fractures, fireball VFX, screen shake (haptic on device)
3. Killmail modal slides up (full-screen overlay):
   - "You were destroyed by [Attacker Name]"
   - Loss summary: "50% of cargo dropped" (Phase 1a death penalty, §3.1 line 130), itemized list (gold, missiles, etc.)
   - Salvage pin on map: "Wreckage at Sector [X,Y]" (tap to navigate back and recover if attacker didn't loot)
   - Attacker stats: Ship class, kills count (for revenge context)
   - Action buttons:
     - **Respawn** (default, takes to neutral zone 0,0 with new class 0 ship per Phase 1a)
     - **Revenge** (adds attacker to enemies list, marks on map if visible)
     - **Report** (if griefing suspected, out of scope for MVP)
4. Respawn flow: Brief loading (3s) → fade in to Local Space HUD at neutral zone, tutorial coach mark: "Rebuild your fleet via trade or conquest"

**Salvage & Loot:**
- Wreckage pin appears on Sector map (golden cargo icon) at death location
- Any player can tap wreckage → "Salvage" action → collect dropped items (first-come, first-served)
- Wreckage expires after 10 minutes (server cleans up) or until looted empty
- Notification to dead player if salvage still available: "Your wreckage remains at [Sector]" (tap to navigate)

**Combat Feedback (Non-Death):**
- **Damage taken:** Screen red vignette flash, ship model shows damage texture (scorch marks, sparks)
- **Damage dealt:** Satisfying impact sound, controller rumble (if gamepad), yellow damage numbers
- **Shield down warning:** "Shields failing!" alert, urgent beep, shield icon pulses red
- **Low energy warning:** "Energy critical!" (below 10%), disable high-energy weapons, suggest Retreat
- **Enemy retreating:** Target flees beyond weapon range → "Target out of range" → Lock Target grays out

#### Planet Assault (Ground Combat)

**Entry Flow:**
1. Player docks at enemy planet (or orbits if neutral/undefended)
2. Planet Detail Sheet shows **Assault** button (red, pulsing if player has sufficient troops)
3. Tap Assault → Conquest Prep Screen (full-screen modal):
   - Attacker loadout:
     - Men slider (from ship cargo, Phase 1a `items[I_MEN]`)
     - Fighters slider (from ship cargo)
   - Defender strength preview (if planet scanned or spy intel available):
     - Men count (Phase 1a `planet.items[I_MEN].qty`)
     - Fighters count
     - Ion cannons (defensive bonus, Phase 1a: each cannon = 10 men)
     - Environment bonus (Phase 1a: higher `enviorn` = defender advantage, 1-9 scale)
     - Technology bonus (Phase 1a: `tech / 100` multiplier)
   - Odds preview (XCOM-style): "Estimated success: 68%" (client-side calculation based on Phase 1a `attack_men()` formula factors)
   - Warning: "This will consume troops regardless of outcome"
   - Confirm button: "Launch Assault"

**Battle Resolution:**
1. Player taps Confirm → loading spinner (1-2s, server runs Phase 1a RNG battle loop `attack_men()` / `attack_fig()`)
2. Battle Report modal (full-screen):
   - Animated wave graphic: Attacker troops advance from left, defenders from right, clash in center
   - Casualty counters tick up (client-side animation for drama, server sends final totals):
     - "Attacker losses: 1,240 men"
     - "Defender losses: 980 men, 3 ion cannons destroyed"
   - Outcome:
     - **Victory:** "Planet captured!" confetti animation, planet card flips to player's color
       - Loot summary: "Seized 45,000 gold from treasury" (Phase 1a `wonplnt()` loots `planet.cash`)
       - Production assets: "Inherited 12 factories" (planet's production rates transfer to player)
       - Action buttons: "Manage Planet" (jumps to Planet Detail), "Return to Fleet"
     - **Defeat:** "Assault repelled." gray screen, sad sound
       - Loss summary: "Lost 1,500 men"
       - Retreat: Ship remains docked (or orbiting if combat prevented docking)
       - Action buttons: "Regroup" (dismiss modal), "Revenge Fleet" (open alliance chat to call reinforcements, social feature)
3. Mail sent to both attacker and defender + spy (if present, Phase 1a spy mechanic §3.3 line 120-188)

**Battle Report Details (Tap "View Full Report" in modal):**
- Phase-by-phase breakdown (if server sends granular data):
  - Round 1: Attacker kills 120 defenders, Defender kills 80 attackers
  - Round 2: ...
  - (Preserve Phase 1a's RNG loop structure `GECMDS.C:3623-3920`, present as readable narrative)
- Defender bonuses applied:
  - "+40% from harsh environment (7/9)"
  - "+20% from advanced technology"
  - "3 ion cannons = +30 men equivalent"
- Random factors: "Attacker rolled 1.2x damage multiplier" (Phase 1a `plattrf1-3` RNG, make it understandable)

**Conquest Empty State:**
- If player has no troops: "Assault" button disabled, tooltip: "Load troops from a planet to attack"
- If planet has no defenders: Auto-capture on orbit + "Admin" action (Phase 1a `cmd_admin()` mechanic for neutral planets)

**Conquest Accessibility:**
- VoiceOver: "Assault button. Planet defended by 1,200 men and 5 ion cannons. Estimated odds: 68% success."
- Confirmation dialog (destructive action): "You will lose troops regardless of outcome. Proceed?"

---

### 2.3 Empire Management

**Design Principle:** Make planet production **glanceable and actionable** (not hidden behind BBS text reports). Surface attention queue (planets needing player action) prominently.

#### Empire Home Screen

**Layout (scrollable vertical):**
1. **Header Card** (hero section):
   - **Networth Sparkline** (Phase 1a `calc_networth()`: kills + planets + cash + production)
     - Large number: "₡2,450,000" (currency symbol, comma-separated)
     - 7-day trend sparkline graph (tiny line chart showing growth/decline)
     - Rank badge: "#12 / 500 players" (weekly leaderboard position)
   - **Empire Stats Row** (3 pills):
     - Planets: "7 owned" (tap → Planet List)
     - Ships: "1 active, 2 docked" (tap → Fleet Hangar)
     - Team: "[Alliance Name]" badge (tap → Team Home)

2. **Attention Queue** (priority section, dismissable cards):
   - Auto-generated alerts for planets needing action:
     - "Planet [Name] needs food" (Phase 1a: troops consuming more food than production, §3.3 line 208)
     - "Production maxed at [Name]" (stockpiles hit `maxpl[item]` cap, Phase 1a §4.2 line 300)
     - "Planet [Name] under attack!" (red urgent card, Phase 1a mail class 1=distress)
   - Each card:
     - Icon (warning triangle, checkmark, alert bell)
     - Short message
     - CTA button: "Manage" → jumps to Planet Detail
     - Swipe right to dismiss (marks as read, no server action)

3. **Production Summary** (expandable section):
   - Total production across all planets (per-tick rates summed, Phase 1a 55s cycle):
     - "Producing 450 gold/hour" (converted from 55s tick math for readability)
     - "Generating ₡12,000/hour in taxes" (Phase 1a `tax` from population)
   - Top 3 producing planets (by value):
     - Planet name, primary resource icon, rate
     - Tap → Planet Detail

4. **Recent Activity Feed** (optional, if space):
   - Last 5 events: "Captured Planet X", "Sold 200 missiles for ₡50k", "Killed [Player]"
   - Tap event → relevant detail screen (Planet/Killmail)

**Empty State (No Planets):**
- Illustration: Empty starfield
- Text: "Your empire awaits. Explore the galaxy to claim your first planet."
- CTA: "Start Exploring" → jumps to Galaxy tab, highlights tutorial sector

#### Planet List Screen

**Layout:**
- Search/filter bar (top):
  - Search by planet name
  - Filter chips: "All" / "High Value" / "Under Threat" / "Maxed Production"
  - Sort dropdown: "Value" / "Production" / "Distance" / "Threats" (default: value descending)
- Scrollable list of owned planets (card per planet):
  - **Planet Card** (horizontal, thumb-tappable):
    - Left: Planet thumbnail (3D render or icon, color-coded by environment/resource per Phase 1a `enviorn`/`resource` 1-9 scale)
    - Center:
      - Planet name (editable, tap to rename)
      - Environment/resource badges: "Lush (7) / Rich (8)" (green pill + gold pill)
      - Treasury: "₡45,000" (Phase 1a `planet.cash`)
      - Production preview: Top 2 producing items (icon + rate, e.g., "Gold +120/hr, Missiles +30/hr")
    - Right:
      - Threat indicator: Shield icon (green=safe, yellow=warnings enabled, red=under attack)
      - Chevron (tap card → Planet Detail)
  - Attention badge: Red dot on card if planet in attention queue

**Empty State (No Owned Planets):**
- Same as Empire Home empty state

**Interaction:**
- Tap card → Planet Detail
- Long-press card → Quick Actions modal: "Navigate to Planet" / "Manage Production" / "View Treasury"
- Swipe left on card → "Abandon Planet" (destructive, confirmation required, releases ownership, Phase 1a reverse of `cmd_admin()`)

#### Planet Detail Screen

**Full-Screen Detail View for Single Planet:**

**Header Section:**
- Planet name (large, editable inline)
- Coordinates: "Sector 12,5 — Planet 3" (Phase 1a `xsect, ysect, plnum`)
- Environment/Resource bars:
  - Environment (1-9 scale, Phase 1a affects production `enviorn / 5.0` multiplier)
  - Resource richness (1-9, Phase 1a `resource / 5.0` multiplier)
  - Visual: Horizontal bar graphs, color intensity (green for lush, gold for rich)
- Ownership badge: "Owned by You" (or ally/enemy name if viewing via scan)
- Beacon message (Phase 1a `beacon[75]` text, editable by owner): Scrolling marquee or tap-to-expand

**Treasury Section (collapsible card):**
- Cash on hand: "₡89,000" (Phase 1a `planet.cash`)
- Tax rate slider: "10%" (Phase 1a `taxrate`, 0-100%, affects population happiness? Code shows no downside, just income)
- Projected tax income: "₡1,200/hour" (calculated from Phase 1a `tax += population * taxrate / 100` per 55s tick)
- Action buttons:
  - **Withdraw** (transfer cash to ship, requires docked)
  - **Deposit** (transfer ship cash to planet treasury)

**Production Grid (primary section):**
- **14 Item Types** (Phase 1a `NUMITEMS=14`, §4.2 line 270):
  0. Men (population labor)
  1. Missiles
  2. Torpedoes
  3. Ion Cannons
  4. Flux Pods (energy refill)
  5. Food
  6. Fighters
  7. Decoys
  8. Troops
  9. Zippers (teleporters)
  10. Jammers
  11. Mines
  12. Gold
  13. Spy

- **Each Item Row:**
  - Icon + name
  - Stockpile qty: "1,240 / 5,000" (current / max per Phase 1a `maxpl[item]`)
  - Production rate control:
    - Slider: 0 to max rate (constrained by manhours, Phase 1a `manhours[item]` labor requirement)
    - Rate display: "+30/hour" (converted from 55s tick)
  - Progress bar (animated, circular or linear):
    - Shows next production increment progress (0-55s countdown until next tick adds qty)
    - ETA label: "Next batch in 22s" (human-readable, Phase 1a `PLANTIME=55s`)
  - Reserve/Markup (for allied sales, Phase 1a `sell='Y'`, `reserve`, `markup2a`):
    - Expand row → "Reserve: 100" (qty held back from allies)
    - "Markup: 120%" (sale price to allies vs base)
    - Toggle: "Sell to Allies" (Y/N)

- **Production Constraints Indicator:**
  - If insufficient men (labor shortage, Phase 1a §4.2 line 290): Warning icon on affected items: "Insufficient labor: reduce rates or increase men production"
  - If food shortage (troops starving, Phase 1a §3.3 line 208): Red alert banner at top: "Food critical! Troops will die in X ticks"

**Defensive Setup (collapsible section):**
- Ion Cannons: Display count (Phase 1a `items[I_IONCANNON].qty`, each = 10 men defense bonus)
- Warnings setting: Dropdown (0-3, Phase 1a `warnings`, auto-message intruders on orbit)
- Password: Text input (Phase 1a `password[10]`, for allied docking access)
- Spy status: "No spy detected" or "Spy planted by [Enemy]" (if discovered, Phase 1a spy mechanics §3.3 line 120)

**Actions (bottom floating button row):**
- **Navigate to Planet** (if not currently orbiting)
- **Dock** (if orbiting, Phase 1a `cmd_orbit()` sets `where >= 10`)
- **Set Production Rates** (if changes made, confirm → sends batch update to server)
- **Trade** (if docked, opens Trade Dock Sheet)

**Empty State (Neutral Planet, not owned):**
- Shows environment/resource info (scanned data)
- Actions: "Claim Planet" (if player meets Phase 1a `cmd_admin()` requirements: sufficient men, docked)

#### Trade Dock Sheet (Modal, appears when docked at planet)

**Design:** Slide-up modal (half-screen or full-screen depending on item count)

**Layout:**
- Header: "Trading at [Planet Name]"
- Ownership context:
  - Own planet: "Your planet — base prices"
  - Allied planet: "Allied planet — markup prices" (Phase 1a `markup2a`)
  - Neutral/enemy: "Docking restricted" (or bribe mechanic, future)

**Buy Section:**
- List of available items (Phase 1a `amt4sale()` formula: own planet = all qty, allied = qty - reserve if `sell='Y'`):
  - Item icon + name
  - Stock available: "450 available"
  - Price per unit: "₡120" (Phase 1a `baseprice[item]` or `markup2a`)
  - Quantity stepper: +/- buttons or slider (constrained by player cash + ship weight limit, Phase 1a `calcweight()`)
  - "Buy" button
- Shopping cart summary (bottom):
  - Total cost: "₡24,000"
  - Weight check: "480 / 1200 tons" (Phase 1a `shipclass[].max_tons`)
  - "Purchase All" (confirm → batch transaction)

**Sell Section (tabs: Buy | Sell):**
- List of items in ship cargo:
  - Item icon + name
  - Qty in cargo: "120 missiles"
  - Sell price: "₡100/unit" (planet's buy price, likely lower than base)
  - Quantity stepper
  - "Sell" button
- Sale summary (bottom):
  - Total revenue: "₡12,000"
  - "Sell All"

**Interaction:**
- Instant UI update on Buy/Sell (optimistic), server confirms, rollback on error (e.g., insufficient cash)
- Bulk actions: "Sell All Gold" button for quick liquidation
- Price comparison tooltip (long-press item): "Base price ₡100, you're paying ₡120 (20% markup)" (transparency for allied trades)

**Empty State (No Stock):**
- Buy section: "No items for sale" (neutral planet or ally hasn't marked items as sellable)
- Sell section: "Cargo empty"

---

### 2.4 Onboarding (First 15 Minutes)

**Goal:** Teach core loop (explore → claim → produce → trade → combat) without walls of text; preserve space conquest fantasy.

#### Step 1: Hook & Character Creation (2 min)

**Intro Cinematic (skippable, 15 seconds):**
- Fade in: Star field, text overlay: "Year 3250. The galaxy awaits a new conqueror."
- Quick cuts: Fleet battle explosions, planet colonies, gold piles, scoreboard rising
- End frame: "Command your destiny." → "Tap to Begin"
- Skip button (bottom-right): "Skip Intro"

**Create Commander:**
- Text input: "Commander Name" (default: random generator "Cmdr [Adjective][Noun]", e.g., "Cmdr SwiftNova")
- Avatar picker (6-8 preset portraits, future: customization)
- Confirm → Brief loading ("Calibrating hyperspace engines...")

**Name Starter Ship:**
- Pre-generated ship shown (Phase 1a class 0 light freighter, 3D model rotating)
- Text input: "Ship Name" (default: random, e.g., "Starfire", "Nomad")
- Coach mark (first UI guidance): "This is your ship. Treat her well."
- Confirm → Fade to Local Space HUD

#### Step 2: Guided Tutorial in Safe Sector (10 min)

**Design Principle:** Tutorial pocket OR soft-gated starter sector (no PvP, only friendly NPCs). Use coach marks (max 5), not modal dialogs.

**Sequence:**

1. **Learn HUD (30 sec):**
   - Spawn in safe sector (0,0 neutral zone or dedicated tutorial sector)
   - Coach mark 1 (points to top status strip): "Monitor your shields and energy here"
   - Coach mark 2 (points to minimap): "Your position in the sector"
   - Coach mark 3 (points to action buttons): "Contextual actions appear here"
   - Auto-advance after 5s or tap "Got it"

2. **First Scan (1 min):**
   - Objective banner (top of screen): "Scan for nearby planets"
   - Scan button (right edge) pulses
   - Player taps Scan → reveal 1-2 planets in sector (Phase 1a `cmd_scan()` mechanic)
   - Scan result card pops up: "2 planets detected" with list (names, distance)
   - Coach mark 4: "Tap a planet to orbit"

3. **Claim First Planet (2 min):**
   - Player taps planet → auto-navigate (tutorial shortcut: instant travel, no wait)
   - Arrive at planet, "Orbit" button appears
   - Tap Orbit → Planet Detail Sheet opens
   - Planet is neutral, "Claim Planet" button highlighted
   - Coach mark 5: "Claim this planet to start your empire"
   - Tap Claim → Confetti animation, "Planet claimed! Name it."
   - Name input → Confirm → Planet now owned

4. **Set First Production (2 min):**
   - Planet Detail auto-scrolls to Production Grid
   - Tutorial highlight: Gold row
   - Instructional text (non-blocking, dismissable): "Set production rate for gold. This generates wealth over time."
   - Player drags Gold rate slider to 50% → Confirm
   - Production progress bar starts animating (accelerated for tutorial: 10s instead of 55s tick)
   - Wait for first gold batch → Notification: "Gold produced! +10 gold. Check your planet's treasury."

5. **First Trade (2 min):**
   - Objective: "Sell your gold at the trade station"
   - Trade station planet marked on map (tutorial sector has NPC station)
   - Navigate to station (again, instant for tutorial)
   - Dock → Trade Dock Sheet auto-opens
   - Sell tab pre-selected, Gold row highlighted
   - Sell 10 gold → Receive ₡1,000 (confetti on first cash)
   - Instructional: "You earned ₡1,000. Use cash to buy upgrades and items."

6. **First Combat Encounter (3 min):**
   - Objective: "Defend yourself against a hostile ship" OR "Meet a training dummy"
   - Friendly training NPC (or very weak cyborg, Phase 1a `cybskill=3` minimum) appears in sector
   - Target auto-locked (tutorial shortcut)
   - Combat Radial opens automatically
   - Instructional: "Tap Phasor to fire"
   - Player fires → Damage dealt → Tutorial NPC's shields drop, it doesn't fire back (scripted to lose)
   - NPC destroyed → Salvage card: "You won! Collect loot: +50 gold"
   - Killmail summary (simplified): "Combat basics complete. You're ready to conquer."

7. **Safe Harbor Introduction (1 min):**
   - Objective banner: "Before you go, learn about Safe Harbor"
   - Safe Harbor status chip (top-right) pulses
   - Tap chip → Explainer modal:
     - "When you log out in open space, your ship is vulnerable to attack."
     - "Dock at a planet or citadel to enable Safe Harbor protection."
     - "Protected ships cannot be attacked while you're offline."
   - Dock at tutorial planet (or station)
   - Green "Safe" badge appears
   - Instructional: "You're now safe to log out. Your empire will continue producing resources."
   - "Finish Tutorial" button → Dismisses modal, unlocks PvP sectors

**Tutorial Complete:**
- Reward screen: "Tutorial Complete! You earned:" (list: tutorial badge, 10k bonus cash, starter resource pack)
- Unlock message: "The galaxy is yours. Explore, conquer, and dominate."
- "Join an Alliance" soft prompt: "Team up with other players for coordinated conquest" → Optional, dismissable
- Jump to Galaxy tab (full access)

**Skipping Tutorial:**
- "Skip Tutorial" button available at any step (top-right)
- Warning: "Skip and start in the open galaxy? You'll miss rewards." → Confirm → Spawn in neutral zone with starter ship, no bonus

**Tutorial Accessibility:**
- All coach marks have audio narration (VoiceOver/TalkBack compatible)
- Visual indicators (pulsing buttons, arrows) redundant with text
- Tutorial replayable from Settings → Help → "Replay Tutorial"

---

### 2.5 Session Shapes & Pacing

**Design Rationale:** Modern mobile MMO must support varying play depths, from 2-minute check-ins to 45-minute campaigns.

#### Micro Sessions (2-5 minutes: Harvest, Orders, Check Threats)
**User Goal:** Quick maintenance, no deep engagement
**UX Flow:**
1. Open app → Local Space HUD loads (resume where left off)
2. Check Attention Queue (Empire tab badge shows count):
   - Tap Empire tab → Attention Queue cards at top
   - Swipe "Production maxed" card → Tap "Withdraw" → Collect gold (optimistic UI, server async)
3. Set travel order:
   - Galaxy tab → Long-press destination → "Travel here" → Confirm → ETA chip appears
4. Check Intel (unread badge):
   - Tap Intel tab → Scan inbox for threats ("Planet under attack" → bookmark for deep session later)
5. Dock for Safe Harbor:
   - If not docked, tap Safe Harbor chip → "Retreat to Citadel" (emergency button) → Instant dock animation
6. Close app (Safe Harbor auto-saves logout state)

**Performance Requirement:** App cold start to usable state in <3 seconds (asset streaming, lazy-load non-critical data)

#### Standard Sessions (10-20 minutes: Travel, Trade, Combat Prep)
**User Goal:** Execute a plan (travel to trade hub, restock ship, prepare for assault)
**UX Flow:**
1. Navigate to trade hub planet (saved bookmark)
2. Dock → Trade Dock Sheet → Buy missiles + torpedoes (bulk purchase, stepper quantity)
3. Load troops from owned planet:
   - Travel to owned planet → Dock → Transfer troops from planet to ship (cargo management screen)
4. Scout enemy planet:
   - Navigate to target sector → Scan (Phase 1a `cmd_scan()`) → View enemy planet stats (if spy planted, get full intel)
5. Prepare assault:
   - Review Conquest Prep Screen → Adjust troop loadout → Check odds (68% success)
   - Bookmark enemy planet, set reminder (optional: schedule assault for alliance raid time)
6. Dock before logout

#### Deep Sessions (30-45 minutes: Campaign Planning, Alliance War)
**User Goal:** Coordinate multi-stage conquest, pvp fleet battle, or economic dominance
**UX Flow:**
1. Alliance chat coordination:
   - Social tab → Alliance Chat → "Raid on Sector 15,8 in 30 min"
   - Team members reply, mark attendance
2. Fleet staging:
   - Multiple players travel to rally sector
   - Set up defensive perimeter (lay mines, deploy jammers)
3. Multi-wave assault:
   - Player A: Scout (hyper-scanner sweep, relay intel in chat)
   - Player B: Soften defenses (orbital bombardment, pre-assault to deplete ion cannons, Phase 1a ion cannons can be destroyed in ground combat)
   - Player C & D: Ground assault (coordinated troop deployment)
4. Post-conquest logistics:
   - Transfer ownership to alliance member
   - Set production for war materiel (missiles, fighters)
   - Establish supply chain (trade routes from production planets to front line)
5. Defense setup:
   - Assign NPC defenders (if feature exists, Phase 1a §9.2 Option C)
   - Set warnings (Phase 1a `warnings` to auto-alert intruders)
6. Debrief in alliance chat → Plan next target → Logout (Safe Harbor)

**UX Support for Deep Sessions:**
- **Persistent map markers:** Pin locations, draw routes (alliance-visible)
- **Shared intel:** Spy reports auto-shared with alliance (toggle in settings)
- **Voice chat integration:** Optional Discord/in-app voice for coordination
- **Session save:** Background app suspend should not lose progress (websocket reconnect, queue pending actions)

---

## 3. HUD Design (Local Space Tactical View)

**Implements Game Design §9.1 Mobile UX Contract exactly.** Platform: iOS + Android, safe areas respected (notch, Dynamic Island, home indicator).

### 3.1 Layout (Portrait Mode Primary per §9.1)

**Portrait Mode (Default, One-Handed Use per §9.1):**

```
┌─────────────────────────────────────┐
│ ⚡₡1.2M 🔋85% [Ship]🚀 [🛡Alliance] ⚙️│  ← Top Bar (§9.1)
├─────────────────────────────────────┤
│                                     │
│                                     │
│    [ Large Contextual Button ]      │  ← Center: Contextual Action
│      (Scan Sector / Fire / Manage)  │     (§9.1: thumb-reachable)
│                                     │
│                                     │
│                            [Minimap]│  ← 10% screen, bottom-right (§9.1)
│                              📍 🟢🔴│
├─────────────────────────────────────┤
│ [Map] [Fleet] [Empire] [Social]     │  ← Bottom Nav (§9.1: 4 icons)
└─────────────────────────────────────┘
```

**Landscape Mode (Optional, Tactical Combat View per §9.1):**
- Full-screen sector view (3D or stylized 2D)
- Weapon radial menu (right side): Phasor, Torpedo, Missile, Shields, Cloak
- Target list (left side): Enemy ships in sector, tap to lock
- Combat log (bottom ticker): "You fired Phasor → 12k damage to [Enemy]. Enemy shields down!"

**HUD Components Detail:**

### 3.2 Top Bar (Game Design §9.1 Specification)

**Elements (left to right, per §9.1):**
1. **Cash balance** (gold icon + number):
   - Display: "₡1.2M" (abbreviated: k for thousands, M for millions)
   - Source: Player liquid wealth (Phase 1a `WARUSR.cash`)
   - Tap: Shows networth breakdown tooltip (cash + planet value + fleet value)
2. **Fleet energy** (lightning icon + %):
   - Display: "85%" (bar graph optional: blue → yellow → red)
   - Source: Active ship energy (Phase 1a `WARSHP.energy` 0-65000, normalized to %)
   - Color: Green >50%, yellow 20-50%, red <20%
   - Recharges 1%/min idle per Game Design §6.3
3. **Active ship thumbnail** (tap to switch ships):
   - Shows current ship class icon (frigate/cruiser/dreadnought silhouette)
   - Tap: Opens Fleet screen (ship roster), quick-switch if multiple ships owned (up to 10 per §4.1)
4. **Alliance badge** (tap to open alliance screen):
   - Shows alliance emblem/flag if in alliance
   - Empty if solo player
   - Tap: Opens Social tab → Alliance sub-tab
5. **Settings gear icon** (right-most):
   - Tap: Opens Settings screen (nested in Social tab per §9.1)

**NOT Included per §9.1** (moved to in-world context or deep screens):
- Shield % / Damage % (shown in combat HUD when engaged, not global top bar)
- Safe Harbor status (shown as minimap badge or contextual alert, not persistent top bar element per Designer spec)

**Accessibility:**
- VoiceOver: "Cash: 245 thousand. Energy: 42 thousand of 65 thousand. Shields: 85 percent, up. Damage: 12 percent. Safe."
- Dynamic Type: Values scale to user's font size preference (iOS Settings → Display → Text Size)
- Contrast: Status strip passes WCAG AA (4.5:1 ratio against background)

### 3.3 Center Canvas (3D Tactical View)

**Rendering:**
- 3D ship model (player's ship, based on Phase 1a `shpclass` 0-9: freighter → dreadnought → cybertron)
- Environment: Starfield background (static or slow-scrolling for performance), planet in background if in orbit
- Contacts: Other ships within range (chevron icons with color-coded ownership: blue=self, green=ally, red=enemy, gray=neutral)
- VFX: Engine trails (particle system), weapon fire (phasor beams, torpedo projectiles), shield impacts (ripple effect), explosions

**Camera:**
- Default: Fixed behind player ship, slight offset for readability
- Rotation: Two-finger drag or gyroscope (opt-in Setting) to rotate camera
- Zoom: Pinch to zoom in/out (constrained to 50%-200% of default)

**Interaction:**
- Tap contact → Select target (highlight with reticle, Target Card slides up)
- Tap empty space → Deselect
- Drag on canvas → Pan camera (ship stays centered, view angle adjusts)
- Long-press contact → Peek info (tooltip: name, class, range, no action)

**Performance:**
- Target 60fps on mid-tier devices (iPhone 12, Samsung Galaxy A series)
- LOD (level of detail): Distant ships render as 2D sprites, close ships as 3D models
- Particle budget: Max 200 particles on-screen (throttle if fps drops below 30)

### 3.4 Minimap (Bottom-Left Corner)

**Size:** 80x80pt square, semi-transparent background
**Content:**
- Sector grid overlay (Phase 1a 30×15 sectors, current sector highlighted)
- Player pip: Blue dot
- Contacts: Red/green/gray dots (enemy/ally/neutral)
- Planets: Small planet icons (color-coded by ownership)
- Fog of war: Dimmed areas outside scan range (Phase 1a hyper-scanner range = 5 sectors)

**Interaction:**
- Tap minimap → Expands to full Sector Grid View (zoom level 2)
- Pinch on minimap → Zoom to Galaxy Overview (zoom level 1)

### 3.5 Contextual Action Stack (Right Edge)

**Design:** Vertical stack of circular buttons (56pt diameter each, iOS standard FAB size), 16pt spacing, aligned to right edge (12pt margin from screen edge)

**Buttons (top to bottom, visibility based on context):**
1. **Scan** (always visible):
   - Icon: 📡 radar dish
   - Tap → Phase 1a `cmd_scan()` → reveals planets/ships in sector
   - Cooldown: 10s (visual: circular timer ring around button)
2. **Fire** (visible when target selected and in weapon range):
   - Icon: 🎯 crosshair
   - Tap → Opens Combat Radial (weapon selector)
   - Badge: Weapon ready indicator (green dot if phasor charged ≥60%, Phase 1a `PMINFIRE=60%`)
3. **Shields** (always visible if ship has shields):
   - Icon: 🛡 shield (glows blue when up)
   - Tap → Toggle shields up/down (Phase 1a `shieldstat`)
   - State color: Green (up), gray (down), red (damaged)
4. **Cloak** (visible if ship has cloak):
   - Icon: 👁 eye
   - Tap → Engage/disengage cloak (Phase 1a `cloak` mechanic)
   - Disabled if cooldown active (grayed out + timer)
5. **Orbit** (visible when near planet, <1000 units distance):
   - Icon: 🪐 planet with ring
   - Tap → Enter orbit (Phase 1a `cmd_orbit()` → sets `where >= 10`)
6. **Dock** (visible when orbiting planet):
   - Icon: ⚓ anchor
   - Tap → Dock at planet (enables trade, transfer, Safe Harbor)

**Haptic Feedback:**
- Button tap: Light haptic (iOS `UIImpactFeedbackGenerator.light`)
- Action success: Medium haptic (e.g., shields up, weapon fired)
- Action failed: Error vibration (3 short pulses, e.g., insufficient energy)

**Accessibility:**
- VoiceOver labels: "Scan button. Reveals contacts in sector. Cooldown: 5 seconds remaining."
- Minimum touch target: 44pt (iOS HIG), buttons spaced to avoid accidental taps
- Color not sole signal: Icons + labels for colorblind users

### 3.6 Bottom Sheet (Selected Target Card)

**Design:** Slide-up panel from bottom, 30% screen height (collapsed) or 60% (expanded), rounded corners, semi-transparent background.

**Collapsed State (Default):**
- Swipe up to expand, swipe down to dismiss
- Content:
  - Target name: "[Enemy Ship Name]"
  - Class icon + label: "Cruiser" (Phase 1a `shpclass`)
  - Range: "4,200 units" (updates live, Phase 1a distance formula `GELIB.C`)
  - Shield %: "72%" (estimated, server-authoritative)
  - Threat badge: "Veteran" (based on Phase 1a `kills` count: <10=Novice, 10-50=Veteran, >50=Deadly)
- Action buttons (horizontal row):
  - **Scan** (reveals full stats: damage %, cargo, owner name)
  - **Fire** (shortcut to Combat Radial)
  - **Retreat** (emergency: engage cloak or warp zipper to escape)

**Expanded State (Swipe Up):**
- Full stats (if scanned):
  - Owner: "[Player Name]" (tap to view profile, if feature exists)
  - Ship class details: "Cruiser — 1200 tons, 50k energy max"
  - Damage %: "18%"
  - Cargo preview: "Estimated 500 gold, 30 missiles" (Phase 1a spy intel or scan guess)
  - Kill count: "42 kills" (Phase 1a `waruptr->kills`)
- Combat history: "Last seen: 2 hours ago attacking your ally [Name]" (optional social feature)
- Actions:
  - **Lock Target** (for torpedoes/missiles, Phase 1a `cmd_lock()`)
  - **Add to Enemies** (bookmark for revenge)
  - **Message** (send DM, if feature exists)

**Empty State (No Target):**
- Collapsed sheet shows: "No target selected. Tap a ship to engage."
- No action buttons visible

---

## 4. Alignment Notes & Open Decisions

### 4.1 Hooks for Designer Loops (Visual Design TBD)

This UX vision defines **interaction patterns, information architecture, and screen flows**. The following are placeholders for Designer collaboration:

1. **Visual Style / Art Direction:**
   - Sci-fi theme: Hard sci-fi (realistic, gritty) vs. space opera (colorful, fantastical)?
   - Ship design aesthetic: Industrial (EVE) vs. sleek (Star Citizen) vs. cartoony (Battlestar Galactica mobile)?
   - Planet rendering: 3D spheres vs. 2D illustrations vs. abstract icons?
   - Color palette: Dark space theme (black/blue/purple) vs. vibrant (neon accents)?

2. **Iconography:**
   - Weapon/item icons: Realistic (photographic missiles) vs. stylized (geometric shapes)?
   - Status icons (shields, energy, damage): Minimalist (single glyph) vs. detailed (illustrated)?
   - Ownership indicators: Color tint only vs. color + shape (ally=circle, enemy=triangle, per accessibility)?

3. **Animation & VFX:**
   - Combat feedback intensity: Subtle (small particles, brief flashes) vs. bombastic (screen shake, explosions filling canvas)?
   - Transition animations: Fast (instant, snappy) vs. smooth (eased, 300ms)?
   - Loading states: Spinners vs. progress bars vs. skeleton screens?

4. **Sound Design:**
   - UI feedback: Clicks, whooshes, confirmation beeps (designer to spec SFX library)
   - Combat sounds: Phasor fire, torpedo launch, explosion, shield impact (asset list TBD)
   - Ambient: Space ambience (engine hum, subtle music) vs. silence (player-choice)?

**Designer Deliverables Needed (Post-Phase 1b):**
- High-fidelity mockups for 5 key screens: Local Space HUD, Planet Detail, Empire Home, Combat Radial, Onboarding Step 2
- Style guide: Color palette (primary/secondary/accent), typography (headers/body/labels), spacing grid (8pt/16pt), button states (default/hover/pressed/disabled)
- Iconography library: 50+ icons for items, actions, statuses (SVG format, @1x/@2x/@3x for retina)
- Animation specs: Transition durations, easing curves (ease-in-out vs. spring), particle counts
- Accessibility audit: Contrast ratios (WCAG AA), VoiceOver labels, colorblind-safe palette

### 4.2 Client Constraints for Stack Architect (Backend/API Surface Notes)

**UX → Backend API Requirements:**

This design assumes the following backend capabilities (Stack Architect to validate feasibility):

1. **Websocket or Push for Real-Time Updates:**
   - UX requires instant notification of sector events (enemy enters range, planet attacked, production complete)
   - HTTP polling every 6s (Phase 1a tick rate) drains battery → need push (websockets, SSE, or FCM/APNs)
   - **API:** `wss://api.ge/v1/sector-events` with subscription per player's active sector

2. **Action Queue with Tick-Based Resolution:**
   - Player taps "Fire" → client sends command instantly, server queues action, resolves at next 6s tick (Phase 1a `warrti()` cadence)
   - **API:** `POST /v1/actions/queue` with params: `{ action: "fire_phasor", target_id: "ship_123", focus: 50 }`
   - Response: `{ queued: true, eta_ms: 4200, tick_id: 42 }` → client shows countdown

3. **Optimistic UI with Rollback:**
   - Client applies actions immediately (fire weapon → show beam VFX), server confirms or rejects at tick boundary
   - **API:** Server sends `tick_result` event via websocket: `{ tick_id: 42, success: true, damage_dealt: 342 }` or `{ success: false, reason: "out_of_range" }`
   - Client rollback on failure: hide damage numbers, show "Miss" or error toast

4. **Interpolated Motion Between Ticks:**
   - Server sends ship position updates every 6s (Phase 1a `moveship()` physics)
   - Client interpolates smooth motion: `lerp(pos_old, pos_new, t / 6000)` for 60fps animation
   - **API:** `GET /v1/sector/:id/state` returns: `{ ships: [{ id, pos, heading, speed, timestamp }], planets: [...] }`

5. **Production ETA Calculations (Client-Side):**
   - Server sends planet production state: `{ item_id: 12, qty: 1240, rate: 30, last_tick_ms: 1694000000000 }`
   - Client calculates ETA: `next_tick_ms = last_tick_ms + 55000` → "Next batch in 22s"
   - No polling needed; client counts down locally, re-sync on tab focus

6. **Offline Safe Harbor State:**
   - Server tracks `player.offline_state` (docked, citadel, open_space)
   - **API:** `POST /v1/player/logout` with param: `{ state: "docked_at_planet", planet_id: "planet_456" }`
   - Server enforces: docked ships invulnerable while offline (Phase 1a §9.2 Option B recommendation)

7. **Map Tile/Sector Streaming:**
   - Client loads only visible sectors (viewport + 1 sector buffer)
   - **API:** `GET /v1/map/sectors?min_x=10&max_x=15&min_y=5&max_y=8` returns: `{ sectors: [...] }`
   - Lazy-load on pan, cache aggressively (1 hour TTL for static sector data)

8. **Auth Session Resume:**
   - Player backgrounds app, returns 5 min later → client resumes session without full re-login
   - **API:** JWT refresh token flow: `POST /v1/auth/refresh` with `refresh_token` → new `access_token`
   - Session timeout: 30 min idle (configurable), after which require re-auth

9. **Deep Links from Push Notifications:**
   - Push notification: "Planet under attack!" → tap → app opens to Planet Detail screen (not home screen)
   - **Deep Link Schema:** `ge://intel/alert/alert_id_123` or universal link `https://ge.app/intel/alert/alert_id_123`
   - Unity handles route parsing, navigates to appropriate screen

10. **Rate Limiting & Anti-Cheat:**
    - Client actions validated server-side (e.g., can't fire phasor if charge <60%)
    - Rate limits: Max 10 actions/second per player (prevent macro spam)
    - **API:** Returns `429 Too Many Requests` if exceeded → client shows cooldown toast

**Stack Architect Open Questions:**
- **Websocket scaling:** How many concurrent connections can FastAPI handle? Need Redis pub/sub for multi-instance deployment?
- **Tick system architecture:** Single global 6s timer or per-sector ticks? How to distribute load across servers?
- **Database choice:** PostgreSQL (relational, Phase 1a Btrieve successor) vs. MongoDB (document store, flexible schema) vs. hybrid (Postgres + Redis cache)?
- **Physics server:** Phase 1a `moveship()` math done in FastAPI (Python slow for real-time) or separate game server (Rust/Go)?
- **Universe size decision:** Keep 30×15 sectors (450 total, small) or expand to 100×50 (5000, Phase 1a §9.1 Option B)? Affects map tile streaming strategy.

### 4.3 Locked Product Decisions (Game Design §8)

**Status: All 7 Phase 1a decisions are now LOCKED per Game Design doc. Monetization locked by Jeremy; remaining six locked by Designer with Empire Lead approval.**

1. **Universe Size (Game Design §8.1 — LOCKED: D+B)**
   - **Decision:** Instanced shards (~100×50 sectors, 5000 total), target 500-1k players/shard
   - **UX Impact:** Need robust search/bookmark (can't pan 5000 sectors on mobile), shard identity UI (show "Galaxy Andromeda"), cross-shard portal events (prestige competition)
   - **UX Requirements:** Galaxy map virtualization (render viewport + buffer), search bar, "My Empire" jump list, shard name badge

2. **Offline Protection (Game Design §8.2 — LOCKED: B+C Hybrid)**
   - **Decision:** Safe Harbor docking (invulnerable at NPC citadels, costs rent) + optional Hire NPC Defenders for planets
   - **UX Impact:** Tutorial MUST explain Safe Harbor before first logout (per §8.2 UX handoff)
   - **UX Requirements:** Safe Harbor status chip (HUD top-right), "Emergency Retreat" button (costs energy), NPC garrison hiring UI in Planet Detail

3. **Combat Pacing (Game Design §8.3 — LOCKED: A keep ~6s)**
   - **Decision:** ~6-second strategic tick for fleet combat (not twitch)
   - **UX Impact:** UI must feel instant (tap Fire → immediate feedback <100ms), mask 6s tick with animations (phasor charges 0-6s, impact at 6s)
   - **UX Anti-Pattern:** Do NOT show "6-second countdown timer" (§6.1 warning — feels turn-based)

4. **Death Penalty (Game Design §8.6 — LOCKED: C insurance)**
   - **Decision:** Insurance system (pay premium → recover 75% cargo), uninsured = 50% loss
   - **UX Impact:** Death screen branches: "Insured: recovered 75%" vs. "Uninsured: lost 50% to [Attacker]"
   - **UX Requirements:** Insurance purchase UI (Fleet screen), renewal reminders (push notification), "Buy Insurance?" CTA in uninsured death screen

5. **PvE vs PvP Balance (Game Design §8.5 — LOCKED: B hybrid)**
   - **Decision:** PvP conquest spine + optional PvE (alien hives, derelicts, anomalies) that feeds PvP economy
   - **UX Impact:** Onboarding explains "PvP sandbox with PvE variety" (not safe PvE endgame)
   - **UX Requirements:** PvE sector markers on map (alien hive icons), co-op mission UI, loot tied to PvP trade economy

6. **Monetization (Game Design §8.4 — LOCKED: B F2P cosmetics, Empire Lead/Jeremy CONFIRMED)**
   - **Decision:** F2P + cosmetics only (ship skins, planet themes, flags, VFX), **NO P2W** production speedups or combat-power IAP
   - **UX Impact:** Cosmetic shop UI (Social tab or dedicated shop button), battle pass (free + premium tracks), seasonal rotations
   - **UX Red Line:** NEVER implement UI for "2x production boost", "+20% weapon damage", energy refills, cargo expansions, or any gameplay-power monetization
   - **Allowed:** Ship skins, planet skylines, empire flags, weapon VFX, warp effects, emotes, HUD themes — purely visual, zero gameplay advantage

7. **Hybrid Strategic Realtime (Game Design §8.7 — LOCKED: A)**
   - **Decision:** Commands instant (tap → <100ms feedback), world resolves at strategic cadence (6s combat, 55s production)
   - **UX Impact:** "Instant input, deliberate resolution" — player perception = real-time, server = strategic tick
   - **UX Requirements:** Optimistic UI (fire weapon → show beam immediately), websocket result at 6s mark, smooth interpolation

**Additional Locked Decisions:**
- **Alliance depth (MVP):** Basic features (chat, shared planets, member roster) per Game Design §5.1
- **NPC density:** Remove legacy throttle, scale up (Game Design §7.3 Kill table)
- **Tutorial:** 90-second interactive (§9.4 anti-pattern: avoid >3min forced tutorial), soft-gated starter sector or dedicated instance
- **Realtime skirmish mode:** Deferred post-MVP (Game Design §11.2)

---

## 5. Summary & Next Steps

### 5.1 What This Document Delivers

**Comprehensive Mobile UX Vision for Galactic Empire (Aligned with Game Design §8 & §9):**
- **Information Architecture:** 4-tab bottom nav (**Map**, **Fleet**, **Empire**, **Social** per §9.1), screen hierarchy for 40+ screens
- **Core Flows:** Galaxy navigation (3 zoom levels), combat presentation (ship-to-ship + planet assault), empire management (production, trade, treasury), onboarding (15-min guided tutorial)
- **HUD Design:** Local Space tactical view with top status strip, center canvas (3D), minimap, contextual action stack, bottom target sheet
- **Session Flexibility:** Micro (2-5 min), standard (10-20 min), deep (30-45 min) play patterns supported
- **Strategic Pacing:** Preserve Phase 1a's 6s combat tick and 55s production cycles, instant UI response via optimistic updates
- **Safe Harbor:** Offline protection via docking (Option B recommendation from Phase 1a §9.2)

**Alignment Hooks:**
- Designer loops: Visual style, iconography, animation, sound (specs TBD, Designer collaboration post-Phase 1b)
- Stack constraints: Websocket push, action queue, interpolated motion, map streaming, auth session resume (backend API requirements documented)
- Open product decisions: Universe size, offline policy, combat pacing, death penalty, PvE/PvP balance, monetization (flagged for Jeremy/Product Lead)

**Grounded in Phase 1a:**
- Every mechanic (14 item types, 6s ticks, 55s production, death penalty, team system, spy mechanics, wormholes) cited from Phase 1a Legacy System Map sections
- KEEP/TRANSFORM/KILL recommendations applied: Preserve strategic depth, replace text commands with touch UI, kill BBS I/O blocking

### 5.2 Deliverables in This PR

1. **`docs/PHASE1B_CLIENT_UX_VISION.md`** (this file)
2. **`docs/PHASE1B_SCREEN_INVENTORY.md`** (companion doc: screen-by-screen inventory, wireframe descriptions, interaction notes)

### 5.3 What's NOT in This Document (Out of Scope)

**Not Included (Design Docs Only, No Implementation):**
- Unity project setup, C# scripts, scene hierarchy
- FastAPI backend code, database schema, API endpoint implementation
- Docker/DevOps configs, CI/CD pipelines
- High-fidelity visual mockups (Designer responsibility)
- Asset lists (3D models, textures, SFX, music)

**Deferred to Future Phases:**
- Phase 2: Advanced alliance features (territory control, alliance wars)
- Phase 3: Realtime skirmish mode (1v1 duels, twitch combat)
- Phase 4: PvE content (alien invasions, derelict stations, co-op raids)
- Phase 5: Monetization (cosmetics shop, battle pass, premium currency UI)

### 5.4 Designer & Stack Architect Action Items

**Designer (Priority 1 for Phase 2):**
1. Review UX vision, flag conflicts or missing considerations
2. Confirm visual style direction (hard sci-fi vs. space opera, dark theme vs. vibrant)
3. Produce high-fidelity mockups for 5 key screens (HUD, Planet Detail, Empire Home, Combat Radial, Onboarding)
4. Deliver style guide (colors, typography, iconography, spacing grid)

**Stack Architect (Priority 1 for Phase 2):**
1. Review backend API requirements (§4.2 Client Constraints)
2. Validate websocket scalability (FastAPI + Redis pub/sub?)
3. Confirm tick system architecture (global 6s timer vs. per-sector ticks)
4. Propose database schema (PostgreSQL for Phase 1a entities: `WARSHP`, `WARUSR`, `GALPLNT`, `GALSECT`)
5. Resolve open questions: universe size (30×15 or expand?), physics server (Python FastAPI or separate Rust/Go?)

**Product Lead / Jeremy (Priority 1 for Phase 2):**
1. Decide open UX assumptions (§4.3): offline policy (A/B/C?), death penalty (50% or insurance?), PvE/PvP balance, monetization model
2. Approve or adjust North Star ("emperor on a phone") and UX pillars (thumb-zone, glanceable status, strategic pacing, session flexibility, Safe Harbor)
3. Confirm Phase 1b approval → green-light Phase 2 (Designer mockups + Stack architecture doc)

---

**End of Phase 1b Client UX Vision.**

**Phase 1b Companion Document:** See `PHASE1B_SCREEN_INVENTORY.md` for full screen-by-screen inventory (40+ screens), wireframe descriptions, interaction notes, accessibility guidance, and empty/error/loading states.
