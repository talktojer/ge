import React from 'react';
import styled from 'styled-components';
import { FaMap, FaSearch, FaFilter, FaExpand } from 'react-icons/fa';

const Container = styled.div`
  max-width: 1400px;
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
  background: #333;
  border: 1px solid #555;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;

  &:hover {
    background: #444;
    border-color: #666;
  }
`;

const MapContainer = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  height: 600px;
  position: relative;
  overflow: hidden;
`;

const PlaceholderContent = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #888;
`;

const Icon = styled.div`
  font-size: 64px;
  margin-bottom: 24px;
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
  max-width: 400px;
`;

const GalaxyMap: React.FC = () => {
  return (
    <Container>
      <Header>
        <Title>
          <FaMap />
          Galaxy Map
        </Title>
        
        <Actions>
          <Button>
            <FaSearch />
            Search
          </Button>
          <Button>
            <FaFilter />
            Filter
          </Button>
          <Button>
            <FaExpand />
            Fullscreen
          </Button>
        </Actions>
      </Header>

      <MapContainer>
        <PlaceholderContent>
          <Icon>
            <FaMap />
          </Icon>
          <PlaceholderTitle>Interactive Galaxy Map</PlaceholderTitle>
          <PlaceholderText>
            Explore the galaxy, discover new systems, track ship movements, 
            and plan your conquest strategy with this interactive 3D map.
          </PlaceholderText>
        </PlaceholderContent>
      </MapContainer>
    </Container>
  );
};

export default GalaxyMap;
