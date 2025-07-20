# Analytics System Documentation

## Overview

The Analytics System is a comprehensive solution for tracking, analyzing, and reporting game results and player statistics in the Telegram Game System. It provides real-time analytics, player statistics, achievements, leaderboards, and administrative monitoring capabilities.

## Architecture

### Components

1. **Analytics Service** (`services/analytics-service/`)
   - FastAPI-based REST API
   - PostgreSQL database with SQLAlchemy ORM
   - Redis caching for performance
   - Comprehensive business logic services

2. **Shared Schemas** (`shared/schemas/results.py`)
   - Pydantic models for data validation
   - Consistent data structures across services

3. **Bot Integrations**
   - Player Bot handlers for result display
   - Admin Bot handlers for analytics monitoring

4. **Database Models** 
   - Normalized schema with proper relationships
   - Optimized indexes for query performance

## Features

### Core Analytics Features

- **Game Results Tracking**: Complete game session recording
- **Player Statistics**: Comprehensive player performance metrics
- **Real-time Analytics**: Live monitoring and metrics
- **Achievements System**: Criteria-based achievement tracking
- **Leaderboards**: Global, weekly, and game-type specific rankings
- **Data Export**: JSON/CSV export functionality
- **Performance Monitoring**: System health and performance metrics

### Player Features

- **Personal Statistics**: Detailed performance breakdown
- **Achievement Progress**: Visual achievement tracking
- **Game History**: Complete game participation history
- **Leaderboard Rankings**: Position tracking and comparisons
- **Progress Visualization**: Level and experience tracking

### Administrative Features

- **System Analytics**: Overall system performance metrics
- **Live Monitoring**: Real-time system status
- **Player Analytics**: Active player analysis
- **Trend Analysis**: Historical data trends
- **Data Export**: Administrative data export tools
- **Performance Alerts**: System health monitoring

## Database Schema

### Core Tables

#### `game_results`
- Primary game session data
- Duration, player counts, completion status
- Links to player results and session analytics

#### `player_results`
- Individual player performance in games
- Scores, accuracy, timing, position
- Links to game results and player statistics

#### `player_statistics`
- Aggregated player performance data
- Total games, scores, accuracy, streaks
- Experience points and level tracking

#### `achievements`
- Achievement definitions and criteria
- Types: speed, accuracy, participation, streak, milestone

#### `player_achievements`
- Player achievement progress and completion
- Earned timestamps and progress tracking

#### `session_analytics`
- Real-time session monitoring data
- Active players, concurrent sessions
- Performance metrics and system health

### Relationships

```
game_results (1) -> (N) player_results
player_results (N) -> (1) player_statistics
achievements (1) -> (N) player_achievements
player_statistics (1) -> (N) player_achievements
```

## API Endpoints

### Results API (`/api/results/`)

- `POST /games` - Record game result
- `POST /players` - Record player result
- `POST /batch` - Batch result recording
- `GET /games/{game_id}` - Get game result
- `GET /players/{player_id}/recent` - Get recent player results

### Analytics API (`/api/analytics/`)

- `GET /system/metrics` - System-wide metrics
- `GET /games/popular` - Popular games analysis
- `GET /players/{player_id}/stats` - Player statistics
- `GET /trends/daily` - Daily trend analysis
- `GET /performance/overall` - Performance analytics

### Leaderboard API (`/api/leaderboard/`)

- `GET /global` - Global leaderboard
- `GET /weekly` - Weekly leaderboard
- `GET /game-type/{type}` - Game-type specific leaderboard

### Achievements API (`/api/achievements/`)

- `GET /` - List all achievements
- `GET /players/{player_id}` - Player achievements
- `POST /check/{player_id}` - Check achievement progress

### Export API (`/api/export/`)

- `POST /data` - Export data with filters
- `GET /status/{export_id}` - Export status

### Metrics API (`/api/metrics/`)

- `GET /system` - System metrics
- `GET /live` - Live analytics data

## Bot Integration

### Player Bot Handlers

#### Statistics Display (`/stats`)
- Personal performance overview
- Recent games summary
- Achievement highlights
- Progress indicators

#### Game Results Display
- Post-game result presentation
- Ranking and position display
- Performance breakdown
- Achievement notifications

#### Interactive Features
- Detailed statistics drill-down
- Achievement progress tracking
- Game history browsing
- Leaderboard comparisons

### Admin Bot Handlers

#### Analytics Dashboard (`/analytics`)
- System-wide analytics overview
- Popular games analysis
- Active player metrics
- Trend visualization

#### Live Monitoring
- Real-time system status
- Active session tracking
- Performance alerts
- Resource utilization

#### Data Export
- Administrative data export
- Custom date ranges
- Multiple format support
- Download link generation

## Performance Optimizations

### Caching Strategy

- **Redis Caching**: Leaderboards, session analytics, popular games
- **Cache TTL**: Configurable expiration times
- **Cache Invalidation**: Automatic on data updates

### Database Optimizations

- **Indexes**: Strategic indexing on query columns
- **Partitioning**: Time-based partitioning for large tables
- **Connection Pooling**: Async connection management
- **Query Optimization**: Efficient JOIN operations

### API Performance

- **Async Operations**: Non-blocking I/O operations
- **Batch Processing**: Bulk data operations
- **Pagination**: Large dataset handling
- **Response Compression**: Reduced bandwidth usage

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://host:port/db
REDIS_POOL_SIZE=10

# API
API_HOST=0.0.0.0
API_PORT=8006
API_WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Features
ENABLE_ACHIEVEMENTS=true
ENABLE_CACHING=true
CACHE_TTL=300
```

### Service Configuration

```python
# services/analytics-service/app/config.py
class Settings(BaseSettings):
    database_url: str
    redis_url: str
    api_host: str = "0.0.0.0"
    api_port: int = 8006
    log_level: str = "INFO"
    enable_achievements: bool = True
    enable_caching: bool = True
    cache_ttl: int = 300
```

## Deployment

### Docker Compose

```yaml
services:
  analytics-service:
    build: ./services/analytics-service
    ports:
      - "8006:8006"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/game_telegram
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
```

### Health Checks

- **Database Connectivity**: PostgreSQL connection test
- **Redis Connectivity**: Redis connection test
- **API Responsiveness**: Endpoint response time
- **System Resources**: Memory and CPU usage

## Testing

### Integration Tests

Run the comprehensive integration test suite:

```bash
python test_analytics_integration.py
```

### Test Coverage

- **API Endpoints**: All REST endpoints tested
- **Database Operations**: CRUD operations verified
- **Business Logic**: Service layer validation
- **Bot Integration**: Handler functionality tested
- **Performance**: Load and stress testing

### Test Data

- **Mock Game Results**: Realistic test scenarios
- **Player Profiles**: Various player types
- **Achievement Scenarios**: Different achievement paths
- **Performance Data**: Load testing datasets

## Monitoring and Alerts

### Metrics Collection

- **System Metrics**: CPU, memory, disk usage
- **Application Metrics**: Request rates, response times
- **Business Metrics**: Games played, active users
- **Error Metrics**: Error rates, exception tracking

### Alert Conditions

- **High Error Rate**: > 5% error rate
- **Slow Response Time**: > 1s average response
- **Database Issues**: Connection failures
- **Memory Usage**: > 80% memory utilization

## Security

### Data Protection

- **Input Validation**: Pydantic schema validation
- **SQL Injection Prevention**: SQLAlchemy ORM usage
- **Rate Limiting**: API request throttling
- **Data Encryption**: Sensitive data encryption

### Access Control

- **API Authentication**: Service-to-service auth
- **Admin Access**: Role-based permissions
- **Data Privacy**: Player data protection
- **Audit Logging**: Access and modification logs

## Maintenance

### Regular Tasks

- **Database Cleanup**: Old data archival
- **Cache Warming**: Preload frequently accessed data
- **Index Maintenance**: Database optimization
- **Log Rotation**: Log file management

### Backup Strategy

- **Database Backups**: Daily automated backups
- **Configuration Backups**: Service configuration
- **Recovery Testing**: Backup restoration tests
- **Disaster Recovery**: Multi-region failover

## Future Enhancements

### Planned Features

- **Advanced Analytics**: Machine learning insights
- **Real-time Dashboards**: Live visualization
- **Mobile Analytics**: Mobile-specific metrics
- **A/B Testing**: Feature experimentation
- **Predictive Analytics**: Player behavior prediction

### Scalability Improvements

- **Horizontal Scaling**: Multi-instance deployment
- **Database Sharding**: Data distribution
- **Microservices**: Service decomposition
- **Event Streaming**: Real-time data processing

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check connection string
   - Verify database availability
   - Review connection pool settings

2. **Redis Connection Issues**
   - Verify Redis service status
   - Check network connectivity
   - Review Redis configuration

3. **Performance Issues**
   - Monitor database query performance
   - Check cache hit rates
   - Review API response times

4. **Data Inconsistencies**
   - Verify transaction handling
   - Check concurrent access patterns
   - Review data validation rules

### Debug Commands

```bash
# Check service health
curl http://localhost:8006/health

# View system metrics
curl http://localhost:8006/api/metrics/system

# Test database connection
python -c "from app.database import test_connection; test_connection()"

# Clear Redis cache
redis-cli FLUSHDB
```

## Support

For technical support and questions:

- **Documentation**: This file and inline code comments
- **Integration Tests**: `test_analytics_integration.py`
- **API Documentation**: FastAPI auto-generated docs at `/docs`
- **Database Schema**: SQLAlchemy models in `app/models.py`