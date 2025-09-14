"""
Galactic Empire - Team Service

This module handles team management operations including team creation,
member management, and team statistics.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from ..models.team import Team
from ..models.user import User
from ..core.auth import auth_service


class TeamService:
    """Service for team management operations"""
    
    def __init__(self):
        self.auth_service = auth_service
    
    def create_team(self, db: Session, user_id: int, team_name: str, password: str = None, secret: str = None) -> Dict[str, Any]:
        """Create a new team"""
        # Check if user exists and is not already in a team
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already in a team"
            )
        
        # Check if team name is already taken
        existing_team = db.query(Team).filter(Team.team_name == team_name).first()
        if existing_team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team name already taken"
            )
        
        # Generate team code (unique identifier)
        team_code = self._generate_team_code(db)
        
        # Create team
        team = Team(
            team_name=team_name,
            team_code=team_code,
            password=password or "",
            secret=secret or "",
            teamcount=1,  # Creator is first member
            teamscore=0,
            flag=1  # Active
        )
        
        db.add(team)
        db.commit()
        db.refresh(team)
        
        # Add creator as team member
        user.team_id = team.id
        user.teamcode = team_code
        db.commit()
        
        return {
            "message": "Team created successfully",
            "team": {
                "id": team.id,
                "team_name": team.team_name,
                "team_code": team.team_code,
                "teamcount": team.teamcount,
                "teamscore": team.teamscore,
                "has_password": bool(password)
            }
        }
    
    def join_team(self, db: Session, user_id: int, team_code: int, password: str = None) -> Dict[str, Any]:
        """Join an existing team"""
        # Check if user exists and is not already in a team
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already in a team"
            )
        
        # Find team by code
        team = db.query(Team).filter(Team.team_code == team_code).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        if team.flag != 1:  # Team not active
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team is not active"
            )
        
        # Check password if required
        if team.password and team.password != password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid team password"
            )
        
        # Add user to team
        user.team_id = team.id
        user.teamcode = team_code
        team.teamcount += 1
        db.commit()
        
        return {
            "message": "Successfully joined team",
            "team": {
                "id": team.id,
                "team_name": team.team_name,
                "team_code": team.team_code,
                "teamcount": team.teamcount,
                "teamscore": team.teamscore
            }
        }
    
    def leave_team(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Leave current team"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not in a team"
            )
        
        team = db.query(Team).filter(Team.id == user.team_id).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Remove user from team
        user.team_id = None
        user.teamcode = 0
        team.teamcount -= 1
        
        # If team is empty, deactivate it
        if team.teamcount <= 0:
            team.flag = 0  # Inactive
            team.teamcount = 0
        
        db.commit()
        
        return {
            "message": "Successfully left team",
            "team_name": team.team_name
        }
    
    def get_team_info(self, db: Session, team_id: int) -> Dict[str, Any]:
        """Get team information"""
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Get team members
        members = db.query(User).filter(User.team_id == team_id).all()
        
        return {
            "team": {
                "id": team.id,
                "team_name": team.team_name,
                "team_code": team.team_code,
                "teamcount": team.teamcount,
                "teamscore": team.teamscore,
                "flag": team.flag,
                "created_at": team.created_at.isoformat()
            },
            "members": [
                {
                    "id": member.id,
                    "userid": member.userid,
                    "score": member.score,
                    "kills": member.kills,
                    "planets": member.planets,
                    "cash": member.cash,
                    "last_login": member.last_login.isoformat() if member.last_login else None
                }
                for member in members
            ]
        }
    
    def get_team_members(self, db: Session, team_id: int) -> List[Dict[str, Any]]:
        """Get team members"""
        members = db.query(User).filter(User.team_id == team_id).all()
        
        return [
            {
                "id": member.id,
                "userid": member.userid,
                "score": member.score,
                "kills": member.kills,
                "planets": member.planets,
                "cash": member.cash,
                "last_login": member.last_login.isoformat() if member.last_login else None
            }
            for member in members
        ]
    
    def update_team_password(self, db: Session, team_id: int, user_id: int, new_password: str) -> Dict[str, Any]:
        """Update team password (team leader only)"""
        # Check if user is team leader (first member)
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or not in team"
            )
        
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Check if user is team leader (simplified: first member by ID)
        team_members = db.query(User).filter(User.team_id == team_id).order_by(User.id).all()
        if not team_members or team_members[0].id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only team leader can update password"
            )
        
        # Update password
        team.password = new_password
        db.commit()
        
        return {"message": "Team password updated successfully"}
    
    def update_team_secret(self, db: Session, team_id: int, user_id: int, new_secret: str) -> Dict[str, Any]:
        """Update team secret (team leader only)"""
        # Check if user is team leader (first member)
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or not in team"
            )
        
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Check if user is team leader (simplified: first member by ID)
        team_members = db.query(User).filter(User.team_id == team_id).order_by(User.id).all()
        if not team_members or team_members[0].id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only team leader can update secret"
            )
        
        # Update secret
        team.secret = new_secret
        db.commit()
        
        return {"message": "Team secret updated successfully"}
    
    def get_team_leaderboard(self, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get team leaderboard by score"""
        teams = db.query(Team).filter(
            Team.flag == 1  # Active teams only
        ).order_by(Team.teamscore.desc()).limit(limit).all()
        
        leaderboard = []
        for i, team in enumerate(teams, 1):
            leaderboard.append({
                "rank": i,
                "team_name": team.team_name,
                "team_code": team.team_code,
                "teamscore": team.teamscore,
                "teamcount": team.teamcount,
                "created_at": team.created_at.isoformat()
            })
        
        return leaderboard
    
    def search_teams(self, db: Session, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for teams by name"""
        teams = db.query(Team).filter(
            Team.team_name.ilike(f"%{query}%"),
            Team.flag == 1  # Active teams only
        ).limit(limit).all()
        
        return [
            {
                "id": team.id,
                "team_name": team.team_name,
                "team_code": team.team_code,
                "teamcount": team.teamcount,
                "teamscore": team.teamscore,
                "has_password": bool(team.password)
            }
            for team in teams
        ]
    
    def _generate_team_code(self, db: Session) -> int:
        """Generate a unique team code"""
        import random
        
        while True:
            team_code = random.randint(100000, 999999)
            existing = db.query(Team).filter(Team.team_code == team_code).first()
            if not existing:
                return team_code


# Global team service instance
team_service = TeamService()
