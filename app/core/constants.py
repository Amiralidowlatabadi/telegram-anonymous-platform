RESERVED_SLUGS = {
    "admin", "administrator", "support", "help", "settings", "start",
    "channel", "group", "bot", "official", "moderator", "system",
    "inbox", "login", "register", "api", "dashboard", "null", "undefined",
    "peymannashenas", "harfbezan", "telebot"
}

MIN_SLUG_LENGTH = 3
MAX_SLUG_LENGTH = 32
SLUG_REGEX = r"^[a-zA-Z0-9_]{3,32}$"

NICKNAME_MIN_LENGTH = 2
NICKNAME_MAX_LENGTH = 32
NICKNAME_REGEX = r"^[\w\u0600-\u06FF\s]{2,32}$"

BANNED_WORDS = [
    "قمار", "شرط بندی", "فیشینگ", "صیغه", "فروش فالوور"
]