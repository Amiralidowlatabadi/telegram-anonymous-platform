import uuid
from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User
from app.database.repositories import ConversationRepository
from app.services.message_router import MessageRouter
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

@router.callback_query(F.data.startswith("reply_msg:"))
async def handle_reply_button_click(
    call: types.CallbackQuery,
    db_user: User,
    db_session: AsyncSession,
    message_router: MessageRouter
):
    conv_id_str = call.data.split(":")[1]
    conv_repo = ConversationRepository(db_session)
    
    # Locate last incoming message for this conversation
    stmt = (
        types.select(conv_repo.session.get_bind())
        if False else None
    )
    from sqlalchemy import select
    from app.database.models import ConversationMessage
    
    stmt = select(ConversationMessage).where(
        ConversationMessage.conversation_id == uuid.UUID(conv_id_str),
        ConversationMessage.recipient_user_id == db_user.id
    ).order_by(ConversationMessage.created_at.desc())
    res = await db_session.execute(stmt)
    last_msg = res.scalar_one_or_none()

    if not last_msg:
        await call.answer("پیامی جهت پاسخ یافت نشد.", show_alert=True)
        return

    # Lock active reply target strictly to this message
    await message_router.set_active_reply_target(db_user.telegram_id, last_msg.id)
    await call.message.reply(
        get_text("reply_target_locked"),
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()

@router.message(F.text == get_text("btn_cancel"))
async def cancel_active_reply(message: types.Message, db_user: User, message_router: MessageRouter):
    await message_router.clear_active_reply_target(db_user.telegram_id)
    await message.answer("حالت پاسخ لغو شد.", reply_markup=get_main_menu_keyboard())

@router.message(F.reply_to_message | F.text | F.photo | F.video | F.voice)
async def process_owner_reply_dispatch(
    message: types.Message,
    db_user: User,
    db_session: AsyncSession,
    message_router: MessageRouter
):
    active_target = await message_router.get_active_reply_target(db_user.telegram_id)
    if not active_target:
        # Not in active reply mode, let other standard handlers take over or ignore
        return

    from app.bot.handlers.personal_chat import extract_payload
    content_type, payload = extract_payload(message)
    if content_type == "unknown":
        return

    try:
        await message_router.dispatch_owner_reply(
            owner=db_user,
            content_type=content_type,
            payload=payload
        )
        await message.answer(get_text("reply_sent_success"), reply_markup=get_main_menu_keyboard())
    except AppError as e:
        await message.answer(f"❌ خطا در ارسال پاسخ: {e}")