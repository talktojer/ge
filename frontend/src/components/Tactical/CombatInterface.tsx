import React, { useEffect, useState, useCallback } from 'react';
import styled from 'styled-components';
import { useAppSelector, useAppDispatch } from '../../hooks/redux';
import { 
  FaCrosshairs, 
  FaBolt, 
  FaRocket, 
  FaShieldAlt,
  FaExclamationTriangle,
  FaFire,
  FaLock,
  FaUnlock,
  FaPlay,
  FaPause,
  FaForward,
  FaBackward,
  FaEye
} from 'react-icons/fa';

// Combat Interface Types
interface WeaponSystem {
  id: string;
  name: string;
  type: 'phaser' | 'torpedo' | 'missile' | 'ion_cannon' | 'hyper_phaser';
  damage_min: number;
  damage_max: number;
  range: number;
  energy_cost: number;
  reload_time: number;
  accuracy: number;
  current_charge: number;
  max_charge: number;
  status: 'ready' | 'charging' | 'cooling' | 'damaged' | 'offline';
  locked_target?: string;
}

interface CombatTarget {
  id: string;
  name: string;
  type: 'ship' | 'planet' | 'station';
  distance: number;
  bearing: number;
  hull_percentage: number;
  shields_percentage: number;
  threat_level: 'low' | 'medium' | 'high' | 'critical';
  lock_strength: number;
  is_hostile: boolean;
  team?: string;
}

interface BattleEvent {
  id: string;
  timestamp: string;
  type: 'weapon_fire' | 'hit' | 'miss' | 'shield_hit' | 'hull_damage' | 'target_lock' | 'target_lost';
  source: string;
  target: string;
  weapon?: string;
  damage?: number;
  message: string;
}

const CombatContainer = styled.div`
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 20px;
  height: 100%;
  min-height: 600px;
`;

const CombatDisplay = styled.div`
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
`;

const CombatHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #1a1a1a;
  border-bottom: 1px solid #333;
`;

const CombatTitle = styled.h3`
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const CombatStatus = styled.div<{ status: 'peaceful' | 'alert' | 'combat' }>`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
  background: ${props => {
    switch (props.status) {
      case 'combat': return 'rgba(239, 68, 68, 0.2)';
      case 'alert': return 'rgba(234, 179, 8, 0.2)';
      default: return 'rgba(34, 197, 94, 0.2)';
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'combat': return '#ef4444';
      case 'alert': return '#eab308';
      default: return '#22c55e';
    }
  }};
`;

const CombatVisualization = styled.div`
  flex: 1;
  position: relative;
  background: radial-gradient(circle at center, #1a0000 0%, #0a0a0a 100%);
  overflow: hidden;
`;

const TargetGrid = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(239, 68, 68, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(239, 68, 68, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
`;

const CombatTarget = styled.div<{ 
  x: number; 
  y: number; 
  selected?: boolean;
  threat: string;
  locked?: boolean;
}>`
  position: absolute;
  left: ${props => props.x}%;
  top: ${props => props.y}%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  border: 2px solid ${props => {
    if (props.locked) return '#4ade80';
    switch (props.threat) {
      case 'critical': return '#ef4444';
      case 'high': return '#f97316';
      case 'medium': return '#eab308';
      default: return '#6b7280';
    }
  }};
  border-radius: 50%;
  background: ${props => props.selected ? 'rgba(255, 255, 255, 0.2)' : 'transparent'};
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  
  &:hover {
    transform: translate(-50%, -50%) scale(1.1);
    background: rgba(255, 255, 255, 0.1);
  }
  
  ${props => props.locked && `
    animation: target-lock 1s ease-in-out infinite;
    box-shadow: 0 0 20px rgba(74, 222, 128, 0.5);
  `}
  
  @keyframes target-lock {
    0%, 100% { border-width: 2px; }
    50% { border-width: 4px; }
  }
`;

const WeaponTrail = styled.div<{ 
  startX: number; 
  startY: number; 
  endX: number; 
  endY: number;
  weaponType: string;
}>`
  position: absolute;
  left: ${props => props.startX}%;
  top: ${props => props.startY}%;
  width: ${props => Math.sqrt(Math.pow(props.endX - props.startX, 2) + Math.pow(props.endY - props.startY, 2))}%;
  height: 2px;
  background: ${props => {
    switch (props.weaponType) {
      case 'phaser': return 'linear-gradient(90deg, #ef4444, transparent)';
      case 'torpedo': return 'linear-gradient(90deg, #22c55e, transparent)';
      case 'missile': return 'linear-gradient(90deg, #f97316, transparent)';
      default: return 'linear-gradient(90deg, #60a5fa, transparent)';
    }
  }};
  transform-origin: left center;
  transform: rotate(${props => Math.atan2(props.endY - props.startY, props.endX - props.startX) * 180 / Math.PI}deg);
  animation: weapon-fire 0.5s ease-out forwards;
  
  @keyframes weapon-fire {
    0% { width: 0%; opacity: 1; }
    100% { opacity: 0; }
  }
`;

const WeaponsPanel = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
`;

const WeaponsPanelHeader = styled.div`
  padding: 16px;
  border-bottom: 1px solid #333;
  background: #222;
`;

const WeaponsPanelTitle = styled.h4`
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const WeaponsList = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 16px;
`;

const WeaponItem = styled.div<{ status: string }>`
  padding: 12px;
  margin-bottom: 12px;
  background: #0a0a0a;
  border: 1px solid ${props => {
    switch (props.status) {
      case 'ready': return '#22c55e';
      case 'charging': return '#eab308';
      case 'cooling': return '#60a5fa';
      case 'damaged': return '#ef4444';
      default: return '#333';
    }
  }};
  border-radius: 8px;
  transition: all 0.2s ease;
  
  &:hover {
    background: #111;
  }
`;

const WeaponHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
`;

const WeaponName = styled.h5`
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const WeaponStatus = styled.span<{ status: string }>`
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: ${props => {
    switch (props.status) {
      case 'ready': return 'rgba(34, 197, 94, 0.2)';
      case 'charging': return 'rgba(234, 179, 8, 0.2)';
      case 'cooling': return 'rgba(96, 165, 250, 0.2)';
      case 'damaged': return 'rgba(239, 68, 68, 0.2)';
      default: return 'rgba(107, 114, 128, 0.2)';
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'ready': return '#22c55e';
      case 'charging': return '#eab308';
      case 'cooling': return '#60a5fa';
      case 'damaged': return '#ef4444';
      default: return '#6b7280';
    }
  }};
`;

const WeaponStats = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 11px;
`;

const StatItem = styled.div`
  display: flex;
  justify-content: space-between;
  color: #888;
`;

const StatValue = styled.span`
  color: #fff;
  font-weight: 500;
`;

const ChargeBar = styled.div`
  height: 4px;
  background: #333;
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
`;

const ChargeFill = styled.div<{ percentage: number; color: string }>`
  height: 100%;
  width: ${props => props.percentage}%;
  background: ${props => props.color};
  transition: width 0.3s ease;
`;

const WeaponActions = styled.div`
  display: flex;
  gap: 8px;
`;

const ActionButton = styled.button<{ variant?: 'fire' | 'lock' | 'secondary' }>`
  flex: 1;
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  
  ${props => {
    switch (props.variant) {
      case 'fire':
        return `
          background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
          color: #fff;
          &:hover { background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); }
        `;
      case 'lock':
        return `
          background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
          color: #000;
          &:hover { background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); }
        `;
      default:
        return `
          background: #333;
          color: #fff;
          border: 1px solid #555;
          &:hover { background: #444; }
        `;
    }
  }}
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const BattleLog = styled.div`
  height: 200px;
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 8px;
  margin-top: 16px;
  overflow-y: auto;
  padding: 12px;
`;

const LogEntry = styled.div<{ type: string }>`
  font-size: 11px;
  margin-bottom: 4px;
  padding: 2px 0;
  color: ${props => {
    switch (props.type) {
      case 'weapon_fire': return '#60a5fa';
      case 'hit': return '#ef4444';
      case 'miss': return '#6b7280';
      case 'shield_hit': return '#22c55e';
      case 'target_lock': return '#eab308';
      default: return '#fff';
    }
  }};
`;

const CombatInterface: React.FC<{ shipId: number }> = ({ shipId }) => {
  const dispatch = useAppDispatch();
  const [combatStatus, setCombatStatus] = useState<'peaceful' | 'alert' | 'combat'>('peaceful');
  const [selectedTarget, setSelectedTarget] = useState<CombatTarget | null>(null);
  const [weaponTrails, setWeaponTrails] = useState<any[]>([]);
  const [battleLog, setBattleLog] = useState<BattleEvent[]>([]);
  
  // Mock weapon systems
  const [weaponSystems, setWeaponSystems] = useState<WeaponSystem[]>([
    {
      id: 'phaser_1',
      name: 'Forward Phasers',
      type: 'phaser',
      damage_min: 50,
      damage_max: 150,
      range: 25000,
      energy_cost: 75,
      reload_time: 2,
      accuracy: 85,
      current_charge: 100,
      max_charge: 100,
      status: 'ready'
    },
    {
      id: 'torpedo_1',
      name: 'Photon Torpedoes',
      type: 'torpedo',
      damage_min: 200,
      damage_max: 400,
      range: 50000,
      energy_cost: 150,
      reload_time: 5,
      accuracy: 70,
      current_charge: 80,
      max_charge: 100,
      status: 'charging'
    },
    {
      id: 'missile_1',
      name: 'Guided Missiles',
      type: 'missile',
      damage_min: 100,
      damage_max: 250,
      range: 40000,
      energy_cost: 100,
      reload_time: 3,
      accuracy: 90,
      current_charge: 100,
      max_charge: 100,
      status: 'ready'
    }
  ]);
  
  // Mock combat targets
  const [combatTargets, setCombatTargets] = useState<CombatTarget[]>([
    {
      id: 'enemy_1',
      name: 'Klingon Warbird',
      type: 'ship',
      distance: 15000,
      bearing: 45,
      hull_percentage: 75,
      shields_percentage: 60,
      threat_level: 'high',
      lock_strength: 0,
      is_hostile: true,
      team: 'Red Team'
    },
    {
      id: 'enemy_2',
      name: 'Romulan Cruiser',
      type: 'ship',
      distance: 25000,
      bearing: 120,
      hull_percentage: 90,
      shields_percentage: 85,
      threat_level: 'medium',
      lock_strength: 0,
      is_hostile: true,
      team: 'Red Team'
    }
  ]);

  const handleTargetSelect = (target: CombatTarget) => {
    setSelectedTarget(target);
    setCombatStatus('alert');
  };

  const handleWeaponFire = useCallback((weapon: WeaponSystem) => {
    if (!selectedTarget || weapon.status !== 'ready') return;
    
    // Create weapon trail animation
    const trail = {
      id: Date.now().toString(),
      startX: 50,
      startY: 50,
      endX: Math.random() * 100,
      endY: Math.random() * 100,
      weaponType: weapon.type
    };
    
    setWeaponTrails(prev => [...prev, trail]);
    
    // Remove trail after animation
    setTimeout(() => {
      setWeaponTrails(prev => prev.filter(t => t.id !== trail.id));
    }, 500);
    
    // Update weapon status
    setWeaponSystems(prev => prev.map(w => 
      w.id === weapon.id 
        ? { ...w, status: 'cooling', current_charge: 0 }
        : w
    ));
    
    // Add battle log entry
    const logEntry: BattleEvent = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      type: 'weapon_fire',
      source: 'USS Enterprise',
      target: selectedTarget.name,
      weapon: weapon.name,
      message: `${weapon.name} fired at ${selectedTarget.name}`
    };
    
    setBattleLog(prev => [logEntry, ...prev].slice(0, 50));
    setCombatStatus('combat');
    
    // Simulate weapon recharge
    setTimeout(() => {
      setWeaponSystems(prev => prev.map(w => 
        w.id === weapon.id 
          ? { ...w, status: 'ready', current_charge: 100 }
          : w
      ));
    }, weapon.reload_time * 1000);
  }, [selectedTarget]);

  const handleTargetLock = (weapon: WeaponSystem) => {
    if (!selectedTarget) return;
    
    setWeaponSystems(prev => prev.map(w => 
      w.id === weapon.id 
        ? { ...w, locked_target: selectedTarget.id }
        : w
    ));
    
    setCombatTargets(prev => prev.map(t => 
      t.id === selectedTarget.id 
        ? { ...t, lock_strength: Math.min(t.lock_strength + 25, 100) }
        : t
    ));
  };

  const getWeaponIcon = (type: WeaponSystem['type']) => {
    switch (type) {
      case 'phaser': return <FaBolt />;
      case 'torpedo': return <FaRocket />;
      case 'missile': return <FaCrosshairs />;
      case 'ion_cannon': return <FaFire />;
      default: return <FaCrosshairs />;
    }
  };

  return (
    <CombatContainer>
      <CombatDisplay>
        <CombatHeader>
          <CombatTitle>
            <FaCrosshairs />
            Combat Interface
          </CombatTitle>
          <CombatStatus status={combatStatus}>
            {combatStatus === 'combat' && <FaExclamationTriangle />}
            {combatStatus === 'alert' && <FaEye />}
            {combatStatus === 'peaceful' && <FaShieldAlt />}
            {combatStatus.toUpperCase()}
          </CombatStatus>
        </CombatHeader>
        
        <CombatVisualization>
          <TargetGrid />
          
          {combatTargets.map(target => (
            <CombatTarget
              key={target.id}
              x={30 + Math.random() * 40}
              y={30 + Math.random() * 40}
              selected={selectedTarget?.id === target.id}
              threat={target.threat_level}
              locked={target.lock_strength > 0}
              onClick={() => handleTargetSelect(target)}
              title={`${target.name} - ${target.distance}m`}
            >
              <FaCrosshairs />
            </CombatTarget>
          ))}
          
          {weaponTrails.map(trail => (
            <WeaponTrail
              key={trail.id}
              startX={trail.startX}
              startY={trail.startY}
              endX={trail.endX}
              endY={trail.endY}
              weaponType={trail.weaponType}
            />
          ))}
        </CombatVisualization>
      </CombatDisplay>
      
      <WeaponsPanel>
        <WeaponsPanelHeader>
          <WeaponsPanelTitle>
            <FaBolt />
            Weapons Control
          </WeaponsPanelTitle>
          {selectedTarget && (
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#888' }}>
              Target: <span style={{ color: '#fff' }}>{selectedTarget.name}</span>
            </div>
          )}
        </WeaponsPanelHeader>
        
        <WeaponsList>
          {weaponSystems.map(weapon => (
            <WeaponItem key={weapon.id} status={weapon.status}>
              <WeaponHeader>
                <WeaponName>
                  {getWeaponIcon(weapon.type)}
                  {weapon.name}
                </WeaponName>
                <WeaponStatus status={weapon.status}>
                  {weapon.status.replace('_', ' ').toUpperCase()}
                </WeaponStatus>
              </WeaponHeader>
              
              <WeaponStats>
                <StatItem>
                  <span>Damage:</span>
                  <StatValue>{weapon.damage_min}-{weapon.damage_max}</StatValue>
                </StatItem>
                <StatItem>
                  <span>Range:</span>
                  <StatValue>{(weapon.range / 1000).toFixed(0)}km</StatValue>
                </StatItem>
                <StatItem>
                  <span>Accuracy:</span>
                  <StatValue>{weapon.accuracy}%</StatValue>
                </StatItem>
                <StatItem>
                  <span>Energy:</span>
                  <StatValue>{weapon.energy_cost}</StatValue>
                </StatItem>
              </WeaponStats>
              
              <ChargeBar>
                <ChargeFill 
                  percentage={(weapon.current_charge / weapon.max_charge) * 100}
                  color={weapon.status === 'ready' ? '#22c55e' : weapon.status === 'charging' ? '#eab308' : '#60a5fa'}
                />
              </ChargeBar>
              
              <WeaponActions>
                <ActionButton
                  variant="fire"
                  disabled={weapon.status !== 'ready' || !selectedTarget}
                  onClick={() => handleWeaponFire(weapon)}
                >
                  <FaFire />
                  FIRE
                </ActionButton>
                <ActionButton
                  variant="lock"
                  disabled={!selectedTarget}
                  onClick={() => handleTargetLock(weapon)}
                >
                  {weapon.locked_target ? <FaLock /> : <FaUnlock />}
                  LOCK
                </ActionButton>
              </WeaponActions>
            </WeaponItem>
          ))}
        </WeaponsList>
        
        <BattleLog>
          {battleLog.length === 0 ? (
            <div style={{ color: '#888', textAlign: 'center', paddingTop: '40px' }}>
              No combat activity
            </div>
          ) : (
            battleLog.map(entry => (
              <LogEntry key={entry.id} type={entry.type}>
                [{new Date(entry.timestamp).toLocaleTimeString()}] {entry.message}
              </LogEntry>
            ))
          )}
        </BattleLog>
      </WeaponsPanel>
    </CombatContainer>
  );
};

export default CombatInterface;
