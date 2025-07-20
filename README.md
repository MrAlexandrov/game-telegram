# Game Telegram

A comprehensive microservices-based platform for creating and managing interactive games through Telegram bots. Built with Python, FastAPI, and modern cloud-native technologies.

## 🎮 Overview

Game Telegram is a scalable, production-ready system that enables administrators to create engaging quiz games, family feud competitions, and interactive challenges that players can participate in through Telegram bots. The system supports real-time gameplay, analytics, user management, and comprehensive administrative tools.

### ✨ Key Features

- **🤖 Dual Bot System**: Separate admin and player bots for optimal user experience
- **🎯 Multiple Game Types**: Quiz games, Family Feud, word games, and extensible architecture
- **⚡ Real-time Gameplay**: WebSocket-based real-time game sessions
- **📊 Advanced Analytics**: Comprehensive game statistics and player insights
- **👥 User Management**: Complete user profiles, authentication, and authorization
- **🔧 Admin Dashboard**: Full administrative control through Telegram bot interface
- **📈 Scalable Architecture**: Microservices design supporting horizontal scaling
- **🛡️ Security First**: JWT authentication, input validation, and security best practices
- **📱 Mobile-First**: Optimized for mobile Telegram experience
- **🌍 Multi-language**: Support for multiple languages and localization

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐
│   Admin Bot     │    │   Player Bot    │
│   (Port 8000)   │    │   (Port 8001)   │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼────┐    ┌──────▼──────┐    ┌────▼────┐
│ Game   │    │  Session    │    │  User   │
│ Engine │    │  Manager    │    │ Manager │
│ :8002  │    │   :8003     │    │  :8004  │
└────────┘    └─────────────┘    └─────────┘
    │                 │                │
    └─────────────────┼────────────────┘
                      │
    ┌─────────────────┼────────────────┐
    │                 │                │
┌───▼─────┐    ┌──────▼──────┐    ┌────▼────┐
│Analytics│    │Notification │    │ Load    │
│Service  │    │  Service    │    │Balancer │
│ :8005   │    │   :8006     │    │ (Nginx) │
└─────────┘    └─────────────┘    └─────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Python 3.11+, FastAPI | REST APIs and business logic |
| **Bots** | aiogram 3.0+ | Telegram bot framework |
| **Database** | PostgreSQL 15+ | Primary data storage |
| **Cache** | Redis 7.0+ | Session storage and caching |
| **Message Queue** | Celery + Redis | Background task processing |
| **Web Server** | Nginx | Load balancing and SSL termination |
| **Containerization** | Docker & Docker Compose | Application packaging |
| **Orchestration** | Kubernetes (optional) | Container orchestration |
| **Monitoring** | Prometheus + Grafana | Metrics and monitoring |

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Telegram Bot Tokens (from [@BotFather](https://t.me/botfather))

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/game-telegram.git
cd game-telegram

# Copy environment configuration
cp .env.example .env
# Edit .env with your bot tokens and configuration
```

### 2. Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps
```

### 3. Load Demo Data

```bash
# Load sample games
python demo/scripts/load_sample_games.py --all

# Create test users
python demo/scripts/create_test_users.py --count 10 --admin
```

### 4. Access Your Bots

- **Admin Bot**: Search for your admin bot in Telegram and start it
- **Player Bot**: Search for your player bot in Telegram and start playing
- **API Documentation**: http://localhost:8002/docs
- **Monitoring**: http://localhost:3000 (Grafana)

## 📖 Documentation

### User Guides
- **[Admin Guide](docs/user-guide/admin-guide.md)** - Complete guide for game administrators
- **[Player Guide](docs/user-guide/player-guide.md)** - How to play games and use features

### Technical Documentation
- **[API Reference](docs/developer-guide/api-reference.md)** - Complete API documentation
- **[Developer Guide](docs/developer-guide/developer-guide.md)** - Development setup and guidelines
- **[Architecture Guide](docs/developer-guide/architecture.md)** - System architecture and design patterns
- **[Deployment Guide](docs/deployment/deployment-guide.md)** - Production deployment instructions

### Additional Resources
- **[Game Pack Structure](docs/game-packs-structure.md)** - How to create game content
- **[Bot Interaction Flows](docs/bot-interaction-flows.md)** - Bot conversation flows
- **[Infrastructure Deployment](docs/infrastructure-deployment.md)** - Infrastructure setup

## 🎯 Game Types

### Quiz Games
- **Single Choice**: Multiple choice questions with one correct answer
- **Multiple Choice**: Questions with multiple correct answers
- **True/False**: Simple true or false questions
- **Text Input**: Free text answer questions
- **Mixed Format**: Combination of different question types

### Family Feud
- **Survey Questions**: "We asked 100 people..." style questions
- **Team Mode**: Support for team-based gameplay
- **Strike System**: Traditional Family Feud strike mechanics
- **Point System**: Weighted scoring based on survey popularity

### Word Games
- **Word Scramble**: Unscramble letters to form words
- **Vocabulary**: Definition-based word guessing
- **Extensible**: Easy to add new word game types

## 🔧 Development

### Local Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start infrastructure services
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Run database migrations
cd services/game-engine && alembic upgrade head
cd ../user-manager && alembic upgrade head

# Start services (in separate terminals)
cd services/game-engine && uvicorn app.main:app --reload --port 8002
cd services/session-manager && uvicorn app.main:app --reload --port 8003
cd services/user-manager && uvicorn app.main:app --reload --port 8004
cd services/analytics-service && uvicorn app.main:app --reload --port 8005
cd services/notification-service && uvicorn app.main:app --reload --port 8006

# Start bots
cd services/admin-bot && python -m app.main
cd services/player-bot && python -m app.main
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests
pytest -m integration   # Integration tests
pytest -m e2e           # End-to-end tests
pytest -m performance   # Performance tests
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy .

# Security scan
bandit -r services/
```

## 📊 Features in Detail

### Admin Bot Features
- **Game Management**: Create, edit, and delete games
- **Session Control**: Start, stop, and monitor game sessions
- **User Administration**: Manage users and permissions
- **Analytics Dashboard**: View game statistics and player insights
- **Content Import**: Import games from JSON files
- **Real-time Monitoring**: Live session monitoring and control

### Player Bot Features
- **Game Discovery**: Browse and search available games
- **Quick Join**: Join games with simple commands
- **Real-time Gameplay**: Participate in live game sessions
- **Progress Tracking**: View personal statistics and achievements
- **Leaderboards**: Compare scores with other players
- **Notifications**: Get notified about new games and results

### API Features
- **RESTful Design**: Clean, consistent API design
- **Authentication**: JWT-based authentication system
- **Rate Limiting**: Built-in rate limiting and abuse prevention
- **Comprehensive Documentation**: OpenAPI/Swagger documentation
- **Versioning**: API versioning support
- **Error Handling**: Consistent error responses and logging

## 🔒 Security

### Security Features
- **JWT Authentication**: Secure token-based authentication
- **Input Validation**: Comprehensive input validation and sanitization
- **Rate Limiting**: API rate limiting and abuse prevention
- **SQL Injection Protection**: Parameterized queries and ORM usage
- **XSS Prevention**: Output encoding and content security policies
- **HTTPS Enforcement**: SSL/TLS encryption for all communications
- **Security Headers**: Comprehensive security headers implementation

### Security Best Practices
- Regular security updates and dependency management
- Comprehensive logging and monitoring
- Secure configuration management
- Regular security audits and penetration testing
- Incident response procedures

## 📈 Monitoring and Analytics

### Built-in Monitoring
- **Health Checks**: Comprehensive service health monitoring
- **Metrics Collection**: Prometheus metrics for all services
- **Performance Monitoring**: Response time and throughput tracking
- **Error Tracking**: Centralized error logging and alerting
- **Resource Monitoring**: CPU, memory, and disk usage tracking

### Analytics Features
- **Game Statistics**: Detailed game performance analytics
- **Player Insights**: User behavior and engagement metrics
- **Real-time Dashboards**: Live monitoring dashboards
- **Custom Reports**: Configurable reporting system
- **Data Export**: Export analytics data for external analysis

## 🚀 Deployment Options

### Docker Compose (Recommended for Small-Medium Scale)
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes (Recommended for Large Scale)
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/
```

### Cloud Platforms
- **AWS**: ECS, EKS, or EC2 deployment
- **Google Cloud**: GKE or Compute Engine deployment
- **Azure**: AKS or Container Instances deployment
- **DigitalOcean**: Kubernetes or Droplets deployment

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Process
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Document new features
- Use type hints
- Follow security best practices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Documentation**: Check our comprehensive documentation
- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Join community discussions
- **Email**: Contact us at support@game-telegram.com

### Community
- **GitHub Discussions**: Ask questions and share ideas
- **Discord**: Join our developer community
- **Twitter**: Follow us for updates and announcements

## 🎉 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- Powered by [aiogram](https://docs.aiogram.dev/) - Telegram Bot API framework
- Inspired by popular game show formats and interactive entertainment
- Thanks to all contributors and the open-source community

---

**Game Telegram** - Making interactive gaming accessible through Telegram 🎮✨

[![GitHub Stars](https://img.shields.io/github/stars/your-org/game-telegram?style=social)](https://github.com/your-org/game-telegram)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)