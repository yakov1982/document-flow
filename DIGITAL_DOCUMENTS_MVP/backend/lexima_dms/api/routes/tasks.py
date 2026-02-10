from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from lexima_dms.api.deps import get_current_user, get_db
from lexima_dms.api.schemas import TaskItem
from lexima_dms.db.models import Document, DocumentStatus, User
from lexima_dms.services.workflow import actionable_step_for_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/my", response_model=list[TaskItem])
def my_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[TaskItem]:
    docs = (
        db.query(Document)
        .options(joinedload(Document.steps))
        .filter(Document.status == DocumentStatus.in_review)
        .order_by(Document.created_at.desc())
        .limit(200)
        .all()
    )
    out: list[TaskItem] = []
    for doc in docs:
        step = actionable_step_for_user(doc, current_user.id)
        if step:
            out.append(
                TaskItem(
                    document_id=doc.id,
                    title=doc.title,
                    step_id=step.id,
                    step_order=step.step_order,
                    state=step.state.value,
                    deadline=step.deadline,
                )
            )
    return out

