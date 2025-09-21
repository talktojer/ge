import React from 'react';
import { useAppSelector } from '../../hooks/redux';
import styled from 'styled-components';
import { 
  FaBars, 
  FaBell, 
  FaWifi, 
  FaExclamationTriangle,
  FaClock,
  FaUser
} from 'react-icons/fa';
import { format } from 'date-fns';

const HeaderContainer = styled.header`
  background: #1a1a1a;
  border-bottom: 1px solid #333;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 64px;
`;

const LeftSection = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`;

const MenuButton = styled.button`
  background: none;
  border: none;
  color: #ccc;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.2s ease;

  &:hover {
    background: #333;
    color: #fff;
  }
`;

const Title = styled.h1`
  font-size: 20px;
  font-weight: 600;
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
`;

const RightSection = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`;

const StatusIndicator = styled.div<{ online: boolean }>`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: ${props => props.online ? '#1a4d1a' : '#4d1a1a'};
  border: 1px solid ${props => props.online ? '#22c55e' : '#ef4444'};
  border-radius: 6px;
  font-size: 12px;
  color: ${props => props.online ? '#4ade80' : '#f87171'};
`;

const GameTime = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 6px;
  font-size: 12px;
  color: #ccc;
`;

const NotificationsButton = styled.button`
  position: relative;
  background: none;
  border: none;
  color: #ccc;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.2s ease;

  &:hover {
    background: #333;
    color: #fff;
  }
`;

const NotificationBadge = styled.span`
  position: absolute;
  top: 4px;
  right: 4px;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 6px;
  font-size: 12px;
  color: #ccc;
`;

interface HeaderProps {
  onToggleSidebar: () => void;
  sidebarCollapsed: boolean;
}

const Header: React.FC<HeaderProps> = ({ onToggleSidebar, sidebarCollapsed }) => {
  const { is_connected, game_time, tick_number } = useAppSelector((state) => state.game);
  const { unreadCount } = useAppSelector((state) => state.communication);
  const { user } = useAppSelector((state) => state.auth);

  const formatGameTime = (timeString: string) => {
    try {
      return format(new Date(timeString), 'HH:mm:ss');
    } catch {
      return '00:00:00';
    }
  };

  return (
    <HeaderContainer>
      <LeftSection>
        <MenuButton onClick={onToggleSidebar}>
          <FaBars size={16} />
        </MenuButton>
        {!sidebarCollapsed && (
          <Title>Galactic Empire</Title>
        )}
      </LeftSection>

      <RightSection>
        <StatusIndicator online={is_connected}>
          {is_connected ? <FaWifi size={12} /> : <FaExclamationTriangle size={12} />}
          {is_connected ? 'Online' : 'Offline'}
        </StatusIndicator>

        <GameTime>
          <FaClock size={12} />
          {formatGameTime(game_time)}
          {tick_number > 0 && ` (Tick ${tick_number})`}
        </GameTime>

        <NotificationsButton>
          <FaBell size={16} />
          {unreadCount > 0 && (
            <NotificationBadge>
              {unreadCount > 99 ? '99+' : unreadCount}
            </NotificationBadge>
          )}
        </NotificationsButton>

        <UserInfo>
          <FaUser size={12} />
          {user?.username || 'Guest'}
        </UserInfo>
      </RightSection>
    </HeaderContainer>
  );
};

export default Header;
