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

## Re-Static Fixes (Second Pass)

### 5. ✅ BootToMapNavigation Wired in Boot Scene

**Fixed**: `BootToMapNavigation` component now attached to AuthController GameObject in `BOOT_001_Splash.unity`.

**Scene Changes**:
```yaml
# BOOT_001_Splash.unity - AuthController GameObject
m_Component:
  - component: {fileID: 1000000035}  # Transform
  - component: {fileID: 1000000036}  # AuthController
  - component: {fileID: 1000000060}  # BootToMapNavigation (NEW)
```

**Component Definition**:
```yaml
--- !u!114 &1000000060
MonoBehaviour:
  m_Script: {fileID: 11500000, guid: 7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a, type: 3}
  mapSceneName: MAP_001_GalaxyOverview
  buttonPosition: {x: 0, y: -50}
  buttonSize: {x: 200, y: 60}
```

**Result**: Map button auto-creates on Boot scene Start, enabled after Sign in.

---

### 6. ✅ Map Scene in Build Settings

**Fixed**: `MAP_001_GalaxyOverview.unity` added to `EditorBuildSettings.asset`.

**Build Settings**:
```yaml
m_Scenes:
  - enabled: 1
    path: Assets/Scenes/Stub/Boot/BOOT_001_Splash.unity
    guid: 00000000000000000000000000000000
  - enabled: 1
    path: Assets/Scenes/Stub/Map/MAP_001_GalaxyOverview.unity
    guid: 6d9fb53b687e74d7cb957514e4f4eea2  # NEW
```

**Result**: `SceneManager.LoadScene("MAP_001_GalaxyOverview")` now works in Play mode.

---

**Status**: ✅ ALL CRITICAL FIXES APPLIED (SECOND PASS COMPLETE)

**Commits**:
- `a03baa2` - WebSocket trailing slash for nginx routing
- `3530a0c` - Input System, JsonUtility arrays, Boot → Map navigation
- `ae27d92` - Documentation updates
- `607aefc` - Wire BootToMapNavigation in Boot scene + add Map to build settings

**Ready for re-static review (second pass)**.

**Last Updated**: 2026-09-12
