#!/usr/bin/env python3
"""
Script to populate basic ship data for MVP testing
"""

import sys
import os
sys.path.append('/app')

from app.core.database import get_db
from app.models.ship import ShipType, ShipClass
from sqlalchemy.orm import Session

def populate_basic_ship_data():
    """Create basic ship types and classes for MVP testing"""
    db = next(get_db())
    
    try:
        # Create ship types
        user_type = ShipType(typename="USER", shipname="Player Ships")
        cyborg_type = ShipType(typename="CYBORG", shipname="Cyborg Ships")
        droid_type = ShipType(typename="DROID", shipname="Droid Ships")
        
        db.add(user_type)
        db.add(cyborg_type)
        db.add(droid_type)
        db.commit()
        
        print("Created ship types: USER, CYBORG, DROID")
        
        # Create basic ship classes
        ship_classes = [
            ShipClass(
                class_number=1,
                name="Interceptor",
                description="Fast, light combat ship",
                ship_type_id=user_type.id,
                is_available=True
            ),
            ShipClass(
                class_number=2,
                name="Destroyer",
                description="Heavy combat ship",
                ship_type_id=user_type.id,
                is_available=True
            ),
            ShipClass(
                class_number=3,
                name="Cruiser",
                description="Balanced combat ship",
                ship_type_id=user_type.id,
                is_available=True
            )
        ]
        
        for ship_class in ship_classes:
            db.add(ship_class)
        
        db.commit()
        print(f"Created {len(ship_classes)} ship classes")
        
        print("✓ Basic ship data populated successfully!")
        
    except Exception as e:
        print(f"Error populating ship data: {e}")
        db.rollback()
        raise

if __name__ == "__main__":
    populate_basic_ship_data()
