import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Planet, PaginatedResponse } from '../../types';
import { planetsApi } from '../../services/api';

interface PlanetsState {
  planets: Planet[];
  selectedPlanet: Planet | null;
  isLoading: boolean;
  error: string | null;
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

const initialState: PlanetsState = {
  planets: [],
  selectedPlanet: null,
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
export const fetchPlanets = createAsyncThunk(
  'planets/fetchPlanets',
  async (params: { page?: number; per_page?: number } = {}, { rejectWithValue }) => {
    try {
      const response = await planetsApi.getPlanets(params);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch planets');
    }
  }
);

export const getPlanet = createAsyncThunk(
  'planets/getPlanet',
  async (planetId: number, { rejectWithValue }) => {
    try {
      const response = await planetsApi.getPlanet(planetId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to get planet');
    }
  }
);

export const colonizePlanet = createAsyncThunk(
  'planets/colonizePlanet',
  async (planetId: number, { rejectWithValue }) => {
    try {
      const response = await planetsApi.colonizePlanet(planetId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to colonize planet');
    }
  }
);

export const updatePlanet = createAsyncThunk(
  'planets/updatePlanet',
  async ({ planetId, planetData }: { planetId: number; planetData: Partial<Planet> }, { rejectWithValue }) => {
    try {
      const response = await planetsApi.updatePlanet(planetId, planetData);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to update planet');
    }
  }
);

const planetsSlice = createSlice({
  name: 'planets',
  initialState,
  reducers: {
    resetPlanetsState: (state) => {
      return initialState;
    },
    updatePlanetInList: (state, action: PayloadAction<Planet>) => {
      const index = state.planets.findIndex(planet => planet.id === action.payload.id);
      if (index !== -1) {
        state.planets[index] = action.payload;
      }
      if (state.selectedPlanet?.id === action.payload.id) {
        state.selectedPlanet = action.payload;
      }
    },
    setSelectedPlanet: (state, action: PayloadAction<Planet | null>) => {
      state.selectedPlanet = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch planets
      .addCase(fetchPlanets.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchPlanets.fulfilled, (state, action) => {
        state.isLoading = false;
        state.planets = action.payload.items;
        state.pagination = {
          page: action.payload.page,
          per_page: action.payload.per_page,
          total: action.payload.total,
          pages: action.payload.pages,
        };
      })
      .addCase(fetchPlanets.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Get planet
      .addCase(getPlanet.fulfilled, (state, action) => {
        state.selectedPlanet = action.payload;
      })
      // Colonize planet
      .addCase(colonizePlanet.fulfilled, (state, action) => {
        const index = state.planets.findIndex(planet => planet.id === action.payload.id);
        if (index !== -1) {
          state.planets[index] = action.payload;
        }
        if (state.selectedPlanet?.id === action.payload.id) {
          state.selectedPlanet = action.payload;
        }
      })
      // Update planet
      .addCase(updatePlanet.fulfilled, (state, action) => {
        const index = state.planets.findIndex(planet => planet.id === action.payload.id);
        if (index !== -1) {
          state.planets[index] = action.payload;
        }
        if (state.selectedPlanet?.id === action.payload.id) {
          state.selectedPlanet = action.payload;
        }
      });
  },
});

export const {
  resetPlanetsState,
  updatePlanetInList,
  setSelectedPlanet,
  clearError,
} = planetsSlice.actions;

export default planetsSlice.reducer;
