# main.py
"""
Основной файл приложения.
База данных инициализируется до запуска бота, затем в bot_data сохраняется SQLAlchemy-сессия.
При вызове команды /start происходит разделение логики: если пользователь администратор,
вызывается admin_start() из модуля admin_flow.py, иначе – gamer_start() из модуля gamer_flow.py.
"""

import logging
from telegram import (
    Update
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from logger import get_logger
from settings import BOT_TOKEN, ADMIN_IDS
from admin_flow import admin_flow
from gamer_flow import gamer_flow

logger = get_logger(__name__)

async def routing_start_command(update: Update, context):
    """
    Обрабатывает команду /start.
    Если пользователь администратор – вызывается admin_start() из модуля admin_flow.py,
    иначе – gamer_start() из модуля gamer_flow.py.
    """
    user_id = update.effective_user.id
    logger.debug(f"user_id = {user_id}")
    logger.debug(f"ADMIN_IDS = {ADMIN_IDS}")
    if user_id in ADMIN_IDS:
        await admin_flow.start(update, context)
    else:
        await gamer_flow.start(update, context)


async def routing_message_handler(update: Update, context):
    """Маршрутизатор для текстовых сообщений.
    Направляет сообщение в админский или геймерский обработчик в зависимости от Telegram ID.
    """
    user_id = update.effective_user.id
    logger.debug(f"user_id = {user_id}")
    logger.debug(f"ADMIN_IDS = {ADMIN_IDS}")
    if user_id in ADMIN_IDS:
        await admin_flow.handle_text(update, context)
    else:
        await gamer_flow.handle_text(update, context)


async def routing_photo_handler(update: Update, context):
    """Маршрутизатор для картинок.
    Направляет сообщение в админский или геймерский обработчик в зависимости от Telegram ID.
    """
    user_id = update.effective_user.id
    logger.debug(f"user_id = {user_id}")
    logger.debug(f"ADMIN_IDS = {ADMIN_IDS}")
    if user_id in ADMIN_IDS:
        await admin_flow.handle_photo(update, context)
    # else:
    #     await gamer_flow.handle_photo(update, context)

async def routing_callback_handler(update: Update, context):
    """Маршрутизатор для inline-обработчиков (callback_query).
    Вызывает соответствующий обработчик в зависимости от типа пользователя.
    """
    user_id = update.effective_user.id
    logger.debug(f"user_id = {user_id}")
    logger.debug(f"ADMIN_IDS = {ADMIN_IDS}")
    if update.callback_query.data.startswith("admin"):
        await admin_flow.handle_callback(update, context)
    else:
        await gamer_flow.handle_callback(update, context)
    # if user_id in ADMIN_IDS:
    #     await admin_flow.handle_callback(update, context)
    # else:
    #     await gamer_flow.handle_callback(update, context)

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", routing_start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, routing_message_handler))  # Для игроков
    application.add_handler(CallbackQueryHandler(routing_callback_handler))  # Можно заменить на нужный обработчик
    application.add_handler(MessageHandler(filters.PHOTO, routing_photo_handler))  # Можно заменить на нужный обработчик

    logger.info("Bot started successfully!")
    application.run_polling()

if __name__ == "__main__":
    main()
