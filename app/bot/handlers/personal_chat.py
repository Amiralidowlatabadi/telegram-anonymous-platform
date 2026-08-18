import uuid
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User
from app.database.repositories import UserRepository, LinkRepository
from app.services.conversation_service import ConversationService
from app.services.message_router import MessageRouter
from app.services.moderation_service import ContentModerationFilter
from app.bot.states import PersonalChatStates
from app.bot.keyboards import get_main_menu_keyboard
from app.core.exceptions import AppError
from app.core.i18n import get_text

router = Router(name="personal_chat_router")

def extract_payload(message: types.Message) -> tuple[str, dict]:
    if message.text:
        return "text", {"text": message.text}
    if message.photo:
        return "photo", {"file_id": message.photo[-1].file_id, "caption": message.caption or ""}
    if message.video:
        return "video", {"file_id": message.video.file_id, "caption": message.caption or ""}
    if message.voice:
        return "voice", {"file_id": message.voice.file_id, "caption": message.caption or ""}
    if message.video_note:
        return "video_note", {"file_id": message.video_note.file_id}
    if message.document:
        return "document", {"file_id": message.document.file_id, "caption": message.caption or ""}
    if message.audio:
        return "audio", {"file_id": message.audio.file_id, "caption": message.caption or ""}
    if message.sticker:
        return "sticker", {"file_id": message.sticker.file_id}
    return "unknown", {}

@router.message(PersonalChatStates.composing_message)
async def process_anonymous_submission(
    message: types.Message,
    state: FSMContext,
    db_user: User,
    db_session: AsyncSession,
    message_router: MessageRouter
):
    if message.text == get_text("btn_cancel"):
        await state.clear()
        await message.answer("عملیات ارسال لغو شد.", reply_markup=get_main_menu_keyboard())
        return

    data = await state.get_data()
    owner_id_str = data.get("target_owner_user_user_id") or data.get("target_owner_user_id")
    link_id_str = data.get("target_personal_link_id")

    if not owner_id_str:
        await state.clear()
        await message.answer(get_text("error_generic"), reply_markup=get_main_menu_keyboard())
        return

    content_type, payload = extract_payload(message)
    if content_type == "unknown":
        await message.answer("⚠️ فرمت این نوع فایل پشتیبانی نمی‌شود.")
        return

    if payload.get("text") or payload.get("caption"):
        mod_filter = ContentModerationFilter()
        try:
            mod_filter.evaluate_text(payload.get("text") or payload.get("caption") or "")
        except AppError as e:
            await message.answer(str(e))
            return

    user_repo = UserRepository(db_session)
    owner = await user_repo.get_by_id(uuid.UUID(owner_id_str))
    if not owner:
        await message.answer(get_text("error_generic"))
        await state.clear()
        return

    conv_service = ConversationService(db_session)
    try:
        conv = await conv_service.initiate_or_resume(
            owner=owner,
            sender=db_user,
            link_id=uuid.UUID(link_id_str) if link_id_str else None
        )
        await message_router.dispatch_anonymous_to_owner(
            conversation_id=conv.id,
            sender=db_user,
            owner=owner,
            content_type=content_type,
            payload=payload
        )
        await message.answer("✅ پیام شما با موفقیت و به صورت کاملاً ناشناس تحویل داده شد.", reply_markup=get_main_menu_keyboard())
        await state.clear()
    except AppError as e:
        await message.answer(f"❌ خطا: {e}", reply_markup=get_main_menu_keyboard())
        await state.clear()