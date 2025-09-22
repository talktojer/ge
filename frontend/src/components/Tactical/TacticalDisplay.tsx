import React, { useEffect, useState, useRef } from 'react';
import styled from 'styled-components';
import { useAppSelector, useAppDispatch } from '../../hooks/redux';
import { 
  FaSearch, 
  FaCrosshairs, 
  FaEye, 
  FaExclamationTriangle,
  FaShieldAlt,
  FaBolt,
  FaCircle,
  FaDotCircle,
  FaPlay,
  FaPause,
  FaExpand,
  FaCompress,
  FaFilter,
  FaCog
} from 'react-icons/fa';

// Types for tactical display
interface TacticalObject {
  id: string;
  type: 'ship' | 'planet' | 'mine' | 'beacon' | 'wormhole' | 'debris';
  name: string;
  x: number;
  y: number;
  distance: number;
  bearing: number;
  threat_level: 'none' | 'low' | 'medium' | 'high' | 'critical';
  owner?: string;
  team?: string;
  status?: string;
  additional_info?: any;
}

interface ScannerData {
  range: number;
  objects: TacticalObject[];
  scanner_type: 'short_range' | 'long_range' | 'tactical' | 'hyperspace' | 'cloak_detector';
  accuracy: number;
  timestamp: string;
}

const TacticalContainer = styled.div<{ isFullscreen: boolean }>`
  position: ${props => props.isFullscreen ? 'fixed' : 'relative'};
  top: ${props => props.isFullscreen ? '0' : 'auto'};
  left: ${props => props.isFullscreen ? '0' : 'auto'};
  width: ${props => props.isFullscreen ? '100vw' : '100%'};
  height: ${props => props.isFullscreen ? '100vh' : '600px'};
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: ${props => props.isFullscreen ? '0' : '12px'};
  overflow: hidden;
  z-index: ${props => props.isFullscreen ? '9999' : 'auto'};
  display: flex;
  flex-direction: column;
`;

const TacticalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #1a1a1a;
  border-bottom: 1px solid #333;
`;

const HeaderLeft = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`;

const HeaderTitle = styled.h3`
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ScannerMode = styled.select`
  background: #333;
  border: 1px solid #555;
  border-radius: 6px;
  color: #fff;
  padding: 8px 12px;
  font-size: 14px;
  
  &:focus {
    outline: none;
    border-color: #4ade80;
  }
`;

const HeaderControls = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const ControlButton = styled.button<{ active?: boolean }>`
  background: ${props => props.active ? '#4ade80' : '#333'};
  border: 1px solid ${props => props.active ? '#4ade80' : '#555'};
  border-radius: 6px;
  color: ${props => props.active ? '#000' : '#fff'};
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  
  &:hover {
    background: ${props => props.active ? '#22c55e' : '#444'};
  }
`;

const TacticalContent = styled.div`
  flex: 1;
  display: flex;
  position: relative;
`;

const RadarDisplay = styled.div`
  flex: 1;
  position: relative;
  background: radial-gradient(circle at center, #0f1f0f 0%, #0a0a0a 100%);
  overflow: hidden;
`;

const RadarGrid = styled.svg`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
`;

const RadarSweep = styled.div<{ active: boolean }>`
  position: absolute;
  top: 50%;
  left: 50%;
  width: 2px;
  height: 40%;
  background: linear-gradient(to top, transparent, #4ade80);
  transform-origin: bottom center;
  transform: translate(-50%, -100%) rotate(0deg);
  animation: ${props => props.active ? 'radar-sweep 4s linear infinite' : 'none'};
  
  @keyframes radar-sweep {
    from { transform: translate(-50%, -100%) rotate(0deg); }
    to { transform: translate(-50%, -100%) rotate(360deg); }
  }
`;

const TacticalObject = styled.div<{ 
  x: number; 
  y: number; 
  threat: string;
  selected?: boolean;
}>`
  position: absolute;
  left: ${props => props.x}%;
  top: ${props => props.y}%;
  transform: translate(-50%, -50%);
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid ${props => {
    switch (props.threat) {
      case 'critical': return '#ef4444';
      case 'high': return '#f97316';
      case 'medium': return '#eab308';
      case 'low': return '#22c55e';
      default: return '#6b7280';
    }
  }};
  background: ${props => props.selected ? '#fff' : 'transparent'};
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 10;
  
  &:hover {
    transform: translate(-50%, -50%) scale(1.2);
    background: rgba(255, 255, 255, 0.3);
  }
  
  &::after {
    content: '';
    position: absolute;
    top: -4px;
    left: -4px;
    right: -4px;
    bottom: -4px;
    border: 1px solid ${props => {
      switch (props.threat) {
        case 'critical': return 'rgba(239, 68, 68, 0.3)';
        case 'high': return 'rgba(249, 115, 22, 0.3)';
        case 'medium': return 'rgba(234, 179, 8, 0.3)';
        case 'low': return 'rgba(34, 197, 94, 0.3)';
        default: return 'rgba(107, 114, 128, 0.3)';
      }
    }};
    border-radius: 50%;
    animation: ${props => props.threat === 'critical' ? 'pulse-critical 1s ease-in-out infinite' : 'none'};
  }
  
  @keyframes pulse-critical {
    0%, 100% { opacity: 0.3; transform: scale(1); }
    50% { opacity: 0.8; transform: scale(1.2); }
  }
`;

const InfoPanel = styled.div`
  width: 300px;
  background: #1a1a1a;
  border-left: 1px solid #333;
  display: flex;
  flex-direction: column;
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

const InfoSectionTitle = styled.h5`
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
`;

const InfoLabel = styled.span`
  color: #888;
  font-size: 12px;
`;

const InfoValue = styled.span<{ highlight?: boolean }>`
  color: ${props => props.highlight ? '#4ade80' : '#fff'};
  font-size: 12px;
  font-weight: 500;
`;

const ThreatIndicator = styled.div<{ level: string }>`
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  background: ${props => {
    switch (props.level) {
      case 'critical': return 'rgba(239, 68, 68, 0.2)';
      case 'high': return 'rgba(249, 115, 22, 0.2)';
      case 'medium': return 'rgba(234, 179, 8, 0.2)';
      case 'low': return 'rgba(34, 197, 94, 0.2)';
      default: return 'rgba(107, 114, 128, 0.2)';
    }
  }};
  color: ${props => {
    switch (props.level) {
      case 'critical': return '#ef4444';
      case 'high': return '#f97316';
      case 'medium': return '#eab308';
      case 'low': return '#22c55e';
      default: return '#6b7280';
    }
  }};
  font-size: 11px;
  font-weight: 600;
`;

const TacticalDisplay: React.FC<{ shipId: number }> = ({ shipId }) => {
  const dispatch = useAppDispatch();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isScanning, setIsScanning] = useState(true);
  const [scannerMode, setScannerMode] = useState<ScannerData['scanner_type']>('long_range');
  const [selectedObject, setSelectedObject] = useState<TacticalObject | null>(null);
  const [scannerData, setScannerData] = useState<ScannerData>({
    range: 50000,
    objects: [],
    scanner_type: 'long_range',
    accuracy: 0.85,
    timestamp: new Date().toISOString()
  });
  const [filters, setFilters] = useState({
    ship: true,
    planet: true,
    mine: true,
    beacon: true,
    wormhole: true,
    debris: false
  });

  const radarRef = useRef<HTMLDivElement>(null);

  // Simulate scanner data updates
  useEffect(() => {
    if (!isScanning) return;

    const interval = setInterval(() => {
      // Simulate receiving scanner data from WebSocket
      const mockObjects: TacticalObject[] = [
        {
          id: 'ship_1',
          type: 'ship',
          name: 'USS Enterprise',
          x: 30,
          y: 40,
          distance: 15000,
          bearing: 45,
          threat_level: 'high',
          owner: 'Federation',
          team: 'Blue Team',
          status: 'hostile'
        },
        {
          id: 'planet_1',
          type: 'planet',
          name: 'Earth',
          x: 70,
          y: 20,
          distance: 35000,
          bearing: 120,
          threat_level: 'none',
          owner: 'Federation',
          status: 'colonized'
        },
        {
          id: 'mine_1',
          type: 'mine',
          name: 'Proximity Mine',
          x: 60,
          y: 80,
          distance: 8000,
          bearing: 220,
          threat_level: 'critical',
          status: 'active'
        }
      ];

      setScannerData(prev => ({
        ...prev,
        objects: mockObjects,
        timestamp: new Date().toISOString()
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, [isScanning, scannerMode]);

  const handleObjectClick = (obj: TacticalObject) => {
    setSelectedObject(obj);
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const toggleScanning = () => {
    setIsScanning(!isScanning);
  };

  const handleScannerModeChange = (mode: ScannerData['scanner_type']) => {
    setScannerMode(mode);
    setScannerData(prev => ({ ...prev, scanner_type: mode }));
  };

  const filteredObjects = scannerData.objects.filter(obj => filters[obj.type]);

  const renderRadarGrid = () => (
    <RadarGrid>
      {/* Concentric circles */}
      {[25, 50, 75].map(radius => (
        <circle
          key={radius}
          cx="50%"
          cy="50%"
          r={`${radius}%`}
          fill="none"
          stroke="rgba(74, 222, 128, 0.2)"
          strokeWidth="1"
        />
      ))}
      
      {/* Cross hairs */}
      <line x1="50%" y1="0%" x2="50%" y2="100%" stroke="rgba(74, 222, 128, 0.2)" strokeWidth="1" />
      <line x1="0%" y1="50%" x2="100%" y2="50%" stroke="rgba(74, 222, 128, 0.2)" strokeWidth="1" />
      
      {/* Bearing markers */}
      {[0, 45, 90, 135, 180, 225, 270, 315].map(angle => (
        <g key={angle}>
          <text
            x="50%"
            y="10%"
            textAnchor="middle"
            fill="rgba(74, 222, 128, 0.6)"
            fontSize="10"
            transform={`rotate(${angle} 50% 50%)`}
          >
            {angle}°
          </text>
        </g>
      ))}
    </RadarGrid>
  );

  return (
    <TacticalContainer isFullscreen={isFullscreen}>
      <TacticalHeader>
        <HeaderLeft>
          <HeaderTitle>
            <FaSearch />
            Tactical Display
          </HeaderTitle>
          <ScannerMode 
            value={scannerMode}
            onChange={(e) => handleScannerModeChange(e.target.value as ScannerData['scanner_type'])}
          >
            <option value="short_range">Short Range (10k)</option>
            <option value="long_range">Long Range (50k)</option>
            <option value="tactical">Tactical (25k)</option>
            <option value="hyperspace">Hyperspace (100k)</option>
            <option value="cloak_detector">Cloak Detector (15k)</option>
          </ScannerMode>
        </HeaderLeft>
        
        <HeaderControls>
          <ControlButton active={isScanning} onClick={toggleScanning}>
            {isScanning ? <FaPause /> : <FaPlay />}
            {isScanning ? 'Scanning' : 'Paused'}
          </ControlButton>
          <ControlButton onClick={toggleFullscreen}>
            {isFullscreen ? <FaCompress /> : <FaExpand />}
          </ControlButton>
        </HeaderControls>
      </TacticalHeader>
      
      <TacticalContent>
        <RadarDisplay ref={radarRef}>
          {renderRadarGrid()}
          <RadarSweep active={isScanning} />
          
          {filteredObjects.map(obj => (
            <TacticalObject
              key={obj.id}
              x={obj.x}
              y={obj.y}
              threat={obj.threat_level}
              selected={selectedObject?.id === obj.id}
              onClick={() => handleObjectClick(obj)}
              title={`${obj.name} - ${obj.distance}m`}
            />
          ))}
        </RadarDisplay>
        
        <InfoPanel>
          <InfoHeader>
            <InfoTitle>
              {selectedObject ? selectedObject.name : 'Scanner Status'}
            </InfoTitle>
            <InfoSubtitle>
              {selectedObject 
                ? `${selectedObject.type.charAt(0).toUpperCase() + selectedObject.type.slice(1)} - ${selectedObject.distance}m`
                : `${scannerMode.replace('_', ' ').toUpperCase()} - ${filteredObjects.length} objects detected`
              }
            </InfoSubtitle>
          </InfoHeader>
          
          <InfoContent>
            {selectedObject ? (
              <>
                <InfoSection>
                  <InfoSectionTitle>
                    <FaEye />
                    Object Details
                  </InfoSectionTitle>
                  <InfoItem>
                    <InfoLabel>Distance:</InfoLabel>
                    <InfoValue>{selectedObject.distance.toLocaleString()}m</InfoValue>
                  </InfoItem>
                  <InfoItem>
                    <InfoLabel>Bearing:</InfoLabel>
                    <InfoValue>{selectedObject.bearing}°</InfoValue>
                  </InfoItem>
                  <InfoItem>
                    <InfoLabel>Owner:</InfoLabel>
                    <InfoValue>{selectedObject.owner || 'Unknown'}</InfoValue>
                  </InfoItem>
                  {selectedObject.team && (
                    <InfoItem>
                      <InfoLabel>Team:</InfoLabel>
                      <InfoValue highlight>{selectedObject.team}</InfoValue>
                    </InfoItem>
                  )}
                  <InfoItem>
                    <InfoLabel>Status:</InfoLabel>
                    <InfoValue>{selectedObject.status || 'Unknown'}</InfoValue>
                  </InfoItem>
                </InfoSection>
                
                <InfoSection>
                  <InfoSectionTitle>
                    <FaExclamationTriangle />
                    Threat Assessment
                  </InfoSectionTitle>
                  <ThreatIndicator level={selectedObject.threat_level}>
                    <FaCircle size={8} />
                    {selectedObject.threat_level.toUpperCase()}
                  </ThreatIndicator>
                </InfoSection>
              </>
            ) : (
              <>
                <InfoSection>
                  <InfoSectionTitle>
                    <FaCog />
                    Scanner Configuration
                  </InfoSectionTitle>
                  <InfoItem>
                    <InfoLabel>Range:</InfoLabel>
                    <InfoValue>{scannerData.range.toLocaleString()}m</InfoValue>
                  </InfoItem>
                  <InfoItem>
                    <InfoLabel>Accuracy:</InfoLabel>
                    <InfoValue>{(scannerData.accuracy * 100).toFixed(1)}%</InfoValue>
                  </InfoItem>
                  <InfoItem>
                    <InfoLabel>Last Update:</InfoLabel>
                    <InfoValue>{new Date(scannerData.timestamp).toLocaleTimeString()}</InfoValue>
                  </InfoItem>
                </InfoSection>
                
                <InfoSection>
                  <InfoSectionTitle>
                    <FaFilter />
                    Object Filters
                  </InfoSectionTitle>
                  {Object.entries(filters).map(([type, enabled]) => (
                    <InfoItem key={type}>
                      <InfoLabel>{type.charAt(0).toUpperCase() + type.slice(1)}:</InfoLabel>
                      <ControlButton
                        active={enabled}
                        onClick={() => setFilters(prev => ({ ...prev, [type]: !enabled }))}
                        style={{ padding: '4px 8px', fontSize: '11px' }}
                      >
                        {enabled ? 'ON' : 'OFF'}
                      </ControlButton>
                    </InfoItem>
                  ))}
                </InfoSection>
                
                <InfoSection>
                  <InfoSectionTitle>
                    <FaDotCircle />
                    Detected Objects
                  </InfoSectionTitle>
                  {filteredObjects.length === 0 ? (
                    <InfoValue style={{ color: '#888', fontSize: '12px' }}>
                      No objects in range
                    </InfoValue>
                  ) : (
                    filteredObjects.map(obj => (
                      <InfoItem 
                        key={obj.id}
                        style={{ cursor: 'pointer' }}
                        onClick={() => handleObjectClick(obj)}
                      >
                        <InfoLabel>{obj.name}</InfoLabel>
                        <ThreatIndicator level={obj.threat_level}>
                          <FaCircle size={6} />
                          {obj.distance}m
                        </ThreatIndicator>
                      </InfoItem>
                    ))
                  )}
                </InfoSection>
              </>
            )}
          </InfoContent>
        </InfoPanel>
      </TacticalContent>
    </TacticalContainer>
  );
};

export default TacticalDisplay;
