import React from 'react';
import { NavLink } from 'react-router-dom';
import { User } from '../../types';
import styled from 'styled-components';
import {
  FaHome,
  FaShip,
  FaGlobe,
  FaMap,
  FaComments,
  FaUsers,
  FaCog,
  FaSignOutAlt,
  FaChevronLeft,
  FaChevronRight,
  FaRocket,
  FaUser
} from 'react-icons/fa';

const SidebarContainer = styled.div<{ collapsed: boolean }>`
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1a1a1a;
  transition: all 0.3s ease;
`;

const SidebarHeader = styled.div`
  padding: 20px;
  border-bottom: 1px solid #333;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const Logo = styled.div<{ collapsed: boolean }>`
  display: flex;
  align-items: center;
  gap: 12px;
  
  ${props => props.collapsed && `
    justify-content: center;
  `}
`;

const LogoIcon = styled.div`
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000;
  font-size: 16px;
  font-weight: bold;
`;

const LogoText = styled.span<{ collapsed: boolean }>`
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  opacity: ${props => props.collapsed ? 0 : 1};
  transition: opacity 0.3s ease;
`;

const ToggleButton = styled.button`
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s ease;

  &:hover {
    background: #333;
    color: #fff;
  }
`;

const Navigation = styled.nav`
  flex: 1;
  padding: 20px 0;
`;

const NavList = styled.ul`
  list-style: none;
  margin: 0;
  padding: 0;
`;

const NavItem = styled.li`
  margin-bottom: 4px;
`;

const NavLinkStyled = styled(NavLink)<{ collapsed: boolean }>`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  color: #ccc;
  text-decoration: none;
  transition: all 0.2s ease;
  position: relative;

  &:hover {
    background: #333;
    color: #fff;
  }

  &.active {
    background: linear-gradient(135deg, rgba(74, 222, 128, 0.1) 0%, rgba(34, 197, 94, 0.1) 100%);
    color: #4ade80;
    border-right: 3px solid #4ade80;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 3px;
      background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
    }
  }

  ${props => props.collapsed && `
    justify-content: center;
    padding: 12px;
  `}
`;

const NavIcon = styled.div`
  width: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
`;

const NavText = styled.span<{ collapsed: boolean }>`
  font-size: 14px;
  font-weight: 500;
  opacity: ${props => props.collapsed ? 0 : 1};
  transition: opacity 0.3s ease;
`;

const SidebarFooter = styled.div`
  padding: 20px;
  border-top: 1px solid #333;
`;

const UserSection = styled.div<{ collapsed: boolean }>`
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  
  ${props => props.collapsed && `
    justify-content: center;
  `}
`;

const UserAvatar = styled.div`
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
`;

const UserInfo = styled.div<{ collapsed: boolean }>`
  opacity: ${props => props.collapsed ? 0 : 1};
  transition: opacity 0.3s ease;
`;

const UserName = styled.div`
  font-size: 14px;
  font-weight: 600;
  color: #fff;
`;

const UserRole = styled.div`
  font-size: 12px;
  color: #888;
`;

const LogoutButton = styled.button<{ collapsed: boolean }>`
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #2d1a1a;
  border: 1px solid #4d1a1a;
  border-radius: 8px;
  color: #f87171;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #4d1a1a;
    border-color: #6d2a2a;
  }

  ${props => props.collapsed && `
    justify-content: center;
    padding: 12px;
  `}
`;

const LogoutText = styled.span<{ collapsed: boolean }>`
  font-size: 14px;
  font-weight: 500;
  opacity: ${props => props.collapsed ? 0 : 1};
  transition: opacity 0.3s ease;
`;

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  onPanelChange: (panel: string) => void;
  activePanel: string;
  user: User | null;
  onLogout: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  onToggle,
  onPanelChange,
  activePanel,
  user,
  onLogout
}) => {
  const navigationItems = [
    { path: '/dashboard', icon: FaHome, label: 'Dashboard', panel: 'dashboard' },
    { path: '/ships', icon: FaShip, label: 'Fleet', panel: 'ships' },
    { path: '/planets', icon: FaGlobe, label: 'Planets', panel: 'planets' },
    { path: '/galaxy', icon: FaMap, label: 'Galaxy Map', panel: 'galaxy' },
    { path: '/communication', icon: FaComments, label: 'Messages', panel: 'communication' },
    { path: '/teams', icon: FaUsers, label: 'Teams', panel: 'teams' },
    { path: '/settings', icon: FaCog, label: 'Settings', panel: 'settings' },
  ];

  return (
    <SidebarContainer collapsed={collapsed}>
      <SidebarHeader>
        <Logo collapsed={collapsed}>
          <LogoIcon>
            <FaRocket />
          </LogoIcon>
          {!collapsed && <LogoText collapsed={collapsed}>GE</LogoText>}
        </Logo>
        <ToggleButton onClick={onToggle}>
          {collapsed ? <FaChevronRight /> : <FaChevronLeft />}
        </ToggleButton>
      </SidebarHeader>

      <Navigation>
        <NavList>
          {navigationItems.map((item) => (
            <NavItem key={item.path}>
              <NavLinkStyled
                to={item.path}
                collapsed={collapsed}
                onClick={() => onPanelChange(item.panel)}
              >
                <NavIcon>
                  <item.icon />
                </NavIcon>
                <NavText collapsed={collapsed}>{item.label}</NavText>
              </NavLinkStyled>
            </NavItem>
          ))}
        </NavList>
      </Navigation>

      <SidebarFooter>
        <UserSection collapsed={collapsed}>
          <UserAvatar>
            <FaUser />
          </UserAvatar>
          {!collapsed && (
            <UserInfo collapsed={collapsed}>
              <UserName>{user?.userid || 'Guest'}</UserName>
              <UserRole>Commander</UserRole>
            </UserInfo>
          )}
        </UserSection>

        <LogoutButton collapsed={collapsed} onClick={onLogout}>
          <FaSignOutAlt />
          <LogoutText collapsed={collapsed}>Logout</LogoutText>
        </LogoutButton>
      </SidebarFooter>
    </SidebarContainer>
  );
};

export default Sidebar;
