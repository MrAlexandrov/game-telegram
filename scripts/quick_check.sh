#!/bin/bash
# Quick system health check script

set -e

echo "🔍 Game Telegram - Quick System Check"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    
    if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name (port $port): Running${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name (port $port): Not responding${NC}"
        return 1
    fi
}

# Function to check if a port is open
check_port() {
    local port=$1
    local service_name=$2
    
    if nc -z localhost $port 2>/dev/null; then
        echo -e "${GREEN}✅ $service_name (port $port): Port open${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name (port $port): Port closed${NC}"
        return 1
    fi
}

# Check if Docker is running
echo "🐳 Checking Docker..."
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker: Running${NC}"
else
    echo -e "${RED}❌ Docker: Not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

# Check if Docker Compose services are running
echo ""
echo "📦 Checking Docker Compose services..."
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Docker Compose: Services running${NC}"
    
    # Show running services
    echo "Running services:"
    docker-compose ps | grep -E "(Up|running)"
else
    echo -e "${YELLOW}⚠️ Docker Compose: No services running${NC}"
    echo "Run 'docker-compose up -d' to start services"
fi

echo ""
echo "🌐 Checking service endpoints..."

# Check core services
services_ok=0
total_services=0

# Game Engine
total_services=$((total_services + 1))
if check_service "Game Engine" 8002; then
    services_ok=$((services_ok + 1))
fi

# Session Manager  
total_services=$((total_services + 1))
if check_service "Session Manager" 8003; then
    services_ok=$((services_ok + 1))
fi

# User Manager
total_services=$((total_services + 1))
if check_service "User Manager" 8004; then
    services_ok=$((services_ok + 1))
fi

# Analytics Service
total_services=$((total_services + 1))
if check_service "Analytics Service" 8005; then
    services_ok=$((services_ok + 1))
fi

# Notification Service
total_services=$((total_services + 1))
if check_service "Notification Service" 8006; then
    services_ok=$((services_ok + 1))
fi

echo ""
echo "🗄️ Checking infrastructure services..."

# PostgreSQL
if check_port 5432 "PostgreSQL"; then
    # Try to connect to database
    if command -v psql > /dev/null 2>&1; then
        if psql "${DATABASE_URL:-postgresql://gameuser:password@localhost:5432/gamedb}" -c "SELECT 1;" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ PostgreSQL: Connection successful${NC}"
        else
            echo -e "${YELLOW}⚠️ PostgreSQL: Port open but connection failed${NC}"
        fi
    fi
fi

# Redis
if check_port 6379 "Redis"; then
    # Try to ping Redis
    if command -v redis-cli > /dev/null 2>&1; then
        if redis-cli ping > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Redis: Connection successful${NC}"
        else
            echo -e "${YELLOW}⚠️ Redis: Port open but connection failed${NC}"
        fi
    fi
fi

echo ""
echo "📊 Summary"
echo "=========="

if [ $services_ok -eq $total_services ]; then
    echo -e "${GREEN}🎉 All services are running! ($services_ok/$total_services)${NC}"
    echo ""
    echo "🚀 System is ready for use!"
    echo "   • Admin Bot: Check your Telegram admin bot"
    echo "   • Player Bot: Check your Telegram player bot"  
    echo "   • API Docs: http://localhost:8002/docs"
    echo "   • Monitoring: http://localhost:3000 (if Grafana is running)"
    exit 0
elif [ $services_ok -gt 0 ]; then
    echo -e "${YELLOW}⚠️ Some services are running ($services_ok/$total_services)${NC}"
    echo ""
    echo "🔧 To start all services:"
    echo "   docker-compose up -d"
    exit 1
else
    echo -e "${RED}❌ No services are running ($services_ok/$total_services)${NC}"
    echo ""
    echo "🔧 To start the system:"
    echo "   1. Make sure Docker is running"
    echo "   2. Run: docker-compose up -d"
    echo "   3. Wait a few moments for services to start"
    echo "   4. Run this check again"
    exit 2
fi