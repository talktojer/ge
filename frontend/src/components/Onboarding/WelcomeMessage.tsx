import React from 'react';
import styled from 'styled-components';
import { FaRocket, FaShip, FaGlobe, FaUsers } from 'react-icons/fa';

const WelcomeContainer = styled.div`
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
  border: 1px solid #4ade80;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  position: relative;
  overflow: hidden;
`;

const WelcomeHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
`;

const WelcomeIcon = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000;
  font-size: 24px;
`;

const WelcomeTitle = styled.h2`
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin: 0;
`;

const WelcomeSubtitle = styled.p`
  font-size: 16px;
  color: #888;
  margin: 0 0 20px 0;
`;

const FeatureGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
`;

const FeatureItem = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(74, 222, 128, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(74, 222, 128, 0.2);
`;

const FeatureIcon = styled.div`
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: rgba(74, 222, 128, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4ade80;
  font-size: 16px;
`;

const FeatureText = styled.div`
  color: #fff;
  font-size: 14px;
  font-weight: 500;
`;

const ActionButton = styled.button`
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
  border: none;
  border-radius: 8px;
  color: #000;
  font-size: 14px;
  font-weight: 600;
  padding: 12px 24px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;

  &:hover {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    transform: translateY(-1px);
  }
`;

const BackgroundPattern = styled.div`
  position: absolute;
  top: 0;
  right: 0;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(74, 222, 128, 0.1) 0%, transparent 70%);
  border-radius: 50%;
  transform: translate(50%, -50%);
  pointer-events: none;
`;

interface WelcomeMessageProps {
  isNewUser?: boolean;
  onStartPlaying?: () => void;
}

const WelcomeMessage: React.FC<WelcomeMessageProps> = ({ 
  isNewUser = false, 
  onStartPlaying 
}) => {
  if (!isNewUser) return null;

  return (
    <WelcomeContainer>
      <BackgroundPattern />
      <WelcomeHeader>
        <WelcomeIcon>
          <FaRocket />
        </WelcomeIcon>
        <div>
          <WelcomeTitle>Welcome to Galactic Empire!</WelcomeTitle>
          <WelcomeSubtitle>
            Your journey through the stars begins now. You've been given your first ship to start exploring the galaxy.
          </WelcomeSubtitle>
        </div>
      </WelcomeHeader>

      <FeatureGrid>
        <FeatureItem>
          <FeatureIcon>
            <FaShip />
          </FeatureIcon>
          <FeatureText>Command your fleet</FeatureText>
        </FeatureItem>
        <FeatureItem>
          <FeatureIcon>
            <FaGlobe />
          </FeatureIcon>
          <FeatureText>Colonize planets</FeatureText>
        </FeatureItem>
        <FeatureItem>
          <FeatureIcon>
            <FaUsers />
          </FeatureIcon>
          <FeatureText>Form alliances</FeatureText>
        </FeatureItem>
      </FeatureGrid>

      {onStartPlaying && (
        <ActionButton onClick={onStartPlaying}>
          <FaRocket />
          Start Your Journey
        </ActionButton>
      )}
    </WelcomeContainer>
  );
};

export default WelcomeMessage;


