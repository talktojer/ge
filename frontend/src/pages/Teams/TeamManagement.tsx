import React from 'react';
import styled from 'styled-components';
import { FaUsers, FaPlus, FaCrown, FaUserPlus, FaSignOutAlt } from 'react-icons/fa';

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

const Button = styled.button<{ variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;

  ${props => {
    switch (props.variant) {
      case 'primary':
        return `
          background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
          color: #000;
          &:hover { background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); }
        `;
      case 'danger':
        return `
          background: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
          color: #fff;
          &:hover { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
        `;
      default:
        return `
          background: #333;
          color: #fff;
          border: 1px solid #555;
          &:hover { background: #444; border-color: #666; }
        `;
    }
  }}

  &:hover {
    transform: translateY(-1px);
  }
`;

const TeamCard = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
`;

const TeamHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
`;

const TeamInfo = styled.div`
  flex: 1;
`;

const TeamName = styled.h2`
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const TeamDescription = styled.p`
  font-size: 16px;
  color: #888;
  margin-bottom: 16px;
`;

const TeamStats = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
`;

const StatItem = styled.div`
  text-align: center;
`;

const StatValue = styled.div`
  font-size: 24px;
  font-weight: 700;
  color: #4ade80;
  margin-bottom: 4px;
`;

const StatLabel = styled.div`
  font-size: 12px;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const MembersSection = styled.div`
  margin-top: 24px;
`;

const MembersTitle = styled.h3`
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 16px;
`;

const MembersList = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 12px;
`;

const MemberCard = styled.div`
  background: #0a0a0a;
  border: 1px solid #222;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const MemberAvatar = styled.div`
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
`;

const MemberInfo = styled.div`
  flex: 1;
`;

const MemberName = styled.p`
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 2px;
`;

const MemberRole = styled.p`
  font-size: 12px;
  color: #888;
`;

const NoTeamCard = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 60px;
  text-align: center;
`;

const NoTeamIcon = styled.div`
  font-size: 64px;
  margin-bottom: 24px;
  opacity: 0.5;
  color: #888;
`;

const NoTeamTitle = styled.h2`
  font-size: 24px;
  color: #fff;
  margin-bottom: 12px;
`;

const NoTeamText = styled.p`
  font-size: 16px;
  color: #888;
  margin-bottom: 24px;
`;

const TeamManagement: React.FC = () => {
  // Mock data - in real app this would come from Redux store
  const hasTeam = false; // Change to true to see team view
  const team = {
    id: 1,
    name: 'Galactic Empire',
    description: 'The most powerful alliance in the galaxy',
    leader: 'Commander Smith',
    memberCount: 5,
    totalScore: 125000,
    created_at: '2024-01-15',
    members: [
      { id: 1, name: 'Commander Smith', role: 'Leader', isOnline: true },
      { id: 2, name: 'Captain Jones', role: 'Member', isOnline: false },
      { id: 3, name: 'Admiral Wilson', role: 'Member', isOnline: true },
      { id: 4, name: 'Lieutenant Brown', role: 'Member', isOnline: false },
      { id: 5, name: 'Ensign Davis', role: 'Member', isOnline: true },
    ]
  };

  return (
    <Container>
      <Header>
        <Title>
          <FaUsers />
          Team Management
        </Title>
        
        {hasTeam ? (
          <Actions>
            <Button variant="secondary">
              <FaUserPlus />
              Invite Members
            </Button>
            <Button variant="danger">
              <FaSignOutAlt />
              Leave Team
            </Button>
          </Actions>
        ) : (
          <Actions>
            <Button variant="primary">
              <FaPlus />
              Create Team
            </Button>
            <Button variant="secondary">
              Browse Teams
            </Button>
          </Actions>
        )}
      </Header>

      {hasTeam ? (
        <TeamCard>
          <TeamHeader>
            <TeamInfo>
              <TeamName>
                <FaCrown />
                {team.name}
              </TeamName>
              <TeamDescription>{team.description}</TeamDescription>
            </TeamInfo>
          </TeamHeader>

          <TeamStats>
            <StatItem>
              <StatValue>{team.memberCount}</StatValue>
              <StatLabel>Members</StatLabel>
            </StatItem>
            <StatItem>
              <StatValue>{team.totalScore.toLocaleString()}</StatValue>
              <StatLabel>Total Score</StatLabel>
            </StatItem>
            <StatItem>
              <StatValue>3</StatValue>
              <StatLabel>Online Now</StatLabel>
            </StatItem>
          </TeamStats>

          <MembersSection>
            <MembersTitle>Team Members</MembersTitle>
            <MembersList>
              {team.members.map((member) => (
                <MemberCard key={member.id}>
                  <MemberAvatar>
                    {member.name.split(' ').map(n => n[0]).join('')}
                  </MemberAvatar>
                  <MemberInfo>
                    <MemberName>
                      {member.name}
                      {member.role === 'Leader' && <FaCrown size={12} style={{ marginLeft: '8px', color: '#fbbf24' }} />}
                    </MemberName>
                    <MemberRole>
                      {member.role} • {member.isOnline ? 'Online' : 'Offline'}
                    </MemberRole>
                  </MemberInfo>
                </MemberCard>
              ))}
            </MembersList>
          </MembersSection>
        </TeamCard>
      ) : (
        <NoTeamCard>
          <NoTeamIcon>
            <FaUsers />
          </NoTeamIcon>
          <NoTeamTitle>No Team Joined</NoTeamTitle>
          <NoTeamText>
            Join an alliance to coordinate with other players, share resources, 
            and dominate the galaxy together. Create your own team or join an existing one.
          </NoTeamText>
          <Actions style={{ justifyContent: 'center' }}>
            <Button variant="primary">
              <FaPlus />
              Create Team
            </Button>
            <Button variant="secondary">
              Browse Teams
            </Button>
          </Actions>
        </NoTeamCard>
      )}
    </Container>
  );
};

export default TeamManagement;
