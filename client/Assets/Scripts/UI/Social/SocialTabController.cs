using UnityEngine;
using UnityEngine.UI;

namespace GalacticEmpire.UI.Social
{
    /// <summary>
    /// Social tab controller - Alliance, leaderboard, inbox, settings
    /// Per PHASE1B_CLIENT_UX_VISION.md §1.1
    /// </summary>
    public class SocialTabController : MonoBehaviour
    {
        // TODO: Implement Team/Alliance hub
        // TODO: Implement Alliance Chat
        // TODO: Implement Sector Chat (proximity-based)
        // TODO: Implement Leaderboard (weekly/monthly/all-time)
        // TODO: Implement Inbox (notifications: threats, reports, killmails)
        // TODO: Implement Settings (nested: account, notifications, audio, accessibility)

        private enum SocialView
        {
            Alliance,
            Leaderboard,
            Inbox,
            Settings
        }

        private SocialView currentView = SocialView.Alliance;

        void Start()
        {
            // TODO: Load alliance data (if player in alliance)
            // TODO: Load inbox messages
            // TODO: Subscribe to chat updates
        }

        void OnEnable()
        {
            // TODO: Refresh current view
            // TODO: Mark messages as read
        }

        public void ShowAllianceView()
        {
            currentView = SocialView.Alliance;
            // TODO: Load alliance members, chat, team score
        }

        public void ShowLeaderboard()
        {
            currentView = SocialView.Leaderboard;
            // TODO: Load top players/alliances
        }

        public void ShowInbox()
        {
            currentView = SocialView.Inbox;
            // TODO: Load messages (attack alerts, production reports, killmails)
        }

        public void ShowSettings()
        {
            currentView = SocialView.Settings;
            // TODO: Load settings UI
            // TODO: Show logout button
        }

        public void SendChatMessage(string message)
        {
            // TODO: Send chat via WebSocket
            // TODO: Update chat UI
        }
    }
}
