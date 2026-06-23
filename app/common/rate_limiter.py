import time
from collections import defaultdict
from typing import DefaultDict

from fastapi import HTTPException, Request


class RateLimiter:
    _CLEANUP_EVERY = 500

    def __init__(self, requests_per_hour: int = 10) -> None:
        self.requests_per_hour = requests_per_hour
        self.window_size = 3600
        self._store: DefaultDict[str, list[float]] = defaultdict(list)
        self._check_count = 0

    def check_limit(self, request: Request) -> None:
        self._check_count += 1
        if self._check_count % self._CLEANUP_EVERY == 0:
            self._cleanup()

        client_id = self._client_id(request)
        now = time.time()
        window = self._store[client_id]
        window[:] = [t for t in window if now - t < self.window_size]

        if len(window) >= self.requests_per_hour:
            reset_in = self._reset_in(window)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.requests_per_hour} requests/hour. Retry in {reset_in}s.",
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_hour),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + reset_in)),
                    "Retry-After": str(reset_in),
                },
            )

        window.append(now)

    def remaining(self, request: Request) -> int:
        client_id = self._client_id(request)
        now = time.time()
        window = self._store[client_id]
        active = [t for t in window if now - t < self.window_size]
        return max(0, self.requests_per_hour - len(active))

    def _client_id(self, request: Request) -> str:
        return request.headers.get("X-Client-ID") or (
            request.client.host if request.client else "unknown"
        )

    def _reset_in(self, window: list[float]) -> int:
        if not window:
            return 0
        return max(0, int(self.window_size - (time.time() - min(window))))

    def _cleanup(self) -> None:
        now = time.time()
        stale = [k for k, v in self._store.items() if not any(now - t < self.window_size for t in v)]
        for k in stale:
            del self._store[k]
