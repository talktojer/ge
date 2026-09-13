# Phase C2b: Locked Specifications

**Status**: PASS WITH NOTES  
**Date**: 2026-09-12  

## Locked-In Requirements

### 1. Exact API Paths - REST vs WebSocket

✅ **LOCKED**: Different trailing slash rules for REST vs WebSocket due to nginx routing.

**UPDATE (C2d post-PR#17)**: FastAPI now accepts both variants without redirect to prevent HTTPS→HTTP scheme downgrade.

**REST Endpoints (both variants work):**
- ✅ `GET /sectors` or `/sectors/` - Galaxy overview (no redirect)
- ✅ `GET /sectors/{id}` or `/sectors/{id}/` - Sector detail (no redirect)

**WebSocket Endpoint (both variants work):**
- ✅ `/ws` or `/ws/` - WebSocket connection (no redirect)

**Implementation:**
```csharp
// NetworkConfig.cs
public const string API_BASE_URL = "https://ge.jersweb.net";  // NO trailing slash
public const string WEBSOCKET_URL = "wss://ge.jersweb.net/ws/";  // WITH trailing slash

// REST calls - no trailing slash (but trailing slash also works now)
GetEndpointUrl("/sectors")        // → https://ge.jersweb.net/sectors
GetEndpointUrl("/sectors/{id}")   // → https://ge.jersweb.net/sectors/1

// WebSocket connection - with trailing slash (but bare /ws also works now)
WEBSOCKET_URL + "?token=" + token // → wss://ge.jersweb.net/ws/?token=...
```

**Why**: 
- **Original issue**: nginx routing required `/ws/` with trailing slash, returned 403 without it
- **C2d issue**: Live `/sectors` returned 307 redirect to `http://…/sectors/` (HTTPS→HTTP downgrade)
- **Fix**: FastAPI routes now dual-mounted (with and without trailing slash) to prevent any redirect
- Unity client can use either variant; both return 200 without redirect

---

### 2. Stub Sector Delta Timing (~5s)

✅ **LOCKED**: Accept stub sector_delta messages every ~5 seconds from Phase C2a server.

**Current Behavior:**
- Phase C2a server sends deltas every ~5 seconds
- Client receives and displays delta events in UI
- NOT YET: 6-second tick alignment per ADR

**UPDATE (C2d)**: Live ge-sim at ge.jersweb.net publishes real sector_delta every ~6s with NO top-level tick/timestamp. The `tick` and `timestamp` fields live inside `events[]` (particularly in the `heartbeat` event). Client now derives display tick/timestamp from first event with those fields.

**Future (Phase C2c):**
- Align with ge-sim 6s ship tick per ADR
- Current ~5s stub timing is acceptable for C2b

**Implementation:**
```csharp
// MapTabController.cs - OnSectorDelta handler
private void OnSectorDelta(WSSectorDeltaMessage delta)
{
    Debug.Log($"[MapTab] Received sector delta tick {delta.tick}");
    // Display tick events, ship movements, etc.
}
```

---

### 3. WebSocket Protocol: sector_id (Integer)

✅ **LOCKED**: WebSocket subscribe/unsubscribe uses `sector_id` (integer), NOT x/y coordinates.

**Message Schema:**
```json
{
  "type": "subscribe",
  "sector_id": 1
}
```

**NOT:**
```json
{
  "type": "subscribe",
  "sector": {"x": 5, "y": 5}
}
```

**Implementation:**
```csharp
// Models/MapModels.cs
[Serializable]
public class WSSubscribeMessage : WSMessage
{
    public int sector_id;  // INTEGER, not coords
}

// NetworkClients.cs - WebSocketClient
public void SubscribeSector(int sectorId)  // INT parameter
{
    var message = new WSSubscribeMessage
    {
        type = "subscribe",
        sector_id = sectorId  // INTEGER field
    };
    SendMessage(message);
}
```

**Why**: Phase C2a server expects integer sector IDs, not x/y grid coordinates. Galaxy overview returns sector stubs with `id` field (integer).

---

### 4. Live Smoke Test Dependency

✅ **ACKNOWLEDGED**: Live smoke test against `https://ge.jersweb.net` requires Phase C2a merge + redeploy.

**Current State:**
- Phase C2a APIs implemented (PR #15) - **NOT YET MERGED**
- Phase C2b client ready - **THIS PR**
- Server NOT deployed to `ge.jersweb.net` yet

**Testing Options:**

**Option A: Local Testing (Available Now)**
```bash
# Terminal 1: Start Phase C2a server locally
cd server
docker-compose -f docker-compose.dev.yml up

# Terminal 2: Unity Editor
# Update NetworkConfig.cs for local testing:
# API_BASE_URL = "http://localhost:8000"
# WEBSOCKET_URL = "ws://localhost:8000/ws"
```

**Option B: Live Testing (After C2a Deploy)**
```bash
# No changes needed - uses production URLs:
# API_BASE_URL = "https://ge.jersweb.net"
# WEBSOCKET_URL = "wss://ge.jersweb.net/ws"
```

**Deployment Sequence:**
1. Review Phase C2a (PR #15) ✅ DONE
2. Merge Phase C2a → master ⏳ PENDING
3. Deploy C2a to `ge.jersweb.net` ⏳ PENDING
4. Review Phase C2b (PR #16) ← **YOU ARE HERE**
5. Test C2b against live server ⏳ BLOCKED ON C2a DEPLOY
6. Merge Phase C2b → master ⏳ PENDING

---

## Verification Checklist

✅ **REST paths**: `/sectors` and `/sectors/{id}` with NO trailing slash  
✅ **WebSocket path**: `/ws/` with TRAILING SLASH (nginx requirement on live host)  
✅ **sector_id**: Integer field in subscribe/unsubscribe messages  
✅ **Delta timing**: ~5s stub timing accepted for C2b (6s ADR is C2c)  
✅ **Dependencies**: Live test blocked on C2a merge+redeploy (local test OK)  

---

## Code Review Sign-Off

**Requirement 1 (Exact Paths)**: ✅ PASS
- NetworkConfig.cs: REST no trailing slash, WebSocket WITH trailing slash
- GetEndpointUrl(): Correct REST path construction
- WEBSOCKET_URL: `/ws/` with trailing slash per nginx routing (live host @ c1ea2ea)

**Requirement 2 (Delta Timing)**: ✅ PASS
- Client accepts ~5s deltas
- ADR 6s alignment deferred to C2c

**Requirement 3 (sector_id Protocol)**: ✅ PASS
- WSSubscribeMessage uses `int sector_id`
- SubscribeSector() takes int parameter
- No x/y coord usage in WebSocket protocol

**Requirement 4 (Deployment Dependency)**: ✅ ACKNOWLEDGED
- Local testing available now
- Live testing blocked on C2a deploy
- Documentation clear about dependency

---

**Phase C2b Status**: ✅ LOCKED AND READY FOR MERGE (after C2a deploy)

**Last Updated**: 2026-09-12  
**Reviewed By**: Stack  
**Approval**: PASS WITH NOTES
