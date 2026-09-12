using UnityEngine;

namespace GalacticEmpire.Core
{
    /// <summary>
    /// Core game state manager. Handles authentication state, player data, and game session.
    /// TODO: Implement Firebase Auth integration
    /// TODO: Implement session token management
    /// TODO: Implement offline queue for commands
    /// </summary>
    public class GameStateManager : MonoBehaviour
    {
        public static GameStateManager Instance { get; private set; }

        // Authentication state
        private bool isAuthenticated = false;
        private string sessionToken = null;
        private string playerId = null;

        public bool IsAuthenticated => isAuthenticated;
        public string SessionToken => sessionToken;
        public string PlayerId => playerId;

        // Game state
        private float lastServerSyncTime = 0f;
        private const float SERVER_SYNC_INTERVAL = 6f; // 6s tick per game design

        void Awake()
        {
            if (Instance == null)
            {
                Instance = this;
                DontDestroyOnLoad(gameObject);
            }
            else
            {
                Destroy(gameObject);
            }
        }

        void Start()
        {
            // TODO: Check for cached session token
            // TODO: Validate with backend
            // TODO: Load player data
        }

        void Update()
        {
            if (isAuthenticated)
            {
                // TODO: Handle periodic server sync
                // TODO: Process queued commands
            }
        }

        public void SetAuthenticationState(string token, string id)
        {
            sessionToken = token;
            playerId = id;
            isAuthenticated = true;
            // TODO: Establish WebSocket connection
        }

        public void Logout()
        {
            isAuthenticated = false;
            sessionToken = null;
            playerId = null;
            // TODO: Close WebSocket
            // TODO: Clear cached data
        }
    }
}
