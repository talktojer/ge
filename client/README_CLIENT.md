# Galactic Empire - Unity Client

Unity Editor 6000.4.10f1 mobile client for iOS and Android.

## Opening in Unity Editor

1. Install Unity Hub
2. Install Unity Editor **6000.4.10f1** (exact version required)
3. Open Unity Hub → Projects → Add → Select this `client/` directory
4. Unity will recognize the project structure and open it

## Project Structure

```
client/
├── Assets/               # Unity assets
│   ├── Scenes/          # Scene files
│   │   ├── Boot.unity          # Splash/loading
│   │   ├── Login.unity         # Authentication
│   │   ├── Onboarding.unity    # Tutorial
│   │   └── Main.unity          # 4-tab main view
│   ├── Scripts/         # C# gameplay scripts
│   │   ├── Core/              # Framework (state, networking)
│   │   ├── UI/                # UI controllers
│   │   │   ├── Map/           # Map tab
│   │   │   ├── Fleet/         # Fleet tab
│   │   │   ├── Empire/        # Empire tab
│   │   │   └── Social/        # Social tab
│   │   ├── Networking/        # WebSocket + REST client
│   │   └── Game/              # Game logic
│   ├── Prefabs/         # Reusable UI prefabs
│   │   ├── HUD/              # Top bar, minimap, action button
│   │   ├── Tabs/             # Tab content containers
│   │   └── Modals/           # Sheets, dialogs, overlays
│   └── Resources/       # Addressables catalog
├── ProjectSettings/     # Unity project settings
│   ├── ProjectSettings.asset  # Build targets: iOS + Android
│   ├── EditorBuildSettings.asset
│   └── ...
└── Packages/           # Unity package manifest
    └── manifest.json   # Dependencies
```

## Build Targets

- **iOS**: Requires macOS with Xcode
- **Android**: Requires Android SDK (via Unity Hub)

## Architecture

### 4-Tab Navigation (per PHASE1B_CLIENT_UX_VISION.md)

1. **Map** 🌌 - Galaxy/Sector/Local space navigation
2. **Fleet** 🚀 - Ship roster, loadout, travel
3. **Empire** 👑 - Planet management, production, treasury
4. **Social** 👥 - Alliance, leaderboard, inbox, settings

### HUD Elements (per PHASE1B_GAME_DESIGN.md §9.1)

- **Top Bar**: Cash, energy, ship status, alliance badge
- **Contextual Action Button**: Center-bottom primary CTA
- **Minimap**: 10% bottom-right corner
- **Bottom Tab Bar**: 4 tabs (portrait+landscape safe area)

### Networking

- **REST API**: Firebase JWT → FastAPI `/auth/exchange` → game API token
- **WebSocket**: Real-time sector updates, combat events, push notifications
- **Offline Support**: Queue commands locally, sync on reconnect

## Combat Pacing

~6 second strategic tick (not twitch):
- Instant UI feedback (tap → optimistic update)
- Server resolves on next tick
- Client interpolates animations between ticks

## Production Cycles

55 second planet tick:
- Masked with progress bars
- Push notifications on completion
- Glanceable status in Empire tab

## Monetization

**F2P + Cosmetics ONLY** (LOCKED by Empire Lead):
- Ship skins, planet themes, flags, VFX, emotes
- **NO P2W**: Zero production speedups, combat power, energy refills

## Firebase Integration

Authentication via Firebase SDK:
- Sign in with Apple (iOS)
- Sign in with Google (iOS + Android)
- Email/password

Client obtains Firebase ID token → sends to FastAPI → receives game session JWT.

## Development Status

**Phase B Scaffold**: Project structure created, screens stubbed as TODO comments in scripts.
Full Unity Editor generation requires macOS for complete ProjectSettings generation.

## Next Steps

1. Open in Unity 6000.4.10f1 Editor
2. Install Firebase Unity SDK package
3. Create scene hierarchy for 4-tab navigation
4. Implement WebSocket client (see `server/` for API contract)
5. Build screen flows per `docs/PHASE1B_SCREEN_INVENTORY.md` (44 screens)

## Resources

- Game Design: `../docs/PHASE1B_GAME_DESIGN.md`
- UX Vision: `../docs/PHASE1B_CLIENT_UX_VISION.md`
- Screen Inventory: `../docs/PHASE1B_SCREEN_INVENTORY.md` (44 screens)
- Stack ADR: `../docs/PHASE1B_STACK_ADR.md`
