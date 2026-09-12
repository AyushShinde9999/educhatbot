import time
from collections import defaultdict
from fastapi import HTTPException, Request, status

class SimpleRateLimiter:
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.client_requests = defaultdict(list)

    def check_rate_limit(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Clean timestamps older than 60 seconds
        self.client_requests[client_ip] = [
            ts for ts in self.client_requests[client_ip] if now - ts < 60
        ]
        
        if len(self.client_requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait a minute before asking more questions."
            )
            
        self.client_requests[client_ip].append(now)

chat_rate_limiter = SimpleRateLimiter(requests_per_minute=40)
