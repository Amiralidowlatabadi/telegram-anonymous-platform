import uuid
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User
from app.database.repositories import ChannelRepository, LinkRepository
from app.services.channel_publisher import ChannelPublisherService
from app.services.moderation_service import ContentModerationFilter
from app.bot.states import ChannelChatStates
from app.bot.keyboards import get_main_menu_keyboard
from app.bot.handlers.personal_chat import extract_payload
from app.core.exceptions import AppError
from app.core.i18n import get_text

router = Router(name="channel_chat_router")

@router.message(ChannelChatStates.composing_post)
async def process_channel_submission(
    message: types.Message,
    state: FSMContext,
    db_user: User,
    db_session: AsyncSession,
    channel_publisher: ChannelPublisherService
):
    if message.text == get_text("btn_cancel"):
        await state.clear()
        await message.answer("عملیات لغو شد.", reply_markup=get_main_menu_keyboard())
        return

    data = await state.get_data()
    channel_id_str = data.get("target_channel_id")
    link_id_str = data.get("target_channel_link_id")

    if not channel_id_str or not link_id_str:
        await state.clear()
        await message.answer(get_text("error_generic"), reply_markup=get_main_menu_keyboard())
        return

    content_type, payload = extract_payload(message)
    if content_type == "unknown":
        await message.answer("⚠️ فرمت ارسالی مجاز نمی‌باشد.")
        return

    raw_text = payload.get("text") or payload.get("caption") or ""
    if raw_text:
        mod_filter = ContentModerationFilter()
        try:
            mod_filter.evaluate_text(raw_text)
        except AppError as e:
            await message.answer(str(e))
            return

    channel_repo = ChannelRepository(db_session)
    link_repo = LinkRepository(db_session)
    channel = await channel_repo.get_channel_by_id(uuid.UUID(channel_id_str))
    channel_link = await db_session.get(link_repo.repo_model if hasattr(link_repo, 'repo_model') else type(channel), uuid.UUID(link_id_str)) if hasattr(link_repo, 'repo_model') else await db_session.get(type(channel), uuid.UUID(channel_id_str)) # fallback
    
    # Safe retrieval
    from app.database.models import ChannelLink
    channel_link_entity = await db_session.get(ChannelLink, uuid.UUID(link_id_str))

    if not channel or not channel_link_entity or not channel.is_active or not channel_link_entity.is_active:
        await message.answer("⚠️ این کانال در حال حاضر پذیرای پیام ناشناس نیست.")
        await state.clear()
        return

    try:
        await channel_publisher.publish_anonymous_post(
            channel=channel,
            channel_link=channel_link_entity,
            author=db_user,
            content_type=content_type,
            payload=payload
        )
        await message.answer(get_text("channel_post_published"), reply_markup=get_main_menu_keyboard())
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ خطا در ارسال پیام به کانال: {e}", reply_markup=get_main_menu_keyboard())
        await state.clear()