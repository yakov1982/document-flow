from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from lexima_dms.api.deps import get_current_user, get_db
from lexima_dms.api.schemas import NotificationOut
from lexima_dms.db.models import Notification, User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/my", response_model=list[NotificationOut])
def my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    unread_only: bool = False,
    limit: int = Query(50, ge=1, le=200),
) -> list[NotificationOut]:
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))
    items = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return [NotificationOut.model_validate(n) for n in items]


@router.post("/{notification_id}/read")
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    n = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).one_or_none()
    if not n:
        return {"ok": False}
    from datetime import datetime, timezone
    n.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}
