# Руководство по развертыванию и тестированию

## Обзор

Этот документ содержит пошаговые инструкции по развертыванию, настройке и тестированию системы телеграм-бота для игр.

## Предварительные требования

### Системные требования

- Python 3.8+
- pip (менеджер пакетов Python)
- Git
- Доступ к интернету для работы с Telegram API

### Telegram боты

Для полноценной работы системы необходимо создать два бота:

1. **Админский бот** - для управления играми
2. **Игровой бот** - для участия игроков

#### Создание ботов

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания первого бота (админского)
4. Сохраните токен админского бота
5. Повторите процесс для создания второго бота (игрового)
6. Сохраните токен игрового бота

#### Настройка ботов

```bash
# Для админского бота
/setname Игровой Админ
/setdescription Бот для управления играми
/setuserpic [загрузите изображение админа]

# Для игрового бота  
/setname Игровой Бот
/setdescription Бот для участия в играх
/setuserpic [загрузите изображение игрока]
```

## Установка и настройка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd game-telegram
```

### 2. Создание виртуального окружения

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
# Токены ботов
ADMIN_BOT_TOKEN=your_admin_bot_token_here
PLAYER_BOT_TOKEN=your_player_bot_token_here

# ID администратора (ваш Telegram ID)
ROOT_ID=your_telegram_id_here

# Настройки хранения
GAME_PACKS_DIR=./game_packs
TEMP_DIR=./temp
QR_CODES_DIR=./temp/qr_codes

# Настройки игр
SESSION_CODE_LENGTH=6
SESSION_TIMEOUT_MINUTES=60
MAX_PLAYERS_PER_SESSION=50

# Логирование
LOG_LEVEL=INFO
LOG_FILE=./logs/bot.log
```

#### Как узнать свой Telegram ID

1. Отправьте сообщение боту [@userinfobot](https://t.me/userinfobot)
2. Скопируйте ваш ID из ответа
3. Вставьте в поле `ROOT_ID`

### 5. Создание необходимых директорий

```bash
mkdir -p game_packs/quiz
mkdir -p game_packs/hundred_to_one
mkdir -p temp/qr_codes
mkdir -p temp/exports
mkdir -p logs
```

## Тестирование системы

### Настройка для тестирования

Для тестирования с одним аккаунтом создайте два конфигурационных файла:

#### Конфигурация админа (`.env.admin`)

```env
ADMIN_BOT_TOKEN=your_admin_bot_token
PLAYER_BOT_TOKEN=your_player_bot_token
ROOT_ID=your_telegram_id
```

#### Конфигурация игрока (`.env.player`)

```env
ADMIN_BOT_TOKEN=your_admin_bot_token
PLAYER_BOT_TOKEN=your_player_bot_token
ROOT_ID=0
```

### Запуск для тестирования

#### Терминал 1 (Админ)

```bash
# Копируем конфигурацию админа
cp .env.admin .env

# Запускаем систему
python src/main.py
```

#### Терминал 2 (Игрок)

```bash
# В новом терминале
cd game-telegram

# Копируем конфигурацию игрока
cp .env.player .env

# Запускаем систему
python src/main.py
```

## Сценарии тестирования

### Тест 1: Создание и запуск викторины

#### Шаг 1: Подготовка игрового пака

Создайте файл `game_packs/quiz/test_quiz.json`:

```json
{
  "name": "Тестовая викторина",
  "description": "Простая викторина для тестирования",
  "type": "quiz",
  "settings": {
    "time_per_question": 30,
    "show_correct_answer": true,
    "points_per_correct": 10
  },
  "questions": [
    {
      "id": 1,
      "question": "Сколько будет 2+2?",
      "type": "multiple_choice",
      "options": ["3", "4", "5", "6"],
      "correct_answer": 1,
      "points": 10
    },
    {
      "id": 2,
      "question": "Столица России?",
      "type": "text_input",
      "correct_answers": ["Москва", "москва"],
      "case_sensitive": false,
      "points": 15
    }
  ]
}
```

#### Шаг 2: Тестирование админских функций

В админском боте:

1. `/start` - проверка приветствия
2. `/create_session test_quiz` - создание сессии
3. Сохраните код сессии и QR-код
4. `/start_game <session_id>` - запуск игры

#### Шаг 3: Тестирование игровых функций

В игровом боте:

1. `/start` - проверка приветствия
2. `/join <код_сессии>` - подключение к игре
3. Ответьте на вопросы викторины
4. Проверьте отображение результатов

### Тест 2: Игра "100 к 1"

#### Подготовка пака

Создайте файл `game_packs/hundred_to_one/test_hundred.json`:

```json
{
  "name": "Тестовая игра 100 к 1",
  "description": "Простая игра для тестирования",
  "type": "hundred_to_one",
  "settings": {
    "teams_count": 2,
    "rounds_count": 1,
    "wrong_answers_limit": 3
  },
  "rounds": [
    {
      "id": 1,
      "question": "Что едят на завтрак?",
      "type": "simple",
      "answers": [
        {"text": "Каша", "points": 40},
        {"text": "Яйца", "points": 30},
        {"text": "Хлеб", "points": 20},
        {"text": "Молоко", "points": 10}
      ]
    }
  ]
}
```

#### Тестирование

1. Создайте сессию: `/create_session test_hundred`
2. Подключите игроков
3. Запустите игру
4. Тестируйте ответы и подсчет очков

## Мониторинг и отладка

### Логирование

Логи сохраняются в файл `logs/bot.log`. Для просмотра в реальном времени:

```bash
tail -f logs/bot.log
```

### Уровни логирования

- `DEBUG` - детальная отладочная информация
- `INFO` - общая информация о работе
- `WARNING` - предупреждения
- `ERROR` - ошибки
- `CRITICAL` - критические ошибки

### Типичные проблемы и решения

#### Проблема: Бот не отвечает

**Решение:**
1. Проверьте токены ботов
2. Убедитесь, что боты запущены
3. Проверьте интернет-соединение

#### Проблема: Ошибка авторизации админа

**Решение:**
1. Проверьте правильность `ROOT_ID`
2. Убедитесь, что используете правильного бота

#### Проблема: Не создается QR-код

**Решение:**
1. Проверьте права доступа к директории `temp/qr_codes`
2. Установите библиотеку `qrcode`: `pip install qrcode[pil]`

#### Проблема: Игра не запускается

**Решение:**
1. Проверьте формат JSON-файла игрового пака
2. Убедитесь, что файл находится в правильной директории
3. Проверьте логи на наличие ошибок валидации

## Производственное развертывание

### Использование systemd (Linux)

Создайте файл `/etc/systemd/system/game-bot.service`:

```ini
[Unit]
Description=Game Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/game-telegram
Environment=PATH=/path/to/game-telegram/venv/bin
ExecStart=/path/to/game-telegram/venv/bin/python src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск сервиса:

```bash
sudo systemctl daemon-reload
sudo systemctl enable game-bot
sudo systemctl start game-bot
sudo systemctl status game-bot
```

### Использование Docker

Создайте `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "src/main.py"]
```

Создайте `docker-compose.yml`:

```yaml
version: '3.8'

services:
  game-bot:
    build: .
    env_file: .env
    volumes:
      - ./game_packs:/app/game_packs
      - ./temp:/app/temp
      - ./logs:/app/logs
    restart: unless-stopped
```

Запуск:

```bash
docker-compose up -d
```

## Резервное копирование

### Что нужно сохранять

1. **Игровые паки** - `game_packs/`
2. **Конфигурация** - `.env`
3. **Логи** - `logs/` (опционально)

### Скрипт резервного копирования

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup_$DATE"

mkdir -p $BACKUP_DIR
cp -r game_packs $BACKUP_DIR/
cp .env $BACKUP_DIR/
cp -r logs $BACKUP_DIR/

tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "Backup created: $BACKUP_DIR.tar.gz"
```

## Масштабирование

### Горизонтальное масштабирование

Для обработки большого количества пользователей:

1. Используйте Redis для хранения сессий
2. Разделите ботов по регионам
3. Используйте load balancer

### Вертикальное масштабирование

1. Увеличьте ресурсы сервера
2. Оптимизируйте базу данных
3. Используйте кэширование

## Безопасность

### Рекомендации

1. **Не публикуйте токены** в открытом доступе
2. **Используйте HTTPS** для webhook'ов
3. **Ограничьте доступ** к серверу
4. **Регулярно обновляйте** зависимости
5. **Мониторьте логи** на предмет подозрительной активности

### Настройка webhook (опционально)

Для production рекомендуется использовать webhook вместо polling:

```python
# В main.py
if settings.use_webhook:
    application.run_webhook(
        listen="0.0.0.0",
