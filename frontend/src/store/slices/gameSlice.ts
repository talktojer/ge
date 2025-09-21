import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { GameState, Ship, Planet, GameUpdate } from '../../types';
import { gameApi } from '../../services/api';

interface GameSliceState {
  current_user: GameState['current_user'];
  selected_ship: Ship | null;
  selected_planet: Planet | null;
  game_time: string;
  tick_number: number;
  is_connected: boolean;
  isLoading: boolean;
  error: string | null;
  real_time_updates: GameUpdate[];
}

const initialState: GameSliceState = {
  current_user: null,
  selected_ship: null,
  selected_planet: null,
  game_time: '',
  tick_number: 0,
  is_connected: false,
  isLoading: false,
  error: null,
  real_time_updates: [],
};

// Async thunks
export const getGameState = createAsyncThunk(
  'game/getGameState',
  async (_, { rejectWithValue }) => {
    try {
      const response = await gameApi.getGameState();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to get game state');
    }
  }
);

export const selectShip = createAsyncThunk(
  'game/selectShip',
  async (shipId: number, { rejectWithValue }) => {
    try {
      const response = await gameApi.getShip(shipId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to select ship');
    }
  }
);

export const selectPlanet = createAsyncThunk(
  'game/selectPlanet',
  async (planetId: number, { rejectWithValue }) => {
    try {
      const response = await gameApi.getPlanet(planetId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to select planet');
    }
  }
);

const gameSlice = createSlice({
  name: 'game',
  initialState,
  reducers: {
    resetGameState: (state) => {
      return initialState;
    },
    setConnectionStatus: (state, action: PayloadAction<boolean>) => {
      state.is_connected = action.payload;
    },
    addGameUpdate: (state, action: PayloadAction<GameUpdate>) => {
      state.real_time_updates.unshift(action.payload);
      // Keep only the last 100 updates
      if (state.real_time_updates.length > 100) {
        state.real_time_updates = state.real_time_updates.slice(0, 100);
      }
    },
    clearGameUpdates: (state) => {
      state.real_time_updates = [];
    },
    updateGameTime: (state, action: PayloadAction<{ game_time: string; tick_number: number }>) => {
      state.game_time = action.payload.game_time;
      state.tick_number = action.payload.tick_number;
    },
    updateSelectedShip: (state, action: PayloadAction<Ship>) => {
      if (state.selected_ship?.id === action.payload.id) {
        state.selected_ship = action.payload;
      }
    },
    updateSelectedPlanet: (state, action: PayloadAction<Planet>) => {
      if (state.selected_planet?.id === action.payload.id) {
        state.selected_planet = action.payload;
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Get game state
      .addCase(getGameState.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(getGameState.fulfilled, (state, action) => {
        state.isLoading = false;
        state.game_time = action.payload.game_time;
        state.tick_number = action.payload.tick_number;
      })
      .addCase(getGameState.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Select ship
      .addCase(selectShip.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(selectShip.fulfilled, (state, action) => {
        state.isLoading = false;
        state.selected_ship = action.payload;
      })
      .addCase(selectShip.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Select planet
      .addCase(selectPlanet.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(selectPlanet.fulfilled, (state, action) => {
        state.isLoading = false;
        state.selected_planet = action.payload;
      })
      .addCase(selectPlanet.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const {
  resetGameState,
  setConnectionStatus,
  addGameUpdate,
  clearGameUpdates,
  updateGameTime,
  updateSelectedShip,
  updateSelectedPlanet,
  clearError,
} = gameSlice.actions;

export default gameSlice.reducer;
