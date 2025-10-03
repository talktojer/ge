"""
Ship management models based on WARSHP structure
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, BigInteger, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class ShipType(Base):
    """Ship type definitions based on SHIP structure - USER, CYBORG, or DROID"""
    __tablename__ = "ship_types"
    
    id = Column(Integer, primary_key=True, index=True)
    typename = Column(String(50), nullable=False, unique=True)  # USER, CYBORG, DROID
    shipname = Column(String(50), nullable=False)  # Ship name/title
    
    # Ship capabilities
    max_shields = Column(Integer, default=0)
    max_phasers = Column(Integer, default=0)
    max_torpedoes = Column(Integer, default=0)
    max_missiles = Column(Integer, default=0)
    
    # Special equipment flags
    has_decoy = Column(Boolean, default=False)
    has_jammer = Column(Boolean, default=False)
    has_zipper = Column(Boolean, default=False)
    has_mine = Column(Boolean, default=False)
    max_attack = Column(Integer, default=0)
    max_cloak = Column(Integer, default=0)
    
    # Performance characteristics
    max_acceleration = Column(Integer, default=0)
    max_warp = Column(Integer, default=0)
    max_tons = Column(BigInteger, default=0)
    max_price = Column(BigInteger, default=0)
    max_points = Column(Integer, default=0)
    max_type = Column(Integer, default=0)
    scan_range = Column(Integer, default=0)
    
    # AI behavior settings
    cybs_can_attack = Column(Boolean, default=True)
    lowest_to_attack = Column(Integer, default=1)
    no_claim = Column(Boolean, default=False)
    total_to_create = Column(Integer, default=0)
    tough_factor = Column(Integer, default=0)
    damage_factor = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    ship_classes = relationship("ShipClass", back_populates="ship_type")
    
    def __repr__(self):
        return f"<ShipType(typename='{self.typename}')>"


class ShipClass(Base):
    """Ship class definitions for different ship types (based on SHIP structure)"""
    __tablename__ = "ship_classes"
    
    id = Column(Integer, primary_key=True, index=True)
    class_number = Column(Integer, nullable=False)  # S01, S02, etc.
    name = Column(String(50), nullable=False)  # SHIP.name (class name)
    description = Column(Text)  # SHIP description
    ship_type_id = Column(Integer, ForeignKey("ship_types.id"), nullable=False)
    is_available = Column(Boolean, default=True)    # From database schema
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    ship_type = relationship("ShipType", back_populates="ship_classes")
    ships = relationship("Ship", back_populates="ship_class")
    
    def __repr__(self):
        return f"<ShipClass(class_number={self.class_number}, name='{self.name}')>"




class Ship(Base):
    """Ship model based on WARSHP structure"""
    __tablename__ = "ships"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Ship identification (from WARSHP)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shipno = Column(Integer, nullable=False)  # WARSHP.shipno - ship id number
    shipname = Column(String(35), nullable=False)  # WARSHP.shipname
    
    # Ship class and type
    ship_class_id = Column(Integer, ForeignKey("ship_classes.id"), nullable=False)
    shpclass = Column(Integer, default=1)  # WARSHP.shpclass - ship class display number
    
    # Navigation (from WARSHP)
    heading = Column(Float, default=0.0)    # WARSHP.heading - current heading
    head2b = Column(Float, default=0.0)     # WARSHP.head2b - direction rotating to
    speed = Column(Float, default=0.0)      # WARSHP.speed - current speed
    speed2b = Column(Float, default=0.0)    # WARSHP.speed2b - speed to be
    
    # Position (from WARSHP.coord)
    x_coord = Column(Float, default=0.0)    # WARSHP.coord.xcoord
    y_coord = Column(Float, default=0.0)    # WARSHP.coord.ycoord
    
    # Ship condition (from WARSHP)
    damage = Column(Float, default=0.0)     # WARSHP.damage - damage percentage (0-100)
    energy = Column(Float, default=0.0)     # WARSHP.energy - available energy
    phaser_strength = Column(Float, default=0.0)  # WARSHP.phasr - phaser strength (0-100)
    phaser_type = Column(Integer, default=0)      # WARSHP.phasrtype - phaser system type
    
    # Combat statistics
    kills = Column(Integer, default=0)      # WARSHP.kills - number of kills
    last_fired = Column(Integer, default=0) # WARSHP.lastfired - usernumber of last attacker
    
    # Shield system (from WARSHP)
    shield_type = Column(Integer, default=0)     # WARSHP.shieldtype
    shield_status = Column(Integer, default=0)   # WARSHP.shieldstat - up/down
    shield_charge = Column(Integer, default=0)   # WARSHP.shield - shield charge
    
    # Cloaking system (from WARSHP)
    cloak = Column(Integer, default=0)      # WARSHP.cloak - cloak flag (-1=up, 0=down, +=time)
    
    # Ship systems status
    tactical = Column(Integer, default=0)   # WARSHP.tactical - tactical display damage
    helm = Column(Integer, default=0)       # WARSHP.helm - helm control damage
    train = Column(Integer, default=0)      # WARSHP.train - training screen counter
    where = Column(Integer, default=0)      # WARSHP.where - hyperspace flag
    
    # Weapons systems
    jammer = Column(Integer, default=0)     # WARSHP.jammer - jammer status
    freq_subspace = Column(Integer, default=0)    # WARSHP.freq[0] - subspace frequency
    freq_hyperspace = Column(Integer, default=0)  # WARSHP.freq[1] - hyperspace frequency  
    freq_planetary = Column(Integer, default=0)   # WARSHP.freq[2] - planetary frequency
    
    # Ship status flags
    hostile = Column(Boolean, default=False)      # WARSHP.hostile - being hostile flag
    cant_exit = Column(Integer, default=0)        # WARSHP.cantexit - cannot exit counter
    repair = Column(Boolean, default=False)       # WARSHP.repair - repairs underway
    hypha = Column(Boolean, default=False)        # WARSHP.hypha - hyper-phasers cooling
    fire_control = Column(Boolean, default=False) # WARSHP.firecntl - fire control damage
    destruct = Column(Integer, default=0)         # WARSHP.destruct - self destruct countdown
    status = Column(Integer, default=0)           # WARSHP.status - record status
    
    # AI/Computer systems
    cyb_mine = Column(Boolean, default=False)     # WARSHP.cybmine - found ship to seek
    cyb_skill = Column(Integer, default=0)        # WARSHP.cybskill - cyborg skill level
    cyb_update = Column(Integer, default=0)       # WARSHP.cybupdate - update counter
    tick = Column(Integer, default=0)             # WARSHP.tick - ship ticker
    emulate = Column(Boolean, default=False)      # WARSHP.emulate - cybertron emulation
    mines_near = Column(Boolean, default=False)   # WARSHP.minesnear - mines nearby flag
    lock = Column(Integer, default=0)             # WARSHP.lock - locked onto ship
    hold_course = Column(Integer, default=0)      # WARSHP.holdcourse - hold course ticker
    top_speed = Column(Integer, default=0)        # WARSHP.topspeed
    warn_counter = Column(Integer, default=0)     # WARSHP.warncntr
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="ships")
    ship_class = relationship("ShipClass", back_populates="ships")
    
    def __repr__(self):
        return f"<Ship(shipname='{self.shipname}', user_id={self.user_id}, shipno={self.shipno})>"
