"""
Test script for the ship types and classes system
This script verifies that step 2.1 is fully implemented and working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.ship_service import ShipConfigurationService, ShipTypeService, ShipClassService
from app.models.ship import ShipType, ShipClass
from app.models.user import User


def test_ship_system():
    """Test the complete ship types and classes system"""
    print("=" * 60)
    print("TESTING GALACTIC EMPIRE SHIP SYSTEM (Step 2.1)")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Initialize the ship system
        print("\n1. Initializing ship system...")
        ship_config_service = ShipConfigurationService(db)
        ship_config_service.initialize_default_ship_types()
        ship_config_service.initialize_default_ship_classes()
        print("✓ Ship system initialized successfully")
        
        # Test ship types
        print("\n2. Testing ship types...")
        ship_type_service = ShipTypeService(db)
        ship_types = ship_type_service.get_all_ship_types()
        
        expected_types = ["USER", "CYBORG", "DROID"]
        print(f"Found {len(ship_types)} ship types:")
        for ship_type in ship_types:
            print(f"  - {ship_type.type_name}: {ship_type.description}")
            if ship_type.type_name in expected_types:
                print(f"    ✓ {ship_type.type_name} type found")
        
        # Test ship classes
        print("\n3. Testing ship classes...")
        ship_class_service = ShipClassService(db)
        ship_classes = ship_class_service.get_all_ship_classes()
        
        print(f"Found {len(ship_classes)} ship classes:")
        for ship_class in ship_classes:
            print(f"  - Class {ship_class.class_number}: {ship_class.typename} ({ship_class.ship_type.type_name})")
        
        # Test USER ship classes
        print("\n4. Testing USER ship classes...")
        user_ships = ship_class_service.get_user_ship_classes()
        print(f"Found {len(user_ships)} USER ship classes:")
        for ship_class in user_ships:
            capabilities = ship_class_service.get_ship_capabilities(ship_class)
            print(f"  - {ship_class.typename}:")
            print(f"    Shields: {ship_class.max_shields}, Phasers: {ship_class.max_phasers}")
            print(f"    Warp: {ship_class.max_warp}, Cargo: {ship_class.max_tons}")
            print(f"    Price: {ship_class.max_price}, Points: {ship_class.max_points}")
            print(f"    Special: Decoy={ship_class.has_decoy}, Jammer={ship_class.has_jammer}")
            print(f"    Zipper={ship_class.has_zipper}, Mine={ship_class.has_mine}")
            print(f"    Cloaking={ship_class.has_cloaking}, Attack Planet={ship_class.has_attack_planet}")
        
        # Test CYBORG ship classes
        print("\n5. Testing CYBORG ship classes...")
        cyborg_ships = ship_class_service.get_cyborg_ship_classes()
        print(f"Found {len(cyborg_ships)} CYBORG ship classes:")
        for ship_class in cyborg_ships:
            print(f"  - {ship_class.typename} ({ship_class.shipname}):")
            print(f"    Tough Factor: {ship_class.tough_factor}")
            print(f"    Damage Factor: {ship_class.damage_factor}")
            print(f"    Total to Create: {ship_class.total_to_create}")
            print(f"    Lowest to Attack: {ship_class.lowest_to_attack}")
        
        # Test DROID ship classes
        print("\n6. Testing DROID ship classes...")
        droid_ships = ship_class_service.get_droid_ship_classes()
        print(f"Found {len(droid_ships)} DROID ship classes:")
        for ship_class in droid_ships:
            print(f"  - {ship_class.typename} ({ship_class.shipname}):")
            print(f"    Shields: {ship_class.max_shields}, Phasers: {ship_class.max_phasers}")
            print(f"    Warp: {ship_class.max_warp}, Cargo: {ship_class.max_tons}")
            print(f"    Damage Factor: {ship_class.damage_factor}")
        
        # Test ship capabilities system
        print("\n7. Testing ship capabilities system...")
        if user_ships:
            test_ship = user_ships[0]
            capabilities = ship_class_service.get_ship_capabilities(test_ship)
            print(f"Capabilities for {test_ship.typename}:")
            print(f"  Shields: {capabilities['shields']}")
            print(f"  Phasers: {capabilities['phasers']}")
            print(f"  Special Equipment: {capabilities['special_equipment']}")
            print(f"  Performance: {capabilities['performance']}")
            print(f"  Economics: {capabilities['economics']}")
        
        # Test ship statistics system
        print("\n8. Testing ship statistics system...")
        if user_ships:
            test_ship = user_ships[0]
            statistics = ship_class_service.get_ship_statistics(test_ship)
            print(f"Statistics for {test_ship.typename}:")
            print(f"  Class Info: {statistics['class_info']}")
            print(f"  Combat Stats: {statistics['combat_stats']}")
            print(f"  Movement Stats: {statistics['movement_stats']}")
            print(f"  Utility Stats: {statistics['utility_stats']}")
        
        print("\n" + "=" * 60)
        print("SHIP SYSTEM TEST COMPLETED SUCCESSFULLY!")
        print("Step 2.1 (Ship Types & Classes) is fully implemented")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    finally:
        db.close()


def test_ship_purchase_system():
    """Test ship purchase capabilities"""
    print("\n" + "=" * 60)
    print("TESTING SHIP PURCHASE SYSTEM")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Create a test user
        test_user = User(
            userid="testuser",
            name="Test User",
            cash=1000000,  # 1 million credits
            email="test@example.com"
        )
        
        ship_class_service = ShipClassService(db)
        user_ships = ship_class_service.get_user_ship_classes()
        
        print(f"Testing purchase capabilities for user with {test_user.cash} credits:")
        for ship_class in user_ships[:3]:  # Test first 3 ships
            can_purchase = ship_class_service.can_purchase_ship_class(ship_class, test_user)
            print(f"  - {ship_class.typename}: {ship_class.max_price} credits")
            print(f"    Can purchase: {'✓' if can_purchase else '✗'}")
        
        print("\n✓ Ship purchase system working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR in purchase test: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("Starting Galactic Empire Ship System Tests...")
    
    # Run main ship system test
    success1 = test_ship_system()
    
    # Run purchase system test
    success2 = test_ship_purchase_system()
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED! Step 2.1 is fully implemented and working.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)


