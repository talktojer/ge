using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;
using System.Collections;
using GalacticEmpire.Networking;

namespace GalacticEmpire.UI.Boot
{
    /// <summary>
    /// Health check controller for Boot splash scene
    /// Calls GET /health and displays status on canvas
    /// </summary>
    public class HealthCheckController : MonoBehaviour
    {
        [Header("UI References")]
        [SerializeField] private Button checkHealthButton;
        [SerializeField] private Text statusText;

        private void Start()
        {
            if (checkHealthButton != null)
            {
                checkHealthButton.onClick.AddListener(OnCheckHealthClicked);
            }

            if (statusText != null)
            {
                statusText.text = "Ready to check health";
            }
        }

        private void OnCheckHealthClicked()
        {
            StartCoroutine(CheckHealthCoroutine());
        }

        private IEnumerator CheckHealthCoroutine()
        {
            if (statusText != null)
            {
                statusText.text = "Checking...";
            }

            string healthUrl = NetworkConfig.GetEndpointUrl("/health");
            Debug.Log($"[HealthCheck] Calling {healthUrl}");

            using (UnityWebRequest request = UnityWebRequest.Get(healthUrl))
            {
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    string responseText = request.downloadHandler.text;
                    Debug.Log($"[HealthCheck] Response: {responseText}");

                    HealthResponse response = JsonUtility.FromJson<HealthResponse>(responseText);
                    
                    if (statusText != null)
                    {
                        statusText.text = $"Pass: {response.api}";
                    }
                }
                else
                {
                    Debug.LogError($"[HealthCheck] Failed: {request.error}");
                    
                    if (statusText != null)
                    {
                        statusText.text = $"Fail: {request.error}";
                    }
                }
            }
        }

        [System.Serializable]
        private class HealthResponse
        {
            public string api;
        }
    }
}
