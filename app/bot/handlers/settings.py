from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.database.models import User
from app.services.link_service import LinkService
from app.bot.keyboards import get_link_management_keyboard, get_cancel_keyboard, get_main_menu_keyboard
from app.bot.states import CustomSlugStates, NicknameStates
from app.core.security import sanitize_nickname
from app.core.i18n import get_text
from app.core.exceptions import AppError

router = Router(name="settings_router")
settings = get_settings()

@router.message(F.text == get_text("btn_personal_link"))
async def view_personal_link(message: types.Message, db_user: User, db_session: AsyncSession):
    link_service = LinkService(db_session)
    link = await link_service.get_or_create_personal_link(db_user)
    public_url = f"https://t.me/{settings.bot_username}?start={link.token}"
    status_text = get_text("link_active") if link.is_active else get_text("link_inactive")
    
    await message.answer(
        get_text("personal_link_info", link=public_url, status=status_text),
        reply_markup=get_link_management_keyboard(link.is_active)
    )

@router.callback_query(F.data == "toggle_link_status")
async def toggle_link(call: types.CallbackQuery, db_user: User, db_session: AsyncSession):
    link_service = LinkService(db_session)
    link = await link_service.get_or_create_personal_link(db_user)
    link.is_active = not link.is_active
    await db_session.flush()
    await call.message.edit_reply_markup(reply_markup=get_link_management_keyboard(link.is_active))
    await call.answer("وضعیت لینک به‌روزرسانی شد.")

@router.callback_query(F.data == "regen_link")
async def regenerate_link(call: types.CallbackQuery, db_user: User, db_session: AsyncSession):
    link_service = LinkService(db_session)
    new_link = await link_service.regenerate_personal_link(db_user)
    public_url = f"https://t.me/{settings.bot_username}?start={new_link.token}"
    await call.message.edit_text(
        get_text("personal_link_info", link=public_url, status=get_text("link_active")),
        reply_markup=get_link_management_keyboard(new_link.is_active)
    )
    await call.answer("لینک جدید تولید شد.")

@router.callback_query(F.data == "set_custom_slug")
async def prompt_custom_slug(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(CustomSlugStates.waiting_for_personal_slug)
    await call.message.answer(
        "✏️ لطفاً شناسه (Slug) دلخواه خود را ارسال کنید (۳ تا ۳۲ حرف انگلیسی، عدد یا زیرخط):",
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()

@router.message(CustomSlugStates.waiting_for_personal_slug)
async def process_custom_slug(message: types.Message, state: FSMContext, db_user: User, db_session: AsyncSession):
    if message.text == get_text("btn_cancel"):
        await state.clear()
        await message.answer("عملیات لغو شد.", reply_markup=get_main_menu_keyboard())
        return

    link_service = LinkService(db_session)
    try:
        link = await link_service.set_custom_personal_slug(db_user, message.text)
        public_url = f"https://t.me/{settings.bot_username}?start={link.token}"
        await message.answer(
            f"✅ شناسه اختصاصی با موفقیت ثبت شد:\n`{public_url}`",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
    except AppError as e:
        await message.answer(f"❌ خطا: {e}\nلطفاً شناسه دیگری ارسال کنید.")

@router.message(F.text == get_text("btn_nickname"))
async def prompt_nickname(message: types.Message, db_user: User, state: FSMContext):
    current = db_user.nickname or "تنظیم نشده"
    await state.set_state(NicknameStates.waiting_for_nickname)
    await message.answer(
        f"👤 نام مستعار فعلی شما: **{current}**\n\nبرای تغییر نام مستعار، نام جدید را ارسال کنید یا عبارت «حذف» را بفرستید:",
        reply_markup=get_cancel_keyboard()
    )

@router.message(NicknameStates.waiting_for_nickname)
async def save_nickname(message: types.Message, state: FSMContext, db_user: User, db_session: AsyncSession):
    if message.text == get_text("btn_cancel"):
        await state.clear()
        await message.answer("عملیات لغو شد.", reply_markup=get_main_menu_keyboard())
        return

    from app.database.repositories import UserRepository
    user_repo = UserRepository(db_session)

    if message.text.strip() == "حذف":
        await user_repo.update_nickname(db_user.id, None)
        await message.answer("نام مستعار حذف شد.", reply_markup=get_main_menu_keyboard())
        await state.clear()
        return

    try:
        clean_nick = sanitize_nickname(message.text)
        await user_repo.update_nickname(db_user.id, clean_nick)
        await message.answer(f"✅ نام مستعار شما به **{clean_nick}** تغییر یافت.", reply_markup=get_main_menu_keyboard())
        await state.clear()
    except AppError as e:
        await message.answer(f"❌ خطا: {e}")