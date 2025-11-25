"""Middleware for API key verification."""

from typing import Awaitable, Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.settings import get_settings

settings = get_settings()


EXCLUDE_PATHS = {
    "/docs",
    "/openapi.json",
    "/redoc",
    "/health",
    "/",
}


async def api_key_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable],
):
    """Validate API key for protected endpoints."""
    if request.url.path in EXCLUDE_PATHS or request.url.path.startswith("/openapi"):
        return await call_next(request)

    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != settings.secrets.x_api_key:
        return JSONResponse(
            {"detail": "Invalid API key"},
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return await call_next(request)


__all__ = ["api_key_middleware"]

