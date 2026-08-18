import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Conversation, ConversationMessage, User
from app.database.repositories import ConversationRepository, BlockRepository
from app.core.exceptions import UserBlockedError, EntityNotFoundError

class ConversationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conv_repo = ConversationRepository(session)
        self.block_repo = BlockRepository(session)

    async def initiate_or_resume(self, owner: User, sender: User, link_id: Optional[uuid.UUID] = None) -> Conversation:
        if await self.block_repo.is_blocked(owner.id, sender.id):
            raise UserBlockedError("شما توسط این کاربر مسدود شده‌اید.")
        return await self.conv_repo.get_or_create_conversation(owner.id, sender.id, link_id)

    async def get_conversation_by_id(self, conv_id: uuid.UUID) -> Conversation:
        conv = await self.conv_repo.get_by_id(conv_id)
        if not conv:
            raise EntityNotFoundError("گفتگوی مورد نظر یافت نشد.")
        return conv

    async def close_conversation(self, conv_id: uuid.UUID, closed_by_owner: bool) -> None:
        conv = await self.get_conversation_by_id(conv_id)
        conv.status = "CLOSED_BY_OWNER" if closed_by_owner else "CLOSED_BY_SENDER"
        await self.session.flush()

    async def block_conversation_participant(self, owner: User, conv_id: uuid.UUID) -> None:
        conv = await self.get_conversation_by_id(conv_id)
        if conv.owner_id != owner.id:
            raise EntityNotFoundError("دسترسی غیرمجاز به گفتگو.")
        conv.status = "BLOCKED"
        await self.block_repo.block_user(owner.id, conv.sender_id, conv.id)
        await self.session.flush()