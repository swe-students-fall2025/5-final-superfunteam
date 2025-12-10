#!/bin/bash
set -e

echo "🚀 Starting deployment to Digital Ocean droplet..."

# Navigate to application directory
cd /opt/nyu-study-spaces

# Pull latest changes
echo "📥 Pulling latest code from GitHub..."
git pull origin main

# Pull latest Docker images
echo "🐳 Pulling latest Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Stop existing containers
echo "⏹️  Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Start containers with latest images
echo "▶️  Starting containers..."
docker-compose -f docker-compose.prod.yml up -d

# Clean up old images
echo "🧹 Cleaning up old Docker images..."
docker system prune -f

# Check container health
echo "🏥 Checking container health..."
sleep 5
docker-compose -f docker-compose.prod.yml ps

echo "✅ Deployment complete!"
echo "📊 Application status:"
docker-compose -f docker-compose.prod.yml logs --tail=20 webapp
