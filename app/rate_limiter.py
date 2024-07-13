import time
import redis
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", 6379))

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int, window_size: int):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_size = window_size
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = int(time.time())
        window_start = current_time // self.window_size * self.window_size

        request_count = self.redis_client.get(f"{client_ip}:{window_start}")
        if request_count is None:
            self.redis_client.set(f"{client_ip}:{window_start}", 1, ex=self.window_size)
        elif int(request_count) < self.max_requests:
            self.redis_client.incr(f"{client_ip}:{window_start}")
        else:
            return Response("Too many requests", status_code=429)

        response = await call_next(request)
        return response
