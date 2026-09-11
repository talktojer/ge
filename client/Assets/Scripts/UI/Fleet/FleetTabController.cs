using UnityEngine;
using UnityEngine.UI;

namespace GalacticEmpire.UI.Fleet
{
    /// <summary>
    /// Fleet tab controller - Ship roster, loadout, travel orders
    /// Per PHASE1B_CLIENT_UX_VISION.md §1.1
    /// </summary>
    public class FleetTabController : MonoBehaviour
    {
        // TODO: Implement ship roster view
        // TODO: Implement active ship card
        // TODO: Implement ship detail view
        // TODO: Implement loadout editor
        // TODO: Implement travel orders
        // TODO: Implement hangar (dock/repair, purchase ships)

        private int activeShipId = 0;

        void Start()
        {
            // TODO: Load player ships from API
            // TODO: Subscribe to ship status updates
        }

        void OnEnable()
        {
            // TODO: Refresh active ship data
        }

        public void SelectShip(int shipId)
        {
            activeShipId = shipId;
            // TODO: Load ship details
            // TODO: Update UI
        }

        public void ShowLoadoutEditor()
        {
            // TODO: Open loadout modal
            // TODO: Show equipment slots (phasors, shields, cargo)
        }

        public void SetTravelOrder(int targetX, int targetY)
        {
            // TODO: Send travel command to API
            // TODO: Update UI with ETA
        }
    }
}
