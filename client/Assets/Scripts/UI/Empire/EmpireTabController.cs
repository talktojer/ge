using UnityEngine;
using UnityEngine.UI;

namespace GalacticEmpire.UI.Empire
{
    /// <summary>
    /// Empire tab controller - Planet management, production, treasury
    /// Per PHASE1B_CLIENT_UX_VISION.md §1.1
    /// </summary>
    public class EmpireTabController : MonoBehaviour
    {
        // TODO: Implement Empire Home (networth, planet count, threats, attention queue)
        // TODO: Implement Planet List (sortable by value/production/threats)
        // TODO: Implement Planet Detail view
        // TODO: Implement Production Editor (set rates, taxes, reserve/markup)
        // TODO: Implement Trade Dock Sheet (buy/sell when docked)
        // TODO: Implement Treasury Summary (cash flow, tax collection)

        void Start()
        {
            // TODO: Load player planets from API
            // TODO: Subscribe to production updates (55s tick)
        }

        void OnEnable()
        {
            // TODO: Refresh empire summary
            // TODO: Check attention queue (planets needing action)
        }

        public void ShowPlanetDetail(int planetId)
        {
            // TODO: Load planet data
            // TODO: Show planet modal
        }

        public void ShowProductionEditor(int planetId)
        {
            // TODO: Load current production settings
            // TODO: Show production sliders (Men, Fighters, Gold per PHASE1B_GAME_DESIGN.md)
            // TODO: Update production rates on confirm
        }

        public void HarvestPlanet(int planetId)
        {
            // TODO: Collect production (triggered by 55s tick notification)
            // TODO: Update treasury
            // TODO: Refresh UI
        }
    }
}
