import re
from typing import List
from app.core.constants import BANNED_WORDS
from app.core.exceptions import ValidationError

class ContentModerationFilter:
    def __init__(self, custom_banned_words: List[str] | None = None):
        self.banned_words = set(BANNED_WORDS + (custom_banned_words or []))

    def evaluate_text(self, text: str) -> None:
        clean_text = text.lower()
        for word in self.banned_words:
            if word in clean_text:
                raise ValidationError("پیام شما حاوی عبارات غیرمجاز است و قابل ارسال نیست.")
        
        url_patterns = r"(https?://\S+|t\.me/\S+)"
        if len(re.findall(url_patterns, text)) > 3:
            raise ValidationError("ارسال لینک‌های متعدد در پیام مجاز نمی‌باشد.")