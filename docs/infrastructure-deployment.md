# Инфраструктура и развертывание

## Технологический стек

**Backend Services:**
- **Python 3.11+** - основной язык разработки
- **FastAPI** - веб-фреймворк для API
- **aiogram 3.x** - библиотека для Telegram ботов
- **SQLAlchemy 2.0** - ORM для работы с базой данных
- **Alembic** - миграции базы данных
- **Pydantic** - валидация данных
- **Celery** - очереди задач
- **aioredis** - асинхронный клиент Redis

**Базы данных:**
- **PostgreSQL 15+** - основная база данных
- **Redis 7+** - кэширование и сессии

**Инфраструктура:**
- **Docker & Docker Compose** - контейнеризация
- **Nginx** - reverse proxy и load balancer
- **Prometheus + Grafana** - мониторинг
- **ELK Stack** - логирование

## Docker Compose конфигурация

```yaml
version: '3.8'

services:
  # Основные сервисы
  core-service:
    build: ./services/core
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/gamedb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    networks:
      - game-network

  admin-bot:
    build: ./services/admin-bot
    environment:
      - BOT_TOKEN=${ADMIN_BOT_TOKEN}
      - CORE_API_URL=http://core-service:8000
    depends_on:
      - core-service
    networks:
      - game-network

  player-bot:
    build: ./services/player-bot
    environment:
      - BOT_TOKEN=${PLAYER_BOT_TOKEN}
      - CORE_API_URL=http://core-service:8000
    depends_on:
      - core-service
    networks:
      - game-network

  game-engine:
    build: ./services/game-engine
    environment:
      - REDIS_URL=redis://redis:6379
      - CORE_API_URL=http://core-service:8000
    depends_on:
      - redis
      - core-service
    networks:
      - game-network

  session-manager:
    build: ./services/session-manager
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://user:pass@postgres:5432/gamedb
    depends_on:
      - postgres
      - redis
    networks:
      - game-network

  media-service:
    build: ./services/media
    environment:
      - STORAGE_PATH=/app/media
      - DATABASE_URL=postgresql://user:pass@postgres:5432/gamedb
    volumes:
      - media-storage:/app/media
    depends_on:
      - postgres
    networks:
      - game-network

  notification-service:
    build: ./services/notifications
    environment:
      - REDIS_URL=redis://redis:6379
      - ADMIN_BOT_URL=http://admin-bot:8000
      - PLAYER_BOT_URL=http://player-bot:8000
    depends_on:
      - redis
    networks:
      - game-network

  # Базы данных
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=gamedb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - game-network

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    networks:
      - game-network

  # Инфраструктура
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - core-service
    networks:
      - game-network

  # Мониторинг
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - game-network

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - game-network

volumes:
  postgres-data:
  redis-data:
  media-storage:
  grafana-data:

networks:
  game-network:
    driver: bridge
```

## Структура проекта

```
game-telegram-system/
├── services/
│   ├── core/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── models/
│   │   │   ├── services/
│   │   │   └── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── admin-bot/
│   │   ├── app/
│   │   │   ├── handlers/
│   │   │   ├── keyboards/
│   │   │   ├── services/
│   │   │   └── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── player-bot/
│   │   ├── app/
│   │   │   ├── handlers/
│   │   │   ├── keyboards/
│   │   │   ├── services/
│   │   │   └── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── game-engine/
│   │   ├── app/
│   │   │   ├── modules/
│   │   │   │   ├── quiz.py
│   │   │   │   ├── family_feud.py
│   │   │   │   └── base.py
│   │   │   ├── services/
│   │   │   └── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── session-manager/
│   ├── media-service/
│   └── notification-service/
├── game-packs/
│   ├── quiz/
│   │   ├── history.json
│   │   ├── science.json
│   │   └── general.json
│   └── family-feud/
│       ├── family.json
│       └── work.json
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── deployment.md
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

## Планирование масштабирования и производительности

### Стратегия масштабирования

**Горизонтальное масштабирование:**
- Каждый сервис может быть запущен в нескольких экземплярах
- Load balancer распределяет нагрузку между инстансами
- Stateless архитектура позволяет легко добавлять новые инстансы

**Вертикальное масштабирование:**
- Увеличение ресурсов для критически важных сервисов
- Оптимизация запросов к базе данных
- Кэширование часто используемых данных

### Оптимизация производительности

**База данных:**
```sql
-- Индексы для оптимизации запросов
CREATE INDEX CONCURRENTLY idx_game_sessions_active 
ON game_sessions(status) WHERE status IN ('waiting', 'active');

CREATE INDEX CONCURRENTLY idx_player_answers_session_user 
ON player_answers(session_id, user_id);

CREATE INDEX CONCURRENTLY idx_questions_game_order 
ON questions(game_id, order_index);

-- Партиционирование для больших таблиц
CREATE TABLE player_answers_partitioned (
    LIKE player_answers INCLUDING ALL
) PARTITION BY RANGE (answered_at);

CREATE TABLE player_answers_2024_01 PARTITION OF player_answers_partitioned
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

**Кэширование в Redis:**
```python
# Структуры данных для кэширования
CACHE_KEYS = {
    "active_session": "session:{session_id}",
    "user_session": "user:{user_id}:session",
    "game_config": "game:{game_id}:config",
    "leaderboard": "session:{session_id}:leaderboard",
    "question_cache": "question:{question_id}"
}

# TTL для разных типов данных
CACHE_TTL = {
    "session": 3600,  # 1 час
    "game_config": 86400,  # 24 часа
    "leaderboard": 300,  # 5 минут
    "question": 1800  # 30 минут
}
```

**Очереди задач:**
```python
# Celery задачи для асинхронной обработки
@celery_app.task
def cleanup_expired_sessions():
    """Очистка истекших сессий"""
    pass

@celery_app.task
def send_bulk_notifications(user_ids: List[str], message: str):
    """Массовая отправка уведомлений"""
    pass

@celery_app.task
def calculate_session_results(session_id: str):
    """Подсчет результатов игры"""
    pass

@celery_app.task
def backup_session_data(session_id: str):
    """Резервное копирование данных сессии"""
    pass
```

### Мониторинг и метрики

**Ключевые метрики:**
- Количество активных сессий
- Количество подключенных игроков
- Время отклика API
- Использование памяти и CPU
- Количество ошибок
- Пропускная способность ботов

**Prometheus метрики:**
```python
from prometheus_client import Counter, Histogram, Gauge

# Счетчики
SESSIONS_CREATED = Counter('game_sessions_created_total', 'Total created sessions')
QUESTIONS_ANSWERED = Counter('questions_answered_total', 'Total answered questions')
ERRORS_TOTAL = Counter('errors_total', 'Total errors', ['service', 'error_type'])

# Гистограммы
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
GAME_DURATION = Histogram('game_duration_seconds', 'Game duration')

# Датчики
ACTIVE_SESSIONS = Gauge('active_sessions', 'Number of active sessions')
CONNECTED_PLAYERS = Gauge('connected_players', 'Number of connected players')
```

## Безопасность и надежность

### Безопасность

**Аутентификация и авторизация:**
- JWT токены для API
- Роли пользователей (admin, player)
- Валидация Telegram данных
- Rate limiting для API

**Защита данных:**
- Шифрование чувствительных данных
- Валидация входных данных
- SQL injection защита через ORM
- XSS защита

**Изоляция сессий:**
- Уникальные коды сессий
- Проверка прав доступа
- Изоляция данных между играми

### Надежность

**Обработка ошибок:**
```python
class GameSystemException(Exception):
    """Базовое исключение системы"""
    pass

class SessionNotFoundError(GameSystemException):
    """Сессия не найдена"""
    pass

class InvalidGameStateError(GameSystemException):
    """Неверное состояние игры"""
    pass

class PlayerNotInSessionError(GameSystemException):
    """Игрок не в сессии"""
    pass

# Middleware для обработки ошибок
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except GameSystemException as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e), "type": type(e).__name__}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
```

**Резервное копирование:**
- Автоматические бэкапы PostgreSQL
- Репликация Redis данных
- Сохранение медиа-файлов в объектном хранилище

**Health checks:**
```python
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "external_apis": await check_telegram_api()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={"status": "healthy" if all_healthy else "unhealthy", "checks": checks}
    )
```

## План развертывания

### Этапы развертывания

**Этап 1: Базовая инфраструктура**
1. Настройка Docker окружения
2. Развертывание баз данных
3. Настройка сетевого взаимодействия

**Этап 2: Основные сервисы**
1. Core Service
2. Session Manager
3. Game Engine с базовыми модулями

**Этап 3: Боты**
1. Admin Bot Service
2. Player Bot Service
3. Интеграция с Telegram API

**Этап 4: Дополнительные сервисы**
1. Media Service
2. Notification Service
3. Мониторинг и логирование

**Этап 5: Тестирование и оптимизация**
1. Нагрузочное тестирование
2. Оптимизация производительности
3. Настройка мониторинга

### Команды развертывания

```bash
# Клонирование репозитория
git clone <repository-url>
cd game-telegram-system

# Настройка переменных окружения
cp .env.example .env
# Редактирование .env файла

# Сборка и запуск сервисов
docker-compose build
docker-compose up -d

# Применение миграций
docker-compose exec core-service alembic upgrade head

# Создание начальных данных
docker-compose exec core-service python scripts/init_data.py

# Проверка статуса сервисов
docker-compose ps