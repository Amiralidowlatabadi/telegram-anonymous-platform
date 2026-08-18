from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from app.core.i18n import get_text

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text("btn_personal_link")), KeyboardButton(text=get_text("btn_inbox"))],
            [KeyboardButton(text=get_text("btn_nickname")), KeyboardButton(text=get_text("btn_settings"))],
        ],
        resize_keyboard=True
    )

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_text("btn_cancel"))]],
        resize_keyboard=True
    )

def get_link_management_keyboard(is_active: bool) -> InlineKeyboardMarkup:
    toggle_text = "🔴 غیرفعال‌سازی لینک" if is_active else "🟢 فعال‌سازی لینک"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data="toggle_link_status")],
            [InlineKeyboardButton(text="🔄 بازتولید لینک تصادفی", callback_data="regen_link")],
            [InlineKeyboardButton(text="✏️ انتخاب شناسه اختصاصی (Slug)", callback_data="set_custom_slug")],
        ]
    )

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 آمار کلی سیستم", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📥 گزارش‌های تخلف", callback_data="admin_reports")],
            [InlineKeyboardButton(text="📢 کانال‌های متصل", callback_data="admin_channels")],
        ]
    )