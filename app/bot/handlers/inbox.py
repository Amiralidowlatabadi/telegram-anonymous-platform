import uuid
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User, ConversationMessage
from app.database.repositories import ConversationRepository
from app.services.message_router import MessageRouter
from app.bot.states import PersonalChatStates
from app.bot.keyboards import get_cancel_keyboard, get_main_menu_keyboard
from app.core.i18n import get_text
from app.core.exceptions import AppError

router = Router(name="inbox_router")

@router.message(F.text == get_text("btn_inbox"))
async def show_inbox(message: types.Message, db_user: User, db_session: AsyncSession):
    conv_repo = ConversationRepository(db_session)
    conversations = await conv_repo.get_user_conversations(db_user.id)
    
    if not conversations:
        await message.answer("📭 صندوق پیام‌های ناشناس شما خالی است.")
        return

    text = "📥 **صندوق پیام‌های ناشناس فعال:**\n\n"
    buttons = []
    for idx, c in enumerate(conversations[:10], start=1):
        status_icon = "🟢" if c.status == "ACTIVE" else "🔴"
        text += f"{idx}. {status_icon} گفتگوی ناشناس ({c.status})\n"
        buttons.append([types.InlineKeyboardButton(text=f"مشاهده گفتگوی {idx}", callback_data=f"open_conv:{c.id}")])

    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=kb)

@router.callback_query(F.data.startswith("open_conv:"))
async def handle_open_conversation(
    call: types.CallbackQuery,
    db_user: User,
    db_session: AsyncSession
):
    conv_id_str = call.data.split(":")[1]
    conv_repo = ConversationRepository(db_session)
    conv = await conv_repo.get_by_id(uuid.UUID(conv_id_str))
    
    if not conv or conv.owner_id != db_user.id:
        await call.answer("گفتگوی مورد نظر یافت نشد.", show_alert=True)
        return

    stmt = select(ConversationMessage).where(
        ConversationMessage.conversation_id == conv.id
    ).order_by(ConversationMessage.created_at.desc()).limit(1)
    res = await db_session.execute(stmt)
    last_msg = res.scalar_one_or_none()

    status_icon = "🟢 فعال" if conv.status == "ACTIVE" else "🔴 غیرفعال"
    details = f"💬 **اطلاعات گفتگو:**\n\nوضعیت: {status_icon}\n"
    if last_msg:
        details += f"آخرین پیام: {last_msg.created_at.strftime('%Y-%m-%d %H:%M')}\nنوع محتوا: {last_msg.content_type}"
    
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="↩️ پاسخ به این گفتگو", callback_data=f"reply_msg:{conv.id}")],
            [
                types.InlineKeyboardButton(text="🚫 مسدود کردن", callback_data=f"block_conv:{conv.id}"),
                types.InlineKeyboardButton(text="🚨 گزارش", callback_data=f"report_conv:{conv.id}"),
            ]
        ]
    )
    await call.message.answer(details, reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("reply_msg:"))
async def handle_reply_button_click(
    call: types.CallbackQuery,
    state: FSMContext,
    db_user: User,
    db_session: AsyncSession,
    message_router: MessageRouter
):
    conv_id_str = call.data.split(":")[1]
    
    stmt = select(ConversationMessage).where(
        ConversationMessage.conversation_id == uuid.UUID(conv_id_str),
        ConversationMessage.recipient_user_id == db_user.id
    ).order_by(ConversationMessage.created_at.desc())
    res = await db_session.execute(stmt)
    last_msg = res.scalar_one_or_none()

    if not last_msg:
        await call.answer("پیامی جهت پاسخ یافت نشد.", show_alert=True)
        return

    # Lock active reply target strictly to this message in Redis and FSM
    await message_router.set_active_reply_target(db_user.telegram_id, last_msg.id)
    await state.set_state(PersonalChatStates.replying_to_message)
    await call.message.reply(
        get_text("reply_target_locked"),
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()

@router.message(PersonalChatStates.replying_to_message)
async def process_owner_reply_dispatch(
    message: types.Message,
    state: FSMContext,
    db_user: User,
    message_router: MessageRouter
):
    if message.text == get_text("btn_cancel"):
        await message_router.clear_active_reply_target(db_user.telegram_id)
        await state.clear()
        await message.answer("حالت پاسخ لغو شد.", reply_markup=get_main_menu_keyboard())
        return

    from app.bot.handlers.personal_chat import extract_payload
    content_type, payload = extract_payload(message)
    if content_type == "unknown":
        await message.answer("⚠️ نوع فایل ارسالی پشتیبانی نمی‌شود.")
        return

    try:
        await message_router.dispatch_owner_reply(
            owner=db_user,
            content_type=content_type,
            payload=payload
        )
        await message_router.clear_active_reply_target(db_user.telegram_id)
        await state.clear()
        await message.answer(get_text("reply_sent_success"), reply_markup=get_main_menu_keyboard())
    except AppError as e:
        await message.answer(f"❌ خطا در ارسال پاسخ: {e}")