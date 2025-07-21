# Руководство пользователя Game Telegram

## Содержание

1. [Введение](#введение)
2. [Быстрый старт](#быстрый-старт)
3. [Пользовательские сценарии](#пользовательские-сценарии)
4. [Администрирование](#администрирование)
5. [Troubleshooting](#troubleshooting)
6. [FAQ](#faq)

---

## Введение

Game Telegram - это комплексная микросервисная платформа для создания и проведения интерактивных игр через Telegram ботов. Система поддерживает различные типы игр (викторины, "100 к одному") и обеспечивает масштабируемость для множественных игровых сессий.

### Ключевые возможности

- 🤖 **Двухботовая система**: отдельные боты для администраторов и игроков
- 🎯 **Множественные типы игр**: викторины, семейные игры, расширяемая архитектура
- ⚡ **Игра в реальном времени**: мгновенная обработка ответов и результатов
- 📊 **Продвинутая аналитика**: подробная статистика игр и игроков
- 👥 **Управление пользователями**: полные профили, аутентификация и авторизация
- 🔧 **Панель администратора**: полный административный контроль через интерфейс бота
- 📱 **Мобильная оптимизация**: оптимизировано для мобильного Telegram

### Архитектура системы

```mermaid
graph TB
    subgraph "Пользователи"
        ADMIN[👨‍💼 Администраторы]
        PLAYERS[👥 Игроки]
    end
    
    subgraph "Telegram Боты"
        AB[🤖 Admin Bot<br/>@your_admin_bot]
        PB[🎮 Player Bot<br/>@your_player_bot]
    end
    
    subgraph "Основные сервисы"
        UM[👤 User Manager<br/>:8001]
        GE[🎯 Game Engine<br/>:8002]
        SM[🎪 Session Manager<br/>:8003]
        NS[📢 Notification Service<br/>:8004]
        AS[📊 Analytics Service<br/>:8005]
    end
    
    subgraph "Инфраструктура"
        PG[(🐘 PostgreSQL<br/>:5432)]
        RD[(🔴 Redis<br/>:6379)]
        NGINX[🔀 Nginx<br/>:80/443]
    end
    
    ADMIN --> AB
    PLAYERS --> PB
    AB --> UM
    AB --> GE
    AB --> SM
    PB --> UM
    PB --> GE
    PB --> SM
    
    UM --> PG
    GE --> PG
    AS --> PG
    SM --> RD
    NS --> RD
```

### Настройка ботов

> **Важно**: Перед началом работы убедитесь, что у вас есть токены для двух Telegram ботов:
> - **Admin Bot** - для администраторов (например: `@your_admin_bot`)
> - **Player Bot** - для игроков (например: `@your_player_bot`)
> 
> Получить токены можно у [@BotFather](https://t.me/botfather) в Telegram.

---

## Быстрый старт

### Системные требования

#### Минимальные требования
- **CPU**: 4 ядра
- **RAM**: 8GB
- **Диск**: 50GB SSD
- **Сеть**: 100 Mbps

#### Рекомендуемые требования
- **CPU**: 8+ ядер
- **RAM**: 16GB+
- **Диск**: 100GB+ SSD
- **Сеть**: 1 Gbps

### Необходимое ПО

```bash
# Обязательное ПО
- Docker 24.0+
- Docker Compose 2.0+
- Git

# Дополнительно (для разработки)
- Python 3.11+
- PostgreSQL 15+
- Redis 7.0+
```

### Шаг 1: Клонирование и настройка

```bash
# 1. Клонируем репозиторий
git clone https://github.com/your-org/game-telegram.git
cd game-telegram

# 2. Копируем файл конфигурации
cp .env.example .env

# 3. Редактируем .env файл
nano .env
```

### Шаг 2: Конфигурация окружения

Отредактируйте файл `.env` со своими настройками:

```bash
# Токены Telegram ботов (ОБЯЗАТЕЛЬНО!)
ADMIN_BOT_TOKEN=1234567890:AAEhBOweik9ai2u5cg6XkhZeQ2lOd3L2zs8
PLAYER_BOT_TOKEN=0987654321:AAFhCPxfjk8bj3v6dh7YliAfR3mPe4M3at9

# Конфигурация базы данных
DATABASE_URL=postgresql://gameuser:gamepass@postgres:5432/gamedb
POSTGRES_DB=gamedb
POSTGRES_USER=gameuser
POSTGRES_PASSWORD=gamepass

# Redis конфигурация
REDIS_URL=redis://redis:6379

# Безопасность
JWT_SECRET=your_super_secret_jwt_key_here_change_this
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Игровые настройки
MAX_PLAYERS_PER_SESSION=50
SESSION_TIMEOUT_MINUTES=60
QUESTION_TIMEOUT_SECONDS=30

# Мониторинг
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=admin

# Логирование
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Шаг 3: Запуск системы

```bash
# 1. Запускаем все сервисы
docker-compose up -d

# 2. Проверяем статус сервисов
docker-compose ps

# 3. Проверяем логи (если нужно)
docker-compose logs -f
```

### Шаг 4: Проверка работоспособности

```bash
# 1. Проверяем здоровье сервисов
curl http://localhost:8001/health  # User Manager
curl http://localhost:8002/health  # Game Engine
curl http://localhost:8003/health  # Session Manager
curl http://localhost:8004/health  # Notification Service
curl http://localhost:8005/health  # Analytics Service

# 2. Проверяем базу данных
docker-compose exec postgres psql -U gameuser -d gamedb -c "SELECT version();"

# 3. Проверяем Redis
docker-compose exec redis redis-cli ping
```

### Шаг 5: Загрузка демо-данных

```bash
# 1. Загружаем примеры игр
python demo/scripts/load_sample_games.py --all

# 2. Создаем тестовых пользователей
python demo/scripts/create_test_users.py --count 10 --admin

# 3. Проверяем загруженные данные
curl http://localhost:8002/api/v1/games/
```

### Шаг 6: Доступ к системе

После успешного запуска у вас будет доступ к:

- **Admin Bot**: Найдите `@your_admin_bot` в Telegram и запустите его
- **Player Bot**: Найдите `@your_player_bot` в Telegram и запустите его
- **API документация**: http://localhost:8002/docs
- **Grafana мониторинг**: http://localhost:3000 (admin/admin)
- **Prometheus метрики**: http://localhost:9090

### Первоначальная проверка

1. **Откройте Admin Bot** в Telegram:
   ```
   /start
   ```
   Вы должны увидеть главное меню администратора.

2. **Откройте Player Bot** в Telegram:
   ```
   /start
   ```
   Вы должны увидеть приветственное сообщение игрока.

3. **Создайте тестовую игру** через Admin Bot:
   - Нажмите "🎮 Управление играми"
   - Выберите "➕ Создать новую игру"
   - Следуйте инструкциям

---

## Пользовательские сценарии

### Сценарий 1: Создание игры (Администратор)

#### Шаг 1: Запуск Admin Bot

1. Найдите вашего админ-бота в Telegram: `@your_admin_bot`
2. Запустите бота командой `/start`
3. Вы увидите главное меню:

```
🎮 Управление играми
📊 Аналитика
⚙️ Настройки
❓ Помощь
```

#### Шаг 2: Создание новой викторины

1. Нажмите **"🎮 Управление играми"**
2. Выберите **"➕ Создать новую игру"**
3. Выберите тип игры: **"📝 Викторина"**

#### Шаг 3: Настройка игры

```
Название игры: История России
Описание: Викторина по истории России для школьников
Категория: Образование

⏱️ Время на вопрос: 30 секунд
👥 Максимум игроков: 20
🎯 Показывать правильные ответы: Да
🔄 Перемешивать вопросы: Да
```

#### Шаг 4: Добавление вопросов

**Пример вопроса с одиночным выбором:**

```
Вопрос: В каком году была основана Москва?
Тип: Одиночный выбор

Варианты ответов:
A) 1147
B) 1156  
C) 1174
D) 1185

Правильный ответ: A
Баллы за ответ: 10
Время на ответ: 25 секунд
Объяснение: Москва была основана в 1147 году князем Юрием Долгоруким
```

#### Шаг 5: Сохранение игры

1. Просмотрите созданную игру
2. Протестируйте несколько вопросов
3. Нажмите **"💾 Сохранить игру"**

### Сценарий 2: Подключение к игре (Игрок)

#### Шаг 1: Запуск Player Bot

1. Найдите бота игрока в Telegram: `@your_player_bot`
2. Запустите бота командой `/start`
3. Настройте профиль при первом запуске

#### Шаг 2: Подключение по коду

1. Нажмите **"🎯 Присоединиться к игре"**
2. Выберите **"🔢 Ввести код"**
3. Введите код сессии (например: `ABC123`)

```
✅ Код принят!
🎮 Игра: История России
👥 Игроков: 5/15
⏳ Ожидание начала игры...
```

#### Шаг 3: Альтернативные способы подключения

**По QR-коду:**
1. Нажмите **"📱 Сканировать QR-код"**
2. Наведите камеру на QR-код от администратора

**По ссылке:**
Просто перейдите по ссылке:
```
https://t.me/your_player_bot?start=join_ABC123
```

### Сценарий 3: Проведение викторины

#### Подготовка (Администратор)

1. **Создайте игровую сессию:**
   - Перейдите в "🎮 Управление играми"
   - Выберите игру "История России"
   - Нажмите "▶️ Создать сессию"

2. **Настройте сессию:**
   ```
   👥 Максимум игроков: 15
   🚀 Автостарт: Выключен
   ⏰ Время ожидания: 5 минут
   🔗 Разрешить поздние подключения: Да
   ```

3. **Получите код подключения:**
   ```
   ✅ Сессия создана!
   
   🔗 Код для подключения: ABC123
   📱 QR-код: [QR-код изображение]
   🌐 Ссылка: https://t.me/your_player_bot?start=join_ABC123
   
   👥 Игроков подключено: 0/15
   ⏱️ Статус: Ожидание игроков
   ```

#### Проведение игры

1. **Ожидание игроков:**
   ```
   👥 Подключенные игроки (8/15):
   1. 👤 Алексей (@alex_user) ✅ Готов
   2. 👤 Мария (@maria_user) ✅ Готов
   3. 👤 Дмитрий (@dmitry_user) ✅ Готов
   ...
   ```

2. **Запуск игры:**
   - Нажмите **"▶️ Начать игру"**
   - Игроки получат уведомление о начале

3. **Управление во время игры:**
   ```
   ❓ Вопрос 3/10: В каком году была основана Москва?
   
   ⏱️ Осталось времени: 15 секунд
   👥 Ответили: 6/8 игроков
   
   Быстрые действия:
   ⏭️ Пропустить вопрос
   ⏸️ Приостановить таймер
   📢 Отправить подсказку
   ```

#### Завершение игры

```
🏁 Игра завершена!

🏆 Финальные результаты:
1. 👑 Алексей - 95 баллов (9/10 правильных)
2. 🥈 Мария - 85 баллов (8/10 правильных)
3. 🥉 Дмитрий - 80 баллов (8/10 правильных)

📊 Статистика сессии:
• Продолжительность: 18 минут
• Средний балл: 74.5
• Процент завершения: 89%

💾 Результаты сохранены
📊 Подробная аналитика
🔄 Создать новую сессию
```

### Сценарий 4: Просмотр результатов

#### Для администратора

1. **Общая аналитика:**
   ```
   📊 Аналитика за последние 30 дней
   
   🎮 Игры:
   - Всего проведено: 156 игр
   - Среднее время игры: 18 минут
   - Самая популярная: "История России" (23 игры)
   
   👥 Игроки:
   - Уникальных игроков: 342
   - Средне игроков в сессии: 8.5
   - Возвращающихся игроков: 67%
   ```

2. **Детальная статистика игры:**
   ```
   🎯 Игра: "История России"
   
   📊 Общие показатели:
   - Проведено сессий: 23
   - Всего игроков: 187
   - Средний балл: 74.5/100
   - Процент завершения: 89%
   
   ❓ Статистика по вопросам:
   1. "Основание Москвы" - 78% правильных ответов
   2. "Куликовская битва" - 65% правильных ответов
   3. "Петр I" - 82% правильных ответов
   ```

#### Для игрока

1. **Личная статистика:**
   ```
   📊 Ваша статистика
   
   🎮 Общие показатели:
   • Игр сыграно: 23
   • Побед: 7 (30%)
   • Призовых мест: 15 (65%)
   • Средний балл: 74.5
   
   🏆 Достижения (12/25):
   ✅ Первая игра
   ✅ Первая победа
   ✅ 10 игр сыграно
   ✅ Быстрый игрок (ответ за 5 сек)
   ✅ Знаток истории (90% в категории)
   ```

---

## Администрирование

### Мониторинг системы

#### Проверка состояния сервисов

```bash
# 1. Статус Docker контейнеров
docker-compose ps

# 2. Использование ресурсов
docker stats

# 3. Логи сервисов
docker-compose logs -f [service_name]

# 4. Проверка здоровья API
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
```

#### Мониторинг через Grafana

1. **Откройте Grafana**: http://localhost:3000
2. **Войдите**: admin/admin (измените пароль при первом входе)
3. **Основные дашборды:**
   - System Metrics - системные метрики
   - Game Analytics - игровая аналитика
   - User Activity - активность пользователей

#### Ключевые метрики для мониторинга

```bash
# Системные метрики
- CPU usage < 80%
- Memory usage < 85%
- Disk usage < 90%
- Network latency < 100ms

# Приложение
- Response time < 500ms
- Error rate < 1%
- Active sessions
- Games per hour
```

### Управление пользователями

#### Через Admin Bot

1. **Просмотр пользователей:**
   ```
   👥 Управление пользователями
   
   📊 Статистика:
   • Всего пользователей: 1,247
   • Активных за сегодня: 156
   • Новых за неделю: 89
   • Заблокированных: 3
   
   Действия:
   🔍 Поиск пользователя
   📋 Список администраторов
   🚫 Заблокированные пользователи
   📊 Детальная статистика
   ```

2. **Управление правами:**
   ```
   👤 Пользователь: @username
   
   📋 Информация:
   • ID: 123456789
   • Имя: Иван Иванов
   • Статус: Активный
   • Регистрация: 15.01.2024
   • Последняя активность: 2 часа назад
   
   🔧 Действия:
   ⭐ Сделать администратором
   🚫 Заблокировать пользователя
   📊 Статистика игр
   💬 Отправить сообщение
   ```

#### Через API

```bash
# Получить список пользователей
curl -X GET "http://localhost:8001/api/v1/users/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Заблокировать пользователя
curl -X POST "http://localhost:8001/api/v1/users/123456789/block" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Сделать пользователя администратором
curl -X POST "http://localhost:8001/api/v1/users/123456789/make-admin" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Резервное копирование

#### Автоматическое резервное копирование

Создайте скрипт `/scripts/backup.sh`:

```bash
#!/bin/bash

# Конфигурация
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Создаем директорию для бэкапов
mkdir -p $BACKUP_DIR

# Бэкап базы данных PostgreSQL
echo "🗄️ Создание бэкапа базы данных..."
docker-compose exec -T postgres pg_dump -U gameuser gamedb > $BACKUP_DIR/gamedb_$DATE.sql

# Бэкап Redis
echo "💾 Создание бэкапа Redis..."
docker-compose exec -T redis redis-cli --rdb /data/dump_$DATE.rdb
docker cp $(docker-compose ps -q redis):/data/dump_$DATE.rdb $BACKUP_DIR/

# Бэкап файлов загрузок
echo "📁 Создание бэкапа файлов..."
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C $(docker volume inspect game-telegram_media-storage -f '{{.Mountpoint}}') .

# Очистка старых бэкапов
echo "🧹 Очистка старых бэкапов..."
find $BACKUP_DIR -name "*.sql" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.rdb" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "✅ Бэкап завершен: $BACKUP_DIR"
```

#### Настройка cron для автоматических бэкапов

```bash
# Добавить в crontab
crontab -e

# Ежедневный бэкап в 2:00
0 2 * * * /path/to/game-telegram/scripts/backup.sh

# Еженедельный полный бэкап в воскресенье в 1:00
0 1 * * 0 /path/to/game-telegram/scripts/full-backup.sh
```

#### Восстановление из бэкапа

```bash
#!/bin/bash
# scripts/restore.sh

BACKUP_FILE=$1
if [ -z "$BACKUP_FILE" ]; then
    echo "Использование: $0 <backup_file.sql>"
    exit 1
fi

echo "⚠️ Остановка сервисов..."
docker-compose stop

echo "🗄️ Восстановление базы данных..."
docker-compose start postgres
sleep 10
cat $BACKUP_FILE | docker-compose exec -T postgres psql -U gameuser -d gamedb

echo "🚀 Запуск всех сервисов..."
docker-compose up -d

echo "✅ Восстановление завершено"
```

### Обновление системы

#### Обновление приложения

```bash
#!/bin/bash
# scripts/update-application.sh

echo "📦 Обновление Game Telegram..."

# 1. Создаем бэкап перед обновлением
echo "💾 Создание бэкапа..."
./scripts/backup.sh

# 2. Получаем последние изменения
echo "📥 Получение обновлений..."
git pull origin main

# 3. Обновляем образы
echo "🔄 Обновление Docker образов..."
docker-compose pull

# 4. Пересобираем кастомные образы
echo "🔨 Пересборка образов..."
docker-compose build --no-cache

# 5. Выполняем миграции базы данных
echo "🗄️ Выполнение миграций..."
docker-compose run --rm game-engine alembic upgrade head
docker-compose run --rm user-manager alembic upgrade head

# 6. Перезапускаем сервисы с нулевым временем простоя
echo "🚀 Rolling update сервисов..."
for service in user-manager game-engine session-manager analytics-service notification-service; do
    echo "Обновление $service..."
    docker-compose up -d --no-deps $service
    sleep 30
    
    # Проверяем здоровье сервиса
    if ! curl -f http://localhost:800X/health; then
        echo "❌ Ошибка обновления $service"
        exit 1
    fi
done

# 7. Обновляем боты
echo "🤖 Обновление ботов..."
docker-compose up -d --no-deps admin-bot player-bot

echo "✅ Обновление завершено успешно!"
```

#### Откат к предыдущей версии

```bash
#!/bin/bash
# scripts/rollback.sh

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Использование: $0 <git_tag_or_commit>"
    exit 1
fi

echo "⏪ Откат к версии $VERSION..."

# 1. Остановка сервисов
docker-compose stop

# 2. Откат кода
git checkout $VERSION

# 3. Восстановление из бэкапа (если нужно)
read -p "Восстановить базу данных из бэкапа? (y/N): " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗄️ Выберите файл бэкапа:"
    ls -la /backups/*.sql | tail -5
    read -p "Введите имя файла: " BACKUP_FILE
    ./scripts/restore.sh /backups/$BACKUP_FILE
fi

# 4. Пересборка и запуск
docker-compose build
docker-compose up -d

echo "✅ Откат завершен"
```

---

## Troubleshooting

### Частые проблемы и их решения

#### 1. Боты не отвечают

**Симптомы:**
- Боты не реагируют на команды
- Сообщение "Bot is not responding"
- Ошибки в логах ботов

**Диагностика:**
```bash
# Проверяем статус ботов
docker-compose ps admin-bot player-bot

# Смотрим логи
docker-compose logs admin-bot
docker-compose logs player-bot

# Проверяем токены
grep BOT_TOKEN .env
```

**Решения:**

1. **Проверьте токены ботов:**
   ```bash
   # Проверьте правильность токенов в .env
   nano .env
   
   # Перезапустите ботов
   docker-compose restart admin-bot player-bot
   ```

2. **Проверьте подключение к Telegram API:**
   ```bash
   # Тест подключения
   curl -X GET "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"
   ```

3. **Проверьте webhook настройки:**
   ```bash
   # Удалите webhook (если используется polling)
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook"
   ```

#### 2. Ошибки подключения к базе данных

**Симптомы:**
- "Connection refused" в логах
- Сервисы не могут подключиться к PostgreSQL
- Ошибки при выполнении запросов

**Диагностика:**
```bash
# Проверяем статус PostgreSQL
docker-compose ps postgres

# Проверяем логи
docker-compose logs postgres

# Тестируем подключение
docker-compose exec postgres psql -U gameuser -d gamedb -c "SELECT version();"
```

**Решения:**

1. **Перезапуск базы данных:**
   ```bash
   docker-compose restart postgres
   
   # Ждем готовности
   docker-compose exec postgres pg_isready -U gameuser -d gamedb
   ```

2. **Проверка конфигурации:**
   ```bash
   # Проверьте настройки в .env
   grep DATABASE_URL .env
   grep POSTGRES .env
   ```

3. **Восстановление из бэкапа:**
   ```bash
   # Если данные повреждены
   ./scripts/restore.sh /backups/latest_backup.sql
   ```

#### 3. Redis недоступен

**Симптомы:**
- Ошибки кэширования
- Проблемы с сессиями
- "Connection refused" для Redis

**Диагностика:**
```bash
# Проверяем Redis
docker-compose ps redis
docker-compose logs redis

# Тестируем подключение
docker-compose exec redis redis-cli ping
```

**Решения:**

1. **Перезапуск Redis:**
   ```bash
   docker-compose restart redis
   ```

2. **Очистка данных Redis:**
   ```bash
   docker-compose exec redis redis-cli FLUSHALL
   ```

#### 4. Высокое использование ресурсов

**Симптомы:**
- Медленная работа системы
- Высокая загрузка CPU/памяти
- Таймауты запросов

**Диагностика:**
```bash
# Мониторинг ресурсов
docker stats

# Проверка дискового пространства
df -h

# Анализ логов
docker-compose logs | grep -i error
```

**Решения:**

1. **Масштабирование сервисов:**
   ```bash
   # Увеличиваем количество реплик
   docker-compose up -d --scale game-

engine=2

   # Оптимизация базы данных
   docker-compose exec postgres psql -U gameuser -d gamedb -c "VACUUM ANALYZE;"
   ```

2. **Очистка логов:**
   ```bash
   # Очистка старых логов Docker
   docker system prune -f
   
   # Ротация логов приложения
   find /var/log -name "*.log" -mtime +7 -delete
   ```

3. **Мониторинг производительности:**
   ```bash
   # Установка htop для мониторинга
   sudo apt install htop
   
   # Мониторинг в реальном времени
   htop
   ```

#### 5. Игроки не могут подключиться к игре

**Симптомы:**
- Ошибка "Игра не найдена"
- Неверный код сессии
- Сессия уже завершена

**Диагностика:**
```bash
# Проверяем активные сессии
curl http://localhost:8003/api/v1/sessions/active

# Проверяем логи Session Manager
docker-compose logs session-manager

# Проверяем Redis
docker-compose exec redis redis-cli keys "session:*"
```

**Решения:**

1. **Проверьте код сессии:**
   - Убедитесь, что код введен правильно
   - Проверьте, что сессия еще активна
   - Создайте новую сессию, если старая истекла

2. **Перезапуск Session Manager:**
   ```bash
   docker-compose restart session-manager
   ```

#### 6. Проблемы с QR-кодами

**Симптомы:**
- QR-код не генерируется
- QR-код не сканируется
- Ошибка при переходе по ссылке

**Решения:**

1. **Проверьте настройки URL:**
   ```bash
   # Проверьте WEBHOOK_URL в .env
   grep WEBHOOK_URL .env
   ```

2. **Тест генерации QR:**
   ```bash
   # Тест через API
   curl -X POST "http://localhost:8003/api/v1/sessions/ABC123/qr"
   ```

### Логи и диагностика

#### Основные файлы логов

```bash
# Логи всех сервисов
docker-compose logs

# Логи конкретного сервиса
docker-compose logs admin-bot
docker-compose logs player-bot
docker-compose logs game-engine
docker-compose logs session-manager
docker-compose logs user-manager
docker-compose logs analytics-service
docker-compose logs notification-service

# Логи инфраструктуры
docker-compose logs postgres
docker-compose logs redis
docker-compose logs nginx
```

#### Анализ логов

```bash
# Поиск ошибок
docker-compose logs | grep -i error

# Поиск предупреждений
docker-compose logs | grep -i warning

# Логи за последний час
docker-compose logs --since 1h

# Следить за логами в реальном времени
docker-compose logs -f
```

#### Уровни логирования

Настройте уровень логирования в `.env`:

```bash
# Уровни: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Для отладки используйте DEBUG
LOG_LEVEL=DEBUG
```

### Восстановление после сбоев

#### Полное восстановление системы

```bash
#!/bin/bash
# scripts/disaster-recovery.sh

echo "🚨 Начало аварийного восстановления..."

# 1. Остановка всех сервисов
echo "⏹️ Остановка сервисов..."
docker-compose down

# 2. Очистка поврежденных данных
echo "🧹 Очистка поврежденных данных..."
docker volume rm game-telegram_postgres-data
docker volume rm game-telegram_redis-data

# 3. Восстановление из последнего бэкапа
echo "📦 Восстановление из бэкапа..."
LATEST_BACKUP=$(ls -t /backups/*.sql | head -1)
echo "Используется бэкап: $LATEST_BACKUP"

# 4. Пересоздание томов и запуск
echo "🚀 Пересоздание и запуск..."
docker-compose up -d postgres redis
sleep 30

# 5. Восстановление данных
echo "🗄️ Восстановление базы данных..."
cat $LATEST_BACKUP | docker-compose exec -T postgres psql -U gameuser -d gamedb

# 6. Запуск всех сервисов
echo "▶️ Запуск всех сервисов..."
docker-compose up -d

# 7. Проверка здоровья
echo "🏥 Проверка здоровья системы..."
sleep 60
./scripts/health-check.sh

echo "✅ Аварийное восстановление завершено"
```

#### Проверка целостности данных

```bash
#!/bin/bash
# scripts/data-integrity-check.sh

echo "🔍 Проверка целостности данных..."

# Проверка базы данных
echo "🗄️ Проверка PostgreSQL..."
docker-compose exec postgres psql -U gameuser -d gamedb -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables;
"

# Проверка Redis
echo "💾 Проверка Redis..."
docker-compose exec redis redis-cli info keyspace

# Проверка файлов
echo "📁 Проверка файлов..."
docker run --rm -v game-telegram_media-storage:/data alpine du -sh /data

echo "✅ Проверка завершена"
```

---

## FAQ

### Общие вопросы

#### Что такое Game Telegram?

Game Telegram - это комплексная микросервисная платформа для создания и проведения интерактивных игр через Telegram ботов. Система поддерживает различные типы игр (викторины, семейные игры) и обеспечивает масштабируемость для множественных игровых сессий.

#### Какие типы игр поддерживаются?

Система поддерживает:
- **Викторины** с различными типами вопросов (одиночный выбор, множественный выбор, правда/ложь, текстовый ввод)
- **Семейные игры** (аналог "100 к одному")
- **Расширяемая архитектура** для добавления новых типов игр

#### Сколько игроков может участвовать одновременно?

По умолчанию система поддерживает до 50 игроков в одной сессии. Это значение можно изменить в настройках:

```bash
# В файле .env
MAX_PLAYERS_PER_SESSION=100
```

#### Можно ли проводить несколько игр одновременно?

Да, система поддерживает множественные параллельные игровые сессии. Каждая сессия имеет уникальный код и работает независимо.

### Настройка и установка

#### Какие системные требования?

**Минимальные требования:**
- CPU: 4 ядра
- RAM: 8GB
- Диск: 50GB SSD
- Сеть: 100 Mbps

**Рекомендуемые требования:**
- CPU: 8+ ядер
- RAM: 16GB+
- Диск: 100GB+ SSD
- Сеть: 1 Gbps

#### Как получить токены для ботов?

1. Откройте [@BotFather](https://t.me/botfather) в Telegram
2. Создайте нового бота командой `/newbot`
3. Следуйте инструкциям для настройки имени и username
4. Получите токен и сохраните его в файле `.env`
5. Повторите процесс для второго бота

#### Можно ли использовать внешнюю базу данных?

Да, вы можете использовать внешние PostgreSQL и Redis. Просто измените настройки в `.env`:

```bash
# Внешний PostgreSQL
DATABASE_URL=postgresql://user:password@external-host:5432/gamedb

# Внешний Redis
REDIS_URL=redis://external-redis-host:6379/0
```

#### Как настроить SSL/HTTPS?

1. **Получите SSL сертификат** (Let's Encrypt, коммерческий CA)
2. **Поместите сертификаты** в папку `./ssl/`
3. **Обновите nginx.conf** с настройками SSL
4. **Перезапустите nginx:**
   ```bash
   docker-compose restart nginx
   ```

### Использование системы

#### Как создать свою игру?

1. **Через Admin Bot:**
   - Запустите админ-бота
   - Выберите "🎮 Управление играми"
   - Нажмите "➕ Создать новую игру"
   - Следуйте пошаговым инструкциям

2. **Через импорт JSON файла:**
   - Создайте JSON файл по образцу из `game-packs/`
   - Загрузите через админ-бота
   - Проверьте и активируйте игру

#### Как игроки подключаются к игре?

Игроки могут подключиться тремя способами:
1. **По коду сессии** - ввести код в боте игрока
2. **По QR-коду** - отсканировать QR-код камерой
3. **По ссылке** - перейти по прямой ссылке

#### Можно ли изменить игру во время сессии?

Во время активной сессии нельзя изменять вопросы, но администратор может:
- Пропустить текущий вопрос
- Приостановить/возобновить игру
- Завершить игру досрочно
- Отправить сообщения игрокам

#### Как посмотреть результаты игры?

**Для администратора:**
- Через админ-бота: "📊 Аналитика"
- Через Grafana: http://localhost:3000
- Через API: `/api/v1/analytics/games/{game_id}`

**Для игрока:**
- Через бота игрока: "📊 Мои результаты"
- Автоматически после завершения игры

### Технические вопросы

#### Как обновить систему?

```bash
# Автоматическое обновление
./scripts/update-application.sh

# Ручное обновление
git pull origin main
docker-compose pull
docker-compose build --no-cache
docker-compose up -d
```

#### Как сделать резервную копию?

```bash
# Ручной бэкап
./scripts/backup.sh

# Автоматический бэкап (cron)
0 2 * * * /path/to/game-telegram/scripts/backup.sh
```

#### Как масштабировать систему?

1. **Горизонтальное масштабирование:**
   ```bash
   # Увеличение реплик сервисов
   docker-compose up -d --scale game-engine=3 --scale session-manager=2
   ```

2. **Kubernetes развертывание:**
   ```bash
   kubectl apply -f k8s/
   kubectl scale deployment game-engine --replicas=5
   ```

#### Как мониторить производительность?

1. **Grafana дашборды:** http://localhost:3000
2. **Prometheus метрики:** http://localhost:9090
3. **Логи приложений:**
   ```bash
   docker-compose logs -f
   ```
4. **Системные метрики:**
   ```bash
   docker stats
   htop
   ```

#### Что делать при высокой нагрузке?

1. **Увеличьте ресурсы контейнеров:**
   ```yaml
   # В docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 2G
         cpus: '2'
   ```

2. **Масштабируйте сервисы:**
   ```bash
   docker-compose up -d --scale game-engine=3
   ```

3. **Оптимизируйте базу данных:**
   ```bash
   docker-compose exec postgres psql -U gameuser -d gamedb -c "VACUUM ANALYZE;"
   ```

### Безопасность

#### Как обеспечить безопасность системы?

1. **Используйте сильные пароли:**
   ```bash
   # Генерация случайных паролей
   openssl rand -base64 32
   ```

2. **Регулярно обновляйте систему:**
   ```bash
   ./scripts/update-application.sh
   ```

3. **Настройте файрвол:**
   ```bash
   # Разрешить только необходимые порты
   ufw allow 80,443,22/tcp
   ufw enable
   ```

4. **Мониторьте логи безопасности:**
   ```bash
   docker-compose logs | grep -i "failed\|error\|unauthorized"
   ```

#### Как защитить API?

1. **JWT токены** используются для аутентификации
2. **Rate limiting** предотвращает злоупотребления
3. **Input validation** защищает от инъекций
4. **HTTPS** шифрует трафик

### Ограничения системы

#### Технические ограничения

- **Максимум игроков в сессии:** 50 (настраивается)
- **Максимум активных сессий:** Ограничено ресурсами сервера
- **Размер файлов игр:** 10MB (настраивается)
- **Время жизни сессии:** 60 минут (настраивается)
- **Время на вопрос:** 30 секунд (настраивается)

#### Ограничения Telegram API

- **Сообщения в секунду:** 30 сообщений/сек на бота
- **Размер сообщения:** 4096 символов
- **Размер файла:** 50MB для ботов
- **Inline клавиатуры:** До 100 кнопок

#### Рекомендации по использованию

1. **Не превышайте лимиты Telegram API**
2. **Регулярно очищайте старые данные**
3. **Мониторьте использование ресурсов**
4. **Делайте регулярные бэкапы**
5. **Тестируйте игры перед проведением**

### Поддержка и сообщество

#### Где получить помощь?

1. **Документация:** Изучите полную документацию в папке `docs/`
2. **GitHub Issues:** Сообщите о проблемах или запросите функции
3. **Логи системы:** Проверьте логи для диагностики проблем
4. **Community:** Присоединяйтесь к сообществу разработчиков

#### Как сообщить об ошибке?

1. **Соберите информацию:**
   ```bash
   # Версия системы
   git describe --tags
   
   # Логи ошибки
   docker-compose logs > error-logs.txt
   
   # Конфигурация (без секретов)
   cat .env | grep -v TOKEN | grep -v PASSWORD
   ```

2. **Создайте issue на GitHub** с подробным описанием
3. **Приложите логи и конфигурацию**

#### Как предложить улучшение?

1. **Создайте Feature Request** на GitHub
2. **Опишите желаемую функциональность**
3. **Объясните, как это поможет пользователям**
4. **Предложите варианты реализации**

---

## Заключение

Поздравляем! Вы изучили полное руководство пользователя Game Telegram. Эта система предоставляет мощные возможности для создания и проведения интерактивных игр через Telegram ботов.

### Ключевые преимущества системы:

- 🚀 **Быстрый запуск** - система готова к работе за несколько минут
- 🎮 **Гибкость** - поддержка различных типов игр и настроек
- 📊 **Аналитика** - подробная статистика и мониторинг
- 🔧 **Простота управления** - интуитивный интерфейс через Telegram ботов
- 📈 **Масштабируемость** - от небольших групп до тысяч игроков
- 🛡️ **Безопасность** - современные стандарты защиты данных

### Следующие шаги:

1. **Установите систему** следуя инструкциям из раздела "Быстрый старт"
2. **Создайте первую игру** используя пользовательские сценарии
3. **Изучите возможности администрирования** для эффективного управления
4. **Настройте мониторинг** для контроля производительности
5. **Присоединяйтесь к сообществу** для обмена опытом

### Полезные ссылки:

- **Техническая документация:** [`docs/technical-documentation.md`](technical-documentation.md)
- **Руководство администратора:** [`docs/user-guide/admin-guide.md`](user-guide/admin-guide.md)
- **Руководство игрока:** [`docs/user-guide/player-guide.md`](user-guide/player-guide.md)
- **Руководство разработчика:** [`docs/developer-guide/developer-guide.md`](developer-guide/developer-guide.md)
- **Руководство по развертыванию:** [`docs/deployment/deployment-guide.md`](deployment/deployment-guide.md)

### Поддержка:

Если у вас возникли вопросы или проблемы:
1. Проверьте раздел [Troubleshooting](#troubleshooting)
2. Изучите [FAQ](#faq)
3. Обратитесь к технической документации
4. Создайте issue на GitHub

**Удачи в создании увлекательных игр! 🎮✨**

---

*Game Telegram - Making interactive gaming accessible through Telegram*

**Версия документа:** 1.0  
**Последнее обновление:** 2024-01-21  
**Совместимость:** Game Telegram v1.0+