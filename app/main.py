import asyncio
import logging
import structlog
import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import ErrorEvent

from app.config import get_settings
from app.database.session import AsyncSessionLocal
from app.services.rate_limiter import RedisRateLimiter
from app.services.message_router import MessageRouter
from app.services.channel_publisher import ChannelPublisherService
from app.services.seen_tracker import SeenTrackerService

from app.bot.middlewares.db_middleware import DbSessionMiddleware
from app.bot.middlewares.ban_middleware import BanCheckMiddleware
from app.bot.middlewares.rate_limit_middleware import RateLimitMiddleware

from app.bot.handlers import start, personal_chat, channel_chat, inbox, settings as settings_handler, moderation, admin

logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

async def main() -> None:
    config = get_settings()
    
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    
    redis_client = redis.from_url(config.redis_url)
    storage = RedisStorage(redis=redis_client)
    dp = Dispatcher(storage=storage)

    # Error Logger Handler
    @dp.error()
    async def global_error_handler(event: ErrorEvent):
        logging.exception(f"Unhandled exception on update: {event.exception}", exc_info=event.exception)

    # Core singletons
    rate_limiter = RedisRateLimiter(redis_client)

    # Register Middlewares
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.message.middleware(BanCheckMiddleware())
    dp.callback_query.middleware(BanCheckMiddleware())
    dp.message.middleware(RateLimitMiddleware(rate_limiter, limit_per_minute=config.default_rate_limit_per_minute))
    dp.callback_query.middleware(RateLimitMiddleware(rate_limiter, limit_per_minute=config.default_rate_limit_per_minute))

    # Helper injectors for handlers
    async def dependency_injection_middleware(handler, event, data):
        session_db = data["db_session"]
        data["redis_client"] = redis_client
        data["message_router"] = MessageRouter(session_db, redis_client, bot)
        data["channel_publisher"] = ChannelPublisherService(session_db, bot)
        data["seen_tracker"] = SeenTrackerService(session_db, redis_client)
        return await handler(event, data)

    dp.update.middleware(dependency_injection_middleware)

    # Register Handlers
    dp.include_router(start.router)
    dp.include_router(inbox.router)
    dp.include_router(personal_chat.router)
    dp.include_router(channel_chat.router)
    dp.include_router(settings_handler.router)
    dp.include_router(moderation.router)
    dp.include_router(admin.router)

    logger.info("Bot is starting polling...", bot_username=config.bot_username)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(main())