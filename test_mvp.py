#!/usr/bin/env python3
"""
Test script to verify MVP functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:18000"

def test_api_status():
    """Test basic API status"""
    print("Testing API status...")
    response = requests.get(f"{BASE_URL}/api/status")
    if response.status_code == 200:
        print("✓ API is running")
        return True
    else:
        print(f"✗ API failed: {response.status_code}")
        return False

def test_game_engine_status():
    """Test game engine status"""
    print("Testing game engine status...")
    response = requests.get(f"{BASE_URL}/api/game-engine/status")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Game engine running: {data['game_running']}")
        print(f"  Tick number: {data['tick_number']}")
        print(f"  Total ships: {data['total_ships']}")
        return True
    else:
        print(f"✗ Game engine failed: {response.status_code}")
        return False

def test_user_registration():
    """Test user registration"""
    print("Testing user registration...")
    test_user = {
        "username": "mvptest",
        "email": "mvptest@example.com",
        "password": "testpass123",
        "confirm_password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/api/users/register", json=test_user)
    if response.status_code == 200:
        print("✓ User registration successful")
        return True
    else:
        print(f"✗ User registration failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return False

def test_user_login():
    """Test user login"""
    print("Testing user login...")
    login_data = {
        "username": "mvptest",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/api/users/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print("✓ User login successful")
        return token
    else:
        print(f"✗ User login failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def test_game_state(token):
    """Test game state endpoint"""
    print("Testing game state...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/users/game-state", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("✓ Game state retrieved successfully")
        print(f"  User: {data['current_user']['userid']}")
        print(f"  Game time: {data['game_time']}")
        print(f"  Tick number: {data['tick_number']}")
        print(f"  Selected ship: {data['selected_ship']}")
        print(f"  Connected: {data['is_connected']}")
        return True
    else:
        print(f"✗ Game state failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return False

def main():
    """Run all tests"""
    print("=== Galactic Empire MVP Test ===")
    print()
    
    # Test 1: API Status
    if not test_api_status():
        return False
    print()
    
    # Test 2: Game Engine Status
    if not test_game_engine_status():
        return False
    print()
    
    # Test 3: User Registration
    if not test_user_registration():
        return False
    print()
    
    # Test 4: User Login
    token = test_user_login()
    if not token:
        return False
    print()
    
    # Test 5: Game State (this should create a starter ship)
    if not test_game_state(token):
        return False
    print()
    
    print("=== All tests passed! MVP is working! ===")
    return True

if __name__ == "__main__":
    main()

