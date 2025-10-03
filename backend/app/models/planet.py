"""
Planet and sector models based on GALPLNT and GALSECT structures
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, BigInteger, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from .associations import planet_items


class Sector(Base):
    """Galaxy sector model based on GALSECT structure"""
    __tablename__ = "sectors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Sector coordinates (from GALSECT)
    xsect = Column(Integer, nullable=False)  # GALSECT.xsect - sector x coord
    ysect = Column(Integer, nullable=False)  # GALSECT.ysect - sector y coord
    plnum = Column(Integer, default=0)       # GALSECT.plnum - always 0
    type = Column(Integer, default=1)        # GALSECT.type - type of sector (SECTYPE_NORMAL=1)
    
    # Planetary objects in this sector
    num_planets = Column(Integer, default=0)  # GALSECT.numplan - number of planetary objects
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    planets = relationship("Planet", back_populates="sector")
    
    def __repr__(self):
        return f"<Sector(xsect={self.xsect}, ysect={self.ysect}, num_planets={self.num_planets})>"


class Planet(Base):
    """Planet model based on GALPLNT structure"""
    __tablename__ = "planets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Sector information (from GALPLNT)
    sector_id = Column(Integer, ForeignKey("sectors.id"))
    xsect = Column(Integer, nullable=False)  # GALPLNT.xsect - sector x coord
    ysect = Column(Integer, nullable=False)  # GALPLNT.ysect - sector y coord
    plnum = Column(Integer, nullable=False)  # GALPLNT.plnum - planet number
    type = Column(Integer, default=2)        # GALPLNT.type - type of sector (PLTYPE_PLNT=2)
    
    # Position (from GALPLNT.coord)
    x_coord = Column(Float, default=0.0)     # GALPLNT.coord.xcoord
    y_coord = Column(Float, default=0.0)     # GALPLNT.coord.ycoord
    
    # Planet ownership (from GALPLNT)
    owner_id = Column(Integer, ForeignKey("users.id"))
    userid = Column(String(25), nullable=False)  # GALPLNT.userid
    name = Column(String(20), nullable=False)    # GALPLNT.name
    
    # Planet characteristics (from GALPLNT)
    environment = Column(Integer, default=0)     # GALPLNT.enviorn - environment factor
    resource = Column(Integer, default=0)        # GALPLNT.resource - resources
    
    # Financial data (from GALPLNT)
    cash = Column(BigInteger, default=0)         # GALPLNT.cash - cash on hand
    debt = Column(BigInteger, default=0)         # GALPLNT.debt - amount owed
    tax = Column(BigInteger, default=0)          # GALPLNT.tax - tax collected
    tax_rate = Column(Integer, default=0)        # GALPLNT.taxrate - tax rate
    
    # Planet management (from GALPLNT)
    warnings = Column(Integer, default=0)        # GALPLNT.warnings - warnings to intruders
    password = Column(String(10), default="")    # GALPLNT.password - alliance password
    last_attacker = Column(String(25), default="")  # GALPLNT.lastattack - last attacker userid
    spy_owner = Column(String(25), default="")   # GALPLNT.spyowner
    technology = Column(Integer, default=0)      # GALPLNT.technology
    team_code = Column(BigInteger, default=0)    # GALPLNT.teamcode
    
    # Beacon message (from GALPLNT.beacon)
    beacon_message = Column(String(75), default="")  # GALPLNT.beacon[BEACONMSGSZ]
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_attack = Column(DateTime(timezone=True))
    
    # Relationships
    sector = relationship("Sector", back_populates="planets")
    owner = relationship("User", back_populates="planets_owned")
    items = relationship("Item", secondary=planet_items, back_populates="planets")
    
    def __repr__(self):
        return f"<Planet(name='{self.name}', owner='{self.userid}', sector=({self.xsect},{self.ysect}))>"


class PlanetItem(Base):
    """Planet item inventory model"""
    __tablename__ = "planet_item_inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    planet_id = Column(Integer, ForeignKey("planets.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    
    # Item quantities and settings (from ITEM structure)
    quantity = Column(BigInteger, default=0)     # ITEM.qty - quantity on hand
    rate = Column(Integer, default=0)            # ITEM.rate - rate of manufacture
    sell_to_allies = Column(Boolean, default=False)  # ITEM.sell - sell to allies?
    reserve = Column(Integer, default=0)         # ITEM.reserve - qty to reserve
    markup_to_allies = Column(Integer, default=0)    # ITEM.markup2a - markup to allies
    sold_to_allies = Column(BigInteger, default=0)   # ITEM.sold2a - # sold to allies
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    planet = relationship("Planet")
    item = relationship("Item")
    
    def __repr__(self):
        return f"<PlanetItem(planet_id={self.planet_id}, item_id={self.item_id}, qty={self.quantity})>"
