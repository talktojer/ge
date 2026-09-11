using UnityEngine;
using UnityEngine.UI;

namespace GalacticEmpire.UI.Map
{
    /// <summary>
    /// Map tab controller - 3 zoom levels: Galaxy, Sector, Local
    /// Per PHASE1B_CLIENT_UX_VISION.md §2.1
    /// </summary>
    public class MapTabController : MonoBehaviour
    {
        // TODO: Implement three zoom levels:
        // Level 1: Galaxy Overview (30x15 sector grid)
        // Level 2: Sector Grid View (sector contents, planets, contacts)
        // Level 3: Local Space HUD (tactical view, ship + nearby contacts)

        private enum ZoomLevel
        {
            Galaxy,
            Sector,
            Local
        }

        private ZoomLevel currentZoom = ZoomLevel.Local;
        private Vector2Int currentSector = new Vector2Int(0, 0);

        void Start()
        {
            // TODO: Subscribe to sector updates via WebSocket
            // TODO: Load galaxy map data
            // TODO: Initialize minimap
        }

        void OnEnable()
        {
            // TODO: Refresh visible sector data
        }

        void OnDisable()
        {
            // TODO: Unsubscribe from sector updates
        }

        public void ZoomIn()
        {
            // Galaxy -> Sector -> Local
            // TODO: Implement zoom transition
        }

        public void ZoomOut()
        {
            // Local -> Sector -> Galaxy
            // TODO: Implement zoom transition
        }

        public void NavigateToSector(int x, int y)
        {
            currentSector = new Vector2Int(x, y);
            // TODO: Update WebSocket subscription
            // TODO: Load sector data
            // TODO: Update UI
        }
    }
}
