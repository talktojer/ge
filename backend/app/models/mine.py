"""
Mine system model based on MINE structure
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Mine(Base):
    """Mine model based on MINE structure"""
    __tablename__ = "mines"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Mine identification (from MINE)
    channel = Column(Integer, nullable=False)  # MINE.channel
    timer = Column(Integer, default=0)         # MINE.timer
    x_coord = Column(Float, default=0.0)       # MINE.coord.xcoord
    y_coord = Column(Float, default=0.0)       # MINE.coord.ycoord
    
    # Mine ownership and settings
    owner_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    damage_potential = Column(Integer, default=100)  # Damage this mine can cause
    
    # Mine type and status
    mine_type = Column(Integer, default=0)     # Type of mine (regular, proximity, etc.)
    is_armed = Column(Boolean, default=True)   # Whether mine is armed and dangerous
    is_visible = Column(Boolean, default=False)  # Whether mine is visible to scanners
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    armed_at = Column(DateTime(timezone=True))
    exploded_at = Column(DateTime(timezone=True))
    
    # Relationships
    owner = relationship("User")
    
    def __repr__(self):
        return f"<Mine(id={self.id}, channel={self.channel}, timer={self.timer}, coords=({self.x_coord},{self.y_coord}))>"


# Mine system constants from original code
class MineConstants:
    NUM_MINES = 20           # NUM_MINES - 20 mines in the game max
    MINERANGE = 10000        # MINERANGE - maximum mine range
    DECOYTIME = 15           # DECOYTIME - times TICKTIME how long a decoy lives
    MINE_DAMAGE_MAX = 100    # Maximum damage a mine can cause
