import React, { useState, useCallback } from 'react';
import styled from 'styled-components';
import { PlayerRanking, TeamRanking } from '../../types';

const ScoringContainer = styled.div`
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
    content: '🏆';
    font-size: 1.1rem;
  }
`;

const RankingsGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;

  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const RankingTable = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  overflow: hidden;
`;

const TableHeader = styled.div`
  background: rgba(0, 212, 255, 0.1);
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
`;

const TableTitle = styled.h4`
  margin: 0;
  color: #00d4ff;
  font-size: 1.1rem;
`;

const TableContent = styled.div`
  max-height: 400px;
  overflow-y: auto;
`;

const TableRow = styled.div<{ rank: number }>`
  display: grid;
  grid-template-columns: 60px 1fr 100px;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
  position: relative;

  &:hover {
    background: rgba(255, 255, 255, 0.05);
  }

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: ${props => {
      if (props.rank === 1) return 'linear-gradient(180deg, #ffd700, #ffed4e)';
      if (props.rank === 2) return 'linear-gradient(180deg, #c0c0c0, #e8e8e8)';
      if (props.rank === 3) return 'linear-gradient(180deg, #cd7f32, #daa520)';
      return 'rgba(255, 255, 255, 0.1)';
    }};
  }
`;

const RankNumber = styled.div<{ rank: number }>`
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
  color: ${props => {
    if (props.rank === 1) return '#ffd700';
    if (props.rank === 2) return '#c0c0c0';
    if (props.rank === 3) return '#cd7f32';
    return '#cccccc';
  }};
`;

const PlayerInfo = styled.div`
  display: flex;
  flex-direction: column;
`;

const PlayerName = styled.div`
  font-weight: bold;
  color: #ffffff;
  margin-bottom: 0.25rem;
`;

const PlayerDetails = styled.div`
  font-size: 0.8rem;
  color: #999999;
`;

const PlayerScore = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: #00d4ff;
  font-size: 1.1rem;
`;

const ScoreBreakdown = styled.div`
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
`;

const BreakdownGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
`;

const BreakdownItem = styled.div`
  text-align: center;
`;

const BreakdownLabel = styled.div`
  font-size: 0.8rem;
  color: #999999;
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const BreakdownValue = styled.div`
  font-weight: bold;
  color: #ffffff;
  font-size: 1.1rem;
`;

const RatingBar = styled.div`
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 0.25rem;
`;

const RatingFill = styled.div<{ value: number }>`
  height: 100%;
  background: linear-gradient(90deg, #ff4757, #f39c12, #2ecc71);
  width: ${props => Math.min(props.value * 10, 100)}%;
  transition: width 0.3s ease;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
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

const LoadingSpinner = styled.div`
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #00d4ff;
  animation: spin 1s ease-in-out infinite;

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

const StatsOverview = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
`;

const StatCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
`;

const StatValue = styled.div`
  font-size: 1.5rem;
  font-weight: bold;
  color: #00d4ff;
  margin-bottom: 0.5rem;
`;

const StatLabel = styled.div`
  font-size: 0.9rem;
  color: #cccccc;
  text-transform: uppercase;
  letter-spacing: 1px;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 2rem;
  color: #999999;
  font-style: italic;
`;

interface ScoringSystemProps {
  playerRankings: PlayerRanking[];
  teamRankings: TeamRanking[];
  onRefresh: () => void;
  loading: boolean;
}

const ScoringSystem: React.FC<ScoringSystemProps> = ({
  playerRankings,
  teamRankings,
  onRefresh,
  loading
}) => {
  const [selectedPlayer, setSelectedPlayer] = useState<PlayerRanking | null>(null);
  const [selectedTeam, setSelectedTeam] = useState<TeamRanking | null>(null);

  const handleRecalculateScores = useCallback(async () => {
    try {
      // This would call the API to recalculate all scores
      console.log('Recalculating all scores...');
      onRefresh();
    } catch (error) {
      console.error('Failed to recalculate scores:', error);
    }
  }, [onRefresh]);

  const handleExportRankings = useCallback(() => {
    const data = {
      playerRankings,
      teamRankings,
      exportedAt: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `galactic-empire-rankings-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [playerRankings, teamRankings]);

  const getTopPlayers = () => playerRankings.slice(0, 10);
  const getTopTeams = () => teamRankings.slice(0, 10);

  const getTotalPlayers = () => playerRankings.length;
  const getTotalTeams = () => teamRankings.length;
  const getAverageScore = () => {
    if (playerRankings.length === 0) return 0;
    const total = playerRankings.reduce((sum, player) => sum + player.score, 0);
    return Math.round(total / playerRankings.length);
  };

  return (
    <ScoringContainer>
      <Section>
        <SectionTitle>Scoring System Overview</SectionTitle>
        
        <ActionButtons>
          <Button variant="primary" onClick={onRefresh} disabled={loading}>
            {loading ? <LoadingSpinner /> : '🔄'} Refresh Rankings
          </Button>
          <Button variant="secondary" onClick={handleRecalculateScores} disabled={loading}>
            ⚡ Recalculate Scores
          </Button>
          <Button variant="secondary" onClick={handleExportRankings} disabled={loading}>
            📊 Export Rankings
          </Button>
        </ActionButtons>

        <StatsOverview>
          <StatCard>
            <StatValue>{getTotalPlayers()}</StatValue>
            <StatLabel>Total Players</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{getTotalTeams()}</StatValue>
            <StatLabel>Total Teams</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{getAverageScore().toLocaleString()}</StatValue>
            <StatLabel>Average Score</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{playerRankings[0]?.score.toLocaleString() || 0}</StatValue>
            <StatLabel>Top Score</StatLabel>
          </StatCard>
        </StatsOverview>
      </Section>

      <Section>
        <SectionTitle>Player Rankings</SectionTitle>
        
        <RankingsGrid>
          <div>
            <RankingTable>
              <TableHeader>
                <TableTitle>Top 10 Players</TableTitle>
              </TableHeader>
              <TableContent>
                {getTopPlayers().length > 0 ? (
                  getTopPlayers().map((player) => (
                    <TableRow
                      key={player.user_id}
                      rank={player.rank}
                      onClick={() => setSelectedPlayer(player)}
                      style={{ cursor: 'pointer' }}
                    >
                      <RankNumber rank={player.rank}>
                        {player.rank === 1 ? '👑' : 
                         player.rank === 2 ? '🥈' : 
                         player.rank === 3 ? '🥉' : 
                         player.rank}
                      </RankNumber>
                      <PlayerInfo>
                        <PlayerName>{player.username}</PlayerName>
                        <PlayerDetails>
                          {player.team_name && `Team: ${player.team_name}`}
                          {player.last_active && ` • Last active: ${new Date(player.last_active).toLocaleDateString()}`}
                        </PlayerDetails>
                      </PlayerInfo>
                      <PlayerScore>{player.score.toLocaleString()}</PlayerScore>
                    </TableRow>
                  ))
                ) : (
                  <EmptyState>No player rankings available</EmptyState>
                )}
              </TableContent>
            </RankingTable>
          </div>

          <div>
            <RankingTable>
              <TableHeader>
                <TableTitle>Top 10 Teams</TableTitle>
              </TableHeader>
              <TableContent>
                {getTopTeams().length > 0 ? (
                  getTopTeams().map((team) => (
                    <TableRow
                      key={team.team_id}
                      rank={team.rank}
                      onClick={() => setSelectedTeam(team)}
                      style={{ cursor: 'pointer' }}
                    >
                      <RankNumber rank={team.rank}>
                        {team.rank === 1 ? '👑' : 
                         team.rank === 2 ? '🥈' : 
                         team.rank === 3 ? '🥉' : 
                         team.rank}
                      </RankNumber>
                      <PlayerInfo>
                        <PlayerName>{team.team_name}</PlayerName>
                        <PlayerDetails>
                          {team.member_count} members • Avg: {team.average_score.toLocaleString()}
                          {team.last_active && ` • Last active: ${new Date(team.last_active).toLocaleDateString()}`}
                        </PlayerDetails>
                      </PlayerInfo>
                      <PlayerScore>{team.total_score.toLocaleString()}</PlayerScore>
                    </TableRow>
                  ))
                ) : (
                  <EmptyState>No team rankings available</EmptyState>
                )}
              </TableContent>
            </RankingTable>
          </div>
        </RankingsGrid>
      </Section>

      {selectedPlayer && (
        <Section>
          <SectionTitle>Player Score Breakdown - {selectedPlayer.username}</SectionTitle>
          
          <ScoreBreakdown>
            <BreakdownGrid>
              <BreakdownItem>
                <BreakdownLabel>Kill Score</BreakdownLabel>
                <BreakdownValue>{selectedPlayer.score_breakdown.kill_score.toLocaleString()}</BreakdownValue>
              </BreakdownItem>
              <BreakdownItem>
                <BreakdownLabel>Planet Score</BreakdownLabel>
                <BreakdownValue>{selectedPlayer.score_breakdown.planet_score.toLocaleString()}</BreakdownValue>
              </BreakdownItem>
              <BreakdownItem>
                <BreakdownLabel>Team Score</BreakdownLabel>
                <BreakdownValue>{selectedPlayer.score_breakdown.team_score.toLocaleString()}</BreakdownValue>
              </BreakdownItem>
              <BreakdownItem>
                <BreakdownLabel>Net Worth</BreakdownLabel>
                <BreakdownValue>{selectedPlayer.score_breakdown.net_worth.toLocaleString()}</BreakdownValue>
              </BreakdownItem>
              <BreakdownItem>
                <BreakdownLabel>Combat Rating</BreakdownLabel>
                <BreakdownValue>{selectedPlayer.score_breakdown.combat_rating.toFixed(1)}/10</BreakdownValue>
                <RatingBar>
                  <RatingFill value={selectedPlayer.score_breakdown.combat_rating} />
                </RatingBar>
              </BreakdownItem>
              <BreakdownItem>
                <BreakdownLabel>Economic Rating</BreakdownLabel>
                <BreakdownValue>{selectedPlayer.score_breakdown.economic_rating.toFixed(1)}/10</BreakdownValue>
                <RatingBar>
                  <RatingFill value={selectedPlayer.score_breakdown.economic_rating} />
                </RatingBar>
              </BreakdownItem>
              <BreakdownItem>
                <BreakdownLabel>Strategic Rating</BreakdownLabel>
                <BreakdownValue>{selectedPlayer.score_breakdown.strategic_rating.toFixed(1)}/10</BreakdownValue>
                <RatingBar>
                  <RatingFill value={selectedPlayer.score_breakdown.strategic_rating} />
                </RatingBar>
              </BreakdownItem>
              <BreakdownItem>
                <BreakdownLabel>Overall Rating</BreakdownLabel>
                <BreakdownValue>{selectedPlayer.score_breakdown.overall_rating.toFixed(1)}/10</BreakdownValue>
                <RatingBar>
                  <RatingFill value={selectedPlayer.score_breakdown.overall_rating} />
                </RatingBar>
              </BreakdownItem>
            </BreakdownGrid>
          </ScoreBreakdown>
        </Section>
      )}

      {selectedTeam && (
        <Section>
          <SectionTitle>Team Details - {selectedTeam.team_name}</SectionTitle>
          
          <ScoreBreakdown>
            <BreakdownGrid>
              <BreakdownItem>
                <BreakdownLabel>Total Score</BreakdownLabel>
                <BreakdownValue>{selectedTeam.total_score.toLocaleString()}</BreakdownValue>
              </BreakdownItem>
              <BreakdownItem>
                <BreakdownLabel>Member Count</BreakdownLabel>
                <BreakdownValue>{selectedTeam.member_count}</BreakdownValue>
              </BreakdownItem>
              <BreakdownItem>
                <BreakdownLabel>Average Score</BreakdownLabel>
                <BreakdownValue>{selectedTeam.average_score.toLocaleString()}</BreakdownValue>
              </BreakdownItem>
              <BreakdownItem>
                <BreakdownLabel>Coordination Bonus</BreakdownLabel>
                <BreakdownValue>{(selectedTeam.coordination_bonus * 100).toFixed(1)}%</BreakdownValue>
              </BreakdownItem>
            </BreakdownGrid>
          </ScoreBreakdown>
        </Section>
      )}
    </ScoringContainer>
  );
};

export default ScoringSystem;
