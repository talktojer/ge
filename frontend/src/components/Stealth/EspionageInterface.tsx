import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { useAppSelector, useAppDispatch } from '../../hooks/redux';
import { 
  FaUserSecret, 
  FaBomb, 
  FaEyeSlash,
  FaSearch,
  FaMapMarkerAlt,
  FaClock,
  FaExclamationTriangle,
  FaCheckCircle,
  FaPlay,
  FaStop,
  FaTrash,
  FaPlus,
  FaEye,
  FaShieldAlt,
  FaCrosshairs,
  FaRocket,
  FaBolt,
  FaSkull,
  FaHeart,
  FaStar,
  FaFlag,
  FaInfoCircle
} from 'react-icons/fa';

// Stealth & Espionage Types
interface SpyAgent {
  id: string;
  name: string;
  location: { x: number; y: number; planet?: string };
  status: 'active' | 'captured' | 'missing' | 'returning' | 'deployed';
  mission_type: 'reconnaissance' | 'sabotage' | 'infiltration' | 'counter_intelligence';
  skill_level: number; // 1-10
  experience: number;
  detection_risk: number; // 0-100%
  mission_progress: number; // 0-100%
  intel_gathered: IntelligenceReport[];
  deployment_date: string;
  last_contact: string;
  cover_identity: string;
  equipment: string[];
}

interface IntelligenceReport {
  id: string;
  type: 'military' | 'economic' | 'political' | 'technological';
  subject: string;
  reliability: number; // 0-100%
  importance: 'low' | 'medium' | 'high' | 'critical';
  content: string;
  timestamp: string;
  location: { x: number; y: number };
}

interface MineField {
  id: string;
  name: string;
  location: { x: number; y: number };
  mine_type: 'standard' | 'proximity' | 'magnetic' | 'thermal' | 'gravimetric' | 'quantum';
  mine_count: number;
  pattern: 'grid' | 'circular' | 'random' | 'corridor';
  activation_radius: number;
  damage_potential: number;
  detection_difficulty: number;
  deployment_date: string;
  status: 'active' | 'triggered' | 'disarmed' | 'expired';
  owner: string;
  stealth_level: number;
}

interface StealthSystem {
  id: string;
  name: string;
  type: 'cloaking_device' | 'sensor_dampener' | 'signature_masker' | 'holographic_disguise';
  effectiveness: number; // 0-100%
  energy_consumption: number;
  duration: number; // seconds
  cooldown: number; // seconds
  status: 'active' | 'charging' | 'offline' | 'damaged';
  detection_methods: string[];
}

const EspionageContainer = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  height: 100%;
  min-height: 700px;
`;

const EspionagePanel = styled.div`
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
`;

const PanelHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #1a1a1a;
  border-bottom: 1px solid #333;
`;

const PanelTitle = styled.h3`
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const PanelControls = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ControlButton = styled.button<{ active?: boolean; variant?: 'primary' | 'danger' | 'warning' }>`
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 4px;
  
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
    } else if (props.variant === 'warning') {
      return `
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        color: #000;
        &:hover { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
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
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const PanelContent = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 16px;
`;

const TabContainer = styled.div`
  display: flex;
  border-bottom: 1px solid #333;
  margin-bottom: 16px;
`;

const Tab = styled.button<{ active: boolean }>`
  flex: 1;
  padding: 12px;
  background: ${props => props.active ? '#333' : 'transparent'};
  border: none;
  border-bottom: 2px solid ${props => props.active ? '#4ade80' : 'transparent'};
  color: ${props => props.active ? '#fff' : '#888'};
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  
  &:hover {
    color: #fff;
    background: rgba(255, 255, 255, 0.05);
  }
`;

const ItemList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const ItemCard = styled.div<{ status?: string; selected?: boolean }>`
  padding: 12px;
  background: ${props => props.selected ? '#333' : '#1a1a1a'};
  border: 1px solid ${props => {
    if (props.selected) return '#4ade80';
    switch (props.status) {
      case 'active': return '#22c55e';
      case 'captured': case 'triggered': return '#ef4444';
      case 'missing': case 'expired': return '#6b7280';
      case 'returning': case 'charging': return '#eab308';
      default: return '#333';
    }
  }};
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: #222;
    border-color: #555;
  }
`;

const ItemHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
`;

const ItemName = styled.h5`
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const StatusBadge = styled.div<{ status: string }>`
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  background: ${props => {
    switch (props.status) {
      case 'active': return 'rgba(34, 197, 94, 0.2)';
      case 'captured': case 'triggered': return 'rgba(239, 68, 68, 0.2)';
      case 'missing': case 'expired': return 'rgba(107, 114, 128, 0.2)';
      case 'returning': case 'charging': return 'rgba(234, 179, 8, 0.2)';
      default: return 'rgba(107, 114, 128, 0.2)';
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'active': return '#22c55e';
      case 'captured': case 'triggered': return '#ef4444';
      case 'missing': case 'expired': return '#6b7280';
      case 'returning': case 'charging': return '#eab308';
      default: return '#6b7280';
    }
  }};
`;

const ItemDetails = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  font-size: 11px;
  color: #888;
`;

const DetailItem = styled.div`
  display: flex;
  justify-content: space-between;
`;

const DetailValue = styled.span`
  color: #fff;
  font-weight: 500;
`;

const ProgressBar = styled.div`
  height: 4px;
  background: #333;
  border-radius: 2px;
  overflow: hidden;
  margin: 8px 0;
`;

const ProgressFill = styled.div<{ percentage: number; color: string }>`
  height: 100%;
  width: ${props => props.percentage}%;
  background: ${props => props.color};
  transition: width 0.3s ease;
`;

const DeploymentForm = styled.div`
  padding: 16px;
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 8px;
  margin-top: 16px;
`;

const FormTitle = styled.h5`
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const FormGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
`;

const FormLabel = styled.label`
  color: #888;
  font-size: 11px;
  font-weight: 500;
`;

const FormInput = styled.input`
  padding: 6px 8px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #fff;
  font-size: 11px;
  
  &:focus {
    outline: none;
    border-color: #4ade80;
  }
`;

const FormSelect = styled.select`
  padding: 6px 8px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #fff;
  font-size: 11px;
  
  &:focus {
    outline: none;
    border-color: #4ade80;
  }
`;

const IntelReport = styled.div<{ importance: 'low' | 'medium' | 'high' | 'critical' }>`
  padding: 12px;
  background: #1a1a1a;
  border-left: 4px solid ${props => {
    switch (props.importance) {
      case 'critical': return '#ef4444';
      case 'high': return '#f97316';
      case 'medium': return '#eab308';
      default: return '#22c55e';
    }
  }};
  border-radius: 0 8px 8px 0;
  margin-bottom: 8px;
`;

const ReportHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
`;

const ReportSubject = styled.h6`
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  margin: 0;
`;

const ReportMeta = styled.div`
  font-size: 10px;
  color: #888;
`;

const ReportContent = styled.p`
  color: #ccc;
  font-size: 11px;
  margin: 0;
  line-height: 1.4;
`;

const EspionageInterface: React.FC<{ shipId: number }> = ({ shipId }) => {
  const dispatch = useAppDispatch();
  const [activeTab, setActiveTab] = useState<'spies' | 'mines' | 'stealth'>('spies');
  const [selectedSpy, setSelectedSpy] = useState<SpyAgent | null>(null);
  const [selectedMineField, setSelectedMineField] = useState<MineField | null>(null);
  const [deploymentMode, setDeploymentMode] = useState<'spy' | 'mine' | null>(null);
  
  // Mock spy data
  const [spies, setSpies] = useState<SpyAgent[]>([
    {
      id: 'spy_001',
      name: 'Agent Shadow',
      location: { x: 15, y: 8, planet: 'Earth' },
      status: 'active',
      mission_type: 'reconnaissance',
      skill_level: 8,
      experience: 157,
      detection_risk: 25,
      mission_progress: 67,
      intel_gathered: [
        {
          id: 'intel_001',
          type: 'military',
          subject: 'Fleet Movements',
          reliability: 85,
          importance: 'high',
          content: 'Enemy fleet of 12 ships detected moving towards Sector 20,10',
          timestamp: new Date().toISOString(),
          location: { x: 15, y: 8 }
        }
      ],
      deployment_date: '2024-12-15',
      last_contact: '2024-12-20',
      cover_identity: 'Merchant Trader',
      equipment: ['Stealth Suit', 'Data Recorder', 'Communication Device']
    },
    {
      id: 'spy_002',
      name: 'Agent Phantom',
      location: { x: 25, y: 12, planet: 'Mars' },
      status: 'captured',
      mission_type: 'sabotage',
      skill_level: 6,
      experience: 89,
      detection_risk: 95,
      mission_progress: 30,
      intel_gathered: [],
      deployment_date: '2024-12-18',
      last_contact: '2024-12-19',
      cover_identity: 'Research Scientist',
      equipment: ['Explosive Device', 'Hacking Tool']
    }
  ]);

  // Mock mine field data
  const [mineFields, setMineFields] = useState<MineField[]>([
    {
      id: 'mine_001',
      name: 'Asteroid Belt Alpha',
      location: { x: 10, y: 5 },
      mine_type: 'proximity',
      mine_count: 25,
      pattern: 'grid',
      activation_radius: 1000,
      damage_potential: 500,
      detection_difficulty: 70,
      deployment_date: '2024-12-10',
      status: 'active',
      owner: 'Federation',
      stealth_level: 85
    },
    {
      id: 'mine_002',
      name: 'Trade Route Gamma',
      location: { x: 18, y: 14 },
      mine_type: 'magnetic',
      mine_count: 15,
      pattern: 'circular',
      activation_radius: 1500,
      damage_potential: 750,
      detection_difficulty: 85,
      deployment_date: '2024-12-12',
      status: 'triggered',
      owner: 'Federation',
      stealth_level: 60
    }
  ]);

  // Mock stealth systems
  const [stealthSystems, setStealthSystems] = useState<StealthSystem[]>([
    {
      id: 'stealth_001',
      name: 'Quantum Cloaking Device',
      type: 'cloaking_device',
      effectiveness: 90,
      energy_consumption: 25,
      duration: 300,
      cooldown: 120,
      status: 'active',
      detection_methods: ['Tachyon Scan', 'Gravimetric Sensor']
    },
    {
      id: 'stealth_002',
      name: 'Sensor Dampening Field',
      type: 'sensor_dampener',
      effectiveness: 75,
      energy_consumption: 15,
      duration: 600,
      cooldown: 60,
      status: 'charging',
      detection_methods: ['Enhanced Scanner']
    }
  ]);

  const handleDeploySpy = (formData: any) => {
    const newSpy: SpyAgent = {
      id: `spy_${Date.now()}`,
      name: formData.name,
      location: { x: parseInt(formData.x), y: parseInt(formData.y), planet: formData.planet },
      status: 'deployed',
      mission_type: formData.mission_type,
      skill_level: parseInt(formData.skill_level),
      experience: 0,
      detection_risk: 10,
      mission_progress: 0,
      intel_gathered: [],
      deployment_date: new Date().toISOString(),
      last_contact: new Date().toISOString(),
      cover_identity: formData.cover_identity,
      equipment: formData.equipment.split(',').map((e: string) => e.trim())
    };
    setSpies(prev => [...prev, newSpy]);
    setDeploymentMode(null);
  };

  const handleDeployMines = (formData: any) => {
    const newMineField: MineField = {
      id: `mine_${Date.now()}`,
      name: formData.name,
      location: { x: parseInt(formData.x), y: parseInt(formData.y) },
      mine_type: formData.mine_type,
      mine_count: parseInt(formData.mine_count),
      pattern: formData.pattern,
      activation_radius: parseInt(formData.activation_radius),
      damage_potential: parseInt(formData.damage_potential),
      detection_difficulty: parseInt(formData.detection_difficulty),
      deployment_date: new Date().toISOString(),
      status: 'active',
      owner: 'Player',
      stealth_level: parseInt(formData.stealth_level)
    };
    setMineFields(prev => [...prev, newMineField]);
    setDeploymentMode(null);
  };

  const handleRecallSpy = (spyId: string) => {
    setSpies(prev => prev.map(spy => 
      spy.id === spyId ? { ...spy, status: 'returning' } : spy
    ));
  };

  const handleActivateStealth = (systemId: string) => {
    setStealthSystems(prev => prev.map(system => 
      system.id === systemId ? { ...system, status: 'active' } : system
    ));
  };

  const renderSpyContent = () => (
    <>
      <TabContainer>
        <Tab active={!deploymentMode} onClick={() => setDeploymentMode(null)}>
          <FaEye />
          Active Agents
        </Tab>
        <Tab active={deploymentMode === 'spy'} onClick={() => setDeploymentMode('spy')}>
          <FaPlus />
          Deploy Spy
        </Tab>
      </TabContainer>

      {deploymentMode === 'spy' ? (
        <DeploymentForm>
          <FormTitle>
            <FaUserSecret />
            Deploy New Agent
          </FormTitle>
          <FormGrid>
            <FormGroup>
              <FormLabel>Agent Name:</FormLabel>
              <FormInput type="text" placeholder="Enter agent name" />
            </FormGroup>
            <FormGroup>
              <FormLabel>Mission Type:</FormLabel>
              <FormSelect>
                <option value="reconnaissance">Reconnaissance</option>
                <option value="sabotage">Sabotage</option>
                <option value="infiltration">Infiltration</option>
                <option value="counter_intelligence">Counter Intelligence</option>
              </FormSelect>
            </FormGroup>
            <FormGroup>
              <FormLabel>Target X:</FormLabel>
              <FormInput type="number" min="0" max="29" />
            </FormGroup>
            <FormGroup>
              <FormLabel>Target Y:</FormLabel>
              <FormInput type="number" min="0" max="14" />
            </FormGroup>
            <FormGroup>
              <FormLabel>Planet/Station:</FormLabel>
              <FormInput type="text" placeholder="Target location" />
            </FormGroup>
            <FormGroup>
              <FormLabel>Cover Identity:</FormLabel>
              <FormInput type="text" placeholder="False identity" />
            </FormGroup>
          </FormGrid>
          <ControlButton variant="primary" style={{ width: '100%' }}>
            <FaPlay />
            Deploy Agent
          </ControlButton>
        </DeploymentForm>
      ) : (
        <ItemList>
          {spies.map(spy => (
            <ItemCard
              key={spy.id}
              status={spy.status}
              selected={selectedSpy?.id === spy.id}
              onClick={() => setSelectedSpy(spy)}
            >
              <ItemHeader>
                <ItemName>
                  <FaUserSecret />
                  {spy.name}
                </ItemName>
                <StatusBadge status={spy.status}>
                  {spy.status.toUpperCase()}
                </StatusBadge>
              </ItemHeader>
              
              <ItemDetails>
                <DetailItem>
                  <span>Location:</span>
                  <DetailValue>({spy.location.x},{spy.location.y})</DetailValue>
                </DetailItem>
                <DetailItem>
                  <span>Mission:</span>
                  <DetailValue>{spy.mission_type}</DetailValue>
                </DetailItem>
                <DetailItem>
                  <span>Skill Level:</span>
                  <DetailValue>{spy.skill_level}/10</DetailValue>
                </DetailItem>
                <DetailItem>
                  <span>Detection Risk:</span>
                  <DetailValue style={{ color: spy.detection_risk > 70 ? '#ef4444' : spy.detection_risk > 40 ? '#eab308' : '#22c55e' }}>
                    {spy.detection_risk}%
                  </DetailValue>
                </DetailItem>
              </ItemDetails>
              
              <ProgressBar>
                <ProgressFill 
                  percentage={spy.mission_progress} 
                  color="#4ade80"
                />
              </ProgressBar>
              
              <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                <ControlButton 
                  onClick={(e) => { e.stopPropagation(); handleRecallSpy(spy.id); }}
                  disabled={spy.status !== 'active'}
                >
                  <FaStop />
                  Recall
                </ControlButton>
                <ControlButton>
                  <FaEye />
                  Intel ({spy.intel_gathered.length})
                </ControlButton>
              </div>
            </ItemCard>
          ))}
        </ItemList>
      )}
    </>
  );

  const renderMineContent = () => (
    <>
      <TabContainer>
        <Tab active={!deploymentMode} onClick={() => setDeploymentMode(null)}>
          <FaBomb />
          Mine Fields
        </Tab>
        <Tab active={deploymentMode === 'mine'} onClick={() => setDeploymentMode('mine')}>
          <FaPlus />
          Deploy Mines
        </Tab>
      </TabContainer>

      {deploymentMode === 'mine' ? (
        <DeploymentForm>
          <FormTitle>
            <FaBomb />
            Deploy Mine Field
          </FormTitle>
          <FormGrid>
            <FormGroup>
              <FormLabel>Field Name:</FormLabel>
              <FormInput type="text" placeholder="Enter field name" />
            </FormGroup>
            <FormGroup>
              <FormLabel>Mine Type:</FormLabel>
              <FormSelect>
                <option value="standard">Standard</option>
                <option value="proximity">Proximity</option>
                <option value="magnetic">Magnetic</option>
                <option value="thermal">Thermal</option>
                <option value="gravimetric">Gravimetric</option>
                <option value="quantum">Quantum</option>
              </FormSelect>
            </FormGroup>
            <FormGroup>
              <FormLabel>Location X:</FormLabel>
              <FormInput type="number" min="0" max="29" />
            </FormGroup>
            <FormGroup>
              <FormLabel>Location Y:</FormLabel>
              <FormInput type="number" min="0" max="14" />
            </FormGroup>
            <FormGroup>
              <FormLabel>Mine Count:</FormLabel>
              <FormInput type="number" min="1" max="50" />
            </FormGroup>
            <FormGroup>
              <FormLabel>Pattern:</FormLabel>
              <FormSelect>
                <option value="grid">Grid</option>
                <option value="circular">Circular</option>
                <option value="random">Random</option>
                <option value="corridor">Corridor</option>
              </FormSelect>
            </FormGroup>
          </FormGrid>
          <ControlButton variant="primary" style={{ width: '100%' }}>
            <FaPlay />
            Deploy Mines
          </ControlButton>
        </DeploymentForm>
      ) : (
        <ItemList>
          {mineFields.map(field => (
            <ItemCard
              key={field.id}
              status={field.status}
              selected={selectedMineField?.id === field.id}
              onClick={() => setSelectedMineField(field)}
            >
              <ItemHeader>
                <ItemName>
                  <FaBomb />
                  {field.name}
                </ItemName>
                <StatusBadge status={field.status}>
                  {field.status.toUpperCase()}
                </StatusBadge>
              </ItemHeader>
              
              <ItemDetails>
                <DetailItem>
                  <span>Location:</span>
                  <DetailValue>({field.location.x},{field.location.y})</DetailValue>
                </DetailItem>
                <DetailItem>
                  <span>Type:</span>
                  <DetailValue>{field.mine_type}</DetailValue>
                </DetailItem>
                <DetailItem>
                  <span>Count:</span>
                  <DetailValue>{field.mine_count}</DetailValue>
                </DetailItem>
                <DetailItem>
                  <span>Stealth:</span>
                  <DetailValue>{field.stealth_level}%</DetailValue>
                </DetailItem>
              </ItemDetails>
              
              <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                <ControlButton variant="danger">
                  <FaTrash />
                  Disarm
                </ControlButton>
                <ControlButton>
                  <FaInfoCircle />
                  Details
                </ControlButton>
              </div>
            </ItemCard>
          ))}
        </ItemList>
      )}
    </>
  );

  const renderStealthContent = () => (
    <ItemList>
      {stealthSystems.map(system => (
        <ItemCard
          key={system.id}
          status={system.status}
        >
          <ItemHeader>
            <ItemName>
              <FaEyeSlash />
              {system.name}
            </ItemName>
            <StatusBadge status={system.status}>
              {system.status.toUpperCase()}
            </StatusBadge>
          </ItemHeader>
          
          <ItemDetails>
            <DetailItem>
              <span>Effectiveness:</span>
              <DetailValue>{system.effectiveness}%</DetailValue>
            </DetailItem>
            <DetailItem>
              <span>Energy/sec:</span>
              <DetailValue>{system.energy_consumption}</DetailValue>
            </DetailItem>
            <DetailItem>
              <span>Duration:</span>
              <DetailValue>{system.duration}s</DetailValue>
            </DetailItem>
            <DetailItem>
              <span>Cooldown:</span>
              <DetailValue>{system.cooldown}s</DetailValue>
            </DetailItem>
          </ItemDetails>
          
          <ProgressBar>
            <ProgressFill 
              percentage={system.status === 'active' ? 100 : system.status === 'charging' ? 45 : 0} 
              color={system.status === 'active' ? '#22c55e' : system.status === 'charging' ? '#eab308' : '#6b7280'}
            />
          </ProgressBar>
          
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <ControlButton 
              variant={system.status === 'active' ? 'danger' : 'primary'}
              onClick={() => handleActivateStealth(system.id)}
              disabled={system.status === 'charging' || system.status === 'damaged'}
            >
              {system.status === 'active' ? <FaStop /> : <FaPlay />}
              {system.status === 'active' ? 'Deactivate' : 'Activate'}
            </ControlButton>
          </div>
        </ItemCard>
      ))}
    </ItemList>
  );

  return (
    <EspionageContainer>
      <EspionagePanel>
        <PanelHeader>
          <PanelTitle>
            <FaUserSecret />
            Espionage Operations
          </PanelTitle>
          <PanelControls>
            <ControlButton 
              active={activeTab === 'spies'} 
              onClick={() => setActiveTab('spies')}
            >
              <FaUserSecret />
              Spies
            </ControlButton>
            <ControlButton 
              active={activeTab === 'mines'} 
              onClick={() => setActiveTab('mines')}
            >
              <FaBomb />
              Mines
            </ControlButton>
            <ControlButton 
              active={activeTab === 'stealth'} 
              onClick={() => setActiveTab('stealth')}
            >
              <FaEyeSlash />
              Stealth
            </ControlButton>
          </PanelControls>
        </PanelHeader>
        
        <PanelContent>
          {activeTab === 'spies' && renderSpyContent()}
          {activeTab === 'mines' && renderMineContent()}
          {activeTab === 'stealth' && renderStealthContent()}
        </PanelContent>
      </EspionagePanel>

      <EspionagePanel>
        <PanelHeader>
          <PanelTitle>
            <FaSearch />
            Intelligence Reports
          </PanelTitle>
        </PanelHeader>
        
        <PanelContent>
          {selectedSpy?.intel_gathered.map(report => (
            <IntelReport key={report.id} importance={report.importance}>
              <ReportHeader>
                <ReportSubject>{report.subject}</ReportSubject>
                <ReportMeta>
                  {report.reliability}% reliable | {new Date(report.timestamp).toLocaleDateString()}
                </ReportMeta>
              </ReportHeader>
              <ReportContent>{report.content}</ReportContent>
            </IntelReport>
          )) || (
            <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>
              <FaSearch style={{ fontSize: '32px', marginBottom: '12px', opacity: 0.5 }} />
              <p>No intelligence reports available</p>
              <p style={{ fontSize: '12px' }}>Select an active spy to view their gathered intelligence</p>
            </div>
          )}
        </PanelContent>
      </EspionagePanel>
    </EspionageContainer>
  );
};

export default EspionageInterface;
