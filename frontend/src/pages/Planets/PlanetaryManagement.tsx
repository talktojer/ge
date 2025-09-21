import React from 'react';
import styled from 'styled-components';
import { FaGlobe, FaPlus, FaSearch, FaFilter, FaEye, FaCog } from 'react-icons/fa';

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
`;

const Title = styled.h1`
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const Actions = styled.div`
  display: flex;
  gap: 12px;
`;

const Button = styled.button`
  padding: 12px 16px;
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
  border: none;
  border-radius: 8px;
  color: #000;
  font-size: 14px;
  font-weight: 600;
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

const PlaceholderCard = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 60px;
  text-align: center;
  color: #888;
`;

const Icon = styled.div`
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
`;

const PlaceholderTitle = styled.h2`
  font-size: 24px;
  margin-bottom: 12px;
  color: #fff;
`;

const PlaceholderText = styled.p`
  font-size: 16px;
  margin-bottom: 24px;
`;

const PlanetaryManagement: React.FC = () => {
  return (
    <Container>
      <Header>
        <Title>
          <FaGlobe />
          Planetary Management
        </Title>
        
        <Actions>
          <Button>
            <FaFilter />
            Filter
          </Button>
          <Button>
            <FaPlus />
            Colonize Planet
          </Button>
        </Actions>
      </Header>

      <PlaceholderCard>
        <Icon>
          <FaGlobe />
        </Icon>
        <PlaceholderTitle>Planetary Management</PlaceholderTitle>
        <PlaceholderText>
          Manage your colonies, resources, and planetary systems. 
          This feature will include planet scanning, colonization, resource management, and trading.
        </PlaceholderText>
        <Button>
          <FaEye />
          View Galaxy Map
        </Button>
      </PlaceholderCard>
    </Container>
  );
};

export default PlanetaryManagement;
