from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import User, Channel, ChannelLink
from app.database.repositories import ChannelRepository
from app.services.template_engine import TemplateEngine

class ChannelPublisherService:
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.channel_repo = ChannelRepository(session)

    async def publish_anonymous_post(
        self,
        channel: Channel,
        channel_link: ChannelLink,
        author: User,
        content_type: str,
        payload: dict[str, Any]
    ) -> int:
        raw_text = payload.get("text") or payload.get("caption") or ""
        formatted_text = TemplateEngine.render(
            template_str=channel_link.template,
            message=raw_text,
            nickname=author.nickname
        )

        reply_markup = None
        if channel_link.show_seen_button:
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="👁 پیام را دیدم", callback_data=f"seen_post:{channel.telegram_channel_id}")]
                ]
            )

        if content_type == "text":
            msg = await self.bot.send_message(
                chat_id=channel.telegram_channel_id,
                text=formatted_text,
                reply_markup=reply_markup
            )
        elif content_type == "photo":
            msg = await self.bot.send_photo(
                chat_id=channel.telegram_channel_id,
                photo=payload["file_id"],
                caption=formatted_text,
                reply_markup=reply_markup
            )
        elif content_type == "video":
            msg = await self.bot.send_video(
                chat_id=channel.telegram_channel_id,
                video=payload["file_id"],
                caption=formatted_text,
                reply_markup=reply_markup
            )
        elif content_type == "document":
            msg = await self.bot.send_document(
                chat_id=channel.telegram_channel_id,
                document=payload["file_id"],
                caption=formatted_text,
                reply_markup=reply_markup
            )
        elif content_type == "voice":
            msg = await self.bot.send_voice(
                chat_id=channel.telegram_channel_id,
                voice=payload["file_id"],
                caption=formatted_text,
                reply_markup=reply_markup
            )
        else:
            msg = await self.bot.send_message(
                chat_id=channel.telegram_channel_id,
                text=formatted_text,
                reply_markup=reply_markup
            )

        await self.channel_repo.add_channel_message(
            channel_id=channel.id,
            author_id=author.id,
            message_id=msg.message_id
        )
        return msg.message_id