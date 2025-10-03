"""
Team/alliance system model based on TEAM structure
"""

from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Team(Base):
    """Team/alliance model based on TEAM structure"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Team identification (from TEAM)
    teamcode = Column(BigInteger, unique=True, nullable=False)  # TEAM.teamcode
    teamname = Column(String(31), nullable=False)               # TEAM.teamname
    teamcount = Column(Integer, default=0)                      # TEAM.teamcount - member count
    teamscore = Column(BigInteger, default=0)                   # TEAM.teamscore
    
    # Team security (from TEAM)
    password = Column(String(11), default="")                   # TEAM.password
    secret = Column(String(11), default="")                     # TEAM.secret
    
    # Team status (from TEAM)
    flag = Column(Integer, default=0)                           # TEAM.flag
    
    # Team settings
    is_active = Column(Boolean, default=True)
    max_members = Column(Integer, default=50)  # MAXTEAMS from original code
    
    # Team leader
    leader_id = Column(Integer, ForeignKey("users.id"))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    leader = relationship("User", foreign_keys=[leader_id], back_populates="led_teams")
    members = relationship("User", foreign_keys="User.team_id", back_populates="team")
    scores = relationship("TeamScore", back_populates="team")
    
    def __repr__(self):
        return f"<Team(teamname='{self.teamname}', teamcode={self.teamcode}, members={self.teamcount})>"
