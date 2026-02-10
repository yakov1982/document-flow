from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from lexima_dms.db.models import AuditLog, Notification, User


def audit(
    db: Session,
    *,
    actor: User,
    action: str,
    document_id: int | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    db.add(AuditLog(actor_user_id=actor.id, action=action, document_id=document_id, meta=meta))


def notify(db: Session, *, user_id: int, message: str, document_id: int | None = None) -> None:
    """Create internal notification for user."""
    db.add(Notification(user_id=user_id, message=message, document_id=document_id))

