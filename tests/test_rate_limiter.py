import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.rate_limiter import RedisRateLimiter
from app.core.exceptions import RateLimitExceededError

@pytest.mark.asyncio
async def test_rate_limiter_within_limit():
    redis_mock = MagicMock()
    pipe_mock = MagicMock()
    pipe_mock.execute = AsyncMock(return_value=[None, None, 3, None])
    redis_mock.pipeline.return_value = pipe_mock

    limiter = RedisRateLimiter(redis_mock)
    await limiter.check_rate_limit("test_user", limit=5, window_seconds=60)

@pytest.mark.asyncio
async def test_rate_limiter_exceeded():
    redis_mock = MagicMock()
    pipe_mock = MagicMock()
    pipe_mock.execute = AsyncMock(return_value=[None, None, 6, None])
    redis_mock.pipeline.return_value = pipe_mock

    limiter = RedisRateLimiter(redis_mock)
    with pytest.raises(RateLimitExceededError):
        await limiter.check_rate_limit("test_user", limit=5, window_seconds=60)
