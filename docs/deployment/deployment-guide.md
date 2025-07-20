# Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [Local Development Deployment](#local-development-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Production Deployment](#production-deployment)
7. [Kubernetes Deployment](#kubernetes-deployment)
8. [Database Setup](#database-setup)
9. [SSL/TLS Configuration](#ssltls-configuration)
10. [Monitoring Setup](#monitoring-setup)
11. [Backup and Recovery](#backup-and-recovery)
12. [Troubleshooting](#troubleshooting)
13. [Maintenance](#maintenance)

## Overview

This guide provides comprehensive instructions for deploying the Game Telegram system in various environments, from local development to production-ready Kubernetes clusters.

### Deployment Options

| Environment | Use Case | Complexity | Scalability |
|-------------|----------|------------|-------------|
| **Local Development** | Development and testing | Low | Limited |
| **Docker Compose** | Small production, staging | Medium | Moderate |
| **Kubernetes** | Large-scale production | High | High |
| **Cloud Platforms** | Managed deployment | Medium | High |

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 50GB SSD
- **Network**: 100 Mbps

#### Recommended Requirements
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **Storage**: 100GB+ SSD
- **Network**: 1 Gbps

### Software Dependencies

```bash
# Required software
- Docker 24.0+
- Docker Compose 2.0+
- Python 3.11+
- PostgreSQL 15+
- Redis 7.0+
- Nginx 1.20+

# Optional (for Kubernetes)
- kubectl 1.28+
- Helm 3.12+
- Kubernetes 1.28+
```

### External Services

```bash
# Telegram Bot Tokens
ADMIN_BOT_TOKEN=your_admin_bot_token
PLAYER_BOT_TOKEN=your_player_bot_token

# Domain and SSL
DOMAIN=yourdomain.com
SSL_EMAIL=admin@yourdomain.com

# Monitoring (optional)
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
```

## Environment Configuration

### Environment Variables

Create `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://gameuser:secure_password@postgres:5432/gamedb
POSTGRES_USER=gameuser
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=gamedb

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=redis_secure_password

# Application Configuration
SECRET_KEY=your-super-secret-key-here
JWT_SECRET=your-jwt-secret-key-here
DEBUG=false
LOG_LEVEL=INFO

# Telegram Bot Configuration
ADMIN_BOT_TOKEN=1234567890:AAEhBOweik9ai2u5cg6XkhZeQ2lOd3L2zs8
PLAYER_BOT_TOKEN=0987654321:AAFhCPxfjk8bj3v6dh7YliAfR3mPe4M3at9

# Service URLs (internal)
GAME_ENGINE_URL=http://game-engine:8002
SESSION_MANAGER_URL=http://session-manager:8003
USER_MANAGER_URL=http://user-manager:8004
ANALYTICS_URL=http://analytics-service:8005
NOTIFICATION_URL=http://notification-service:8006

# External URLs (public)
API_BASE_URL=https://api.yourdomain.com
WEBHOOK_URL=https://yourdomain.com/webhook

# Security
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://admin.yourdomain.com

# File Storage
UPLOAD_PATH=/app/uploads
MAX_FILE_SIZE=10485760  # 10MB

# Email Configuration (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=email_password
SMTP_TLS=true

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
```

### Configuration Validation

```bash
# Validate configuration script
#!/bin/bash
# scripts/validate-config.sh

echo "🔍 Validating configuration..."

# Check required environment variables
required_vars=(
    "DATABASE_URL"
    "REDIS_URL"
    "SECRET_KEY"
    "JWT_SECRET"
    "ADMIN_BOT_TOKEN"
    "PLAYER_BOT_TOKEN"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing required environment variable: $var"
        exit 1
    fi
done

# Validate bot tokens
if [[ ! $ADMIN_BOT_TOKEN =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
    echo "❌ Invalid ADMIN_BOT_TOKEN format"
    exit 1
fi

if [[ ! $PLAYER_BOT_TOKEN =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
    echo "❌ Invalid PLAYER_BOT_TOKEN format"
    exit 1
fi

# Test database connection
echo "🔍 Testing database connection..."
python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    conn.close()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Test Redis connection
echo "🔍 Testing Redis connection..."
python -c "
import redis
import os
try:
    r = redis.from_url(os.getenv('REDIS_URL'))
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    exit(1)
"

echo "✅ Configuration validation completed successfully!"
```

## Local Development Deployment

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/your-org/game-telegram.git
cd game-telegram

# 2. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 3. Start infrastructure services
docker-compose -f docker-compose.dev.yml up -d postgres redis

# 4. Install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 5. Run database migrations
cd services/game-engine
alembic upgrade head
cd ../user-manager
alembic upgrade head
cd ../..

# 6. Start services (in separate terminals)
cd services/game-engine && uvicorn app.main:app --reload --port 8002
cd services/session-manager && uvicorn app.main:app --reload --port 8003
cd services/user-manager && uvicorn app.main:app --reload --port 8004
cd services/analytics-service && uvicorn app.main:app --reload --port 8005
cd services/notification-service && uvicorn app.main:app --reload --port 8006

# 7. Start bots
cd services/admin-bot && python -m app.main
cd services/player-bot && python -m app.main
```

### Development Docker Compose

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: gamedb
      POSTGRES_USER: gameuser
      POSTGRES_PASSWORD: devpassword
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gameuser -d gamedb"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI

volumes:
  postgres_dev_data:
  redis_dev_data:
```

## Docker Deployment

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Infrastructure
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - game-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - game-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  # Core Services
  game-engine:
    build:
      context: ./services/game-engine
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - game-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  session-manager:
    build:
      context: ./services/session-manager
      dockerfile: Dockerfile
    environment:
      - REDIS_URL=${REDIS_URL}
      - GAME_ENGINE_URL=http://game-engine:8002
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      redis:
        condition: service_healthy
      game-engine:
        condition: service_healthy
    networks:
      - game-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  user-manager:
    build:
      context: ./services/user-manager
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - game-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  analytics-service:
    build:
      context: ./services/analytics-service
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - game-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8005/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  notification-service:
    build:
      context: ./services/notification-service
      dockerfile: Dockerfile
    environment:
      - REDIS_URL=${REDIS_URL}
      - ADMIN_BOT_TOKEN=${ADMIN_BOT_TOKEN}
      - PLAYER_BOT_TOKEN=${PLAYER_BOT_TOKEN}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - game-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8006/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  # Bot Services
  admin-bot:
    build:
      context: ./services/admin-bot
      dockerfile: Dockerfile
    environment:
      - ADMIN_BOT_TOKEN=${ADMIN_BOT_TOKEN}
      - GAME_ENGINE_URL=http://game-engine:8002
      - USER_MANAGER_URL=http://user-manager:8004
      - ANALYTICS_URL=http://analytics-service:8005
      - REDIS_URL=${REDIS_URL}
      - WEBHOOK_URL=${WEBHOOK_URL}/admin
    depends_on:
      game-engine:
        condition: service_healthy
      user-manager:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - game-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  player-bot:
    build:
      context: ./services/player-bot
      dockerfile: Dockerfile
    environment:
      - PLAYER_BOT_TOKEN=${PLAYER_BOT_TOKEN}
      - SESSION_MANAGER_URL=http://session-manager:8003
      - USER_MANAGER_URL=http://user-manager:8004
      - REDIS_URL=${REDIS_URL}
      - WEBHOOK_URL=${WEBHOOK_URL}/player
    depends_on:
      session-manager:
        condition: service_healthy
      user-manager:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - game-network
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  # Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./nginx/logs:/var/log/nginx
    depends_on:
      - game-engine
      - session-manager
      - user-manager
      - analytics-service
      - notification-service
    networks:
      - game-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - game-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - game-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  game-network:
    driver: bridge
```

### Deployment Script

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

echo "🚀 Starting Game Telegram deployment..."

# Configuration
ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"

# Validate environment
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Compose file $COMPOSE_FILE not found"
    exit 1
fi

# Validate configuration
echo "🔍 Validating configuration..."
./scripts/validate-config.sh

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p nginx/logs
mkdir -p backups
mkdir -p uploads

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose -f $COMPOSE_FILE pull

# Build custom images
echo "🔨 Building custom images..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Stop existing services
echo "🛑 Stopping existing services..."
docker-compose -f $COMPOSE_FILE down

# Start infrastructure services first
echo "🏗️ Starting infrastructure services..."
docker-compose -f $COMPOSE_FILE up -d postgres redis

# Wait for infrastructure to be ready
echo "⏳ Waiting for infrastructure services..."
sleep 30

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose -f $COMPOSE_FILE run --rm game-engine alembic upgrade head
docker-compose -f $COMPOSE_FILE run --rm user-manager alembic upgrade head

# Start all services
echo "🚀 Starting all services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 60

# Health check
echo "🏥 Performing health checks..."
./scripts/health-check.sh

echo "✅ Deployment completed successfully!"
echo "🌐 Services are available at:"
echo "  - API: https://api.yourdomain.com"
echo "  - Monitoring: http://localhost:3000 (Grafana)"
echo "  - Metrics: http://localhost:9090 (Prometheus)"
```

## Production Deployment

### Pre-deployment Checklist

```bash
# Production deployment checklist
□ Domain name configured and DNS pointing to server
□ SSL certificates obtained (Let's Encrypt or commercial)
□ Firewall configured (ports 80, 443, 22 only)
□ Server hardened (SSH keys, fail2ban, etc.)
□ Backup strategy implemented
□ Monitoring configured
□ Log aggregation set up
□ Environment variables secured
□ Database backups automated
□ Disaster recovery plan documented
```

### Server Setup

```bash
#!/bin/bash
# scripts/setup-server.sh

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install additional tools
sudo apt install -y htop curl wget git unzip

# Configure firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Create application user
sudo useradd -m -s /bin/bash gameapp
sudo usermod -aG docker gameapp

# Create application directory
sudo mkdir -p /opt/game-telegram
sudo chown gameapp:gameapp /opt/game-telegram

echo "✅ Server setup completed!"
```

### SSL Configuration

```bash
#!/bin/bash
# scripts/setup-ssl.sh

DOMAIN=${1:-yourdomain.com}
EMAIL=${2:-admin@yourdomain.com}

# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot certonly --standalone -d $DOMAIN -d api.$DOMAIN --email $EMAIL --agree-tos --non-interactive

# Set up auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# Copy certificates to nginx directory
sudo mkdir -p /opt/game-telegram/nginx/ssl
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/game-telegram/nginx/ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/game-telegram/nginx/ssl/
sudo chown -R gameapp:gameapp /opt/game-telegram/nginx/ssl

echo "✅ SSL certificates configured for $DOMAIN"
```

### Nginx Configuration

```nginx
# nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=webhook:10m rate=100r/s;

    # Upstream servers
    upstream game_engine {
        least_conn;
        server game-engine:8002 max_fails=3 fail_timeout=30s;
    }

    upstream session_manager {
        least_conn;
        server session-manager:8003 max_fails=3 fail_timeout=30s;
    }

    upstream user_manager {
        least_conn;
        server user-manager:8004 max_fails=3 fail_timeout=30s;
    }

    upstream analytics_service {
        least_conn;
        server analytics-service:8005 max_fails=3 fail_timeout=30s;
    }

    upstream notification_service {
        least_conn;
        server notification-service:8006 max_fails=3 fail_timeout=30s;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name yourdomain.com api.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # Main API server
    server {
        listen 443 ssl http2;
        server_name api.yourdomain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # API routes
        location /api/v1/games {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://game_engine;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        location /api/v1/sessions {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://session_manager;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        location /api/v1/users {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://user_manager;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/v1/analytics {
            limit_req zone=api burst=10 nodelay;
            proxy_pass http://analytics_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/v1/notifications {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://notification_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health checks
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Webhook endpoints
        location /webhook/ {
            limit_req zone=webhook burst=200 nodelay;
            proxy_pass http://notification_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

    # Monitoring server
    server {
        listen 443 ssl http2;
        server_name monitor.yourdomain.com;

        # SSL configuration (same as above)
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers off;

        # Basic auth for monitoring
        auth_basic "Monitoring";
        auth_basic_user_file /etc/nginx/.htpasswd;

        location /grafana/ {
            proxy_pass http://grafana:3000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /prometheus/ {
            proxy_pass http://prometheus:9090/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## Kubernetes Deployment

### Namespace and ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: game-telegram
  labels:
    name: game-telegram

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: game-config
  namespace: game-telegram
data:
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  GAME_ENGINE_URL: "http://game-engine-service:8002"
  SESSION_MANAGER_URL: "http://session-manager-service:8003"
  USER_MANAGER_URL: "http://user-manager-service:8004"
  ANALYTICS_URL: "http://analytics-service:8005"
  NOTIFICATION_URL: "http://notification-service:8006"
  PROMETHEUS_ENABLED: "true"
  METRICS_PORT: "9090"
```

### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: game-secrets
  namespace: game-telegram
type: Opaque
data:
  # Base64 encoded values
  database-url: cG9zdGdyZXNxbDovL2dhbWV1c2VyOnNlY3VyZV9wYXNzd29yZEBwb3N0
gres:5432/gamedb
  redis-url: cmVkaXM6Ly9yZWRpczpzZWN1cmVfcGFzc3dvcmRAcmVkaXM6NjM3OS8w
  jwt-secret: eW91ci1qd3Qtc2VjcmV0LWtleS1oZXJl
  secret-key: eW91ci1zdXBlci1zZWNyZXQta2V5LWhlcmU=
  admin-bot-token: MTIzNDU2Nzg5MDpBQUVoQk93ZWlrOWFpMnU1Y2c2WGtoWmVRMmxPZDNMMnpzOA==
  player-bot-token: MDk4NzY1NDMyMTpBQUZoQ1B4Zms4YmozdjZkaDdZbGlBZlIzbVBlNE0zYXQ5
```

### Persistent Volumes

```yaml
# k8s/persistent-volumes.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: postgres-pv
  namespace: game-telegram
spec:
  capacity:
    storage: 50Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: fast-ssd
  hostPath:
    path: /data/postgres

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: game-telegram
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: fast-ssd

---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: redis-pv
  namespace: game-telegram
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: fast-ssd
  hostPath:
    path: /data/redis

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: game-telegram
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd
```

### Database Deployment

```yaml
# k8s/postgres-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: game-telegram
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: "gamedb"
        - name: POSTGRES_USER
          value: "gameuser"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: game-secrets
              key: postgres-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - gameuser
            - -d
            - gamedb
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - gameuser
            - -d
            - gamedb
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: game-telegram
spec:
  selector:
    app: postgres
  ports:
  - protocol: TCP
    port: 5432
    targetPort: 5432
  type: ClusterIP
```

### Redis Deployment

```yaml
# k8s/redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: game-telegram
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command:
        - redis-server
        - --appendonly
        - "yes"
        - --requirepass
        - $(REDIS_PASSWORD)
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: game-secrets
              key: redis-password
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - redis-cli
            - --no-auth-warning
            - -a
            - $(REDIS_PASSWORD)
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - --no-auth-warning
            - -a
            - $(REDIS_PASSWORD)
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: game-telegram
spec:
  selector:
    app: redis
  ports:
  - protocol: TCP
    port: 6379
    targetPort: 6379
  type: ClusterIP
```

### Application Services

```yaml
# k8s/game-engine-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: game-engine
  namespace: game-telegram
spec:
  replicas: 3
  selector:
    matchLabels:
      app: game-engine
  template:
    metadata:
      labels:
        app: game-engine
    spec:
      containers:
      - name: game-engine
        image: game-telegram/game-engine:latest
        ports:
        - containerPort: 8002
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: game-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: game-secrets
              key: redis-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: game-secrets
              key: secret-key
        envFrom:
        - configMapRef:
            name: game-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: game-engine-service
  namespace: game-telegram
spec:
  selector:
    app: game-engine
  ports:
  - protocol: TCP
    port: 8002
    targetPort: 8002
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: game-engine-hpa
  namespace: game-telegram
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: game-engine
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Ingress Configuration

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: game-telegram-ingress
  namespace: game-telegram
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: api-tls-secret
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /api/v1/games
        pathType: Prefix
        backend:
          service:
            name: game-engine-service
            port:
              number: 8002
      - path: /api/v1/sessions
        pathType: Prefix
        backend:
          service:
            name: session-manager-service
            port:
              number: 8003
      - path: /api/v1/users
        pathType: Prefix
        backend:
          service:
            name: user-manager-service
            port:
              number: 8004
      - path: /api/v1/analytics
        pathType: Prefix
        backend:
          service:
            name: analytics-service
            port:
              number: 8005
      - path: /webhook
        pathType: Prefix
        backend:
          service:
            name: notification-service
            port:
              number: 8006
```

### Deployment Script for Kubernetes

```bash
#!/bin/bash
# scripts/k8s-deploy.sh

set -e

NAMESPACE="game-telegram"
KUBECTL_CONTEXT=${1:-default}

echo "🚀 Deploying Game Telegram to Kubernetes..."
echo "📋 Context: $KUBECTL_CONTEXT"
echo "📋 Namespace: $NAMESPACE"

# Switch to correct context
kubectl config use-context $KUBECTL_CONTEXT

# Create namespace
echo "📁 Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Apply secrets (ensure they exist)
echo "🔐 Applying secrets..."
if [ ! -f k8s/secrets.yaml ]; then
    echo "❌ secrets.yaml not found. Please create it first."
    exit 1
fi
kubectl apply -f k8s/secrets.yaml

# Apply ConfigMaps
echo "⚙️ Applying configuration..."
kubectl apply -f k8s/configmap.yaml

# Apply persistent volumes
echo "💾 Setting up storage..."
kubectl apply -f k8s/persistent-volumes.yaml

# Deploy infrastructure
echo "🏗️ Deploying infrastructure..."
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml

# Wait for infrastructure
echo "⏳ Waiting for infrastructure..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=300s

# Run database migrations
echo "🗄️ Running database migrations..."
kubectl run migration-job --image=game-telegram/game-engine:latest --rm -i --restart=Never -n $NAMESPACE -- alembic upgrade head

# Deploy application services
echo "🚀 Deploying application services..."
kubectl apply -f k8s/game-engine-deployment.yaml
kubectl apply -f k8s/session-manager-deployment.yaml
kubectl apply -f k8s/user-manager-deployment.yaml
kubectl apply -f k8s/analytics-service-deployment.yaml
kubectl apply -f k8s/notification-service-deployment.yaml

# Deploy bot services
echo "🤖 Deploying bot services..."
kubectl apply -f k8s/admin-bot-deployment.yaml
kubectl apply -f k8s/player-bot-deployment.yaml

# Apply ingress
echo "🌐 Setting up ingress..."
kubectl apply -f k8s/ingress.yaml

# Wait for deployments
echo "⏳ Waiting for deployments..."
kubectl wait --for=condition=available deployment --all -n $NAMESPACE --timeout=600s

# Show status
echo "📊 Deployment status:"
kubectl get pods -n $NAMESPACE
kubectl get services -n $NAMESPACE
kubectl get ingress -n $NAMESPACE

echo "✅ Kubernetes deployment completed successfully!"
```

## Database Setup

### Database Initialization

```sql
-- scripts/init-db.sql
-- Initial database setup

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database user (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'gameuser') THEN
        CREATE ROLE gameuser WITH LOGIN PASSWORD 'secure_password';
    END IF;
END
$$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE gamedb TO gameuser;
GRANT ALL ON SCHEMA public TO gameuser;

-- Create indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_games_created_at ON games(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_games_type_category ON games(type, category);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_active ON users(last_active);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_game_results_session ON game_results(session_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_game_results_user_game ON game_results(user_id, game_id);

-- Create functions for common operations
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
CREATE TRIGGER update_games_updated_at BEFORE UPDATE ON games
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Database Migration Script

```bash
#!/bin/bash
# scripts/migrate-db.sh

set -e

DATABASE_URL=${DATABASE_URL:-"postgresql://gameuser:password@localhost:5432/gamedb"}
BACKUP_DIR="./backups"

echo "🗄️ Database Migration Script"
echo "📋 Database: $DATABASE_URL"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup current database
echo "💾 Creating backup..."
BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
pg_dump $DATABASE_URL > $BACKUP_FILE
echo "✅ Backup created: $BACKUP_FILE"

# Run migrations for each service
services=("game-engine" "user-manager" "analytics-service")

for service in "${services[@]}"; do
    echo "🔄 Running migrations for $service..."
    cd services/$service
    
    if [ -f "alembic.ini" ]; then
        alembic upgrade head
        echo "✅ $service migrations completed"
    else
        echo "⚠️ No alembic configuration found for $service"
    fi
    
    cd ../..
done

echo "✅ All database migrations completed successfully!"
```

## SSL/TLS Configuration

### Let's Encrypt Setup

```bash
#!/bin/bash
# scripts/setup-letsencrypt.sh

DOMAIN=${1:-yourdomain.com}
EMAIL=${2:-admin@yourdomain.com}
STAGING=${3:-false}

if [ "$STAGING" = "true" ]; then
    ACME_SERVER="https://acme-staging-v02.api.letsencrypt.org/directory"
    echo "🧪 Using Let's Encrypt staging environment"
else
    ACME_SERVER="https://acme-v02.api.letsencrypt.org/directory"
    echo "🔒 Using Let's Encrypt production environment"
fi

# Install certbot
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx
fi

# Stop nginx temporarily
echo "🛑 Stopping nginx..."
sudo systemctl stop nginx || docker-compose stop nginx

# Obtain certificate
echo "🔐 Obtaining SSL certificate for $DOMAIN..."
sudo certbot certonly \
    --standalone \
    --server $ACME_SERVER \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --domains $DOMAIN,api.$DOMAIN,admin.$DOMAIN

# Copy certificates to nginx directory
echo "📋 Copying certificates..."
sudo mkdir -p ./nginx/ssl
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ./nginx/ssl/
sudo chown -R $USER:$USER ./nginx/ssl

# Set up auto-renewal
echo "🔄 Setting up auto-renewal..."
sudo crontab -l | grep -v certbot | sudo crontab -
echo "0 12 * * * /usr/bin/certbot renew --quiet --deploy-hook 'docker-compose restart nginx'" | sudo crontab -

# Start nginx
echo "🚀 Starting nginx..."
sudo systemctl start nginx || docker-compose start nginx

echo "✅ SSL certificate setup completed for $DOMAIN"
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'game-engine'
    static_configs:
      - targets: ['game-engine:8002']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'session-manager'
    static_configs:
      - targets: ['session-manager:8003']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'user-manager'
    static_configs:
      - targets: ['user-manager:8004']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'analytics-service'
    static_configs:
      - targets: ['analytics-service:8005']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'notification-service'
    static_configs:
      - targets: ['notification-service:8006']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

### Alert Rules

```yaml
# monitoring/alert_rules.yml
groups:
- name: game-telegram-alerts
  rules:
  - alert: ServiceDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Service {{ $labels.job }} is down"
      description: "Service {{ $labels.job }} has been down for more than 1 minute."

  - alert: HighCPUUsage
    expr: (100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)) > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage on {{ $labels.instance }}"
      description: "CPU usage is above 80% for more than 5 minutes."

  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage on {{ $labels.instance }}"
      description: "Memory usage is above 85% for more than 5 minutes."

  - alert: DatabaseConnectionsHigh
    expr: pg_stat_database_numbackends > 80
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High number of database connections"
      description: "Database has more than 80 active connections."

  - alert: RedisMemoryHigh
    expr: redis_memory_used_bytes / redis_memory_max_bytes * 100 > 90
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Redis memory usage is high"
      description: "Redis memory usage is above 90%."

  - alert: GameSessionsHigh
    expr: active_sessions_total > 1000
    for: 1m
    labels:
      severity: info
    annotations:
      summary: "High number of active game sessions"
      description: "There are more than 1000 active game sessions."
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "Game Telegram Dashboard",
    "tags": ["game-telegram"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Active Sessions",
        "type": "stat",
        "targets": [
          {
            "expr": "active_sessions_total",
            "legendFormat": "Active Sessions"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 500},
                {"color": "red", "value": 1000}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "id": 3,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

## Backup and Recovery

### Automated Backup Script

```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="/opt/backups/game-telegram"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

# Configuration
DATABASE_URL=${DATABASE_URL:-"postgresql://gameuser:password@localhost:5432/gamedb"}
REDIS_HOST=${REDIS_HOST:-"localhost"}
REDIS_PORT=${REDIS_PORT:-"6379"}
REDIS_PASSWORD=${REDIS_PASSWORD:-""}

echo "🔄 Starting backup process..."

# Create backup directory
mkdir -p $BACKUP_DIR/{database,redis,uploads}

# Database backup
echo "💾 Backing up PostgreSQL database..."
pg_dump $DATABASE_URL | gzip > $BACKUP_DIR/database/gamedb_$DATE.sql.gz

# Redis backup
echo "💾 Backing up Redis data..."
if [ -n "$REDIS_PASSWORD" ]; then
    redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD --rdb $BACKUP_DIR/redis/redis_$DATE.rdb
else
    redis-cli -h $REDIS_HOST -p $REDIS_PORT --rdb $BACKUP_DIR/redis/redis_$DATE.rdb
fi

# File uploads backup
echo "💾 Backing up uploaded files..."
if [ -d "/opt/game-telegram/uploads" ]; then
    tar -czf $BACKUP_DIR/uploads/uploads_$DATE.tar.gz -C /opt/game-telegram uploads/
fi

# Clean old backups
echo "🧹 Cleaning old backups..."
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

# Upload to cloud storage (optional)
if [ -n "$AWS_S3_BUCKET" ]; then
    echo "☁️ Uploading to S3..."
    aws s3 sync $BACKUP_DIR s3://$AWS_S3_BUCKET/game-telegram-backups/
fi

echo "✅ Backup completed successfully!"
echo "📁 Backup location: $BACKUP_DIR"
```

### Recovery Script

```bash
#!/bin/bash
# scripts/restore.sh

set -e

BACKUP_DIR="/opt/backups/game-telegram"
BACKUP_DATE=${1:-"latest"}

if [ "$BACKUP_DATE" = "latest" ]; then
    DB_BACKUP=$(ls -t $BACKUP_DIR/database/*.sql.gz | head -1)
    REDIS_BACKUP=$(ls -t $BACKUP_DIR/redis/*.rdb | head -1)
    UPLOADS_BACKUP=$(ls -t $BACKUP_DIR/uploads/*.tar.gz | head -1)
else
    DB_BACKUP="$BACKUP_DIR/database/gamedb_$BACKUP_DATE.sql.gz"
    REDIS_BACKUP="$BACKUP_DIR/redis/redis_$BACKUP_DATE.rdb"
    UPLOADS_BACKUP="$BACKUP_DIR/uploads/uploads_$BACKUP_DATE.tar.gz"
fi

echo "🔄 Starting restore process..."
echo "📅 Backup date: $BACKUP_DATE"

# Stop services
echo "🛑 Stopping services..."
docker-compose stop

# Restore database
if [ -f "$DB_BACKUP" ]; then
    echo "🗄️ Restoring PostgreSQL database..."
    docker-compose up -d postgres
    sleep 10
    gunzip -c $DB_BACKUP | docker-compose exec -T postgres psql -U gameuser -d gamedb
else
    echo "❌ Database backup not found: $DB_BACKUP"
    exit 1
fi

# Restore Redis
if [ -f "$REDIS_BACKUP" ]; then
    echo "💾 Restoring Redis data..."
    docker-compose up -d redis
    sleep 5
    docker-compose exec redis redis-cli FLUSHALL
    docker cp $REDIS_BACKUP $(docker-compose ps -q redis):/data/dump.rdb
    docker-compose restart redis
else
    echo "❌ Redis backup not found: $REDIS_BACKUP"
fi

# Restore uploads
if [ -f "$UPLOADS_BACKUP" ]; then
    echo "📁 Restoring uploaded files..."
    tar -xzf $UPLOADS_BACKUP -C /opt/game-telegram/
else
    echo "⚠️ Uploads backup not found: $UPLOADS_BACKUP"
fi

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

echo "✅ Restore completed successfully!"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Service Won't Start

```bash
# Check service logs
docker-compose logs service-name

# Check service health
curl http://localhost:8002/health

# Check resource usage
docker stats

# Check disk space
df -h
```

#### 2. Database Connection Issues

```bash
# Test database connectivity
docker-compose exec postgres psql -U gameuser -d gamedb -c "SELECT 1;"

# Check database logs
docker-compose logs postgres

# Check connection pool
docker-compose exec game-engine python -c "
from app.database import engine
print(f'Pool size: {engine.pool.size()}')
print(f'Checked out: {engine.pool.checkedout()}')
"
```

#### 3. Redis Connection Issues

```bash
# Test Redis connectivity
docker-compose exec redis redis-cli ping

# Check Redis memory usage
docker-compose exec redis redis-cli info memory

# Check Redis connections
docker-compose exec redis redis-cli info clients
```

#### 4. Bot Token Issues

```bash
# Test bot token
curl "https://api.telegram.org/bot$ADMIN_BOT_TOKEN/getMe"

# Check webhook status
curl "https://api.telegram.org/bot$ADMIN_BOT_TOKEN/getWebhookInfo"

# Set webhook
curl -X POST "https://api.telegram.org/bot$ADMIN_BOT_TOKEN/setWebhook" \
     -d "url=https://yourdomain.com/webhook/admin"
```

#### 5. SSL Certificate Issues

```bash
# Check certificate expiry
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout | grep "Not After"

# Test SSL configuration
curl -I https://yourdomain.com

# Renew certificate manually
sudo certbot renew --force-renewal
```

### Health Check Script

```bash
#!/bin/bash
# scripts/health-check.sh

set -e

echo "🏥 Performing health checks..."

# Service endpoints
services=(
    "http://localhost:8002/health:Game Engine"
    "http://localhost:8003/health:Session Manager"
    "http://localhost:8004/health:User Manager"
    "http://localhost:8005/health:Analytics Service"
    "http://localhost:8006/health:Notification Service"
)

# Check each service
for service in "${services[@]}"; do
    IFS=':' read -r url name <<< "$service"
    
    if curl -f -s "$url" > /dev/null; then
        echo "✅ $name: Healthy"
    else
        echo "❌ $name: Unhealthy"
        exit 1
    fi
done

# Check database
if docker-compose exec -T postgres pg_isready -U gameuser -d gamedb > /dev/null; then
    echo "

✅ PostgreSQL: Healthy"
else
    echo "❌ PostgreSQL: Unhealthy"
    exit 1
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null; then
    echo "✅ Redis: Healthy"
else
    echo "❌ Redis: Unhealthy"
    exit 1
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    echo "✅ Disk Space: ${DISK_USAGE}% used"
else
    echo "⚠️ Disk Space: ${DISK_USAGE}% used (Warning: >80%)"
fi

# Check memory usage
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $MEMORY_USAGE -lt 85 ]; then
    echo "✅ Memory Usage: ${MEMORY_USAGE}%"
else
    echo "⚠️ Memory Usage: ${MEMORY_USAGE}% (Warning: >85%)"
fi

echo "✅ All health checks completed!"
```

### Log Analysis Script

```bash
#!/bin/bash
# scripts/analyze-logs.sh

LOG_LEVEL=${1:-ERROR}
HOURS=${2:-1}

echo "📊 Analyzing logs for the last $HOURS hours..."
echo "🔍 Log level: $LOG_LEVEL"

# Analyze application logs
echo "🔍 Application errors:"
docker-compose logs --since="${HOURS}h" | grep -i "$LOG_LEVEL" | head -20

# Analyze nginx logs
echo "🔍 Nginx errors:"
docker-compose exec nginx tail -100 /var/log/nginx/error.log | grep -i error

# Analyze database logs
echo "🔍 Database errors:"
docker-compose logs postgres --since="${HOURS}h" | grep -i error

# Show top error patterns
echo "🔍 Top error patterns:"
docker-compose logs --since="${HOURS}h" | grep -i error | \
    sed 's/[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}T[0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}/TIMESTAMP/g' | \
    sort | uniq -c | sort -nr | head -10
```

## Maintenance

### Regular Maintenance Tasks

#### Daily Tasks

```bash
#!/bin/bash
# scripts/daily-maintenance.sh

echo "🔄 Daily maintenance tasks..."

# Check service health
./scripts/health-check.sh

# Check disk space
df -h | grep -E "(80%|90%|100%)" && echo "⚠️ Disk space warning"

# Check log file sizes
find /var/log -name "*.log" -size +100M -exec ls -lh {} \; | head -10

# Backup database
./scripts/backup.sh

# Clean old Docker images
docker image prune -f

echo "✅ Daily maintenance completed"
```

#### Weekly Tasks

```bash
#!/bin/bash
# scripts/weekly-maintenance.sh

echo "🔄 Weekly maintenance tasks..."

# Update system packages
sudo apt update && sudo apt list --upgradable

# Check SSL certificate expiry
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout | grep "Not After"

# Analyze performance metrics
echo "📊 Performance summary (last 7 days):"
# Add Prometheus queries here

# Clean old backups
find /opt/backups -type f -mtime +30 -delete

# Restart services (if needed)
# docker-compose restart

echo "✅ Weekly maintenance completed"
```

#### Monthly Tasks

```bash
#!/bin/bash
# scripts/monthly-maintenance.sh

echo "🔄 Monthly maintenance tasks..."

# Security updates
sudo apt update && sudo apt upgrade -y

# Database maintenance
docker-compose exec postgres psql -U gameuser -d gamedb -c "VACUUM ANALYZE;"

# Check and rotate logs
sudo logrotate -f /etc/logrotate.conf

# Review and update monitoring alerts
echo "📊 Review monitoring alerts and thresholds"

# Performance review
echo "📈 Monthly performance review needed"

echo "✅ Monthly maintenance completed"
```

### Update Procedures

#### Application Updates

```bash
#!/bin/bash
# scripts/update-application.sh

VERSION=${1:-latest}
ENVIRONMENT=${2:-production}

echo "🔄 Updating Game Telegram to version $VERSION..."

# Create backup before update
echo "💾 Creating backup..."
./scripts/backup.sh

# Pull new images
echo "📥 Pulling new images..."
docker-compose pull

# Build new images
echo "🔨 Building new images..."
docker-compose build --no-cache

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose run --rm game-engine alembic upgrade head
docker-compose run --rm user-manager alembic upgrade head

# Rolling update (zero downtime)
echo "🔄 Performing rolling update..."
services=("game-engine" "session-manager" "user-manager" "analytics-service" "notification-service")

for service in "${services[@]}"; do
    echo "🔄 Updating $service..."
    docker-compose up -d --no-deps $service
    sleep 30
    
    # Health check
    if ! ./scripts/health-check.sh; then
        echo "❌ Health check failed for $service"
        echo "🔄 Rolling back..."
        docker-compose restart $service
        exit 1
    fi
done

# Update bot services
echo "🤖 Updating bot services..."
docker-compose up -d --no-deps admin-bot player-bot

echo "✅ Application update completed successfully!"
```

#### Database Updates

```bash
#!/bin/bash
# scripts/update-database.sh

echo "🗄️ Database update procedure..."

# Create backup
echo "💾 Creating database backup..."
./scripts/backup.sh

# Check current schema version
echo "🔍 Checking current schema version..."
docker-compose exec postgres psql -U gameuser -d gamedb -c "SELECT version_num FROM alembic_version;"

# Run migrations
echo "🔄 Running database migrations..."
docker-compose exec game-engine alembic upgrade head
docker-compose exec user-manager alembic upgrade head

# Verify migrations
echo "✅ Verifying migrations..."
docker-compose exec postgres psql -U gameuser -d gamedb -c "SELECT version_num FROM alembic_version;"

# Run database maintenance
echo "🧹 Running database maintenance..."
docker-compose exec postgres psql -U gameuser -d gamedb -c "VACUUM ANALYZE;"

echo "✅ Database update completed successfully!"
```

### Performance Tuning

#### Database Performance Tuning

```sql
-- scripts/tune-database.sql
-- PostgreSQL performance tuning

-- Update PostgreSQL configuration
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Reload configuration
SELECT pg_reload_conf();

-- Create additional indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_games_search 
ON games USING gin(to_tsvector('english', title || ' ' || description));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_game_results_performance 
ON game_results(created_at, score) WHERE score > 0;

-- Update table statistics
ANALYZE games;
ANALYZE users;
ANALYZE game_results;
```

#### Application Performance Tuning

```python
# Performance tuning configuration
# app/config.py

class ProductionConfig:
    # Database connection pool
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'max_overflow': 30,
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }
    
    # Redis connection pool
    REDIS_CONNECTION_POOL = {
        'max_connections': 50,
        'retry_on_timeout': True,
        'socket_keepalive': True,
        'socket_keepalive_options': {},
    }
    
    # Caching configuration
    CACHE_DEFAULT_TIMEOUT = 3600
    CACHE_KEY_PREFIX = 'game_telegram:'
    
    # API rate limiting
    RATELIMIT_STORAGE_URL = 'redis://redis:6379/1'
    RATELIMIT_DEFAULT = '100/minute'
    
    # Background task configuration
    CELERY_BROKER_URL = 'redis://redis:6379/2'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/2'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
```

## Security Hardening

### Server Security

```bash
#!/bin/bash
# scripts/harden-server.sh

echo "🔒 Hardening server security..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install security tools
sudo apt install -y fail2ban ufw unattended-upgrades

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Configure fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Configure automatic security updates
echo 'Unattended-Upgrade::Automatic-Reboot "false";' | sudo tee -a /etc/apt/apt.conf.d/50unattended-upgrades

# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Set up log monitoring
sudo apt install -y logwatch
echo "logwatch --output mail --mailto admin@yourdomain.com --detail high" | sudo crontab -

echo "✅ Server hardening completed"
```

### Application Security

```bash
#!/bin/bash
# scripts/security-scan.sh

echo "🔍 Running security scans..."

# Scan Docker images for vulnerabilities
echo "🔍 Scanning Docker images..."
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image game-telegram/game-engine:latest

# Check for outdated packages
echo "🔍 Checking for outdated Python packages..."
pip list --outdated

# Run security linting
echo "🔍 Running security linting..."
bandit -r services/ -f json -o security-report.json

# Check SSL configuration
echo "🔍 Checking SSL configuration..."
curl -I https://yourdomain.com | grep -i security

echo "✅ Security scan completed"
```

---

## Summary

This deployment guide provides comprehensive instructions for deploying the Game Telegram system across different environments:

### Key Features:
- **Multiple deployment options**: Local development, Docker Compose, Kubernetes
- **Production-ready configurations**: SSL/TLS, monitoring, backup strategies
- **Automated scripts**: Deployment, backup, maintenance, and health checks
- **Security hardening**: Server security, application security, SSL configuration
- **Monitoring and alerting**: Prometheus, Grafana, custom dashboards
- **Troubleshooting guides**: Common issues and solutions

### Deployment Environments:
1. **Local Development**: Quick setup for development and testing
2. **Docker Compose**: Production deployment for small to medium scale
3. **Kubernetes**: Large-scale production deployment with auto-scaling
4. **Cloud Platforms**: Managed deployment options

### Maintenance:
- Automated backup and recovery procedures
- Regular maintenance tasks (daily, weekly, monthly)
- Update procedures for applications and databases
- Performance tuning guidelines
- Security hardening and monitoring

The deployment guide ensures reliable, secure, and scalable deployment of the Game Telegram system in any environment.

**Last Updated**: January 2024  
**Version**: 1.0.0
