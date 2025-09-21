import { io, Socket } from 'socket.io-client';
import { GameUpdate, WebSocketMessage } from '../types';
import { store } from '../store';
import { addGameUpdate, setConnectionStatus } from '../store/slices/gameSlice';
import { updateShipInList } from '../store/slices/shipsSlice';
import { updatePlanetInList } from '../store/slices/planetsSlice';
import { addMessage } from '../store/slices/communicationSlice';
import { addNotification } from '../store/slices/uiSlice';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(): void {
    const token = localStorage.getItem('token');
    if (!token) {
      console.warn('No auth token found, skipping WebSocket connection');
      return;
    }

    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    
    this.socket = io(wsUrl, {
      auth: {
        token: token,
      },
      transports: ['websocket'],
      upgrade: false,
    });

    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      store.dispatch(setConnectionStatus(true));
      store.dispatch(addNotification({
        type: 'success',
        title: 'Connected',
        message: 'Real-time updates enabled',
      }));
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      store.dispatch(setConnectionStatus(false));
      
      if (reason === 'io server disconnect') {
        // Server disconnected, try to reconnect
        this.handleReconnect();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      store.dispatch(setConnectionStatus(false));
      this.handleReconnect();
    });

    // Game state updates
    this.socket.on('game_update', (data: GameUpdate) => {
      store.dispatch(addGameUpdate(data));
      this.handleGameUpdate(data);
    });

    // Ship updates
    this.socket.on('ship_update', (shipData) => {
      store.dispatch(updateShipInList(shipData));
      
      // Check if this is the currently selected ship
      const currentShip = store.getState().game.selected_ship;
      if (currentShip?.id === shipData.id) {
        store.dispatch(updateShipInList(shipData));
      }
    });

    // Planet updates
    this.socket.on('planet_update', (planetData) => {
      store.dispatch(updatePlanetInList(planetData));
      
      // Check if this is the currently selected planet
      const currentPlanet = store.getState().game.selected_planet;
      if (currentPlanet?.id === planetData.id) {
        store.dispatch(updatePlanetInList(planetData));
      }
    });

    // Communication updates
    this.socket.on('message_received', (messageData) => {
      store.dispatch(addMessage(messageData));
      store.dispatch(addNotification({
        type: 'info',
        title: 'New Message',
        message: `From: ${messageData.sender_name}`,
      }));
    });

    // Combat updates
    this.socket.on('combat_update', (combatData) => {
      store.dispatch(addGameUpdate({
        type: 'combat_update',
        data: combatData,
        timestamp: new Date().toISOString(),
      }));
      
      store.dispatch(addNotification({
        type: 'warning',
        title: 'Combat Alert',
        message: combatData.message || 'Combat detected',
      }));
    });

    // System notifications
    this.socket.on('system_notification', (notification) => {
      store.dispatch(addNotification({
        type: notification.type || 'info',
        title: notification.title || 'System',
        message: notification.message,
      }));
    });

    // Tick updates
    this.socket.on('tick_update', (tickData) => {
      store.dispatch(addGameUpdate({
        type: 'tick',
        data: tickData,
        timestamp: new Date().toISOString(),
      }));
    });

    // Advanced tactical updates
    this.socket.on('tactical_scan_result', (scanData) => {
      store.dispatch(addGameUpdate({
        type: 'message',
        data: { message: 'Tactical scan completed', scanData },
        timestamp: new Date().toISOString(),
      }));
    });

    this.socket.on('combat_event', (combatEvent) => {
      store.dispatch(addGameUpdate({
        type: 'combat_update',
        data: combatEvent,
        timestamp: new Date().toISOString(),
      }));
      
      // Handle different combat event types
      if (combatEvent.type === 'weapon_fire') {
        store.dispatch(addNotification({
          type: 'warning',
          title: 'Weapon Fired',
          message: `${combatEvent.source} fired ${combatEvent.weapon} at ${combatEvent.target}`,
        }));
      } else if (combatEvent.type === 'ship_destroyed') {
        store.dispatch(addNotification({
          type: 'error',
          title: 'Ship Destroyed',
          message: `${combatEvent.ship_name} has been destroyed`,
        }));
      }
    });

    // Wormhole updates
    this.socket.on('wormhole_discovered', (wormholeData) => {
      store.dispatch(addGameUpdate({
        type: 'wormhole_discovered',
        data: wormholeData,
        timestamp: new Date().toISOString(),
      }));
      
      store.dispatch(addNotification({
        type: 'success',
        title: 'Wormhole Discovered',
        message: `New wormhole found: ${wormholeData.name}`,
      }));
    });

    this.socket.on('wormhole_travel_complete', (travelData) => {
      store.dispatch(addGameUpdate({
        type: 'message',
        data: { message: 'Wormhole travel completed', travelData },
        timestamp: new Date().toISOString(),
      }));
      
      store.dispatch(addNotification({
        type: 'success',
        title: 'Travel Complete',
        message: `Arrived at sector (${travelData.destination.x}, ${travelData.destination.y})`,
      }));
    });

    // Espionage updates
    this.socket.on('spy_report', (spyData) => {
      store.dispatch(addGameUpdate({
        type: 'message',
        data: { message: 'Spy report received', spyData },
        timestamp: new Date().toISOString(),
      }));
      
      store.dispatch(addNotification({
        type: 'info',
        title: 'Intelligence Report',
        message: `Agent ${spyData.spy_name} has new intelligence`,
      }));
    });

    this.socket.on('spy_captured', (captureData) => {
      store.dispatch(addGameUpdate({
        type: 'spy_captured',
        data: captureData,
        timestamp: new Date().toISOString(),
      }));
      
      store.dispatch(addNotification({
        type: 'error',
        title: 'Agent Captured',
        message: `Agent ${captureData.spy_name} has been captured`,
      }));
    });

    this.socket.on('mine_triggered', (mineData) => {
      store.dispatch(addGameUpdate({
        type: 'message',
        data: { message: 'Mine field triggered', mineData },
        timestamp: new Date().toISOString(),
      }));
      
      store.dispatch(addNotification({
        type: 'warning',
        title: 'Mine Field Triggered',
        message: `Mine field ${mineData.field_name} has been triggered`,
      }));
    });

    // Team warfare updates
    this.socket.on('team_battle_update', (battleData) => {
      store.dispatch(addGameUpdate({
        type: 'team_battle',
        data: battleData,
        timestamp: new Date().toISOString(),
      }));
      
      store.dispatch(addNotification({
        type: 'warning',
        title: 'Team Battle',
        message: battleData.message,
      }));
    });

    this.socket.on('alliance_formed', (allianceData) => {
      store.dispatch(addGameUpdate({
        type: 'alliance_formed',
        data: allianceData,
        timestamp: new Date().toISOString(),
      }));
      
      store.dispatch(addNotification({
        type: 'success',
        title: 'Alliance Formed',
        message: `${allianceData.team1} and ${allianceData.team2} have formed an alliance`,
      }));
    });

    // Diplomatic updates
    this.socket.on('diplomatic_message', (diplomaticData) => {
      store.dispatch(addGameUpdate({
        type: 'diplomatic_message',
        data: diplomaticData,
        timestamp: new Date().toISOString(),
      }));
      
      store.dispatch(addNotification({
        type: 'info',
        title: 'Diplomatic Message',
        message: `New diplomatic communication from ${diplomaticData.sender_team}`,
      }));
    });

    this.socket.on('trade_proposal', (tradeData) => {
      store.dispatch(addGameUpdate({
        type: 'trade_proposal',
        data: tradeData,
        timestamp: new Date().toISOString(),
      }));
      
      store.dispatch(addNotification({
        type: 'info',
        title: 'Trade Proposal',
        message: `${tradeData.sender} has proposed a trade`,
      }));
    });

    // Real-time battle visualization
    this.socket.on('battle_visualization_update', (visualData) => {
      store.dispatch(addGameUpdate({
        type: 'battle_visualization',
        data: visualData,
        timestamp: new Date().toISOString(),
      }));
    });

    // Sector activity updates
    this.socket.on('sector_activity', (activityData) => {
      store.dispatch(addGameUpdate({
        type: 'sector_activity',
        data: activityData,
        timestamp: new Date().toISOString(),
      }));
    });

    // Configuration Management Events
    this.socket.on('config_updated', (data: any) => {
      console.log('Configuration updated:', data);
      store.dispatch(addNotification({
        type: 'info',
        title: 'Configuration Updated',
        message: `Setting '${data.key}' changed to ${data.value}`,
      }));
      
      // Dispatch custom action for configuration updates
      store.dispatch({
        type: 'admin/configUpdated',
        payload: data
      });
    });

    this.socket.on('config_batch_updated', (data: any) => {
      console.log('Configuration batch update:', data);
      store.dispatch(addNotification({
        type: 'info',
        title: 'Configuration Updated',
        message: `${data.count} settings updated successfully`,
      }));
      
      // Dispatch custom action for batch configuration updates
      store.dispatch({
        type: 'admin/configBatchUpdated',
        payload: data
      });
    });

    this.socket.on('balance_adjustment', (data: any) => {
      console.log('Balance adjustment made:', data);
      store.dispatch(addNotification({
        type: 'warning',
        title: 'Balance Adjustment',
        message: data.message || 'Game balance has been adjusted',
      }));
      
      // Dispatch custom action for balance adjustments
      store.dispatch({
        type: 'admin/balanceAdjusted',
        payload: data
      });
    });

    this.socket.on('scoring_recalculated', (data: any) => {
      console.log('Scoring recalculated:', data);
      store.dispatch(addNotification({
        type: 'info',
        title: 'Scores Updated',
        message: 'Player and team scores have been recalculated',
      }));
      
      // Dispatch custom action for score recalculation
      store.dispatch({
        type: 'admin/scoresRecalculated',
        payload: data
      });
    });

    this.socket.on('admin_action', (data: any) => {
      console.log('Admin action performed:', data);
      store.dispatch(addNotification({
        type: 'info',
        title: 'Admin Action',
        message: data.message || 'An administrative action has been performed',
      }));
    });

    // Administrative Events
    this.socket.on('admin_broadcast', (data: any) => {
      console.log('Admin broadcast received:', data);
      store.dispatch(addNotification({
        type: 'info',
        title: 'Admin Announcement',
        message: data.message,
      }));
    });

    this.socket.on('system_maintenance', (data: any) => {
      console.log('System maintenance notification:', data);
      store.dispatch(addNotification({
        type: 'warning',
        title: 'System Maintenance',
        message: data.message,
      }));
    });

    this.socket.on('game_reset', (data: any) => {
      console.log('Game reset notification:', data);
      store.dispatch(addNotification({
        type: 'warning',
        title: 'Game Reset',
        message: data.message,
      }));
      // Optionally refresh the page or redirect
      setTimeout(() => {
        window.location.reload();
      }, 3000);
    });
  }

  private handleGameUpdate(update: GameUpdate): void {
    switch (update.type) {
      case 'ship_update':
        // Ship updates are handled by the ship_update event
        break;
      case 'planet_update':
        // Planet updates are handled by the planet_update event
        break;
      case 'combat_update':
        // Combat updates are handled by the combat_update event
        break;
      case 'message':
        // Messages are handled by the message_received event
        break;
      case 'tick':
        // Tick updates are handled by the tick_update event
        break;
      default:
        console.log('Unknown game update type:', update.type);
    }
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        if (this.socket) {
          this.socket.connect();
        }
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
      store.dispatch(addNotification({
        type: 'error',
        title: 'Connection Lost',
        message: 'Unable to reconnect to game server',
      }));
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      store.dispatch(setConnectionStatus(false));
    }
  }

  sendMessage(type: string, data: any): void {
    if (this.socket && this.socket.connected) {
      this.socket.emit(type, data);
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }

  isConnected(): boolean {
    return this.socket ? this.socket.connected : false;
  }

  // Specific game actions
  joinChannel(channel: string): void {
    this.sendMessage('join_channel', { channel });
  }

  leaveChannel(channel: string): void {
    this.sendMessage('leave_channel', { channel });
  }

  requestShipUpdate(shipId: number): void {
    this.sendMessage('request_ship_update', { ship_id: shipId });
  }

  requestPlanetUpdate(planetId: number): void {
    this.sendMessage('request_planet_update', { planet_id: planetId });
  }

  // Advanced tactical features
  requestTacticalScan(shipId: number, scanType: string, range: number): void {
    this.sendMessage('tactical_scan', { 
      ship_id: shipId, 
      scan_type: scanType, 
      range: range 
    });
  }

  requestCombatData(shipId: number): void {
    this.sendMessage('request_combat_data', { ship_id: shipId });
  }

  fireCombatWeapon(shipId: number, weaponId: string, targetId: string): void {
    this.sendMessage('combat_weapon_fire', { 
      ship_id: shipId, 
      weapon_id: weaponId, 
      target_id: targetId 
    });
  }

  lockTarget(shipId: number, targetId: string): void {
    this.sendMessage('combat_target_lock', { 
      ship_id: shipId, 
      target_id: targetId 
    });
  }

  // Wormhole operations
  requestWormholeData(shipId: number): void {
    this.sendMessage('request_wormhole_data', { ship_id: shipId });
  }

  initiateWormholeTravel(shipId: number, wormholeId: string): void {
    this.sendMessage('wormhole_travel', { 
      ship_id: shipId, 
      wormhole_id: wormholeId 
    });
  }

  scanForWormholes(shipId: number, sectorX: number, sectorY: number): void {
    this.sendMessage('wormhole_scan', { 
      ship_id: shipId, 
      sector_x: sectorX, 
      sector_y: sectorY 
    });
  }

  // Espionage operations
  deploySpy(shipId: number, spyData: any): void {
    this.sendMessage('deploy_spy', { 
      ship_id: shipId, 
      spy_data: spyData 
    });
  }

  recallSpy(shipId: number, spyId: string): void {
    this.sendMessage('recall_spy', { 
      ship_id: shipId, 
      spy_id: spyId 
    });
  }

  deployMineField(shipId: number, mineFieldData: any): void {
    this.sendMessage('deploy_mines', { 
      ship_id: shipId, 
      mine_field_data: mineFieldData 
    });
  }

  activateStealthSystem(shipId: number, systemId: string): void {
    this.sendMessage('activate_stealth', { 
      ship_id: shipId, 
      system_id: systemId 
    });
  }

  // Team warfare
  requestTeamData(teamId: number): void {
    this.sendMessage('request_team_data', { team_id: teamId });
  }

  coordinateAttack(teamId: number, attackData: any): void {
    this.sendMessage('coordinate_attack', { 
      team_id: teamId, 
      attack_data: attackData 
    });
  }

  shareResources(teamId: number, resourceData: any): void {
    this.sendMessage('share_resources', { 
      team_id: teamId, 
      resource_data: resourceData 
    });
  }

  // Diplomatic operations
  sendDiplomaticMessage(targetTeam: number, messageType: string, data: any): void {
    this.sendMessage('diplomatic_message', { 
      target_team: targetTeam, 
      message_type: messageType, 
      data: data 
    });
  }

  proposeTrade(targetPlayer: number, tradeOffer: any): void {
    this.sendMessage('trade_proposal', { 
      target_player: targetPlayer, 
      trade_offer: tradeOffer 
    });
  }

  // Real-time subscriptions
  subscribeToBattleUpdates(battleId: string): void {
    this.sendMessage('subscribe_battle', { battle_id: battleId });
  }

  subscribeToSectorUpdates(sectorX: number, sectorY: number): void {
    this.sendMessage('subscribe_sector', { 
      sector_x: sectorX, 
      sector_y: sectorY 
    });
  }

  subscribeToTeamUpdates(teamId: number): void {
    this.sendMessage('subscribe_team', { team_id: teamId });
  }

  unsubscribeFromBattleUpdates(battleId: string): void {
    this.sendMessage('unsubscribe_battle', { battle_id: battleId });
  }

  unsubscribeFromSectorUpdates(sectorX: number, sectorY: number): void {
    this.sendMessage('unsubscribe_sector', { 
      sector_x: sectorX, 
      sector_y: sectorY 
    });
  }

  unsubscribeFromTeamUpdates(teamId: number): void {
    this.sendMessage('unsubscribe_team', { team_id: teamId });
  }

  // Admin Configuration Management
  updateConfiguration(key: string, value: any, reason?: string): void {
    this.sendMessage('admin_config_update', { 
      key, 
      value, 
      reason 
    });
  }

  batchUpdateConfigurations(updates: Array<{key: string, value: any}>, reason?: string): void {
    this.sendMessage('admin_config_batch_update', { 
      updates, 
      reason 
    });
  }

  resetConfiguration(key: string): void {
    this.sendMessage('admin_config_reset', { key });
  }

  applyBalancePreset(presetId: string): void {
    this.sendMessage('admin_balance_preset', { preset_id: presetId });
  }

  recalculateScores(scope?: 'all' | 'players' | 'teams'): void {
    this.sendMessage('admin_recalculate_scores', { scope: scope || 'all' });
  }

  generateBalanceReport(): void {
    this.sendMessage('admin_balance_report', {});
  }

  exportConfigurations(): void {
    this.sendMessage('admin_export_config', {});
  }

  importConfigurations(configData: any): void {
    this.sendMessage('admin_import_config', { config_data: configData });
  }

  createConfigVersion(versionName: string, description?: string): void {
    this.sendMessage('admin_create_config_version', { 
      version_name: versionName, 
      description 
    });
  }

  broadcastAdminMessage(message: string, targetUsers?: number[]): void {
    this.sendMessage('admin_broadcast', { 
      message, 
      target_users: targetUsers 
    });
  }

  initiateMaintenanceMode(message: string, estimatedDuration?: number): void {
    this.sendMessage('admin_maintenance_mode', { 
      message, 
      estimated_duration: estimatedDuration 
    });
  }

  emergencyReset(reason: string): void {
    this.sendMessage('admin_emergency_reset', { reason });
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();
export default websocketService;
