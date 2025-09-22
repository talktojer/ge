import { configureStore } from '@reduxjs/toolkit';
import authSlice from './slices/authSlice';
import gameSlice from './slices/gameSlice';
import uiSlice from './slices/uiSlice';
import shipsSlice from './slices/shipsSlice';
import planetsSlice from './slices/planetsSlice';
import communicationSlice from './slices/communicationSlice';
import notificationSlice from './slices/notificationSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    game: gameSlice,
    ui: uiSlice,
    ships: shipsSlice,
    planets: planetsSlice,
    communication: communicationSlice,
    notifications: notificationSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
