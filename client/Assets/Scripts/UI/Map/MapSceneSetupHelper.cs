using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;

namespace GalacticEmpire.UI.Map
{
    /// <summary>
    /// Helper to programmatically create Map UI elements if not assigned in Inspector
    /// This allows testing the Map functionality without manual Unity Editor setup
    /// </summary>
    [RequireComponent(typeof(MapTabController))]
    public class MapSceneSetupHelper : MonoBehaviour
    {
        private void Start()
        {
            EnsureEventSystem();
            SetupMapUIIfNeeded();
        }

        private void EnsureEventSystem()
        {
            if (FindObjectOfType<EventSystem>() == null)
            {
                var eventSystemObj = new GameObject("EventSystem");
                eventSystemObj.AddComponent<EventSystem>();
                var inputModule = eventSystemObj.AddComponent<StandaloneInputModule>();
                Debug.Log("[MapSceneSetup] Created EventSystem with StandaloneInputModule");
            }
        }

        private void SetupMapUIIfNeeded()
        {
            var mapController = GetComponent<MapTabController>();
            
            var statusTextField = mapController.GetType().GetField("statusText", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            var statusText = (Text)statusTextField?.GetValue(mapController);

            if (statusText == null)
            {
                Debug.Log("[MapSceneSetup] Creating Map UI programmatically...");
                CreateMapUI(mapController);
            }
            else
            {
                Debug.Log("[MapSceneSetup] Map UI already assigned in Inspector");
            }
        }

        private void CreateMapUI(MapTabController controller)
        {
            Canvas canvas = FindObjectOfType<Canvas>();
            
            if (canvas == null)
            {
                var canvasObj = new GameObject("Canvas");
                canvas = canvasObj.AddComponent<Canvas>();
                canvas.renderMode = RenderMode.ScreenSpaceOverlay;
                canvasObj.AddComponent<CanvasScaler>();
                canvasObj.AddComponent<GraphicRaycaster>();
                Debug.Log("[MapSceneSetup] Created Canvas");
            }

            var uiRoot = new GameObject("MapUI");
            uiRoot.transform.SetParent(canvas.transform, false);
            
            var rectTransform = uiRoot.AddComponent<RectTransform>();
            rectTransform.anchorMin = Vector2.zero;
            rectTransform.anchorMax = Vector2.one;
            rectTransform.sizeDelta = Vector2.zero;

            var statusText = CreateText(uiRoot.transform, "StatusText", new Vector2(0, 200), new Vector2(800, 50), "Ready");
            statusText.alignment = TextAnchor.MiddleCenter;
            statusText.fontSize = 16;

            var loadGalaxyButton = CreateButton(uiRoot.transform, "LoadGalaxyButton", new Vector2(0, 120), new Vector2(200, 60), "Load Galaxy");

            var scrollViewObj = CreateScrollView(uiRoot.transform, "SectorList", new Vector2(-200, -50), new Vector2(350, 400));
            var sectorListContainer = scrollViewObj.transform.Find("Viewport/Content");

            var sectorDetailObj = new GameObject("SectorDetail");
            sectorDetailObj.transform.SetParent(uiRoot.transform, false);
            var sectorDetailRect = sectorDetailObj.AddComponent<RectTransform>();
            sectorDetailRect.anchorMin = new Vector2(1, 0.5f);
            sectorDetailRect.anchorMax = new Vector2(1, 0.5f);
            sectorDetailRect.pivot = new Vector2(1, 0.5f);
            sectorDetailRect.anchoredPosition = new Vector2(-20, 50);
            sectorDetailRect.sizeDelta = new Vector2(350, 300);
            
            var sectorDetailBg = sectorDetailObj.AddComponent<Image>();
            sectorDetailBg.color = new Color(0.1f, 0.1f, 0.1f, 0.9f);
            
            var sectorDetailText = CreateText(sectorDetailObj.transform, "Text", Vector2.zero, new Vector2(-20, -20), "Select a sector to view details");
            sectorDetailText.alignment = TextAnchor.UpperLeft;
            sectorDetailText.fontSize = 12;
            var sectorDetailTextRect = sectorDetailText.GetComponent<RectTransform>();
            sectorDetailTextRect.anchorMin = Vector2.zero;
            sectorDetailTextRect.anchorMax = Vector2.one;

            var liveUpdatesObj = new GameObject("LiveUpdates");
            liveUpdatesObj.transform.SetParent(uiRoot.transform, false);
            var liveUpdatesRect = liveUpdatesObj.AddComponent<RectTransform>();
            liveUpdatesRect.anchorMin = new Vector2(1, 0);
            liveUpdatesRect.anchorMax = new Vector2(1, 0);
            liveUpdatesRect.pivot = new Vector2(1, 0);
            liveUpdatesRect.anchoredPosition = new Vector2(-20, 20);
            liveUpdatesRect.sizeDelta = new Vector2(350, 200);
            
            var liveUpdatesBg = liveUpdatesObj.AddComponent<Image>();
            liveUpdatesBg.color = new Color(0.1f, 0.1f, 0.15f, 0.9f);
            
            var liveUpdatesText = CreateText(liveUpdatesObj.transform, "Text", Vector2.zero, new Vector2(-20, -20), "Live updates will appear here...");
            liveUpdatesText.alignment = TextAnchor.UpperLeft;
            liveUpdatesText.fontSize = 10;
            var liveUpdatesTextRect = liveUpdatesText.GetComponent<RectTransform>();
            liveUpdatesTextRect.anchorMin = Vector2.zero;
            liveUpdatesTextRect.anchorMax = Vector2.one;

            var sectorButtonPrefab = CreateSectorButtonPrefab();

            AssignFieldsViaReflection(controller, statusText, loadGalaxyButton, sectorListContainer, sectorButtonPrefab, sectorDetailText, liveUpdatesText);

            Debug.Log("[MapSceneSetup] Map UI created successfully");
        }

        private Text CreateText(Transform parent, string name, Vector2 position, Vector2 size, string content)
        {
            var textObj = new GameObject(name);
            textObj.transform.SetParent(parent, false);
            
            var rectTransform = textObj.AddComponent<RectTransform>();
            rectTransform.anchoredPosition = position;
            rectTransform.sizeDelta = size;
            
            var text = textObj.AddComponent<Text>();
            text.text = content;
            text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            text.color = Color.white;
            text.fontSize = 14;
            
            return text;
        }

        private Button CreateButton(Transform parent, string name, Vector2 position, Vector2 size, string label)
        {
            var buttonObj = new GameObject(name);
            buttonObj.transform.SetParent(parent, false);
            
            var rectTransform = buttonObj.AddComponent<RectTransform>();
            rectTransform.anchoredPosition = position;
            rectTransform.sizeDelta = size;
            
            var image = buttonObj.AddComponent<Image>();
            image.color = new Color(0.2f, 0.4f, 0.8f);
            
            var button = buttonObj.AddComponent<Button>();
            
            var textObj = new GameObject("Text");
            textObj.transform.SetParent(buttonObj.transform, false);
            var textRect = textObj.AddComponent<RectTransform>();
            textRect.anchorMin = Vector2.zero;
            textRect.anchorMax = Vector2.one;
            textRect.sizeDelta = Vector2.zero;
            
            var text = textObj.AddComponent<Text>();
            text.text = label;
            text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            text.color = Color.white;
            text.fontSize = 16;
            text.alignment = TextAnchor.MiddleCenter;
            
            return button;
        }

        private GameObject CreateScrollView(Transform parent, string name, Vector2 position, Vector2 size)
        {
            var scrollViewObj = new GameObject(name);
            scrollViewObj.transform.SetParent(parent, false);
            
            var rectTransform = scrollViewObj.AddComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(0, 0.5f);
            rectTransform.anchorMax = new Vector2(0, 0.5f);
            rectTransform.pivot = new Vector2(0, 0.5f);
            rectTransform.anchoredPosition = position;
            rectTransform.sizeDelta = size;
            
            var scrollRect = scrollViewObj.AddComponent<ScrollRect>();
            scrollRect.horizontal = false;
            scrollRect.vertical = true;
            
            var viewportObj = new GameObject("Viewport");
            viewportObj.transform.SetParent(scrollViewObj.transform, false);
            var viewportRect = viewportObj.AddComponent<RectTransform>();
            viewportRect.anchorMin = Vector2.zero;
            viewportRect.anchorMax = Vector2.one;
            viewportRect.sizeDelta = Vector2.zero;
            viewportObj.AddComponent<Image>().color = new Color(0.1f, 0.1f, 0.1f, 0.9f);
            viewportObj.AddComponent<Mask>().showMaskGraphic = true;
            
            var contentObj = new GameObject("Content");
            contentObj.transform.SetParent(viewportObj.transform, false);
            var contentRect = contentObj.AddComponent<RectTransform>();
            contentRect.anchorMin = new Vector2(0, 1);
            contentRect.anchorMax = new Vector2(1, 1);
            contentRect.pivot = new Vector2(0.5f, 1);
            contentRect.anchoredPosition = Vector2.zero;
            contentRect.sizeDelta = new Vector2(0, 500);
            
            var vlg = contentObj.AddComponent<VerticalLayoutGroup>();
            vlg.childAlignment = TextAnchor.UpperCenter;
            vlg.childControlHeight = false;
            vlg.childControlWidth = true;
            vlg.childForceExpandHeight = false;
            vlg.childForceExpandWidth = true;
            vlg.spacing = 5;
            
            var csf = contentObj.AddComponent<ContentSizeFitter>();
            csf.verticalFit = ContentSizeFitter.FitMode.PreferredSize;
            
            scrollRect.viewport = viewportRect;
            scrollRect.content = contentRect;
            
            return scrollViewObj;
        }

        private GameObject CreateSectorButtonPrefab()
        {
            var prefabObj = new GameObject("SectorButtonPrefab");
            DontDestroyOnLoad(prefabObj);
            prefabObj.SetActive(false);
            
            var rectTransform = prefabObj.AddComponent<RectTransform>();
            rectTransform.sizeDelta = new Vector2(320, 60);
            
            var image = prefabObj.AddComponent<Image>();
            image.color = new Color(0.15f, 0.15f, 0.2f);
            
            var button = prefabObj.AddComponent<Button>();
            
            var layoutElement = prefabObj.AddComponent<LayoutElement>();
            layoutElement.preferredHeight = 60;
            
            var textObj = new GameObject("Text");
            textObj.transform.SetParent(prefabObj.transform, false);
            var textRect = textObj.AddComponent<RectTransform>();
            textRect.anchorMin = Vector2.zero;
            textRect.anchorMax = Vector2.one;
            textRect.sizeDelta = new Vector2(-10, -10);
            
            var text = textObj.AddComponent<Text>();
            text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            text.color = Color.white;
            text.fontSize = 12;
            text.alignment = TextAnchor.MiddleLeft;
            
            return prefabObj;
        }

        private void AssignFieldsViaReflection(MapTabController controller, Text statusText, Button loadGalaxyButton, 
            Transform sectorListContainer, GameObject sectorButtonPrefab, Text sectorDetailText, Text liveUpdatesText)
        {
            var type = controller.GetType();
            var bindingFlags = System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance;
            
            type.GetField("statusText", bindingFlags)?.SetValue(controller, statusText);
            type.GetField("loadGalaxyButton", bindingFlags)?.SetValue(controller, loadGalaxyButton);
            type.GetField("sectorListContainer", bindingFlags)?.SetValue(controller, sectorListContainer);
            type.GetField("sectorButtonPrefab", bindingFlags)?.SetValue(controller, sectorButtonPrefab);
            type.GetField("sectorDetailText", bindingFlags)?.SetValue(controller, sectorDetailText);
            type.GetField("liveUpdatesText", bindingFlags)?.SetValue(controller, liveUpdatesText);
            
            Debug.Log("[MapSceneSetup] Fields assigned via reflection");
        }
    }
}
