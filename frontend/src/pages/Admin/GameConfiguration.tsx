import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store';
import { api } from '../../services/api';
import { 
  AdminStatsResponse, 
  ConfigParameter, 
  BalanceMetrics, 
  PlayerRanking,
  TeamRanking 
} from '../../types';
import BalanceControls from '../../components/Admin/BalanceControls';
import ScoringSystem from '../../components/Admin/ScoringSystem';
import { showNotification } from '../../store/slices/notificationSlice';

const AdminContainer = styled.div`
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
  min-height: 100vh;
  color: #ffffff;
`;

const AdminHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #333;
`;

const AdminTitle = styled.h1`
  font-size: 2.5rem;
  font-weight: bold;
  background: linear-gradient(45deg, #00d4ff, #0099cc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
`;

const StatCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-5px);
    border-color: rgba(0, 212, 255, 0.3);
    box-shadow: 0 10px 30px rgba(0, 212, 255, 0.1);
  }
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: bold;
  color: #00d4ff;
  margin-bottom: 0.5rem;
`;

const StatLabel = styled.div`
  font-size: 0.9rem;
  color: #cccccc;
  text-transform: uppercase;
  letter-spacing: 1px;
`;

const TabContainer = styled.div`
  margin-bottom: 2rem;
`;

const TabList = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  border-bottom: 2px solid #333;
`;

const Tab = styled.button<{ active: boolean }>`
  padding: 1rem 2rem;
  background: ${props => props.active ? 'linear-gradient(45deg, #00d4ff, #0099cc)' : 'transparent'};
  border: none;
  border-radius: 8px 8px 0 0;
  color: ${props => props.active ? '#ffffff' : '#cccccc'};
  font-weight: ${props => props.active ? 'bold' : 'normal'};
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;

  &:hover {
    background: ${props => props.active ? 'linear-gradient(45deg, #00d4ff, #0099cc)' : 'rgba(255, 255, 255, 0.1)'};
    color: #ffffff;
  }

  &::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    right: 0;
    height: 2px;
    background: ${props => props.active ? 'linear-gradient(45deg, #00d4ff, #0099cc)' : 'transparent'};
  }
`;

const TabContent = styled.div`
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 2rem;
  backdrop-filter: blur(10px);
`;

const ConfigSection = styled.div`
  margin-bottom: 2rem;
`;

const SectionTitle = styled.h3`
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: #00d4ff;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &::before {
    content: '⚙️';
    font-size: 1.2rem;
  }
`;

const ConfigGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
`;

const ConfigItem = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
`;

const ConfigLabel = styled.label`
  display: block;
  font-size: 0.9rem;
  color: #cccccc;
  margin-bottom: 0.5rem;
  font-weight: 500;
`;

const ConfigInput = styled.input`
  width: 100%;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: #ffffff;
  font-size: 1rem;

  &:focus {
    outline: none;
    border-color: #00d4ff;
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
  }
`;

const ConfigSelect = styled.select`
  width: 100%;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: #ffffff;
  font-size: 1rem;

  &:focus {
    outline: none;
    border-color: #00d4ff;
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
  }

  option {
    background: #1a1a2e;
    color: #ffffff;
  }
`;

const ConfigDescription = styled.div`
  font-size: 0.8rem;
  color: #999999;
  margin-top: 0.5rem;
  line-height: 1.4;
`;

const Button = styled.button<{ variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;

  ${props => {
    switch (props.variant) {
      case 'primary':
        return `
          background: linear-gradient(45deg, #00d4ff, #0099cc);
          color: #ffffff;
          &:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 212, 255, 0.3);
          }
        `;
      case 'danger':
        return `
          background: linear-gradient(45deg, #ff4757, #c44569);
          color: #ffffff;
          &:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 71, 87, 0.3);
          }
        `;
      default:
        return `
          background: rgba(255, 255, 255, 0.1);
          color: #ffffff;
          border: 1px solid rgba(255, 255, 255, 0.2);
          &:hover {
            background: rgba(255, 255, 255, 0.2);
          }
        `;
    }
  }}

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none !important;
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
  flex-wrap: wrap;
`;

const LoadingSpinner = styled.div`
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #00d4ff;
  animation: spin 1s ease-in-out infinite;

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

const ErrorMessage = styled.div`
  background: rgba(255, 71, 87, 0.1);
  border: 1px solid rgba(255, 71, 87, 0.3);
  border-radius: 6px;
  padding: 1rem;
  color: #ff4757;
  margin-bottom: 1rem;
`;

const SuccessMessage = styled.div`
  background: rgba(46, 204, 113, 0.1);
  border: 1px solid rgba(46, 204, 113, 0.3);
  border-radius: 6px;
  padding: 1rem;
  color: #2ecc71;
  margin-bottom: 1rem;
`;

type TabType = 'overview' | 'configuration' | 'balance' | 'scoring' | 'history';

interface GameConfigurationProps {}

const GameConfiguration: React.FC<GameConfigurationProps> = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state: RootState) => state.auth);
  
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // State for different data
  const [stats, setStats] = useState<AdminStatsResponse | null>(null);
  const [configurations, setConfigurations] = useState<Record<string, ConfigParameter>>({});
  const [balanceMetrics, setBalanceMetrics] = useState<BalanceMetrics[]>([]);
  const [playerRankings, setPlayerRankings] = useState<PlayerRanking[]>([]);
  const [teamRankings, setTeamRankings] = useState<TeamRanking[]>([]);

  // Check admin privileges
  useEffect(() => {
    if (!user?.is_admin) {
      setError('Admin privileges required to access this page');
      return;
    }
  }, [user]);

  // Load initial data
  useEffect(() => {
    if (user?.is_admin) {
      loadInitialData();
    }
  }, [user]);

  const loadInitialData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load admin stats
      const statsResponse = await api.get('/admin/stats');
      setStats(statsResponse.data);
      
      // Load configurations
      const configResponse = await api.get('/admin/config');
      setConfigurations(configResponse.data);
      
      // Load balance analysis
      const balanceResponse = await api.get('/admin/balance/analysis');
      setBalanceMetrics(balanceResponse.data.analysis);
      
      // Load player rankings
      const playerRankingsResponse = await api.get('/admin/scoring/rankings/players');
      setPlayerRankings(playerRankingsResponse.data.rankings);
      
      // Load team rankings
      const teamRankingsResponse = await api.get('/admin/scoring/rankings/teams');
      setTeamRankings(teamRankingsResponse.data.rankings);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load admin data');
      dispatch(showNotification({
        type: 'error',
        message: 'Failed to load admin data'
      }));
    } finally {
      setLoading(false);
    }
  }, [dispatch]);

  const handleConfigUpdate = useCallback(async (key: string, value: any, reason?: string) => {
    try {
      setLoading(true);
      setError(null);
      
      await api.put(`/admin/config/${key}`, {
        key,
        value,
        reason
      });
      
      // Update local state
      setConfigurations(prev => ({
        ...prev,
        [key]: {
          ...prev[key],
          value
        }
      }));
      
      setSuccess(`Configuration '${key}' updated successfully`);
      dispatch(showNotification({
        type: 'success',
        message: `Configuration '${key}' updated`
      }));
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update configuration');
      dispatch(showNotification({
        type: 'error',
        message: 'Failed to update configuration'
      }));
    } finally {
      setLoading(false);
    }
  }, [dispatch]);

  const handleBatchConfigUpdate = useCallback(async (updates: Array<{key: string, value: any}>, reason?: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.put('/admin/config/batch', {
        updates,
        reason
      });
      
      // Update local state for successful updates
      const successfulUpdates = response.data.results;
      setConfigurations(prev => {
        const updated = { ...prev };
        successfulUpdates.forEach((update: any) => {
          updated[update.key] = {
            ...updated[update.key],
            value: update.value
          };
        });
        return updated;
      });
      
      const errorCount = response.data.errors.length;
      if (errorCount > 0) {
        setError(`${errorCount} configuration updates failed. Check the console for details.`);
      } else {
        setSuccess('All configurations updated successfully');
      }
      
      dispatch(showNotification({
        type: errorCount > 0 ? 'warning' : 'success',
        message: `Batch update completed: ${successfulUpdates.length} successful, ${errorCount} failed`
      }));
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update configurations');
      dispatch(showNotification({
        type: 'error',
        message: 'Failed to update configurations'
      }));
    } finally {
      setLoading(false);
    }
  }, [dispatch]);

  const handleConfigReset = useCallback(async (key: string) => {
    try {
      setLoading(true);
      setError(null);
      
      await api.post(`/admin/config/reset/${key}`);
      
      // Reload configurations to get updated values
      const configResponse = await api.get('/admin/config');
      setConfigurations(configResponse.data);
      
      setSuccess(`Configuration '${key}' reset to default`);
      dispatch(showNotification({
        type: 'success',
        message: `Configuration '${key}' reset to default`
      }));
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset configuration');
      dispatch(showNotification({
        type: 'error',
        message: 'Failed to reset configuration'
      }));
    } finally {
      setLoading(false);
    }
  }, [dispatch]);

  const renderOverviewTab = () => (
    <div>
      <SectionTitle>System Overview</SectionTitle>
      {stats && (
        <StatsGrid>
          <StatCard>
            <StatValue>{stats.total_players}</StatValue>
            <StatLabel>Total Players</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.active_players}</StatValue>
            <StatLabel>Active Players</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.total_teams}</StatValue>
            <StatLabel>Total Teams</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.game_uptime}</StatValue>
            <StatLabel>Game Uptime</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.configuration_count}</StatValue>
            <StatLabel>Configurations</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.pending_balance_adjustments}</StatValue>
            <StatLabel>Pending Adjustments</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue style={{ color: stats.system_health === 'healthy' ? '#2ecc71' : '#ff4757' }}>
              {stats.system_health.toUpperCase()}
            </StatValue>
            <StatLabel>System Health</StatLabel>
          </StatCard>
        </StatsGrid>
      )}
      
      <SectionTitle>Balance Analysis</SectionTitle>
      {balanceMetrics.length > 0 ? (
        <div>
          {balanceMetrics.map((metric, index) => (
            <ConfigItem key={index}>
              <ConfigLabel>{metric.factor.replace('_', ' ').toUpperCase()}</ConfigLabel>
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>Current:</strong> {metric.current_value} | 
                <strong> Target:</strong> {metric.target_value} | 
                <strong> Deviation:</strong> {metric.deviation_percent.toFixed(1)}%
              </div>
              <ConfigDescription>
                <strong>Recommendation:</strong> {metric.recommendation}
              </ConfigDescription>
              <div style={{ 
                marginTop: '0.5rem', 
                padding: '0.25rem 0.5rem', 
                borderRadius: '4px',
                background: metric.impact_level === 'critical' ? 'rgba(255, 71, 87, 0.2)' :
                           metric.impact_level === 'high' ? 'rgba(255, 193, 7, 0.2)' :
                           metric.impact_level === 'medium' ? 'rgba(52, 152, 219, 0.2)' :
                           'rgba(46, 204, 113, 0.2)',
                color: metric.impact_level === 'critical' ? '#ff4757' :
                       metric.impact_level === 'high' ? '#f39c12' :
                       metric.impact_level === 'medium' ? '#3498db' : '#2ecc71',
                fontSize: '0.8rem',
                fontWeight: 'bold',
                textTransform: 'uppercase'
              }}>
                {metric.impact_level} Impact
              </div>
            </ConfigItem>
          ))}
        </div>
      ) : (
        <div>No balance metrics available</div>
      )}
    </div>
  );

  const renderConfigurationTab = () => (
    <div>
      <SectionTitle>Game Configuration</SectionTitle>
      <ConfigSection>
        <h4>Ship Balance</h4>
        <ConfigGrid>
          {Object.entries(configurations)
            .filter(([key, config]) => config.category === 'ship_balance')
            .map(([key, config]) => (
              <ConfigItem key={key}>
                <ConfigLabel>{config.description}</ConfigLabel>
                {config.config_type === 'boolean' ? (
                  <ConfigSelect
                    value={config.value}
                    onChange={(e) => handleConfigUpdate(key, e.target.value === 'true')}
                  >
                    <option value="true">True</option>
                    <option value="false">False</option>
                  </ConfigSelect>
                ) : (
                  <ConfigInput
                    type={config.config_type === 'integer' ? 'number' : 
                          config.config_type === 'float' ? 'number' : 'text'}
                    value={config.value}
                    onChange={(e) => {
                      const value = config.config_type === 'integer' ? parseInt(e.target.value) :
                                   config.config_type === 'float' ? parseFloat(e.target.value) :
                                   e.target.value;
                      handleConfigUpdate(key, value);
                    }}
                    min={config.min_value}
                    max={config.max_value}
                    step={config.config_type === 'float' ? '0.1' : undefined}
                  />
                )}
                <ConfigDescription>
                  Type: {config.config_type} | 
                  Range: {config.min_value !== undefined ? config.min_value : 'N/A'} - {config.max_value !== undefined ? config.max_value : 'N/A'}
                  {config.requires_restart && ' | Requires Restart'}
                </ConfigDescription>
                <Button
                  variant="secondary"
                  onClick={() => handleConfigReset(key)}
                  style={{ marginTop: '0.5rem', fontSize: '0.8rem', padding: '0.5rem 1rem' }}
                >
                  Reset to Default
                </Button>
              </ConfigItem>
            ))}
        </ConfigGrid>
      </ConfigSection>

      <ConfigSection>
        <h4>Combat Balance</h4>
        <ConfigGrid>
          {Object.entries(configurations)
            .filter(([key, config]) => config.category === 'combat_balance')
            .map(([key, config]) => (
              <ConfigItem key={key}>
                <ConfigLabel>{config.description}</ConfigLabel>
                {config.config_type === 'boolean' ? (
                  <ConfigSelect
                    value={config.value}
                    onChange={(e) => handleConfigUpdate(key, e.target.value === 'true')}
                  >
                    <option value="true">True</option>
                    <option value="false">False</option>
                  </ConfigSelect>
                ) : (
                  <ConfigInput
                    type={config.config_type === 'integer' ? 'number' : 
                          config.config_type === 'float' ? 'number' : 'text'}
                    value={config.value}
                    onChange={(e) => {
                      const value = config.config_type === 'integer' ? parseInt(e.target.value) :
                                   config.config_type === 'float' ? parseFloat(e.target.value) :
                                   e.target.value;
                      handleConfigUpdate(key, value);
                    }}
                    min={config.min_value}
                    max={config.max_value}
                    step={config.config_type === 'float' ? '0.1' : undefined}
                  />
                )}
                <ConfigDescription>
                  Type: {config.config_type} | 
                  Range: {config.min_value !== undefined ? config.min_value : 'N/A'} - {config.max_value !== undefined ? config.max_value : 'N/A'}
                  {config.requires_restart && ' | Requires Restart'}
                </ConfigDescription>
                <Button
                  variant="secondary"
                  onClick={() => handleConfigReset(key)}
                  style={{ marginTop: '0.5rem', fontSize: '0.8rem', padding: '0.5rem 1rem' }}
                >
                  Reset to Default
                </Button>
              </ConfigItem>
            ))}
        </ConfigGrid>
      </ConfigSection>
    </div>
  );

  const renderBalanceTab = () => (
    <BalanceControls
      configurations={configurations}
      balanceMetrics={balanceMetrics}
      onConfigUpdate={handleConfigUpdate}
      onBatchUpdate={handleBatchConfigUpdate}
      loading={loading}
    />
  );

  const renderScoringTab = () => (
    <ScoringSystem
      playerRankings={playerRankings}
      teamRankings={teamRankings}
      onRefresh={loadInitialData}
      loading={loading}
    />
  );

  const renderHistoryTab = () => (
    <div>
      <SectionTitle>Configuration History</SectionTitle>
      <p>Configuration change history and audit trail will be displayed here.</p>
      <Button variant="primary" onClick={() => api.get('/admin/config/history').then(console.log)}>
        Load History
      </Button>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverviewTab();
      case 'configuration':
        return renderConfigurationTab();
      case 'balance':
        return renderBalanceTab();
      case 'scoring':
        return renderScoringTab();
      case 'history':
        return renderHistoryTab();
      default:
        return renderOverviewTab();
    }
  };

  if (!user?.is_admin) {
    return (
      <AdminContainer>
        <ErrorMessage>
          <h2>Access Denied</h2>
          <p>Admin privileges are required to access the game configuration panel.</p>
        </ErrorMessage>
      </AdminContainer>
    );
  }

  return (
    <AdminContainer>
      <AdminHeader>
        <AdminTitle>Galactic Empire - Admin Panel</AdminTitle>
        <div>
          <Button variant="primary" onClick={loadInitialData} disabled={loading}>
            {loading ? <LoadingSpinner /> : 'Refresh Data'}
          </Button>
        </div>
      </AdminHeader>

      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}

      <TabContainer>
        <TabList>
          <Tab active={activeTab === 'overview'} onClick={() => setActiveTab('overview')}>
            📊 Overview
          </Tab>
          <Tab active={activeTab === 'configuration'} onClick={() => setActiveTab('configuration')}>
            ⚙️ Configuration
          </Tab>
          <Tab active={activeTab === 'balance'} onClick={() => setActiveTab('balance')}>
            ⚖️ Balance
          </Tab>
          <Tab active={activeTab === 'scoring'} onClick={() => setActiveTab('scoring')}>
            🏆 Scoring
          </Tab>
          <Tab active={activeTab === 'history'} onClick={() => setActiveTab('history')}>
            📜 History
          </Tab>
        </TabList>

        <TabContent>
          {renderTabContent()}
        </TabContent>
      </TabContainer>
    </AdminContainer>
  );
};

export default GameConfiguration;
