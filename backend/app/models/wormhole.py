"""
Wormhole system models based on GALWORM and WORMTAB structures
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Wormhole(Base):
    """Wormhole model based on GALWORM structure"""
    __tablename__ = "wormholes"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Wormhole location (from GALWORM)
    xsect = Column(Integer, nullable=False)     # GALWORM.xsect - sector x coord
    ysect = Column(Integer, nullable=False)     # GALWORM.ysect - sector y coord
    plnum = Column(Integer, default=0)          # GALWORM.plnum - planet number
    type = Column(Integer, default=3)           # GALWORM.type - type of sector (PLTYPE_WORM=3)
    
    # Position (from GALWORM.coord)
    x_coord = Column(Float, default=0.0)        # GALWORM.coord.xcoord
    y_coord = Column(Float, default=0.0)        # GALWORM.coord.ycoord
    
    # Destination (from GALWORM.destination)
    dest_x_coord = Column(Float, default=0.0)   # GALWORM.destination.xcoord
    dest_y_coord = Column(Float, default=0.0)   # GALWORM.destination.ycoord
    
    # Wormhole properties (from GALWORM)
    visible = Column(Boolean, default=False)    # GALWORM.visible - is the wormhole visible flag
    name = Column(String(20), default="")       # GALWORM.name
    
    # Wormhole settings
    is_active = Column(Boolean, default=True)
    is_stable = Column(Boolean, default=True)   # Whether wormhole is stable or temporary
    energy_required = Column(Integer, default=0)  # Energy required to use wormhole
    
    # Wormhole statistics
    usage_count = Column(Integer, default=0)    # Number of times used
    last_used = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Wormhole(id={self.id}, coords=({self.x_coord},{self.y_coord}), dest=({self.dest_x_coord},{self.dest_y_coord}), visible={self.visible})>"


class WormholeTable(Base):
    """Wormhole table model based on WORMTAB structure"""
    __tablename__ = "wormhole_table"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Wormhole coordinates (from WORMTAB)
    x_coord = Column(Float, nullable=False)     # WORMTAB.coord.xcoord
    y_coord = Column(Float, nullable=False)     # WORMTAB.coord.ycoord
    dest_x_coord = Column(Float, nullable=False)  # WORMTAB.dest.xcoord
    dest_y_coord = Column(Float, nullable=False)  # WORMTAB.dest.ycoord
    
    # Reference to main wormhole
    wormhole_id = Column(Integer, ForeignKey("wormholes.id"))
    
    # Table entry settings
    is_active = Column(Boolean, default=True)
    table_index = Column(Integer, default=0)    # Index in the wormhole table
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    wormhole = relationship("Wormhole")
    
    def __repr__(self):
        return f"<WormholeTable(id={self.id}, coords=({self.x_coord},{self.y_coord}), dest=({self.dest_x_coord},{self.dest_y_coord}))>"


# Wormhole system constants from original code
class WormholeConstants:
    PLTYPE_WORM = 3         # PLTYPE_WORM - wormhole planet type
    WORM_ODDS = 6           # wormodds - odds of wormhole generation
    MAX_WORMHOLES = 50      # Maximum number of wormholes in the game
