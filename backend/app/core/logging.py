"""Structured logging configuration for Spend Sense API.

- Production / staging: emits JSON lines (one object per log record) compatible
  with Render log drains, Datadog, Loki, etc.
- Local / test: emits human-readable text so tailing the terminal stays pleasant.

Usage
-----
Import and call ``configure_logging()`` once at app startup (``create_app``).
After that, all code should use the standard ``logging`` module::

    import logging
    logger = logging.getLogger(__name__)
    logger.info("message", extra={"user_id": str(user.id)})
"""

import json
import logging
import sys
from datetime import UTC, datetime


class _JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include any extra fields the caller attached via ``extra={}``.
        _STANDARD_ATTRS = frozenset(logging.LogRecord(
            "", 0, "", 0, "", (), None
        ).__dict__.keys()) | {"message", "asctime"}
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


class _TextFormatter(logging.Formatter):
    """Human-readable formatter for local development."""

    _FMT = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
    _DATEFMT = "%H:%M:%S"

    def __init__(self) -> None:
        super().__init__(fmt=self._FMT, datefmt=self._DATEFMT)


def configure_logging(level: str = "INFO", *, json_logs: bool = False) -> None:
    """Install application-wide logging handlers.

    Parameters
    ----------
    level:
        Minimum log level string, e.g. ``"INFO"`` or ``"DEBUG"``.
    json_logs:
        When *True*, emit JSON-formatted log lines (production).
        When *False*, emit human-readable text (local/test).
    """
    formatter: logging.Formatter = (
        _JSONFormatter() if json_logs else _TextFormatter()
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Silence noisy third-party loggers in production.
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
