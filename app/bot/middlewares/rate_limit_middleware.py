from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from app.services.rate_limiter import RedisRateLimiter
from app.core.exceptions import RateLimitExceededError
from app.core.i18n import get_text

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, rate_limiter: RedisRateLimiter, limit_per_minute: int = 20):
        self.rate_limiter = rate_limiter
        self.limit = limit_per_minute

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_tg = getattr(event, "from_user", None)
        if user_tg:
            try:
                await self.rate_limiter.check_rate_limit(f"user:{user_tg.id}", limit=self.limit, window_seconds=60)
            except RateLimitExceededError:
                if isinstance(event, Message):
                    await event.answer(get_text("error_rate_limited"))
                elif isinstance(event, CallbackQuery):
                    await event.answer(get_text("error_rate_limited"), show_alert=True)
                return None
        return await handler(event, data)