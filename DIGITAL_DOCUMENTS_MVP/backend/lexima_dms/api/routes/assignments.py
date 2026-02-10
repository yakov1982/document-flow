from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from lexima_dms.api.deps import get_current_user, get_db
from lexima_dms.api.schemas import AssignmentOut
from lexima_dms.db.models import Assignment, Document, User

router = APIRouter(prefix="/assignments", tags=["assignments"])


class CreateAssignmentIn(BaseModel):
    document_id: int
    assignee_username: str
    title: str
    deadline: str | None = None


@router.post("", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def create_assignment(
    body: CreateAssignmentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssignmentOut:
    doc = db.query(Document).filter(Document.id == body.document_id).one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    assignee = db.query(User).filter(User.username == body.assignee_username).one_or_none()
    if not assignee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    dl = None
    if body.deadline:
        try:
            dl = datetime.fromisoformat(body.deadline.replace("Z", "+00:00"))
        except Exception:
            pass
    a = Assignment(
        document_id=body.document_id,
        assignee_user_id=assignee.id,
        created_by_user_id=current_user.id,
        title=body.title,
        deadline=dl,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return AssignmentOut.model_validate(a)


@router.get("/my", response_model=list[AssignmentOut])
def my_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AssignmentOut]:
    items = db.query(Assignment).filter(Assignment.assignee_user_id == current_user.id).all()
    return [AssignmentOut.model_validate(a) for a in items]


class UpdateAssignmentIn(BaseModel):
    status: str = "done"


@router.patch("/{assignment_id}", response_model=AssignmentOut)
def update_assignment_status(
    assignment_id: int,
    body: UpdateAssignmentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssignmentOut:
    a = db.query(Assignment).filter(Assignment.id == assignment_id).one_or_none()
    if not a or a.assignee_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    a.status = body.status
    db.commit()
    db.refresh(a)
    return AssignmentOut.model_validate(a)
