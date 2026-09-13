#!/bin/bash
# Setup script for Phase C3 database (run inside Docker container)
# Usage: docker exec ge-api-dev bash /app/setup_c3_db.sh

set -e

echo "🔧 Phase C3 Database Setup"
echo "=========================="

# Check if Postgres is ready
echo "1. Checking Postgres connection..."
if ! pg_isready -h postgres -U postgres -d galactic_empire > /dev/null 2>&1; then
    echo "❌ Postgres not ready. Make sure docker-compose is running."
    exit 1
fi
echo "✅ Postgres is ready"

# Run migrations
echo ""
echo "2. Running Alembic migrations..."
cd /app
PYTHONPATH=/app python3 -m alembic upgrade head
echo "✅ Migrations applied"

# Seed data
echo ""
echo "3. Seeding test data..."
PYTHONPATH=/app python3 seed_data.py
echo "✅ Database seeded"

echo ""
echo "=========================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Restart ge-sim: docker-compose restart ge-sim"
echo "  2. Watch logs: docker logs -f ge-sim-dev"
echo "  3. Test REST API: curl -H 'Authorization: Bearer ge-dev-user-alice' http://localhost:8000/sectors/1"
echo "  4. Test WebSocket: See docs/PHASE_C3_SIM_POSTGRES.md for examples"
