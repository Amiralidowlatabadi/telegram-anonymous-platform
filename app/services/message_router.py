import uuid
from typing import Optional, Any
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import User, ConversationMessage
from app.database.repositories import ConversationRepository, UserRepository
from app.core.exceptions import ReplyTargetExpiredError, EntityNotFoundError

class MessageRouter:
    REPLY_KEY_PREFIX = "reply_target:"

    def __init__(self, session: AsyncSession, redis_client: redis.Redis, bot: Bot):
        self.session = session
        self.redis = redis_client
        self.bot = bot
        self.conv_repo = ConversationRepository(session)
        self.user_repo = UserRepository(session)

    async def set_active_reply_target(self, owner_tg_id: int, message_db_id: uuid.UUID, ttl_seconds: int = 3600) -> None:
        key = f"{self.REPLY_KEY_PREFIX}{owner_tg_id}"
        await self.redis.set(key, str(message_db_id), ex=ttl_seconds)

    async def get_active_reply_target(self, owner_tg_id: int) -> Optional[uuid.UUID]:
        key = f"{self.REPLY_KEY_PREFIX}{owner_tg_id}"
        val = await self.redis.get(key)
        if val:
            return uuid.UUID(val.decode("utf-8") if isinstance(val, bytes) else val)
        return None

    async def clear_active_reply_target(self, owner_tg_id: int) -> None:
        key = f"{self.REPLY_KEY_PREFIX}{owner_tg_id}"
        await self.redis.delete(key)

    async def dispatch_anonymous_to_owner(
        self,
        conversation_id: uuid.UUID,
        sender: User,
        owner: User,
        content_type: str,
        payload: dict[str, Any],
    ) -> ConversationMessage:
        """Sends synthetic reconstructed payload to owner without sender attribution."""
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="↩️ پاسخ به این پیام", callback_data=f"reply_msg:{conversation_id}")],
                [
                    InlineKeyboardButton(text="🚫 مسدود کردن", callback_data=f"block_conv:{conversation_id}"),
                    InlineKeyboardButton(text="🚨 گزارش", callback_data=f"report_conv:{conversation_id}"),
                ]
            ]
        )
        
        sent_msg_id = await self._send_reconstructed_message(
            chat_id=owner.telegram_id,
            content_type=content_type,
            payload=payload,
            reply_markup=kb
        )

        return await self.conv_repo.add_message(
            conversation_id=conversation_id,
            sender_user_id=sender.id,
            recipient_user_id=owner.id,
            content_type=content_type,
            content_payload=payload,
            owner_telegram_message_id=sent_msg_id
        )

    async def dispatch_owner_reply(
        self,
        owner: User,
        content_type: str,
        payload: dict[str, Any],
    ) -> ConversationMessage:
        """Dispatches an owner's reply strictly to the conversation locked in the active reply target."""
        target_msg_id = await self.get_active_reply_target(owner.telegram_id)
        if not target_msg_id:
            raise ReplyTargetExpiredError("هیچ پیام فعالی برای پاسخ انتخاب نشده است. لطفاً روی دکمه پاسخ در پیام مورد نظر کلیک کنید.")

        target_msg = await self.conv_repo.get_message_by_id(target_msg_id)
        if not target_msg:
            raise EntityNotFoundError("پیام مورد نظر جهت پاسخ در سیستم یافت نشد.")

        conv = await self.conv_repo.get_by_id(target_msg.conversation_id)
        if not conv or conv.owner_id != owner.id:
            raise EntityNotFoundError("عدم تطابق گفتگو.")

        recipient = await self.user_repo.get_by_id(conv.sender_id)
        if not recipient:
            raise EntityNotFoundError("گیرنده یافت نشد.")

        sent_msg_id = await self._send_reconstructed_message(
            chat_id=recipient.telegram_id,
            content_type=content_type,
            payload=payload,
            header_text="📬 **پاسخ جدید از طرف مخاطب:**\n\n"
        )

        return await self.conv_repo.add_message(
            conversation_id=conv.id,
            sender_user_id=owner.id,
            recipient_user_id=recipient.id,
            content_type=content_type,
            content_payload=payload,
            sender_telegram_message_id=sent_msg_id
        )

    async def _send_reconstructed_message(
        self,
        chat_id: int,
        content_type: str,
        payload: dict[str, Any],
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        header_text: str = ""
    ) -> int:
        caption = f"{header_text}{payload.get('caption', '')}".strip()
        text = f"{header_text}{payload.get('text', '')}".strip()

        if content_type == "text":
            msg = await self.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
        elif content_type == "photo":
            msg = await self.bot.send_photo(chat_id=chat_id, photo=payload["file_id"], caption=caption, reply_markup=reply_markup)
        elif content_type == "video":
            msg = await self.bot.send_video(chat_id=chat_id, video=payload["file_id"], caption=caption, reply_markup=reply_markup)
        elif content_type == "voice":
            msg = await self.bot.send_voice(chat_id=chat_id, voice=payload["file_id"], caption=caption, reply_markup=reply_markup)
        elif content_type == "video_note":
            msg = await self.bot.send_video_note(chat_id=chat_id, video_note=payload["file_id"], reply_markup=reply_markup)
        elif content_type == "document":
            msg = await self.bot.send_document(chat_id=chat_id, document=payload["file_id"], caption=caption, reply_markup=reply_markup)
        elif content_type == "audio":
            msg = await self.bot.send_audio(chat_id=chat_id, audio=payload["file_id"], caption=caption, reply_markup=reply_markup)
        elif content_type == "sticker":
            msg = await self.bot.send_sticker(chat_id=chat_id, sticker=payload["file_id"], reply_markup=reply_markup)
        else:
            msg = await self.bot.send_message(chat_id=chat_id, text=text or "[محتوای چندرسانه‌ای]", reply_markup=reply_markup)

        return msg.message_id