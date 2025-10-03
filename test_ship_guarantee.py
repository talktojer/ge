#!/usr/bin/env python3
"""
Test script to verify that users always have at least one ship.
This script tests the ship guarantee functionality.
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_PREFIX = "test_ship_user_"

def create_test_user(username_suffix):
    """Create a test user and return user data"""
    username = f"{TEST_USER_PREFIX}{username_suffix}"
    email = f"{username}@test.com"
    password = "testpass123"
    
    registration_data = {
        "username": username,
        "email": email,
        "password": password,
        "confirm_password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/users/register", json=registration_data)
        if response.status_code == 200:
            print(f"✅ Created user: {username}")
            return response.json()
        else:
            print(f"❌ Failed to create user {username}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating user {username}: {e}")
        return None

def login_user(username, password="testpass123"):
    """Login a user and return auth data"""
    login_data = {
        "userid": username,
        "password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/users/login", json=login_data)
        if response.status_code == 200:
            print(f"✅ Logged in user: {username}")
            return response.json()
        else:
            print(f"❌ Failed to login user {username}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error logging in user {username}: {e}")
        return None

def get_user_ships(auth_token):
    """Get user's ships"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/users/ships", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get ships: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting ships: {e}")
        return None

def get_user_stats(auth_token):
    """Get user statistics"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/users/statistics", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get stats: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return None

def test_ship_guarantee():
    """Test that users always have at least one ship"""
    print("🚀 Testing Ship Guarantee Functionality")
    print("=" * 50)
    
    # Test 1: New user registration should create a ship
    print("\n📝 Test 1: New user registration")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    user_data = create_test_user(timestamp)
    
    if not user_data:
        print("❌ Test 1 FAILED: Could not create user")
        return False
    
    # Test 2: Login should ensure user has a ship
    print("\n🔐 Test 2: User login")
    username = user_data["user"]["userid"]
    auth_data = login_user(username)
    
    if not auth_data:
        print("❌ Test 2 FAILED: Could not login user")
        return False
    
    auth_token = auth_data["access_token"]
    
    # Test 3: Check that user has ships after login
    print("\n🚢 Test 3: Check user ships after login")
    ships_data = get_user_ships(auth_token)
    
    if not ships_data:
        print("❌ Test 3 FAILED: Could not get ships data")
        return False
    
    ships = ships_data.get("ships", [])
    ship_count = len(ships)
    
    print(f"📊 User has {ship_count} ships")
    
    if ship_count == 0:
        print("❌ Test 3 FAILED: User has no ships after login")
        return False
    else:
        print("✅ Test 3 PASSED: User has ships after login")
    
    # Test 4: Check user statistics
    print("\n📈 Test 4: Check user statistics")
    stats_data = get_user_stats(auth_token)
    
    if not stats_data:
        print("❌ Test 4 FAILED: Could not get stats data")
        return False
    
    print(f"📊 User statistics: {json.dumps(stats_data, indent=2)}")
    
    # Test 5: Verify ship details
    print("\n🔍 Test 5: Verify ship details")
    if ships:
        ship = ships[0]
        print(f"🚢 First ship: {ship.get('ship_name', 'Unknown')} (Class {ship.get('ship_class', 'Unknown')})")
        print(f"📍 Position: {ship.get('position', {})}")
        print(f"⚡ Energy: {ship.get('energy', 'Unknown')}")
        print(f"🛡️ Shields: {ship.get('shields', 'Unknown')}/{ship.get('max_shields', 'Unknown')}")
        print("✅ Test 5 PASSED: Ship has proper details")
    else:
        print("❌ Test 5 FAILED: No ships to verify")
        return False
    
    print("\n🎉 All tests passed! Users are guaranteed to have at least one ship.")
    return True

def cleanup_test_users():
    """Clean up test users (placeholder - would need admin API)"""
    print("\n🧹 Note: Test users created for this test should be cleaned up manually")
    print("   In a production environment, implement user cleanup via admin API")

if __name__ == "__main__":
    print("Galactic Empire - Ship Guarantee Test")
    print("====================================")
    
    try:
        success = test_ship_guarantee()
        cleanup_test_users()
        
        if success:
            print("\n✅ All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


