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
    approver_username: str | None = None
    delegated_to_user_id: int | None = None
    delegated_to_username: str | None = None
    state: str
    comment: str | None
    acted_at: datetime | None
    deadline: datetime | None

    @model_validator(mode="wrap")
    @classmethod
    def add_usernames(cls, data: object, handler: object) -> "ApprovalStepOut":
        if hasattr(data, "approver"):
            d = {
                "id": data.id,
                "step_order": data.step_order,
                "approver_user_id": data.approver_user_id,
                "approver_username": data.approver.username if data.approver else None,
                "delegated_to_user_id": getattr(data, "delegated_to_user_id", None),
                "delegated_to_username": data.delegated_to.username if getattr(data, "delegated_to", None) else None,
                "state": data.state.value if hasattr(data.state, "value") else data.state,
                "comment": data.comment,
                "acted_at": data.acted_at,
                "deadline": getattr(data, "deadline", None),
            }
            return handler(d)
        return handler(data)


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
    document_date: datetime | None = None
    counterparty_from: str | None = None
    counterparty_to: str | None = None
    custom_attributes: dict[str, Any] | None = None
    created_by_user_id: int
    versions: list[DocumentVersionOut] = []
    steps: list[ApprovalStepOut] = []
    signatures: list[DocumentSignatureOut] = []
    assignments: list[dict[str, Any]] = []


class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    doc_type: str
    reg_number: str | None
    status: str
    created_at: datetime
    created_by_username: str | None = None

    @model_validator(mode="wrap")
    @classmethod
    def add_author(cls, data: object, handler: object) -> "DocumentListItem":
        if hasattr(data, "created_by") and data.created_by:
            d = {**{k: getattr(data, k) for k in ["id", "title", "doc_type", "reg_number", "status", "created_at"]}, "created_by_username": data.created_by.username}
            return handler(d)
        return handler(data)


class TaskItem(BaseModel):
    document_id: int
    title: str
    step_id: int
    step_order: int
    state: str
    deadline: datetime | None = None
    meta: dict[str, Any] | None = None


class AuditLogItem(BaseModel):
    id: int
    created_at: datetime
    actor_username: str | None = None
    action: str
    document_id: int | None
    meta: dict[str, Any] | None = None


class AssignmentOut(BaseModel):
    id: int
    document_id: int
    assignee_user_id: int
    title: str
    deadline: datetime | None
    status: str
    created_at: datetime


class NotificationOut(BaseModel):
    id: int
    message: str
    document_id: int | None
    read_at: datetime | None
    created_at: datetime

