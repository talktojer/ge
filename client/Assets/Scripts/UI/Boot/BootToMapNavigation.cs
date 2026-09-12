using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using GalacticEmpire.Core;

namespace GalacticEmpire.UI.Boot
{
    /// <summary>
    /// Adds Map navigation button to Boot scene after Sign in
    /// Attach this to the Boot scene root or any active GameObject
    /// </summary>
    public class BootToMapNavigation : MonoBehaviour
    {
        [Header("Map Scene Configuration")]
        [SerializeField] private string mapSceneName = "MAP_001_GalaxyOverview";
        
        [Header("UI References (Optional - will auto-create if not assigned)")]
        [SerializeField] private Button mapButton;
        [SerializeField] private Transform buttonContainer;
        
        [Header("Button Position")]
        [SerializeField] private Vector2 buttonPosition = new Vector2(0, -50);
        [SerializeField] private Vector2 buttonSize = new Vector2(200, 60);

        private void Start()
        {
            if (mapButton == null)
            {
                CreateMapButton();
            }
            else
            {
                mapButton.onClick.AddListener(OnMapButtonClicked);
            }

            // Initially disable until authenticated
            if (mapButton != null)
            {
                mapButton.interactable = false;
            }

            // Check auth state periodically
            InvokeRepeating(nameof(CheckAuthState), 0.5f, 0.5f);
        }

        private void CreateMapButton()
        {
            Canvas canvas = FindObjectOfType<Canvas>();
            
            if (canvas == null)
            {
                Debug.LogWarning("[BootToMapNav] No Canvas found, cannot create Map button");
                return;
            }

            Transform parent = buttonContainer != null ? buttonContainer : canvas.transform;

            var buttonObj = new GameObject("MapButton");
            buttonObj.transform.SetParent(parent, false);
            
            var rectTransform = buttonObj.AddComponent<RectTransform>();
            rectTransform.anchoredPosition = buttonPosition;
            rectTransform.sizeDelta = buttonSize;
            
            var image = buttonObj.AddComponent<Image>();
            image.color = new Color(0.2f, 0.6f, 0.4f);
            
            mapButton = buttonObj.AddComponent<Button>();
            mapButton.onClick.AddListener(OnMapButtonClicked);
            
            var textObj = new GameObject("Text");
            textObj.transform.SetParent(buttonObj.transform, false);
            var textRect = textObj.AddComponent<RectTransform>();
            textRect.anchorMin = Vector2.zero;
            textRect.anchorMax = Vector2.one;
            textRect.sizeDelta = Vector2.zero;
            
            var text = textObj.AddComponent<Text>();
            text.text = "Map";
            text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            text.color = Color.white;
            text.fontSize = 18;
            text.alignment = TextAnchor.MiddleCenter;
            text.fontStyle = FontStyle.Bold;
            
            Debug.Log("[BootToMapNav] Created Map button");
        }

        private void CheckAuthState()
        {
            if (mapButton == null) return;

            bool isAuthenticated = GameStateManager.Instance != null && 
                                   GameStateManager.Instance.IsAuthenticated;
            
            mapButton.interactable = isAuthenticated;
        }

        private void OnMapButtonClicked()
        {
            if (GameStateManager.Instance == null || !GameStateManager.Instance.IsAuthenticated)
            {
                Debug.LogWarning("[BootToMapNav] Cannot open Map - not authenticated");
                return;
            }

            Debug.Log($"[BootToMapNav] Loading Map scene: {mapSceneName}");
            
            // Load Map scene
            try
            {
                SceneManager.LoadScene(mapSceneName);
            }
            catch (System.Exception ex)
            {
                Debug.LogError($"[BootToMapNav] Failed to load Map scene '{mapSceneName}': {ex.Message}");
                Debug.LogError("[BootToMapNav] Make sure the Map scene is added to Build Settings");
            }
        }

        private void OnDestroy()
        {
            CancelInvoke(nameof(CheckAuthState));
        }
    }
}
