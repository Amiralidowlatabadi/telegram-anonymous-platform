from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.database.models import User, Conversation, ChannelMessage, Report
from app.bot.keyboards import get_admin_panel_keyboard

router = Router(name="admin_router")
settings = get_settings()

@router.message(Command("admin"))
async def show_admin_panel(message: types.Message):
    if message.from_user.id not in settings.admin_telegram_ids:
        return
    await message.answer("🛡 **پنل مدیریت ارشد سامانه ناشناس**", reply_markup=get_admin_panel_keyboard())

@router.callback_query(F.data == "admin_stats")
async def view_admin_stats(call: types.CallbackQuery, db_session: AsyncSession):
    if call.from_user.id not in settings.admin_telegram_ids:
        await call.answer("دسترسی غیرمجاز", show_alert=True)
        return

    users_count = (await db_session.execute(select(func.count(User.id)))).scalar() or 0
    convs_count = (await db_session.execute(select(func.count(Conversation.id)))).scalar() or 0
    posts_count = (await db_session.execute(select(func.count(ChannelMessage.id)))).scalar() or 0
    reports_count = (await db_session.execute(select(func.count(Report.id)).where(Report.status == "PENDING"))).scalar() or 0

    text = (
        "📊 **آمار کلی پلتفرم:**\n\n"
        f"👥 کل کاربران ثبت‌شده: `{users_count}`\n"
        f"💬 کل گفتگوهای دوطرفه: `{convs_count}`\n"
        f"📢 کل پست‌های ارسالی کانال: `{posts_count}`\n"
        f"🚨 گزارش‌های در انتظار بررسی: `{reports_count}`\n"
    )
    await call.message.edit_text(text, reply_markup=get_admin_panel_keyboard())
    await call.answer()