"""
Главный файл приложения - точка входа
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime

from src.settings import settings, ensure_directories
from src.core.bot import BotManager


def setup_logging():
    """Настройка системы логирования"""
    # Создаем директорию для логов
    import os
    log_dir = os.path.dirname(settings.log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Настройка форматирования
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настройка обработчиков
    handlers = []
    
    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # Файловый обработчик
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Настройка корневого логгера
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        handlers=handlers,
        force=True
    )
    
    # Настройка логгеров библиотек
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.INFO)


async def main():
    """Главная функция приложения"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 Запуск телеграм-бота для игр")
        logger.info(f"Версия Python: {sys.version}")
        logger.info(f"Окружение: {settings.environment}")
        
        # Создаем необходимые директории
        ensure_directories()
        logger.info("📁 Директории созданы")
        
        # Создаем и инициализируем менеджер ботов
        bot_manager = BotManager()
        await bot_manager.initialize()
        logger.info("🤖 Боты инициализированы")
        
        # Настройка обработки сигналов для graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Получен сигнал {signum}, завершение работы...")
            asyncio.create_task(shutdown(bot_manager))
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Запускаем ботов
        await bot_manager.start()
        logger.info("✅ Боты запущены и готовы к работе")
        
        # Выводим информацию о конфигурации
        logger.info(f"👑 Администратор: {settings.root_id}")
        logger.info(f"📊 Максимум игроков в сессии: {settings.max_players_per_session}")
        logger.info(f"⏱️ Таймаут сессии: {settings.session_timeout_minutes} минут")
        logger.info(f"🔢 Длина кода сессии: {settings.session_code_length}")
        
        # Основной цикл приложения
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания")
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


async def shutdown(bot_manager: BotManager):
    """Graceful shutdown приложения"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🛑 Начало процедуры завершения...")
        
        # Останавливаем ботов
        await bot_manager.stop()
        logger.info("🤖 Боты остановлены")
        
        # Останавливаем фоновые задачи
        from src.sessions.manager import session_manager
        await session_manager.stop_cleanup_task()
        logger.info("🧹 Фоновые задачи остановлены")
        
        # Сохраняем данные
        logger.info("💾 Сохранение данных...")
        
        logger.info("✅ Приложение успешно завершено")
        
    except Exception as e:
        logger.error(f"Ошибка при завершении: {e}", exc_info=True)
    
    finally:
        # Принудительное завершение
        sys.exit(0)


def run():
    """Функция запуска приложения"""
    # Настройка логирования
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("🎮 ТЕЛЕГРАМ-БОТ ДЛЯ ИГР")
    logger.info(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    try:
        # Проверяем настройки
        if not settings.admin_bot_token:
            logger.error("❌ Не указан токен админского бота (ADMIN_BOT_TOKEN)")
            sys.exit(1)
        
        if not settings.player_bot_token:
            logger.error("❌ Не указан токен игрового бота (PLAYER_BOT_TOKEN)")
            sys.exit(1)
        
        if not settings.root_id:
            logger.error("❌ Не указан ID администратора (ROOT_ID)")
            sys.exit(1)
        
        # Запускаем приложение
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("👋 Приложение завершено пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка при запуске: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run()