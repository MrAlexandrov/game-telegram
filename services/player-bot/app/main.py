"""
Player Bot Service - Main Application
Telegram bot for game players
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import structlog

from .config import settings
from .handlers import player_handlers, game_handlers, question_handlers
from .services.api_client import APIClient
from .middlewares import ErrorHandlerMiddleware, LoggingMiddleware

logger = structlog.get_logger()


async def create_bot() -> Bot:
    """Create and configure bot instance"""
    bot = Bot(token=settings.BOT_TOKEN)
    return bot


async def create_dispatcher() -> Dispatcher:
    """Create and configure dispatcher"""
    # Use Redis for FSM storage
    storage = RedisStorage.from_url(settings.REDIS_URL)
    dp = Dispatcher(storage=storage)
    
    # Setup middlewares
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())
    
    # Include routers
    dp.include_router(player_handlers.router)
    dp.include_router(game_handlers.router)
    dp.include_router(question_handlers.router)
    
    return dp


async def on_startup(bot: Bot) -> None:
    """Bot startup handler"""
    logger.info("Player Bot starting up")
    
    # Set webhook if configured
    if settings.WEBHOOK_URL:
        await bot.set_webhook(
            url=f"{settings.WEBHOOK_URL}/webhook",
            secret_token=settings.WEBHOOK_SECRET
        )
        logger.info(f"Webhook set to {settings.WEBHOOK_URL}/webhook")
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook disabled, using polling")


async def on_shutdown(bot: Bot) -> None:
    """Bot shutdown handler"""
    logger.info("Player Bot shutting down")
    await bot.session.close()


async def main():
    """Main application entry point"""
    # Configure logging
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
    
    # Create bot and dispatcher
    bot = await create_bot()
    dp = await create_dispatcher()
    
    # Register startup and shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Initialize API client
    api_client = APIClient(
        user_manager_url=settings.USER_MANAGER_URL,
        game_engine_url=settings.GAME_ENGINE_URL,
        session_manager_url=settings.SESSION_MANAGER_URL
    )
    
    # Store API client in bot data for access in handlers
    dp["api_client"] = api_client
    
    if settings.WEBHOOK_URL:
        # Run with webhook
        app = web.Application()
        
        # Health check endpoint
        async def health_check(request):
            return web.json_response({"status": "healthy"})
        
        app.router.add_get("/health", health_check)
        
        # Setup webhook handler
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=settings.WEBHOOK_SECRET
        )
        webhook_requests_handler.register(app, path="/webhook")
        setup_application(app, dp, bot=bot)
        
        # Start web server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=settings.API_HOST, port=settings.API_PORT)
        await site.start()
        
        logger.info(f"Player Bot webhook server started on {settings.API_HOST}:{settings.API_PORT}")
        
        # Keep running
        try:
            await asyncio.Future()  # Run forever
        finally:
            await runner.cleanup()
    else:
        # Run with polling
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())