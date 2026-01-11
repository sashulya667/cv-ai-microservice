import time
from collections import defaultdict
from typing import DefaultDict

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self, requests_per_hour: int = 10):
        self.requests_per_hour = requests_per_hour
        self.window_size = 3600
        self.requests: DefaultDict[str, list[float]] = defaultdict(list)

    def get_client_id(self, request: Request) -> str:
        return request.headers.get("X-Client-ID") or (
            request.client.host if request.client else "unknown"
        )

    def is_allowed(self, request: Request) -> bool:
        client_id = self.get_client_id(request)
        now = time.time()
        
        requests = self.requests[client_id]
        requests[:] = [req_time for req_time in requests if now - req_time < self.window_size]
        
        if len(requests) >= self.requests_per_hour:
            return False
        
        requests.append(now)
        return True

    def get_remaining(self, request: Request) -> int:
        client_id = self.get_client_id(request)
        now = time.time()
        requests = self.requests[client_id]
        requests[:] = [req_time for req_time in requests if now - req_time < self.window_size]
        return max(0, self.requests_per_hour - len(requests))

    def check_limit(self, request: Request) -> None:
        if not self.is_allowed(request):
            remaining_time = self._get_reset_time(request)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.requests_per_hour} per hour. Try again in {remaining_time} seconds.",
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_hour),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + remaining_time)),
                },
            )

    def _get_reset_time(self, request: Request) -> int:
        client_id = self.get_client_id(request)
        requests = self.requests[client_id]
        if not requests:
            return 0
        oldest_request = min(requests)
        return max(0, int(self.window_size - (time.time() - oldest_request)))

