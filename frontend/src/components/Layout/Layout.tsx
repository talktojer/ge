import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { logout } from '../../store/slices/authSlice';
import { toggleSidebar, setActivePanel } from '../../store/slices/uiSlice';
import Sidebar from './Sidebar';
import Header from './Header';
import styled from 'styled-components';

const LayoutContainer = styled.div`
  display: flex;
  height: 100vh;
  background: #0a0a0a;
  color: #fff;
`;

const SidebarWrapper = styled.div<{ collapsed: boolean }>`
  width: ${props => props.collapsed ? '60px' : '280px'};
  transition: width 0.3s ease;
  background: #1a1a1a;
  border-right: 1px solid #333;
  overflow: hidden;
`;

const MainContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const ContentArea = styled.main`
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #0a0a0a;
`;

const Layout: React.FC = () => {
  const dispatch = useAppDispatch();
  const { sidebar_collapsed, active_panel } = useAppSelector((state) => state.ui);
  const { user } = useAppSelector((state) => state.auth);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth < 768) {
        dispatch(toggleSidebar());
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, [dispatch]);

  const handleLogout = () => {
    dispatch(logout());
  };

  const handlePanelChange = (panel: string) => {
    dispatch(setActivePanel(panel));
  };

  return (
    <LayoutContainer>
      <SidebarWrapper collapsed={sidebar_collapsed}>
        <Sidebar 
          collapsed={sidebar_collapsed}
          onToggle={() => dispatch(toggleSidebar())}
          onPanelChange={handlePanelChange}
          activePanel={active_panel}
          user={user}
          onLogout={handleLogout}
        />
      </SidebarWrapper>
      
      <MainContent>
        <Header 
          onToggleSidebar={() => dispatch(toggleSidebar())}
          sidebarCollapsed={sidebar_collapsed}
        />
        <ContentArea>
          <Outlet />
        </ContentArea>
      </MainContent>
    </LayoutContainer>
  );
};

export default Layout;
