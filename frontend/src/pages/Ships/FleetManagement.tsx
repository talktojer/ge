import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { fetchShips } from '../../store/slices/shipsSlice';
import styled from 'styled-components';
import {
  FaShip,
  FaPlus,
  FaSearch,
  FaFilter,
  FaEye,
  FaCog,
  FaTrash,
  FaPlay,
  FaPause,
  FaExclamationTriangle,
  FaCheckCircle
} from 'react-icons/fa';

const FleetContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
`;

const FleetHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
`;

const FleetTitle = styled.h1`
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const FleetActions = styled.div`
  display: flex;
  gap: 12px;
`;

const SearchBar = styled.div`
  position: relative;
  display: flex;
  align-items: center;
`;

const SearchInput = styled.input`
  padding: 12px 16px 12px 40px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  width: 300px;

  &:focus {
    outline: none;
    border-color: #4ade80;
  }

  &::placeholder {
    color: #666;
  }
`;

const SearchIcon = styled.div`
  position: absolute;
  left: 12px;
  color: #666;
  font-size: 14px;
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

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const SecondaryButton = styled(Button)`
  background: #333;
  color: #fff;

  &:hover {
    background: #444;
  }
`;

const ShipsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
`;

const ShipCard = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
  transition: all 0.2s ease;

  &:hover {
    border-color: #444;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  }
`;

const ShipHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
`;

const ShipInfo = styled.div`
  flex: 1;
`;

const ShipName = styled.h3`
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 4px;
`;

const ShipType = styled.p`
  font-size: 14px;
  color: #888;
  margin-bottom: 8px;
`;

const ShipStatus = styled.div<{ active: boolean }>`
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: ${props => props.active ? '#4ade80' : '#f87171'};
`;

const ShipActions = styled.div`
  display: flex;
  gap: 8px;
`;

const ActionButton = styled.button`
  padding: 8px;
  background: #333;
  border: none;
  border-radius: 6px;
  color: #ccc;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #444;
    color: #fff;
  }
`;

const ShipStats = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
`;

const StatItem = styled.div`
  text-align: center;
`;

const StatLabel = styled.p`
  font-size: 12px;
  color: #888;
  margin-bottom: 4px;
`;

const StatValue = styled.p`
  font-size: 16px;
  font-weight: 600;
  color: #fff;
`;

const ShipLocation = styled.div`
  padding: 12px;
  background: #0a0a0a;
  border-radius: 8px;
  border: 1px solid #222;
`;

const LocationTitle = styled.p`
  font-size: 12px;
  color: #888;
  margin-bottom: 4px;
`;

const LocationCoords = styled.p`
  font-size: 14px;
  color: #fff;
  font-weight: 500;
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  font-size: 16px;
  color: #888;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 60px 20px;
  color: #888;
`;

const EmptyIcon = styled.div`
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
`;

const EmptyTitle = styled.h3`
  font-size: 20px;
  margin-bottom: 8px;
  color: #fff;
`;

const EmptyDescription = styled.p`
  font-size: 14px;
  margin-bottom: 24px;
`;

const FleetManagement: React.FC = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { ships, isLoading } = useAppSelector((state) => state.ships);
  const [searchTerm, setSearchTerm] = React.useState('');

  useEffect(() => {
    dispatch(fetchShips({}));
  }, [dispatch]);

  const filteredShips = ships.filter(ship =>
    ship.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    ship.ship_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleShipSelect = (shipId: number) => {
    navigate(`/ships/${shipId}`);
  };

  const handleCreateShip = () => {
    // TODO: Implement ship creation modal
    console.log('Create new ship');
  };

  if (isLoading) {
    return (
      <FleetContainer>
        <LoadingSpinner>Loading fleet...</LoadingSpinner>
      </FleetContainer>
    );
  }

  return (
    <FleetContainer>
      <FleetHeader>
        <FleetTitle>
          <FaShip />
          Fleet Management
        </FleetTitle>
        
        <FleetActions>
          <SearchBar>
            <SearchIcon>
              <FaSearch />
            </SearchIcon>
            <SearchInput
              type="text"
              placeholder="Search ships..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </SearchBar>
          
          <SecondaryButton>
            <FaFilter />
            Filter
          </SecondaryButton>
          
          <Button onClick={handleCreateShip}>
            <FaPlus />
            New Ship
          </Button>
        </FleetActions>
      </FleetHeader>

      {filteredShips.length === 0 ? (
        <EmptyState>
          <EmptyIcon>
            <FaShip />
          </EmptyIcon>
          <EmptyTitle>No Ships Found</EmptyTitle>
          <EmptyDescription>
            {searchTerm ? 'No ships match your search criteria.' : 'You don\'t have any ships yet.'}
          </EmptyDescription>
          {!searchTerm && (
            <Button onClick={handleCreateShip}>
              <FaPlus />
              Build Your First Ship
            </Button>
          )}
        </EmptyState>
      ) : (
        <ShipsGrid>
          {filteredShips.map((ship) => (
            <ShipCard key={ship.id}>
              <ShipHeader>
                <ShipInfo>
                  <ShipName>{ship.name}</ShipName>
                  <ShipType>{ship.ship_class} {ship.ship_type}</ShipType>
                  <ShipStatus active={ship.is_active}>
                    {ship.is_active ? <FaCheckCircle /> : <FaPause />}
                    {ship.is_active ? 'Active' : 'Inactive'}
                  </ShipStatus>
                </ShipInfo>
                
                <ShipActions>
                  <ActionButton onClick={() => handleShipSelect(ship.id)} title="View Details">
                    <FaEye />
                  </ActionButton>
                  <ActionButton title="Settings">
                    <FaCog />
                  </ActionButton>
                  <ActionButton title="Delete">
                    <FaTrash />
                  </ActionButton>
                </ShipActions>
              </ShipHeader>

              <ShipStats>
                <StatItem>
                  <StatLabel>Hull Points</StatLabel>
                  <StatValue>{ship.hull_points}/{ship.max_hull_points}</StatValue>
                </StatItem>
                <StatItem>
                  <StatLabel>Shields</StatLabel>
                  <StatValue>{ship.shields}/{ship.max_shields}</StatValue>
                </StatItem>
                <StatItem>
                  <StatLabel>Fuel</StatLabel>
                  <StatValue>{ship.fuel}/{ship.max_fuel}</StatValue>
                </StatItem>
                <StatItem>
                  <StatLabel>Cargo</StatLabel>
                  <StatValue>{ship.cargo_used}/{ship.cargo_capacity}</StatValue>
                </StatItem>
              </ShipStats>

              <ShipLocation>
                <LocationTitle>Current Location</LocationTitle>
                <LocationCoords>
                  Sector {ship.sector} - ({ship.x}, {ship.y}, {ship.z})
                </LocationCoords>
              </ShipLocation>
            </ShipCard>
          ))}
        </ShipsGrid>
      )}
    </FleetContainer>
  );
};

export default FleetManagement;
