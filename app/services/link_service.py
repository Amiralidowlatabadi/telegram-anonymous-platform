import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import PersonalLink, ChannelLink, User
from app.database.repositories import LinkRepository
from app.core.security import generate_secure_token, sanitize_slug
from app.core.exceptions import SlugCollisionError, ValidationError

class LinkService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = LinkRepository(session)

    async def get_or_create_personal_link(self, user: User) -> PersonalLink:
        existing = await self.repo.get_user_active_personal_link(user.id)
        if existing and existing.is_active:
            return existing
        token = generate_secure_token(prefix="p_")
        return await self.repo.create_personal_link(user.id, token, is_custom=False)

    async def regenerate_personal_link(self, user: User) -> PersonalLink:
        existing = await self.repo.get_user_active_personal_link(user.id)
        if existing:
            existing.is_active = False
            from datetime import datetime, timezone
            existing.revoked_at = datetime.now(timezone.utc)
            await self.session.flush()
        token = generate_secure_token(prefix="p_")
        return await self.repo.create_personal_link(user.id, token, is_custom=False)

    async def set_custom_personal_slug(self, user: User, requested_slug: str) -> PersonalLink:
        slug = sanitize_slug(requested_slug)
        token = f"p_{slug}"
        existing_token = await self.repo.get_personal_link_by_token(token)
        if existing_token and existing_token.user_id != user.id:
            raise SlugCollisionError("این شناسه قبلاً توسط شخص دیگری انتخاب شده است.")
        existing = await self.repo.get_user_active_personal_link(user.id)
        if existing:
            existing.is_active = False
            await self.session.flush()
        return await self.repo.create_personal_link(user.id, token, is_custom=True)

    async def set_custom_channel_slug(self, channel_id: uuid.UUID, requested_slug: str) -> ChannelLink:
        slug = sanitize_slug(requested_slug)
        token = f"c_{slug}"
        existing = await self.repo.get_channel_link_by_token(token)
        if existing and existing.channel_id != channel_id:
            raise SlugCollisionError("این شناسه برای کانال دیگری ثبت شده است.")
        return await self.repo.create_channel_link(channel_id, token, is_custom=True)