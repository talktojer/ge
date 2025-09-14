"""
User account models based on WARUSR structure
"""

from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class User(Base):
    """User account model based on WARUSR structure"""
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User identification (from WARUSR.userid)
    userid = Column(String(25), unique=True, index=True, nullable=False)
    
    # Game statistics (from WARUSR)
    score = Column(BigInteger, default=0)  # WARUSR.score
    noships = Column(Integer, default=0)   # WARUSR.noships - number of ships
    topshipno = Column(Integer, default=0) # WARUSR.topshipno - top ship number used
    kills = Column(Integer, default=0)     # WARUSR.kills - number of kills
    planets = Column(Integer, default=0)   # WARUSR.planets - planets owned
    
    # Financial data (from WARUSR)
    cash = Column(BigInteger, default=0)   # WARUSR.cash - cash on hand
    debt = Column(BigInteger, default=0)   # WARUSR.debt - amount owed
    
    # Scoring breakdown (from WARUSR)
    plscore = Column(BigInteger, default=0)    # WARUSR.plscore - planet score
    klscore = Column(BigInteger, default=0)    # WARUSR.klscore - kill score
    population = Column(BigInteger, default=0) # WARUSR.population
    
    # Team information (from WARUSR)
    teamcode = Column(BigInteger, default=0)   # WARUSR.teamcode
    team_id = Column(Integer, ForeignKey("teams.id"))
    
    # User options (from WARUSR.options array)
    # We'll store this as JSON or individual boolean columns
    scan_names = Column(Boolean, default=True)     # SCANNAMES
    scan_home = Column(Boolean, default=True)      # SCANHOME  
    scan_full = Column(Boolean, default=False)     # SCANFULL
    msg_filter = Column(Boolean, default=False)    # MSG_FILTER
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    ships = relationship("Ship", back_populates="user")
    planets_owned = relationship("Planet", back_populates="owner")
    mail_sent = relationship("Mail", foreign_keys="Mail.sender_id", back_populates="sender")
    mail_received = relationship("Mail", foreign_keys="Mail.recipient_id", back_populates="recipient")
    team = relationship("Team", back_populates="members")
    
    def __repr__(self):
        return f"<User(userid='{self.userid}', score={self.score})>"


class UserAccount(Base):
    """Extended user account information"""
    __tablename__ = "user_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Additional account settings
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_sysop = Column(Boolean, default=False)
    
    # Game preferences
    preferred_ship_class = Column(Integer, default=1)
    auto_repair = Column(Boolean, default=False)
    auto_shield = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<UserAccount(user_id={self.user_id}, is_active={self.is_active})>"
