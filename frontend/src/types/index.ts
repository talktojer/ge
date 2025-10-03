// Core game types
export interface User {
  id: number;
  userid: string;
  email: string;
  team_id?: number;
  created_at: string;
  last_login?: string;
  is_active: boolean;
  is_admin: boolean;
}

export interface Team {
  id: number;
  name: string;
  description?: string;
  leader_id: number;
  member_count: number;
  total_score: number;
  created_at: string;
}

export interface Ship {
  id: number;
  name: string;
  owner_id: number;
  ship_type: string;
  ship_class: number;
  x: number;
  y: number;
  z: number;
  sector: number;
  hull_points: number;
  max_hull_points: number;
  shields: number;
  max_shields: number;
  fuel: number;
  max_fuel: number;
  cargo_capacity: number;
  cargo_used: number;
  weapons: string[];
  is_active: boolean;
  created_at: string;
  last_updated: string;
}

export interface ShipCreateRequest {
  ship_name: string;
  ship_class: number;
}

export interface Planet {
  id: number;
  name: string;
  owner_id?: number;
  x: number;
  y: number;
  z: number;
  sector: number;
  planet_type: string;
  population?: number;
  max_population?: number;
  resources: Record<string, number>;
  is_colonized: boolean;
  created_at: string;
}

export interface GameState {
  current_user: User | null;
  selected_ship: Ship | null;
  selected_planet: Planet | null;
  game_time: string;
  tick_number: number;
  is_connected: boolean;
}

// API Response types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

// Admin Configuration Types
export interface ConfigParameter {
  value: any;
  type: string;
  config_type: string;
  category: string;
  description: string;
  min_value?: number;
  max_value?: number;
  default_value: any;
  requires_restart: boolean;
}

export interface BalanceMetrics {
  factor: string;
  current_value: number;
  target_value: number;
  deviation_percent: number;
  recommendation: string;
  impact_level: string;
}

export interface ScoreBreakdown {
  kill_score: number;
  planet_score: number;
  team_score: number;
  net_worth: number;
  combat_rating: number;
  economic_rating: number;
  strategic_rating: number;
  overall_rating: number;
}

export interface PlayerRanking {
  user_id: number;
  username: string;
  rank: number;
  score: number;
  score_breakdown: ScoreBreakdown;
  team_name?: string;
  last_active?: string;
  achievements: string[];
}

export interface TeamRanking {
  team_id: number;
  team_name: string;
  rank: number;
  total_score: number;
  member_count: number;
  average_score: number;
  coordination_bonus: number;
  last_active?: string;
}

export interface AdminStatsResponse {
  total_players: number;
  active_players: number;
  total_teams: number;
  game_uptime: string;
  configuration_count: number;
  pending_balance_adjustments: number;
  system_health: string;
}

export interface GameUpdate {
  type: 'ship_update' | 'planet_update' | 'combat_update' | 'message' | 'tick' | 'wormhole_discovered' | 'spy_captured' | 'team_battle' | 'alliance_formed' | 'diplomatic_message' | 'trade_proposal' | 'battle_visualization' | 'sector_activity';
  data: any;
  timestamp: string;
}

// Form types
export interface LoginForm {
  username: string; // This maps to userid in the backend
  password: string;
}

export interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface ShipCommand {
  ship_id: number;
  command: string;
  parameters: Record<string, any>;
}

// UI State types
export interface UIState {
  sidebar_collapsed: boolean;
  active_panel: string;
  notifications: Notification[];
  theme: 'dark' | 'light';
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}
