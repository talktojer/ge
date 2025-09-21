import React from 'react';
import styled from 'styled-components';
import { FaComments, FaEnvelope, FaUserFriends, FaBullhorn, FaPlus } from 'react-icons/fa';

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

const CommunicationGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 24px;
  height: 600px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const ChannelsPanel = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
`;

const ChannelsTitle = styled.h2`
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 20px;
`;

const ChannelList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const ChannelItem = styled.div`
  padding: 12px;
  background: #0a0a0a;
  border: 1px solid #222;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 12px;

  &:hover {
    background: #111;
    border-color: #333;
  }

  &.active {
    background: rgba(74, 222, 128, 0.1);
    border-color: #4ade80;
    color: #4ade80;
  }
`;

const ChannelIcon = styled.div`
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(74, 222, 128, 0.2);
  color: #4ade80;
`;

const ChannelInfo = styled.div`
  flex: 1;
`;

const ChannelName = styled.p`
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 2px;
`;

const ChannelDescription = styled.p`
  font-size: 12px;
  color: #888;
`;

const MessagePanel = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
`;

const MessageHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #333;
`;

const MessageTitle = styled.h3`
  font-size: 18px;
  font-weight: 600;
  color: #fff;
`;

const MessagesArea = styled.div`
  flex: 1;
  overflow-y: auto;
  margin-bottom: 20px;
`;

const MessageInput = styled.div`
  display: flex;
  gap: 12px;
`;

const Input = styled.input`
  flex: 1;
  padding: 12px 16px;
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;

  &:focus {
    outline: none;
    border-color: #4ade80;
  }

  &::placeholder {
    color: #666;
  }
`;

const SendButton = styled.button`
  padding: 12px 16px;
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
  border: none;
  border-radius: 8px;
  color: #000;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  }
`;

const PlaceholderMessage = styled.div`
  text-align: center;
  color: #888;
  padding: 40px;
`;

const Communication: React.FC = () => {
  const channels = [
    { id: 1, name: 'Mail', icon: FaEnvelope, description: 'Personal messages', unread: 3 },
    { id: 2, name: 'Team Chat', icon: FaUserFriends, description: 'Alliance communication', unread: 0 },
    { id: 3, name: 'Beacons', icon: FaBullhorn, description: 'Emergency broadcasts', unread: 1 },
    { id: 4, name: 'Distress Calls', icon: FaComments, description: 'Urgent communications', unread: 0 },
  ];

  return (
    <Container>
      <Header>
        <Title>
          <FaComments />
          Communication Center
        </Title>
        
        <Actions>
          <Button>
            <FaPlus />
            New Message
          </Button>
        </Actions>
      </Header>

      <CommunicationGrid>
        <ChannelsPanel>
          <ChannelsTitle>Channels</ChannelsTitle>
          <ChannelList>
            {channels.map((channel) => (
              <ChannelItem key={channel.id} className={channel.id === 1 ? 'active' : ''}>
                <ChannelIcon>
                  <channel.icon size={16} />
                </ChannelIcon>
                <ChannelInfo>
                  <ChannelName>
                    {channel.name}
                    {channel.unread > 0 && (
                      <span style={{ marginLeft: '8px', color: '#ef4444', fontSize: '12px' }}>
                        ({channel.unread})
                      </span>
                    )}
                  </ChannelName>
                  <ChannelDescription>{channel.description}</ChannelDescription>
                </ChannelInfo>
              </ChannelItem>
            ))}
          </ChannelList>
        </ChannelsPanel>

        <MessagePanel>
          <MessageHeader>
            <MessageTitle>Mail</MessageTitle>
          </MessageHeader>
          
          <MessagesArea>
            <PlaceholderMessage>
              <FaEnvelope size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
              <h3 style={{ color: '#fff', marginBottom: '8px' }}>No Messages</h3>
              <p>Select a channel to view messages or send a new message to get started.</p>
            </PlaceholderMessage>
          </MessagesArea>

          <MessageInput>
            <Input type="text" placeholder="Type your message..." />
            <SendButton>Send</SendButton>
          </MessageInput>
        </MessagePanel>
      </CommunicationGrid>
    </Container>
  );
};

export default Communication;
