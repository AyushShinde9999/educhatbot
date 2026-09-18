import time
import logging
from collections import defaultdict
from urllib.parse import urlparse
from fastapi import HTTPException, Request, status
from app.config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, requests_per_minute: int = 40):
        self.requests_per_minute = requests_per_minute
        self.client_requests = defaultdict(list)
        self.redis_client = None

        redis_url = settings.REDIS_URL.strip().strip('"').strip("'")
        if redis_url and urlparse(redis_url).scheme in {"redis", "rediss", "unix"}:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                logger.info("Redis rate limiting configured")
            except Exception as e:
                logger.warning("Could not configure Redis (%s); using in-memory rate limiting.", str(e))
        elif redis_url:
            logger.warning(
                "REDIS_URL must use redis://, rediss://, or unix://; using in-memory rate limiting."
            )

    def check_rate_limit(self, request: Request, identifier: str = None):
        client_ip = identifier or (request.client.host if request.client else "unknown")
        now = time.time()

        if self.redis_client:
            try:
                key = f"rate_limit:{client_ip}"
                current_count = self.redis_client.get(key)
                if current_count and int(current_count) >= self.requests_per_minute:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Please wait before asking more questions."
                    )
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, 60)
                pipe.execute()
                return
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Redis rate limit check failed: {str(e)}. Falling back to in-memory.")

        # In-memory sliding window
        self.client_requests[client_ip] = [
            ts for ts in self.client_requests[client_ip] if now - ts < 60
        ]

        if len(self.client_requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait a minute before sending more requests."
            )

        self.client_requests[client_ip].append(now)

chat_rate_limiter = RateLimiter(requests_per_minute=40)
auth_rate_limiter = RateLimiter(requests_per_minute=10)
