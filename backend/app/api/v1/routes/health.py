"""Enhanced health check endpoint.

Returns basic service metadata plus a live database connectivity check.
Render uses ``/api/v1/health`` as its health check path; a non-200 response
causes Render to restart the dyno.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    """Return service health including a live database ping.

    Response shape::

        {
            "status": "ok",
            "version": "0.1.0",
            "environment": "production",
            "db": "ok"
        }

    ``db`` will be ``"error"`` (and status ``"degraded"``) when the database is
    unreachable, while still returning HTTP 200 so Render does not thrash the
    dyno on transient DB hiccups.  Alert on ``db != "ok"`` in your monitoring.
    """
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check DB ping failed")
        db_status = "error"

    overall = "ok" if db_status == "ok" else "degraded"

    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "db": db_status,
    }
