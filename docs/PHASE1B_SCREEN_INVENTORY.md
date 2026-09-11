# Phase 1b: Screen Inventory – Galactic Empire Mobile Client

**Date:** 2026-09-11  
**Companion to:** `PHASE1B_CLIENT_UX_VISION.md`  
**Aligned with:** `PHASE1B_GAME_DESIGN.md` (PR #2, Designer Mobile UX Contract §9)  
**Target Platform:** iOS + Android (Unity Editor 6000.4.10f1)  
**Scope:** Screen-by-screen inventory, wireframe descriptions, interaction notes, states, accessibility.

---

## Document Purpose

**This Screen Inventory implements the Designer's Mobile UX Contract (Game Design §9)** and extends the UX Vision with detailed per-screen specifications. Navigation follows the locked 4-tab structure (**Map**, **Fleet**, **Empire**, **Social** per §9.1), HUD elements match §9.1 exactly, and push triggers implement §9.3.

This document provides a **comprehensive inventory of every screen** in the Galactic Empire mobile client, including:
- Screen ID, name, navigation path
- Primary user goal
- Key UI components (layout, elements, actions)
- Entry/exit conditions
- Empty/error/loading states
- Push notification / deep link support
- Accessibility notes (Dynamic Type, VoiceOver, one-handed use, color-independence)
- ASCII or bullet-point wireframe descriptions
- Interaction notes (gestures, haptics, confirmations)

**Minimum Coverage (40+ Screens):**
- Boot / Auth / Character Select
- Onboarding steps (5 screens)
- Galaxy overview, Sector view, Local space HUD (3 map zoom levels)
- Target sheet, Combat radial, Killmail, Salvage
- Empire home, Planet list, Planet detail, Production editor, Trade dock sheet
- Fleet hangar, Ship detail/loadout, Travel order sheet
- Intel inbox, Alert detail, Spy report
- Team/Alliance hub, Chat (sector / alliance), Leaderboard
- Safe Harbor explainer, Settings, Legal/account
- Empty states for no planets / no mail / fog of war

---

## Screen Inventory Table of Contents

**Aligned with Game Design §9 4-Tab Navigation: Map, Fleet, Empire, Social**

1. [Boot & Auth Screens (3)](#1-boot--auth-screens)
2. [Onboarding Screens (5)](#2-onboarding-screens)
3. [Map Tab Screens (8)](#3-map-tab-screens) — Renamed from "Galaxy" per Designer §9.1
4. [Empire Tab Screens (6)](#4-empire-tab-screens)
5. [Fleet Tab Screens (5)](#5-fleet-tab-screens)
6. [Social Tab Screens (8)](#6-social-tab-screens) — Includes Inbox (fka Intel) + Leaderboard + Alliance per §9.2
7. [Overlay & Modal Screens (6)](#7-overlay--modal-screens)
8. [Settings & Legal Screens (3)](#8-settings--legal-screens)

**Total Screens:** 44 (consolidated: Intel folded into Social per Designer spec)

---

## 1. Boot & Auth Screens

### 1.1 Splash Screen (ID: `BOOT_001`)

**Name:** Splash / Loading  
**Nav Path:** App launch → auto-advance  
**Primary Goal:** Load assets, establish server connection, brand impression

**Key Components:**
- Galactic Empire logo (centered, animated fade-in)
- Tagline: "Command Your Destiny" (subtitle, fades in 0.5s after logo)
- Loading progress bar (bottom, 20% height from bottom edge)
- Version number (bottom-right corner, small text: "v1.0.0 (build 42)")

**Wireframe (ASCII):**
```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│          ⭐ GALACTIC EMPIRE ⭐       │
│        "Command Your Destiny"       │
│                                     │
│                                     │
│  [████████░░░░░░░░░░] 45%          │
│                                     │
│                       v1.0.0 (42)   │
└─────────────────────────────────────┘
```

**Interaction:**
- No user input; auto-advance when assets loaded (target: <3s cold start)
- If load fails: Error state (see below)

**Entry:** App launch (cold start or resume from terminated)  
**Exit:** Auto-navigate to Login (if no saved session) or Local Space HUD (if session valid)

**States:**
- **Loading:** Progress bar animates 0→100%
- **Error:** "Connection failed. Retry?" with Retry button (haptic: error vibration)
- **Offline:** "No internet. Playing offline limited." with Continue button (gray out multiplayer features)

**Push/Deep Link:** None (launch screen)

**Accessibility:**
- VoiceOver: "Galactic Empire. Loading game assets. 45 percent complete."
- No critical actions (skip button optional for advanced users: long-press logo → skip to login)

---

### 1.2 Login Screen (ID: `AUTH_001`)

**Name:** Login / Sign In  
**Nav Path:** Splash → auto or manual logout → here  
**Primary Goal:** Authenticate user, restore session

**Key Components:**
- App logo (top third, smaller than splash)
- Email input field (standard iOS/Android text input, keyboard type: email)
- Password input field (secure entry, show/hide password toggle)
- "Sign In" button (primary CTA, full width, 56pt height)
- "Forgot Password?" link (secondary, below Sign In)
- "Create Account" button (tertiary, bottom)
- Social OAuth buttons (optional): "Sign in with Google" / "Apple" (iOS only)

**Wireframe:**
```
┌─────────────────────────────────────┐
│         ⭐ GALACTIC EMPIRE           │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Email                       │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ Password           [👁 Show] │   │
│  └─────────────────────────────┘   │
│                                     │
│  [     Sign In     ]                │
│  Forgot Password?                   │
│                                     │
│  [   Continue with Google   ]       │
│  [   Continue with Apple    ]       │
│                                     │
│  [    Create Account    ]           │
└─────────────────────────────────────┘
```

**Interaction:**
- Tap email/password fields → keyboard appears (safe area adjusted for keyboard height)
- Tap "Sign In" → Loading spinner on button → Navigate to Character Select or Local Space HUD
- Tap "Forgot Password" → Modal: email input → "Send Reset Link" → Toast: "Check your email"
- Tap social OAuth → Platform OAuth flow (Google/Apple SDK) → auto-create account if first-time → Navigate

**Entry:** Splash (no session) or manual logout  
**Exit:** Success → Character Select (if multi-character) or Local Space HUD (resume session)

**States:**
- **Default:** Empty fields, Sign In button enabled (grayed if fields empty, validation client-side)
- **Loading:** Button shows spinner, fields disabled
- **Error:** Toast or inline error below button: "Invalid credentials" or "Network error. Retry?"
- **Offline:** "No internet. Sign in unavailable." with "Play Offline Demo" button (limited single-player mode, optional)

**Push/Deep Link:** 
- Deep link from email verification: `ge://auth/verify?token=abc123` → auto-login

**Accessibility:**
- VoiceOver: "Email field. Password field. Sign In button."
- Dynamic Type: Text scales to user preference (Large Text support)
- One-handed: All inputs within thumb zone (bottom 2/3 of screen)
- Contrast: WCAG AA compliance (4.5:1 ratio for text on background)

---

### 1.3 Character Select Screen (ID: `AUTH_002`)

**Name:** Character Select (Optional, Future Feature)  
**Nav Path:** Login success → here (if multiple commanders per account)  
**Primary Goal:** Choose active commander/profile

**Key Components:**
- "Select Commander" title (top)
- List of commanders (scrollable, 1-3 per account):
  - Commander card: Avatar, name, rank, last played timestamp, primary ship class
- "Create New Commander" button (bottom, if <3 commanders)
- "Logout" link (top-right)

**Wireframe:**
```
┌─────────────────────────────────────┐
│  Select Commander          [Logout] │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 👤 Cmdr SwiftNova           │   │
│  │ Rank: Captain | Dreadnought │   │
│  │ Last played: 2 hours ago    │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ 👤 Cmdr DarkStar            │   │
│  │ Rank: Admiral | Cruiser     │   │
│  │ Last played: 3 days ago     │   │
│  └─────────────────────────────┘   │
│                                     │
│  [ + Create New Commander ]         │
└─────────────────────────────────────┘
```

**Interaction:**
- Tap commander card → Confirm modal: "Play as [Name]?" → Navigate to Local Space HUD (load that commander's session)
- Tap "Create New" → Navigate to Onboarding (Create Commander step)

**Entry:** Login success (if account has >1 commander)  
**Exit:** Commander selected → Local Space HUD

**States:**
- **Default:** List of commanders
- **Empty (New Account):** Auto-skip to Onboarding (no select screen)
- **Loading:** Spinner while fetching commanders from server

**Push/Deep Link:** None (internal flow)

**Accessibility:**
- VoiceOver: "Commander SwiftNova. Rank Captain. Dreadnought. Last played 2 hours ago."

---

## 2. Onboarding Screens

### 2.1 Intro Cinematic (ID: `ONBOARD_001`)

**Name:** Intro Cinematic  
**Nav Path:** First launch after character creation → auto-play  
**Primary Goal:** Establish fantasy hook, set year 3250 space conquest theme

**Key Components:**
- Full-screen video or animated sequence (15 seconds):
  - Frame 1: Star field, text overlay: "Year 3250"
  - Frame 2: Fleet battle (explosions, ship silhouettes)
  - Frame 3: Planet colonies (domed cities, production facilities)
  - Frame 4: Gold piles, scoreboard rising
  - Frame 5: "Command your destiny."
- "Skip" button (top-right, small, always visible)
- Auto-advance to Create Commander after 15s

**Wireframe:**
```
┌─────────────────────────────────────┐
│                             [Skip]  │
│                                     │
│        [  VIDEO / ANIMATION  ]      │
│          Year 3250 ...              │
│        Fleet battles, colonies      │
│                                     │
└─────────────────────────────────────┘
```

**Interaction:**
- Tap "Skip" → Immediate jump to Create Commander
- Auto-advance at end → Create Commander

**Entry:** First launch or explicitly requested from Settings → Help → Replay Tutorial  
**Exit:** Create Commander screen

**States:**
- **Playing:** Video renders, skip button visible
- **Skipped:** Immediate transition (no fade, fast exit)

**Push/Deep Link:** None

**Accessibility:**
- VoiceOver narration: Pre-recorded audio describing cinematic content
- Closed captions: Text overlay for deaf/hard-of-hearing users (toggle in Settings)

---

### 2.2 Create Commander (ID: `ONBOARD_002`)

**Name:** Create Commander  
**Nav Path:** Intro Cinematic → here, or Character Select → Create New  
**Primary Goal:** Personalize player identity

**Key Components:**
- "Create Your Commander" title (top)
- Avatar picker (horizontal scrollable row, 6-8 preset portraits):
  - Tap to select, selected portrait highlighted with border
- Name input field:
  - Placeholder: "Commander Name"
  - Random name generator button (🎲 dice icon) → suggests names like "Cmdr SwiftNova", "Cmdr IronFist"
- "Confirm" button (bottom, primary CTA)

**Wireframe:**
```
┌─────────────────────────────────────┐
│      Create Your Commander          │
│                                     │
│  Avatar:                            │
│  [👤] [👤] [👤] [👤] [👤] [👤]      │
│   ↑ selected                        │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Commander Name     [🎲 Dice]│   │
│  └─────────────────────────────┘   │
│                                     │
│  [       Confirm       ]            │
└─────────────────────────────────────┘
```

**Interaction:**
- Swipe avatar row left/right to browse
- Tap dice → Random name populates field (with animation: text scrambles then settles)
- Tap "Confirm" → Validation (name 3-20 chars, no profanity check client-side) → Navigate to Name Starter Ship

**Entry:** Intro Cinematic or Character Select → Create New  
**Exit:** Name Starter Ship

**States:**
- **Default:** Empty name, random avatar pre-selected
- **Error:** Inline error below name field: "Name too short" or "Name taken" (server check on confirm)
- **Loading:** Confirm button shows spinner

**Push/Deep Link:** None

**Accessibility:**
- VoiceOver: "Avatar 1 of 8. Dice button: generate random name."
- Dynamic Type: Name field text scales

---

### 2.3 Name Starter Ship (ID: `ONBOARD_003`)

**Name:** Name Starter Ship  
**Nav Path:** Create Commander → Confirm → here  
**Primary Goal:** Personalize starter ship (Phase 1a class 0 light freighter)

**Key Components:**
- "Name Your Ship" title
- 3D ship model preview (center, rotating slowly, light freighter class 0)
- Name input field (pre-filled with random suggestion: "Starfire", "Nomad", "Aurora")
- "Confirm" button (bottom)

**Wireframe:**
```
┌─────────────────────────────────────┐
│         Name Your Ship              │
│                                     │
│           🚀                        │
│      [3D Ship Model]                │
│        (rotating)                   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Ship Name                   │   │
│  └─────────────────────────────┘   │
│                                     │
│  [       Confirm       ]            │
└─────────────────────────────────────┘
```

**Interaction:**
- Edit ship name (optional, default is fine)
- Tap "Confirm" → Brief loading (server creates player account, ship, spawns in tutorial sector) → Fade to Tutorial Step 1 (Learn HUD)

**Entry:** Create Commander confirmed  
**Exit:** Tutorial Step 1 (Learn HUD) in Local Space

**States:**
- **Default:** Random name suggested
- **Loading:** Spinner overlay while server initializes player (1-2s)

**Push/Deep Link:** None

**Accessibility:**
- VoiceOver: "Ship name field. Light Freighter model preview."

---

### 2.4 Tutorial: Learn HUD (ID: `ONBOARD_004`)

**Name:** Tutorial Step 1 — Learn HUD  
**Nav Path:** Name Starter Ship → Confirm → spawn in Local Space with coach marks  
**Primary Goal:** Teach HUD elements (status strip, minimap, action buttons)

**Key Components:**
- Local Space HUD (full screen, player ship at center, tutorial sector 0,0)
- Coach marks (sequential, dismissable):
  1. Points to top status strip: "Monitor shields and energy here"
  2. Points to minimap: "Your sector position"
  3. Points to action stack (right edge): "Contextual actions"
- "Got it" button (bottom-center, advances to next coach mark)
- Objective banner (top): "Learn the HUD" with progress indicator (1/5 steps)

**Wireframe:**
```
┌─────────────────────────────────────┐
│ [Objective: Learn HUD  1/5]         │
│ ⚡ ₡10k  🔋 50k  🛡 100%  💔 0%     │
│       👆 Monitor shields here       │
│                                     │
│         🚀 (Your Ship)              │
│                                     │
│  [Minimap]                          │
│                                     │
│  [       Got it       ]             │
└─────────────────────────────────────┘
```

**Interaction:**
- Coach marks appear one at a time (3 total)
- Tap "Got it" → Next coach mark → After coach mark 3 → Auto-advance to Tutorial Step 2 (First Scan)

**Entry:** Name Starter Ship confirmed  
**Exit:** Tutorial Step 2 (First Scan)

**States:**
- **Coach Mark Active:** Screen dimmed except highlighted element, tooltip with arrow
- **Skipped:** "Skip Tutorial" button (top-right) → Warning dialog → Confirm → Jump to full game (no rewards)

**Push/Deep Link:** None

**Accessibility:**
- VoiceOver: Reads coach mark text aloud automatically
- Haptic: Light tap on coach mark appear

---

### 2.5 Tutorial: First Scan → Claim → Produce → Trade → Combat (ID: `ONBOARD_005` - `009`)

**Consolidated Wireframe Notes for Tutorial Steps 2-6:**

Each tutorial step follows similar structure:
- Objective banner (top): "Scan for planets" / "Claim your first planet" / etc.
- Highlighted UI element (button pulses or glows)
- Instructional text (non-blocking, dismissable card at bottom)
- Auto-advance when objective complete (e.g., scan executed → next step unlocks)

**Step Breakdown:**
- **Step 2 (Scan):** Scan button pulses → Player taps → Planets revealed → Step 3
- **Step 3 (Claim):** Navigate to neutral planet → Orbit → Claim button highlighted → Tap → Planet owned → Step 4
- **Step 4 (Produce):** Planet Detail auto-opens → Production Grid, Gold row highlighted → Set rate slider → Confirm → Step 5
- **Step 5 (Trade):** Navigate to NPC trade station → Dock → Sell gold → Earn cash → Step 6
- **Step 6 (Combat):** Friendly NPC appears → Auto-locked → Fire button highlighted → Fire phasor → NPC dies → Loot salvage → Step 7

**Step 7: Safe Harbor Intro (ID: `ONBOARD_010`)**
- Safe Harbor chip pulses
- Tap chip → Explainer modal (see §8.1 Safe Harbor Explainer)
- Dock at planet → Green "Safe" badge → "Finish Tutorial" button → Tutorial complete

**Accessibility:** All steps narrated via VoiceOver, haptic on objective complete (medium impact)

---

## 3. Map Tab Screens

**Designer Note:** "Map" tab naming per Game Design §9.1 (replaces "Galaxy" from earlier drafts). Covers galaxy overview, sector grid, local space HUD, and all navigation/combat screens.

### 3.1 Galaxy Overview (ID: `MAP_001`)

**Name:** Galaxy Overview (Strategic Map, Zoom Level 1)  
**Nav Path:** Tap **Map** tab (bottom nav) → Default view if no prior zoom state  
**Primary Goal:** Strategic planning, find targets, bookmark locations, navigate sharded universe (~100×50 sectors per Game Design §8.1)

**Key Components:**
- Top-down grid view (30×15 sectors, or larger if Phase 1a §9.1 expanded)
- Sector tiles:
  - Color-tinted by ownership (blue=self, green=ally, red=enemy, gray=neutral)
  - Optional threat heat overlay (toggle button top-right): Red intensity = enemy fleet density
- Bookmarks/pins: Star icon on owned planets, flag icon on team strongholds
- Fog of war: Unexplored sectors dimmed (Phase 1a scan mechanics)
- Search bar (top): "Search planets, players, sectors"
- Zoom controls (bottom-right): Pinch or +/- buttons
- "My Empire" quick-jump button (top-left): List of owned planets → tap to fly

**Wireframe:**
```
┌─────────────────────────────────────┐
│ [🏠 My Empire]  [Search...] [🔥Heat]│
│                                     │
│  ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐  │
│  │░│░│░│█│█│░│░│░│░│░│░│░│░│░│░│  │ (30 cols)
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤  │
│  │░│⭐│░│░│░│█│░│░│░│░│░│░│░│░│░│  │ (15 rows)
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤  │
│  │░│░│░│░│░│░│░│█│░│░│░│░│░│░│🚩│  │
│  └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘  │
│                             [+ -]   │
└─────────────────────────────────────┘
 Legend: ░=fog █=owned ⭐=bookmark 🚩=team
```

**Interaction:**
- **Pinch in/out:** Zoom between Galaxy ↔ Sector ↔ Local
- **Tap sector:** Jump to Sector Grid View (zoom level 2)
- **Long-press sector:** Peek intel tooltip (planet count, ownership, threat)
- **Tap bookmark:** Fly to bookmarked location
- **Search:** Type planet/player name → Autocomplete results → Tap result → Navigate

**Entry:** Galaxy tab tap (bottom nav)  
**Exit:** Tap sector → Sector Grid View, or switch tab

**States:**
- **Default:** Map rendered, fog of war active (shard size ~100×50 per §8.1, virtualized rendering)
- **Loading (First Time):** "Loading galaxy..." spinner over blank grid
- **Empty (New Player):** Mostly fog (gray), tutorial sector or starter zone highlighted with pulsing border
- **Threat Heat ON:** Red overlay intensity on enemy-dense sectors
- **Shard Identity:** Shard name badge (e.g., "Galaxy Andromeda") top-left per §8.1

**Push/Deep Link:** 
- Deep link from push: `ge://map/sector/12/5` → Auto-navigate to sector 12,5

**Accessibility:**
- VoiceOver: "Map view. Shard Galaxy Andromeda. Sector 12,5: 3 planets, ownership neutral, threat low."
- Pan gesture alternative: D-pad overlay (optional, Settings → Accessibility) for non-pinch navigation
- Contrast: High-contrast mode (Settings) increases sector border thickness

---

### 3.2 Sector Grid View (ID: `MAP_002`)

**Name:** Sector Grid View (Zoom Level 2)  
**Nav Path:** Galaxy Overview → Tap sector → here  
**Primary Goal:** See sector contents (planets, ships, wormholes)

**Key Components:**
- Sector ID (top-left): "Sector 12,5"
- Planetary objects (0-9 per Phase 1a `MAXPLANETS=9`):
  - Planet spheres with environment/resource color coding
  - Wormholes as swirling portal icons
- Ship contacts:
  - Chevron icons with ownership color (blue/green/red/gray)
  - Class icon (frigate/cruiser/dreadnought silhouette)
- Range rings around player ship (scan range, weapon range, concentric circles)
- Object labels (tap planet/ship → name badge pops up)
- "Zoom to Local" button (bottom-center, or double-tap planet)

**Wireframe:**
```
┌─────────────────────────────────────┐
│ ← Sector 12,5                       │
│                                     │
│      🪐 (Planet A)                  │
│         "Kepler-442b"               │
│                                     │
│  👾 (Enemy Ship)    🚀 (Your Ship)  │
│                                     │
│      🌀 (Wormhole)                  │
│                                     │
│      [   Zoom to Local   ]          │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap planet:** Detail card slides up (mini Planet Detail)
- **Tap ship:** Opens Target Sheet (§3.4)
- **Double-tap planet:** Enter orbit (if in range) or Local Space zoom
- **Long-press object:** Peek intel (distance, ownership)
- **Pinch out:** Zoom to Local Space (zoom level 3)
- **Pinch in:** Zoom out to Galaxy Overview (zoom level 1)

**Entry:** Galaxy Overview → Tap sector  
**Exit:** Zoom to Local Space, or back to Galaxy

**States:**
- **Default:** Sector rendered with objects
- **Empty Sector:** "Unexplored sector. Scan to reveal." message (if fog of war active)
- **Wormhole Hidden:** If Phase 1a `visible=false`, wormhole not shown until player enters sector and scans

**Push/Deep Link:** 
- `ge://map/sector/12/5/planet/3` → Jump to sector, highlight planet 3

**Accessibility:**
- VoiceOver: "Sector 12,5 contains 3 planets and 1 wormhole. Your ship is here."

---

### 3.3 Local Space HUD (ID: `MAP_003`)

**Name:** Local Space HUD (Zoom Level 3, Tactical Combat View)  
**Nav Path:** Sector Grid → Pinch out, or Galaxy tab default if mid-session  
**Primary Goal:** Tactical control (navigate, combat, scan, orbit)

**Key Components:**
- See §3 HUD Design in UX Vision doc for full detail
- Top status strip: Cash, energy, shields, damage, Safe Harbor chip
- Center canvas: 3D ship + contacts (enemies, planets, salvage)
- Minimap (bottom-left corner): Sector pip
- Action stack (right edge): Scan, Fire, Shields, Cloak, Orbit, Dock
- Bottom sheet: Selected target card (if target selected)

**Wireframe:**
```
┌─────────────────────────────────────┐
│ ⚡₡245k 🔋42k 🛡85% 💔12% [🟢Safe] │
├─────────────────────────────────────┤
│                                     │
│         🚀 (Your Ship)              │  [📡Scan]
│                                     │  [🎯Fire]
│   👾 (Enemy Ship)                   │  [🛡Shields]
│                                     │  [👁Cloak]
│  [Minimap]                          │  [🪐Orbit]
│   📍                                │
├─────────────────────────────────────┤
│ Target: Enemy Ship | Range: 4.2k   │
│ [Scan] [Fire] [Retreat]             │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap contact:** Select target → Bottom sheet slides up
- **Tap action button (Fire):** Opens Combat Radial (§3.5)
- **Drag canvas:** Pan camera (ship stays centered)
- **Pinch in:** Zoom out to Sector Grid View
- **Tap minimap:** Expand to Sector Grid

**Entry:** Galaxy tab (default if mid-session), Sector Grid → zoom in, or deep link  
**Exit:** Switch tab or zoom out

**States:**
- **Default:** Ship + contacts rendered
- **Empty Sector:** "No contacts detected. Scan to reveal."
- **Combat Active:** Screen vignette (red pulse if taking damage)
- **Docked:** Canvas shows planet surface or station interior (simplified, or just text: "Docked at [Planet Name]")

**Push/Deep Link:** 
- `ge://map/local` → Jump to Local Space (resume last position)
- Push: "Enemy detected!" → Tap → Local Space, enemy auto-selected

**Accessibility:**
- VoiceOver: "Local space. Your ship at center. Enemy ship 4.2 kilometers south."
- Haptic: Medium impact when target selected, heavy impact when taking damage

---

### 3.4 Target Sheet (ID: `MAP_004`)

**Name:** Target Sheet (Slide-Up Modal)  
**Nav Path:** Local Space HUD → Tap contact → here  
**Primary Goal:** View target details, initiate combat actions

**Key Components:**
- Target name (top, large text)
- Class icon + label (e.g., "Cruiser")
- Range readout (updates live, e.g., "4,200 units")
- Shield % (estimated, progress bar)
- Threat badge ("Novice" / "Veteran" / "Deadly", based on kills)
- Action buttons (horizontal row):
  - **Scan** (reveal full stats)
  - **Fire** (open Combat Radial)
  - **Retreat** (emergency exit)
- Expand handle (top-center, drag up to see full stats)

**Wireframe (Collapsed):**
```
┌─────────────────────────────────────┐
│ ═══════ (drag handle) ═══════       │
│ Enemy Ship — Cruiser   [Veteran]    │
│ Range: 4,200 units                  │
│ Shields: ████████░░ 80%             │
│                                     │
│ [Scan] [Fire] [Retreat]             │
└─────────────────────────────────────┘
```

**Wireframe (Expanded, after scan):**
```
┌─────────────────────────────────────┐
│ ═══════ (drag handle) ═══════       │
│ Enemy Ship — Cruiser   [Veteran]    │
│ Owner: PlayerName123                │
│ Range: 4,200 units                  │
│ Shields: 80% | Damage: 18%          │
│ Cargo: ~500 gold, 30 missiles       │
│ Kills: 42                           │
│                                     │
│ [Lock Target] [Add to Enemies] [✉️] │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap Scan:** Server request → Updates sheet with full stats (if scan succeeds, Phase 1a `cmd_scan()`)
- **Tap Fire:** Opens Combat Radial (§3.5)
- **Tap Retreat:** Engage cloak (if available) or warp zipper (instant escape) → Closes sheet
- **Drag handle down:** Dismiss sheet (deselect target)
- **Drag handle up:** Expand to full stats (if scanned)

**Entry:** Local Space HUD → Tap contact  
**Exit:** Swipe down to dismiss, or tap X button (top-right)

**States:**
- **Collapsed (Default):** Minimal info (name, class, range, shields)
- **Expanded (Scanned):** Full stats visible
- **Out of Range:** Action buttons grayed (except Retreat), tooltip: "Move closer to engage"
- **Target Destroyed:** Sheet auto-closes, salvage pin appears on map

**Push/Deep Link:** 
- `ge://map/local/target/ship_123` → Auto-select target, open sheet

**Accessibility:**
- VoiceOver: "Target: Enemy Ship. Cruiser class. Range 4,200 units. Shields 80%. Scan button."
- Haptic: Light tap on sheet open/close

---

### 3.5 Combat Radial (ID: `MAP_005`)

**Name:** Combat Radial (Weapon Selector)  
**Nav Path:** Target Sheet → Tap Fire → here, OR Local Space action stack → Tap Fire → here  
**Primary Goal:** Choose weapon, fire at target

**Key Components:**
- Radial menu centered on target ship (or screen center if off-screen target)
- 4-6 weapon options (based on ship loadout, Phase 1a weapons):
  - **Phasor** (infinite ammo, charge ring 0-100%)
  - **Torpedo** (lock-on, shows ammo count: "12")
  - **Missile** (faster lock-on, ammo count: "8")
  - **Hyper-Phasor** (wide beam, high energy, cooldown timer if recently fired)
  - **Mine** (deploy trap, ammo count)
  - **Decoy** (deploy distraction, ammo count)
- Each option:
  - Icon (weapon silhouette)
  - Ammo/charge indicator
  - Disabled if insufficient energy/ammo (grayed, shake animation on tap)
- Cancel (tap outside radial or X button center)

**Wireframe:**
```
┌─────────────────────────────────────┐
│                                     │
│         [Phasor 🎯 85%]             │
│  [Torp 🚀x12]     [Missile 💥x8]    │
│         [ ✕ Cancel ]                │
│  [Mine 💣x3]      [Decoy 🎈x5]      │
│                                     │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap weapon (Phasor):** 
  - Auto-aim default: Instant fire → Optimistic beam VFX → Server resolves at tick → Damage numbers
  - Precision mode (drag after tap): Drag radial to adjust aim offset (±degrees) → Release to fire → Bonus damage if hit
- **Tap Torpedo/Missile:** 
  - Check if target locked (Phase 1a `cmd_lock()`)
  - If not locked: "Lock target first" toast → Auto-lock (1s animation) → Fire
  - Projectile launches, client interpolates smooth motion between ticks
- **Tap Mine/Decoy:** Confirm modal: "Deploy [Item]?" → Confirm → Item placed at ship position → Radial closes
- **Tap outside or Cancel:** Close radial (no action)

**Entry:** Target Sheet → Fire, OR Action stack → Fire (if target selected)  
**Exit:** Weapon fired → Close radial, OR Cancel → Close

**States:**
- **Default:** All equipped weapons shown, available ones enabled
- **Insufficient Energy:** Phasor/Hyper-Phasor grayed, tooltip: "Recharge energy to fire"
- **No Ammo:** Torpedo/Missile grayed, tooltip: "Restock at trade station"
- **Cooldown Active:** Hyper-Phasor shows timer ring, tooltip: "Ready in 12s"

**Push/Deep Link:** None (in-session modal)

**Accessibility:**
- VoiceOver: "Weapon selector. Phasor ready, 85% charge. Torpedo, 12 remaining. Select weapon."
- Haptic: Medium impact on weapon select, heavy impact on fire

---

### 3.6 Killmail Screen (ID: `MAP_006`)

**Name:** Killmail (Death Summary Modal)  
**Nav Path:** Local Space HUD → Ship destroyed (damage 100%) → auto-appear  
**Primary Goal:** Inform player of death, show losses, offer respawn/revenge

**Key Components:**
- Full-screen overlay (dark vignette, explosion animation fades out)
- "You were destroyed!" title (large, red)
- Attacker info:
  - Name, ship class, kill count (for context)
  - Avatar or ship thumbnail
- Loss summary:
  - "50% of cargo dropped" (Phase 1a death penalty)
  - Itemized list: Gold, missiles, torpedoes (qty lost)
- Salvage pin: "Wreckage at Sector [X,Y]" (tap to navigate)
- Action buttons:
  - **Respawn** (primary, green CTA) → Neutral zone 0,0 with class 0 ship
  - **Revenge** (secondary, red) → Adds attacker to enemies list, marks on map
  - **Report** (tertiary, if griefing, optional) → Opens report form

**Wireframe:**
```
┌─────────────────────────────────────┐
│ 💥 You were destroyed!              │
│                                     │
│ Killed by: PlayerName123            │
│ Ship: Dreadnought | Kills: 56      │
│                                     │
│ Losses:                             │
│  - 500 gold (50% of 1,000)          │
│  - 15 missiles (50% of 30)          │
│  - 5 torpedoes (50% of 10)          │
│                                     │
│ Wreckage at Sector 12,5 [Navigate] │
│                                     │
│ [   Respawn   ] [  Revenge  ]       │
│              [Report]               │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap Respawn:** 
  - Brief loading (3s, "Preparing new ship...")
  - Fade to Local Space HUD at neutral zone (0,0), new class 0 light freighter
  - Tutorial coach mark: "Rebuild via trade or conquest"
- **Tap Revenge:** 
  - Adds attacker to enemies list (Intel tab → Enemies section)
  - If attacker visible on map, red skull marker added
  - Toast: "Added to enemies. Hunt them down."
  - Then respawn
- **Tap Wreckage Navigate:** 
  - Sets waypoint to death location
  - Respawn → Auto-pilot to wreckage (if not looted)

**Entry:** Local Space HUD → Ship damage reaches 100%  
**Exit:** Respawn → Local Space at 0,0

**States:**
- **Default:** Attacker info + loss summary
- **Salvage Already Looted:** "Wreckage looted by [Player]" (if attacker or others scavenged)
- **Assisted Suicide (No Attacker):** "Destroyed by environment" (e.g., mine, gravity, rare)

**Push/Deep Link:** 
- `ge://intel/killmail/km_123` → Re-open past killmail from Intel tab

**Accessibility:**
- VoiceOver: "You were destroyed. Killed by PlayerName123. Lost 500 gold. Respawn button."
- Haptic: Heavy impact on death (3-pulse pattern), light tap on respawn

---

### 3.7 Salvage Pin / Loot (ID: `MAP_007`)

**Name:** Salvage / Loot Screen (Modal or Inline)  
**Nav Path:** Local Space HUD → Tap wreckage icon on map → here  
**Primary Goal:** Collect dropped cargo from destroyed ships

**Key Components:**
- "Salvage Wreckage" title
- List of items (scrollable if many):
  - Item icon + name + qty (e.g., "Gold: 250", "Missiles: 15")
  - Checkbox (select items to loot, or "Take All" button)
- Weight check: "480 / 1200 tons" (Phase 1a `calcweight()`)
- Action buttons:
  - **Take All** (primary, if within weight limit)
  - **Take Selected** (if checkboxes used)
  - **Leave** (cancel, close modal)

**Wireframe:**
```
┌─────────────────────────────────────┐
│ Salvage Wreckage                    │
│ Destroyed: EnemyShip42              │
│                                     │
│ ☑ Gold: 250                         │
│ ☑ Missiles: 15                      │
│ ☑ Torpedoes: 5                      │
│ ☐ Flux Pods: 10                     │
│                                     │
│ Weight: 320 / 1200 tons             │
│                                     │
│ [  Take All  ] [  Leave  ]          │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap "Take All":** 
  - If within weight: Instant transfer to ship cargo → Toast: "Looted 250 gold, 15 missiles" → Close modal
  - If overweight: Warning: "Cargo full. Select items or leave some." → Enable checkboxes
- **Tap checkboxes:** Select specific items → "Take Selected" button enabled
- **Tap "Leave":** Close modal, wreckage remains (for 10 min or until looted empty)

**Entry:** Local Space HUD → Tap salvage pin (golden cargo icon)  
**Exit:** Items looted → Modal closes, pin removed from map

**States:**
- **Default:** List of lootable items
- **Empty Wreckage:** "Wreckage already looted" message (if another player got there first)
- **Expired:** Wreckage auto-removed after 10 min (server cleanup) → Toast: "Wreckage expired"

**Push/Deep Link:** 
- `ge://map/local/salvage/wreck_456` → Navigate to wreckage, auto-open loot modal

**Accessibility:**
- VoiceOver: "Salvage wreckage. Gold 250. Missiles 15. Take all button."
- Haptic: Medium impact on loot success

---

### 3.8 Travel Order Sheet (ID: `MAP_008`)

**Name:** Travel Order / Autopilot  
**Nav Path:** Local Space or Sector Grid → Tap destination → "Travel Here" → here  
**Primary Goal:** Set destination, choose drive mode, monitor ETA

**Key Components:**
- "Travel to [Destination]" title
- Destination info: Name, coordinates, distance (sectors or units)
- ETA calculation (Phase 1a physics: `speed * sin/cos(heading)`, displayed as human-readable "3 min 24s")
- Drive mode selector (radio buttons or tabs):
  - **Impulse** (default, normal speed ~9 warp, Phase 1a standard)
  - **Hyperspace** (faster, no combat allowed, Phase 1a `where=1`)
  - **Warp Zipper** (instant teleport, consumes zipper item, Phase 1a)
- Energy cost preview: "Cost: 5,000 energy" (calculated from distance)
- Confirm button: "Start Autopilot"
- Cancel button

**Wireframe:**
```
┌─────────────────────────────────────┐
│ Travel to Kepler-442b               │
│ Sector 12,5 — Planet 3              │
│ Distance: 8.4 sectors               │
│                                     │
│ Drive Mode:                         │
│ ⦿ Impulse     ETA: 3m 24s           │
│ ○ Hyperspace  ETA: 1m 12s           │
│ ○ Warp Zipper ETA: Instant (1x)    │
│                                     │
│ Energy Cost: 5,000 ⚡               │
│                                     │
│ [ Start Autopilot ] [ Cancel ]      │
└─────────────────────────────────────┘
```

**Interaction:**
- **Select drive mode:** Tap radio button → ETA updates
- **Tap "Start Autopilot":** 
  - Server validates (sufficient energy, zipper if chosen)
  - Ship begins moving (client interpolates motion smoothly)
  - ETA chip appears near minimap (persistent, shows countdown: "Arrives in 2m 58s")
  - Modal closes
- **Interrupt:** 
  - If enemy enters range mid-travel: Banner alert "Enemy contact! Autopilot paused" → Player can Engage or Resume
  - Tap ETA chip mid-travel → "Cancel Autopilot?" confirm dialog
- **Arrival:** 
  - Notification: "Arrived at [Destination]" (haptic + toast)
  - If planet: Auto-suggest Orbit action

**Entry:** Galaxy/Sector/Local → Long-press or tap destination → "Travel Here" button  
**Exit:** Autopilot started → Modal closes, OR Cancel → Modal closes (no action)

**States:**
- **Default:** All drive modes available (if items/energy sufficient)
- **Insufficient Energy:** Impulse/Hyperspace disabled, tooltip: "Recharge at planet"
- **No Zipper:** Warp Zipper option grayed, tooltip: "Buy zippers at trade station"
- **Autopilot Active:** ETA chip visible on map (persistent across tab switches)

**Push/Deep Link:** None (in-session modal)

**Accessibility:**
- VoiceOver: "Travel to Kepler-442b. Select drive mode. Impulse, ETA 3 minutes 24 seconds."
- Haptic: Light tap on mode select, medium impact on autopilot start

---

## 4. Empire Tab Screens

### 4.1 Empire Home (ID: `EMPIRE_001`)

**Name:** Empire Home (Overview Dashboard)  
**Nav Path:** Tap Empire tab (bottom nav) → Default view  
**Primary Goal:** Glanceable empire status, attention queue, quick access to planets

**Key Components:**
- **Header Card** (top, hero section):
  - Networth: "₡2,450,000" (large number, Phase 1a `calc_networth()`)
  - 7-day trend sparkline (tiny line chart, growth/decline)
  - Rank badge: "#12 / 500 players"
  - Empire stats row (3 pills):
    - Planets: "7 owned" (tap → Planet List)
    - Ships: "1 active, 2 docked" (tap → Fleet Hangar)
    - Team: "[Alliance Name]" (tap → Team Home)

- **Attention Queue** (priority section, collapsible):
  - Auto-alerts for planets needing action:
    - Card: "Planet [Name] needs food" (red warning icon)
    - Card: "Production maxed at [Name]" (green checkmark icon)
    - Card: "Planet under attack!" (red urgent, pulsing)
  - Each card: Icon + message + "Manage" CTA → Planet Detail
  - Swipe right to dismiss (non-destructive, just marks as read)

- **Production Summary** (expandable):
  - Total production rates: "Producing 450 gold/hour"
  - Tax income: "Generating ₡12,000/hour"
  - Top 3 planets by value (mini cards, tap → Planet Detail)

- **Recent Activity Feed** (optional, bottom):
  - "Captured Planet X" / "Sold 200 missiles" / "Killed [Player]"
  - Tap event → Relevant detail screen

**Wireframe:**
```
┌─────────────────────────────────────┐
│ ₡2,450,000  [📈 +5%]  #12 / 500    │
│ Planets: 7 | Ships: 3 | Team: [AB] │
│                                     │
│ ⚠ Attention (3)                     │
│ ┌───────────────────────────────┐   │
│ │ ⚠ Planet Alpha needs food     │   │
│ │                     [Manage]  │   │
│ └───────────────────────────────┘   │
│ ┌───────────────────────────────┐   │
│ │ ✓ Production maxed: Beta      │   │
│ │                     [Manage]  │   │
│ └───────────────────────────────┘   │
│                                     │
│ 📊 Production: 450 gold/hr          │
│ 💰 Tax Income: ₡12k/hr              │
│ Top Planets: Alpha, Beta, Gamma     │
│                                     │
│ Recent: Captured Planet X (2h ago)  │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap planet count:** Navigate to Planet List (§4.2)
- **Tap "Manage" in attention card:** Navigate to Planet Detail (§4.3)
- **Swipe attention card right:** Dismiss (optimistic UI, server marks as read)
- **Tap production summary:** Expand to see per-planet breakdown (collapse/expand toggle)
- **Tap recent activity:** Navigate to relevant screen (killmail, planet, trade log)

**Entry:** Empire tab tap  
**Exit:** Tap other tab or navigate to Planet List/Detail

**States:**
- **Default:** Attention queue + production summary
- **Empty (No Planets):** 
  - Header shows ₡0 networth
  - Attention queue hidden
  - Illustration: Empty starfield
  - Text: "Your empire awaits. Explore to claim planets."
  - CTA: "Start Exploring" → Galaxy tab
- **No Alerts:** Attention queue shows "✓ All clear. No actions needed."

**Push/Deep Link:** 
- `ge://empire` → Empire Home
- Push: "Planet under attack!" → Tap → Empire Home, attention card highlighted

**Accessibility:**
- VoiceOver: "Empire Home. Networth 2.45 million. 3 attention alerts. Planet Alpha needs food. Manage button."
- Haptic: Light tap on card swipe dismiss

---

### 4.2 Planet List (ID: `EMPIRE_002`)

**Name:** Planet List  
**Nav Path:** Empire Home → Tap planet count, OR Empire tab → default if bookmarked  
**Primary Goal:** Browse owned planets, sort, quick access

**Key Components:**
- Search/filter bar (top):
  - Search: Type planet name
  - Filter chips: "All" / "High Value" / "Under Threat" / "Maxed Production"
  - Sort dropdown: "Value ↓" / "Production" / "Distance" / "Threats"
- Scrollable list (vertical, card per planet):
  - Planet Card (horizontal layout):
    - Left: Planet thumbnail (3D render or icon, color by environment)
    - Center:
      - Name (editable inline)
      - Environment/resource badges: "Lush (7) / Rich (8)"
      - Treasury: "₡45,000"
      - Production preview: "Gold +120/hr, Missiles +30/hr"
    - Right:
      - Threat indicator: Shield icon (green/yellow/red)
      - Chevron → Planet Detail
  - Attention badge: Red dot on card if in attention queue

**Wireframe:**
```
┌─────────────────────────────────────┐
│ [Search...] [All ▼] [Value ↓]      │
│                                     │
│ ┌───────────────────────────────┐   │
│ │🪐 Planet Alpha               →│   │
│ │ Lush(7) Rich(8)  ₡45k   🛡️🟢│   │
│ │ Gold +120/hr, Missiles +30/hr │   │
│ └───────────────────────────────┘   │
│ ┌───────────────────────────────┐   │
│ │🪐 Planet Beta  [⚠️]          →│   │
│ │ Barren(3) Poor(2) ₡12k  🛡️🟡│   │
│ │ Food +10/hr                   │   │
│ └───────────────────────────────┘   │
│ ...                                 │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap card:** Navigate to Planet Detail (§4.3)
- **Long-press card:** Quick Actions modal:
  - "Navigate to Planet" → Galaxy tab, auto-fly
  - "Manage Production" → Planet Detail, scroll to Production Grid
  - "View Treasury" → Planet Detail, scroll to Treasury
- **Swipe left on card:** "Abandon Planet" button (destructive, red)
  - Confirm dialog: "Abandon [Name]? You'll lose all production and defenses."
  - Confirm → Server releases ownership → Card removed from list
- **Search:** Type → Real-time filter (client-side if <100 planets, server if more)
- **Filter chips:** Tap chip → Filter applies (e.g., "Under Threat" shows only planets with warnings/attacks)
- **Sort dropdown:** Tap → Options: Value ↓/↑, Production ↓/↑, Distance (from current ship position), Threats

**Entry:** Empire Home → Planet count tap, OR Empire tab bookmark  
**Exit:** Tap card → Planet Detail, OR back to Empire Home

**States:**
- **Default:** List of owned planets, sorted by value descending
- **Empty:** "No planets owned. Claim planets to build your empire." + CTA: "Explore Galaxy"
- **Search No Results:** "No planets match '[query]'" + "Clear Search" button
- **Filter No Results:** "No planets match filter 'Under Threat'" + "Clear Filters"

**Push/Deep Link:** 
- `ge://empire/planets` → Planet List
- `ge://empire/planets?filter=threat` → Planet List, threat filter applied

**Accessibility:**
- VoiceOver: "Planet Alpha. Lush 7, Rich 8. Treasury 45 thousand. Gold production 120 per hour."
- Swipe actions announce intent: "Swipe left to abandon planet. Double-tap to confirm."

---

### 4.3 Planet Detail (ID: `EMPIRE_003`)

**Name:** Planet Detail  
**Nav Path:** Planet List → Tap card → here, OR deep link from attention queue  
**Primary Goal:** View/edit single planet (production, treasury, defenses)

**Key Components:**
- **Header:**
  - Planet name (large, editable: tap → inline text input)
  - Coordinates: "Sector 12,5 — Planet 3"
  - Environment bar: 1-9 scale, color-coded (green=lush → brown=barren)
  - Resource bar: 1-9 scale (gold intensity)
  - Ownership badge: "Owned by You"
  - Beacon message: Scrolling marquee (tap to edit)

- **Treasury Card** (collapsible):
  - Cash: "₡89,000"
  - Tax rate slider: 0-100% (Phase 1a `taxrate`)
  - Projected income: "₡1,200/hour"
  - Buttons: "Withdraw" (if docked), "Deposit"

- **Production Grid** (primary, scrollable):
  - 14 item types (Phase 1a `NUMITEMS=14`):
    - Each row: Icon, name, stockpile "1,240 / 5,000", rate slider, progress bar, ETA "Next batch in 22s"
    - Reserve/Markup (expand row): Reserve qty, markup %, "Sell to Allies" toggle
  - Labor constraint warning: "⚠️ Insufficient men. Reduce rates or increase men production."

- **Defensive Setup** (collapsible):
  - Ion cannons: "5 cannons (=50 men defense)"
  - Warnings: Dropdown (0-3, auto-message intruders)
  - Password: Text input (allied docking)
  - Spy status: "No spy" or "Spy by [Enemy]"

- **Actions** (bottom floating buttons):
  - "Navigate" / "Dock" / "Set Production" / "Trade"

**Wireframe:**
```
┌─────────────────────────────────────┐
│ ← Planet Alpha  [Edit Name]         │
│ Sector 12,5 — Planet 3              │
│ Env: ████████░ 8/9 (Lush)           │
│ Res: ████████░ 8/9 (Rich)           │
│ Beacon: "Trading hub — Open access" │
│                                     │
│ 💰 Treasury: ₡89,000                │
│ Tax: ▓▓░░░░░░░░ 10%  ₡1.2k/hr      │
│ [Withdraw] [Deposit]                │
│                                     │
│ 🏭 Production (14 items)            │
│ ┌───────────────────────────────┐   │
│ │ 🪙 Gold  1,240 / 5,000        │   │
│ │ Rate: ▓▓▓▓░░░░░░ +120/hr      │   │
│ │ ●●●●●●●○○○ Next: 22s          │   │
│ └───────────────────────────────┘   │
│ (scroll for 13 more items)          │
│                                     │
│ 🛡️ Defenses: 5 ion cannons          │
│ Warnings: [Auto-Alert ▼] Password:  │
│                                     │
│ [Navigate] [Dock] [Set Production]  │
└─────────────────────────────────────┘
```

**Interaction:**
- **Edit planet name:** Tap name → Inline text input → Confirm (check icon)
- **Adjust tax rate:** Drag slider → Real-time preview of income change
- **Withdraw/Deposit:** Tap → Modal: "Amount to withdraw?" → Number input → Confirm (requires docked)
- **Production rate slider:** Drag slider per item → "Set Production" button highlights (save pending) → Tap "Set Production" → Batch update to server
- **Expand item row:** Tap row → Reserve/Markup controls slide down → Edit → Collapse
- **Dock button:** If not docked, tap → Navigate to planet (auto-pilot) → On arrival, auto-dock → Button changes to "Trade"

**Entry:** Planet List → Tap card, OR Empire Home → Attention queue → Manage  
**Exit:** Back button → Planet List, OR Navigate → Galaxy tab

**States:**
- **Default:** All data loaded, editable
- **Loading:** Skeleton screen (gray placeholder boxes) while fetching planet data
- **Docked:** "Trade" button enabled, Withdraw/Deposit enabled
- **Not Docked:** "Dock" button visible, Withdraw/Deposit grayed
- **Food Shortage:** Red banner at top: "⚠️ Food critical! Troops will die in 3 ticks (3 min)"

**Push/Deep Link:** 
- `ge://empire/planet/planet_456` → Planet Detail
- Push: "Production maxed at Alpha" → Tap → Planet Detail, scroll to maxed item

**Accessibility:**
- VoiceOver: "Planet Alpha. Environment 8, lush. Resource 8, rich. Treasury 89 thousand. Gold production rate 50%, 120 per hour."
- Dynamic Type: All text scales (labels, values)

---

### 4.4 Production Editor (ID: `EMPIRE_004`)

**Name:** Production Editor (Batch Edit Modal, Optional)  
**Nav Path:** Planet Detail → "Set Production" → here (if complex batch edit UI preferred over inline sliders)  
**Primary Goal:** Adjust all 14 item production rates at once, see labor allocation

**Key Components:**
- "Production Editor — [Planet Name]" title
- Labor pool indicator (top): "Men available: 2,400" (Phase 1a labor constraint)
- 14 item rows (scrollable):
  - Item icon + name
  - Current rate: "+30/hr"
  - Slider: 0 to max rate (constrained by manhours)
  - Manhours required: "120 manhours/tick" (Phase 1a `manhours[item]`)
- Total manhours: "1,800 / 2,400 available" (updates as sliders adjust)
- Overallocation warning: "⚠️ Insufficient labor. Some items won't produce at full rate."
- Action buttons: "Save Changes" / "Cancel"

**Wireframe:**
```
┌─────────────────────────────────────┐
│ Production Editor — Planet Alpha    │
│ Men Available: 2,400 👷             │
│ Total Manhours: 1,800 / 2,400       │
│                                     │
│ 🪙 Gold       ▓▓▓▓░░░░░░ +120/hr   │
│ Manhours: 120                       │
│ 🚀 Missiles   ▓▓░░░░░░░░ +30/hr    │
│ Manhours: 60                        │
│ ... (12 more items)                 │
│                                     │
│ [  Save Changes  ] [  Cancel  ]     │
└─────────────────────────────────────┘
```

**Interaction:**
- **Drag slider:** Adjusts rate → Manhours recalc → Total manhours updates
- **Overallocation:** If total manhours > men available → Warning appears → Server caps production proportionally (Phase 1a §4.2 line 290-293)
- **Tap "Save":** Batch update to server → Planet Detail refreshes → Close modal
- **Tap "Cancel":** Discard changes → Close modal

**Entry:** Planet Detail → "Set Production" button (if modal preferred over inline)  
**Exit:** Save → Close, OR Cancel → Close

**States:**
- **Default:** Current rates pre-filled
- **Overallocated:** Warning banner, "Save" still enabled (server handles caps)

**Accessibility:**
- VoiceOver: "Gold production rate 50%. Requires 120 manhours. Adjust slider."

---

### 4.5 Trade Dock Sheet (ID: `EMPIRE_005`)

**Name:** Trade Dock (Buy/Sell Modal)  
**Nav Path:** Planet Detail → "Trade" (if docked), OR Local Space → Dock → auto-open  
**Primary Goal:** Buy goods from planet, sell cargo to planet

**Key Components:**
- "Trading at [Planet Name]" title
- Ownership context: "Your planet — base prices" / "Allied planet — markup prices"
- Tabs: "Buy" | "Sell"

**Buy Tab:**
- List of available items (Phase 1a `amt4sale()` formula):
  - Item icon + name
  - Stock: "450 available"
  - Price: "₡120/unit" (Phase 1a `baseprice` or `markup2a`)
  - Qty stepper: +/- buttons or slider
  - "Buy" button per item
- Shopping cart (bottom):
  - Total cost: "₡24,000"
  - Weight: "480 / 1200 tons" (Phase 1a `calcweight()`)
  - "Purchase All" button (batch transaction)

**Sell Tab:**
- List of ship cargo items:
  - Item icon + name
  - Qty: "120 missiles"
  - Price: "₡100/unit"
  - Qty stepper
  - "Sell" button per item
- Sale summary (bottom):
  - Total revenue: "₡12,000"
  - "Sell All" button

**Wireframe (Buy Tab):**
```
┌─────────────────────────────────────┐
│ Trading at Planet Alpha             │
│ Your planet — Base prices           │
│ [ Buy | Sell ]                      │
│                                     │
│ 🪙 Gold     450 avail  ₡120/unit    │
│ Qty: [- 10 +]              [Buy]    │
│ 🚀 Missiles 200 avail  ₡50/unit     │
│ Qty: [- 0 +]               [Buy]    │
│ ... (12 more items)                 │
│                                     │
│ Total: ₡1,200  Weight: 80/1200 t    │
│ [     Purchase All     ]            │
└─────────────────────────────────────┘
```

**Interaction:**
- **Qty stepper:** Tap +/- → Qty adjusts → Total cost/weight updates
- **Tap "Buy" per item:** Instant optimistic UI (item added to ship) → Server confirms → Rollback if error (insufficient cash)
- **Tap "Purchase All":** Batch transaction → All selected items transferred → Toast: "Purchased 10 gold, 5 missiles"
- **Switch to Sell tab:** Same pattern, reverse direction (ship → planet)
- **Overweight:** If weight exceeds `max_tons` → "Buy" button grayed, tooltip: "Cargo full. Sell items or upgrade ship."

**Entry:** Planet Detail → "Trade" (docked), OR Local Space → Dock action → auto-open  
**Exit:** Close button (X top-right), OR swipe down to dismiss

**States:**
- **Default (Own Planet):** All items available at base price
- **Allied Planet:** Only items with `sell='Y'` shown, markup price applied
- **Neutral/Enemy Planet:** "Docking restricted" (or bribe mechanic, future)
- **Empty Stock (Buy):** "No items for sale. Set production on this planet."
- **Empty Cargo (Sell):** "Your cargo is empty."

**Push/Deep Link:** 
- `ge://empire/planet/planet_456/trade` → Auto-dock (if not docked) → Open trade sheet

**Accessibility:**
- VoiceOver: "Gold. 450 available. Price 120 per unit. Quantity stepper. Buy button."
- Haptic: Medium impact on purchase success

---

### 4.6 Treasury Summary (ID: `EMPIRE_006`)

**Name:** Treasury Summary (Optional, if separate from Planet Detail)  
**Nav Path:** Empire Home → "View Treasury" link, OR Planet Detail → Expand treasury card  
**Primary Goal:** See cash flow across all planets, tax collection breakdown

**Key Components:**
- "Treasury Summary" title
- Total cash across all planets: "₡245,000"
- Cash in ship: "₡50,000" (from ship cargo)
- Per-planet breakdown (scrollable list):
  - Planet name, cash on hand, tax rate, projected income
- Total income: "₡18,000/hour" (sum of all planet taxes + production sales, if tracked)
- Withdraw all button: "Withdraw All to Ship" (if docked at any owned planet)

**Wireframe:**
```
┌─────────────────────────────────────┐
│ Treasury Summary                    │
│ Total: ₡245,000                     │
│ Ship Cargo: ₡50,000                 │
│                                     │
│ ┌───────────────────────────────┐   │
│ │ Planet Alpha: ₡89,000         │   │
│ │ Tax: 10%  +₡1.2k/hr           │   │
│ └───────────────────────────────┘   │
│ ┌───────────────────────────────┐   │
│ │ Planet Beta: ₡45,000          │   │
│ │ Tax: 15%  +₡800/hr            │   │
│ └───────────────────────────────┘   │
│ ... (5 more planets)                │
│                                     │
│ Total Income: ₡18k/hr               │
│ [   Withdraw All to Ship   ]        │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap planet card:** Navigate to Planet Detail
- **Tap "Withdraw All":** Confirmation: "Withdraw ₡245,000 to ship? (Must be docked)" → Confirm → Transfer

**Entry:** Empire Home → Treasury link (if added), OR Planet Detail → Treasury card expand  
**Exit:** Back to Empire Home or Planet Detail

**States:**
- **Default:** Per-planet breakdown
- **No Cash:** "No cash in empire. Produce and sell goods to earn."

**Accessibility:**
- VoiceOver: "Treasury summary. Total 245 thousand. Planet Alpha 89 thousand."

---

## 5. Fleet Tab Screens

### 5.1 Active Ship Card (ID: `FLEET_001`)

**Name:** Active Ship Card (Fleet Home, Default View)  
**Nav Path:** Tap Fleet tab → Default view  
**Primary Goal:** See current ship status, quick access to loadout/hangar

**Key Components:**
- 3D ship model preview (top, rotating)
- Ship name (large, editable)
- Ship class: "Cruiser (Class 4)" (Phase 1a `shpclass`)
- Status badges:
  - Damage: "12%" (color: green/yellow/red)
  - Shields: "85%" (up/down indicator)
  - Energy: "42,000 / 65,000"
- Cargo summary: "480 / 1200 tons" (tap → expand to item list)
- Equipped loadout (quick view):
  - Phasor type: "Type 12 Phasor"
  - Shield type: "Type 8 Shields"
  - Special: "Cloak" (if equipped)
- Action buttons:
  - "View Details" → Ship Detail (§5.2)
  - "Edit Loadout" → Loadout Editor (§5.3)
  - "Hangar" → Hangar screen (§5.4)
  - "Repair" (if damaged >25%)

**Wireframe:**
```
┌─────────────────────────────────────┐
│         🚀 (Ship Model)             │
│        USS Starfire                 │
│        Cruiser (Class 4)            │
│                                     │
│ 💔 Damage: 12%  🛡️ Shields: 85%    │
│ ⚡ Energy: 42k / 65k                │
│ 📦 Cargo: 480 / 1200 tons           │
│                                     │
│ Equipped:                           │
│ Phasor: Type 12 | Shields: Type 8  │
│ Special: Cloak                      │
│                                     │
│ [Details] [Loadout] [Hangar] [Repair]│
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap ship name:** Inline edit (rename ship)
- **Tap cargo summary:** Expands to show itemized list (gold, missiles, etc.)
- **Tap "Details":** Navigate to Ship Detail (§5.2)
- **Tap "Loadout":** Navigate to Loadout Editor (§5.3)
- **Tap "Hangar":** Navigate to Hangar (§5.4)
- **Tap "Repair":** 
  - If docked: Modal: "Repair cost: ₡5,000. Confirm?" → Confirm → Damage → 0%, cash deducted
  - If not docked: "Dock at a planet to repair" toast

**Entry:** Fleet tab tap  
**Exit:** Navigate to Detail/Loadout/Hangar, or switch tab

**States:**
- **Default:** Ship healthy (<25% damage)
- **Damaged (>25%):** Red warning banner: "⚠️ Ship damaged. Repair recommended." + "Repair" button
- **Critical (>75%):** Red pulsing border, urgent banner: "🚨 Critical damage! Repair immediately."
- **Destroyed (Respawned):** Shows new class 0 light freighter, tooltip: "New ship issued after destruction."

**Push/Deep Link:** 
- `ge://fleet` → Active Ship Card

**Accessibility:**
- VoiceOver: "Fleet Home. Active ship USS Starfire. Cruiser class 4. Damage 12%. Shields 85%. Details button."

---

### 5.2 Ship Detail (ID: `FLEET_002`)

**Name:** Ship Detail (Full Stats)  
**Nav Path:** Fleet → "View Details" → here  
**Primary Goal:** View comprehensive ship stats, upgrade options

**Key Components:**
- 3D ship model (large, rotatable by drag)
- Ship name + class (editable name)
- Full stats table:
  - Max speed: "9 warp" (Phase 1a `shipclass[].max_speed`)
  - Max tons: "1200" (cargo capacity)
  - Max energy: "65,000" (Phase 1a `ENGYMAX`)
  - Phasor charge rate: "+5%/tick"
  - Shield max: "5,000" (varies by `shieldtype`)
- Equipped items (full list):
  - Phasor, shields, cloak, decoys, mines (qty in cargo)
- Cargo breakdown (all 14 items, qty + weight)
- Upgrade preview (if higher class available):
  - "Upgrade to Dreadnought (Class 5)" button
  - Cost: "₡500,000"
  - Stat comparison: "+20% speed, +500 tons, +10k energy"

**Wireframe:**
```
┌─────────────────────────────────────┐
│ ←     🚀 USS Starfire               │
│       Cruiser (Class 4)             │
│                                     │
│ Stats:                              │
│ Max Speed: 9 warp                   │
│ Max Tons: 1200                      │
│ Max Energy: 65,000                  │
│ Phasor Charge: +5%/tick             │
│ Shield Max: 5,000                   │
│                                     │
│ Equipped:                           │
│ Phasor: Type 12 (Range 10k)         │
│ Shields: Type 8 (Absorb 4x dmg)     │
│ Cloak: Installed                    │
│                                     │
│ Cargo: (expand to see 14 items)     │
│                                     │
│ Upgrade Available:                  │
│ Dreadnought (Class 5)  ₡500k        │
│ +20% speed, +500 tons               │
│ [     Upgrade Now     ]             │
└─────────────────────────────────────┘
```

**Interaction:**
- **Rotate ship model:** Two-finger drag or gyroscope (opt-in)
- **Tap "Upgrade Now":** 
  - Confirmation: "Upgrade to Dreadnought for ₡500,000? Current ship will be replaced."
  - Confirm → Server transaction (Phase 1a `cmd_new()` mechanic) → New ship issued, old ship replaced
- **Tap cargo:** Expands to itemized list (same as Trade Dock, read-only here)

**Entry:** Fleet → "View Details"  
**Exit:** Back to Active Ship Card

**States:**
- **Default:** Full stats shown
- **No Upgrade Available:** Upgrade section hidden (if max class or insufficient cash)
- **Insufficient Funds:** "Upgrade" button grayed, tooltip: "Need ₡500k (you have ₡200k)"

**Push/Deep Link:** 
- `ge://fleet/ship/ship_789` → Ship Detail (if multi-ship feature, specify ship ID)

**Accessibility:**
- VoiceOver: "Ship Detail. USS Starfire. Cruiser class 4. Max speed 9 warp. Upgrade available to Dreadnought for 500 thousand."

---

### 5.3 Loadout Editor (ID: `FLEET_003`)

**Name:** Loadout Editor  
**Nav Path:** Fleet → "Edit Loadout" → here  
**Primary Goal:** Equip phasors, shields, special items (cloak, decoys, mines)

**Key Components:**
- "Loadout Editor — [Ship Name]" title
- Equipment slots (Phase 1a weapon/shield types):
  - **Phasor Slot:** Dropdown or list of owned phasor types (1-19, Phase 1a line 570 `GEMAIN.H`)
    - Current: "Type 12 Phasor"
    - Available: List of types in inventory (if any) or "Purchase at trade station"
  - **Shield Slot:** Dropdown of shield types (1-19)
  - **Special Slot 1:** Cloak (toggle: Installed / Not Installed, if ship supports)
  - **Special Slot 2:** Decoy qty (slider: allocate decoys from cargo, max `MAXDECOY=10`)
  - **Special Slot 3:** Mines (qty slider)
- Weight check: "Total weight: 480 / 1200 tons"
- Action buttons: "Save Loadout" / "Cancel"

**Wireframe:**
```
┌─────────────────────────────────────┐
│ Loadout Editor — USS Starfire       │
│                                     │
│ Phasor: [Type 12 Phasor     ▼]     │
│ Range: 10k | Damage: High           │
│                                     │
│ Shield: [Type 8 Shields     ▼]     │
│ Max: 5,000 | Absorb: 4x             │
│                                     │
│ Cloak:  [⦿ Installed  ○ None]      │
│                                     │
│ Decoys: [▓▓▓▓░░░░░░] 4 / 10        │
│ Mines:  [▓▓░░░░░░░░] 2 / 10        │
│                                     │
│ Weight: 480 / 1200 tons             │
│ [  Save Loadout  ] [  Cancel  ]     │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap phasor/shield dropdown:** List of available types (owned or purchasable)
- **Select type:** Updates loadout preview, weight recalc
- **Toggle cloak:** On/Off (if ship class supports, Phase 1a some classes can't cloak)
- **Adjust decoy/mine qty:** Slider allocates from cargo (Phase 1a `items[I_DECOY]`, `items[I_MINE]`)
- **Tap "Save":** Batch update to server → Fleet card refreshes → Close modal
- **Tap "Cancel":** Discard changes → Close

**Entry:** Fleet → "Edit Loadout"  
**Exit:** Save → Close, OR Cancel → Close

**States:**
- **Default:** Current loadout pre-filled
- **Overweight:** Warning if total weight > max_tons (shouldn't happen, but graceful error)
- **No Items in Cargo:** Decoy/mine sliders disabled, tooltip: "Purchase at trade station"

**Push/Deep Link:** None (in-session modal)

**Accessibility:**
- VoiceOver: "Phasor dropdown. Type 12 selected. Range 10 thousand, damage high."

---

### 5.4 Fleet Hangar (ID: `FLEET_004`)

**Name:** Fleet Hangar (Multi-Ship Management, if feature exists)  
**Nav Path:** Fleet → "Hangar" → here  
**Primary Goal:** Switch active ship, dock/repair ships, purchase new ships

**Key Components:**
- "Fleet Hangar" title
- List of owned ships (if Phase 1a multi-ship feature enabled, `noships` field):
  - Ship card per ship:
    - Thumbnail + name + class
    - Status: "Active" / "Docked" / "Destroyed"
    - Damage % (if applicable)
    - "Switch" button (if not active)
- "Purchase New Ship" button (bottom):
  - Opens ship shop (list of classes 0-9, Phase 1a `shipclass[]`)
  - Shows cost, stats comparison
  - "Buy" button → Confirm → New ship added to hangar

**Wireframe:**
```
┌─────────────────────────────────────┐
│ Fleet Hangar                        │
│                                     │
│ ┌───────────────────────────────┐   │
│ │ 🚀 USS Starfire  [Active]     │   │
│ │ Cruiser (Class 4)             │   │
│ │ Damage: 12%                   │   │
│ └───────────────────────────────┘   │
│ ┌───────────────────────────────┐   │
│ │ 🚀 HMS Voyager   [Docked]     │   │
│ │ Freighter (Class 1)           │   │
│ │ Damage: 0%  [Switch] [Repair] │   │
│ └───────────────────────────────┘   │
│                                     │
│ [   + Purchase New Ship   ]         │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap "Switch":** Confirmation: "Switch to HMS Voyager?" → Confirm → Active ship changes, player respawns in Voyager's last location
- **Tap "Repair":** If docked, instant repair (cost deducted), OR navigate to planet to dock first
- **Tap "Purchase New Ship":** Modal: Ship shop (classes 0-9, costs, stats) → Select class → Buy → New ship added

**Entry:** Fleet → "Hangar"  
**Exit:** Back to Fleet card

**States:**
- **Single Ship (Default MVP):** Hangar only shows current ship + "Purchase" button
- **Multi-Ship:** List of ships shown
- **No Ships (Edge Case):** "No ships. Purchase a new ship to continue." (shouldn't happen, always have respawn ship)

**Push/Deep Link:** 
- `ge://fleet/hangar` → Hangar

**Accessibility:**
- VoiceOver: "Fleet Hangar. USS Starfire, active. Cruiser class 4. Damage 12%. HMS Voyager, docked. Switch button."

---

### 5.5 Travel Orders (Current Destination, ETA) (ID: `FLEET_005`)

**Name:** Travel Orders (Active Autopilot Status)  
**Nav Path:** Fleet → "Travel Orders" link (if autopilot active), OR ETA chip in Local Space → tap  
**Primary Goal:** Monitor autopilot, cancel or adjust travel

**Key Components:**
- "Travel Orders" title
- Destination: "Kepler-442b (Sector 12,5)"
- Drive mode: "Impulse" / "Hyperspace"
- ETA: "Arrives in 2m 18s" (live countdown)
- Route map (mini): Line from current position to destination (optional visual)
- Energy cost: "5,000 ⚡ consumed on arrival"
- Action buttons:
  - "Cancel Autopilot" (red, destructive)
  - "Pause" (if feature exists, ship holds position)

**Wireframe:**
```
┌─────────────────────────────────────┐
│ Travel Orders                       │
│                                     │
│ Destination: Kepler-442b            │
│ Sector 12,5 — Planet 3              │
│                                     │
│ Drive: Impulse                      │
│ ETA: Arrives in 2m 18s              │
│ Energy: 5,000 ⚡ consumed            │
│                                     │
│ ┌───────────────────────────────┐   │
│ │  🚀 -----> 🪐                 │   │
│ │  (route line)                 │   │
│ └───────────────────────────────┘   │
│                                     │
│ [Cancel Autopilot] [Pause]          │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap "Cancel":** Confirmation: "Cancel autopilot? Ship will stop." → Confirm → Ship halts, destination cleared
- **Tap "Pause":** Ship stops moving (retains destination), "Resume" button appears
- **Live countdown:** ETA updates every second (client-side, re-sync on tab focus)

**Entry:** Fleet → "Travel Orders" (if active), OR ETA chip in Local Space → tap  
**Exit:** Arrival (ETA → 0s, auto-close, notification), OR Cancel → Close

**States:**
- **Active:** ETA counting down
- **Paused:** "Paused" badge, ETA frozen, "Resume" button
- **Interrupted (Enemy Contact):** Banner: "Autopilot paused — Enemy detected!" + "Resume" or "Engage" buttons
- **No Active Travel:** Fleet tab doesn't show "Travel Orders" link (only visible if autopilot active)

**Push/Deep Link:** 
- `ge://fleet/travel` → Travel Orders (if active)

**Accessibility:**
- VoiceOver: "Travel Orders. Destination Kepler-442b. ETA 2 minutes 18 seconds. Cancel button."

---

## 6. Social Tab Screens

**Designer Note:** Social tab per Game Design §9.1 & §9.2 includes: Alliance sub-tab, Inbox sub-tab (notifications history, fka "Intel"), and Leaderboard sub-tab. Consolidates social features, messaging, and competitive ranking.

### 6.1 Social Hub / Alliance Home (ID: `SOCIAL_001`)

**Name:** Social Hub (Alliance Tab, Default View if in Alliance)  
**Nav Path:** Tap **Social** tab → Alliance sub-tab (if in alliance) or Leaderboard (if solo)  
**Primary Goal:** View alliance info, members, alliance chat, coordinate conquest

**Key Components:**
- Team name + badge/emblem (large, top)
- Alliance score + rank (e.g., "₡8.5M, Rank #3/50" per Game Design §4.4)
- Member roster (scrollable: avatar, name, networth, online status)
- "Open Alliance Chat" button → Alliance Chat screen (§6.2)
- Alliance tech pool (contribute/spend points per §5.1)
- Territory map (alliance-controlled sectors highlighted)
- Management buttons (if officer/leader): "Invite Member", "Set Password", "Kick Member"

**Wireframe:** (See Phase 1b UX Vision §2.x for alliance management detail)

**Entry:** Social tab tap  
**Exit:** Tap sub-tab (Inbox, Leaderboard) or navigate to Alliance Chat

**States:**
- **In Alliance:** Alliance home shown
- **Solo Player:** Redirects to Leaderboard, "Join an Alliance" CTA banner at top

**Push/Deep Link:**
- `ge://social/alliance` → Alliance Home

**Accessibility:**
- VoiceOver: "Social tab. Alliance Name. Score 8.5 million. Rank 3 of 50. 12 members online."

---

### 6.2 Inbox (Notifications History) (ID: `SOCIAL_002`)

**Name:** Inbox (Notifications History, fka "Intel Inbox")  
**Nav Path:** Tap **Social** tab → **Inbox** sub-tab  
**Primary Goal:** Browse notifications history (attack reports, production alerts, spy reports, killmails, seasonal rewards)

**Key Components:**
- "Intel" title
- Filter chips (horizontal scroll):
  - "All" / "Threats" / "Reports" / "Social" / "Killmails"
- Message list (scrollable, card per message):
  - Icon (alert 🚨, mail ✉️, skull 💀, spy 🕵️)
  - Sender/subject: "Planet Alpha under attack!" / "Spy Report: Beta"
  - Timestamp: "2 hours ago"
  - Unread badge (blue dot)
  - Chevron → Detail screen
- Empty state (no messages): "No new intel. All clear."

**Wireframe:**
```
┌─────────────────────────────────────┐
│ Intel                (3 unread)     │
│ [All] [Threats] [Reports] [Killmails]│
│                                     │
│ ┌───────────────────────────────┐   │
│ │ 🚨 Planet Alpha under attack! │●│→│
│ │ 2 hours ago                   │   │
│ └───────────────────────────────┘   │
│ ┌───────────────────────────────┐   │
│ │ 🕵️ Spy Report: Planet Beta    │●│→│
│ │ 5 hours ago                   │   │
│ └───────────────────────────────┘   │
│ ┌───────────────────────────────┐   │
│ │ 💀 Killmail: You killed X     │ │→│
│ │ 1 day ago                     │   │
│ └───────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap filter chip:** Filter messages by type (Phase 1a `mail.class`: 1=distress, 2=maxout, 3=production, 4=stats, 5=planet)
- **Tap message card:** Navigate to Alert Detail (§6.2), Spy Report (§6.3), or Killmail (§3.6)
- **Swipe left on card:** "Delete" button (red) → Confirm → Remove message
- **Long-press card:** Quick Actions: "Mark Read" / "Delete" / "Pin" (priority message)

**Entry:** Intel tab tap  
**Exit:** Tap card → Detail screen, or switch tab

**States:**
- **Default:** List of messages, unread count badge on tab
- **Empty:** "No new intel. All clear." + illustration (empty inbox icon)
- **Filter No Results:** "No threat alerts." + "Clear Filter"

**Push/Deep Link:** 
- `ge://intel` → Inbox
- Push: "Planet under attack!" → Tap → Inbox, threat filter applied, relevant message highlighted

**Accessibility:**
- VoiceOver: "Intel Inbox. 3 unread messages. Threat alert: Planet Alpha under attack. 2 hours ago."
- Badge: Unread count announced as "3 unread"

---

### 6.2 Alert Detail (ID: `INTEL_002`)

**Name:** Alert Detail (Threat, Production, etc.)  
**Nav Path:** Intel Inbox → Tap alert card → here  
**Primary Goal:** Read full alert, take action (navigate to planet, manage production, etc.)

**Key Components:**
- Alert title: "Planet Alpha Under Attack!"
- Icon (alert type: 🚨 threat, ✓ production maxed, 📊 report)
- Message body:
  - "Your planet Alpha is under assault by PlayerName123."
  - "Defender strength: 1,200 men, 5 ion cannons"
  - "Attacker: 1,500 men deployed"
  - "Time remaining: Assault in progress..."
- Timestamp: "2 hours ago"
- Action buttons:
  - "View Planet" → Planet Detail
  - "Navigate" → Galaxy tab, auto-fly to planet
  - "Dismiss" (mark as read)

**Wireframe:**
```
┌─────────────────────────────────────┐
│ ← Alert: Planet Alpha Under Attack! │
│                                     │
│ 🚨 Your planet Alpha is under       │
│ assault by PlayerName123.           │
│                                     │
│ Defender: 1,200 men, 5 ion cannons  │
│ Attacker: 1,500 men                 │
│                                     │
│ Time: Assault in progress...        │
│ (2 hours ago)                       │
│                                     │
│ [View Planet] [Navigate] [Dismiss]  │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap "View Planet":** Navigate to Planet Detail (§4.3)
- **Tap "Navigate":** Set autopilot to planet (Galaxy tab, auto-fly)
- **Tap "Dismiss":** Mark as read → Back to Inbox

**Entry:** Intel Inbox → Tap alert card  
**Exit:** Navigate to Planet/Galaxy, or back to Inbox

**States:**
- **Default:** Alert shown, action buttons enabled
- **Resolved (Planet Conquered):** Banner: "Planet captured by enemy" (if assault succeeded after alert sent)

**Push/Deep Link:** 
- `ge://intel/alert/alert_123` → Alert Detail

**Accessibility:**
- VoiceOver: "Alert. Planet Alpha under attack. Your planet is under assault by PlayerName123. View Planet button."

---

### 6.3 Spy Report (ID: `INTEL_003`)

**Name:** Spy Report  
**Nav Path:** Intel Inbox → Tap spy report card → here  
**Primary Goal:** View enemy planet intel (from planted spy, Phase 1a spy mechanics)

**Key Components:**
- "Spy Report — [Planet Name]" title
- Spy owner: "Your spy on Planet Beta"
- Report timestamp: "6 hours ago"
- Intel data (Phase 1a spy report format, §3.3 line 150-188):
  - Owner: "PlayerName456"
  - Treasury estimate: "~45,000 ₡ (±10%)" (random error per Phase 1a)
  - Production snapshot (top 3 items):
    - "Gold: ~300 qty"
    - "Missiles: ~50 qty"
    - "Fighters: ~20 qty"
  - Defenses:
    - "Ion cannons: ~3"
    - "Men: ~800"
- Risk status: "Spy not detected" or "Spy discovered! Lost contact."
- Action buttons:
  - "View Planet" (if location known) → Planet Detail (read-only view)
  - "Plan Assault" → Conquest Prep (§2.2 Planet Assault)
  - "Dismiss"

**Wireframe:**
```
┌─────────────────────────────────────┐
│ ← Spy Report — Planet Beta          │
│                                     │
│ 🕵️ Your spy reports:                │
│ Owner: PlayerName456                │
│ Treasury: ~45,000 ₡ (estimate)      │
│                                     │
│ Production:                         │
│ Gold: ~300 qty                      │
│ Missiles: ~50 qty                   │
│                                     │
│ Defenses:                           │
│ Ion Cannons: ~3 | Men: ~800         │
│                                     │
│ Status: Spy not detected            │
│ (6 hours ago)                       │
│                                     │
│ [View Planet] [Plan Assault] [Dismiss]│
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap "View Planet":** Navigate to read-only Planet Detail (enemy planet, no edit)
- **Tap "Plan Assault":** Navigate to Conquest Prep (§2.2), pre-fill enemy strength from spy intel
- **Tap "Dismiss":** Mark as read → Back to Inbox

**Entry:** Intel Inbox → Tap spy report card  
**Exit:** Navigate to Planet/Assault, or back to Inbox

**States:**
- **Spy Active:** Intel shown, status "Not detected"
- **Spy Caught:** Status "Spy discovered! Lost contact." → Partial intel (last known data)

**Push/Deep Link:** 
- `ge://intel/spy/spy_789` → Spy Report

**Accessibility:**
- VoiceOver: "Spy Report. Planet Beta. Owner PlayerName456. Treasury 45 thousand estimate. Gold 300. View Planet button."

---

### 6.4 Killmail (Previously Covered, See §3.6)

**Cross-Reference:** See Combat Radial section §3.6 Killmail Screen for full detail.

**Brief Summary Here:**
- Full killmail accessible from Intel Inbox (filter: Killmails)
- Tap killmail card → Opens full death summary (attacker, losses, respawn/revenge options)

---

### 6.5 Threat Dashboard (ID: `INTEL_005`)

**Name:** Threat Dashboard  
**Nav Path:** Intel Inbox → "Threats" filter → "View All Threats" link → here (optional dedicated screen)  
**Primary Goal:** Consolidated view of current dangers (locked missiles, nearby enemies, planet attacks)

**Key Components:**
- "Threat Dashboard" title
- Active threats (categorized):
  - **Locked Projectiles:**
    - "2 torpedoes tracking your ship"
    - "1 missile locked" (Phase 1a `ltorps`, `lmissl`)
    - Countdown to impact: "12 seconds"
  - **Nearby Enemies:**
    - List of enemy ships in sector (name, range, threat level)
  - **Planet Attacks:**
    - List of owned planets under assault (name, attacker, status)
- Threat level indicator: "High" / "Medium" / "Low" (aggregate)
- Action buttons per threat:
  - Locked projectile: "Deploy Decoy" / "Cloak"
  - Enemy ship: "Engage" / "Retreat"
  - Planet attack: "View Planet" / "Reinforce"

**Wireframe:**
```
┌─────────────────────────────────────┐
│ Threat Dashboard          [🔴 High] │
│                                     │
│ 🚨 Locked Projectiles (2)           │
│ - Torpedo: Impact in 12s [Decoy]    │
│ - Missile: Impact in 8s  [Cloak]    │
│                                     │
│ 👾 Nearby Enemies (1)               │
│ - EnemyShip: 4.2k range  [Engage]   │
│                                     │
│ 🏰 Planet Attacks (1)               │
│ - Alpha under assault    [View]     │
│                                     │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap "Deploy Decoy":** Instant action (consumes decoy item, Phase 1a decoy mechanics) → Torpedo evades → Threat removed from list
- **Tap "Engage":** Navigate to Local Space, target enemy ship
- **Tap "View" (planet):** Navigate to Planet Detail

**Entry:** Intel Inbox → "Threats" filter → "View All" link (optional)  
**Exit:** Back to Inbox

**States:**
- **Default:** List of active threats
- **No Threats:** "✓ All clear. No immediate threats." + green checkmark

**Push/Deep Link:** 
- `ge://intel/threats` → Threat Dashboard

**Accessibility:**
- VoiceOver: "Threat Dashboard. Threat level high. 2 locked projectiles. Torpedo impact in 12 seconds. Deploy decoy button."

---

## 7. Social Tab Screens

### 7.1 Team Home (ID: `SOCIAL_001`)

**Name:** Team/Alliance Home  
**Nav Path:** Tap Social tab → Default if in team, else Leaderboard  
**Primary Goal:** View alliance info, members, team score, chat access

**Key Components:**
- Team name + badge/emblem (top, large)
- Team score: "₡8,500,000" (sum of member scores, Phase 1a `teamscore`)
- Rank: "#3 / 50 teams"
- Member count: "12 members" (Phase 1a `teamcount`)
- Member list (scrollable):
  - Avatar, name, rank, networth, online status (green dot)
- Team chat button: "Open Chat" → Alliance Chat (§7.2)
- Team management (if admin):
  - "Invite Member" → Modal: enter username → Send invite
  - "Set Password" → Modal: change team password (Phase 1a `password`)
  - "Kick Member" → Select member → Confirm

**Wireframe:**
```
┌─────────────────────────────────────┐
│ 🛡️ Alliance Name  [Badge/Emblem]    │
│ Score: ₡8,500,000  Rank: #3 / 50    │
│ 12 Members                          │
│                                     │
│ [      Open Team Chat      ]        │
│                                     │
│ Members:                            │
│ ┌───────────────────────────────┐   │
│ │ 👤 PlayerA  🟢 ₡1.2M          │   │
│ └───────────────────────────────┘   │
│ ┌───────────────────────────────┐   │
│ │ 👤 PlayerB  ⚪ ₡800k           │   │
│ └───────────────────────────────┘   │
│ ... (10 more members)               │
│                                     │
│ [Invite] [Settings] [Leave Team]    │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap "Open Chat":** Navigate to Alliance Chat (§7.2)
- **Tap member card:** View member profile (optional feature: stats, ships, planets)
- **Tap "Invite":** Modal: "Username to invite?" → Send invite (server validates)
- **Tap "Leave Team":** Confirmation: "Leave Alliance Name?" → Confirm → Remove from team, back to Leaderboard

**Entry:** Social tab (if in team)  
**Exit:** Navigate to Chat, or switch tab

**States:**
- **Default (In Team):** Team info shown
- **Not in Team:** Redirect to Leaderboard (§7.4), "Join a Team" CTA

**Push/Deep Link:** 
- `ge://social/team` → Team Home

**Accessibility:**
- VoiceOver: "Team Home. Alliance Name. Score 8.5 million. Rank 3 of 50. 12 members. PlayerA online, networth 1.2 million."

---

### 7.2 Alliance Chat (ID: `SOCIAL_002`)

**Name:** Alliance Chat  
**Nav Path:** Team Home → "Open Chat" → here  
**Primary Goal:** Real-time text chat with team members

**Key Components:**
- Chat title: "Alliance Name Chat"
- Message list (scrollable, reverse chronological):
  - Avatar, username, message text, timestamp
  - Own messages right-aligned (blue bubble), others left-aligned (gray)
- Text input field (bottom):
  - Placeholder: "Type message..."
  - Send button (paper plane icon)
- Optional: Voice chat button (microphone icon, top-right) → Initiates voice call (optional feature, out of scope for MVP)

**Wireframe:**
```
┌─────────────────────────────────────┐
│ ← Alliance Name Chat         [🎤]  │
│                                     │
│ 👤 PlayerA: "Need backup at 12,5"  │
│ 2m ago                              │
│                                     │
│        You: "On my way"       2m ago│
│                                     │
│ 👤 PlayerB: "I'll bring missiles"  │
│ 1m ago                              │
│                                     │
│ ┌─────────────────────────────┐    │
│ │ Type message...         [📤]│    │
│ └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

**Interaction:**
- **Type message:** Keyboard appears, text input
- **Tap Send:** Message sent to server (websocket or HTTP POST) → Appears in chat instantly (optimistic UI)
- **Scroll up:** Load more history (pagination, lazy-load past messages)
- **Tap voice button (optional):** Initiates voice call (Discord-style, future feature)

**Entry:** Team Home → "Open Chat"  
**Exit:** Back button → Team Home

**States:**
- **Default:** Chat history shown, input enabled
- **Offline:** "Offline. Messages will send when reconnected." + Queued messages marked with clock icon
- **Empty (New Team):** "No messages yet. Start the conversation!"

**Push/Deep Link:** 
- `ge://social/chat/team` → Alliance Chat
- Push: "PlayerA: Need backup!" → Tap → Chat, message highlighted

**Accessibility:**
- VoiceOver: "Alliance chat. PlayerA says need backup at 12,5. 2 minutes ago."

---

### 7.3 Sector Chat (ID: `SOCIAL_003`)

**Name:** Sector Chat (Proximity Chat)  
**Nav Path:** Social tab → "Sector Chat" link (if in sector with active players), OR Local Space HUD → Chat bubble icon (top-right, optional)  
**Primary Goal:** Communicate with nearby players (current sector, Phase 1a `cmd_send()` broadcast)

**Key Components:**
- Chat title: "Sector 12,5 Chat"
- Message list (same as Alliance Chat format)
- Frequency toggle (Phase 1a `freq` mechanic, §7.4 line 560):
  - "Subspace" (sector-wide, default)
  - "Hyperspace" (hyperspace only, if ship in hyperspace)
  - "Planetary" (docked ships only)
- Text input + Send

**Wireframe:**
```
┌─────────────────────────────────────┐
│ ← Sector 12,5 Chat                  │
│ Freq: [Subspace ▼]                  │
│                                     │
│ 👤 EnemyShip: "Stay out of my way" │
│ 5m ago                              │
│                                     │
│        You: "Make me"         4m ago│
│                                     │
│ 👤 NeutralPlayer: "Anyone trading?" │
│ 2m ago                              │
│                                     │
│ ┌─────────────────────────────┐    │
│ │ Type message...         [📤]│    │
│ └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

**Interaction:**
- Same as Alliance Chat, but messages sent to sector (all players in sector see)
- **Frequency toggle:** Tap dropdown → Select freq → Chat filters to that channel

**Entry:** Social tab → "Sector Chat", OR Local Space HUD → Chat icon (if present)  
**Exit:** Back to Social tab or Local Space

**States:**
- **Default:** Active chat if players in sector
- **Empty Sector:** "No players in this sector. Messages visible when players arrive."

**Push/Deep Link:** 
- `ge://social/chat/sector/12/5` → Sector Chat

**Accessibility:**
- VoiceOver: "Sector 12,5 chat. Frequency Subspace. EnemyShip says stay out of my way."

---

### 7.4 Leaderboard (ID: `SOCIAL_004`)

**Name:** Leaderboard  
**Nav Path:** Social tab → Default if not in team, OR "Leaderboard" link in Team Home  
**Primary Goal:** View rankings (players, teams), compare scores

**Key Components:**
- "Leaderboard" title
- Tabs: "Players" | "Teams"
- Time filter: "Weekly" / "Monthly" / "All-Time" (Phase 1a §8 KILL midnight reset replaced with rolling leaderboards)
- Scrollable list (rank, avatar/name, score):
  - Rank # (1-500)
  - Player/team name
  - Networth (Phase 1a `waruptr->score`)
  - Trend arrow (↑ rising, ↓ falling, — stable)
- "My Rank" card (sticky at top or highlighted):
  - "You: #42 / 500" with score
- Search bar (top): "Search player/team"

**Wireframe:**
```
┌─────────────────────────────────────┐
│ Leaderboard  [Weekly ▼]             │
│ [ Players | Teams ]                 │
│                                     │
│ 🏆 You: #42 / 500  ₡2.45M  ↑        │
│                                     │
│ #1  👤 TopPlayer   ₡10M  ↑          │
│ #2  👤 SecondBest  ₡9.5M  —         │
│ #3  👤 ThirdPlace  ₡9.2M  ↓         │
│ ...                                 │
│ #42 👤 You         ₡2.45M  ↑        │
│ ...                                 │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap player/team card:** View profile (optional: stats, planets, ships)
- **Switch tabs:** Players ↔ Teams
- **Time filter:** Tap dropdown → Select weekly/monthly/all-time → Leaderboard refreshes
- **Search:** Type name → Filter list

**Entry:** Social tab (default if no team)  
**Exit:** Switch tab

**States:**
- **Default:** Ranked list shown
- **Loading:** Skeleton screen (gray placeholder rows)
- **Search No Results:** "No player named '[query]'"

**Push/Deep Link:** 
- `ge://social/leaderboard` → Leaderboard
- `ge://social/leaderboard?filter=weekly&tab=teams` → Teams, weekly

**Accessibility:**
- VoiceOver: "Leaderboard. Weekly. You rank 42 of 500. Networth 2.45 million. Rank 1: TopPlayer, 10 million."

---

### 7.5 Settings (Nested in Social Tab) (ID: `SOCIAL_005`)

**Name:** Settings  
**Nav Path:** Social tab → Overflow menu (☰) → "Settings" → here  
**Primary Goal:** Configure app preferences, account, notifications, accessibility

**Key Components:**
- "Settings" title
- Sections (scrollable list):
  - **Account:** Username, email, logout button
  - **Notifications:** Toggle push notifications (planet attacks, production, killmails)
  - **Audio:** Master volume slider, SFX on/off, music on/off
  - **Accessibility:** VoiceOver test, high-contrast mode, one-handed mode (moves action buttons to bottom), Dynamic Type preview
  - **Gameplay:** Safe Harbor default (toggle: auto-dock on logout), combat confirmation (toggle: confirm before firing), tutorial replay button
  - **Privacy:** Data usage, privacy policy link
  - **Help:** FAQ, support contact, report bug
  - **Legal:** Terms of Service, Privacy Policy, licenses (MIT for Phase 1a code)
  - **About:** App version, build number, credits

**Wireframe:**
```
┌─────────────────────────────────────┐
│ ← Settings                          │
│                                     │
│ Account                             │
│ Username: PlayerName                │
│ Email: user@example.com             │
│ [      Logout      ]                │
│                                     │
│ Notifications                       │
│ Push Alerts:  [⦿ On  ○ Off]        │
│                                     │
│ Audio                               │
│ Master Volume: ▓▓▓▓▓░░░░░ 50%      │
│ SFX: [⦿ On  ○ Off]                 │
│                                     │
│ Accessibility                       │
│ High Contrast: [○ On  ⦿ Off]       │
│ One-Handed Mode: [○ On  ⦿ Off]     │
│                                     │
│ Help & Legal                        │
│ [FAQ] [Privacy Policy] [TOS]        │
│                                     │
│ About                               │
│ Version: 1.0.0 (build 42)           │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap toggle:** Switches preference (instant, saved locally + synced to server)
- **Tap "Logout":** Confirmation → Logout → Back to Login screen (§1.2)
- **Tap links (Privacy, TOS):** Opens in-app browser or native browser

**Entry:** Social tab → Overflow → "Settings"  
**Exit:** Back to Social tab

**States:**
- **Default:** All preferences shown, current values pre-filled
- **Logged Out (Edge Case):** Account section shows "Not logged in" + "Login" button

**Push/Deep Link:** 
- `ge://settings` → Settings
- `ge://settings/notifications` → Settings, scroll to Notifications section

**Accessibility:**
- VoiceOver: "Settings. Account. Username PlayerName. Logout button. Notifications. Push alerts on."

---

## 8. Overlay & Modal Screens

### 8.1 Safe Harbor Explainer (ID: `OVERLAY_001`)

**Name:** Safe Harbor Explainer (Modal)  
**Nav Path:** Tap Safe Harbor chip (top-right HUD) → here  
**Primary Goal:** Explain offline protection, offer emergency retreat

**Key Components:**
- "Safe Harbor" title
- Explainer text:
  - "When you log out in open space, your ship is vulnerable."
  - "Dock at a planet or citadel to enable protection."
  - "Protected ships cannot be attacked while offline."
- Current status badge: "Safe" (green) / "In Danger" (red)
- Action buttons:
  - "Emergency Retreat" (red, costs energy, instant dock at nearest owned planet)
  - "Understood" (dismiss)

**Wireframe:**
```
┌─────────────────────────────────────┐
│ Safe Harbor                         │
│                                     │
│ When you log out in open space,     │
│ your ship is vulnerable to attack.  │
│                                     │
│ Dock at a planet to enable          │
│ offline protection.                 │
│                                     │
│ Current Status: [🔴 In Danger]      │
│                                     │
│ [  Emergency Retreat  ]             │
│ (Costs 10,000 ⚡)                   │
│                                     │
│ [     Understood     ]              │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap "Emergency Retreat":** 
  - Confirmation: "Retreat to nearest planet for 10,000 energy?"
  - Confirm → Instant dock animation (ship teleports to nearest owned planet, Phase 1a warp zipper-style)
  - Safe Harbor status → Green "Safe"
- **Tap "Understood":** Dismiss modal

**Entry:** Tap Safe Harbor chip (HUD) or first-time undocked logout (auto-prompt)  
**Exit:** Dismiss or Retreat completes

**States:**
- **In Danger:** Red status, Retreat button enabled
- **Safe:** Green status, Retreat button grayed (already safe)

**Push/Deep Link:** 
- `ge://safeharbor` → Explainer modal

**Accessibility:**
- VoiceOver: "Safe Harbor explainer. Current status in danger. Emergency retreat button costs 10 thousand energy."

---

### 8.2 Command Sheet (ID: `OVERLAY_002`)

**Name:** Command Sheet (Contextual Action Modal)  
**Nav Path:** Long-press target in Local Space → here, OR tap overflow menu on Target Sheet → here  
**Primary Goal:** Show all available actions for selected target (ship, planet, wormhole)

**Key Components:**
- Target name (top)
- Action list (vertical, icon + label per action):
  - **Ship target:** Scan, Fire, Lock, Retreat, Add to Enemies, Message
  - **Planet target:** Orbit, Dock, Scan, Claim (if neutral), Attack (if enemy)
  - **Wormhole target:** Enter Wormhole, Scan
- Cancel button (bottom)

**Wireframe:**
```
┌─────────────────────────────────────┐
│ Actions: Enemy Ship                 │
│                                     │
│ 📡 Scan                             │
│ 🎯 Fire Weapons                     │
│ 🔒 Lock Target                      │
│ 🏃 Retreat                          │
│ ⚔️ Add to Enemies                   │
│ ✉️ Send Message                     │
│                                     │
│ [        Cancel        ]            │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap action:** Execute action (Scan → Phase 1a `cmd_scan()`, Fire → Combat Radial, etc.) → Close modal
- **Tap "Cancel":** Close modal (no action)

**Entry:** Long-press target in Local Space, OR Target Sheet → Overflow  
**Exit:** Tap action → Close, OR Cancel → Close

**States:**
- **Default:** All available actions shown
- **Out of Range:** Some actions grayed (e.g., "Dock" if not in orbit range)

**Push/Deep Link:** None (contextual, in-session)

**Accessibility:**
- VoiceOver: "Actions for Enemy Ship. Scan. Fire weapons. Lock target."

---

### 8.3 Confirmation Dialogs (ID: `OVERLAY_003`)

**Name:** Confirmation Dialog (Generic)  
**Nav Path:** Triggered by destructive actions (sell ship, abandon planet, attack, logout)  
**Primary Goal:** Prevent accidental destructive actions

**Key Components:**
- Title: "Confirm Action"
- Message: "Are you sure you want to [action]?" (e.g., "abandon Planet Alpha? You'll lose all production.")
- Warning icon (⚠️) if destructive
- Action buttons:
  - "Confirm" (red for destructive, green for constructive)
  - "Cancel" (gray)

**Wireframe:**
```
┌─────────────────────────────────────┐
│ ⚠️ Confirm Action                   │
│                                     │
│ Abandon Planet Alpha?               │
│ You'll lose all production and      │
│ defenses. This cannot be undone.    │
│                                     │
│ [  Cancel  ]  [  Confirm  ]         │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap "Confirm":** Execute action → Close dialog
- **Tap "Cancel":** Dismiss dialog (no action)
- **Tap outside dialog (if modal allows):** Cancel

**Entry:** Triggered by app (destructive action attempted)  
**Exit:** Confirm or Cancel → Close

**States:**
- **Default:** Buttons enabled
- **Loading (if action async):** "Confirm" button shows spinner

**Accessibility:**
- VoiceOver: "Confirm action. Abandon Planet Alpha? You'll lose all production. Confirm button. Cancel button."
- Haptic: Error vibration on destructive action confirmation

---

### 8.4 Push Threat Banner (ID: `OVERLAY_004`)

**Name:** Push Threat Banner (Slide-Down Alert)  
**Nav Path:** Auto-appears when threat event occurs (planet attack, ship engaged) while user in different tab  
**Primary Goal:** Alert user to urgent threat without full-screen interrupt

**Key Components:**
- Banner (top of screen, slide-down animation):
  - Icon (🚨)
  - Message: "Planet Alpha under attack!" or "Enemy ship engaging!"
  - CTA button: "View" (jumps to relevant screen)
  - Dismiss button (X)
- Auto-dismiss after 10s if not interacted

**Wireframe:**
```
┌─────────────────────────────────────┐
│ 🚨 Planet Alpha under attack! [View][X]│
└─────────────────────────────────────┘
(slides down from top, overlays content)
```

**Interaction:**
- **Tap "View":** Navigate to Planet Detail or Local Space (threat location)
- **Tap "X":** Dismiss banner
- **Swipe up:** Dismiss banner
- **Auto-dismiss:** Fades out after 10s

**Entry:** Auto-triggered by server push event  
**Exit:** View, dismiss, or auto-dismiss

**States:**
- **Active:** Banner visible, CTA enabled
- **Dismissed:** Fades out

**Push/Deep Link:** Triggered by push notification while app in foreground

**Accessibility:**
- VoiceOver: Announces "Alert. Planet Alpha under attack. View button." (interrupts current VO focus)
- Haptic: Heavy impact on banner appear

---

### 8.5 Loading States (ID: `OVERLAY_005`)

**Name:** Loading Spinner / Skeleton Screen  
**Nav Path:** Auto-appears during async operations (login, fetch data, travel)  
**Primary Goal:** Indicate progress, prevent perceived freeze

**Key Components:**
- **Spinner (Small):** Inline button spinner (login, save changes)
- **Spinner (Full-Screen):** Modal overlay with spinner + "Loading..." text (initial data fetch)
- **Skeleton Screen:** Gray placeholder boxes (Planet List, Leaderboard) while data loads
- **Progress Bar:** Travel/production progress (deterministic, shows %)

**Wireframe (Full-Screen Spinner):**
```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│            ⏳                       │
│         Loading...                  │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

**Interaction:**
- No user input; auto-dismiss when operation completes
- Optional: Cancel button for cancelable operations (e.g., travel)

**Entry:** Auto-triggered by async operation  
**Exit:** Auto-dismiss on complete, or error state

**States:**
- **Loading:** Spinner animates
- **Error:** Transitions to error state (see below)

**Accessibility:**
- VoiceOver: "Loading" announced, periodic updates if long (e.g., "Still loading, 5 seconds elapsed")

---

### 8.6 Error States (ID: `OVERLAY_006`)

**Name:** Error Toast / Modal  
**Nav Path:** Auto-appears when operation fails (network error, validation error)  
**Primary Goal:** Inform user of error, offer retry or dismiss

**Key Components:**
- **Toast (Small Error):** Slide-up banner (bottom), auto-dismiss after 5s
  - Icon (❌), message: "Network error. Retry?"
  - Optional "Retry" button
- **Modal (Critical Error):** Full-screen overlay
  - Title: "Error"
  - Message: "Failed to load data. Check your connection."
  - "Retry" button, "Dismiss" button

**Wireframe (Toast):**
```
(Bottom of screen)
┌─────────────────────────────────────┐
│ ❌ Network error. [Retry] [X]       │
└─────────────────────────────────────┘
```

**Wireframe (Modal):**
```
┌─────────────────────────────────────┐
│ ❌ Error                            │
│                                     │
│ Failed to load planet data.         │
│ Check your internet connection.     │
│                                     │
│ [  Retry  ]  [  Dismiss  ]          │
└─────────────────────────────────────┘
```

**Interaction:**
- **Tap "Retry":** Re-attempt failed operation
- **Tap "Dismiss" or X:** Close error (user acknowledges)
- **Auto-dismiss (toast only):** Fades out after 5s

**Entry:** Auto-triggered by error  
**Exit:** Retry, dismiss, or auto-dismiss

**States:**
- **Toast:** Non-blocking, overlays content
- **Modal:** Blocking, user must dismiss or retry

**Accessibility:**
- VoiceOver: "Error. Network error. Retry button."
- Haptic: Error vibration (3 short pulses) on error appear

---

## 9. Settings & Legal Screens

### 9.1 Settings (Covered in §7.5, Cross-Reference)

**See §7.5 Settings (Nested in Social Tab) for full detail.**

---

### 9.2 Legal / Privacy Policy (ID: `LEGAL_001`)

**Name:** Legal / Privacy Policy  
**Nav Path:** Settings → "Privacy Policy" or "Terms of Service" → here  
**Primary Goal:** Display legal text, allow user to read and dismiss

**Key Components:**
- Title: "Privacy Policy" or "Terms of Service"
- Scrollable text (full legal document)
- "Close" button (top-right or bottom)

**Wireframe:**
```
┌─────────────────────────────────────┐
│ ← Privacy Policy              [X]   │
│                                     │
│ (Scrollable legal text)             │
│ ...                                 │
│ Last updated: 2026-09-11            │
│                                     │
│                                     │
│ [        Close        ]             │
└─────────────────────────────────────┘
```

**Interaction:**
- **Scroll:** Read text
- **Tap "Close":** Dismiss → Back to Settings

**Entry:** Settings → Legal links  
**Exit:** Close → Settings

**States:**
- **Default:** Text displayed

**Accessibility:**
- VoiceOver: Reads legal text (long, user can skip with VO gestures)

---

### 9.3 Account / Logout (ID: `LEGAL_002`)

**Name:** Account Screen (within Settings)  
**Nav Path:** Settings → "Account" section → here (if dedicated screen)  
**Primary Goal:** View/edit account info, logout

**Key Components:**
- Username (editable)
- Email (editable)
- Password: "Change Password" button → Modal: old password, new password, confirm
- "Delete Account" button (destructive, red)
- "Logout" button (secondary)

**Wireframe:**
```
┌─────────────────────────────────────┐
│ ← Account                           │
│                                     │
│ Username: [PlayerName        ]      │
│ Email: [user@example.com     ]      │
│                                     │
│ [  Change Password  ]               │
│                                     │
│ [   Delete Account   ]              │
│ (This action is permanent)          │
│                                     │
│ [      Logout      ]                │
└─────────────────────────────────────┘
```

**Interaction:**
- **Edit username/email:** Tap field → Inline edit → Save (check icon)
- **Tap "Change Password":** Modal: old password, new password, confirm → Save
- **Tap "Delete Account":** 
  - Confirmation: "Delete account? All data will be lost. Type 'DELETE' to confirm."
  - Text input: must type "DELETE" exactly → Confirm → Account deleted, logout
- **Tap "Logout":** Confirmation: "Logout? Unsaved changes may be lost." → Confirm → Logout → Login screen

**Entry:** Settings → "Account" section  
**Exit:** Back to Settings, or Logout → Login

**States:**
- **Default:** Account info shown
- **Delete Account Confirmation:** Destructive warning, text input required

**Accessibility:**
- VoiceOver: "Account. Username field PlayerName. Email field user@example.com. Change password button. Logout button."
- Confirmation for destructive action: "Delete account. This action is permanent. Type DELETE to confirm."

---

## 10. Summary & Screen Count

**Total Screens Documented:** 46

**Breakdown by Section:**
- Boot & Auth: 3
- Onboarding: 5 (Steps 1-7 consolidated as 2.1-2.5)
- Galaxy Tab: 8 (Overview, Sector, Local, Target, Radial, Killmail, Salvage, Travel)
- Empire Tab: 6 (Home, List, Detail, Editor, Trade, Treasury)
- Fleet Tab: 5 (Active Ship, Detail, Loadout, Hangar, Travel Orders)
- Intel Tab: 5 (Inbox, Alert, Spy, Killmail ref, Threat)
- Social Tab: 5 (Team, Alliance Chat, Sector Chat, Leaderboard, Settings)
- Overlays: 6 (Safe Harbor, Command, Confirmation, Banner, Loading, Error)
- Settings/Legal: 3 (Settings ref, Privacy, Account)

**All Screens Include:**
- Screen ID, name, nav path
- Primary user goal
- Key components (layout, elements, actions)
- ASCII wireframe or bullet description
- Interaction notes (gestures, haptics, confirmations)
- Entry/exit conditions
- Empty/error/loading states
- Push notification / deep link support (where applicable)
- Accessibility notes (VoiceOver, Dynamic Type, one-handed, contrast)

**Cross-References to UX Vision Doc:**
- All mechanics grounded in Phase 1a Legacy System Map sections (cited inline)
- HUD design details in UX Vision §3
- Combat flow in UX Vision §2.2
- Empire management in UX Vision §2.3
- Onboarding flow in UX Vision §2.4

**Companion to `PHASE1B_CLIENT_UX_VISION.md`** — Use both documents together for comprehensive UX understanding.

---

**End of Phase 1b Screen Inventory.**
