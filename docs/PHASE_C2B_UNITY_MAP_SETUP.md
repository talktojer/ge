# Phase C2b: Unity Map Client Setup

Unity client implementation for Map screen with REST and WebSocket integration.

## Overview

**Phase**: C2b - Unity Map Client  
**Depends on**: Phase C2a server APIs (PR #15)  
**Contract**: `docs/PHASE_C2A_MAP_API.md`

## What's Implemented

### Networking

✅ **REST API Client** (`NetworkClients.cs`)
- `GetGalaxyOverview()` - Calls GET /sectors
- `GetSectorDetail(sectorId)` - Calls GET /sectors/{id}
- Bearer token authentication from GameStateManager

✅ **WebSocket Client** (`NetworkClients.cs`)
- Connects to `/ws` with session token
- Subscribe/unsubscribe to sectors by ID
- Event handlers for:
  - `OnAuthenticated` - Connection established
  - `OnSectorSnapshot` - Initial sector state
  - `OnSectorDelta` - Periodic updates (~5s)
  - `OnError` - Error messages

✅ **Data Models** (`Models/MapModels.cs`)
- `GalaxyOverviewResponse` - Galaxy + sector list
- `SectorDetailResponse` - Sector detail + planets + ships
- WebSocket message types (snapshot, delta, events)

### Map UI Controller

✅ **MapTabController** (`UI/Map/MapTabController.cs`)
- Load galaxy overview (sector list)
- Click sector to load detail
- Auto-subscribe to WebSocket for selected sector
- Display live sector deltas in UI
- Unsubscribe on tab close

✅ **MapSceneSetupHelper** (`UI/Map/MapSceneSetupHelper.cs`)
- Programmatically creates Map UI if not assigned in Inspector
- Useful for quick testing without manual Unity Editor setup

### Authentication Integration

✅ **AuthController Updates**
- Stores session token in `GameStateManager.Instance`
- `GameStateManager` exposes `SessionToken`, `PlayerId`, `IsAuthenticated`

## Unity Editor Setup

### Boot Scene Setup (Required for Navigation)

1. Open `BOOT_001_Splash.unity` scene
2. Select any active GameObject (e.g., Canvas root)
3. Add Component: `BootToMapNavigation`
4. Configure (or leave defaults):
   - Map Scene Name: `MAP_001_GalaxyOverview` (default)
   - Button will auto-create after Sign in
5. Ensure `MAP_001_GalaxyOverview` scene is in Build Settings

**Result**: After Sign in (dev), a "Map" button appears and loads the Map scene with authentication token wired through `GameStateManager`.

### Option 1: Quick Test with MapSceneSetupHelper (Recommended)

1. Open Unity Editor 6000.4.10f1
2. Create a new scene: `File > New Scene` (or use existing `MAP_001_GalaxyOverview`)
3. Add an empty GameObject: `GameObject > Create Empty`
4. Name it "MapController"
5. Attach scripts:
   - Add `MapTabController` component
   - Add `MapSceneSetupHelper` component (will auto-create UI)
6. Ensure EventSystem with `InputSystemUIInputModule` exists (or will be created)
7. Press Play from Boot scene

The `MapSceneSetupHelper` will programmatically create all UI elements if they're not assigned.

**Important**: Project uses Input System. `MapSceneSetupHelper` creates `InputSystemUIInputModule` (NOT `StandaloneInputModule`).

### Option 2: Manual Scene Setup (Full Control)

1. Create a new scene: `File > New Scene`
2. Create Canvas: `GameObject > UI > Canvas`
3. Create UI elements:
   - **StatusText**: UI > Text (displays status messages)
   - **LoadGalaxyButton**: UI > Button (triggers galaxy load)
   - **SectorList**: UI > Scroll View (displays sector list)
   - **SectorDetail**: UI > Panel + Text (displays sector detail)
   - **LiveUpdates**: UI > Panel + Text (displays WebSocket deltas)
4. Create empty GameObject "MapController"
5. Attach `MapTabController` script
6. Assign UI references in Inspector:
   - `statusText` → StatusText component
   - `loadGalaxyButton` → LoadGalaxyButton component
   - `sectorListContainer` → Scroll View > Viewport > Content
   - `sectorButtonPrefab` → Create a prefab for sector buttons (Button + Text)
   - `sectorDetailText` → SectorDetail Text component
   - `liveUpdatesText` → LiveUpdates Text component

### EventSystem Requirement

**REQUIRED**: Project uses Input System (NOT Legacy Input).

Ensure an EventSystem with `InputSystemUIInputModule` exists:
- `GameObject > UI > Event System`
- Add Component: `InputSystemUIInputModule` (from Unity.InputSystem.UI)
- Remove any `StandaloneInputModule` components

`MapSceneSetupHelper` will auto-create EventSystem with correct `InputSystemUIInputModule` if missing.

## Testing the Map Client

### Prerequisites

1. **Server Running**: Start the Phase C2a server (PR #15 branch)
   ```bash
   cd server
   docker-compose -f docker-compose.dev.yml up
   ```

2. **Unity Project Open**: Unity Editor 6000.4.10f1 with `ge/client/` project

3. **Authenticated**: Sign in via Boot scene first to get session token

### Smoke Test Path

**In Unity Editor Play Mode:**

1. **Boot Scene**: Start from `BOOT_001_Splash.unity`
2. **Sign In**: Click "Sign in (dev)" button
   - Should display: "Signed in: player_..."
   - Session token stored in GameStateManager
   - "Map" button appears (enabled after auth)

3. **Navigate to Map**: Click "Map" button
   - Loads `MAP_001_GalaxyOverview` scene
   - Session token wired through GameStateManager

4. **Map Scene**:
   - Click "Load Galaxy" button
   - Should display: "Galaxy loaded: 5 sectors in shard alpha-1"
   - Sector list appears with 5 sectors:
     - Core Sector (5,5)
     - Nebula Expanse (5,6)
     - Asteroid Belt Alpha (6,5)
     - Safe Harbor Station (4,5)
     - Frontier Outpost (5,4)

5. **Select Sector**: Click any sector button (e.g., "Core Sector")
   - Status: "Loading sector 1..."
   - Sector detail panel shows:
     - Sector name, coordinates, type
     - 3 planets (Terra Prime, New Horizon, Mining Station 7)
     - 2 ships (frigate, scout)
   - Status: "Subscribed to sector 1. Waiting for updates..."

6. **Live Updates**: WebSocket deltas appear every ~5 seconds
   - "Tick 1 @ 2026-09-12T..."
   - "- Tick 1" (heartbeat)
   - "- Ship 201 moved from (5,5) to (6,5)" (example)

7. **Select Different Sector**: Click another sector
   - Unsubscribes from previous sector
   - Subscribes to new sector
   - New sector detail and live updates appear

### Expected Behavior

✅ **REST Calls**:
- GET /sectors returns 5 sectors
- GET /sectors/{id} returns sector detail

✅ **WebSocket**:
- Connects with `?token=<session_token>`
- Receives `authenticated` message
- Receives `subscribed` message
- Receives `sector_snapshot` immediately
- Receives `sector_delta` every ~5 seconds

✅ **UI Updates**:
- Status text shows operation progress
- Sector list displays all sectors
- Sector detail shows planets and ships
- Live updates show delta events

### Troubleshooting

**"Error: Not authenticated"**
- Ensure you've signed in via Boot scene first
- GameStateManager.Instance should have valid SessionToken

**"Failed to load galaxy: 401"**
- Session token expired or invalid
- Sign in again

**"WebSocket error: Connection failed"** or **"403 Forbidden"**
- Ensure server is running at `https://ge.jersweb.net` (or `http://localhost:8000` if testing locally)
- Check NetworkConfig.cs WEBSOCKET_URL has trailing slash: `wss://ge.jersweb.net/ws/`
- nginx routing requires trailing slash on live host (returns 403 without it)

**No sectors displayed**
- Check Console logs for API response
- Verify JSON parsing succeeded
- Check SectorListContainer is assigned

**No live updates**
- Check Console logs for WebSocket messages
- Verify WebSocket connected successfully
- Server should send deltas every ~5 seconds

## Integration with Boot Scene

**DONE**: Use `BootToMapNavigation` component (included in PR).

1. Open `BOOT_001_Splash.unity`
2. Select any active GameObject (e.g., Canvas root)
3. Add Component: `BootToMapNavigation`
4. Component will:
   - Auto-create "Map" button on Start
   - Enable button only when authenticated
   - Load `MAP_001_GalaxyOverview` scene on click
   - Wire GameStateManager session token through

**Play path**: Boot → Sign in (dev) → Map button appears → Click Map → Map scene loads with auth

## API Configuration

Configured in `NetworkConfig.cs`:
- **API_BASE_URL**: `https://ge.jersweb.net` (no trailing slash)
- **WEBSOCKET_URL**: `wss://ge.jersweb.net/ws/` (trailing slash REQUIRED for nginx)

For local testing, temporarily change to:
```csharp
public const string API_BASE_URL = "http://localhost:8000";
public const string WEBSOCKET_URL = "ws://localhost:8000/ws/";  // Keep trailing slash
```

## Known Limitations

- **Stub Data**: Server returns hardcoded 5 sectors (Phase C2a limitation)
- **No Persistence**: Sector changes are simulated, not real game state
- **Basic UI**: Functional but not final mobile UX
- **No Error Recovery**: WebSocket disconnect doesn't auto-reconnect yet

## Next Steps

**Phase C2c+** (Future):
1. Integrate real ge-sim tick engine events
2. Replace stub data with database queries
3. Polish Map UI for mobile (pinch-zoom, sector grid rendering)
4. Add minimap and sector navigation controls
5. WebSocket reconnection logic
6. Fog of war (sensor range visibility)

---

**Status**: Phase C2b implementation complete, ready for Editor testing  
**Last Updated**: 2026-09-12
