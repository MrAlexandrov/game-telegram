# Makefile для телеграм-бота игр

.PHONY: help build run run-admin run-player test clean logs

# Переменные
IMAGE_NAME = game-telegram-bot
COMPOSE_FILE = docker-compose.yml

# Помощь
help:
	@echo "Доступные команды:"
	@echo "  build        - Собрать Docker образ"
	@echo "  run          - Запустить в полном режиме"
	@echo "  run-admin    - Запустить только админского бота"
	@echo "  run-player   - Запустить только игрового бота"
	@echo "  test         - Запустить оба бота для тестирования"
	@echo "  stop         - Остановить все контейнеры"
	@echo "  logs         - Показать логи"
	@echo "  logs-admin   - Показать логи админского бота"
	@echo "  logs-player  - Показать логи игрового бота"
	@echo "  clean        - Очистить контейнеры и образы"
	@echo "  setup        - Настроить конфигурацию"

# Сборка образа
build:
	docker build -t $(IMAGE_NAME) .

# Запуск в полном режиме
run:
	docker-compose --profile full up game-bot-full

# Запуск только админского бота
run-admin:
	docker-compose up game-bot-admin

# Запуск только игрового бота
run-player:
	docker-compose up game-bot-player

# Тестирование с двумя ботами
test:
	@echo "Запуск двух ботов для тестирования..."
	docker-compose up -d game-bot-admin game-bot-player
	@echo "Боты запущены. Используйте 'make logs' для просмотра логов"

# Остановка всех контейнеров
stop:
	docker-compose down

# Просмотр логов
logs:
	docker-compose logs -f

# Логи админского бота
logs-admin:
	docker-compose logs -f game-bot-admin

# Логи игрового бота
logs-player:
	docker-compose logs -f game-bot-player

# Очистка
clean:
	docker-compose down -v
	docker rmi $(IMAGE_NAME) 2>/dev/null || true
	docker system prune -f

# Настройка конфигурации
setup:
	@echo "Настройка конфигурации..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Создан .env файл"; fi
	@if [ ! -f .env.admin ]; then cp .env.admin.example .env.admin; echo "Создан .env.admin файл"; fi
	@if [ ! -f .env.player ]; then cp .env.player.example .env.player; echo "Создан .env.player файл"; fi
	@echo "Отредактируйте .env файлы и укажите токены ботов"

# Локальный запуск без Docker
run-local:
	python run.py

run-local-admin:
	python scripts/run_admin.py

run-local-player:
	python scripts/run_player.py

# Установка зависимостей
install:
	pip install -r requirements.txt

# Проверка статуса
status:
	docker-compose ps

# Перезапуск
restart:
	docker-compose restart

# Обновление (пересборка и перезапуск)
update: build restart

# Резервное копирование данных
backup:
	@echo "Создание резервной копии..."
	mkdir -p backup
	docker run --rm -v game-telegram_admin_logs:/data -v $(PWD)/backup:/backup alpine tar czf /backup/admin_logs_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .
	docker run --rm -v game-telegram_player_logs:/data -v $(PWD)/backup:/backup alpine tar czf /backup/player_logs_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .
	@echo "Резервная копия создана в папке backup/"
