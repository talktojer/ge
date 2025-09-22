import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { fetchShips } from '../../store/slices/shipsSlice';
import { fetchPlanets } from '../../store/slices/planetsSlice';
import { getGameState } from '../../store/slices/gameSlice';
import styled from 'styled-components';
import {
  FaShip,
  FaGlobe,
  FaUsers,
  FaExclamationTriangle,
  FaCheckCircle,
  FaClock,
  FaWifi
} from 'react-icons/fa';

const DashboardContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
`;

const WelcomeSection = styled.div`
  margin-bottom: 32px;
`;

const WelcomeTitle = styled.h1`
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
`;

const WelcomeSubtitle = styled.p`
  font-size: 16px;
  color: #888;
  margin-bottom: 16px;
`;

const StatusBanner = styled.div<{ type: 'success' | 'warning' | 'error' | 'info' }>`
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: ${props => {
    switch (props.type) {
      case 'success': return 'rgba(34, 197, 94, 0.1)';
      case 'warning': return 'rgba(251, 191, 36, 0.1)';
      case 'error': return 'rgba(239, 68, 68, 0.1)';
      case 'info': return 'rgba(59, 130, 246, 0.1)';
      default: return 'rgba(107, 114, 128, 0.1)';
    }
  }};
  border: 1px solid ${props => {
    switch (props.type) {
      case 'success': return 'rgba(34, 197, 94, 0.3)';
      case 'warning': return 'rgba(251, 191, 36, 0.3)';
      case 'error': return 'rgba(239, 68, 68, 0.3)';
      case 'info': return 'rgba(59, 130, 246, 0.3)';
      default: return 'rgba(107, 114, 128, 0.3)';
    }
  }};
  color: ${props => {
    switch (props.type) {
      case 'success': return '#22c55e';
      case 'warning': return '#fbbf24';
      case 'error': return '#ef4444';
      case 'info': return '#3b82f6';
      default: return '#6b7280';
    }
  }};
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
`;

const StatCard = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
  transition: all 0.2s ease;

  &:hover {
    border-color: #444;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  }
`;

const StatHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
`;

const StatIcon = styled.div<{ color: string }>`
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: ${props => props.color};
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000;
  font-size: 18px;
`;

const StatTitle = styled.h3`
  font-size: 16px;
  font-weight: 600;
  color: #fff;
`;

const StatValue = styled.div`
  font-size: 32px;
  font-weight: 700;
  color: #4ade80;
  margin-bottom: 8px;
`;

const StatDescription = styled.p`
  font-size: 14px;
  color: #888;
`;

const RecentActivity = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
`;

const ActivityTitle = styled.h2`
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 16px;
`;

const ActivityList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const ActivityItem = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #0a0a0a;
  border-radius: 8px;
  border: 1px solid #222;
`;

const ActivityIcon = styled.div<{ type: string }>`
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${props => {
    switch (props.type) {
      case 'ship': return 'rgba(74, 222, 128, 0.2)';
      case 'planet': return 'rgba(59, 130, 246, 0.2)';
      case 'combat': return 'rgba(239, 68, 68, 0.2)';
      case 'message': return 'rgba(251, 191, 36, 0.2)';
      default: return 'rgba(107, 114, 128, 0.2)';
    }
  }};
  color: ${props => {
    switch (props.type) {
      case 'ship': return '#4ade80';
      case 'planet': return '#3b82f6';
      case 'combat': return '#ef4444';
      case 'message': return '#fbbf24';
      default: return '#6b7280';
    }
  }};
`;

const ActivityContent = styled.div`
  flex: 1;
`;

const ActivityText = styled.p`
  font-size: 14px;
  color: #fff;
  margin-bottom: 4px;
`;

const ActivityTime = styled.p`
  font-size: 12px;
  color: #888;
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  font-size: 16px;
  color: #888;
`;

const Dashboard: React.FC = () => {
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);
  const { game_time, tick_number, is_connected } = useAppSelector((state) => state.game);
  const { ships, isLoading: shipsLoading } = useAppSelector((state) => state.ships);
  const { planets, isLoading: planetsLoading } = useAppSelector((state) => state.planets);

  useEffect(() => {
    dispatch(getGameState());
    dispatch(fetchShips({}));
    dispatch(fetchPlanets({}));
  }, [dispatch]);

  const activeShips = ships.filter(ship => ship.is_active).length;
  const colonizedPlanets = planets.filter(planet => planet.is_colonized).length;
  const totalFleetSize = ships.length;

  // Mock recent activity data
  const recentActivity = [
    { type: 'ship', text: 'Ship "Star Runner" completed jump to Sector 12', time: '2 minutes ago' },
    { type: 'planet', text: 'Planet "New Terra" colonization complete', time: '15 minutes ago' },
    { type: 'message', text: 'New message from Commander Smith', time: '1 hour ago' },
    { type: 'combat', text: 'Combat detected in Sector 8', time: '2 hours ago' },
  ];

  if (shipsLoading || planetsLoading) {
    return (
      <DashboardContainer>
        <LoadingSpinner>Loading dashboard...</LoadingSpinner>
      </DashboardContainer>
    );
  }

  return (
    <DashboardContainer>
      <WelcomeSection>
        <WelcomeTitle>Welcome back, Commander {user?.username}</WelcomeTitle>
        <WelcomeSubtitle>
          The galaxy awaits your command. Current game time: {game_time} (Tick {tick_number})
        </WelcomeSubtitle>
        
        <StatusBanner type={is_connected ? 'success' : 'error'}>
          {is_connected ? <FaCheckCircle /> : <FaExclamationTriangle />}
          <div>
            <strong>{is_connected ? 'Connected' : 'Disconnected'}</strong>
            {is_connected ? ' - Real-time updates active' : ' - Limited functionality'}
          </div>
        </StatusBanner>
      </WelcomeSection>

      <StatsGrid>
        <StatCard>
          <StatHeader>
            <StatIcon color="linear-gradient(135deg, #4ade80 0%, #22c55e 100%)">
              <FaShip />
            </StatIcon>
            <StatTitle>Active Ships</StatTitle>
          </StatHeader>
          <StatValue>{activeShips}</StatValue>
          <StatDescription>Out of {totalFleetSize} total ships</StatDescription>
        </StatCard>

        <StatCard>
          <StatHeader>
            <StatIcon color="linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)">
              <FaGlobe />
            </StatIcon>
            <StatTitle>Colonized Planets</StatTitle>
          </StatHeader>
          <StatValue>{colonizedPlanets}</StatValue>
          <StatDescription>Under your control</StatDescription>
        </StatCard>

        <StatCard>
          <StatHeader>
            <StatIcon color="linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)">
              <FaUsers />
            </StatIcon>
            <StatTitle>Team Members</StatTitle>
          </StatHeader>
          <StatValue>{user?.team_id ? '5' : '0'}</StatValue>
          <StatDescription>{user?.team_id ? 'Active alliance' : 'No team'}</StatDescription>
        </StatCard>

        <StatCard>
          <StatHeader>
            <StatIcon color="linear-gradient(135deg, #f87171 0%, #ef4444 100%)">
              <FaExclamationTriangle />
            </StatIcon>
            <StatTitle>Alerts</StatTitle>
          </StatHeader>
          <StatValue>0</StatValue>
          <StatDescription>All systems nominal</StatDescription>
        </StatCard>
      </StatsGrid>

      <RecentActivity>
        <ActivityTitle>Recent Activity</ActivityTitle>
        <ActivityList>
          {recentActivity.map((activity, index) => (
            <ActivityItem key={index}>
              <ActivityIcon type={activity.type}>
                {activity.type === 'ship' && <FaShip />}
                {activity.type === 'planet' && <FaGlobe />}
                {activity.type === 'combat' && <FaExclamationTriangle />}
                {activity.type === 'message' && <FaUsers />}
              </ActivityIcon>
              <ActivityContent>
                <ActivityText>{activity.text}</ActivityText>
                <ActivityTime>{activity.time}</ActivityTime>
              </ActivityContent>
            </ActivityItem>
          ))}
        </ActivityList>
      </RecentActivity>
    </DashboardContainer>
  );
};

export default Dashboard;
