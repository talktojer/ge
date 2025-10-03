import React, { useState, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { createShip } from '../../store/slices/shipsSlice';
import { fetchShips } from '../../store/slices/shipsSlice';
import styled from 'styled-components';
import {
  FaTimes,
  FaShip,
  FaCheck,
  FaExclamationTriangle,
  FaSpinner
} from 'react-icons/fa';

const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
`;

const ModalContent = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 24px 0 24px;
  margin-bottom: 24px;
`;

const ModalTitle = styled.h2`
  font-size: 24px;
  font-weight: 600;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  color: #888;
  font-size: 24px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s ease;

  &:hover {
    color: #fff;
    background: #333;
  }
`;

const ModalBody = styled.div`
  padding: 0 24px 24px 24px;
`;

const FormGroup = styled.div`
  margin-bottom: 24px;
`;

const Label = styled.label`
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  margin-bottom: 8px;
`;

const Input = styled.input`
  width: 100%;
  padding: 12px 16px;
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 8px;
  color: #fff;
  font-size: 16px;
  transition: border-color 0.2s ease;

  &:focus {
    outline: none;
    border-color: #4ade80;
  }

  &::placeholder {
    color: #666;
  }
`;

const Select = styled.select`
  width: 100%;
  padding: 12px 16px;
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 8px;
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  transition: border-color 0.2s ease;

  &:focus {
    outline: none;
    border-color: #4ade80;
  }

  option {
    background: #0a0a0a;
    color: #fff;
  }
`;

const ShipClassInfo = styled.div`
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 16px;
  margin-top: 12px;
`;

const ShipClassTitle = styled.h4`
  font-size: 16px;
  font-weight: 600;
  color: #4ade80;
  margin-bottom: 8px;
`;

const ShipClassStats = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  font-size: 14px;
`;

const StatItem = styled.div`
  display: flex;
  justify-content: space-between;
  color: #ccc;

  .stat-label {
    color: #888;
  }

  .stat-value {
    color: #fff;
    font-weight: 500;
  }
`;

const ErrorMessage = styled.div`
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ef4444;
  font-size: 14px;
`;

const ModalFooter = styled.div`
  display: flex;
  gap: 12px;
  padding: 24px;
  border-top: 1px solid #333;
`;

const Button = styled.button<{ variant?: 'primary' | 'secondary' }>`
  flex: 1;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: none;

  ${props => props.variant === 'primary' ? `
    background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
    color: #000;
    
    &:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(74, 222, 128, 0.3);
    }
  ` : `
    background: #333;
    color: #fff;
    
    &:hover:not(:disabled) {
      background: #444;
    }
  `}

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none !important;
  }
`;

interface ShipClass {
  id: number;
  class_number: number;
  typename: string;
  shipname: string;
  max_shields: number;
  max_phasers: number;
  max_torpedoes: number;
  max_missiles: number;
  max_acceleration: number;
  max_warp: number;
  cost: number;
}

interface ShipCreationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ShipCreationModal: React.FC<ShipCreationModalProps> = ({ isOpen, onClose }) => {
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);
  const { isLoading: creatingShip, error: createError } = useAppSelector((state) => state.ships);

  const [shipName, setShipName] = useState('');
  const [selectedShipClass, setSelectedShipClass] = useState<number>(1);
  const [shipClasses, setShipClasses] = useState<ShipClass[]>([]);
  const [isLoadingClasses, setIsLoadingClasses] = useState(false);

  // Fetch ship classes when modal opens
  useEffect(() => {
    if (isOpen && shipClasses.length === 0) {
      fetchShipClasses();
    }
  }, [isOpen]);

  const fetchShipClasses = async () => {
    setIsLoadingClasses(true);
    try {
      const response = await fetch('/api/ship-classes');
      if (response.ok) {
        const classes = await response.json();
        // Filter for USER ship types only
        const userClasses = classes.filter((cls: any) => cls.ship_type === 'USER');
        setShipClasses(userClasses);
        if (userClasses.length > 0) {
          setSelectedShipClass(userClasses[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch ship classes:', error);
    } finally {
      setIsLoadingClasses(false);
    }
  };

  const selectedClass = shipClasses.find(cls => cls.id === selectedShipClass);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!shipName.trim()) {
      return;
    }

    try {
      await dispatch(createShip({
        ship_name: shipName.trim(),
        ship_class: selectedShipClass
      })).unwrap();

      // Refresh the ships list
      dispatch(fetchShips({}));
      
      // Close modal and reset form
      onClose();
      setShipName('');
    } catch (error) {
      console.error('Failed to create ship:', error);
    }
  };

  const handleClose = () => {
    if (!creatingShip) {
      onClose();
      setShipName('');
    }
  };

  if (!isOpen) return null;

  return (
    <ModalOverlay onClick={handleClose}>
      <ModalContent onClick={(e) => e.stopPropagation()}>
        <ModalHeader>
          <ModalTitle>
            <FaShip />
            Create New Ship
          </ModalTitle>
          <CloseButton onClick={handleClose} disabled={creatingShip}>
            <FaTimes />
          </CloseButton>
        </ModalHeader>

        <ModalBody>
          <form onSubmit={handleSubmit}>
            <FormGroup>
              <Label htmlFor="shipName">Ship Name</Label>
              <Input
                id="shipName"
                type="text"
                value={shipName}
                onChange={(e) => setShipName(e.target.value)}
                placeholder="Enter ship name..."
                maxLength={50}
                required
                disabled={creatingShip}
              />
            </FormGroup>

            <FormGroup>
              <Label htmlFor="shipClass">Ship Class</Label>
              {isLoadingClasses ? (
                <div style={{ padding: '12px', textAlign: 'center', color: '#888' }}>
                  <FaSpinner style={{ animation: 'spin 1s linear infinite' }} />
                  Loading ship classes...
                </div>
              ) : (
                <Select
                  id="shipClass"
                  value={selectedShipClass}
                  onChange={(e) => setSelectedShipClass(Number(e.target.value))}
                  disabled={creatingShip}
                >
                  {shipClasses.map((shipClass) => (
                    <option key={shipClass.id} value={shipClass.id}>
                      {shipClass.shipname} (Class {shipClass.class_number})
                    </option>
                  ))}
                </Select>
              )}

              {selectedClass && (
                <ShipClassInfo>
                  <ShipClassTitle>{selectedClass.shipname}</ShipClassTitle>
                  <ShipClassStats>
                    <StatItem>
                      <span className="stat-label">Shields:</span>
                      <span className="stat-value">{selectedClass.max_shields}</span>
                    </StatItem>
                    <StatItem>
                      <span className="stat-label">Phasers:</span>
                      <span className="stat-value">{selectedClass.max_phasers}</span>
                    </StatItem>
                    <StatItem>
                      <span className="stat-label">Torpedoes:</span>
                      <span className="stat-value">{selectedClass.max_torpedoes}</span>
                    </StatItem>
                    <StatItem>
                      <span className="stat-label">Missiles:</span>
                      <span className="stat-value">{selectedClass.max_missiles}</span>
                    </StatItem>
                    <StatItem>
                      <span className="stat-label">Max Acceleration:</span>
                      <span className="stat-value">{selectedClass.max_acceleration}</span>
                    </StatItem>
                    <StatItem>
                      <span className="stat-label">Max Warp:</span>
                      <span className="stat-value">{selectedClass.max_warp}</span>
                    </StatItem>
                  </ShipClassStats>
                </ShipClassInfo>
              )}
            </FormGroup>

            {createError && (
              <ErrorMessage>
                <FaExclamationTriangle />
                {typeof createError === 'string' ? createError : 'Failed to create ship'}
              </ErrorMessage>
            )}

            <ModalFooter>
              <Button type="button" variant="secondary" onClick={handleClose} disabled={creatingShip}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" disabled={creatingShip || !shipName.trim()}>
                {creatingShip ? (
                  <>
                    <FaSpinner style={{ animation: 'spin 1s linear infinite' }} />
                    Creating...
                  </>
                ) : (
                  <>
                    <FaCheck />
                    Create Ship
                  </>
                )}
              </Button>
            </ModalFooter>
          </form>
        </ModalBody>
      </ModalContent>
    </ModalOverlay>
  );
};

export default ShipCreationModal;



