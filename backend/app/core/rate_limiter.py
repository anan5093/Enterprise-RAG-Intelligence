import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        identifier = request.headers.get("authorization") or (request.client.host if request.client else "anonymous")
        now = time.time()
        hits = self._hits[identifier]
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()
        if len(hits) >= self.requests_per_minute:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        hits.append(now)
        return await call_next(request)

