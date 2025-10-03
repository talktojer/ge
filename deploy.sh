#!/bin/bash

# Galactic Empire Production Deployment Script
# This script sets up and deploys the Galactic Empire game in production

set -e

echo "🚀 Starting Galactic Empire Production Deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "⚠️  .env.prod not found. Creating from example..."
    cp env.prod.example .env.prod
    echo "📝 Please edit .env.prod with your production values before continuing."
    echo "   Important: Change all passwords and secret keys!"
    read -p "Press Enter when you've updated .env.prod..."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p nginx/logs
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources
mkdir -p backend/logs

# Set proper permissions
echo "🔐 Setting proper permissions..."
chmod 755 deploy.sh
chmod 644 docker-compose.prod.yml
chmod 644 nginx/nginx.conf

# Build and start services
echo "🔨 Building and starting services..."
docker-compose -f docker-compose.prod.yml down --remove-orphans
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🏥 Checking service health..."
services=("postgres" "redis" "backend" "frontend" "nginx")

for service in "${services[@]}"; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "${service}.*Up"; then
        echo "✅ ${service} is running"
    else
        echo "❌ ${service} is not running"
        echo "📋 Checking logs for ${service}:"
        docker-compose -f docker-compose.prod.yml logs --tail=20 ${service}
    fi
done

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Initialize game data
echo "🎮 Initializing game data..."
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.core.init_ship_data import initialize_ship_data
from app.core.database import get_db
from sqlalchemy.orm import Session

db = next(get_db())
initialize_ship_data(db)
print('Ship data initialized successfully')
"

# Display deployment information
echo ""
echo "🎉 Galactic Empire has been deployed successfully!"
echo ""
echo "📊 Service URLs:"
echo "   Game Frontend: http://localhost:3000"
echo "   API Backend:   http://localhost:8000"
echo "   Grafana:       http://localhost:3001"
echo "   Prometheus:    http://localhost:9090"
echo ""
echo "🔧 Management Commands:"
echo "   View logs:     docker-compose -f docker-compose.prod.yml logs -f [service]"
echo "   Stop services: docker-compose -f docker-compose.prod.yml down"
echo "   Restart:       docker-compose -f docker-compose.prod.yml restart [service]"
echo "   Update:        ./deploy.sh"
echo ""
echo "📋 Default Credentials:"
echo "   Grafana Admin: admin / (check .env.prod for GRAFANA_PASSWORD)"
echo ""
echo "⚠️  Remember to:"
echo "   1. Change all default passwords"
echo "   2. Configure SSL certificates for HTTPS"
echo "   3. Set up proper firewall rules"
echo "   4. Configure backup strategies"
echo ""
echo "🚀 Deployment complete! The game is now running in production mode."
