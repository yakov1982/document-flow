from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    created_at: datetime


class DocumentVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: int
    filename: str
    content_type: str | None
    size: int
    uploaded_at: datetime
    uploaded_by_user_id: int


class ApprovalStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    step_order: int
    approver_user_id: int
    state: str
    comment: str | None
    acted_at: datetime | None


class DocumentSignatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    signed_at: datetime
    cert_subject: str | None
    cert_thumbprint: str | None
    has_detached_signature: bool = False

    @model_validator(mode="wrap")
    @classmethod
    def set_has_detached(cls, data: object, handler: object) -> "DocumentSignatureOut":
        if hasattr(data, "signature_data"):
            return handler(
                {
                    "id": data.id,
                    "user_id": data.user_id,
                    "signed_at": data.signed_at,
                    "cert_subject": data.cert_subject,
                    "cert_thumbprint": data.cert_thumbprint,
                    "has_detached_signature": bool(data.signature_data),
                }
            )
        return handler(data)


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    doc_type: str
    reg_number: str | None
    status: str
    created_at: datetime
    created_by_user_id: int
    versions: list[DocumentVersionOut] = []
    steps: list[ApprovalStepOut] = []
    signatures: list[DocumentSignatureOut] = []


class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    doc_type: str
    reg_number: str | None
    status: str
    created_at: datetime


class TaskItem(BaseModel):
    document_id: int
    title: str
    step_id: int
    step_order: int
    state: str
    meta: dict[str, Any] | None = None

