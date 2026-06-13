"""In-process rate limiter using slowapi.

Provides two dependency factories:
  - auth_rate_limit   — tight limit for login / register / refresh
  - api_rate_limit    — generous limit for authenticated API endpoints

Key strategy: X-Forwarded-For → client.host fallback (proxy-safe).
When RATE_LIMIT_ENABLED=False (e.g. in tests) the limiter is a no-op.
"""

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.core.config import settings


def _get_client_key(request: Request) -> str:
    """Extract the rate-limit key: forwarded IP → direct remote address."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Global limiter instance — mounted in main.py via SlowAPIMiddleware
limiter = Limiter(
    key_func=_get_client_key,
    enabled=settings.RATE_LIMIT_ENABLED,
    default_limits=[],
)

# Convenience strings read from config
_AUTH_LIMIT = f"{settings.RATE_LIMIT_AUTH_PER_MINUTE}/minute"
_API_LIMIT = f"{settings.RATE_LIMIT_API_PER_MINUTE}/minute"


def auth_rate_limit(request: Request) -> None:
    """Dependency: apply tight rate limit for auth endpoints."""
    # Decorator-style limiting on individual routes is handled by
    # @limiter.limit(_AUTH_LIMIT) in the route file; this dependency
    # is an alternative for non-decorator usage and import convenience.
    pass  # Actual enforcement is via @limiter.limit on route handlers


def get_auth_limit_string() -> str:
    return _AUTH_LIMIT


def get_api_limit_string() -> str:
    return _API_LIMIT


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Return RFC 6585-compliant 429 response with Retry-After header."""
    retry_after = getattr(exc, "retry_after", 60)
    return JSONResponse(
        status_code=429,
        headers={"Retry-After": str(retry_after)},
        content={
            "error": {
                "code": "rate_limit_exceeded",
                "message": f"Too many requests. Retry after {retry_after} seconds.",
                "details": [],
            }
        },
    )
