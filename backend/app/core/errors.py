from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _error_payload(
    *,
    code: str,
    message: str,
    details: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
        }
    }


def _http_status_to_code(status_code: int) -> str:
    mapping = {
        status.HTTP_400_BAD_REQUEST: "bad_request",
        status.HTTP_401_UNAUTHORIZED: "unauthorized",
        status.HTTP_403_FORBIDDEN: "forbidden",
        status.HTTP_404_NOT_FOUND: "not_found",
        status.HTTP_409_CONFLICT: "conflict",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "validation_error",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "internal_error",
    }
    return mapping.get(status_code, "bad_request")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details: list[dict[str, str]] = []
        for error in exc.errors():
            field_parts = [str(part) for part in error.get("loc", ()) if part != "body"]
            field = ".".join(field_parts) if field_parts else "body"
            details.append({"field": field, "message": error.get("msg", "Invalid value.")})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_payload(
                code="validation_error",
                message="Request validation failed.",
                details=details,
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)

        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                code=_http_status_to_code(exc.status_code),
                message=str(exc.detail),
            ),
        )
