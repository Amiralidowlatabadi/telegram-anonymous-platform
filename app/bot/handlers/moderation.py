import uuid
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User
from app.database.repositories import ReportRepository
from app.services.conversation_service import ConversationService
from app.services.seen_tracker import SeenTrackerService
from app.bot.states import ReportStates
from app.core.i18n import get_text

router = Router(name="moderation_router")

@router.callback_query(F.data.startswith("block_conv:"))
async def handle_block_participant(call: types.CallbackQuery, db_user: User, db_session: AsyncSession):
    conv_id_str = call.data.split(":")[1]
    conv_service = ConversationService(db_session)
    try:
        await conv_service.block_conversation_participant(db_user, uuid.UUID(conv_id_str))
        await call.answer(get_text("user_blocked_notice"), show_alert=True)
    except Exception as e:
        await call.answer(f"خطا: {e}", show_alert=True)

@router.callback_query(F.data.startswith("report_conv:"))
async def prompt_report(call: types.CallbackQuery, state: FSMContext):
    conv_id_str = call.data.split(":")[1]
    await state.set_state(ReportStates.waiting_for_reason)
    await state.update_data(reporting_conv_id=conv_id_str)
    await call.message.reply("🚨 لطفاً دلیل گزارش تخلف این گفتگو را ارسال نمایید:")
    await call.answer()

@router.message(ReportStates.waiting_for_reason)
async def process_report_submission(message: types.Message, state: FSMContext, db_user: User, db_session: AsyncSession):
    data = await state.get_data()
    conv_id_str = data.get("reporting_conv_id")
    if not conv_id_str:
        await state.clear()
        return

    report_repo = ReportRepository(db_session)
    await report_repo.create_report(
        reporter_id=db_user.id,
        conv_id=uuid.UUID(conv_id_str),
        reason=message.text
    )
    await message.answer(get_text("report_submitted"))
    await state.clear()

@router.callback_query(F.data.startswith("seen_post:"))
async def handle_seen_post_click(call: types.CallbackQuery, seen_tracker: SeenTrackerService, bot: types.Bot):
    channel_tg_id = int(call.data.split(":")[1])
    message_tg_id = call.message.message_id
    viewer_tg_id = call.from_user.id

    is_new, total_count, author = await seen_tracker.register_seen_event(
        channel_tg_id=channel_tg_id,
        message_tg_id=message_tg_id,
        viewer_tg_id=viewer_tg_id
    )

    if not is_new:
        await call.answer("شما قبلاً بازدید خود را برای این پیام ثبت کرده‌اید.", show_alert=False)
        return

    await call.answer(f"👁 بازدید شما ثبت شد (مجموع: {total_count})")
    
    if author:
        try:
            await bot.send_message(
                chat_id=author.telegram_id,
                text=get_text("seen_notification", count=total_count)
            )
        except Exception:
            pass  # Non-blocking if author blocked the bot