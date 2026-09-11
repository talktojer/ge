# Phase B: Unity Stub Screen Map

**Date:** 2026-09-11  
**Source:** PR #4 Screen Inventory (`docs/PHASE1B_SCREEN_INVENTORY.md`, branch `cursor/phase1b-mobile-ux-vision-2ef6`)  
**Base:** PR #5 Cleanup Branch (`cursor/archive-web-port-cleanup-62f7`)  
**Target Platform:** Unity 6000.4.10f1 (iOS + Android)  
**Purpose:** Design-only mapping document for Empire Lead scaffold agent — NO MERGE

---

## Executive Summary

This document maps **every screen** from PR #4's `PHASE1B_SCREEN_INVENTORY.md` (44 screens) to Unity 6000.4.10f1 stub scenes and prefabs for the **Phase B scaffold**. Phase B delivers a skeleton navigation shell with empty placeholder screens — no game logic, no real networking, no art assets — enabling the Empire Lead scaffold agent to wire up the **4-tab IA** (Map / Fleet / Empire / Social) + HUD chrome + overlay system.

**Key Constraints:**
- **F2P cosmetics only, NO P2W** — Zero UI for production speedups, combat-power boosts, or gameplay-advantage IAPs
- **4-Tab Navigation** — Bottom nav: Map / Fleet / Empire / Social (locked per Game Design §9.1)
- **HUD Requirements** — Status strip (top), minimap (bottom-right), Safe Harbor chip, action stack (right edge), contextual overlays
- **Scaffold Scope** — Must-have stubs enable navigation + HUD integration; Should-have stubs reserve screen IDs; Later items document only
- **Out of Scope** — Real art, real FastAPI networking, Celery/React UI, production speedups/P2W monetization, merging PRs

**Deliverable:** Unity scene/prefab paths + Must/Should/Later priority matrix + gap checklist for Empire Lead to validate scaffold completeness.

---

## 1. Unity Naming Conventions

### 1.1 Scene Organization

**Path Template:** `Assets/Scenes/Stub/{Area}/{ScreenId}_{ScreenName}.unity`

**Area Categories:**
- `Boot/` — Splash, login, character select
- `Onboard/` — Tutorial flows
- `Map/` — Galaxy, sector, local space, combat
- `Empire/` — Planets, production, treasury
- `Fleet/` — Ships, hangar, loadout
- `Social/` — Alliance, chat, leaderboard, inbox
- `Overlays/` — Modals, confirmation dialogs, toasts
- `Settings/` — Legal, account, preferences

**Example:**
```
Assets/Scenes/Stub/Map/MAP_003_LocalSpaceHUD.unity
Assets/Scenes/Stub/Empire/EMPIRE_001_EmpireHome.unity
Assets/Scenes/Stub/Overlays/OVERLAY_001_SafeHarborExplainer.unity
```

### 1.2 Prefab Organization

**Path Template:** `Assets/Prefabs/UI/Stub/{Area}/{ComponentName}.prefab`

**Shared UI Components:**
- `Assets/Prefabs/UI/Stub/Shared/HUD_Root.prefab` — Top status strip container (cash, energy, shields, damage %)
- `Assets/Prefabs/UI/Stub/Shared/BottomNav_MapFleetEmpireSocial.prefab` — 4-tab bottom nav bar
- `Assets/Prefabs/UI/Stub/Shared/Minimap.prefab` — Bottom-right sector pip (10% screen size per UX Vision §9.1)
- `Assets/Prefabs/UI/Stub/Shared/SafeHarborChip.prefab` — Floating status indicator (top-right or near minimap)
- `Assets/Prefabs/UI/Stub/Shared/ActionStack.prefab` — Right-edge contextual button stack

**Overlay Prefabs:**
- `Assets/Prefabs/UI/Stub/Overlays/ConfirmationDialog.prefab` — Generic confirm/cancel modal
- `Assets/Prefabs/UI/Stub/Overlays/LoadingSpinner.prefab` — Full-screen or inline spinner
- `Assets/Prefabs/UI/Stub/Overlays/ErrorToast.prefab` — Bottom toast for transient errors

**Area-Specific Prefabs:**
- Map: `Assets/Prefabs/UI/Stub/Map/TargetSheet.prefab`, `CombatRadial.prefab`, `TravelOrderSheet.prefab`
- Empire: `Assets/Prefabs/UI/Stub/Empire/PlanetCard.prefab`, `ProductionEditor.prefab`, `TradeDockSheet.prefab`
- Fleet: `Assets/Prefabs/UI/Stub/Fleet/ShipCard.prefab`, `LoadoutEditor.prefab`
- Social: `Assets/Prefabs/UI/Stub/Social/AllianceHub.prefab`, `ChatPanel.prefab`, `LeaderboardTable.prefab`

### 1.3 Naming Rules

- **PascalCase** for scene/prefab file names
- **Screen IDs** prefix all scenes (e.g., `BOOT_001_`, `MAP_003_`)
- **Descriptive suffixes** for clarity (e.g., `_HUD`, `_Sheet`, `_Modal`, `_Panel`)
- **No spaces** in paths (use underscores for multi-word)

---

## 2. Complete Screen Mapping Table

### Legend: Phase B Stub Levels

| Level | Definition | Action |
|-------|------------|--------|
| **Must** | Scaffold now — Empty canvas/panel with nav wiring, essential for IA testing | Create scene + basic prefab, wire to bottom nav or overlay system |
| **Should** | Reserve screen ID — Empty placeholder scene (no UI), pre-allocated for future work | Create empty scene file, add to build settings, document path |
| **Later** | Document only — Screen ID reserved in this map, no Unity asset created | Entry in this table only, no file creation |

---

### 2.1 Boot & Auth Screens

| Inventory ID | Screen Name | Unity Stub Path | Parent / Flow | Phase B Level | Notes |
|--------------|-------------|-----------------|---------------|---------------|-------|
| `BOOT_001` | Splash Screen | `Assets/Scenes/Stub/Boot/BOOT_001_Splash.unity` | App launch | **Must** | Empty canvas + version label stub. Auto-advance logic placeholder (hardcoded 2s delay to login). |
| `AUTH_001` | Login Screen | `Assets/Scenes/Stub/Boot/AUTH_001_Login.unity` | Splash → Login | **Must** | Empty email/password input stubs (no Firebase yet). "Sign In" button navigates to Local Space HUD directly. OAuth buttons grayed out. |
| `AUTH_002` | Character Select | `Assets/Scenes/Stub/Boot/AUTH_002_CharacterSelect.unity` | Login (optional) | **Later** | Future feature (multi-commander). No scene created. Hardwire single-commander path for Phase B. |

---

### 2.2 Onboarding Screens

| Inventory ID | Screen Name | Unity Stub Path | Parent / Flow | Phase B Level | Notes |
|--------------|-------------|-----------------|---------------|---------------|-------|
| `ONBOARD_001` | Intro Cinematic | `Assets/Scenes/Stub/Onboard/ONBOARD_001_IntroCinematic.unity` | First launch | **Should** | Empty canvas with "Skip" button → jumps to Create Commander. Video placeholder (black screen + subtitle "Year 3250..."). |
| `ONBOARD_002` | Create Commander | `Assets/Scenes/Stub/Onboard/ONBOARD_002_CreateCommander.unity` | Cinematic → Create | **Should** | Avatar picker stub (hardcoded 3 preset icons), name input field (no validation), Confirm → Name Starter Ship. |
| `ONBOARD_003` | Name Starter Ship | `Assets/Scenes/Stub/Onboard/ONBOARD_003_NameStarterShip.unity` | Create Commander → Ship Name | **Should** | Ship name input (pre-filled "Starfire"), 3D ship placeholder (cube with "Ship Model TBD" label). Confirm → Tutorial. |
| `ONBOARD_004` | Tutorial: Learn HUD | `Assets/Scenes/Stub/Onboard/ONBOARD_004_TutorialHUD.unity` | Ship Name → Tutorial | **Should** | Local Space HUD scene with 3 coach marks (hardcoded positions, no real tutorial engine). "Got it" button advances. |
| `ONBOARD_005–009` | Tutorial: Scan/Claim/Produce/Trade/Combat | `Assets/Scenes/Stub/Onboard/ONBOARD_00X_TutorialSteps.unity` | Tutorial flow | **Later** | Consolidate as single tutorial scene with step counter (1/7). No interactive logic. Skip to completion button. |
| `ONBOARD_010` | Tutorial: Safe Harbor Intro | `Assets/Scenes/Stub/Onboard/ONBOARD_010_SafeHarborIntro.unity` | Final tutorial step | **Later** | Trigger Safe Harbor explainer modal (OVERLAY_001), then mark tutorial complete. |

---

### 2.3 Map Tab Screens

| Inventory ID | Screen Name | Unity Stub Path | Parent / Flow | Phase B Level | Notes |
|--------------|-------------|-----------------|---------------|---------------|-------|
| `MAP_001` | Galaxy Overview | `Assets/Scenes/Stub/Map/MAP_001_GalaxyOverview.unity` | Map Tab (Zoom 1) | **Must** | Empty 30×15 grid canvas (white squares on black). Pinch-zoom placeholder (no real zoom, button to switch to Sector view). Top search bar stub, "My Empire" button (no-op). |
| `MAP_002` | Sector Grid View | `Assets/Scenes/Stub/Map/MAP_002_SectorGrid.unity` | Map Tab (Zoom 2) | **Must** | Empty sector canvas with 3 planet placeholder circles + 1 ship chevron. Tap planet → no action (future: Planet Detail). Pinch-zoom button to Local Space. |
| `MAP_003` | Local Space HUD | `Assets/Scenes/Stub/Map/MAP_003_LocalSpaceHUD.unity` | Map Tab (Zoom 3) / Default | **Must** | **Primary scene** with HUD_Root, BottomNav, Minimap, SafeHarborChip, ActionStack prefabs integrated. Center canvas empty (ship 3D model placeholder: gray cube). Status strip shows dummy values (Cash: ₡10k, Energy: 50k, Shields: 100%). Minimap shows static sector grid. Bottom nav functional (tabs switch scenes). |
| `MAP_004` | Target Sheet | `Assets/Prefabs/UI/Stub/Map/TargetSheet.prefab` | Local Space → Tap Contact | **Must** | Slide-up sheet prefab (no scene). Stub fields: Target name, class, distance, shield %. Action buttons: Scan, Lock, Fire, Retreat (all no-ops). Instantiated by Local Space HUD on tap (hardcoded trigger). |
| `MAP_005` | Combat Radial | `Assets/Prefabs/UI/Stub/Map/CombatRadial.prefab` | Target Sheet → Fire | **Must** | Radial menu prefab (6 weapon icons: Phasor, Torpedo, Missile, Hyper-Phasor, Mine, Decoy). Tap weapon → close radial + debug log "Fired [Weapon]". No combat logic. |
| `MAP_006` | Killmail Modal | `Assets/Prefabs/UI/Stub/Overlays/Killmail.prefab` | Combat death | **Must** | Full-screen overlay prefab. Stub fields: "You were destroyed by [Enemy]", loss summary list (hardcoded "50% cargo dropped"). Respawn button → reload Local Space HUD. |
| `MAP_007` | Travel Order Sheet | `Assets/Prefabs/UI/Stub/Map/TravelOrderSheet.prefab` | Map → Set Destination | **Should** | Slide-up sheet. Destination input, drive mode buttons (Impulse/Hyperspace/Warp), ETA stub (hardcoded "Arrives in 3m 24s"). Confirm → debug log "Travel started". |
| `MAP_008` | Wormhole Transit | `Assets/Scenes/Stub/Map/MAP_008_WormholeTransit.unity` | Sector → Wormhole Entry | **Later** | Discovery flow screen. Empty canvas with "Scanning anomaly..." text + Scan button. No scene created. |

---

### 2.4 Empire Tab Screens

| Inventory ID | Screen Name | Unity Stub Path | Parent / Flow | Phase B Level | Notes |
|--------------|-------------|-----------------|---------------|---------------|-------|
| `EMPIRE_001` | Empire Home | `Assets/Scenes/Stub/Empire/EMPIRE_001_EmpireHome.unity` | Empire Tab | **Must** | Dashboard canvas with stub cards: Networth (₡500k), Planet count (3), Attention queue list (2 hardcoded items: "Planet Alpha under attack", "Planet Beta production maxed"). Cards non-interactive. Bottom nav integrated. |
| `EMPIRE_002` | Planet List | `Assets/Scenes/Stub/Empire/EMPIRE_002_PlanetList.unity` | Empire Tab → View All | **Should** | Scrollable list of 5 hardcoded planet cards (PlanetCard.prefab): Name, production rate stub, threat badge. Tap card → debug log "Navigate to Planet Detail [Name]". Sort buttons (Value/Production/Threats) non-functional. |
| `EMPIRE_003` | Planet Detail | `Assets/Scenes/Stub/Empire/EMPIRE_003_PlanetDetail.unity` | Planet List → Tap Planet | **Should** | Single planet view. Stub fields: Planet name, resource bars (Gold/Food/Energy, hardcoded 60%), population count. Production grid placeholder (empty 6×6 grid). Action buttons: Edit Production, Trade Dock (navigate to respective screens). |
| `EMPIRE_004` | Production Editor | `Assets/Scenes/Stub/Empire/EMPIRE_004_ProductionEditor.unity` | Planet Detail → Edit | **Should** | Production rate sliders for 6 resources (Gold/Food/Clothing/Phasors/Shields/Ships). All sliders at 50%, no calculation logic. Save button → back to Planet Detail. |
| `EMPIRE_005` | Trade Dock Sheet | `Assets/Prefabs/UI/Stub/Empire/TradeDockSheet.prefab` | Planet Detail / Local Space (docked) | **Should** | Slide-up sheet. Buy/Sell tabs. 6 resource rows with quantity input + price stub (₡100/unit). Buy/Sell buttons → debug log. No inventory sync. |
| `EMPIRE_006` | Treasury Summary | `Assets/Scenes/Stub/Empire/EMPIRE_006_TreasurySummary.unity` | Empire Home → Treasury | **Later** | Cash flow chart placeholder (empty graph canvas). Tax collection log (hardcoded 3 entries). No scene created. |

---

### 2.5 Fleet Tab Screens

| Inventory ID | Screen Name | Unity Stub Path | Parent / Flow | Phase B Level | Notes |
|--------------|-------------|-----------------|---------------|---------------|-------|
| `FLEET_001` | Active Ship Card | `Assets/Scenes/Stub/Fleet/FLEET_001_ActiveShipCard.unity` | Fleet Tab | **Must** | Ship card with stub stats: Class (Light Freighter), Shields (100%), Damage (0%), Cargo (5/50 tons). Loadout slots (6 empty squares). Action buttons: Ship List, Detail, Hangar (navigate to respective screens). Bottom nav integrated. |
| `FLEET_002` | Ship List | `Assets/Scenes/Stub/Fleet/FLEET_002_ShipList.unity` | Fleet Tab → View All | **Should** | Scrollable list of 3 hardcoded ships (ShipCard.prefab): Class, status (Active/Docked/Destroyed), location. Tap card → set active + reload Active Ship Card. |
| `FLEET_003` | Ship Detail | `Assets/Scenes/Stub/Fleet/FLEET_003_ShipDetail.unity` | Ship Card → Detail | **Should** | Full stats view: Hull tonnage, speed, weapon range, cargo capacity. Upgrade preview section (empty, "No upgrades available" text). Back button. |
| `FLEET_004` | Loadout Editor | `Assets/Scenes/Stub/Fleet/FLEET_004_LoadoutEditor.unity` | Ship Card → Loadout | **Should** | 6 equipment slots (Phasor 1/2, Shields, Cloak, Torpedo, Missile). Drag-drop placeholder (slots fixed, no interaction). Inventory list (hardcoded 10 items). Equip button → debug log. |
| `FLEET_005` | Hangar (Dock/Repair) | `Assets/Scenes/Stub/Fleet/FLEET_005_Hangar.unity` | Fleet Tab → Hangar | **Later** | Ship purchase screen. 5 ship classes listed (Class 0-4: Freighter to Dreadnought). Price stubs. Buy button → debug log "Purchased [Class]". No scene created. |

---

### 2.6 Social Tab Screens

**Note:** Inventory consolidates Intel/Inbox into Social per Designer §9.2. Prefix adjusted from `INTEL_*` to `SOCIAL_*` for Social tab placement.

| Inventory ID | Screen Name | Unity Stub Path | Parent / Flow | Phase B Level | Notes |
|--------------|-------------|-----------------|---------------|---------------|-------|
| `SOCIAL_001` | Alliance Hub | `Assets/Scenes/Stub/Social/SOCIAL_001_AllianceHub.unity` | Social Tab | **Must** | Alliance info card (Name: "The Coalition", Members: 12, Team Score: 1.2M). Tabs: Chat, Members, Settings. Chat panel embedded (see SOCIAL_004). Bottom nav integrated. |
| `SOCIAL_002` | Inbox (Notifications) | `Assets/Scenes/Stub/Social/SOCIAL_002_Inbox.unity` | Social Tab → Inbox | **Must** | Scrollable list of 8 hardcoded alerts: "Planet Alpha under attack" (red), "Production maxed" (yellow), "Trade completed" (green), "Killmail: You destroyed [Enemy]" (blue). Tap alert → Alert Detail (SOCIAL_003). Filter tabs: All/Threats/Reports/Social (non-functional). |
| `SOCIAL_003` | Alert Detail | `Assets/Scenes/Stub/Social/SOCIAL_003_AlertDetail.unity` | Inbox → Tap Alert | **Should** | Full message view. Title, timestamp, body text (lorem ipsum), action button ("Navigate to Planet" / "View Killmail"). Back button. |
| `SOCIAL_004` | Alliance Chat | `Assets/Prefabs/UI/Stub/Social/ChatPanel.prefab` | Social Hub → Chat Tab | **Should** | Chat panel prefab (embeddable in Social_001). 10 hardcoded messages (username + text). Input field + Send button (appends to list locally, no server). Scroll view. |
| `SOCIAL_005` | Sector Chat | `Assets/Prefabs/UI/Stub/Social/SectorChatPanel.prefab` | Local Space HUD → Chat Overlay | **Later** | Proximity chat. Same prefab as Alliance Chat but different message source. Overlay toggle button on Local Space HUD. No prefab created. |
| `SOCIAL_006` | Leaderboard | `Assets/Scenes/Stub/Social/SOCIAL_006_Leaderboard.unity` | Social Tab → Leaderboard | **Must** | Scrollable table: Rank, Player Name, Networth, Kills. 20 hardcoded rows. Filter tabs: Weekly/Monthly/All-Time (non-functional). Team filter toggle (Individual/Team). |
| `SOCIAL_007` | Team Management | `Assets/Scenes/Stub/Social/SOCIAL_007_TeamManagement.unity` | Social Hub → Settings Tab | **Later** | Invite/kick UI. Member list with role badges (Leader/Officer/Member). Password set field. No scene created. |
| `SOCIAL_008` | Spy Report | `Assets/Prefabs/UI/Stub/Social/SpyReportSheet.prefab` | Inbox → Spy Report Alert | **Later** | Sheet prefab with enemy planet intel: Production rates, defense fleet count, resource reserves. Timestamp + confidence % (hardcoded 75%). No prefab created. |

---

### 2.7 Overlay & Modal Screens

| Inventory ID | Screen Name | Unity Prefab Path | Parent / Trigger | Phase B Level | Notes |
|--------------|-------------|-------------------|------------------|---------------|-------|
| `OVERLAY_001` | Safe Harbor Explainer | `Assets/Prefabs/UI/Stub/Overlays/SafeHarborExplainer.prefab` | SafeHarborChip Tap | **Must** | Full-screen modal. Title: "Safe Harbor System", 3 bullet points (lorem ipsum explaining docking invulnerability). "Retreat to Planet" button (navigate to nearest planet orbit). Close button. |
| `OVERLAY_002` | Confirmation Dialog | `Assets/Prefabs/UI/Stub/Overlays/ConfirmationDialog.prefab` | Destructive Actions | **Must** | Generic confirm/cancel modal. Title + body text (configurable). Confirm button (red) + Cancel button (gray). Instantiated by any screen needing confirmation (e.g., "Sell ship?" from Hangar). |
| `OVERLAY_003` | Loading Spinner | `Assets/Prefabs/UI/Stub/Overlays/LoadingSpinner.prefab` | Global | **Must** | Full-screen dimmed overlay with centered spinner + "Loading..." text. Instantiated on scene transitions (0.5s artificial delay for Phase B stub). |
| `OVERLAY_004` | Error Toast | `Assets/Prefabs/UI/Stub/Overlays/ErrorToast.prefab` | Global | **Must** | Bottom toast (3s auto-dismiss). Red background, white text (error message). Close button (X). Instantiated on errors (e.g., "Network error. Retry?"). |
| `OVERLAY_005` | Push Threat Banner | `Assets/Prefabs/UI/Stub/Overlays/PushThreatBanner.prefab` | Background Event | **Should** | Slide-down banner (top). Alert text: "Planet Alpha under attack!" Tap banner → navigate to Alert Detail (SOCIAL_003). Auto-dismiss after 5s. |
| `OVERLAY_006` | Command Sheet | `Assets/Prefabs/UI/Stub/Overlays/CommandSheet.prefab` | Contextual Actions | **Later** | Generic action sheet (swipe up from bottom). 3-6 action buttons (configurable). Used for planet actions (Orbit/Dock/Scan) or contact actions (Attack/Trade/Ignore). No prefab created. |

---

### 2.8 Settings & Legal Screens

| Inventory ID | Screen Name | Unity Stub Path | Parent / Flow | Phase B Level | Notes |
|--------------|-------------|-----------------|---------------|---------------|-------|
| `LEGAL_001` | Settings | `Assets/Scenes/Stub/Settings/LEGAL_001_Settings.unity` | Social Tab → Gear Icon | **Should** | Grouped settings list: Account (Email, Password reset), Notifications (Push toggles), Audio (SFX/Music sliders), Accessibility (VoiceOver, Dynamic Type toggles). All toggles/sliders functional locally (no save). Logout button (return to AUTH_001). |
| `LEGAL_002` | Privacy Policy | `Assets/Scenes/Stub/Settings/LEGAL_002_Privacy.unity` | Settings → Privacy | **Later** | Scrollable lorem ipsum text (500 words). Back button. No scene created. |
| `LEGAL_003` | Terms of Service | `Assets/Scenes/Stub/Settings/LEGAL_003_Terms.unity` | Settings → Terms | **Later** | Scrollable lorem ipsum text (800 words). Back button. No scene created. |

---

## 3. Phase B Must-Have Stub Set (Minimum for Scaffold)

The following 18 screens/prefabs are **REQUIRED** for Empire Lead scaffold to validate 4-tab IA, HUD integration, and overlay system wiring. All Must stubs must:
1. Exist as Unity scenes or prefabs at specified paths
2. Be added to Build Settings (Scenes in Build)
3. Have basic canvas structure (UI Camera + EventSystem)
4. Wire bottom nav tabs to respective tab home scenes (Map→MAP_003, Fleet→FLEET_001, Empire→EMPIRE_001, Social→SOCIAL_001)

### Must-Have Checklist

#### Boot & Core Flow
- [ ] `BOOT_001_Splash.unity` — Splash with auto-advance to Login
- [ ] `AUTH_001_Login.unity` — Login screen navigates to Local Space HUD

#### HUD & Navigation Chrome
- [ ] `MAP_003_LocalSpaceHUD.unity` — **PRIMARY SCENE** with all HUD prefabs integrated:
  - [ ] `HUD_Root.prefab` wired (status strip with dummy cash/energy/shields/damage values)
  - [ ] `BottomNav_MapFleetEmpireSocial.prefab` wired (4 tabs switch scenes: Map→MAP_003, Fleet→FLEET_001, Empire→EMPIRE_001, Social→SOCIAL_001)
  - [ ] `Minimap.prefab` positioned bottom-right (10% screen width, static sector grid)
  - [ ] `SafeHarborChip.prefab` positioned top-right (tap opens OVERLAY_001)
  - [ ] `ActionStack.prefab` positioned right edge (3 stub buttons: Scan, Fire, Shields)

#### Map Tab Stubs
- [ ] `MAP_001_GalaxyOverview.unity` — Empty grid canvas + search bar stub
- [ ] `MAP_002_SectorGrid.unity` — 3 planet circles + 1 ship chevron, zoom button to Local Space
- [ ] `TargetSheet.prefab` — Slide-up sheet instantiated on contact tap, 4 action buttons (Scan/Lock/Fire/Retreat)
- [ ] `CombatRadial.prefab` — Radial menu with 6 weapon icons
- [ ] `Killmail.prefab` — Full-screen overlay with loss summary + Respawn button

#### Fleet Tab Stubs
- [ ] `FLEET_001_ActiveShipCard.unity` — Ship stats card with dummy values + action buttons

#### Empire Tab Stubs
- [ ] `EMPIRE_001_EmpireHome.unity` — Dashboard with networth card + planet count + attention queue (2 hardcoded alerts)

#### Social Tab Stubs
- [ ] `SOCIAL_001_AllianceHub.unity` — Alliance info card + chat panel embed
- [ ] `SOCIAL_002_Inbox.unity` — 8 hardcoded alerts in scrollable list
- [ ] `SOCIAL_006_Leaderboard.unity` — 20-row table with rank/player/networth/kills

#### Overlay System
- [ ] `SafeHarborExplainer.prefab` — Full-screen modal with 3 bullet points + Retreat button
- [ ] `ConfirmationDialog.prefab` — Generic confirm/cancel modal (configurable title/body)
- [ ] `LoadingSpinner.prefab` — Full-screen dimmed spinner
- [ ] `ErrorToast.prefab` — Bottom toast with 3s auto-dismiss

**Validation:** Empire Lead scaffold agent must confirm all 18 Must items are functional (scenes load, prefabs instantiate, nav transitions work) before proceeding to Should-have stubs.

---

## 4. Phase B Should-Have Stub Set

The following 12 screens reserve IDs and create empty placeholder scenes for future expansion. Should stubs:
1. Exist as empty Unity scenes (blank canvas, no UI)
2. Be added to Build Settings
3. Document path in this table (no wiring required)

**Purpose:** Pre-allocate scene IDs to avoid future rework when Client UX implements real UI.

### Should-Have Scenes
- [ ] `ONBOARD_001_IntroCinematic.unity` — Empty canvas + Skip button
- [ ] `ONBOARD_002_CreateCommander.unity` — Avatar picker + name input stubs
- [ ] `ONBOARD_003_NameStarterShip.unity` — Ship name input + 3D placeholder
- [ ] `ONBOARD_004_TutorialHUD.unity` — Local Space HUD + 3 coach marks
- [ ] `MAP_007_TravelOrderSheet.prefab` — Slide-up sheet with drive mode buttons
- [ ] `EMPIRE_002_PlanetList.unity` — 5 hardcoded planet cards
- [ ] `EMPIRE_003_PlanetDetail.unity` — Single planet view + production grid placeholder
- [ ] `EMPIRE_004_ProductionEditor.unity` — 6 resource sliders
- [ ] `TradeDockSheet.prefab` — Buy/Sell tabs + 6 resource rows
- [ ] `FLEET_002_ShipList.unity` — 3 hardcoded ship cards
- [ ] `FLEET_003_ShipDetail.unity` — Full stats view + upgrade preview section
- [ ] `FLEET_004_LoadoutEditor.unity` — 6 equipment slots + inventory list
- [ ] `SOCIAL_003_AlertDetail.unity` — Full alert message view
- [ ] `ChatPanel.prefab` — 10 hardcoded messages + input field
- [ ] `PushThreatBanner.prefab` — Slide-down alert banner
- [ ] `LEGAL_001_Settings.unity` — Grouped settings list with toggles/sliders

---

## 5. Phase B Later (Document Only)

The following 14 screens are **documented in this map** but have NO Unity assets created in Phase B. These IDs are reserved for future implementation by Client UX. No action required by scaffold agent.

### Later Screen IDs (No Files Created)
- `AUTH_002` — Character Select (multi-commander future feature)
- `ONBOARD_005–009` — Tutorial steps 2-6 (Scan/Claim/Produce/Trade/Combat)
- `ONBOARD_010` — Tutorial Safe Harbor Intro
- `MAP_008` — Wormhole Transit discovery flow
- `EMPIRE_006` — Treasury Summary (cash flow chart)
- `FLEET_005` — Hangar (ship purchase screen)
- `SOCIAL_005` — Sector Chat (proximity chat)
- `SOCIAL_007` — Team Management (invite/kick UI)
- `SOCIAL_008` — Spy Report sheet
- `OVERLAY_006` — Command Sheet (generic action sheet)
- `LEGAL_002` — Privacy Policy (lorem ipsum scroll)
- `LEGAL_003` — Terms of Service (lorem ipsum scroll)

**Note:** Later items appear in §2 Complete Screen Mapping Table with Unity paths for reference, but Empire Lead scaffold agent MUST NOT create these files. Client UX will implement when needed.

---

## 6. Gap Checklist for Empire Lead Scaffold Validation

This checklist ensures the scaffold agent satisfies all Designer Mobile UX Contract requirements (PR #4 Game Design §9) and Client UX stub expectations. **Client UX will re-check when scaffold PR lands.**

### 6.1 Navigation IA (§9.1 4-Tab Bottom Nav)
- [ ] Bottom nav bar exists as `BottomNav_MapFleetEmpireSocial.prefab`
- [ ] All 4 tabs present: Map (🌌), Fleet (🚀), Empire (👑), Social (👥)
- [ ] Tab order left-to-right: Map, Fleet, Empire, Social (matches Designer spec)
- [ ] Tapping Map tab loads `MAP_003_LocalSpaceHUD.unity`
- [ ] Tapping Fleet tab loads `FLEET_001_ActiveShipCard.unity`
- [ ] Tapping Empire tab loads `EMPIRE_001_EmpireHome.unity`
- [ ] Tapping Social tab loads `SOCIAL_001_AllianceHub.unity` (or `SOCIAL_002_Inbox.unity` fallback if no alliance)
- [ ] Bottom nav visible on all tab home screens (persistent across Map/Fleet/Empire/Social)
- [ ] Bottom nav hidden on overlay modals (Killmail, Safe Harbor Explainer, Confirmation Dialog)
- [ ] Tab icons display correctly (unicode or placeholder sprite)

### 6.2 HUD Elements (§9.1 HUD Requirements)
- [ ] HUD_Root prefab instantiated on `MAP_003_LocalSpaceHUD.unity`
- [ ] Status strip (top) shows 5 fields: Cash (₡), Energy (🔋), Shields (🛡), Damage (💔), Alliance badge (optional)
- [ ] Status strip dummy values: Cash=₡10,000, Energy=50,000, Shields=100%, Damage=0%
- [ ] Minimap positioned bottom-right corner (10% screen width per §9.1)
- [ ] Minimap shows static sector grid (9 squares, center square highlighted as player position)
- [ ] Safe Harbor chip positioned top-right (or near minimap if space constrained)
- [ ] Safe Harbor chip shows status: "Safe" (green) or "In Danger" (red pulse)
- [ ] Tapping Safe Harbor chip instantiates `SafeHarborExplainer.prefab` overlay
- [ ] Action stack positioned right edge (vertical stack, 3-6 buttons)
- [ ] Action stack buttons: Scan (top), Fire (middle), Shields (bottom) — all no-ops in Phase B
- [ ] Action stack buttons within thumb zone (bottom 60% of screen for one-handed use)

### 6.3 Overlay System (Modals & Toasts)
- [ ] `SafeHarborExplainer.prefab` instantiates as full-screen modal (dim background, close button)
- [ ] `ConfirmationDialog.prefab` instantiates centered with configurable title/body text
- [ ] Confirmation dialog has 2 buttons: Confirm (red) on left, Cancel (gray) on right
- [ ] `LoadingSpinner.prefab` instantiates full-screen with 0.5s artificial delay on scene transitions
- [ ] `ErrorToast.prefab` instantiates bottom of screen, auto-dismisses after 3s
- [ ] `Killmail.prefab` instantiates full-screen on death event (trigger: debug button on Local Space HUD for Phase B testing)
- [ ] Overlays close on back button press (Android) or swipe down (iOS) where appropriate

### 6.4 Screen State Stubs (Empty States & Errors)
- [ ] Inbox (`SOCIAL_002`) shows 8 hardcoded alerts (mix of red/yellow/green/blue threat levels)
- [ ] Inbox empty state (optional): "No new alerts" message when list cleared
- [ ] Leaderboard (`SOCIAL_006`) shows 20 hardcoded rows (placeholder names: "Player001", "Player002", etc.)
- [ ] Empire Home attention queue (`EMPIRE_001`) shows 2 hardcoded alerts (planet under attack, production maxed)
- [ ] Local Space HUD (`MAP_003`) shows empty center canvas with gray cube placeholder for ship 3D model
- [ ] Error toast triggers on button press (test button on Local Space HUD: "Trigger Error" → shows "Network error. Retry?" toast)

### 6.5 Gesture & Interaction Stubs
- [ ] Pinch-zoom gesture recognized on `MAP_001_GalaxyOverview` (Phase B: button-based zoom fallback OK)
- [ ] Tap planet on `MAP_002_SectorGrid` logs debug message (no navigation)
- [ ] Tap ship contact on `MAP_003_LocalSpaceHUD` instantiates `TargetSheet.prefab`
- [ ] Target sheet Fire button instantiates `CombatRadial.prefab`
- [ ] Combat radial weapon tap logs "Fired [Weapon]" debug message
- [ ] Long-press gesture recognized (Phase B: no action, but input system logs "Long press detected")
- [ ] Swipe right-to-left on bottom nav triggers tab switch animation (Phase B: instant scene switch OK)

### 6.6 Accessibility (Basic Placeholder Support)
- [ ] All scenes have UI Camera + EventSystem (Unity requirement for touch input)
- [ ] Text fields use Unity default font (scalable, supports Dynamic Type on device)
- [ ] Button tap areas ≥44pt (iOS) / 48dp (Android) minimum touch target size
- [ ] Error toast contrast ratio ≥4.5:1 (WCAG AA compliance) — Phase B: use Unity red (255,0,0) on black (0,0,0) background
- [ ] VoiceOver labels on bottom nav tabs: "Map Tab Button", "Fleet Tab Button", etc. (Unity Accessibility package not required for Phase B; document only)

### 6.7 Monetization Constraints (F2P Cosmetics Only, NO P2W)
- [ ] **Zero** UI elements for production speedups (no "Speed up 2x" buttons on Production Editor)
- [ ] **Zero** UI elements for combat-power boosts (no "Buy +50% Damage" in Loadout Editor)
- [ ] **Zero** UI elements for energy refills (no "Buy 10k Energy" on status strip)
- [ ] **Zero** UI elements for cargo expansion beyond ship class limits
- [ ] Social tab has placeholder "Cosmetic Shop" button (grayed out, tap logs "Shop not implemented")
- [ ] Cosmetic shop button labeled "Skins & Emotes" (Phase B: empty scene `SOCIAL_009_CosmeticShop.unity` optional)
- [ ] No IAP SKUs wired in Unity IAP (Phase B: Unity IAP package not imported)

### 6.8 Build Settings & Scene Management
- [ ] All Must scenes (18) added to Build Settings in order: Boot → Onboard → Map → Fleet → Empire → Social → Overlays → Settings
- [ ] All Should scenes (16) added to Build Settings (no specific order required)
- [ ] Scene load transitions use `LoadingSpinner.prefab` (0.5s artificial delay via `yield return new WaitForSeconds(0.5f)`)
- [ ] No missing prefab references (all prefabs in `Assets/Prefabs/UI/Stub/` directory exist and assigned)
- [ ] No console errors on Play Mode start (Unity Editor 6000.4.10f1)

### 6.9 Phase B Out of Scope (Confirmed Absent)
- [ ] **No** real FastAPI networking calls (no HTTP requests, no WebSocket connections)
- [ ] **No** real game logic (no production rate calculations, no combat damage formulas, no trade pricing)
- [ ] **No** real 3D ship models (gray cube placeholders OK)
- [ ] **No** real art assets (white squares for planets, unicode icons for UI, placeholder sprites)
- [ ] **No** real Firebase Auth (email/password input stubs only, Sign In button hardwired to Local Space HUD)
- [ ] **No** real push notifications (PushThreatBanner prefab created but not wired to OS notification service)
- [ ] **No** real player account system (single hardcoded player, no multi-user support)
- [ ] **No** real Unity IAP (no store integration, no receipt validation)

---

## 7. Out of Scope for Phase B

The following are **explicitly excluded** from Phase B scaffold and MUST NOT be implemented by Empire Lead scaffold agent:

### 7.1 Game Logic & Networking
- Real FastAPI backend integration (stub scenes have no HTTP/WebSocket calls)
- Celery task queue UI (no production/combat tick polling)
- Real-time multiplayer (no shared state, no player-to-player visibility)
- Real combat calculations (no damage formulas, no physics simulation)
- Real production cycles (no 55s ticks, no resource generation)
- Real trade pricing (no dynamic market, no supply/demand)
- Real travel physics (no acceleration curves, no distance calculations)

### 7.2 Visual Assets & Polish
- Real 3D ship models (gray cube placeholders only)
- Real planet textures (colored circles only)
- Real particle effects (no engine trails, no shield shimmers, no explosions)
- Real UI art (Unity default UI sprites only)
- Real animations (no smooth transitions, instant scene switches OK)
- Real sound effects / music (silent client OK)

### 7.3 Platform Integration
- Firebase Authentication (stub login screen, no real OAuth)
- Push notifications (PushThreatBanner prefab exists but not wired to OS)
- Unity IAP (no in-app purchase store)
- Unity Analytics (no telemetry)
- Crashlytics / error reporting (no crash logging)
- Leaderboard backend (hardcoded 20 rows only)

### 7.4 Advanced Features
- Tutorial engine (coach marks hardcoded, no step tracking)
- AI bots / NPC ships (no entity AI)
- Fog of war calculations (static dimmed sectors only)
- Wormhole discovery logic (screen stub only, no scan mechanics)
- Safe Harbor rent payments (explainer modal only, no billing)
- Alliance management (alliance info card only, no invite/kick)
- Chat server (hardcoded local messages only)
- Spy reports (prefab stub only, no intel gathering)

### 7.5 Production Features Explicitly Forbidden
- **Production speedups UI** — NO "Speed up 2x", "Instant production", or time-skip buttons
- **Combat-power boosts UI** — NO "Buy +50% damage", "Buy shield pack", or stat-boost IAPs
- **Energy refill UI** — NO "Buy 10k energy" or energy-purchase buttons
- **Cargo expansion beyond ship class limits** — NO "Buy +50 cargo" upgrades
- **Pay-to-win monetization** — ZERO gameplay-advantage IAPs (cosmetics only per Empire Lead policy)

---

## 8. Success Criteria

Phase B scaffold is **complete** when:

1. **All 18 Must scenes/prefabs exist** and are functional per §3 Must-Have Checklist
2. **All 16 Should scenes/prefabs exist** as empty placeholders per §4 Should-Have Stub Set
3. **Gap checklist (§6) is 100% satisfied** — Empire Lead scaffold agent validates all 60+ items
4. **Unity Editor 6000.4.10f1 Play Mode** launches without errors:
   - Splash → Login → Local Space HUD path works
   - Bottom nav switches between Map/Fleet/Empire/Social tabs
   - Overlays instantiate (Safe Harbor Explainer, Confirmation Dialog, Loading Spinner, Error Toast)
   - HUD prefabs display correctly (status strip, minimap, Safe Harbor chip, action stack)
5. **Build Settings** include all Must + Should scenes in correct order
6. **No P2W UI elements present** — §6.7 monetization checklist 100% satisfied
7. **Document PR open** — This `PHASE_B_UNITY_STUB_SCREEN_MAP.md` committed to `docs/` directory

**Validation Method:** Client UX will:
1. Clone scaffold PR branch
2. Open Unity 6000.4.10f1 project
3. Run through Must-Have Checklist (§3) manually (tap tabs, open overlays, verify paths)
4. Run through Gap Checklist (§6) line-by-line
5. Confirm zero P2W UI elements (§6.7)
6. Approve scaffold PR if all criteria met

**Non-Blocking Issues (OK for Phase B):**
- Missing 3D ship models (gray cube placeholder acceptable)
- Missing planet textures (colored circles acceptable)
- Missing animations (instant transitions acceptable)
- Empty game logic (no-op buttons acceptable)
- Hardcoded dummy data (acceptable for all stubs)

**Blocking Issues (Must Fix Before Approval):**
- Missing Must scenes/prefabs
- Bottom nav not functional (tabs don't switch scenes)
- Overlays don't instantiate
- HUD prefabs not wired to Local Space HUD
- P2W UI elements present (violates Empire Lead policy)
- Unity console errors on Play Mode

---

## Appendix A: Screen ID Reference (PR #4 Inventory)

This table cross-references all 44 screen IDs from `PHASE1B_SCREEN_INVENTORY.md` (PR #4, branch `cursor/phase1b-mobile-ux-vision-2ef6`) to confirm 100% coverage in Phase B mapping.

| Inventory Section | Screen Count | IDs Covered | Phase B Status |
|-------------------|--------------|-------------|----------------|
| Boot & Auth | 3 | `BOOT_001`, `AUTH_001`, `AUTH_002` | 2 Must, 1 Later |
| Onboarding | 7 | `ONBOARD_001–010` (consolidates 005-009) | 4 Should, 3 Later |
| Map Tab | 8 | `MAP_001–008` | 5 Must, 1 Should, 2 Later |
| Empire Tab | 6 | `EMPIRE_001–006` | 2 Must, 3 Should, 1 Later |
| Fleet Tab | 5 | `FLEET_001–005` | 1 Must, 3 Should, 1 Later |
| Social Tab | 8 | `SOCIAL_001–008` | 3 Must, 2 Should, 3 Later |
| Overlays | 6 | `OVERLAY_001–006` | 4 Must, 1 Should, 1 Later |
| Settings & Legal | 3 | `LEGAL_001–003` | 1 Should, 2 Later |
| **Total** | **44** | **All IDs mapped** | **18 Must, 16 Should, 14 Later (4 consolidated)** |

**Coverage Validation:** All 44 screen IDs from PR #4 inventory appear in §2 Complete Screen Mapping Table. Zero screens omitted.

---

## Appendix B: Unity 6000.4.10f1 Setup Notes

### B.1 Project Structure
```
Assets/
├── Scenes/
│   └── Stub/
│       ├── Boot/
│       ├── Onboard/
│       ├── Map/
│       ├── Empire/
│       ├── Fleet/
│       ├── Social/
│       ├── Overlays/
│       └── Settings/
├── Prefabs/
│   └── UI/
│       └── Stub/
│           ├── Shared/
│           ├── Map/
│           ├── Empire/
│           ├── Fleet/
│           ├── Social/
│           └── Overlays/
└── Scripts/
    └── Stub/
        ├── Navigation/
        │   └── BottomNavController.cs
        ├── Overlays/
        │   └── OverlayManager.cs
        └── HUD/
            └── HUDController.cs
```

### B.2 Required Unity Packages
- **Unity UI** (com.unity.ugui) — Default UI package (always installed)
- **TextMeshPro** (com.unity.textmeshpro) — For better text rendering (optional, Unity default UI Text OK for Phase B)
- **Input System** (com.unity.inputsystem) — For touch/gesture handling (optional, legacy Input OK for Phase B)

**NO** packages required for Phase B beyond Unity defaults. Avoid:
- Unity IAP (not needed until monetization implementation)
- Firebase SDK (not needed until real auth)
- Photon/Mirror networking (no multiplayer in Phase B)

### B.3 Build Settings Configuration
1. **Platform:** Switch to iOS or Android (Project Settings → Player)
2. **Orientation:** Portrait only (lock landscape off per mobile UX)
3. **Scenes in Build:** Add all Must + Should scenes in §3-4 order
4. **Bundle Identifier:** `com.galacticempire.mobile.stub` (placeholder)
5. **Version:** `0.1.0-phaseb-stub` (semantic versioning for Phase B)

### B.4 Canvas Setup (All Scenes)
Every scene must have:
- **Canvas** (UI Mode: Screen Space - Overlay)
- **Canvas Scaler** (UI Scale Mode: Scale With Screen Size, Reference Resolution: 1080×1920, Match: 0.5)
- **EventSystem** (for touch input)

**Safe Area:** Account for iPhone notch/home indicator via SafeArea script (optional for Phase B, hardwired later).

---

## Document Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-09-11 | Client UX | Initial Phase B Unity stub screen map. Covers all 44 screens from PR #4 inventory. Must/Should/Later priority matrix + gap checklist. |

---

**End of Document**
