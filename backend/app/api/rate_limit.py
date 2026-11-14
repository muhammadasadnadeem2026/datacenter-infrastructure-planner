"""Simple in-process sliding-window rate limiter.

Suitable for a single instance. Behind multiple replicas, enforce limits at the
reverse proxy / API gateway as well (see README, Production deployment).
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

WINDOW_S = 60.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit_per_minute: int):
        super().__init__(app)
        self.limit = limit_per_minute
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if self.limit <= 0 or not request.url.path.startswith("/api/") or request.url.path == "/api/health":
            return await call_next(request)
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > WINDOW_S:
            q.popleft()
        if len(q) >= self.limit:
            retry = max(1, int(WINDOW_S - (now - q[0])))
            return JSONResponse({"detail": "rate limit exceeded"}, status_code=429,
                                headers={"Retry-After": str(retry)})
        q.append(now)
        return await call_next(request)
