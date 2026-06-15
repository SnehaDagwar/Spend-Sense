import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.security import decode_token

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log details of every incoming HTTP request and response.

    Logs execution time, status code, method, path, IP, user agent,
    and user_id if the request is authenticated with a valid JWT.
    """

    async def dispatch(self, request: Request, call_next: object) -> Response:
        start_time = time.perf_counter()

        # Extract user_id from JWT token if present
        user_id = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
            try:
                payload = decode_token(token, expected_type="access")
                user_id = payload.get("sub")
            except Exception:
                # If token is invalid or expired, ignore it for logging purposes
                pass

        try:
            response: Response = await call_next(request)  # type: ignore[call-arg]
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            extra = {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
            if user_id:
                extra["user_id"] = str(user_id)

            log_msg = f"{request.method} {request.url.path} finished with {response.status_code} in {duration_ms:.2f}ms"

            if response.status_code >= 500:
                logger.error(log_msg, extra=extra)
            elif response.status_code >= 400:
                logger.warning(log_msg, extra=extra)
            else:
                logger.info(log_msg, extra=extra)

            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            extra = {
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "duration_ms": round(duration_ms, 2),
                "ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
            if user_id:
                extra["user_id"] = str(user_id)

            logger.exception(
                f"Unhandled exception during {request.method} {request.url.path}: {exc}",
                extra=extra,
            )
            raise exc
