from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from lexima_dms.api.deps import get_current_user, get_db
from lexima_dms.api.schemas import DocumentListItem, DocumentOut
from lexima_dms.db.models import (
    ApprovalStep,
    Document,
    DocumentSignature,
    DocumentStatus,
    DocumentVersion,
    StepState,
    User,
)
from lexima_dms.services.audit import audit
from lexima_dms.services.workflow import actionable_step_for_user, recompute_document_status
from lexima_dms.storage.files import resolve_storage_path, save_version_file

router = APIRouter(prefix="/documents", tags=["documents"])


def _parse_approvers(raw: str) -> list[list[str]]:
    """Parse approvers: 'user1, user2|user3' = step1: [user1], step2: [user2, user3] (parallel)."""
    if not raw.strip():
        return []
    steps = []
    for part in raw.replace(";", ",").replace("\n", ",").split(","):
        usernames = [u.strip() for u in part.split("|") if u.strip()]
        if usernames:
            steps.append(usernames)
    return steps


@router.get("", response_model=list[DocumentListItem])
def list_documents(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
    q: str | None = None,
    status_filter: str | None = None,
    doc_type_filter: str | None = None,
    author_id: int | None = None,
    counterparty: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort: str = "created_at_desc",
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[DocumentListItem]:
    query = db.query(Document).options(joinedload(Document.created_by))
    if q:
        like = f"%{q}%"
        query = query.filter((Document.title.ilike(like)) | (Document.reg_number.ilike(like)))
    if status_filter:
        query = query.filter(Document.status == status_filter)
    if doc_type_filter:
        query = query.filter(Document.doc_type == doc_type_filter)
    if author_id:
        query = query.filter(Document.created_by_user_id == author_id)
    if counterparty:
        cp = f"%{counterparty}%"
        query = query.filter(
            (Document.counterparty_from.ilike(cp)) | (Document.counterparty_to.ilike(cp))
        )
    if date_from:
        try:
            df = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            query = query.filter(Document.created_at >= df)
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            query = query.filter(Document.created_at <= dt)
        except Exception:
            pass

    order_col = Document.created_at
    if "title" in sort:
        order_col = Document.title
    elif "status" in sort:
        order_col = Document.status
    if "asc" in sort:
        query = query.order_by(order_col.asc())
    else:
        query = query.order_by(order_col.desc())

    docs = query.offset(skip).limit(limit).all()
    return [DocumentListItem.model_validate(d) for d in docs]


@router.get("/export/csv")
def export_documents_csv(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
    q: str | None = None,
    status_filter: str | None = None,
) -> StreamingResponse:
    """Export document list as CSV."""
    query = db.query(Document).options(joinedload(Document.created_by))
    if q:
        like = f"%{q}%"
        query = query.filter((Document.title.ilike(like)) | (Document.reg_number.ilike(like)))
    if status_filter:
        query = query.filter(Document.status == status_filter)
    docs = query.order_by(Document.created_at.desc()).limit(1000).all()

    def stream():
        yield "id;title;doc_type;reg_number;status;created_at;author\n"
        for d in docs:
            author = d.created_by.username if d.created_by else ""
            row = f"{d.id};{d.title};{d.doc_type};{d.reg_number or ''};{d.status.value};{d.created_at};{author}\n"
            yield row

    return StreamingResponse(
        stream(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=documents.csv"},
    )


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def create_document(
    title: Annotated[str, Form()],
    doc_type: Annotated[str, Form()] = "generic",
    reg_number: Annotated[str | None, Form()] = None,
    document_date: Annotated[str | None, Form()] = None,
    counterparty_from: Annotated[str | None, Form()] = None,
    counterparty_to: Annotated[str | None, Form()] = None,
    approvers: Annotated[str, Form()] = "",
    file: Annotated[UploadFile | None, File()] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentOut:
    doc_date = None
    if document_date:
        try:
            doc_date = datetime.fromisoformat(document_date.replace("Z", "+00:00"))
        except Exception:
            pass
    doc = Document(
        title=title,
        doc_type=doc_type,
        reg_number=reg_number,
        status=DocumentStatus.draft,
        created_by_user_id=current_user.id,
        document_date=doc_date,
        counterparty_from=counterparty_from,
        counterparty_to=counterparty_to,
    )
    db.add(doc)
    db.flush()  # assign doc.id

    approver_steps = _parse_approvers(approvers)
    if approver_steps:
        for step_order, usernames in enumerate(approver_steps, start=1):
            for username in usernames:
                u = db.query(User).filter(User.username == username).one_or_none()
                if not u:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Approver '{username}' not found",
                    )
                db.add(
                    ApprovalStep(
                        document_id=doc.id,
                        step_order=step_order,
                        approver_user_id=u.id,
                        state=StepState.pending,
                    )
                )
        doc.status = DocumentStatus.in_review

    if file:
        storage_path, size = save_version_file(doc_id=doc.id, version=1, upload=file)
        db.add(
            DocumentVersion(
                document_id=doc.id,
                version=1,
                filename=file.filename or "file",
                content_type=file.content_type,
                size=size,
                storage_path=storage_path,
                uploaded_by_user_id=current_user.id,
            )
        )

    audit(db, actor=current_user, action="document.create", document_id=doc.id)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document with same (doc_type, reg_number) already exists",
        ) from e

    db.refresh(doc)
    return DocumentOut.model_validate(doc)


class DelegateIn(BaseModel):
    step_id: int
    to_username: str


@router.post("/{doc_id}/delegate", response_model=DocumentOut)
def delegate_step(
    doc_id: int,
    body: DelegateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentOut:
    """Делегировать шаг согласования другому пользователю."""
    doc = db.query(Document).options(joinedload(Document.steps)).filter(Document.id == doc_id).one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    step = actionable_step_for_user(doc, current_user.id)
    if not step or step.id != body.step_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delegate")
    to_user = db.query(User).filter(User.username == body.to_username).one_or_none()
    if not to_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    step.delegated_to_user_id = to_user.id
    audit(db, actor=current_user, action="document.step.delegate", document_id=doc.id, meta={"step_id": body.step_id, "to": body.to_username})
    db.commit()
    db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DocumentOut:
    doc = (
        db.query(Document)
        .options(
            joinedload(Document.versions),
            joinedload(Document.steps).joinedload(ApprovalStep.approver),
            joinedload(Document.steps).joinedload(ApprovalStep.delegated_to),
            joinedload(Document.signatures),
            joinedload(Document.assignments),
        )
        .filter(Document.id == doc_id)
        .one_or_none()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    result = DocumentOut.model_validate(doc)
    result.assignments = [
        {"id": a.id, "document_id": a.document_id, "assignee_user_id": a.assignee_user_id, "title": a.title, "deadline": a.deadline, "status": a.status, "created_at": a.created_at}
        for a in (doc.assignments or [])
    ]
    return result


@router.post("/{doc_id}/versions", response_model=DocumentOut)
def upload_new_version(
    doc_id: int,
    file: Annotated[UploadFile, File(...)],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentOut:
    doc = db.query(Document).filter(Document.id == doc_id).one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    last_version = (
        db.query(DocumentVersion.version)
        .filter(DocumentVersion.document_id == doc_id)
        .order_by(DocumentVersion.version.desc())
        .limit(1)
        .scalar()
    )
    next_version = int(last_version or 0) + 1

    storage_path, size = save_version_file(doc_id=doc.id, version=next_version, upload=file)
    db.add(
        DocumentVersion(
            document_id=doc.id,
            version=next_version,
            filename=file.filename or "file",
            content_type=file.content_type,
            size=size,
            storage_path=storage_path,
            uploaded_by_user_id=current_user.id,
        )
    )
    audit(db, actor=current_user, action="document.version.upload", document_id=doc.id, meta={"version": next_version})
    db.commit()
    db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.get("/{doc_id}/versions/{version_id}/download")
def download_version(
    doc_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    v = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.id == version_id, DocumentVersion.document_id == doc_id)
        .one_or_none()
    )
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    path = resolve_storage_path(v.storage_path)
    return FileResponse(path, filename=v.filename, media_type=v.content_type or "application/octet-stream")


@router.post("/{doc_id}/approve", response_model=DocumentOut)
def approve(
    doc_id: int,
    comment: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentOut:
    doc = db.query(Document).filter(Document.id == doc_id).one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    step = actionable_step_for_user(doc, current_user.id)
    if not step:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No actionable step for this user")

    step.state = StepState.approved
    step.comment = comment
    audit(db, actor=current_user, action="document.step.approve", document_id=doc.id, meta={"step_order": step.step_order})
    recompute_document_status(db, doc)
    db.commit()
    db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.post("/{doc_id}/reject", response_model=DocumentOut)
def reject(
    doc_id: int,
    comment: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentOut:
    doc = db.query(Document).filter(Document.id == doc_id).one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    step = actionable_step_for_user(doc, current_user.id)
    if not step:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No actionable step for this user")

    step.state = StepState.rejected
    step.comment = comment
    audit(db, actor=current_user, action="document.step.reject", document_id=doc.id, meta={"step_order": step.step_order})
    recompute_document_status(db, doc)
    db.commit()
    db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.post("/{doc_id}/sign", response_model=DocumentOut)
def sign_document(
    doc_id: int,
    cert_subject: Annotated[str | None, Form()] = None,
    cert_thumbprint: Annotated[str | None, Form()] = None,
    signature_file: Annotated[UploadFile | None, File()] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentOut:
    """ЭЦП: подписать документ. Опционально: сертификат (subject, thumbprint), файл подписи (PKCS#7)."""
    doc = db.query(Document).filter(Document.id == doc_id).one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    sig_data: bytes | None = None
    if signature_file:
        sig_data = signature_file.file.read()

    sig = DocumentSignature(
        document_id=doc.id,
        user_id=current_user.id,
        cert_subject=cert_subject,
        cert_thumbprint=cert_thumbprint,
        signature_data=sig_data,
    )
    db.add(sig)
    audit(db, actor=current_user, action="document.sign", document_id=doc.id)
    db.commit()
    db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.get("/{doc_id}/signatures/{sig_id}/download")
def download_signature(
    doc_id: int,
    sig_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Скачать файл подписи (PKCS#7) для проверки."""
    sig = (
        db.query(DocumentSignature)
        .filter(
            DocumentSignature.id == sig_id,
            DocumentSignature.document_id == doc_id,
        )
        .one_or_none()
    )
    if not sig or not sig.signature_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signature not found")
    from fastapi.responses import Response
    return Response(
        content=sig.signature_data,
        media_type="application/pkcs7-signature",
        headers={"Content-Disposition": f'attachment; filename="signature_{sig_id}.p7s"'},
    )
