import time
import redis.asyncio as redis
from app.core.exceptions import RateLimitExceededError

class RedisRateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_rate_limit(self, identifier: str, limit: int, window_seconds: int = 60) -> None:
        """Sliding window rate-limiter using Redis sorted sets."""
        current_time = time.time()
        key = f"rate_limit:{identifier}:{window_seconds}"
        
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, current_time - window_seconds)
        pipe.zadd(key, {f"{current_time}": current_time})
        pipe.zcard(key)
        pipe.expire(key, window_seconds + 1)
        results = await pipe.execute()
        
        request_count = results[2]
        if request_count > limit:
            raise RateLimitExceededError("شما بیش از حد مجاز درخواست ارسال کرده‌اید. لطفاً شکیبا باشید.")