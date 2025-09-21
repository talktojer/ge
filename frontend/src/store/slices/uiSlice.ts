import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { UIState, Notification } from '../../types';

const initialState: UIState = {
  sidebar_collapsed: false,
  active_panel: 'dashboard',
  notifications: [],
  theme: 'dark',
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebar_collapsed = !state.sidebar_collapsed;
    },
    setActivePanel: (state, action: PayloadAction<string>) => {
      state.active_panel = action.payload;
    },
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id' | 'timestamp' | 'read'>>) => {
      const notification: Notification = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        read: false,
      };
      state.notifications.unshift(notification);
      // Keep only the last 50 notifications
      if (state.notifications.length > 50) {
        state.notifications = state.notifications.slice(0, 50);
      }
    },
    markNotificationAsRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload);
      if (notification) {
        notification.read = true;
      }
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    setTheme: (state, action: PayloadAction<'dark' | 'light'>) => {
      state.theme = action.payload;
      localStorage.setItem('theme', action.payload);
    },
  },
});

export const {
  toggleSidebar,
  setActivePanel,
  addNotification,
  markNotificationAsRead,
  clearNotifications,
  setTheme,
} = uiSlice.actions;

export default uiSlice.reducer;
