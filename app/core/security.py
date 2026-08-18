import secrets
import re
from app.core.constants import RESERVED_SLUGS, SLUG_REGEX, MIN_SLUG_LENGTH, MAX_SLUG_LENGTH
from app.core.exceptions import ValidationError, SlugCollisionError

def generate_secure_token(prefix: str = "") -> str:
    """Generates a high-entropy cryptographically secure random opaque token."""
    raw_token = secrets.token_urlsafe(16)
    return f"{prefix}{raw_token}"

def sanitize_slug(slug: str) -> str:
    """Validates and sanitizes a user-requested custom slug."""
    clean_slug = slug.strip().lower()
    if len(clean_slug) < MIN_SLUG_LENGTH or len(clean_slug) > MAX_SLUG_LENGTH:
        raise ValidationError(f"طول شناسه انتخابی باید بین {MIN_SLUG_LENGTH} تا {MAX_SLUG_LENGTH} نویسه باشد.")
    
    if not re.match(SLUG_REGEX, clean_slug):
        raise ValidationError("شناسه فقط می‌تواند شامل حروف انگلیسی، اعداد و زیرخط (_) باشد.")
        
    if clean_slug in RESERVED_SLUGS:
        raise ValidationError("این شناسه جزو کلمات رزرو شده سیستم است و امکان ثبت آن وجود ندارد.")
        
    return clean_slug

def sanitize_nickname(nickname: str) -> str:
    """Sanitizes user nickname ensuring no HTML injections or illegal spoofing."""
    clean = re.sub(r"[<>&\"']", "", nickname).strip()
    if len(clean) < 2 or len(clean) > 32:
        raise ValidationError("نام مستعار باید بین ۲ تا ۳۲ نویسه باشد.")
    if clean.lower() in RESERVED_SLUGS:
        raise ValidationError("استفاده از این نام مستعار مجاز نیست.")
    return clean