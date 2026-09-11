using UnityEngine;
using System;
using System.Threading.Tasks;

namespace GalacticEmpire.Networking
{
    /// <summary>
    /// REST API client for FastAPI backend
    /// Handles authentication, inventory, commands
    /// </summary>
    public class APIClient
    {
        private string baseUrl;
        private string authToken;

        public APIClient(string url)
        {
            baseUrl = url;
        }

        public void SetAuthToken(string token)
        {
            authToken = token;
        }

        // TODO: Implement REST endpoints:
        // - POST /auth/exchange (Firebase JWT -> session token)
        // - GET /player/profile
        // - GET /player/ships
        // - GET /player/planets
        // - POST /commands/move
        // - POST /commands/fire
        // - POST /commands/claim
        // - GET /sector/{x}/{y}
        // - POST /trade/buy
        // - POST /trade/sell
    }

    /// <summary>
    /// WebSocket client for real-time updates
    /// Handles sector subscriptions, combat events, production notifications
    /// </summary>
    public class WebSocketClient
    {
        private string wsUrl;
        private bool isConnected = false;

        public event Action<string> OnSectorUpdate;
        public event Action<string> OnCombatEvent;
        public event Action<string> OnProductionComplete;

        public WebSocketClient(string url)
        {
            wsUrl = url;
        }

        public async Task Connect(string authToken)
        {
            // TODO: Establish WebSocket connection with auth token
            // TODO: Handle reconnection logic
            isConnected = true;
        }

        public void SubscribeSector(int x, int y)
        {
            if (!isConnected) return;
            // TODO: Send SUBSCRIBE message {"type": "subscribe", "sector": {"x": x, "y": y}}
        }

        public void UnsubscribeSector(int x, int y)
        {
            if (!isConnected) return;
            // TODO: Send UNSUBSCRIBE message
        }

        public void Disconnect()
        {
            // TODO: Close WebSocket gracefully
            isConnected = false;
        }

        private void HandleMessage(string message)
        {
            // TODO: Parse JSON message and route to appropriate event
            // Message types:
            // - ship_moved
            // - combat_damage
            // - planet_production_complete
            // - player_joined_sector
            // - player_left_sector
        }
    }
}
