import React, { useState, useCallback } from 'react';
import styled from 'styled-components';
import { ConfigParameter, BalanceMetrics } from '../../types';

const BalanceContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2rem;
`;

const Section = styled.div`
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
`;

const SectionTitle = styled.h3`
  font-size: 1.3rem;
  margin-bottom: 1rem;
  color: #00d4ff;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &::before {
    content: '⚖️';
    font-size: 1.1rem;
  }
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
`;

const MetricCard = styled.div<{ impactLevel: string }>`
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid ${props => {
    switch (props.impactLevel) {
      case 'critical': return 'rgba(255, 71, 87, 0.3)';
      case 'high': return 'rgba(255, 193, 7, 0.3)';
      case 'medium': return 'rgba(52, 152, 219, 0.3)';
      default: return 'rgba(46, 204, 113, 0.3)';
    }
  }};
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
  }
`;

const MetricHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
`;

const MetricName = styled.div`
  font-weight: bold;
  color: #ffffff;
  text-transform: capitalize;
`;

const ImpactBadge = styled.div<{ level: string }>`
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: bold;
  text-transform: uppercase;
  background: ${props => {
    switch (props.level) {
      case 'critical': return 'rgba(255, 71, 87, 0.2)';
      case 'high': return 'rgba(255, 193, 7, 0.2)';
      case 'medium': return 'rgba(52, 152, 219, 0.2)';
      default: return 'rgba(46, 204, 113, 0.2)';
    }
  }};
  color: ${props => {
    switch (props.level) {
      case 'critical': return '#ff4757';
      case 'high': return '#f39c12';
      case 'medium': return '#3498db';
      default: return '#2ecc71';
    }
  }};
`;

const MetricValues = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
`;

const MetricValue = styled.div`
  color: #cccccc;
`;

const MetricCurrent = styled(MetricValue)`
  color: #00d4ff;
  font-weight: bold;
`;

const DeviationBar = styled.div`
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
`;

const DeviationFill = styled.div<{ deviation: number }>`
  height: 100%;
  background: ${props => {
    const absDev = Math.abs(props.deviation);
    if (absDev > 30) return 'linear-gradient(90deg, #ff4757, #c44569)';
    if (absDev > 15) return 'linear-gradient(90deg, #f39c12, #e67e22)';
    if (absDev > 5) return 'linear-gradient(90deg, #3498db, #2980b9)';
    return 'linear-gradient(90deg, #2ecc71, #27ae60)';
  }};
  width: ${props => Math.min(Math.abs(props.deviation), 100)}%;
  transition: all 0.3s ease;
`;

const Recommendation = styled.div`
  font-size: 0.8rem;
  color: #999999;
  line-height: 1.4;
  font-style: italic;
`;

const PresetContainer = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
`;

const PresetButton = styled.button<{ active?: boolean }>`
  padding: 0.75rem 1.5rem;
  border: 1px solid ${props => props.active ? '#00d4ff' : 'rgba(255, 255, 255, 0.2)'};
  border-radius: 6px;
  background: ${props => props.active ? 'rgba(0, 212, 255, 0.1)' : 'rgba(255, 255, 255, 0.05)'};
  color: ${props => props.active ? '#00d4ff' : '#cccccc'};
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: ${props => props.active ? 'bold' : 'normal'};

  &:hover {
    border-color: #00d4ff;
    background: rgba(0, 212, 255, 0.1);
    color: #00d4ff;
  }
`;

const BalancePreset = styled.div`
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
`;

const PresetTitle = styled.div`
  font-weight: bold;
  color: #00d4ff;
  margin-bottom: 0.5rem;
`;

const PresetDescription = styled.div`
  font-size: 0.9rem;
  color: #cccccc;
  line-height: 1.4;
`;

const AdjustmentForm = styled.form`
  display: flex;
  gap: 1rem;
  align-items: end;
  margin-bottom: 1rem;
`;

const FormGroup = styled.div`
  flex: 1;
`;

const FormLabel = styled.label`
  display: block;
  font-size: 0.9rem;
  color: #cccccc;
  margin-bottom: 0.5rem;
  font-weight: 500;
`;

const FormSelect = styled.select`
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

const FormInput = styled.input`
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

const FormTextarea = styled.textarea`
  width: 100%;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: #ffffff;
  font-size: 1rem;
  min-height: 80px;
  resize: vertical;

  &:focus {
    outline: none;
    border-color: #00d4ff;
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
  }
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

interface BalanceControlsProps {
  configurations: Record<string, ConfigParameter>;
  balanceMetrics: BalanceMetrics[];
  onConfigUpdate: (key: string, value: any, reason?: string) => void;
  onBatchUpdate: (updates: Array<{key: string, value: any}>, reason?: string) => void;
  loading: boolean;
}

const BalanceControls: React.FC<BalanceControlsProps> = ({
  configurations,
  balanceMetrics,
  onConfigUpdate,
  onBatchUpdate,
  loading
}) => {
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [customAdjustment, setCustomAdjustment] = useState({
    parameter: '',
    value: '',
    reason: ''
  });

  const balancePresets = [
    {
      id: 'balanced',
      name: 'Balanced',
      description: 'Standard balanced configuration for fair gameplay'
    },
    {
      id: 'aggressive',
      name: 'Aggressive Combat',
      description: 'Higher damage, faster combat, more intense battles'
    },
    {
      id: 'economic',
      name: 'Economic Focus',
      description: 'Enhanced trading and resource management'
    },
    {
      id: 'casual',
      name: 'Casual Play',
      description: 'Reduced difficulty for new players'
    },
    {
      id: 'competitive',
      name: 'Competitive',
      description: 'Optimized for competitive tournament play'
    }
  ];

  const handlePresetApply = useCallback((presetId: string) => {
    // This would apply the specific preset configurations
    // For now, just show a notification
    console.log(`Applying preset: ${presetId}`);
  }, []);

  const handleCustomAdjustment = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (!customAdjustment.parameter || !customAdjustment.value) return;

    const updates = [{
      key: customAdjustment.parameter,
      value: customAdjustment.value
    }];

    onBatchUpdate(updates, customAdjustment.reason);
    
    setCustomAdjustment({
      parameter: '',
      value: '',
      reason: ''
    });
  }, [customAdjustment, onBatchUpdate]);

  const getImpactColor = (level: string) => {
    switch (level) {
      case 'critical': return '#ff4757';
      case 'high': return '#f39c12';
      case 'medium': return '#3498db';
      default: return '#2ecc71';
    }
  };

  return (
    <BalanceContainer>
      <Section>
        <SectionTitle>Balance Analysis</SectionTitle>
        
        {balanceMetrics.length > 0 ? (
          <MetricsGrid>
            {balanceMetrics.map((metric, index) => (
              <MetricCard key={index} impactLevel={metric.impact_level}>
                <MetricHeader>
                  <MetricName>{metric.factor.replace('_', ' ')}</MetricName>
                  <ImpactBadge level={metric.impact_level}>
                    {metric.impact_level}
                  </ImpactBadge>
                </MetricHeader>
                
                <MetricValues>
                  <MetricValue>Current: {metric.current_value.toFixed(2)}</MetricValue>
                  <MetricValue>Target: {metric.target_value.toFixed(2)}</MetricValue>
                </MetricValues>
                
                <DeviationBar>
                  <DeviationFill deviation={metric.deviation_percent} />
                </DeviationBar>
                
                <Recommendation>
                  {metric.recommendation}
                </Recommendation>
              </MetricCard>
            ))}
          </MetricsGrid>
        ) : (
          <div style={{ color: '#999999', textAlign: 'center', padding: '2rem' }}>
            No balance metrics available. Run balance analysis to see current status.
          </div>
        )}
      </Section>

      <Section>
        <SectionTitle>Balance Presets</SectionTitle>
        
        <PresetContainer>
          {balancePresets.map((preset) => (
            <PresetButton
              key={preset.id}
              active={selectedPreset === preset.id}
              onClick={() => {
                setSelectedPreset(preset.id);
                handlePresetApply(preset.id);
              }}
              disabled={loading}
            >
              {preset.name}
            </PresetButton>
          ))}
        </PresetContainer>

        {balancePresets.map((preset) => (
          <BalancePreset key={preset.id}>
            <PresetTitle>{preset.name}</PresetTitle>
            <PresetDescription>{preset.description}</PresetDescription>
          </BalancePreset>
        ))}
      </Section>

      <Section>
        <SectionTitle>Custom Balance Adjustment</SectionTitle>
        
        <AdjustmentForm onSubmit={handleCustomAdjustment}>
          <FormGroup>
            <FormLabel>Parameter</FormLabel>
            <FormSelect
              value={customAdjustment.parameter}
              onChange={(e) => setCustomAdjustment(prev => ({ ...prev, parameter: e.target.value }))}
              required
            >
              <option value="">Select parameter...</option>
              {Object.entries(configurations)
                .filter(([key, config]) => config.category === 'combat_balance' || config.category === 'ship_balance')
                .map(([key, config]) => (
                  <option key={key} value={key}>{config.description}</option>
                ))}
            </FormSelect>
          </FormGroup>

          <FormGroup>
            <FormLabel>New Value</FormLabel>
            <FormInput
              type="number"
              value={customAdjustment.value}
              onChange={(e) => setCustomAdjustment(prev => ({ ...prev, value: e.target.value }))}
              placeholder="Enter new value..."
              required
            />
          </FormGroup>

          <FormGroup>
            <FormLabel>Reason</FormLabel>
            <FormTextarea
              value={customAdjustment.reason}
              onChange={(e) => setCustomAdjustment(prev => ({ ...prev, reason: e.target.value }))}
              placeholder="Explain the reason for this adjustment..."
            />
          </FormGroup>

          <Button type="submit" variant="primary" disabled={loading}>
            Apply Adjustment
          </Button>
        </AdjustmentForm>
      </Section>

      <Section>
        <SectionTitle>Quick Actions</SectionTitle>
        
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <Button 
            variant="secondary" 
            onClick={() => {
              // Reset all to defaults
              const updates = Object.keys(configurations).map(key => ({
                key,
                value: configurations[key].default_value
              }));
              onBatchUpdate(updates, 'Reset all configurations to default values');
            }}
            disabled={loading}
          >
            Reset All to Defaults
          </Button>
          
          <Button 
            variant="secondary"
            onClick={() => {
              // Optimize for current player count
              console.log('Optimizing for current player count...');
            }}
            disabled={loading}
          >
            Optimize for Player Count
          </Button>
          
          <Button 
            variant="secondary"
            onClick={() => {
              // Generate balance report
              console.log('Generating balance report...');
            }}
            disabled={loading}
          >
            Generate Balance Report
          </Button>
          
          <Button 
            variant="danger"
            onClick={() => {
              // Emergency reset
              if (window.confirm('Are you sure you want to perform an emergency reset? This will revert all configurations to safe defaults.')) {
                console.log('Emergency reset initiated...');
              }
            }}
            disabled={loading}
          >
            Emergency Reset
          </Button>
        </div>
      </Section>
    </BalanceContainer>
  );
};

export default BalanceControls;
