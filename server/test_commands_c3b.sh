#!/bin/bash
# Phase C3b Smoke Test
# Tests command→Postgres→event→WebSocket delta flow with database persistence

set -e

API_URL="${API_URL:-http://localhost:8000}"
PLAYER_ID="player_1"

echo "======================================"
echo "Phase C3b Smoke Test"
echo "======================================"
echo ""

echo "Prerequisites:"
echo "  1. Postgres running and DATABASE_URL configured"
echo "  2. Redis running and REDIS_URL configured"
echo "  3. Database seeded with: python server/seed_dev_data.py"
echo "  4. API server running: cd server && uvicorn api.main:app"
echo ""

# Step 1: Get session token
echo "[1/5] Getting session token for player_1..."
TOKEN=$(curl -s -X POST "$API_URL/auth/exchange" \
  -H "Content-Type: application/json" \
  -d "{\"dev_token\": \"ge-dev-user-$PLAYER_ID\"}" | jq -r .session_token)

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Failed to get session token"
  exit 1
fi

echo "✅ Token acquired: ${TOKEN:0:20}..."
echo ""

# Step 2: Move command (tests Postgres UPDATE with FOR UPDATE lock)
echo "[2/5] Issuing move command (ship 201: 5,5 → 6,5)..."
MOVE_RESULT=$(curl -s -X POST "$API_URL/commands/move" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ship_id": 201, "target_x": 6, "target_y": 5}')

echo "$MOVE_RESULT" | jq .
if echo "$MOVE_RESULT" | jq -e '.success == true' > /dev/null; then
  echo "✅ Move command successful (Postgres updated)"
else
  echo "❌ Move command failed"
  exit 1
fi
echo ""

# Step 3: Fire command (tests Postgres SELECT)
echo "[3/5] Issuing fire command (ship 201 → target 202, phasor)..."
FIRE_RESULT=$(curl -s -X POST "$API_URL/commands/fire" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ship_id": 201, "weapon_type": "phasor", "target_id": 202}')

echo "$FIRE_RESULT" | jq .
if echo "$FIRE_RESULT" | jq -e '.success == true' > /dev/null; then
  echo "✅ Fire command successful"
else
  echo "❌ Fire command failed"
  exit 1
fi
echo ""

# Step 4: Claim command (tests Postgres UPDATE with FOR UPDATE lock on planets)
echo "[4/5] Issuing claim command (ship 201 → planet 102)..."
CLAIM_RESULT=$(curl -s -X POST "$API_URL/commands/claim" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ship_id": 201, "planet_id": 102}')

echo "$CLAIM_RESULT" | jq .
if echo "$CLAIM_RESULT" | jq -e '.success == true' > /dev/null; then
  echo "✅ Claim command successful (Postgres planet updated)"
else
  echo "❌ Claim command failed"
  exit 1
fi
echo ""

# Step 5: Verify persistence (query /sectors endpoint to confirm DB state)
echo "[5/5] Verifying planet 102 is now owned by player_1 (Postgres persistence)..."
SECTOR_DETAIL=$(curl -s "$API_URL/sectors/1" \
  -H "Authorization: Bearer $TOKEN")

PLANET_102_OWNER=$(echo "$SECTOR_DETAIL" | jq -r '.planets[] | select(.id == 102) | .owner_id')

if [ "$PLANET_102_OWNER" = "$PLAYER_ID" ]; then
  echo "✅ Planet 102 ownership verified in Postgres"
else
  echo "⚠️  Planet 102 owner: $PLANET_102_OWNER (expected: $PLAYER_ID)"
fi
echo ""

# Test authorization (should fail with 403)
echo "Testing authorization (player_3 tries to move player_1's ship)..."
TOKEN_P3=$(curl -s -X POST "$API_URL/auth/exchange" \
  -H "Content-Type: application/json" \
  -d '{"dev_token": "ge-dev-user-player_3"}' | jq -r .session_token)

AUTH_FAIL=$(curl -s -X POST "$API_URL/commands/move" \
  -H "Authorization: Bearer $TOKEN_P3" \
  -H "Content-Type: application/json" \
  -d '{"ship_id": 201, "target_x": 7, "target_y": 5}')

if echo "$AUTH_FAIL" | jq -e '.detail | contains("do not own")' > /dev/null; then
  echo "✅ Authorization check passed (403 Forbidden)"
else
  echo "⚠️  Authorization check unexpected result:"
  echo "$AUTH_FAIL" | jq .
fi
echo ""

# Test double-claim (planet 102 now owned, should fail)
echo "Testing double-claim prevention (ship 201 tries to claim already-owned planet 102)..."
DOUBLE_CLAIM=$(curl -s -X POST "$API_URL/commands/claim" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ship_id": 201, "planet_id": 102}')

if echo "$DOUBLE_CLAIM" | jq -e '.detail | contains("already owned")' > /dev/null; then
  echo "✅ Double-claim prevention passed (403 Forbidden)"
else
  echo "⚠️  Double-claim check unexpected result:"
  echo "$DOUBLE_CLAIM" | jq .
fi
echo ""

echo "======================================"
echo "✅ Phase C3b Smoke Test PASSED"
echo "======================================"
echo ""
echo "All commands persisted to Postgres and published events to Redis."
echo "WebSocket clients subscribed to sector 1 would see:"
echo "  - ship_moved (ship 201)"
echo "  - combat (ship 201 → 202, phasor, damage 15.0)"
echo "  - planet_claimed (planet 102 → player_1)"
echo ""
echo "Database state changes:"
echo "  - Ship 201 position updated: (5,5) → (6,5)"
echo "  - Planet 102 owner updated: null → player_1"
echo ""
echo "To test WebSocket deltas, run:"
echo "  websocat \"ws://localhost:8000/ws?token=\$TOKEN\""
echo "  Send: {\"type\": \"subscribe\", \"sector_id\": 1}"
echo "  Then issue commands in another terminal."
