import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { useAppSelector, useAppDispatch } from '../../hooks/redux';
import { 
  FaDotCircle, 
  FaRocket, 
  FaMapMarkerAlt,
  FaExclamationTriangle,
  FaCheckCircle,
  FaClock,
  FaBolt,
  FaRoute,
  FaCompass,
  FaStar,
  FaQuestionCircle,
  FaPlay,
  FaStop,
  FaSearch,
  FaFilter,
  FaExpand,
  FaEye,
  FaCircle
} from 'react-icons/fa';

// Wormhole Interface Types
interface WormholeConnection {
  id: string;
  name: string;
  from_sector: { x: number; y: number };
  to_sector: { x: number; y: number };
  stability: number; // 0-100%
  energy_cost: number;
  travel_time: number; // seconds
  discovery_date: string;
  last_used: string;
  usage_count: number;
  status: 'stable' | 'unstable' | 'collapsing' | 'unknown';
  accessibility: 'public' | 'restricted' | 'classified';
  danger_level: 'safe' | 'moderate' | 'dangerous' | 'lethal';
  discovered_by?: string;
}

interface TeleportationNetwork {
  total_wormholes: number;
  discovered_wormholes: number;
  accessible_wormholes: number;
  network_efficiency: number;
  last_scan: string;
}

interface NavigationRoute {
  id: string;
  destination: { x: number; y: number };
  route_type: 'direct' | 'wormhole' | 'multi_hop';
  total_distance: number;
  estimated_time: number;
  energy_cost: number;
  safety_rating: number;
  wormholes_used: string[];
  waypoints: Array<{ x: number; y: number; type: 'wormhole' | 'sector' }>;
}

const WormholeContainer = styled.div`
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 24px;
  height: 100%;
  min-height: 700px;
`;

const NavigationDisplay = styled.div`
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
`;

const DisplayHeader = styled.div`
  display: flex;
  justify-content: between;
  align-items: center;
  padding: 16px 20px;
  background: #1a1a1a;
  border-bottom: 1px solid #333;
`;

const DisplayTitle = styled.h3`
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const DisplayControls = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const ControlButton = styled.button<{ active?: boolean; variant?: 'primary' | 'danger' }>`
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  
  ${props => {
    if (props.variant === 'primary') {
      return `
        background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
        color: #000;
        &:hover { background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); }
      `;
    } else if (props.variant === 'danger') {
      return `
        background: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
        color: #fff;
        &:hover { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
      `;
    } else {
      return `
        background: ${props.active ? '#4ade80' : '#333'};
        color: ${props.active ? '#000' : '#fff'};
        border: 1px solid ${props.active ? '#4ade80' : '#555'};
        &:hover { background: ${props.active ? '#22c55e' : '#444'}; }
      `;
    }
  }}
`;

const GalaxyMap = styled.div`
  flex: 1;
  position: relative;
  background: radial-gradient(circle at center, #001122 0%, #000000 100%);
  overflow: hidden;
`;

const GridOverlay = styled.svg`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
`;

const Sector = styled.div<{ 
  x: number; 
  y: number; 
  hasWormhole?: boolean;
  isCurrentLocation?: boolean;
  isDestination?: boolean;
}>`
  position: absolute;
  left: ${props => (props.x / 30) * 100}%;
  top: ${props => (props.y / 15) * 100}%;
  width: 20px;
  height: 20px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 2px solid ${props => {
    if (props.isCurrentLocation) return '#4ade80';
    if (props.isDestination) return '#ef4444';
    if (props.hasWormhole) return '#a855f7';
    return '#374151';
  }};
  background: ${props => {
    if (props.isCurrentLocation) return 'rgba(74, 222, 128, 0.3)';
    if (props.isDestination) return 'rgba(239, 68, 68, 0.3)';
    if (props.hasWormhole) return 'rgba(168, 85, 247, 0.3)';
    return 'rgba(55, 65, 81, 0.1)';
  }};
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 10;
  
  &:hover {
    transform: translate(-50%, -50%) scale(1.2);
    border-width: 3px;
  }
  
  ${props => props.hasWormhole && `
    &::after {
      content: '';
      position: absolute;
      top: -6px;
      left: -6px;
      right: -6px;
      bottom: -6px;
      border: 1px solid rgba(168, 85, 247, 0.5);
      border-radius: 50%;
      animation: wormhole-pulse 2s ease-in-out infinite;
    }
  `}
  
  @keyframes wormhole-pulse {
    0%, 100% { opacity: 0.3; transform: scale(1); }
    50% { opacity: 0.8; transform: scale(1.2); }
  }
`;

const WormholeConnection = styled.div<{
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
  stability: number;
}>`
  position: absolute;
  left: ${props => (props.fromX / 30) * 100}%;
  top: ${props => (props.fromY / 15) * 100}%;
  width: ${props => Math.sqrt(Math.pow((props.toX - props.fromX) / 30 * 100, 2) + Math.pow((props.toY - props.fromY) / 15 * 100, 2))}%;
  height: 2px;
  background: linear-gradient(90deg, 
    rgba(168, 85, 247, ${props => props.stability / 100}), 
    rgba(168, 85, 247, 0.3),
    rgba(168, 85, 247, ${props => props.stability / 100})
  );
  transform-origin: left center;
  transform: rotate(${props => Math.atan2((props.toY - props.fromY) / 15, (props.toX - props.fromX) / 30) * 180 / Math.PI}deg);
  pointer-events: none;
  z-index: 5;
  
  &::after {
    content: '';
    position: absolute;
    top: -1px;
    left: 0;
    right: 0;
    bottom: -1px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    animation: wormhole-energy 3s ease-in-out infinite;
  }
  
  @keyframes wormhole-energy {
    0%, 100% { transform: translateX(-100%); }
    50% { transform: translateX(100%); }
  }
`;

const InfoPanel = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const InfoHeader = styled.div`
  padding: 16px;
  border-bottom: 1px solid #333;
  background: #222;
`;

const InfoTitle = styled.h4`
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const InfoSubtitle = styled.p`
  color: #888;
  font-size: 12px;
  margin: 0;
`;

const InfoContent = styled.div`
  flex: 1;
  overflow-y: auto;
`;

const InfoSection = styled.div`
  padding: 16px;
  border-bottom: 1px solid #333;
`;

const SectionTitle = styled.h5`
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const InfoItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding: 8px;
  background: #0a0a0a;
  border-radius: 6px;
`;

const InfoLabel = styled.span`
  color: #888;
  font-size: 12px;
`;

const InfoValue = styled.span<{ highlight?: boolean; color?: string }>`
  color: ${props => props.color || (props.highlight ? '#4ade80' : '#fff')};
  font-size: 12px;
  font-weight: 500;
`;

const StatusIndicator = styled.div<{ status: string }>`
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  background: ${props => {
    switch (props.status) {
      case 'stable': return 'rgba(34, 197, 94, 0.2)';
      case 'unstable': return 'rgba(234, 179, 8, 0.2)';
      case 'collapsing': return 'rgba(239, 68, 68, 0.2)';
      default: return 'rgba(107, 114, 128, 0.2)';
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'stable': return '#22c55e';
      case 'unstable': return '#eab308';
      case 'collapsing': return '#ef4444';
      default: return '#6b7280';
    }
  }};
`;

const WormholeList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
`;

const WormholeItem = styled.div<{ selected?: boolean }>`
  padding: 12px;
  background: ${props => props.selected ? '#333' : '#0a0a0a'};
  border: 1px solid ${props => props.selected ? '#4ade80' : '#222'};
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: #222;
    border-color: #555;
  }
`;

const WormholeItemHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
`;

const WormholeItemName = styled.h6`
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  margin: 0;
`;

const WormholeItemDetails = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  font-size: 11px;
`;

const DetailItem = styled.div`
  display: flex;
  justify-content: space-between;
  color: #888;
`;

const DetailValue = styled.span`
  color: #fff;
  font-weight: 500;
`;

const RouteCalculator = styled.div`
  padding: 16px;
  background: #0a0a0a;
  border-radius: 8px;
  margin-top: 16px;
`;

const RouteInput = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
`;

const InputGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
`;

const InputLabel = styled.label`
  color: #888;
  font-size: 11px;
  font-weight: 500;
`;

const Input = styled.input`
  padding: 8px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #fff;
  font-size: 12px;
  
  &:focus {
    outline: none;
    border-color: #4ade80;
  }
`;

const WormholeInterface: React.FC<{ shipId: number }> = ({ shipId }) => {
  const dispatch = useAppDispatch();
  const [selectedWormhole, setSelectedWormhole] = useState<WormholeConnection | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [viewMode, setViewMode] = useState<'network' | 'routes'>('network');
  const [destination, setDestination] = useState({ x: 0, y: 0 });
  const [calculatedRoutes, setCalculatedRoutes] = useState<NavigationRoute[]>([]);
  
  // Mock current ship position
  const currentPosition = { x: 15, y: 7 };
  
  // Mock wormhole data
  const [wormholes, setWormholes] = useState<WormholeConnection[]>([
    {
      id: 'wh_001',
      name: 'Alpha Centauri Gateway',
      from_sector: { x: 10, y: 5 },
      to_sector: { x: 25, y: 12 },
      stability: 85,
      energy_cost: 150,
      travel_time: 30,
      discovery_date: '2024-01-15',
      last_used: '2024-12-20',
      usage_count: 47,
      status: 'stable',
      accessibility: 'public',
      danger_level: 'safe',
      discovered_by: 'Federation'
    },
    {
      id: 'wh_002',
      name: 'Vega Nexus',
      from_sector: { x: 5, y: 8 },
      to_sector: { x: 20, y: 3 },
      stability: 60,
      energy_cost: 200,
      travel_time: 45,
      discovery_date: '2024-02-03',
      last_used: '2024-12-18',
      usage_count: 23,
      status: 'unstable',
      accessibility: 'restricted',
      danger_level: 'moderate',
      discovered_by: 'Klingon Empire'
    },
    {
      id: 'wh_003',
      name: 'Quantum Rift',
      from_sector: { x: 18, y: 10 },
      to_sector: { x: 2, y: 14 },
      stability: 25,
      energy_cost: 300,
      travel_time: 60,
      discovery_date: '2024-03-12',
      last_used: '2024-12-15',
      usage_count: 8,
      status: 'collapsing',
      accessibility: 'classified',
      danger_level: 'dangerous'
    }
  ]);

  const [networkStats, setNetworkStats] = useState<TeleportationNetwork>({
    total_wormholes: 15,
    discovered_wormholes: 8,
    accessible_wormholes: 5,
    network_efficiency: 73,
    last_scan: new Date().toISOString()
  });

  const handleScanForWormholes = () => {
    setIsScanning(true);
    setTimeout(() => {
      setIsScanning(false);
      // Simulate discovering new wormhole
      const newWormhole: WormholeConnection = {
        id: `wh_${Date.now()}`,
        name: 'Unknown Anomaly',
        from_sector: { 
          x: Math.floor(Math.random() * 30), 
          y: Math.floor(Math.random() * 15) 
        },
        to_sector: { 
          x: Math.floor(Math.random() * 30), 
          y: Math.floor(Math.random() * 15) 
        },
        stability: Math.floor(Math.random() * 100),
        energy_cost: 100 + Math.floor(Math.random() * 200),
        travel_time: 20 + Math.floor(Math.random() * 60),
        discovery_date: new Date().toISOString(),
        last_used: 'Never',
        usage_count: 0,
        status: 'unknown',
        accessibility: 'public',
        danger_level: 'safe'
      };
      setWormholes(prev => [...prev, newWormhole]);
    }, 3000);
  };

  const handleCalculateRoute = () => {
    // Mock route calculation
    const routes: NavigationRoute[] = [
      {
        id: 'route_direct',
        destination,
        route_type: 'direct',
        total_distance: Math.sqrt(Math.pow(destination.x - currentPosition.x, 2) + Math.pow(destination.y - currentPosition.y, 2)) * 10000,
        estimated_time: 180,
        energy_cost: 250,
        safety_rating: 90,
        wormholes_used: [],
        waypoints: [currentPosition, destination]
      },
      {
        id: 'route_wormhole',
        destination,
        route_type: 'wormhole',
        total_distance: 25000,
        estimated_time: 75,
        energy_cost: 180,
        safety_rating: 75,
        wormholes_used: ['wh_001'],
        waypoints: [
          currentPosition, 
          { x: 10, y: 5, type: 'wormhole' }, 
          { x: 25, y: 12, type: 'wormhole' }, 
          destination
        ]
      }
    ];
    setCalculatedRoutes(routes);
  };

  const handleWormholeTravel = (wormholeId: string) => {
    const wormhole = wormholes.find(w => w.id === wormholeId);
    if (!wormhole) return;
    
    // Simulate travel
    console.log(`Traveling through ${wormhole.name}...`);
    // Here you would dispatch the actual travel action
  };

  const renderGalaxyGrid = () => (
    <GridOverlay>
      {/* Sector grid lines */}
      {Array.from({ length: 31 }, (_, i) => (
        <line
          key={`v${i}`}
          x1={`${(i / 30) * 100}%`}
          y1="0%"
          x2={`${(i / 30) * 100}%`}
          y2="100%"
          stroke="rgba(74, 222, 128, 0.1)"
          strokeWidth="0.5"
        />
      ))}
      {Array.from({ length: 16 }, (_, i) => (
        <line
          key={`h${i}`}
          x1="0%"
          y1={`${(i / 15) * 100}%`}
          x2="100%"
          y2={`${(i / 15) * 100}%`}
          stroke="rgba(74, 222, 128, 0.1)"
          strokeWidth="0.5"
        />
      ))}
      
      {/* Coordinate labels */}
      {Array.from({ length: 6 }, (_, i) => (
        <text
          key={`label_x${i}`}
          x={`${(i * 5 / 30) * 100}%`}
          y="95%"
          textAnchor="middle"
          fill="rgba(74, 222, 128, 0.6)"
          fontSize="10"
        >
          {i * 5}
        </text>
      ))}
      {Array.from({ length: 4 }, (_, i) => (
        <text
          key={`label_y${i}`}
          x="2%"
          y={`${(i * 5 / 15) * 100 + 5}%`}
          textAnchor="start"
          fill="rgba(74, 222, 128, 0.6)"
          fontSize="10"
        >
          {i * 5}
        </text>
      ))}
    </GridOverlay>
  );

  return (
    <WormholeContainer>
      <NavigationDisplay>
        <DisplayHeader>
          <DisplayTitle>
            <FaDotCircle />
            Wormhole Navigation Network
          </DisplayTitle>
          <DisplayControls>
            <ControlButton 
              active={viewMode === 'network'} 
              onClick={() => setViewMode('network')}
            >
              <FaCompass />
              Network
            </ControlButton>
            <ControlButton 
              active={viewMode === 'routes'} 
              onClick={() => setViewMode('routes')}
            >
              <FaRoute />
              Routes
            </ControlButton>
            <ControlButton 
              onClick={handleScanForWormholes}
              disabled={isScanning}
              variant="primary"
            >
              {isScanning ? <FaClock /> : <FaSearch />}
              {isScanning ? 'Scanning...' : 'Scan'}
            </ControlButton>
          </DisplayControls>
        </DisplayHeader>
        
        <GalaxyMap>
          {renderGalaxyGrid()}
          
          {/* Render wormhole connections */}
          {wormholes.map(wormhole => (
            <WormholeConnection
              key={`connection_${wormhole.id}`}
              fromX={wormhole.from_sector.x}
              fromY={wormhole.from_sector.y}
              toX={wormhole.to_sector.x}
              toY={wormhole.to_sector.y}
              stability={wormhole.stability}
            />
          ))}
          
          {/* Render sectors */}
          {Array.from({ length: 30 * 15 }, (_, i) => {
            const x = i % 30;
            const y = Math.floor(i / 30);
            const hasWormhole = wormholes.some(w => 
              (w.from_sector.x === x && w.from_sector.y === y) ||
              (w.to_sector.x === x && w.to_sector.y === y)
            );
            const isCurrentLocation = x === currentPosition.x && y === currentPosition.y;
            const isDestination = x === destination.x && y === destination.y;
            
            return (
              <Sector
                key={`sector_${x}_${y}`}
                x={x}
                y={y}
                hasWormhole={hasWormhole}
                isCurrentLocation={isCurrentLocation}
                isDestination={isDestination}
                onClick={() => setDestination({ x, y })}
                title={`Sector (${x}, ${y})`}
              />
            );
          })}
        </GalaxyMap>
      </NavigationDisplay>
      
      <InfoPanel>
        <InfoHeader>
          <InfoTitle>
            <FaEye />
            {selectedWormhole ? selectedWormhole.name : 'Network Overview'}
          </InfoTitle>
          <InfoSubtitle>
            {selectedWormhole 
              ? `${selectedWormhole.from_sector.x},${selectedWormhole.from_sector.y} → ${selectedWormhole.to_sector.x},${selectedWormhole.to_sector.y}`
              : `${networkStats.discovered_wormholes}/${networkStats.total_wormholes} wormholes discovered`
            }
          </InfoSubtitle>
        </InfoHeader>
        
        <InfoContent>
          {selectedWormhole ? (
            <>
              <InfoSection>
                <SectionTitle>
                  <FaDotCircle />
                  Wormhole Details
                </SectionTitle>
                <InfoItem>
                  <InfoLabel>Stability:</InfoLabel>
                  <InfoValue color={selectedWormhole.stability > 70 ? '#22c55e' : selectedWormhole.stability > 40 ? '#eab308' : '#ef4444'}>
                    {selectedWormhole.stability}%
                  </InfoValue>
                </InfoItem>
                <InfoItem>
                  <InfoLabel>Energy Cost:</InfoLabel>
                  <InfoValue>{selectedWormhole.energy_cost} units</InfoValue>
                </InfoItem>
                <InfoItem>
                  <InfoLabel>Travel Time:</InfoLabel>
                  <InfoValue>{selectedWormhole.travel_time}s</InfoValue>
                </InfoItem>
                <InfoItem>
                  <InfoLabel>Usage Count:</InfoLabel>
                  <InfoValue>{selectedWormhole.usage_count}</InfoValue>
                </InfoItem>
                <InfoItem>
                  <InfoLabel>Status:</InfoLabel>
                  <StatusIndicator status={selectedWormhole.status}>
                    <FaCircle size={6} />
                    {selectedWormhole.status.toUpperCase()}
                  </StatusIndicator>
                </InfoItem>
              </InfoSection>
              
              <InfoSection>
                <ControlButton
                  variant="primary"
                  onClick={() => handleWormholeTravel(selectedWormhole.id)}
                  style={{ width: '100%' }}
                  disabled={selectedWormhole.status === 'collapsing'}
                >
                  <FaRocket />
                  Initiate Travel
                </ControlButton>
              </InfoSection>
            </>
          ) : (
            <>
              <InfoSection>
                <SectionTitle>
                  <FaStar />
                  Network Statistics
                </SectionTitle>
                <InfoItem>
                  <InfoLabel>Total Wormholes:</InfoLabel>
                  <InfoValue>{networkStats.total_wormholes}</InfoValue>
                </InfoItem>
                <InfoItem>
                  <InfoLabel>Discovered:</InfoLabel>
                  <InfoValue highlight>{networkStats.discovered_wormholes}</InfoValue>
                </InfoItem>
                <InfoItem>
                  <InfoLabel>Accessible:</InfoLabel>
                  <InfoValue>{networkStats.accessible_wormholes}</InfoValue>
                </InfoItem>
                <InfoItem>
                  <InfoLabel>Network Efficiency:</InfoLabel>
                  <InfoValue color={networkStats.network_efficiency > 70 ? '#22c55e' : '#eab308'}>
                    {networkStats.network_efficiency}%
                  </InfoValue>
                </InfoItem>
              </InfoSection>
              
              <InfoSection>
                <SectionTitle>
                  <FaCompass />
                  Known Wormholes
                </SectionTitle>
                <WormholeList>
                  {wormholes.map(wormhole => (
                    <WormholeItem
                      key={wormhole.id}
                      selected={selectedWormhole?.id === wormhole.id}
                      onClick={() => setSelectedWormhole(wormhole)}
                    >
                      <WormholeItemHeader>
                        <WormholeItemName>{wormhole.name}</WormholeItemName>
                        <StatusIndicator status={wormhole.status}>
                          <FaCircle size={4} />
                        </StatusIndicator>
                      </WormholeItemHeader>
                      <WormholeItemDetails>
                        <DetailItem>
                          <span>From:</span>
                          <DetailValue>({wormhole.from_sector.x},{wormhole.from_sector.y})</DetailValue>
                        </DetailItem>
                        <DetailItem>
                          <span>To:</span>
                          <DetailValue>({wormhole.to_sector.x},{wormhole.to_sector.y})</DetailValue>
                        </DetailItem>
                        <DetailItem>
                          <span>Stability:</span>
                          <DetailValue>{wormhole.stability}%</DetailValue>
                        </DetailItem>
                        <DetailItem>
                          <span>Energy:</span>
                          <DetailValue>{wormhole.energy_cost}</DetailValue>
                        </DetailItem>
                      </WormholeItemDetails>
                    </WormholeItem>
                  ))}
                </WormholeList>
              </InfoSection>
              
              <InfoSection>
                <RouteCalculator>
                  <SectionTitle>
                    <FaRoute />
                    Route Calculator
                  </SectionTitle>
                  <RouteInput>
                    <InputGroup>
                      <InputLabel>Destination X:</InputLabel>
                      <Input
                        type="number"
                        value={destination.x}
                        onChange={(e) => setDestination(prev => ({ ...prev, x: parseInt(e.target.value) || 0 }))}
                        min={0}
                        max={29}
                      />
                    </InputGroup>
                    <InputGroup>
                      <InputLabel>Destination Y:</InputLabel>
                      <Input
                        type="number"
                        value={destination.y}
                        onChange={(e) => setDestination(prev => ({ ...prev, y: parseInt(e.target.value) || 0 }))}
                        min={0}
                        max={14}
                      />
                    </InputGroup>
                  </RouteInput>
                  <ControlButton
                    onClick={handleCalculateRoute}
                    style={{ width: '100%' }}
                    variant="primary"
                  >
                    <FaCompass />
                    Calculate Routes
                  </ControlButton>
                  
                  {calculatedRoutes.length > 0 && (
                    <div style={{ marginTop: '12px' }}>
                      <h6 style={{ color: '#fff', fontSize: '12px', marginBottom: '8px' }}>Available Routes:</h6>
                      {calculatedRoutes.map(route => (
                        <div key={route.id} style={{ padding: '8px', background: '#1a1a1a', borderRadius: '4px', marginBottom: '6px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                            <span style={{ color: '#fff', fontSize: '11px', fontWeight: '600' }}>
                              {route.route_type.replace('_', ' ').toUpperCase()}
                            </span>
                            <span style={{ color: '#4ade80', fontSize: '11px' }}>
                              {route.estimated_time}s
                            </span>
                          </div>
                          <div style={{ fontSize: '10px', color: '#888' }}>
                            Distance: {route.total_distance.toLocaleString()}m | 
                            Energy: {route.energy_cost} | 
                            Safety: {route.safety_rating}%
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </RouteCalculator>
              </InfoSection>
            </>
          )}
        </InfoContent>
      </InfoPanel>
    </WormholeContainer>
  );
};

export default WormholeInterface;
