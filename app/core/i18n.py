MESSAGES = {
    "welcome": "سلام! به پلتفرم ارسال و دریافت پیام ناشناس خوش آمدید.\nیکی از گزینه‌های زیر را انتخاب کنید:",
    "btn_personal_link": "🔗 لینک ناشناس من",
    "btn_inbox": "📥 صندوق پیام‌ها",
    "btn_channel_submission": "📢 ارسال ناشناس به کانال",
    "btn_nickname": "👤 نام مستعار",
    "btn_settings": "⚙️ تنظیمات",
    "btn_reply": "↩️ پاسخ",
    "btn_close_conv": "❌ بستن گفتگو",
    "btn_block": "🚫 مسدود کردن فرستنده",
    "btn_report": "🚨 گزارش تخلف",
    "btn_seen": "👁 پیام را دیدم",
    "btn_back": "🔙 بازگشت",
    "btn_cancel": "❌ لغو عملیات",
    "personal_link_info": "🔗 **لینک پیام ناشناس اختصاصی شما:**\n\n`{link}`\n\nوضعیت: {status}\nهر کس این لینک را باز کند، می‌تواند بدون افشای هویت خود با شما گفتگو کند.",
    "link_active": "🟢 فعال",
    "link_inactive": "🔴 غیرفعال",
    "reply_target_locked": "↩️ **در حال پاسخ به پیام ناشناس...**\nپیام بعدی شما مستقیماً برای این مخاطب ارسال خواهد شد.\nبرای خروج از این حالت روی «لغو» کلیک کنید.",
    "reply_sent_success": "✅ پاسخ شما با موفقیت و به صورت کاملاً ناشناس برای مخاطب ارسال شد.",
    "anon_message_received": "📩 **پیام ناشناس جدید دریافت شد:**\n\n{content}",
    "channel_post_published": "✅ پیام شما با موفقیت در کانال منتشر شد.",
    "seen_notification": "👁 پیام ارسالی شما در کانال توسط {count} نفر مشاهده شد.",
    "user_blocked_notice": "🚫 این مخاطب ناشناس با موفقیت مسدود شد و دیگر قادر به ارسال پیام به شما نخواهد بود.",
    "error_generic": "⚠️ خطایی رخ داد. لطفاً مجدداً تلاش کنید.",
    "error_rate_limited": "⏳ شما بیش از حد مجاز پیام ارسال کرده‌اید. لطفاً اندکی صبر کنید.",
    "error_blocked": "⛔ امکان ارسال پیام به این کاربر وجود ندارد.",
    "error_link_disabled": "⚠️ این لینک در حال حاضر غیرفعال شده است.",
    "error_invalid_link": "❌ لینک مورد نظر نامعتبر است یا منقضی شده است.",
    "report_submitted": "🚨 گزارش شما ثبت شد و توسط تیم مدیریت بررسی خواهد شد."
}

def get_text(key: str, **kwargs) -> str:
    template = MESSAGES.get(key, key)
    if kwargs:
        return template.format(**kwargs)
    return template