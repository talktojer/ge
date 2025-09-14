"""
Beacon system model based on BEACONTAB structure
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Beacon(Base):
    """Beacon model based on BEACONTAB structure"""
    __tablename__ = "beacons"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Beacon location (from BEACONTAB)
    x_coord = Column(Float, nullable=False)    # BEACONTAB.coord.xcoord
    y_coord = Column(Float, nullable=False)    # BEACONTAB.coord.ycoord
    plnum = Column(Integer, default=0)         # BEACONTAB.plnum - planet number
    
    # Beacon message (from BEACONTAB)
    beacon_message = Column(String(75), default="")  # BEACONTAB.beacon[BEACONMSGSZ]
    
    # Beacon ownership and settings
    owner_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)  # Whether beacon is visible to all players
    
    # Beacon type and status
    beacon_type = Column(Integer, default=0)   # Type of beacon (distress, trade, etc.)
    priority = Column(Integer, default=0)      # Beacon priority level
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))  # When beacon expires (if applicable)
    
    # Relationships
    owner = relationship("User")
    
    def __repr__(self):
        return f"<Beacon(id={self.id}, coords=({self.x_coord},{self.y_coord}), message='{self.beacon_message[:20]}...')>"


# Beacon system constants from original code
class BeaconConstants:
    BEACONMSGSZ = 75         # BEACONMSGSZ - beacon message size
    MAX_BEACONS = 100        # Maximum number of beacons in the game
