import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  ApiResponse, 
  LoginForm, 
  RegisterForm, 
  User, 
  Ship, 
  Planet, 
  PaginatedResponse,
  ShipCommand 
} from '../types';

// Create axios instance with base configuration
const api: AxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: (credentials: LoginForm): Promise<AxiosResponse<{ access_token: string; refresh_token: string; session_token: string; token_type: string; user: User }>> =>
    api.post('/api/users/login', credentials),
  
  register: (userData: RegisterForm): Promise<AxiosResponse<{ user: User; message: string }>> =>
    api.post('/api/users/register', userData),
  
  getCurrentUser: (): Promise<AxiosResponse<{ user: User }>> =>
    api.get('/api/users/profile'),
};

// Game API
export const gameApi = {
  getGameState: (): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.get('/game/state'),
  
  getShip: (shipId: number): Promise<AxiosResponse<ApiResponse<Ship>>> =>
    api.get(`/ships/${shipId}`),
  
  getPlanet: (planetId: number): Promise<AxiosResponse<ApiResponse<Planet>>> =>
    api.get(`/planets/${planetId}`),
};

// Ships API
export const shipsApi = {
  getShips: (params?: { page?: number; per_page?: number }): Promise<AxiosResponse<PaginatedResponse<Ship>>> =>
    api.get('/ships', { params }),
  
  getShip: (shipId: number): Promise<AxiosResponse<ApiResponse<Ship>>> =>
    api.get(`/ships/${shipId}`),
  
  createShip: (shipData: Partial<Ship>): Promise<AxiosResponse<ApiResponse<Ship>>> =>
    api.post('/ships', shipData),
  
  updateShip: (shipId: number, shipData: Partial<Ship>): Promise<AxiosResponse<ApiResponse<Ship>>> =>
    api.put(`/ships/${shipId}`, shipData),
  
  deleteShip: (shipId: number): Promise<AxiosResponse<ApiResponse<void>>> =>
    api.delete(`/ships/${shipId}`),
  
  executeCommand: (command: ShipCommand): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post('/ships/command', command),
  
  moveShip: (shipId: number, x: number, y: number, z: number): Promise<AxiosResponse<ApiResponse<Ship>>> =>
    api.post(`/ships/${shipId}/move`, { x, y, z }),
  
  attackTarget: (shipId: number, targetId: number, targetType: string): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post(`/ships/${shipId}/attack`, { target_id: targetId, target_type: targetType }),
};

// Planets API
export const planetsApi = {
  getPlanets: (params?: { page?: number; per_page?: number }): Promise<AxiosResponse<PaginatedResponse<Planet>>> =>
    api.get('/planets', { params }),
  
  getPlanet: (planetId: number): Promise<AxiosResponse<ApiResponse<Planet>>> =>
    api.get(`/planets/${planetId}`),
  
  colonizePlanet: (planetId: number): Promise<AxiosResponse<ApiResponse<Planet>>> =>
    api.post(`/planets/${planetId}/colonize`),
  
  updatePlanet: (planetId: number, planetData: Partial<Planet>): Promise<AxiosResponse<ApiResponse<Planet>>> =>
    api.put(`/planets/${planetId}`, planetData),
  
  scanPlanet: (planetId: number): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post(`/planets/${planetId}/scan`),
};

// Teams API
export const teamsApi = {
  getTeams: (): Promise<AxiosResponse<ApiResponse<any[]>>> =>
    api.get('/teams'),
  
  getTeam: (teamId: number): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.get(`/teams/${teamId}`),
  
  createTeam: (teamData: any): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post('/teams', teamData),
  
  joinTeam: (teamId: number): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post(`/teams/${teamId}/join`),
  
  leaveTeam: (): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post('/teams/leave'),
};

// Communication API
export const communicationApi = {
  getMessages: (channel: string): Promise<AxiosResponse<ApiResponse<any[]>>> =>
    api.get(`/communication/${channel}`),
  
  sendMessage: (messageData: any): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post('/communication/send', messageData),
  
  markAsRead: (messageId: number): Promise<AxiosResponse<ApiResponse<void>>> =>
    api.put(`/communication/${messageId}/read`),
};

// Battle API
export const battleApi = {
  getBattles: (): Promise<AxiosResponse<ApiResponse<any[]>>> =>
    api.get('/battles'),
  
  getBattle: (battleId: number): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.get(`/battles/${battleId}`),
  
  engageTarget: (shipId: number, targetId: number): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post('/battles/engage', { ship_id: shipId, target_id: targetId }),
};

// Wormholes API
export const wormholesApi = {
  getWormholes: (): Promise<AxiosResponse<ApiResponse<any[]>>> =>
    api.get('/wormholes'),
  
  useWormhole: (wormholeId: number, shipId: number): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post(`/wormholes/${wormholeId}/use`, { ship_id: shipId }),
};

// Beacons API
export const beaconsApi = {
  getBeacons: (): Promise<AxiosResponse<ApiResponse<any[]>>> =>
    api.get('/beacons'),
  
  createBeacon: (beaconData: any): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post('/beacons', beaconData),
  
  activateBeacon: (beaconId: number): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post(`/beacons/${beaconId}/activate`),
};

// Mines API
export const minesApi = {
  getMines: (): Promise<AxiosResponse<ApiResponse<any[]>>> =>
    api.get('/mines'),
  
  layMine: (mineData: any): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post('/mines', mineData),
  
  disarmMine: (mineId: number): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post(`/mines/${mineId}/disarm`),
};

// Spies API
export const spiesApi = {
  getSpies: (): Promise<AxiosResponse<ApiResponse<any[]>>> =>
    api.get('/spies'),
  
  deploySpy: (spyData: any): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post('/spies', spyData),
  
  recallSpy: (spyId: number): Promise<AxiosResponse<ApiResponse<any>>> =>
    api.post(`/spies/${spyId}/recall`),
};

export default api;
