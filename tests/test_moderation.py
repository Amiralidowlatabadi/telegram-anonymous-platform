import pytest
from app.services.moderation_service import ContentModerationFilter
from app.core.exceptions import ValidationError

def test_moderation_banned_words():
    mod = ContentModerationFilter()
    with pytest.raises(ValidationError):
        mod.evaluate_text("این یک پیام حاوی قمار و شرط بندی است")

def test_moderation_excessive_links():
    mod = ContentModerationFilter()
    with pytest.raises(ValidationError):
        mod.evaluate_text("https://site1.com https://site2.com https://site3.com https://site4.com")

def test_moderation_clean_text():
    mod = ContentModerationFilter()
    mod.evaluate_text("سلام وقتتون بخیر، پیام من کاملا امن است.")
