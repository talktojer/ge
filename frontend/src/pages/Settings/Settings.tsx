import React from 'react';
import styled from 'styled-components';
import { FaCog, FaUser, FaBell, FaPalette, FaShieldAlt, FaSave } from 'react-icons/fa';

const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
`;

const Header = styled.div`
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

const SettingsGrid = styled.div`
  display: grid;
  gap: 24px;
`;

const SettingsSection = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
`;

const SectionTitle = styled.h2`
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const SettingItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #222;

  &:last-child {
    border-bottom: none;
  }
`;

const SettingInfo = styled.div`
  flex: 1;
`;

const SettingLabel = styled.p`
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 4px;
`;

const SettingDescription = styled.p`
  font-size: 12px;
  color: #888;
`;

const SettingControl = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const Toggle = styled.label`
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
`;

const ToggleInput = styled.input`
  opacity: 0;
  width: 0;
  height: 0;

  &:checked + span {
    background-color: #4ade80;
  }

  &:checked + span:before {
    transform: translateX(24px);
  }
`;

const ToggleSlider = styled.span`
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #333;
  transition: 0.2s;
  border-radius: 24px;

  &:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: 0.2s;
    border-radius: 50%;
  }
`;

const Select = styled.select`
  padding: 8px 12px;
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 6px;
  color: #fff;
  font-size: 14px;

  &:focus {
    outline: none;
    border-color: #4ade80;
  }
`;

const Button = styled.button<{ variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 12px 24px;
  background: ${props => {
    switch (props.variant) {
      case 'secondary': return '#333';
      case 'danger': return '#ef4444';
      default: return 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)';
    }
  }};
  border: none;
  border-radius: 8px;
  color: ${props => props.variant === 'secondary' || props.variant === 'danger' ? '#fff' : '#000'};
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

const Settings: React.FC = () => {
  return (
    <Container>
      <Header>
        <Title>
          <FaCog />
          Settings
        </Title>
      </Header>

      <SettingsGrid>
        {/* Profile Settings */}
        <SettingsSection>
          <SectionTitle>
            <FaUser />
            Profile
          </SectionTitle>
          
          <SettingItem>
            <SettingInfo>
              <SettingLabel>Username</SettingLabel>
              <SettingDescription>Your display name in the game</SettingDescription>
            </SettingInfo>
            <SettingControl>
              <span style={{ color: '#fff' }}>Commander123</span>
            </SettingControl>
          </SettingItem>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Email</SettingLabel>
              <SettingDescription>Your account email address</SettingDescription>
            </SettingInfo>
            <SettingControl>
              <span style={{ color: '#888' }}>user@example.com</span>
            </SettingControl>
          </SettingItem>
        </SettingsSection>

        {/* Notification Settings */}
        <SettingsSection>
          <SectionTitle>
            <FaBell />
            Notifications
          </SectionTitle>
          
          <SettingItem>
            <SettingInfo>
              <SettingLabel>In-game Messages</SettingLabel>
              <SettingDescription>Receive notifications for new messages</SettingDescription>
            </SettingInfo>
            <SettingControl>
              <Toggle>
                <ToggleInput type="checkbox" defaultChecked />
                <ToggleSlider />
              </Toggle>
            </SettingControl>
          </SettingItem>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Combat Alerts</SettingLabel>
              <SettingDescription>Get notified when combat occurs</SettingDescription>
            </SettingInfo>
            <SettingControl>
              <Toggle>
                <ToggleInput type="checkbox" defaultChecked />
                <ToggleSlider />
              </Toggle>
            </SettingControl>
          </SettingItem>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>System Updates</SettingLabel>
              <SettingDescription>Notifications for game system changes</SettingDescription>
            </SettingInfo>
            <SettingControl>
              <Toggle>
                <ToggleInput type="checkbox" />
                <ToggleSlider />
              </Toggle>
            </SettingControl>
          </SettingItem>
        </SettingsSection>

        {/* Display Settings */}
        <SettingsSection>
          <SectionTitle>
            <FaPalette />
            Display
          </SectionTitle>
          
          <SettingItem>
            <SettingInfo>
              <SettingLabel>Theme</SettingLabel>
              <SettingDescription>Choose your preferred color scheme</SettingDescription>
            </SettingInfo>
            <SettingControl>
              <Select defaultValue="dark">
                <option value="dark">Dark</option>
                <option value="light">Light</option>
              </Select>
            </SettingControl>
          </SettingItem>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Language</SettingLabel>
              <SettingDescription>Interface language</SettingDescription>
            </SettingInfo>
            <SettingControl>
              <Select defaultValue="en">
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
              </Select>
            </SettingControl>
          </SettingItem>
        </SettingsSection>

        {/* Security Settings */}
        <SettingsSection>
          <SectionTitle>
            <FaShieldAlt />
            Security
          </SectionTitle>
          
          <SettingItem>
            <SettingInfo>
              <SettingLabel>Two-Factor Authentication</SettingLabel>
              <SettingDescription>Add an extra layer of security to your account</SettingDescription>
            </SettingInfo>
            <SettingControl>
              <Button variant="secondary">
                Enable 2FA
              </Button>
            </SettingControl>
          </SettingItem>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Change Password</SettingLabel>
              <SettingDescription>Update your account password</SettingDescription>
            </SettingInfo>
            <SettingControl>
              <Button variant="secondary">
                Change Password
              </Button>
            </SettingControl>
          </SettingItem>
        </SettingsSection>

        {/* Save Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button>
            <FaSave />
            Save Settings
          </Button>
        </div>
      </SettingsGrid>
    </Container>
  );
};

export default Settings;
