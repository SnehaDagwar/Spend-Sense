"""Exports API route handlers.

All endpoints require a valid JWT access token and return downloadable attachments.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import ReportFilters
from app.services.export import ExportService
from app.api.v1.routes.reports import _parse_report_filters


router = APIRouter(prefix="/exports", tags=["exports"])


# ---------------------------------------------------------------------------
# Route Handlers
# ---------------------------------------------------------------------------

@router.get("/csv")
def export_csv(
    filters: Annotated[ReportFilters, Depends(_parse_report_filters)],
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> StreamingResponse:
    """Stream user financial history as a standard CSV attachment."""
    service = ExportService(db)
    csv_gen = service.export_csv_stream(user_id=user.id, filters=filters)
    
    filename = f"spend_sense_export_{date.today().isoformat()}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    
    return StreamingResponse(
        csv_gen,
        media_type="text/csv",
        headers=headers,
    )


@router.get("/xlsx")
def export_xlsx(
    filters: Annotated[ReportFilters, Depends(_parse_report_filters)],
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> Response:
    """Download user financial history as a beautifully styled Excel workbook."""
    service = ExportService(db)
    xlsx_io = service.export_xlsx(user_id=user.id, filters=filters)
    
    filename = f"spend_sense_export_{date.today().isoformat()}.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    
    return Response(
        content=xlsx_io.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/json")
def export_json(
    filters: Annotated[ReportFilters, Depends(_parse_report_filters)],
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> StreamingResponse:
    """Stream user financial history as a validated JSON array attachment."""
    service = ExportService(db)
    json_gen = service.export_json_stream(user_id=user.id, filters=filters)
    
    filename = f"spend_sense_export_{date.today().isoformat()}.json"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    
    return StreamingResponse(
        json_gen,
        media_type="application/json",
        headers=headers,
    )
