# Telegram Bots Deployment Guide

## Обзор

Данное руководство описывает процесс развертывания и настройки Telegram ботов для игровой системы.

## Архитектура

Система состоит из двух основных ботов:

### Admin Bot
- **Назначение**: Управление играми и сессиями
- **Функции**:
  - Создание и редактирование игр
  - Запуск игровых сессий
  - Мониторинг хода игры
  - Валидация ответов игроков
  - Генерация QR-кодов для подключения

### Player Bot
- **Назначение**: Участие в играх
- **Функции**:
  - Подключение к играм по коду или QR-коду
  - Ответы на вопросы
  - Просмотр результатов
  - Статистика игрока

## Предварительные требования

### Системные требования
- Python 3.9+
- Redis 6.0+
- Docker и Docker Compose (опционально)

### Telegram Bot Tokens
1. Создайте двух ботов через [@BotFather](https://t.me/BotFather)
2. Получите токены для Admin Bot и Player Bot
3. Настройте команды для ботов:

**Admin Bot команды:**
```
start - Запуск бота
help - Помощь
games - Управление играми
sessions - Управление сессиями
stats - Статистика
```

**Player Bot команды:**
```
start - Запуск бота
help - Помощь
join - Присоединиться к игре
stats - Моя статистика
```

## Установка и настройка

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd game-telegram
```

### 2. Настройка переменных окружения

Создайте файлы `.env` для каждого бота:

**services/admin-bot/.env:**
```env
BOT_TOKEN=your_admin_bot_token_here
REDIS_URL=redis://localhost:6379/0
USER_MANAGER_URL=http://localhost:8001
GAME_ENGINE_URL=http://localhost:8002
SESSION_MANAGER_URL=http://localhost:8003
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
WEBHOOK_URL=
WEBHOOK_SECRET=
```

**services/player-bot/.env:**
```env
BOT_TOKEN=your_player_bot_token_here
REDIS_URL=redis://localhost:6379/1
USER_MANAGER_URL=http://localhost:8001
GAME_ENGINE_URL=http://localhost:8002
SESSION_MANAGER_URL=http://localhost:8003
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8001
WEBHOOK_URL=
WEBHOOK_SECRET=
```

### 3. Установка зависимостей

**Для Admin Bot:**
```bash
cd services/admin-bot
pip install -r requirements.txt
```

**Для Player Bot:**
```bash
cd services/player-bot
pip install -r requirements.txt
```

### 4. Запуск Redis
```bash
# Локально
redis-server

# Или через Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

## Запуск ботов

### Режим разработки (Polling)

**Admin Bot:**
```bash
cd services/admin-bot
python -m app.main
```

**Player Bot:**
```bash
cd services/player-bot
python -m app.main
```

### Продакшн режим (Webhook)

1. Настройте WEBHOOK_URL в .env файлах
2. Настройте WEBHOOK_SECRET
3. Запустите боты:

```bash
# Admin Bot
cd services/admin-bot
python -m app.main

# Player Bot
cd services/player-bot
python -m app.main
```

### Запуск через Docker Compose

```bash
# Запуск всей системы
docker-compose up -d

# Запуск только ботов
docker-compose up -d admin-bot player-bot redis
```

## Использование

### Admin Bot

1. **Запуск бота**: `/start`
2. **Создание игры**:
   - Нажмите "🎮 Управление играми"
   - Выберите "➕ Создать игру"
   - Загрузите JSON файл с игрой или создайте вручную
3. **Запуск сессии**:
   - Нажмите "🎯 Управление сессиями"
   - Выберите "🚀 Создать сессию"
   - Выберите игру и запустите
4. **Мониторинг игры**:
   - Используйте "📊 Активные сессии"
   - Валидируйте ответы игроков
   - Управляйте ходом игры

### Player Bot

1. **Запуск бота**: `/start`
2. **Подключение к игре**:
   - Нажмите "🎮 Присоединиться к игре"
   - Введите код сессии или отсканируйте QR-код
3. **Участие в игре**:
   - Отвечайте на вопросы
   - Следите за результатами
   - Просматривайте статистику

## Структура JSON файла игры

```json
{
  "title": "Название игры",
  "description": "Описание игры",
  "game_type": "quiz",
  "config": {
    "time_per_question": 30,
    "max_players": 50,
    "scoring_system": "standard"
  },
  "questions": [
    {
      "id": 1,
      "type": "single_choice",
      "question": "Текст вопроса",
      "options": ["Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4"],
      "correct_answer": 0,
      "points": 10,
      "time_limit": 30
    }
  ]
}
```

## Мониторинг и логирование

### Логи
Логи сохраняются в структурированном формате JSON:
- Admin Bot: логи администраторских действий
- Player Bot: логи действий игроков

### Метрики
- Количество активных пользователей
- Статистика игр и сессий
- Производительность ботов

## Troubleshooting

### Частые проблемы

1. **Бот не отвечает**:
   - Проверьте токен бота
   - Убедитесь, что Redis запущен
   - Проверьте логи на ошибки

2. **Ошибки API**:
   - Проверьте доступность backend сервисов
   - Убедитесь в правильности URL в конфигурации

3. **Проблемы с webhook**:
   - Проверьте SSL сертификат
   - Убедитесь, что webhook URL доступен извне
   - Проверьте WEBHOOK_SECRET

### Логи и отладка

```bash
# Просмотр логов Docker контейнеров
docker-compose logs -f admin-bot
docker-compose logs -f player-bot

# Проверка состояния Redis
redis-cli ping

# Тестирование API endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
```

## Безопасность

### Рекомендации
1. Используйте сильные WEBHOOK_SECRET
2. Ограничьте доступ к Redis
3. Используйте HTTPS для webhook
4. Регулярно обновляйте зависимости
5. Мониторьте логи на подозрительную активность

### Переменные окружения
Никогда не коммитьте файлы .env в репозиторий. Используйте:
- Docker secrets в продакшне
- Системы управления секретами (HashiCorp Vault, AWS Secrets Manager)

## Масштабирование

### Горизонтальное масштабирование
- Запустите несколько экземпляров ботов
- Используйте Redis Cluster для FSM storage
- Настройте load balancer для webhook

### Вертикальное масштабирование
- Увеличьте ресурсы контейнеров
- Оптимизируйте Redis конфигурацию
- Используйте connection pooling для HTTP клиентов

## Поддержка

Для получения поддержки:
1. Проверьте документацию
2. Изучите логи системы
3. Создайте issue в репозитории с подробным описанием проблемы