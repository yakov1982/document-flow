from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    admin = "admin"
    author = "author"
    approver = "approver"
    viewer = "viewer"


class DocumentStatus(str, enum.Enum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"


class StepState(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    skipped = "skipped"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.author, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    doc_type: Mapped[str] = mapped_column(String(64), default="generic", index=True)
    reg_number: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.draft, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    document_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    counterparty_from: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    counterparty_to: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    custom_attributes: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped[User] = relationship("User")

    versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version.desc()",
    )
    steps: Mapped[list["ApprovalStep"]] = relationship(
        "ApprovalStep",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="ApprovalStep.step_order.asc()",
    )
    signatures: Mapped[list["DocumentSignature"]] = relationship(
        "DocumentSignature",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentSignature.signed_at.desc()",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("doc_type", "reg_number", name="uq_doc_type_reg_number"),)


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String(1024))

    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    uploaded_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    uploaded_by: Mapped[User] = relationship("User")

    document: Mapped[Document] = relationship("Document", back_populates="versions")

    __table_args__ = (UniqueConstraint("document_id", "version", name="uq_doc_version"),)


class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    step_order: Mapped[int] = mapped_column(Integer, index=True)
    approver_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    delegated_to_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    state: Mapped[StepState] = mapped_column(Enum(StepState), default=StepState.pending, index=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    acted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped[Document] = relationship("Document", back_populates="steps")
    approver: Mapped[User] = relationship("User", foreign_keys=[approver_user_id])
    delegated_to: Mapped[User | None] = relationship("User", foreign_keys=[delegated_to_user_id])

    __table_args__ = (UniqueConstraint("document_id", "step_order", "approver_user_id", name="uq_doc_step_approver"),)


class DocumentSignature(Base):
    """ЭЦП: подпись документа."""

    __tablename__ = "document_signatures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    cert_subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cert_thumbprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    signature_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="signatures")
    user: Mapped[User] = relationship("User")


class Assignment(Base):
    """Поручение по документу."""

    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    assignee_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)  # pending, in_progress, done
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    document: Mapped["Document"] = relationship("Document", back_populates="assignments")
    assignee: Mapped[User] = relationship("User", foreign_keys=[assignee_user_id])
    created_by: Mapped[User] = relationship("User", foreign_keys=[created_by_user_id])


class Notification(Base):
    """Внутреннее уведомление."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    message: Mapped[str] = mapped_column(String(512))
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship("User")


class NumberingRule(Base):
    """Правило автонумерации по типу документа."""

    __tablename__ = "numbering_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doc_type: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    prefix: Mapped[str] = mapped_column(String(32), default="")
    next_number: Mapped[int] = mapped_column(Integer, default=1)


class SavedFilter(Base):
    """Сохранённый фильтр пользователя."""

    __tablename__ = "saved_filters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    filter_data: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    actor: Mapped[User] = relationship("User")

    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

