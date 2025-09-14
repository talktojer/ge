"""
Item/commodity system models based on ITEM structure
"""

from sqlalchemy import Column, Integer, String, BigInteger, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class ItemType(Base):
    """Item type definitions based on original NUMITEMS (14 item types)"""
    __tablename__ = "item_types"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Item identification
    name = Column(String(50), nullable=False, unique=True)
    keyword = Column(String(20), nullable=False, unique=True)  # from kwrd[NUMITEMS]
    description = Column(Text)
    
    # Item properties (from original constants)
    base_price = Column(BigInteger, default=0)     # baseprice[NUMITEMS]
    max_quantity = Column(Float, default=0.0)      # maxpl[NUMITEMS] 
    weight = Column(BigInteger, default=0)         # weight[NUMITEMS]
    value = Column(BigInteger, default=0)          # value[NUMITEMS]
    man_hours = Column(BigInteger, default=0)      # manhours[NUMITEMS]
    
    # Item category
    category = Column(String(50), default="general")
    is_consumable = Column(Boolean, default=False)
    is_weapon = Column(Boolean, default=False)
    is_equipment = Column(Boolean, default=False)
    is_resource = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    items = relationship("Item", back_populates="item_type")
    planets = relationship("Planet", secondary="planet_items", back_populates="items")
    
    def __repr__(self):
        return f"<ItemType(name='{self.name}', keyword='{self.keyword}')>"


class Item(Base):
    """Item inventory model based on ITEM structure"""
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Item identification
    item_type_id = Column(Integer, ForeignKey("item_types.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))  # Can be owned by user or planet
    
    # Item quantities and settings (from ITEM structure)
    quantity = Column(BigInteger, default=0)     # ITEM.qty - quantity on hand
    rate = Column(Integer, default=0)            # ITEM.rate - rate of manufacture
    sell_to_allies = Column(Boolean, default=False)  # ITEM.sell - sell to allies?
    reserve = Column(Integer, default=0)         # ITEM.reserve - qty to reserve
    markup_to_allies = Column(Integer, default=0)    # ITEM.markup2a - markup to allies
    sold_to_allies = Column(BigInteger, default=0)   # ITEM.sold2a - # sold to allies
    
    # Item location
    location_type = Column(String(20), default="user")  # "user", "planet", "ship"
    location_id = Column(Integer, default=0)  # ID of the location (user_id, planet_id, ship_id)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    item_type = relationship("ItemType", back_populates="items")
    owner = relationship("User")
    planets = relationship("Planet", secondary="planet_items", back_populates="items")
    
    def __repr__(self):
        return f"<Item(item_type_id={self.item_type_id}, quantity={self.quantity}, location={self.location_type})>"


# Item type constants from original code (NUMITEMS = 14)
class ItemConstants:
    MEN = 0           # I_MEN
    MISSILE = 1       # I_MISSILE
    TORPEDO = 2       # I_TORPEDO
    IONCANNON = 3     # I_IONCANNON
    FLUXPOD = 4       # I_FLUXPOD
    FOOD = 5          # I_FOOD
    FIGHTER = 6       # I_FIGHTER
    DECOYS = 7        # I_DECOYS
    TROOPS = 8        # I_TROOPS
    ZIPPERS = 9       # I_ZIPPERS
    JAMMERS = 10      # I_JAMMERS
    MINE = 11         # I_MINE
    GOLD = 12         # I_GOLD
    SPY = 13          # I_SPY
    
    # Item names from original code
    NAMES = [
        "Men", "Missile", "Torpedo", "Ion Cannon",
        "Flux Pod", "Food", "Fighter", "Decoys", 
        "Troops", "Zippers", "Jammers", "Mine",
        "Gold", "Spy"
    ]
    
    # Item keywords from original code
    KEYWORDS = [
        "men", "missile", "torpedo", "ioncannon",
        "fluxpod", "food", "fighter", "decoys",
        "troops", "zippers", "jammers", "mine", 
        "gold", "spy"
    ]
