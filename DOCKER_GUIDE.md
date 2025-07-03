# Docker и тестирование телеграм-бота

## 🐳 Запуск с Docker

### Быстрый старт

1. **Подготовьте конфигурацию:**
   ```bash
   # Скопируйте примеры конфигураций
   cp .env.example .env
   cp .env.admin.example .env.admin
   cp .env.player.example .env.player
   
   # Отредактируйте файлы, указав токены ботов
   ```

2. **Соберите образ:**
   ```bash
   docker build -t game-telegram-bot .
   ```

3. **Запустите в нужном режиме:**
   ```bash
   # Полный режим (оба бота)
   docker-compose --profile full up game-bot-full
   
   # Только админский бот
   docker-compose up game-bot-admin
   
   # Только игровой бот
   docker-compose up game-bot-player
   
   # Оба бота раздельно (для тестирования)
   docker-compose up game-bot-admin game-bot-player
   ```

## 🧪 Тестирование с одним аккаунтом

### Вариант 1: Два отдельных бота

Создайте двух ботов в @BotFather:

1. **Админский бот** - для управления играми
2. **Игровой бот** - для участия в играх

**Настройка .env.admin:**
```env
ADMIN_BOT_TOKEN=1111111111:AAEhBOweik6ad9r_QXMENQjEqZoHq9XYhBQ
PLAYER_BOT_TOKEN=1111111111:AAEhBOweik6ad9r_QXMENQjEqZoHq9XYhBQ
ROOT_ID=123456789
MODE=admin
```

**Настройка .env.player:**
```env
ADMIN_BOT_TOKEN=2222222222:AAFhCPxfjk7bd8s_RYNFOSjFrApIr8ZYiCR
PLAYER_BOT_TOKEN=2222222222:AAFhCPxfjk7bd8s_RYNFOSjFrApIr8ZYiCR
ROOT_ID=0
MODE=player
```

**Запуск:**
```bash
# Запускаем оба контейнера
docker-compose up game-bot-admin game-bot-player

# Или в фоне
docker-compose up -d game-bot-admin game-bot-player
```

### Вариант 2: Один бот, два режима

Используйте один бот-токен, но запускайте в разных режимах:

**Настройка .env.admin:**
```env
ADMIN_BOT_TOKEN=1111111111:AAEhBOweik6ad9r_QXMENQjEqZoHq9XYhBQ
PLAYER_BOT_TOKEN=1111111111:AAEhBOweik6ad9r_QXMENQjEqZoHq9XYhBQ
ROOT_ID=123456789
MODE=admin
```

**Настройка .env.player:**
```env
ADMIN_BOT_TOKEN=1111111111:AAEhBOweik6ad9r_QXMENQjEqZoHq9XYhBQ
PLAYER_BOT_TOKEN=1111111111:AAEhBOweik6ad9r_QXMENQjEqZoHq9XYhBQ
ROOT_ID=0
MODE=player
```

## 🔧 Локальная разработка

### Запуск без Docker

```bash
# Установите зависимости
pip install -r requirements.txt

# Запуск в полном режиме
python run.py

# Запуск только админского бота
python scripts/run_admin.py

# Запуск только игрового бота
python scripts/run_player.py
```

### Переменные окружения

```bash
# Установка режима через переменную окружения
export MODE=admin
python run.py

export MODE=player
python run.py

export MODE=both
python run.py
```

## 📋 Docker команды

### Основные команды

```bash
# Сборка образа
docker build -t game-telegram-bot .

# Запуск контейнера
docker run -d --name game-bot --env-file .env game-telegram-bot

# Просмотр логов
docker logs game-bot
docker logs -f game-bot  # следить за логами

# Остановка и удаление
docker stop game-bot
docker rm game-bot

# Вход в контейнер
docker exec -it game-bot bash
```

### Docker Compose команды

```bash
# Запуск сервисов
docker-compose up                    # все сервисы
docker-compose up game-bot-admin     # только админский
docker-compose up game-bot-player    # только игровой
docker-compose --profile full up     # полный режим

# Запуск в фоне
docker-compose up -d

# Остановка
docker-compose down

# Пересборка
docker-compose build
docker-compose up --build

# Просмотр логов
docker-compose logs
docker-compose logs game-bot-admin
docker-compose logs -f game-bot-player

# Статус сервисов
docker-compose ps
```

## 🗂️ Структура томов

Docker Compose создает следующие тома:

- `admin_logs` - логи админского бота
- `admin_temp` - временные файлы админского бота
- `player_logs` - логи игрового бота
- `player_temp` - временные файлы игрового бота
- `full_logs` - логи полного режима
- `full_temp` - временные файлы полного режима

### Доступ к данным

```bash
# Просмотр томов
docker volume ls

# Инспекция тома
docker volume inspect game-telegram_admin_logs

# Копирование файлов из тома
docker run --rm -v game-telegram_admin_logs:/data -v $(pwd):/backup alpine cp -r /data /backup/admin_logs_backup
```

## 🔍 Отладка

### Просмотр логов

```bash
# Логи конкретного сервиса
docker-compose logs game-bot-admin

# Последние 100 строк
docker-compose logs --tail=100 game-bot-admin

# Следить за логами в реальном времени
docker-compose logs -f game-bot-admin
```

### Вход в контейнер

```bash
# Вход в работающий контейнер
docker-compose exec game-bot-admin bash

# Запуск нового контейнера для отладки
docker run -it --rm --env-file .env.admin game-telegram-bot bash
```

### Проверка конфигурации

```bash
# Проверка переменных окружения
docker-compose exec game-bot-admin env

# Проверка конфигурационного файла
docker-compose exec game-bot-admin cat config.yaml

# Проверка структуры файлов
docker-compose exec game-bot-admin ls -la
```

## 🚀 Продакшен

### Оптимизированный Dockerfile

Для продакшена можно создать многоэтапную сборку:

```dockerfile
# Dockerfile.prod
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY src/ ./src/
COPY game_packs/ ./game_packs/
COPY config.yaml .
COPY run.py .

RUN mkdir -p logs temp temp/qr_codes
RUN useradd -m -u 1000 gamebot && chown -R gamebot:gamebot /app
USER gamebot

ENV PATH=/root/.local/bin:$PATH
CMD ["python", "run.py"]
```

### Docker Compose для продакшена

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  game-bot:
    build:
      context: .
      dockerfile: Dockerfile.prod
    restart: always
    env_file: .env
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./game_packs:/app/game_packs:ro
      - logs:/app/logs
      - temp:/app/temp
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  logs:
  temp:
```

## 📊 Мониторинг

### Healthcheck

Добавьте в Dockerfile:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1
```

### Логирование

Логи автоматически собираются Docker и доступны через:

```bash
# Просмотр логов
docker-compose logs

# Экспорт логов
docker-compose logs > bot_logs.txt
```

## 🔒 Безопасность

### Рекомендации

1. **Не включайте .env файлы в образ**
2. **Используйте Docker secrets для токенов**
3. **Запускайте от непривилегированного пользователя**
4. **Ограничьте ресурсы контейнера**

### Пример с ограничениями

```yaml
services:
  game-bot:
    # ...
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

Это руководство поможет вам эффективно использовать Docker для разработки и тестирования телеграм-бота!