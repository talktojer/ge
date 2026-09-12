using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;
using System.Collections;
using GalacticEmpire.Networking;
using GalacticEmpire.Core;

namespace GalacticEmpire.UI.Boot
{
    /// <summary>
    /// Auth controller for Boot splash scene
    /// Handles DEV bypass login and player profile retrieval
    /// </summary>
    public class AuthController : MonoBehaviour
    {
        [Header("UI References")]
        [SerializeField] private Button signInButton;
        [SerializeField] private Button whoAmIButton;
        [SerializeField] private Text authStatusText;

        private string sessionToken;

        private void Start()
        {
            if (signInButton != null)
            {
                signInButton.onClick.AddListener(OnSignInClicked);
            }

            if (whoAmIButton != null)
            {
                whoAmIButton.onClick.AddListener(OnWhoAmIClicked);
                whoAmIButton.interactable = false; // Disabled until login
            }

            if (authStatusText != null)
            {
                authStatusText.text = "Ready to sign in";
            }
        }

        private void OnSignInClicked()
        {
            StartCoroutine(SignInCoroutine());
        }

        private void OnWhoAmIClicked()
        {
            StartCoroutine(WhoAmICoroutine());
        }

        private IEnumerator SignInCoroutine()
        {
            if (authStatusText != null)
            {
                authStatusText.text = "Signing in...";
            }

            string exchangeUrl = NetworkConfig.GetEndpointUrl("/auth/exchange");
            Debug.Log($"[Auth] Calling {exchangeUrl}");

            // Use DEV bypass token
            string devToken = "ge-dev-user-jeremy";
            string jsonBody = $"{{\"dev_token\":\"{devToken}\"}}";

            using (UnityWebRequest request = new UnityWebRequest(exchangeUrl, "POST"))
            {
                byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonBody);
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    string responseText = request.downloadHandler.text;
                    Debug.Log($"[Auth] Exchange response: {responseText}");

                    SessionTokenResponse response = JsonUtility.FromJson<SessionTokenResponse>(responseText);
                    sessionToken = response.session_token;

                    if (authStatusText != null)
                    {
                        authStatusText.text = $"Signed in: {response.player_id}";
                    }

                    // Enable Who am I button
                    if (whoAmIButton != null)
                    {
                        whoAmIButton.interactable = true;
                    }

                    // Store session in GameStateManager
                    if (GameStateManager.Instance != null)
                    {
                        GameStateManager.Instance.SetAuthenticationState(sessionToken, response.player_id);
                    }

                    Debug.Log($"[Auth] Session token acquired for player {response.player_id}");
                }
                else
                {
                    Debug.LogError($"[Auth] Sign in failed: {request.error}");

                    if (authStatusText != null)
                    {
                        authStatusText.text = $"Sign in failed: {request.error}";
                    }
                }
            }
        }

        private IEnumerator WhoAmICoroutine()
        {
            if (string.IsNullOrEmpty(sessionToken))
            {
                if (authStatusText != null)
                {
                    authStatusText.text = "No session token. Sign in first.";
                }
                yield break;
            }

            if (authStatusText != null)
            {
                authStatusText.text = "Fetching profile...";
            }

            string meUrl = NetworkConfig.GetEndpointUrl("/auth/me");
            Debug.Log($"[Auth] Calling {meUrl}");

            using (UnityWebRequest request = UnityWebRequest.Get(meUrl))
            {
                request.SetRequestHeader("Authorization", $"Bearer {sessionToken}");

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    string responseText = request.downloadHandler.text;
                    Debug.Log($"[Auth] Me response: {responseText}");

                    PlayerProfile profile = JsonUtility.FromJson<PlayerProfile>(responseText);

                    if (authStatusText != null)
                    {
                        authStatusText.text = $"{profile.display_name}\nCash: {profile.cash} | Kills: {profile.kills} | Planets: {profile.planets_owned}";
                    }

                    Debug.Log($"[Auth] Profile loaded: {profile.display_name}");
                }
                else
                {
                    Debug.LogError($"[Auth] Who am I failed: {request.error}");

                    if (authStatusText != null)
                    {
                        authStatusText.text = $"Profile fetch failed: {request.error}";
                    }
                }
            }
        }

        [System.Serializable]
        private class SessionTokenResponse
        {
            public string session_token;
            public string player_id;
            public int expires_in;
        }

        [System.Serializable]
        private class PlayerProfile
        {
            public string player_id;
            public string display_name;
            public int cash;
            public int kills;
            public int planets_owned;
        }
    }
}
