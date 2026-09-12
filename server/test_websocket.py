#!/usr/bin/env python3
"""
Simple WebSocket client test for Phase C2a.
Tests authentication, subscribe, and receiving deltas.
"""
import asyncio
import websockets
import json
import sys

async def test_websocket():
    # Get session token first
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/auth/exchange",
            json={"dev_token": "ge-dev-user-wstest"}
        ) as resp:
            data = await resp.json()
            token = data["session_token"]
            print(f"✓ Got session token: {token[:30]}...")
    
    # Connect to WebSocket with token in query param
    uri = f"ws://localhost:8000/ws?token={token}"
    
    async with websockets.connect(uri) as websocket:
        print("✓ WebSocket connected")
        
        # Should receive authenticated message
        msg = json.loads(await websocket.recv())
        print(f"✓ Received: {msg}")
        assert msg["type"] == "authenticated", f"Expected authenticated, got {msg}"
        
        # Subscribe to sector 1
        await websocket.send(json.dumps({
            "type": "subscribe",
            "sector_id": 1
        }))
        print("✓ Sent subscribe message")
        
        # Should receive subscribed confirmation
        msg = json.loads(await websocket.recv())
        print(f"✓ Received: {msg['type']}")
        assert msg["type"] == "subscribed", f"Expected subscribed, got {msg}"
        
        # Should receive sector snapshot
        msg = json.loads(await websocket.recv())
        print(f"✓ Received: {msg['type']}")
        assert msg["type"] == "sector_snapshot", f"Expected sector_snapshot, got {msg}"
        print(f"  Snapshot data: {len(msg['data']['ships'])} ships, {len(msg['data']['planets'])} planets")
        
        # Wait for first delta (should arrive within 6 seconds)
        print("⏳ Waiting for sector delta (up to 6 seconds)...")
        try:
            msg = json.loads(await asyncio.wait_for(websocket.recv(), timeout=6.5))
            print(f"✓ Received: {msg['type']}")
            assert msg["type"] == "sector_delta", f"Expected sector_delta, got {msg}"
            print(f"  Delta tick: {msg['tick']}, events: {len(msg['events'])}")
            for event in msg['events']:
                print(f"    - {event['event_type']}")
        except asyncio.TimeoutError:
            print("✗ Timeout waiting for delta")
            return False
        
        # Send ping
        await websocket.send(json.dumps({"type": "ping"}))
        msg = json.loads(await websocket.recv())
        print(f"✓ Ping/pong: {msg['type']}")
        assert msg["type"] == "pong", f"Expected pong, got {msg}"
        
        # Unsubscribe
        await websocket.send(json.dumps({
            "type": "unsubscribe",
            "sector_id": 1
        }))
        msg = json.loads(await websocket.recv())
        print(f"✓ Received: {msg['type']}")
        assert msg["type"] == "unsubscribed", f"Expected unsubscribed, got {msg}"
        
        print("\n✓ All WebSocket tests passed!")
        return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_websocket())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
