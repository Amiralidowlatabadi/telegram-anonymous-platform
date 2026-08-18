from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User
from app.database.repositories import LinkRepository
from app.bot.keyboards import get_main_menu_keyboard, get_cancel_keyboard
from app.bot.states import PersonalChatStates, ChannelChatStates
from app.core.i18n import get_text

router = Router(name="start_router")

@router.message(CommandStart())
async def handle_start(
    message: types.Message,
    command: CommandObject,
    db_user: User,
    db_session: AsyncSession,
    state: FSMContext
):
    args = command.args
    if not args:
        await state.clear()
        await message.answer(get_text("welcome"), reply_markup=get_main_menu_keyboard())
        return

    link_repo = LinkRepository(db_session)
    
    # 1. Check Personal Link Prefix
    if args.startswith("p_"):
        token = args
        personal_link = await link_repo.get_personal_link_by_token(token)
        if not personal_link or not personal_link.is_active:
            await message.answer(get_text("error_invalid_link"))
            return
        if personal_link.user_id == db_user.id:
            await message.answer("⚠️ شما نمی‌توانید برای لینک شخصی خودتان پیام ناشناس ارسال کنید!")
            return

        await state.set_state(PersonalChatStates.composing_message)
        await state.update_data(target_personal_link_id=str(personal_link.id), target_owner_user_id=str(personal_link.user_id))
        await message.answer(
            "✍️ **در حال نوشتن پیام ناشناس...**\nهر متنی، صدایی یا تصویری ارسال کنید، مستقیماً و به صورت کاملاً ناشناس برای مخاطب ارسال خواهد شد.",
            reply_markup=get_cancel_keyboard()
        )
        return

    # 2. Check Channel Link Prefix
    if args.startswith("c_"):
        token = args
        channel_link = await link_repo.get_channel_link_by_token(token)
        if not channel_link or not channel_link.is_active:
            await message.answer(get_text("error_invalid_link"))
            return

        await state.set_state(ChannelChatStates.composing_post)
        await state.update_data(target_channel_link_id=str(channel_link.id), target_channel_id=str(channel_link.channel_id))
        await message.answer(
            "📢 **ارسال ناشناس به کانال**\nپیام ارسالی شما پس از تأیید فیلترها مستقیماً و با نام مستعار شما در کانال منتشر خواهد شد.",
            reply_markup=get_cancel_keyboard()
        )
        return

    await message.answer(get_text("error_invalid_link"))