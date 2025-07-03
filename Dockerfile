# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src/ ./src/
COPY game_packs/ ./game_packs/
COPY config.yaml .
COPY run.py .

# Создаем необходимые директории
RUN mkdir -p logs temp temp/qr_codes

# Создаем пользователя для запуска приложения
RUN useradd -m -u 1000 gamebot && chown -R gamebot:gamebot /app
USER gamebot

# Открываем порт (не обязательно для Telegram ботов, но для мониторинга)
EXPOSE 8080

# Команда по умолчанию
CMD ["python", "run.py"]