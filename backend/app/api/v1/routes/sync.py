from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.sync import SyncPullResponse, SyncPushRequest
from app.services.sync_service import SyncService

router = APIRouter(prefix="/sync", tags=["sync"])

@router.get("/pull", response_model=SyncPullResponse)
def pull_changes(
    last_pulled_at: Annotated[Optional[datetime], Query(alias="lastPulledAt")] = None,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> SyncPullResponse:
    """Pull database modifications since last sync."""
    service = SyncService(db)
    result = service.pull_changes(user_id=user.id, last_pulled_at=last_pulled_at)
    return SyncPullResponse(
        changes=result["changes"],
        timestamp=result["timestamp"]
    )

@router.post("/push", status_code=status.HTTP_200_OK)
def push_changes(
    payload: SyncPushRequest,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> dict[str, str]:
    """Push mobile database changes to backend."""
    service = SyncService(db)
    return service.push_changes(user_id=user.id, request=payload)
