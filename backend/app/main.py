from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.limiter import limiter


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject security headers on every response.

    HSTS is only set in production to avoid confusing local HTTPS setups.
    CSP is set to 'default-src none' since this is a pure JSON API
    that never serves HTML, scripts, or styles.
    """

    async def dispatch(self, request: Request, call_next: object) -> Response:
        response: Response = await call_next(request)  # type: ignore[call-arg]
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'none'"
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


def create_app() -> FastAPI:
    openapi_url = (
        f"{settings.API_V1_PREFIX}/openapi.json" if settings.OPENAPI_ENABLED else None
    )

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        openapi_url=openapi_url,
    )

    # ── Rate limiting ───────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    # ── Security headers ────────────────────────────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)

    # ── CORS ────────────────────────────────────────────────────────────
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(o) for o in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "Accept"],
        )

    # ── Exception handlers ──────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routes ─────────────────────────────────────────────────────────
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", tags=["root"])
    def root() -> dict[str, str]:
        return {"name": settings.APP_NAME, "status": "ok"}

    return app


app = create_app()
