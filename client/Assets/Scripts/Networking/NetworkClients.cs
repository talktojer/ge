using UnityEngine;
using UnityEngine.Networking;
using System;
using System.Collections;
using GalacticEmpire.Models;

namespace GalacticEmpire.Networking
{
    /// <summary>
    /// REST API client for FastAPI backend
    /// Handles authentication, inventory, commands
    /// Contract: docs/PHASE_C2A_MAP_API.md (PR #15)
    /// </summary>
    public class APIClient
    {
        private string baseUrl;
        private string authToken;

        public APIClient(string url = null)
        {
            baseUrl = url ?? NetworkConfig.GetApiUrl();
        }

        public void SetAuthToken(string token)
        {
            authToken = token;
        }

        public IEnumerator GetGalaxyOverview(Action<GalaxyOverviewResponse> onSuccess, Action<string> onError)
        {
            string url = NetworkConfig.GetEndpointUrl("/sectors/");
            Debug.Log($"[APIClient] GET {url}");

            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                if (!string.IsNullOrEmpty(authToken))
                {
                    request.SetRequestHeader("Authorization", $"Bearer {authToken}");
                }

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    string responseText = request.downloadHandler.text;
                    Debug.Log($"[APIClient] Galaxy overview response: {responseText}");

                    try
                    {
                        GalaxyOverviewResponse response = JsonUtility.FromJson<GalaxyOverviewResponse>(responseText);
                        onSuccess?.Invoke(response);
                    }
                    catch (Exception ex)
                    {
                        Debug.LogError($"[APIClient] Parse error: {ex.Message}");
                        onError?.Invoke($"Parse error: {ex.Message}");
                    }
                }
                else
                {
                    Debug.LogError($"[APIClient] Galaxy overview failed: {request.error}");
                    onError?.Invoke(request.error);
                }
            }
        }

        public IEnumerator GetSectorDetail(int sectorId, Action<SectorDetailResponse> onSuccess, Action<string> onError)
        {
            string url = NetworkConfig.GetEndpointUrl($"/sectors/{sectorId}");
            Debug.Log($"[APIClient] GET {url}");

            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                if (!string.IsNullOrEmpty(authToken))
                {
                    request.SetRequestHeader("Authorization", $"Bearer {authToken}");
                }

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    string responseText = request.downloadHandler.text;
                    Debug.Log($"[APIClient] Sector detail response: {responseText}");

                    try
                    {
                        SectorDetailResponse response = JsonUtility.FromJson<SectorDetailResponse>(responseText);
                        onSuccess?.Invoke(response);
                    }
                    catch (Exception ex)
                    {
                        Debug.LogError($"[APIClient] Parse error: {ex.Message}");
                        onError?.Invoke($"Parse error: {ex.Message}");
                    }
                }
                else
                {
                    Debug.LogError($"[APIClient] Sector detail failed: {request.error}");
                    onError?.Invoke(request.error);
                }
            }
        }

        public IEnumerator PostMove(MoveCommandRequest moveRequest, Action<MoveCommandResponse> onSuccess, Action<string> onError)
        {
            string url = NetworkConfig.GetEndpointUrl("/commands/move/");
            string jsonBody = JsonUtility.ToJson(moveRequest);
            Debug.Log($"[APIClient] POST {url} body: {jsonBody}");

            using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
            {
                byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonBody);
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");

                if (!string.IsNullOrEmpty(authToken))
                {
                    request.SetRequestHeader("Authorization", $"Bearer {authToken}");
                }

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    string responseText = request.downloadHandler.text;
                    Debug.Log($"[APIClient] Move response: {responseText}");

                    try
                    {
                        MoveCommandResponse response = JsonUtility.FromJson<MoveCommandResponse>(responseText);
                        onSuccess?.Invoke(response);
                    }
                    catch (Exception ex)
                    {
                        Debug.LogError($"[APIClient] Parse error: {ex.Message}");
                        onError?.Invoke($"Parse error: {ex.Message}");
                    }
                }
                else
                {
                    Debug.LogError($"[APIClient] Move command failed: {request.error}");
                    onError?.Invoke(request.error);
                }
            }
        }

        public IEnumerator PostFire(FireCommandRequest fireRequest, Action<FireCommandResponse> onSuccess, Action<string> onError)
        {
            string url = NetworkConfig.GetEndpointUrl("/commands/fire/");
            string jsonBody = JsonUtility.ToJson(fireRequest);
            Debug.Log($"[APIClient] POST {url} body: {jsonBody}");

            using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
            {
                byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonBody);
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");

                if (!string.IsNullOrEmpty(authToken))
                {
                    request.SetRequestHeader("Authorization", $"Bearer {authToken}");
                }

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    string responseText = request.downloadHandler.text;
                    Debug.Log($"[APIClient] Fire response: {responseText}");

                    try
                    {
                        FireCommandResponse response = JsonUtility.FromJson<FireCommandResponse>(responseText);
                        onSuccess?.Invoke(response);
                    }
                    catch (Exception ex)
                    {
                        Debug.LogError($"[APIClient] Parse error: {ex.Message}");
                        onError?.Invoke($"Parse error: {ex.Message}");
                    }
                }
                else
                {
                    Debug.LogError($"[APIClient] Fire command failed: {request.error}");
                    onError?.Invoke(request.error);
                }
            }
        }

        public IEnumerator PostClaim(ClaimCommandRequest claimRequest, Action<ClaimCommandResponse> onSuccess, Action<string> onError)
        {
            string url = NetworkConfig.GetEndpointUrl("/commands/claim/");
            string jsonBody = JsonUtility.ToJson(claimRequest);
            Debug.Log($"[APIClient] POST {url} body: {jsonBody}");

            using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
            {
                byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonBody);
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");

                if (!string.IsNullOrEmpty(authToken))
                {
                    request.SetRequestHeader("Authorization", $"Bearer {authToken}");
                }

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    string responseText = request.downloadHandler.text;
                    Debug.Log($"[APIClient] Claim response: {responseText}");

                    try
                    {
                        ClaimCommandResponse response = JsonUtility.FromJson<ClaimCommandResponse>(responseText);
                        onSuccess?.Invoke(response);
                    }
                    catch (Exception ex)
                    {
                        Debug.LogError($"[APIClient] Parse error: {ex.Message}");
                        onError?.Invoke($"Parse error: {ex.Message}");
                    }
                }
                else
                {
                    Debug.LogError($"[APIClient] Claim command failed: {request.error}");
                    onError?.Invoke(request.error);
                }
            }
        }

        // TODO: Implement remaining REST endpoints:
        // - GET /player/profile
        // - GET /player/ships
        // - GET /player/planets
        // - POST /trade/buy
        // - POST /trade/sell
    }

    /// <summary>
    /// WebSocket client for real-time updates
    /// Handles sector subscriptions, combat events, production notifications
    /// Contract: docs/PHASE_C2A_MAP_API.md (PR #15)
    /// </summary>
    public class WebSocketClient : MonoBehaviour
    {
        private string wsUrl;
        private bool isConnected = false;
        private System.Net.WebSockets.ClientWebSocket webSocket;
        private System.Threading.CancellationTokenSource cancellationTokenSource;

        public event Action<string> OnAuthenticated;
        public event Action<WSSectorSnapshotMessage> OnSectorSnapshot;
        public event Action<WSSectorDeltaMessage> OnSectorDelta;
        public event Action<string> OnError;
        public event Action<int> OnSubscribed;
        public event Action<int> OnUnsubscribed;

        private void Awake()
        {
            wsUrl = NetworkConfig.GetWebSocketUrl();
        }

        public IEnumerator Connect(string authToken)
        {
            if (isConnected)
            {
                Debug.LogWarning("[WebSocketClient] Already connected");
                yield break;
            }

            Debug.Log($"[WebSocketClient] Connecting to {wsUrl}?token=...");

            webSocket = new System.Net.WebSockets.ClientWebSocket();
            cancellationTokenSource = new System.Threading.CancellationTokenSource();

            string wsUrlWithToken = $"{wsUrl}?token={authToken}";

            var connectTask = webSocket.ConnectAsync(new Uri(wsUrlWithToken), cancellationTokenSource.Token);
            
            while (!connectTask.IsCompleted)
            {
                yield return null;
            }

            if (connectTask.IsFaulted)
            {
                Debug.LogError($"[WebSocketClient] Connection failed: {connectTask.Exception}");
                OnError?.Invoke($"Connection failed: {connectTask.Exception?.Message}");
                yield break;
            }

            isConnected = true;
            Debug.Log("[WebSocketClient] Connected successfully");

            StartCoroutine(ReceiveMessages());
        }

        private IEnumerator ReceiveMessages()
        {
            var buffer = new byte[8192];

            while (isConnected && webSocket.State == System.Net.WebSockets.WebSocketState.Open)
            {
                var segment = new ArraySegment<byte>(buffer);
                var receiveTask = webSocket.ReceiveAsync(segment, cancellationTokenSource.Token);

                while (!receiveTask.IsCompleted)
                {
                    yield return null;
                }

                if (receiveTask.IsFaulted)
                {
                    Debug.LogError($"[WebSocketClient] Receive error: {receiveTask.Exception}");
                    OnError?.Invoke($"Receive error: {receiveTask.Exception?.Message}");
                    yield break;
                }

                var result = receiveTask.Result;

                if (result.MessageType == System.Net.WebSockets.WebSocketMessageType.Close)
                {
                    Debug.Log("[WebSocketClient] Server closed connection");
                    isConnected = false;
                    yield break;
                }

                string message = System.Text.Encoding.UTF8.GetString(buffer, 0, result.Count);
                Debug.Log($"[WebSocketClient] Received: {message}");

                HandleMessage(message);
            }
        }

        public void SubscribeSector(int sectorId)
        {
            if (!isConnected)
            {
                Debug.LogWarning("[WebSocketClient] Not connected, cannot subscribe");
                return;
            }

            var message = new WSSubscribeMessage
            {
                type = "subscribe",
                sector_id = sectorId
            };

            SendMessage(message);
        }

        public void UnsubscribeSector(int sectorId)
        {
            if (!isConnected)
            {
                Debug.LogWarning("[WebSocketClient] Not connected, cannot unsubscribe");
                return;
            }

            var message = new WSSubscribeMessage
            {
                type = "unsubscribe",
                sector_id = sectorId
            };

            SendMessage(message);
        }

        private void SendMessage(object messageObj)
        {
            if (!isConnected) return;

            string json = JsonUtility.ToJson(messageObj);
            Debug.Log($"[WebSocketClient] Sending: {json}");

            byte[] bytes = System.Text.Encoding.UTF8.GetBytes(json);
            var segment = new ArraySegment<byte>(bytes);

            StartCoroutine(SendMessageAsync(segment));
        }

        private IEnumerator SendMessageAsync(ArraySegment<byte> segment)
        {
            var sendTask = webSocket.SendAsync(segment, System.Net.WebSockets.WebSocketMessageType.Text, true, cancellationTokenSource.Token);

            while (!sendTask.IsCompleted)
            {
                yield return null;
            }

            if (sendTask.IsFaulted)
            {
                Debug.LogError($"[WebSocketClient] Send error: {sendTask.Exception}");
            }
        }

        private void HandleMessage(string message)
        {
            try
            {
                var baseMsg = JsonUtility.FromJson<WSMessage>(message);

                switch (baseMsg.type)
                {
                    case "authenticated":
                        var authMsg = JsonUtility.FromJson<WSAuthenticatedMessage>(message);
                        Debug.Log($"[WebSocketClient] Authenticated as {authMsg.player_id}");
                        OnAuthenticated?.Invoke(authMsg.player_id);
                        break;

                    case "subscribed":
                        var subMsg = JsonUtility.FromJson<WSSubscribedMessage>(message);
                        Debug.Log($"[WebSocketClient] Subscribed to sector {subMsg.sector_id}");
                        OnSubscribed?.Invoke(subMsg.sector_id);
                        break;

                    case "unsubscribed":
                        var unsubMsg = JsonUtility.FromJson<WSSubscribedMessage>(message);
                        Debug.Log($"[WebSocketClient] Unsubscribed from sector {unsubMsg.sector_id}");
                        OnUnsubscribed?.Invoke(unsubMsg.sector_id);
                        break;

                    case "sector_snapshot":
                        var snapshotMsg = JsonUtility.FromJson<WSSectorSnapshotMessage>(message);
                        Debug.Log($"[WebSocketClient] Sector snapshot for sector {snapshotMsg.sector_id}");
                        OnSectorSnapshot?.Invoke(snapshotMsg);
                        break;

                    case "sector_delta":
                        var deltaMsg = JsonUtility.FromJson<WSSectorDeltaMessage>(message);
                        Debug.Log($"[WebSocketClient] Sector delta tick {deltaMsg.tick} for sector {deltaMsg.sector_id}");
                        OnSectorDelta?.Invoke(deltaMsg);
                        break;

                    case "error":
                        var errorMsg = JsonUtility.FromJson<WSErrorMessage>(message);
                        Debug.LogError($"[WebSocketClient] Error: {errorMsg.message}");
                        OnError?.Invoke(errorMsg.message);
                        break;

                    case "pong":
                        Debug.Log("[WebSocketClient] Pong received");
                        break;

                    default:
                        Debug.LogWarning($"[WebSocketClient] Unknown message type: {baseMsg.type}");
                        break;
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"[WebSocketClient] Message parse error: {ex.Message}");
            }
        }

        public void Disconnect()
        {
            if (!isConnected) return;

            Debug.Log("[WebSocketClient] Disconnecting...");

            isConnected = false;

            if (webSocket != null && webSocket.State == System.Net.WebSockets.WebSocketState.Open)
            {
                StartCoroutine(DisconnectAsync());
            }
        }

        private IEnumerator DisconnectAsync()
        {
            var closeTask = webSocket.CloseAsync(System.Net.WebSockets.WebSocketCloseStatus.NormalClosure, "Client disconnect", cancellationTokenSource.Token);

            while (!closeTask.IsCompleted)
            {
                yield return null;
            }

            webSocket?.Dispose();
            cancellationTokenSource?.Cancel();
            cancellationTokenSource?.Dispose();

            Debug.Log("[WebSocketClient] Disconnected");
        }

        private void OnDestroy()
        {
            Disconnect();
        }
    }
}
