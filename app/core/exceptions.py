class AppError(Exception):
    """Base application exception."""
    pass

class ValidationError(AppError):
    pass

class SlugCollisionError(AppError):
    pass

class RateLimitExceededError(AppError):
    pass

class EntityNotFoundError(AppError):
    pass

class PermissionDeniedError(AppError):
    pass

class UserBlockedError(AppError):
    pass

class ChannelPermissionError(AppError):
    pass

class ReplyTargetExpiredError(AppError):
    pass