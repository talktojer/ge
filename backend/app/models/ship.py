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
    type_name = Column(String(20), nullable=False, unique=True)  # USER, CYBORG, DROID
    description = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    ship_classes = relationship("ShipClass", back_populates="ship_type")
    
    def __repr__(self):
        return f"<ShipType(type_name='{self.type_name}')>"


class ShipClass(Base):
    """Ship class definitions for different ship types (based on SHIP structure)"""
    __tablename__ = "ship_classes"
    
    id = Column(Integer, primary_key=True, index=True)
    class_number = Column(Integer, nullable=False)  # S01, S02, etc.
    typename = Column(String(50), nullable=False)  # SHIP.typename (class name)
    shipname = Column(String(50), nullable=False)  # SHIP.shipname (ship title name)
    ship_type_id = Column(Integer, ForeignKey("ship_types.id"), nullable=False)
    
    # Ship capabilities (from SHIP structure)
    max_shields = Column(Integer, default=0)       # SHIP.max_shlds (0-19)
    max_phasers = Column(Integer, default=0)       # SHIP.max_phasr (0-19)
    max_torpedoes = Column(Integer, default=0)     # SHIP.max_torps (boolean)
    max_missiles = Column(Integer, default=0)      # SHIP.max_missl (boolean)
    
    # Special equipment flags
    has_decoy = Column(Boolean, default=False)     # SHIP.has_decoy
    has_jammer = Column(Boolean, default=False)    # SHIP.has_jam
    has_zipper = Column(Boolean, default=False)    # SHIP.has_zip
    has_mine = Column(Boolean, default=False)      # SHIP.has_mine
    has_attack_planet = Column(Boolean, default=False)  # Planet attack capability
    has_cloaking = Column(Boolean, default=False)  # SHIP.max_cloak (boolean)
    
    # Performance characteristics
    max_acceleration = Column(Integer, default=0)  # SHIP.max_accel (0-32767)
    max_warp = Column(Integer, default=0)          # SHIP.max_warp (0-255)
    max_tons = Column(BigInteger, default=0)       # SHIP.max_tons (cargo capacity)
    max_price = Column(BigInteger, default=0)      # SHIP.max_price (purchase price)
    max_points = Column(Integer, default=0)        # SHIP.max_points (kill points)
    scan_range = Column(Integer, default=0)        # SHIP.scanrange (1-10000000)
    
    # AI behavior settings (for CYBORG/DROID ships)
    cybs_can_attack = Column(Boolean, default=True)  # SHIP.cybs_can_att
    number_to_attack = Column(Integer, default=0)    # Number of cybs to attack this class
    lowest_to_attack = Column(Integer, default=1)    # SHIP.lowest_to_attk
    no_claim = Column(Boolean, default=False)        # SHIP.noclaim
    total_to_create = Column(Integer, default=0)     # SHIP.tot_to_create
    tough_factor = Column(Integer, default=0)        # SHIP.tough_factor (0-1)
    damage_factor = Column(Integer, default=90)      # SHIP.damfact (damage effect)
    
    # System flags
    is_active = Column(Boolean, default=True)      # Whether this class is available
    help_message = Column(Text)                    # Additional help text
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    ship_type = relationship("ShipType", back_populates="ship_classes")
    ships = relationship("Ship", back_populates="ship_class")
    
    def __repr__(self):
        return f"<ShipClass(class_number={self.class_number}, typename='{self.typename}')>"




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
