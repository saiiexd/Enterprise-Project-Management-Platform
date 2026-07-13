import logging

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger("epmp.redis")


class RedisService:
    def __init__(self) -> None:
        self.client: Redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def blacklist_token(self, token: str, expires_in_seconds: int) -> None:
        try:
            # Store blacklisted token with expiration
            await self.client.setex(f"blacklist:{token}", expires_in_seconds, "1")
        except Exception as e:
            logger.error(f"Redis blacklist_token error: {e}")

    async def is_token_blacklisted(self, token: str) -> bool:
        try:
            val = await self.client.get(f"blacklist:{token}")
            return val is not None
        except Exception as e:
            logger.error(f"Redis is_token_blacklisted error: {e}")
            return False

    async def increment_login_attempts(self, email: str) -> int:
        try:
            key = f"attempts:{email}"
            attempts = await self.client.incr(key)
            if attempts == 1:
                # Set lockout tracking window to 15 minutes (900 seconds)
                await self.client.expire(key, 900)
            return int(attempts)
        except Exception as e:
            logger.error(f"Redis increment_login_attempts error: {e}")
            return 0

    async def reset_login_attempts(self, email: str) -> None:
        try:
            await self.client.delete(f"attempts:{email}")
        except Exception as e:
            logger.error(f"Redis reset_login_attempts error: {e}")

    async def rate_limit_check(self, ip_or_key: str, limit: int, window: int) -> bool:
        """
        Returns True if request is allowed, False if it exceeds rate limits.
        """
        try:
            key = f"rate:{ip_or_key}"
            requests = await self.client.incr(key)
            if requests == 1:
                await self.client.expire(key, window)
            return int(requests) <= limit
        except Exception as e:
            logger.error(f"Redis rate_limit_check error: {e}")
            return True  # Fallback to true if Redis fails to prevent lockouts


redis_service = RedisService()
