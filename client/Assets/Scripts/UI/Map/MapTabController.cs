using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;
using GalacticEmpire.Networking;
using GalacticEmpire.Models;
using GalacticEmpire.Core;

namespace GalacticEmpire.UI.Map
{
    /// <summary>
    /// Map tab controller - Phase C2b implementation
    /// Shows galaxy overview, sector detail, and live WebSocket updates
    /// Contract: docs/PHASE_C2A_MAP_API.md (PR #15)
    /// </summary>
    public class MapTabController : MonoBehaviour
    {
        [Header("UI References")]
        [SerializeField] private Text statusText;
        [SerializeField] private Button loadGalaxyButton;
        [SerializeField] private Transform sectorListContainer;
        [SerializeField] private GameObject sectorButtonPrefab;
        [SerializeField] private Text sectorDetailText;
        [SerializeField] private Text liveUpdatesText;

        private APIClient apiClient;
        private WebSocketClient wsClient;
        private GalaxyOverviewResponse galaxyData;
        private SectorDetailResponse currentSectorDetail;
        private int? subscribedSectorId;

        void Start()
        {
            apiClient = new APIClient();
            
            if (GameStateManager.Instance != null && GameStateManager.Instance.IsAuthenticated)
            {
                apiClient.SetAuthToken(GameStateManager.Instance.SessionToken);
            }

            if (loadGalaxyButton != null)
            {
                loadGalaxyButton.onClick.AddListener(OnLoadGalaxyClicked);
            }

            SetStatus("Ready. Click 'Load Galaxy' to fetch sectors.");
        }

        void OnEnable()
        {
            if (GameStateManager.Instance != null && GameStateManager.Instance.IsAuthenticated)
            {
                apiClient?.SetAuthToken(GameStateManager.Instance.SessionToken);
            }
        }

        void OnDisable()
        {
            if (wsClient != null && subscribedSectorId.HasValue)
            {
                wsClient.UnsubscribeSector(subscribedSectorId.Value);
            }
        }

        private void OnDestroy()
        {
            if (wsClient != null)
            {
                wsClient.Disconnect();
            }
        }

        private void OnLoadGalaxyClicked()
        {
            if (GameStateManager.Instance == null || !GameStateManager.Instance.IsAuthenticated)
            {
                SetStatus("Error: Not authenticated. Please sign in first.");
                return;
            }

            SetStatus("Loading galaxy overview...");
            StartCoroutine(apiClient.GetGalaxyOverview(OnGalaxyLoaded, OnGalaxyError));
        }

        private void OnGalaxyLoaded(GalaxyOverviewResponse response)
        {
            galaxyData = response;
            int sectorCount = response.sectors?.Length ?? 0;
            SetStatus($"Galaxy loaded: {sectorCount} sectors in shard {response.shard_id}");
            DisplaySectorList();
        }

        private void OnGalaxyError(string error)
        {
            SetStatus($"Failed to load galaxy: {error}");
        }

        private void DisplaySectorList()
        {
            if (sectorListContainer == null)
            {
                Debug.LogWarning("[MapTab] No sector list container assigned");
                return;
            }

            foreach (Transform child in sectorListContainer)
            {
                Destroy(child.gameObject);
            }

            if (galaxyData == null || galaxyData.sectors == null)
            {
                return;
            }

            foreach (var sector in galaxyData.sectors)
            {
                GameObject buttonObj;
                
                if (sectorButtonPrefab != null)
                {
                    buttonObj = Instantiate(sectorButtonPrefab, sectorListContainer);
                }
                else
                {
                    buttonObj = new GameObject($"Sector_{sector.id}");
                    buttonObj.transform.SetParent(sectorListContainer);
                    buttonObj.AddComponent<Button>();
                    var text = buttonObj.AddComponent<Text>();
                    text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
                    text.color = Color.white;
                }

                var button = buttonObj.GetComponent<Button>();
                var buttonText = buttonObj.GetComponentInChildren<Text>();

                if (buttonText != null)
                {
                    buttonText.text = $"{sector.name} ({sector.x},{sector.y})\n{sector.sector_type} | Planets: {sector.planet_count} | Ships: {sector.ship_count}";
                }

                int sectorId = sector.id;
                button.onClick.AddListener(() => OnSectorClicked(sectorId));
            }
        }

        private void OnSectorClicked(int sectorId)
        {
            SetStatus($"Loading sector {sectorId}...");
            StartCoroutine(apiClient.GetSectorDetail(sectorId, OnSectorDetailLoaded, OnSectorDetailError));
        }

        private void OnSectorDetailLoaded(SectorDetailResponse response)
        {
            currentSectorDetail = response;
            SetStatus($"Sector {response.id} loaded. Connecting to WebSocket...");
            DisplaySectorDetail();
            ConnectWebSocketAndSubscribe(response.id);
        }

        private void OnSectorDetailError(string error)
        {
            SetStatus($"Failed to load sector: {error}");
        }

        private void DisplaySectorDetail()
        {
            if (sectorDetailText == null || currentSectorDetail == null)
            {
                return;
            }

            string detail = $"<b>{currentSectorDetail.name}</b> ({currentSectorDetail.x},{currentSectorDetail.y})\n";
            detail += $"Type: {currentSectorDetail.sector_type}\n\n";

            detail += $"<b>Planets ({currentSectorDetail.planets?.Length ?? 0}):</b>\n";
            if (currentSectorDetail.planets != null)
            {
                foreach (var planet in currentSectorDetail.planets)
                {
                    string owner = string.IsNullOrEmpty(planet.owner_name) ? "Unclaimed" : planet.owner_name;
                    detail += $"- {planet.name} (Owner: {owner})\n";
                }
            }

            detail += $"\n<b>Ships ({currentSectorDetail.ships?.Length ?? 0}):</b>\n";
            if (currentSectorDetail.ships != null)
            {
                foreach (var ship in currentSectorDetail.ships)
                {
                    detail += $"- {ship.class_type} (Owner: {ship.owner_name}) @ ({ship.position_x},{ship.position_y})\n";
                }
            }

            sectorDetailText.text = detail;
        }

        private void ConnectWebSocketAndSubscribe(int sectorId)
        {
            if (GameStateManager.Instance == null || !GameStateManager.Instance.IsAuthenticated)
            {
                SetStatus("Error: Not authenticated for WebSocket");
                return;
            }

            if (wsClient == null)
            {
                GameObject wsObj = new GameObject("WebSocketClient");
                wsObj.transform.SetParent(transform);
                wsClient = wsObj.AddComponent<WebSocketClient>();

                wsClient.OnAuthenticated += OnWebSocketAuthenticated;
                wsClient.OnSubscribed += OnWebSocketSubscribed;
                wsClient.OnSectorSnapshot += OnSectorSnapshot;
                wsClient.OnSectorDelta += OnSectorDelta;
                wsClient.OnError += OnWebSocketError;

                StartCoroutine(wsClient.Connect(GameStateManager.Instance.SessionToken));
            }

            if (subscribedSectorId.HasValue && subscribedSectorId.Value != sectorId)
            {
                wsClient.UnsubscribeSector(subscribedSectorId.Value);
            }

            subscribedSectorId = sectorId;
            wsClient.SubscribeSector(sectorId);
        }

        private void OnWebSocketAuthenticated(string playerId)
        {
            Debug.Log($"[MapTab] WebSocket authenticated as {playerId}");
        }

        private void OnWebSocketSubscribed(int sectorId)
        {
            SetStatus($"Subscribed to sector {sectorId}. Waiting for updates...");
            SetLiveUpdates("Waiting for first update...");
        }

        private void OnSectorSnapshot(WSSectorSnapshotMessage snapshot)
        {
            Debug.Log($"[MapTab] Received sector snapshot for sector {snapshot.sector_id}");
            SetLiveUpdates($"<b>Snapshot received</b> @ {snapshot.timestamp}\n");
            
            if (snapshot.data?.ships != null)
            {
                SetLiveUpdates($"Ships: {snapshot.data.ships.Length}\n", append: true);
                foreach (var ship in snapshot.data.ships)
                {
                    SetLiveUpdates($"- Ship {ship.id} @ ({ship.position_x},{ship.position_y}) heading {ship.heading}° speed {ship.speed}\n", append: true);
                }
            }
        }

        private void OnSectorDelta(WSSectorDeltaMessage delta)
        {
            Debug.Log($"[MapTab] Received sector delta tick {delta.tick} for sector {delta.sector_id}");
            
            // Derive tick and timestamp from first event with those fields (typically heartbeat)
            // when top-level tick is 0 or missing (live ge-sim doesn't send top-level tick)
            int displayTick = delta.tick;
            string displayTimestamp = delta.timestamp;
            
            if (delta.events != null && delta.events.Length > 0)
            {
                foreach (var evt in delta.events)
                {
                    if (evt.tick > 0 || !string.IsNullOrEmpty(evt.timestamp))
                    {
                        if (displayTick == 0 && evt.tick > 0)
                        {
                            displayTick = evt.tick;
                        }
                        if (string.IsNullOrEmpty(displayTimestamp) && !string.IsNullOrEmpty(evt.timestamp))
                        {
                            displayTimestamp = evt.timestamp;
                        }
                        if (displayTick > 0 && !string.IsNullOrEmpty(displayTimestamp))
                        {
                            break;
                        }
                    }
                }
            }
            
            string updates = $"<b>Tick {displayTick}</b> @ {displayTimestamp}\n";
            
            if (delta.events != null)
            {
                foreach (var evt in delta.events)
                {
                    if (evt.event_type == "heartbeat")
                    {
                        updates += $"- {evt.message}\n";
                    }
                    else if (evt.event_type == "ship_moved")
                    {
                        updates += $"- Ship {evt.ship_id} moved from ({evt.old_position?.x},{evt.old_position?.y}) to ({evt.new_position?.x},{evt.new_position?.y})\n";
                    }
                    else
                    {
                        updates += $"- {evt.event_type}: {evt.message}\n";
                    }
                }
            }

            SetLiveUpdates(updates);
        }

        private void OnWebSocketError(string error)
        {
            SetStatus($"WebSocket error: {error}");
        }

        private void SetStatus(string message)
        {
            if (statusText != null)
            {
                statusText.text = message;
            }
            Debug.Log($"[MapTab] {message}");
        }

        private void SetLiveUpdates(string message, bool append = false)
        {
            if (liveUpdatesText != null)
            {
                if (append)
                {
                    liveUpdatesText.text += message;
                }
                else
                {
                    liveUpdatesText.text = message;
                }
            }
        }
    }
}
