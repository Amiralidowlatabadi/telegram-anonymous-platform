from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from app.database.session import AsyncSessionLocal
from app.database.repositories import UserRepository

class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with AsyncSessionLocal() as session:
            data["db_session"] = session
            
            user_tg = None
            if isinstance(event, Update):
                if event.message:
                    user_tg = event.message.from_user
                elif event.callback_query:
                    user_tg = event.callback_query.from_user
                elif event.inline_query:
                    user_tg = event.inline_query.from_user
            else:
                user_tg = getattr(event, "from_user", None)

            if user_tg:
                user_repo = UserRepository(session)
                db_user = await user_repo.get_or_create(user_tg.id)
                data["db_user"] = db_user

            try:
                res = await handler(event, data)
                await session.commit()
                return res
            except Exception:
                await session.rollback()
                raise