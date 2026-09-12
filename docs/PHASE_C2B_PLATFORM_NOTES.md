# Phase C2b: Platform Compatibility Notes

## WebSocket Implementation

### Current Implementation

The WebSocket client uses `System.Net.WebSockets.ClientWebSocket` from .NET Standard 2.1, which is available in Unity 2021.2+ with .NET Standard 2.1 profile.

**Unity 6000.4.10f1** (Unity 6) uses **.NET Standard 2.1** by default, so `System.Net.WebSockets.ClientWebSocket` **should be available**.

### Platform Support

| Platform | System.Net.WebSockets Support | Notes |
|----------|------------------------------|-------|
| **Windows** | ✅ Full support | Native .NET WebSocket implementation |
| **macOS** | ✅ Full support | Native .NET WebSocket implementation |
| **Linux** | ✅ Full support | Native .NET WebSocket implementation |
| **iOS** | ⚠️ Limited | May require IL2CPP compatibility checks |
| **Android** | ⚠️ Limited | May require IL2CPP compatibility checks |
| **WebGL** | ❌ Not supported | Browser WebSocket required (JSLIB plugin) |

### Mobile Testing Required

The current implementation uses `System.Net.WebSockets.ClientWebSocket` which **should work on iOS/Android** with Unity 6, but requires testing on actual devices.

**If mobile compatibility issues arise**, consider these alternatives:

1. **Native WebSocket Plugin** (Recommended for Mobile):
   - [NativeWebSocket](https://github.com/endel/NativeWebSocket) - Unity package with native support
   - Supports WebGL, iOS, Android, and desktop

2. **WebSocketSharp** (C# Library):
   - [websocket-sharp](https://github.com/sta/websocket-sharp) - Pure C# implementation
   - Cross-platform but older codebase

3. **Unity WebSocket** (Asset Store):
   - Commercial plugins with full platform support

### Testing Checklist

Before deploying to mobile:
- [ ] Test WebSocket connection on Windows/macOS Editor (✅ should work)
- [ ] Test WebSocket connection in iOS build (⚠️ needs verification)
- [ ] Test WebSocket connection in Android build (⚠️ needs verification)
- [ ] Verify IL2CPP compatibility (iOS/Android requirement)
- [ ] Test secure WebSocket (wss://) on mobile devices
- [ ] Handle network interruptions (auto-reconnect)

### IL2CPP Considerations

Unity's IL2CPP (used for iOS/Android) may have issues with:
- Reflection (used in `MapSceneSetupHelper`)
- Async/await patterns
- System.Net sockets

**Mitigations**:
1. Test on IL2CPP builds early
2. Add `link.xml` to preserve types if needed
3. Consider native WebSocket plugin if issues arise

### WebGL Special Case

**WebGL cannot use System.Net.WebSockets** - browser WebSocket API must be used via JavaScript interop.

For WebGL support, implement a separate WebSocket client using JSLIB:

```csharp
#if UNITY_WEBGL && !UNITY_EDITOR
    // Use JSLIB WebSocket implementation
#else
    // Use System.Net.WebSockets.ClientWebSocket
#endif
```

## Coroutines and Async

### Current Design

The implementation uses **coroutines** (`IEnumerator`) for async operations:
- REST API calls: `StartCoroutine(apiClient.GetGalaxyOverview(...))`
- WebSocket operations: `StartCoroutine(wsClient.Connect(...))`

This is **Unity best practice** and works across all platforms.

### Why Not async/await?

Unity coroutines are preferred over .NET async/await for:
1. **Main thread guarantee**: Coroutines always run on Unity main thread
2. **GameObject lifecycle**: Coroutines stop when GameObject is destroyed
3. **Platform compatibility**: Works on all Unity platforms including WebGL
4. **Unity Editor integration**: Better debugging and profiling

The WebSocket client uses `async` internally for .NET socket operations, but exposes coroutine-based API to Unity code.

## Recommendations

### For Desktop/Editor Testing (Current Phase)
✅ Current implementation is sufficient

### For Mobile Development (Phase C2c+)
1. Test on actual iOS/Android devices
2. If `System.Net.WebSockets` issues arise:
   - Switch to **NativeWebSocket** package
   - Or implement platform-specific WebSocket backends
3. Add WebSocket reconnection logic for mobile network changes

### For WebGL Support (Future)
- Implement JSLIB-based WebSocket client
- Use conditional compilation for platform-specific implementations

---

**Current Status**: Implementation works on Windows/macOS/Linux Editor and likely iOS/Android builds. Mobile device testing required before production deployment.

**Recommended Next Step**: Test on iOS/Android devices in Phase C2c. If issues arise, integrate NativeWebSocket package.
