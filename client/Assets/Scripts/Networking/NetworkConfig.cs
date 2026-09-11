using UnityEngine;

namespace GalacticEmpire.Networking
{
    /// <summary>
    /// Network configuration for Galactic Empire API
    /// Defines the production API base URL and WebSocket endpoint
    /// </summary>
    public static class NetworkConfig
    {
        /// <summary>
        /// Production API base URL (no trailing slash)
        /// Points to the FastAPI backend hosted at ge.jersweb.net
        /// </summary>
        public const string API_BASE_URL = "https://ge.jersweb.net";

        /// <summary>
        /// WebSocket endpoint URL for real-time updates
        /// Uses secure WebSocket protocol (wss://) mounted at /ws per ADR
        /// </summary>
        public const string WEBSOCKET_URL = "wss://ge.jersweb.net/ws";

        /// <summary>
        /// Returns the full REST API base URL
        /// </summary>
        public static string GetApiUrl() => API_BASE_URL;

        /// <summary>
        /// Returns the WebSocket URL
        /// </summary>
        public static string GetWebSocketUrl() => WEBSOCKET_URL;

        /// <summary>
        /// Constructs a full API endpoint URL from a path
        /// </summary>
        /// <param name="path">API path (e.g., "/auth/exchange" or "player/profile")</param>
        /// <returns>Full URL with base and path</returns>
        public static string GetEndpointUrl(string path)
        {
            // Ensure path starts with / if not empty
            if (!string.IsNullOrEmpty(path) && !path.StartsWith("/"))
            {
                path = "/" + path;
            }
            return API_BASE_URL + path;
        }

#if UNITY_EDITOR
        /// <summary>
        /// Debug method to verify configuration in Unity Editor
        /// </summary>
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterAssembliesLoaded)]
        private static void LogConfiguration()
        {
            Debug.Log($"[NetworkConfig] API Base URL: {API_BASE_URL}");
            Debug.Log($"[NetworkConfig] WebSocket URL: {WEBSOCKET_URL}");
        }
#endif
    }
}
