"""
Galactic Empire - Configuration Storage Models

Database models for storing game configuration, versioning, and audit trails.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class GameConfig(Base):
    """Stores game configuration parameters"""
    __tablename__ = "game_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=False)
    config_type = Column(String(20), nullable=False)  # integer, float, boolean, string, json
    category = Column(String(50), nullable=False)     # ship_balance, combat_balance, etc.
    description = Column(Text)
    min_value = Column(Float)
    max_value = Column(Float)
    default_value = Column(JSON)
    requires_restart = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    history = relationship("ConfigHistory", back_populates="config", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<GameConfig(key='{self.key}', value={self.value}, type='{self.config_type}')>"


class ConfigHistory(Base):
    """Audit trail for configuration changes"""
    __tablename__ = "config_history"
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("game_configs.id"), nullable=False)
    old_value = Column(JSON)
    new_value = Column(JSON)
    changed_by = Column(String(100), nullable=False)  # Admin username
    change_reason = Column(Text)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    config = relationship("GameConfig", back_populates="history")
    
    def __repr__(self):
        return f"<ConfigHistory(config='{self.config.key}', changed_by='{self.changed_by}', at='{self.created_at}')>"


class ConfigVersion(Base):
    """Configuration version snapshots"""
    __tablename__ = "config_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    version_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    config_snapshot = Column(JSON, nullable=False)  # Full configuration state
    created_by = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ConfigVersion(name='{self.version_name}', created_by='{self.created_by}')>"


class BalanceAdjustment(Base):
    """Records of balance adjustments made by admins"""
    __tablename__ = "balance_adjustments"
    
    id = Column(Integer, primary_key=True, index=True)
    adjustment_type = Column(String(50), nullable=False)  # energy, combat, economic, etc.
    parameter_name = Column(String(100), nullable=False)
    old_value = Column(JSON)
    new_value = Column(JSON)
    reason = Column(Text, nullable=False)
    impact_analysis = Column(JSON)  # Predicted impact on game balance
    changed_by = Column(String(100), nullable=False)
    approved_by = Column(String(100))  # For major changes requiring approval
    status = Column(String(20), default="pending")  # pending, approved, rejected, applied
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    applied_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<BalanceAdjustment(type='{self.adjustment_type}', parameter='{self.parameter_name}', by='{self.changed_by}')>"


class PlayerScore(Base):
    """Player score tracking and history"""
    __tablename__ = "player_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score_type = Column(String(50), nullable=False)  # kill_score, planet_score, etc.
    score_value = Column(Integer, nullable=False, default=0)
    rank = Column(Integer)
    percentile = Column(Float)  # Position in percentile ranking
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    metadata = Column(JSON)  # Additional score details
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="scores")
    
    def __repr__(self):
        return f"<PlayerScore(user_id={self.user_id}, type='{self.score_type}', value={self.score_value})>"


class PlayerAchievement(Base):
    """Player achievements tracking"""
    __tablename__ = "player_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(String(100), nullable=False)  # Achievement identifier
    achievement_name = Column(String(200), nullable=False)
    achievement_type = Column(String(50), nullable=False)  # combat, economic, etc.
    description = Column(Text)
    reward_score = Column(Integer, default=0)
    rarity = Column(String(20), default="common")  # common, rare, epic, legendary
    icon = Column(String(10))  # Emoji or icon identifier
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(JSON)  # Additional achievement details
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    
    def __repr__(self):
        return f"<PlayerAchievement(user_id={self.user_id}, achievement='{self.achievement_name}')>"


class TeamScore(Base):
    """Team score tracking and history"""
    __tablename__ = "team_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    score_type = Column(String(50), nullable=False)  # team_score, coordination_bonus, etc.
    score_value = Column(Integer, nullable=False, default=0)
    rank = Column(Integer)
    percentile = Column(Float)  # Position in percentile ranking
    member_count = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    metadata = Column(JSON)  # Additional score details
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="scores")
    
    def __repr__(self):
        return f"<TeamScore(team_id={self.team_id}, type='{self.score_type}', value={self.score_value})>"


class GameStatistics(Base):
    """Game-wide statistics and metrics"""
    __tablename__ = "game_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    stat_name = Column(String(100), unique=True, nullable=False)
    stat_value = Column(JSON, nullable=False)
    stat_type = Column(String(50), nullable=False)  # counter, gauge, histogram, etc.
    category = Column(String(50), nullable=False)   # gameplay, performance, balance, etc.
    description = Column(Text)
    tags = Column(JSON)  # Additional categorization tags
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<GameStatistics(name='{self.stat_name}', value={self.stat_value})>"


class BalanceReport(Base):
    """Automated balance analysis reports"""
    __tablename__ = "balance_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), nullable=False)  # daily, weekly, monthly, on_demand
    analysis_data = Column(JSON, nullable=False)  # Balance metrics and recommendations
    recommendations = Column(JSON)  # Suggested adjustments
    critical_issues = Column(JSON)  # Critical balance problems
    generated_by = Column(String(100), default="system")
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="pending")  # pending, reviewed, applied
    
    def __repr__(self):
        return f"<BalanceReport(type='{self.report_type}', generated_at='{self.generated_at}')>"


# Add relationships to existing models
def add_config_relationships():
    """Add relationships to existing User and Team models"""
    # This would be called during model initialization
    # The actual relationships would be added to the existing User and Team models
    pass


# Configuration categories for reference
CONFIG_CATEGORIES = {
    "ship_balance": "Ship system balance parameters",
    "combat_balance": "Combat system balance parameters", 
    "economic_system": "Economic system parameters",
    "scoring_system": "Scoring and ranking parameters",
    "game_mechanics": "Core game mechanics parameters",
    "admin_settings": "Administrative settings"
}

# Configuration types for validation
CONFIG_TYPES = {
    "integer": int,
    "float": float,
    "boolean": bool,
    "string": str,
    "json": dict
}

# Score types for tracking
SCORE_TYPES = {
    "kill_score": "Combat kills and victories",
    "planet_score": "Planet control and development",
    "team_score": "Team cooperation and coordination",
    "net_worth": "Total asset value",
    "combat_rating": "Combat effectiveness rating",
    "economic_rating": "Economic performance rating",
    "strategic_rating": "Strategic planning rating",
    "overall_rating": "Overall performance rating"
}

# Achievement types
ACHIEVEMENT_TYPES = {
    "combat": "Combat-related achievements",
    "economic": "Economic achievements",
    "strategic": "Strategic achievements", 
    "teamwork": "Team cooperation achievements",
    "exploration": "Exploration achievements",
    "special": "Special or unique achievements"
}
