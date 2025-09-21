import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Ship, PaginatedResponse, ShipCommand } from '../../types';
import { shipsApi } from '../../services/api';

interface ShipsState {
  ships: Ship[];
  selectedShip: Ship | null;
  isLoading: boolean;
  error: string | null;
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

const initialState: ShipsState = {
  ships: [],
  selectedShip: null,
  isLoading: false,
  error: null,
  pagination: {
    page: 1,
    per_page: 20,
    total: 0,
    pages: 0,
  },
};

// Async thunks
export const fetchShips = createAsyncThunk(
  'ships/fetchShips',
  async (params: { page?: number; per_page?: number } = {}, { rejectWithValue }) => {
    try {
      const response = await shipsApi.getShips(params);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch ships');
    }
  }
);

export const getShip = createAsyncThunk(
  'ships/getShip',
  async (shipId: number, { rejectWithValue }) => {
    try {
      const response = await shipsApi.getShip(shipId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to get ship');
    }
  }
);

export const createShip = createAsyncThunk(
  'ships/createShip',
  async (shipData: Partial<Ship>, { rejectWithValue }) => {
    try {
      const response = await shipsApi.createShip(shipData);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to create ship');
    }
  }
);

export const updateShip = createAsyncThunk(
  'ships/updateShip',
  async ({ shipId, shipData }: { shipId: number; shipData: Partial<Ship> }, { rejectWithValue }) => {
    try {
      const response = await shipsApi.updateShip(shipId, shipData);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to update ship');
    }
  }
);

export const executeShipCommand = createAsyncThunk(
  'ships/executeCommand',
  async (command: ShipCommand, { rejectWithValue }) => {
    try {
      const response = await shipsApi.executeCommand(command);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to execute command');
    }
  }
);

const shipsSlice = createSlice({
  name: 'ships',
  initialState,
  reducers: {
    resetShipsState: (state) => {
      return initialState;
    },
    updateShipInList: (state, action: PayloadAction<Ship>) => {
      const index = state.ships.findIndex(ship => ship.id === action.payload.id);
      if (index !== -1) {
        state.ships[index] = action.payload;
      }
      if (state.selectedShip?.id === action.payload.id) {
        state.selectedShip = action.payload;
      }
    },
    removeShipFromList: (state, action: PayloadAction<number>) => {
      state.ships = state.ships.filter(ship => ship.id !== action.payload);
      if (state.selectedShip?.id === action.payload) {
        state.selectedShip = null;
      }
    },
    setSelectedShip: (state, action: PayloadAction<Ship | null>) => {
      state.selectedShip = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch ships
      .addCase(fetchShips.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchShips.fulfilled, (state, action) => {
        state.isLoading = false;
        state.ships = action.payload.items;
        state.pagination = {
          page: action.payload.page,
          per_page: action.payload.per_page,
          total: action.payload.total,
          pages: action.payload.pages,
        };
      })
      .addCase(fetchShips.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Get ship
      .addCase(getShip.fulfilled, (state, action) => {
        state.selectedShip = action.payload;
      })
      // Create ship
      .addCase(createShip.fulfilled, (state, action) => {
        state.ships.unshift(action.payload);
      })
      // Update ship
      .addCase(updateShip.fulfilled, (state, action) => {
        const index = state.ships.findIndex(ship => ship.id === action.payload.id);
        if (index !== -1) {
          state.ships[index] = action.payload;
        }
        if (state.selectedShip?.id === action.payload.id) {
          state.selectedShip = action.payload;
        }
      })
      // Execute command
      .addCase(executeShipCommand.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(executeShipCommand.fulfilled, (state) => {
        state.isLoading = false;
      })
      .addCase(executeShipCommand.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const {
  resetShipsState,
  updateShipInList,
  removeShipFromList,
  setSelectedShip,
  clearError,
} = shipsSlice.actions;

export default shipsSlice.reducer;
