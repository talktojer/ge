"""
Initialize ship types and classes data
This script populates the database with the default ship configuration from the original game
"""

from sqlalchemy.orm import Session
from app.core.ship_service import ShipConfigurationService, ShipTypeService, ShipClassService
from app.core.database import SessionLocal


def init_ship_system():
    """Initialize the complete ship system with all ship types and classes"""
    db = SessionLocal()
    try:
        ship_config_service = ShipConfigurationService(db)
        
        print("Initializing ship types...")
        ship_config_service.initialize_default_ship_types()
        
        print("Initializing ship classes...")
        ship_config_service.initialize_default_ship_classes()
        
        print("Ship system initialization completed successfully!")
        
        # Verify the data was created
        ship_type_service = ShipTypeService(db)
        ship_class_service = ShipClassService(db)
        
        ship_types = ship_type_service.get_all_ship_types()
        ship_classes = ship_class_service.get_all_ship_classes()
        
        print(f"Created {len(ship_types)} ship types:")
        for ship_type in ship_types:
            print(f"  - {ship_type.type_name}: {ship_type.description}")
        
        print(f"Created {len(ship_classes)} ship classes:")
        for ship_class in ship_classes:
            print(f"  - Class {ship_class.class_number}: {ship_class.typename} ({ship_class.ship_type.type_name})")
        
    except Exception as e:
        print(f"Error initializing ship system: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_complete_ship_classes():
    """Create all 12 ship classes from the original game configuration"""
    db = SessionLocal()
    try:
        ship_config_service = ShipConfigurationService(db)
        
        # Get ship types
        ship_type_service = ShipTypeService(db)
        user_type = ship_type_service.get_ship_type_by_name("USER")
        cyborg_type = ship_type_service.get_ship_type_by_name("CYBORG")
        droid_type = ship_type_service.get_ship_type_by_name("DROID")
        
        if not all([user_type, cyborg_type, droid_type]):
            raise ValueError("Ship types must exist before creating ship classes")
        
        # Complete ship classes configuration based on MBMGESHP.MSG
        complete_ship_classes = [
            # USER Ships (Classes 1-8)
            {
                "class_number": 1, "typename": "Interceptor", "shipname": "",
                "ship_type_id": user_type.id, "max_shields": 10, "max_phasers": 10,
                "max_torpedoes": 1, "max_missiles": 0, "has_decoy": True, "has_jammer": True,
                "has_zipper": True, "has_mine": True, "has_attack_planet": False,
                "has_cloaking": False, "max_acceleration": 5000, "max_warp": 10,
                "max_tons": 1000, "max_price": 65000, "max_points": 750,
                "scan_range": 100000, "cybs_can_attack": True, "number_to_attack": 1,
                "damage_factor": 90, "total_to_create": 3
            },
            {
                "class_number": 2, "typename": "Stealth Fighter", "shipname": "",
                "ship_type_id": user_type.id, "max_shields": 15, "max_phasers": 15,
                "max_torpedoes": 1, "max_missiles": 1, "has_decoy": True, "has_jammer": True,
                "has_zipper": True, "has_mine": True, "has_attack_planet": True,
                "has_cloaking": True, "max_acceleration": 5000, "max_warp": 20,
                "max_tons": 2000, "max_price": 500000, "max_points": 1500,
                "scan_range": 200000, "cybs_can_attack": True, "number_to_attack": 2,
                "damage_factor": 90, "total_to_create": 3
            },
            {
                "class_number": 3, "typename": "Heavy Freighter", "shipname": "",
                "ship_type_id": user_type.id, "max_shields": 5, "max_phasers": 5,
                "max_torpedoes": 1, "max_missiles": 0, "has_decoy": True, "has_jammer": True,
                "has_zipper": False, "has_mine": True, "has_attack_planet": True,
                "has_cloaking": False, "max_acceleration": 3000, "max_warp": 8,
                "max_tons": 60000, "max_price": 40000, "max_points": 500,
                "scan_range": 50000, "cybs_can_attack": False, "number_to_attack": 0,
                "damage_factor": 200, "total_to_create": 3
            },
            {
                "class_number": 4, "typename": "Destroyer", "shipname": "",
                "ship_type_id": user_type.id, "max_shields": 15, "max_phasers": 15,
                "max_torpedoes": 1, "max_missiles": 1, "has_decoy": True, "has_jammer": True,
                "has_zipper": True, "has_mine": True, "has_attack_planet": True,
                "has_cloaking": False, "max_acceleration": 5000, "max_warp": 25,
                "max_tons": 5000, "max_price": 600000, "max_points": 2000,
                "scan_range": 100000, "cybs_can_attack": True, "number_to_attack": 2,
                "damage_factor": 90, "total_to_create": 3
            },
            {
                "class_number": 5, "typename": "Star Cruiser", "shipname": "",
                "ship_type_id": user_type.id, "max_shields": 15, "max_phasers": 15,
                "max_torpedoes": 1, "max_missiles": 1, "has_decoy": True, "has_jammer": True,
                "has_zipper": True, "has_mine": True, "has_attack_planet": True,
                "has_cloaking": True, "max_acceleration": 10000, "max_warp": 25,
                "max_tons": 3000, "max_price": 700000, "max_points": 5000,
                "scan_range": 200000, "cybs_can_attack": True, "number_to_attack": 2,
                "damage_factor": 90, "total_to_create": 3
            },
            {
                "class_number": 6, "typename": "Battleship", "shipname": "",
                "ship_type_id": user_type.id, "max_shields": 18, "max_phasers": 18,
                "max_torpedoes": 1, "max_missiles": 1, "has_decoy": True, "has_jammer": True,
                "has_zipper": True, "has_mine": True, "has_attack_planet": True,
                "has_cloaking": False, "max_acceleration": 3000, "max_warp": 15,
                "max_tons": 8000, "max_price": 1200000, "max_points": 8000,
                "scan_range": 150000, "cybs_can_attack": True, "number_to_attack": 3,
                "damage_factor": 90, "total_to_create": 3
            },
            {
                "class_number": 7, "typename": "Dreadnought", "shipname": "",
                "ship_type_id": user_type.id, "max_shields": 19, "max_phasers": 19,
                "max_torpedoes": 1, "max_missiles": 1, "has_decoy": True, "has_jammer": True,
                "has_zipper": True, "has_mine": True, "has_attack_planet": True,
                "has_cloaking": False, "max_acceleration": 2000, "max_warp": 12,
                "max_tons": 12000, "max_price": 2000000, "max_points": 15000,
                "scan_range": 120000, "cybs_can_attack": True, "number_to_attack": 3,
                "damage_factor": 90, "total_to_create": 2
            },
            {
                "class_number": 8, "typename": "Flagship", "shipname": "",
                "ship_type_id": user_type.id, "max_shields": 19, "max_phasers": 19,
                "max_torpedoes": 1, "max_missiles": 1, "has_decoy": True, "has_jammer": True,
                "has_zipper": True, "has_mine": True, "has_attack_planet": True,
                "has_cloaking": True, "max_acceleration": 1500, "max_warp": 10,
                "max_tons": 15000, "max_price": 5000000, "max_points": 30000,
                "scan_range": 100000, "cybs_can_attack": True, "number_to_attack": 4,
                "damage_factor": 90, "total_to_create": 1
            },
            # CYBORG Ships (Classes 9-10)
            {
                "class_number": 9, "typename": "Cyber-Destroyer", "shipname": "Cyber-Destroyer",
                "ship_type_id": cyborg_type.id, "max_shields": 15, "max_phasers": 15,
                "max_torpedoes": 1, "max_missiles": 1, "has_decoy": True, "has_jammer": True,
                "has_zipper": True, "has_mine": True, "has_attack_planet": True,
                "has_cloaking": False, "max_acceleration": 6000, "max_warp": 30,
                "max_tons": 3000, "max_price": 0, "max_points": 2500,
                "scan_range": 150000, "cybs_can_attack": False, "number_to_attack": 0,
                "lowest_to_attack": 1, "damage_factor": 95, "tough_factor": 0,
                "total_to_create": 5
            },
            {
                "class_number": 10, "typename": "Cyber-Cruiser", "shipname": "Cyber-Cruiser",
                "ship_type_id": cyborg_type.id, "max_shields": 18, "max_phasers": 18,
                "max_torpedoes": 1, "max_missiles": 1, "has_decoy": True, "has_jammer": True,
                "has_zipper": True, "has_mine": True, "has_attack_planet": True,
                "has_cloaking": True, "max_acceleration": 8000, "max_warp": 35,
                "max_tons": 2000, "max_price": 0, "max_points": 5000,
                "scan_range": 200000, "cybs_can_attack": False, "number_to_attack": 0,
                "lowest_to_attack": 3, "damage_factor": 100, "tough_factor": 1,
                "total_to_create": 3
            },
            # DROID Ships (Classes 11-12)
            {
                "class_number": 11, "typename": "Mining Droid", "shipname": "Mining Droid",
                "ship_type_id": droid_type.id, "max_shields": 2, "max_phasers": 2,
                "max_torpedoes": 0, "max_missiles": 0, "has_decoy": False, "has_jammer": False,
                "has_zipper": False, "has_mine": False, "has_attack_planet": False,
                "has_cloaking": False, "max_acceleration": 1000, "max_warp": 5,
                "max_tons": 50000, "max_price": 0, "max_points": 100,
                "scan_range": 25000, "cybs_can_attack": False, "number_to_attack": 0,
                "damage_factor": 50, "total_to_create": 10
            },
            {
                "class_number": 12, "typename": "Scout Droid", "shipname": "Scout Droid",
                "ship_type_id": droid_type.id, "max_shields": 1, "max_phasers": 1,
                "max_torpedoes": 0, "max_missiles": 0, "has_decoy": False, "has_jammer": False,
                "has_zipper": False, "has_mine": False, "has_attack_planet": False,
                "has_cloaking": True, "max_acceleration": 8000, "max_warp": 40,
                "max_tons": 100, "max_price": 0, "max_points": 50,
                "scan_range": 300000, "cybs_can_attack": False, "number_to_attack": 0,
                "damage_factor": 25, "total_to_create": 15
            }
        ]
        
        ship_class_service = ShipClassService(db)
        
        for class_data in complete_ship_classes:
            existing = ship_class_service.get_ship_class_by_number(class_data["class_number"])
            if not existing:
                ship_class_service.create_ship_class(class_data)
                print(f"Created ship class {class_data['class_number']}: {class_data['typename']}")
            else:
                print(f"Ship class {class_data['class_number']} already exists")
        
        db.commit()
        print(f"Successfully created/verified {len(complete_ship_classes)} ship classes")
        
    except Exception as e:
        print(f"Error creating ship classes: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing complete ship system...")
    init_ship_system()
    create_complete_ship_classes()
    print("Ship system initialization complete!")
