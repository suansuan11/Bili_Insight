"""API认证中间件"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from ..config import settings

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.api_key:
            return await call_next(request)

        # 跳过OPTIONS预检请求和公开路径
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if api_key != settings.api_key:
            raise HTTPException(status_code=403, detail="Invalid API key")

        return await call_next(request)
