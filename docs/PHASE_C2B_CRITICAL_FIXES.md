# Phase C2b: Critical Fixes (Static Review)

**Status**: Fixed per static UX review  
**Date**: 2026-09-12  

## Critical Fixes Applied

### 1. WebSocket Trailing Slash (nginx Routing)

**Issue**: Live nginx @ c1ea2ea requires `/ws/` WITH trailing slash. Bare `/ws` returns 403.

**Fix Applied**:
```csharp
// NetworkConfig.cs
public const string WEBSOCKET_URL = "wss://ge.jersweb.net/ws/";  // WITH trailing slash
```

**Connection**:
```csharp
// Connect as: wss://ge.jersweb.net/ws/?token=<session_token>
wsUrlWithToken = $"{WEBSOCKET_URL}?token={authToken}";
```

**REST vs WebSocket**:
- ✅ REST: `/sectors` and `/sectors/{id}` (NO trailing slash)
- ✅ WebSocket: `/ws/` (WITH trailing slash - nginx requirement)

---

### 2. Boot → Map Navigation

**Issue**: No visible navigation from Boot to Map. Play path required manual scene switch.

**Fix Applied**: Created `BootToMapNavigation` component.

**Setup**:
1. Attach `BootToMapNavigation` to any GameObject in `BOOT_001_Splash.unity`
2. Component auto-creates "Map" button on Start
3. Button enabled only when authenticated (checks `GameStateManager.IsAuthenticated`)
4. Click → Loads `MAP_001_GalaxyOverview` scene
5. Session token wired through `GameStateManager.Instance.SessionToken`

**Play Path (Fixed)**:
```
Boot → Sign in (dev) → Map button appears → Click Map → Map scene loads with auth
```

**Code**:
```csharp
// BootToMapNavigation.cs
private void OnMapButtonClicked()
{
    if (GameStateManager.Instance != null && GameStateManager.Instance.IsAuthenticated)
    {
        SceneManager.LoadScene("MAP_001_GalaxyOverview");
    }
}
```

---

### 3. Input System (InputSystemUIInputModule)

**Issue**: `MapSceneSetupHelper` was adding `StandaloneInputModule`. Project uses Input System only.

**Fix Applied**:
```csharp
// MapSceneSetupHelper.cs
using UnityEngine.InputSystem.UI;

private void EnsureEventSystem()
{
    var existingEventSystem = FindObjectOfType<EventSystem>();
    
    if (existingEventSystem == null)
    {
        var eventSystemObj = new GameObject("EventSystem");
        eventSystemObj.AddComponent<EventSystem>();
        eventSystemObj.AddComponent<InputSystemUIInputModule>();  // NOT StandaloneInputModule
        Debug.Log("[MapSceneSetup] Created EventSystem with InputSystemUIInputModule");
    }
    else
    {
        Debug.Log("[MapSceneSetup] Using existing EventSystem");
    }
}
```

**Why**: Project uses Unity Input System (not Legacy Input). `StandaloneInputModule` is legacy and incompatible.

---

### 4. JsonUtility Arrays (Serialization Fix)

**Issue**: `JsonUtility` cannot deserialize `List<T>` directly - requires arrays or wrapper classes.

**Fix Applied**: Replaced all `List<T>` with `T[]` arrays.

**Changes**:
```csharp
// MapModels.cs - BEFORE
public class GalaxyOverviewResponse
{
    public List<SectorStub> sectors;  // ❌ JsonUtility fails
}

// MapModels.cs - AFTER
public class GalaxyOverviewResponse
{
    public SectorStub[] sectors;  // ✅ JsonUtility works
}
```

**All Fixed Models**:
- `GalaxyOverviewResponse.sectors` → `SectorStub[]`
- `SectorDetailResponse.planets` → `PlanetData[]`
- `SectorDetailResponse.ships` → `ShipData[]`
- `SectorSnapshotData.ships` → `ShipData[]`
- `SectorSnapshotData.planets` → `PlanetData[]`
- `WSSectorDeltaMessage.events` → `SectorEvent[]`

**MapTabController Updates**:
```csharp
// Count changed from .Count to .Length
int sectorCount = response.sectors?.Length ?? 0;
int planetCount = currentSectorDetail.planets?.Length ?? 0;
int shipCount = snapshot.data.ships?.Length;
```

---

## Verification Checklist

✅ **WebSocket trailing slash**: `wss://ge.jersweb.net/ws/` (nginx requirement)  
✅ **REST no trailing slash**: `/sectors` and `/sectors/{id}` (correct)  
✅ **Boot → Map navigation**: `BootToMapNavigation` component wires flow  
✅ **Input System**: `InputSystemUIInputModule` (NOT Standalone)  
✅ **JsonUtility arrays**: All `List<T>` replaced with `T[]`  
✅ **Play path**: Boot Sign in → Map button → Map scene (no manual switch)  

---

## Testing After Fixes

**Play Path (Unity Editor)**:

1. Open `BOOT_001_Splash.unity`
2. Attach `BootToMapNavigation` to any GameObject (if not already)
3. Press Play
4. Click "Sign in (dev)"
   - Status: "Signed in: player_..."
   - "Map" button appears (enabled)
5. Click "Map" button
   - Loads `MAP_001_GalaxyOverview` scene
   - Session token wired through
6. Click "Load Galaxy"
   - Galaxy loaded: 5 sectors in shard alpha-1
7. Click sector → WebSocket connects to `wss://ge.jersweb.net/ws/?token=...`
8. Live deltas arrive every ~5s

**Expected Logs**:
```
[Auth] Session token acquired for player player_123
[BootToMapNav] Loading Map scene: MAP_001_GalaxyOverview
[MapTab] Loading galaxy overview...
[APIClient] GET https://ge.jersweb.net/sectors
[MapTab] Galaxy loaded: 5 sectors in shard alpha-1
[WebSocketClient] Connecting to wss://ge.jersweb.net/ws/?token=...
[WebSocketClient] Connected successfully
[WebSocketClient] Authenticated as player_123
```

---

## Files Changed

1. **client/Assets/Scripts/Networking/NetworkConfig.cs**
   - `WEBSOCKET_URL = "wss://ge.jersweb.net/ws/"` (trailing slash)

2. **client/Assets/Scripts/Models/MapModels.cs**
   - All `List<T>` → `T[]` arrays
   - Removed `System.Collections.Generic` import

3. **client/Assets/Scripts/UI/Map/MapTabController.cs**
   - `.Count` → `.Length` for array access
   - Null-safe array length checks

4. **client/Assets/Scripts/UI/Map/MapSceneSetupHelper.cs**
   - `StandaloneInputModule` → `InputSystemUIInputModule`
   - Added `using UnityEngine.InputSystem.UI`

5. **client/Assets/Scripts/UI/Boot/BootToMapNavigation.cs** (NEW)
   - Boot → Map navigation component
   - Auto-creates Map button
   - Wires GameStateManager session token

---

**Status**: ✅ ALL CRITICAL FIXES APPLIED

**Commits**:
- `a03baa2` - WebSocket trailing slash for nginx routing
- `3530a0c` - Input System, JsonUtility arrays, Boot → Map navigation

**Ready for re-static review**.

**Last Updated**: 2026-09-12
