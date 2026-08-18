import uuid
from typing import Optional, List
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import (
    User, PersonalLink, Channel, ChannelAdmin, ChannelLink,
    Conversation, ConversationMessage, ChannelMessage, SeenEvent,
    UserBlock, Report
)

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, telegram_id: int) -> User:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id)
            self.session.add(user)
            await self.session.flush()
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def update_nickname(self, user_id: uuid.UUID, nickname: Optional[str]) -> None:
        stmt = update(User).where(User.id == user_id).values(nickname=nickname)
        await self.session.execute(stmt)

class LinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_personal_link_by_token(self, token: str) -> Optional[PersonalLink]:
        stmt = select(PersonalLink).where(PersonalLink.token == token)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_active_personal_link(self, user_id: uuid.UUID) -> Optional[PersonalLink]:
        stmt = select(PersonalLink).where(
            and_(PersonalLink.user_id == user_id, PersonalLink.revoked_at.is_(None))
        ).order_by(PersonalLink.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_personal_link(self, user_id: uuid.UUID, token: str, is_custom: bool = False) -> PersonalLink:
        link = PersonalLink(user_id=user_id, token=token, is_custom_slug=is_custom, is_active=True)
        self.session.add(link)
        await self.session.flush()
        return link

    async def get_channel_link_by_token(self, token: str) -> Optional[ChannelLink]:
        stmt = select(ChannelLink).where(ChannelLink.token == token)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_channel_link(self, channel_id: uuid.UUID, token: str, is_custom: bool = False) -> ChannelLink:
        link = ChannelLink(channel_id=channel_id, token=token, is_custom_slug=is_custom, is_active=True)
        self.session.add(link)
        await self.session.flush()
        return link

class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_conversation(self, owner_id: uuid.UUID, sender_id: uuid.UUID, link_id: Optional[uuid.UUID] = None) -> Conversation:
        stmt = select(Conversation).where(
            and_(Conversation.owner_id == owner_id, Conversation.sender_id == sender_id)
        )
        res = await self.session.execute(stmt)
        conv = res.scalar_one_or_none()
        if not conv:
            conv = Conversation(owner_id=owner_id, sender_id=sender_id, personal_link_id=link_id, status="ACTIVE")
            self.session.add(conv)
            await self.session.flush()
        elif conv.status in ("CLOSED_BY_OWNER", "CLOSED_BY_SENDER"):
            conv.status = "ACTIVE"
            await self.session.flush()
        return conv

    async def get_by_id(self, conv_id: uuid.UUID) -> Optional[Conversation]:
        return await self.session.get(Conversation, conv_id)

    async def get_user_conversations(self, owner_id: uuid.UUID) -> List[Conversation]:
        stmt = select(Conversation).where(Conversation.owner_id == owner_id).order_by(Conversation.updated_at.desc())
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        sender_user_id: uuid.UUID,
        recipient_user_id: uuid.UUID,
        content_type: str,
        content_payload: dict,
        owner_telegram_message_id: Optional[int] = None,
        sender_telegram_message_id: Optional[int] = None,
    ) -> ConversationMessage:
        msg = ConversationMessage(
            conversation_id=conversation_id,
            sender_user_id=sender_user_id,
            recipient_user_id=recipient_user_id,
            content_type=content_type,
            content_payload=content_payload,
            owner_telegram_message_id=owner_telegram_message_id,
            sender_telegram_message_id=sender_telegram_message_id,
        )
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def get_message_by_owner_msg_id(self, owner_telegram_msg_id: int) -> Optional[ConversationMessage]:
        stmt = select(ConversationMessage).where(ConversationMessage.owner_telegram_message_id == owner_telegram_msg_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_message_by_id(self, message_id: uuid.UUID) -> Optional[ConversationMessage]:
        return await self.session.get(ConversationMessage, message_id)

class BlockRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_blocked(self, blocker_id: uuid.UUID, blocked_id: uuid.UUID) -> bool:
        stmt = select(UserBlock).where(
            and_(UserBlock.blocker_id == blocker_id, UserBlock.blocked_id == blocked_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def block_user(self, blocker_id: uuid.UUID, blocked_id: uuid.UUID, conv_id: Optional[uuid.UUID] = None) -> UserBlock:
        block = UserBlock(blocker_id=blocker_id, blocked_id=blocked_id, conversation_id=conv_id)
        self.session.add(block)
        await self.session.flush()
        return block

    async def unblock_user(self, blocker_id: uuid.UUID, blocked_id: uuid.UUID) -> None:
        stmt = select(UserBlock).where(
            and_(UserBlock.blocker_id == blocker_id, UserBlock.blocked_id == blocked_id)
        )
        res = await self.session.execute(stmt)
        block = res.scalar_one_or_none()
        if block:
            await self.session.delete(block)

class ChannelRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_channel_by_tg_id(self, channel_tg_id: int) -> Optional[Channel]:
        stmt = select(Channel).where(Channel.telegram_channel_id == channel_tg_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_channel_by_id(self, channel_id: uuid.UUID) -> Optional[Channel]:
        return await self.session.get(Channel, channel_id)

    async def register_channel(self, channel_tg_id: int, title: str, username: Optional[str], owner: User) -> Channel:
        channel = Channel(telegram_channel_id=channel_tg_id, title=title, username=username, is_active=True)
        self.session.add(channel)
        await self.session.flush()
        admin = ChannelAdmin(channel_id=channel.id, user_id=owner.id, role="owner")
        self.session.add(admin)
        await self.session.flush()
        return channel

    async def add_channel_message(self, channel_id: uuid.UUID, author_id: uuid.UUID, message_id: int) -> ChannelMessage:
        msg = ChannelMessage(channel_id=channel_id, author_id=author_id, telegram_message_id=message_id)
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def get_channel_message(self, channel_id: uuid.UUID, message_id: int) -> Optional[ChannelMessage]:
        stmt = select(ChannelMessage).where(
            and_(ChannelMessage.channel_id == channel_id, ChannelMessage.telegram_message_id == message_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

class ReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_report(self, reporter_id: uuid.UUID, conv_id: uuid.UUID, reason: str, msg_id: Optional[uuid.UUID] = None) -> Report:
        report = Report(reporter_id=reporter_id, conversation_id=conv_id, message_id=msg_id, reason=reason, status="PENDING")
        self.session.add(report)
        await self.session.flush()
        return report

    async def get_pending_reports(self) -> List[Report]:
        stmt = select(Report).where(Report.status == "PENDING").order_by(Report.created_at.asc())
        res = await self.session.execute(stmt)
        return list(res.scalars().all())