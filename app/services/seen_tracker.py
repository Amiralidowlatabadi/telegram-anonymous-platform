import uuid
from typing import Optional
import redis.asyncio as redis
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import SeenEvent, ChannelMessage, Channel, User
from app.database.repositories import UserRepository

class SeenTrackerService:
    def __init__(self, session: AsyncSession, redis_client: redis.Redis):
        self.session = session
        self.redis = redis_client
        self.user_repo = UserRepository(session)

    async def register_seen_event(self, channel_tg_id: int, message_tg_id: int, viewer_tg_id: int) -> tuple[bool, int, Optional[User]]:
        """Idempotently records a seen event and returns (is_new, total_seen_count, author_user)."""
        viewer = await self.user_repo.get_or_create(viewer_tg_id)
        
        stmt = (
            select(ChannelMessage)
            .join(Channel, ChannelMessage.channel_id == Channel.id)
            .where(
                and_(
                    Channel.telegram_channel_id == channel_tg_id,
                    ChannelMessage.telegram_message_id == message_tg_id
                )
            )
        )
        res = await self.session.execute(stmt)
        ch_msg = res.scalar_one_or_none()
        if not ch_msg:
            return False, 0, None

        seen_stmt = select(SeenEvent).where(
            and_(
                SeenEvent.channel_message_id == ch_msg.id,
                SeenEvent.viewer_id == viewer.id
            )
        )
        seen_res = await self.session.execute(seen_stmt)
        if seen_res.scalar_one_or_none():
            count_stmt = select(func.count(SeenEvent.id)).where(SeenEvent.channel_message_id == ch_msg.id)
            total_count = (await self.session.execute(count_stmt)).scalar() or 0
            return False, total_count, None

        event = SeenEvent(channel_message_id=ch_msg.id, viewer_id=viewer.id)
        self.session.add(event)
        await self.session.flush()

        count_stmt = select(func.count(SeenEvent.id)).where(SeenEvent.channel_message_id == ch_msg.id)
        total_count = (await self.session.execute(count_stmt)).scalar() or 1
        
        author = await self.user_repo.get_by_id(ch_msg.author_id)
        return True, total_count, author