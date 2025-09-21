import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { getShip, executeShipCommand } from '../../store/slices/shipsSlice';
import styled from 'styled-components';
import {
  FaShip,
  FaArrowUp,
  FaArrowDown,
  FaArrowLeft,
  FaArrowRight,
  FaCrosshairs,
  FaShieldAlt,
  FaBolt,
  FaCog,
  FaMap,
  FaPlay,
  FaPause,
  FaStop,
  FaExclamationTriangle,
  FaCheckCircle,
  FaInfo,
  FaRadar,
  FaEye,
  FaPortal,
  FaUserSecret
} from 'react-icons/fa';

// Import new tactical components
import TacticalDisplay from '../../components/Tactical/TacticalDisplay';
import CombatInterface from '../../components/Tactical/CombatInterface';
import WormholeInterface from '../../components/Navigation/WormholeInterface';
import EspionageInterface from '../../components/Stealth/EspionageInterface';

const ShipControlContainer = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
`;

const ShipHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 24px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
`;

const ShipInfo = styled.div`
  flex: 1;
`;

const ShipName = styled.h1`
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const ShipDetails = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 16px;
`;

const DetailItem = styled.div`
  text-align: center;
`;

const DetailLabel = styled.p`
  font-size: 12px;
  color: #888;
  margin-bottom: 4px;
`;

const DetailValue = styled.p`
  font-size: 16px;
  font-weight: 600;
  color: #fff;
`;

const ShipStatus = styled.div<{ active: boolean }>`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: ${props => props.active ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)'};
  border: 1px solid ${props => props.active ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'};
  border-radius: 8px;
  color: ${props => props.active ? '#22c55e' : '#ef4444'};
  font-weight: 600;
`;

const ControlGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 32px;

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
`;

const ControlPanel = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
`;

const PanelTitle = styled.h2`
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const NavigationControls = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 24px;
`;

const NavButton = styled.button<{ direction: string }>`
  aspect-ratio: 1;
  background: #333;
  border: 1px solid #555;
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;

  &:hover {
    background: #444;
    border-color: #666;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  ${props => props.direction === 'up' && 'grid-column: 2;'}
  ${props => props.direction === 'down' && 'grid-column: 2; grid-row: 3;'}
  ${props => props.direction === 'left' && 'grid-column: 1; grid-row: 2;'}
  ${props => props.direction === 'right' && 'grid-column: 3; grid-row: 2;'}
`;

const CoordinateInput = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
`;

const InputGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const Label = styled.label`
  font-size: 12px;
  color: #888;
  font-weight: 500;
`;

const Input = styled.input`
  padding: 12px;
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 6px;
  color: #fff;
  font-size: 14px;

  &:focus {
    outline: none;
    border-color: #4ade80;
  }
`;

const Button = styled.button<{ variant?: 'primary' | 'danger' | 'secondary' }>`
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;

  ${props => {
    switch (props.variant) {
      case 'primary':
        return `
          background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
          color: #000;
          &:hover { background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); }
        `;
      case 'danger':
        return `
          background: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
          color: #fff;
          &:hover { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
        `;
      default:
        return `
          background: #333;
          color: #fff;
          border: 1px solid #555;
          &:hover { background: #444; border-color: #666; }
        `;
    }
  }}

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const StatusBars = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
`;

const StatusBar = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const StatusBarHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const StatusBarLabel = styled.span`
  font-size: 14px;
  font-weight: 500;
  color: #ccc;
`;

const StatusBarValue = styled.span`
  font-size: 14px;
  font-weight: 600;
  color: #fff;
`;

const StatusBarContainer = styled.div`
  height: 8px;
  background: #333;
  border-radius: 4px;
  overflow: hidden;
`;

const StatusBarFill = styled.div<{ percentage: number; color: string }>`
  height: 100%;
  width: ${props => props.percentage}%;
  background: ${props => props.color};
  transition: width 0.3s ease;
`;

const WeaponsList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const WeaponItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #0a0a0a;
  border: 1px solid #222;
  border-radius: 8px;
`;

const WeaponInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const WeaponIcon = styled.div`
  width: 32px;
  height: 32px;
  background: rgba(239, 68, 68, 0.2);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ef4444;
`;

const WeaponDetails = styled.div`
  flex: 1;
`;

const WeaponName = styled.p`
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 2px;
`;

const WeaponStatus = styled.p`
  font-size: 12px;
  color: #888;
`;

const WeaponAction = styled.button`
  padding: 8px 12px;
  background: #333;
  border: 1px solid #555;
  border-radius: 6px;
  color: #fff;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #444;
  }
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  font-size: 16px;
  color: #888;
`;

const TabContainer = styled.div`
  display: flex;
  border-bottom: 1px solid #333;
  background: #1a1a1a;
  border-radius: 12px 12px 0 0;
`;

const Tab = styled.button<{ active: boolean }>`
  padding: 16px 24px;
  background: ${props => props.active ? '#333' : 'transparent'};
  border: none;
  border-bottom: 2px solid ${props => props.active ? '#4ade80' : 'transparent'};
  color: ${props => props.active ? '#fff' : '#888'};
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  
  &:hover {
    color: #fff;
    background: rgba(255, 255, 255, 0.05);
  }
`;

const TabContent = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 0 0 12px 12px;
  border-top: none;
  min-height: 600px;
`;

const ShipControl: React.FC = () => {
  const { shipId } = useParams<{ shipId: string }>();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { selectedShip, isLoading } = useAppSelector((state) => state.ships);
  
  const [targetCoords, setTargetCoords] = React.useState({
    x: 0,
    y: 0,
    z: 0
  });
  
  const [activeTab, setActiveTab] = React.useState<'navigation' | 'tactical' | 'combat' | 'wormholes' | 'espionage'>('navigation');

  useEffect(() => {
    if (shipId) {
      dispatch(getShip(parseInt(shipId)));
    }
  }, [dispatch, shipId]);

  const handleMoveShip = (direction: string) => {
    if (!selectedShip) return;

    const command = {
      ship_id: selectedShip.id,
      command: 'move',
      parameters: { direction }
    };

    dispatch(executeShipCommand(command));
  };

  const handleJumpToCoordinates = () => {
    if (!selectedShip) return;

    const command = {
      ship_id: selectedShip.id,
      command: 'jump',
      parameters: targetCoords
    };

    dispatch(executeShipCommand(command));
  };

  const handleWeaponFire = (weaponName: string) => {
    if (!selectedShip) return;

    const command = {
      ship_id: selectedShip.id,
      command: 'fire_weapon',
      parameters: { weapon: weaponName }
    };

    dispatch(executeShipCommand(command));
  };

  if (isLoading) {
    return (
      <ShipControlContainer>
        <LoadingSpinner>Loading ship data...</LoadingSpinner>
      </ShipControlContainer>
    );
  }

  if (!selectedShip) {
    return (
      <ShipControlContainer>
        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
          <h2 style={{ color: '#fff', marginBottom: '16px' }}>Ship Not Found</h2>
          <p style={{ color: '#888', marginBottom: '24px' }}>The requested ship could not be found.</p>
          <Button onClick={() => navigate('/ships')}>
            Back to Fleet
          </Button>
        </div>
      </ShipControlContainer>
    );
  }

  const hullPercentage = (selectedShip.hull_points / selectedShip.max_hull_points) * 100;
  const shieldsPercentage = (selectedShip.shields / selectedShip.max_shields) * 100;
  const fuelPercentage = (selectedShip.fuel / selectedShip.max_fuel) * 100;

  return (
    <ShipControlContainer>
      <ShipHeader>
        <ShipInfo>
          <ShipName>
            <FaShip />
            {selectedShip.name}
          </ShipName>
          <p style={{ color: '#888', fontSize: '16px' }}>
            {selectedShip.ship_class} {selectedShip.ship_type}
          </p>
          
          <ShipDetails>
            <DetailItem>
              <DetailLabel>Location</DetailLabel>
              <DetailValue>Sector {selectedShip.sector}</DetailValue>
            </DetailItem>
            <DetailItem>
              <DetailLabel>Coordinates</DetailLabel>
              <DetailValue>({selectedShip.x}, {selectedShip.y}, {selectedShip.z})</DetailValue>
            </DetailItem>
            <DetailItem>
              <DetailLabel>Created</DetailLabel>
              <DetailValue>{new Date(selectedShip.created_at).toLocaleDateString()}</DetailValue>
            </DetailItem>
          </ShipDetails>
        </ShipInfo>
        
        <ShipStatus active={selectedShip.is_active}>
          {selectedShip.is_active ? <FaCheckCircle /> : <FaExclamationTriangle />}
          {selectedShip.is_active ? 'Active' : 'Inactive'}
        </ShipStatus>
      </ShipHeader>

      {/* Enhanced Tabbed Interface */}
      <div style={{ marginBottom: '32px' }}>
        <TabContainer>
          <Tab 
            active={activeTab === 'navigation'} 
            onClick={() => setActiveTab('navigation')}
          >
            <FaMap />
            Navigation & Systems
          </Tab>
          <Tab 
            active={activeTab === 'tactical'} 
            onClick={() => setActiveTab('tactical')}
          >
            <FaRadar />
            Tactical Display
          </Tab>
          <Tab 
            active={activeTab === 'combat'} 
            onClick={() => setActiveTab('combat')}
          >
            <FaCrosshairs />
            Combat Interface
          </Tab>
          <Tab 
            active={activeTab === 'wormholes'} 
            onClick={() => setActiveTab('wormholes')}
          >
            <FaPortal />
            Wormholes
          </Tab>
          <Tab 
            active={activeTab === 'espionage'} 
            onClick={() => setActiveTab('espionage')}
          >
            <FaUserSecret />
            Espionage
          </Tab>
        </TabContainer>
        
        <TabContent>
          {activeTab === 'navigation' && (
            <div style={{ padding: '24px' }}>
              <ControlGrid>
                {/* Navigation Panel */}
                <ControlPanel>
                  <PanelTitle>
                    <FaMap />
                    Navigation Controls
                  </PanelTitle>
                  
                  <NavigationControls>
                    <NavButton direction="up" onClick={() => handleMoveShip('up')}>
                      <FaArrowUp />
                    </NavButton>
                    <NavButton direction="left" onClick={() => handleMoveShip('left')}>
                      <FaArrowLeft />
                    </NavButton>
                    <NavButton direction="right" onClick={() => handleMoveShip('right')}>
                      <FaArrowRight />
                    </NavButton>
                    <NavButton direction="down" onClick={() => handleMoveShip('down')}>
                      <FaArrowDown />
                    </NavButton>
                  </NavigationControls>

                  <CoordinateInput>
                    <InputGroup>
                      <Label>X Coordinate</Label>
                      <Input
                        type="number"
                        value={targetCoords.x}
                        onChange={(e) => setTargetCoords(prev => ({ ...prev, x: parseInt(e.target.value) || 0 }))}
                      />
                    </InputGroup>
                    <InputGroup>
                      <Label>Y Coordinate</Label>
                      <Input
                        type="number"
                        value={targetCoords.y}
                        onChange={(e) => setTargetCoords(prev => ({ ...prev, y: parseInt(e.target.value) || 0 }))}
                      />
                    </InputGroup>
                    <InputGroup>
                      <Label>Z Coordinate</Label>
                      <Input
                        type="number"
                        value={targetCoords.z}
                        onChange={(e) => setTargetCoords(prev => ({ ...prev, z: parseInt(e.target.value) || 0 }))}
                      />
                    </InputGroup>
                  </CoordinateInput>

                  <Button onClick={handleJumpToCoordinates} style={{ width: '100%' }}>
                    <FaPlay />
                    Jump to Coordinates
                  </Button>
                </ControlPanel>

                {/* Systems Panel */}
                <ControlPanel>
                  <PanelTitle>
                    <FaCog />
                    Ship Systems
                  </PanelTitle>
                  
                  <StatusBars>
                    <StatusBar>
                      <StatusBarHeader>
                        <StatusBarLabel>Hull Points</StatusBarLabel>
                        <StatusBarValue>{selectedShip.hull_points}/{selectedShip.max_hull_points}</StatusBarValue>
                      </StatusBarHeader>
                      <StatusBarContainer>
                        <StatusBarFill 
                          percentage={hullPercentage} 
                          color={hullPercentage > 50 ? '#22c55e' : hullPercentage > 25 ? '#fbbf24' : '#ef4444'}
                        />
                      </StatusBarContainer>
                    </StatusBar>

                    <StatusBar>
                      <StatusBarHeader>
                        <StatusBarLabel>Shields</StatusBarLabel>
                        <StatusBarValue>{selectedShip.shields}/{selectedShip.max_shields}</StatusBarValue>
                      </StatusBarHeader>
                      <StatusBarContainer>
                        <StatusBarFill 
                          percentage={shieldsPercentage} 
                          color="#60a5fa"
                        />
                      </StatusBarContainer>
                    </StatusBar>

                    <StatusBar>
                      <StatusBarHeader>
                        <StatusBarLabel>Fuel</StatusBarLabel>
                        <StatusBarValue>{selectedShip.fuel}/{selectedShip.max_fuel}</StatusBarValue>
                      </StatusBarHeader>
                      <StatusBarContainer>
                        <StatusBarFill 
                          percentage={fuelPercentage} 
                          color="#fbbf24"
                        />
                      </StatusBarContainer>
                    </StatusBar>
                  </StatusBars>

                  <div style={{ marginTop: '20px' }}>
                    <Label>Cargo Status</Label>
                    <div style={{ marginTop: '8px', padding: '12px', background: '#0a0a0a', borderRadius: '6px' }}>
                      <p style={{ color: '#fff', fontSize: '14px' }}>
                        {selectedShip.cargo_used} / {selectedShip.cargo_capacity} units used
                      </p>
                    </div>
                  </div>
                </ControlPanel>
              </ControlGrid>

              {/* Basic Weapons Panel */}
              <ControlPanel style={{ marginTop: '24px' }}>
                <PanelTitle>
                  <FaCrosshairs />
                  Weapons Systems
                </PanelTitle>
                
                <WeaponsList>
                  {selectedShip.weapons?.length > 0 ? (
                    selectedShip.weapons.map((weapon, index) => (
                      <WeaponItem key={index}>
                        <WeaponInfo>
                          <WeaponIcon>
                            <FaBolt />
                          </WeaponIcon>
                          <WeaponDetails>
                            <WeaponName>{weapon}</WeaponName>
                            <WeaponStatus>Ready to fire</WeaponStatus>
                          </WeaponDetails>
                        </WeaponInfo>
                        <WeaponAction onClick={() => handleWeaponFire(weapon)}>
                          Fire
                        </WeaponAction>
                      </WeaponItem>
                    ))
                  ) : (
                    <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>
                      <FaCrosshairs style={{ fontSize: '32px', marginBottom: '12px', opacity: 0.5 }} />
                      <p>No weapons installed</p>
                    </div>
                  )}
                </WeaponsList>
              </ControlPanel>
            </div>
          )}
          
          {activeTab === 'tactical' && (
            <div style={{ padding: '24px', height: '600px' }}>
              <TacticalDisplay shipId={selectedShip.id} />
            </div>
          )}
          
          {activeTab === 'combat' && (
            <div style={{ padding: '24px' }}>
              <CombatInterface shipId={selectedShip.id} />
            </div>
          )}
          
          {activeTab === 'wormholes' && (
            <div style={{ padding: '24px' }}>
              <WormholeInterface shipId={selectedShip.id} />
            </div>
          )}
          
          {activeTab === 'espionage' && (
            <div style={{ padding: '24px' }}>
              <EspionageInterface shipId={selectedShip.id} />
            </div>
          )}
        </TabContent>
      </div>
    </ShipControlContainer>
  );
};

export default ShipControl;
