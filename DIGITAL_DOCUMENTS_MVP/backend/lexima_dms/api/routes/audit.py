from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from lexima_dms.api.deps import get_current_user, get_db
from lexima_dms.api.schemas import AuditLogItem
from lexima_dms.db.models import AuditLog, User
from sqlalchemy.orm import Session, joinedload

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogItem])
def list_audit_log(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
    document_id: int | None = None,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
) -> list[AuditLogItem]:
    query = db.query(AuditLog).options(joinedload(AuditLog.actor))
    if document_id:
        query = query.filter(AuditLog.document_id == document_id)
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return [
        AuditLogItem(
            id=l.id,
            created_at=l.created_at,
            actor_username=l.actor.username if l.actor else None,
            action=l.action,
            document_id=l.document_id,
            meta=l.meta,
        )
        for l in logs
    ]
