from __future__ import annotations

from sqlalchemy.orm import Session

from lexima_dms.db.models import ApprovalStep, Document, DocumentStatus, StepState


def _effective_approver(step: ApprovalStep) -> int:
    """User ID of who can act (delegated_to or approver)."""
    return step.delegated_to_user_id if step.delegated_to_user_id else step.approver_user_id


def actionable_step(document: Document) -> ApprovalStep | None:
    """
    Returns the step that is currently actionable (first pending step
    with all previous steps approved). For parallel: all steps at same
    step_order must be approved before next. Supports delegation.
    """
    steps = sorted(document.steps, key=lambda s: (s.step_order, s.id))
    step_orders = sorted({s.step_order for s in steps})
    for order in step_orders:
        order_steps = [s for s in steps if s.step_order == order]
        if any(s.state == StepState.rejected for s in order_steps):
            return None
        if not all(s.state == StepState.approved for s in order_steps):
            for s in order_steps:
                if s.state == StepState.pending:
                    return s
            return None
    return None


def actionable_step_for_user(document: Document, user_id: int) -> ApprovalStep | None:
    """Return actionable step if the given user can act on it."""
    step = actionable_step(document)
    if step and _effective_approver(step) == user_id:
        return step
    return None


def recompute_document_status(db: Session, document: Document) -> None:
    steps = sorted(document.steps, key=lambda s: (s.step_order, s.id))
    if not steps:
        document.status = DocumentStatus.draft
        return

    if any(s.state == StepState.rejected for s in steps):
        document.status = DocumentStatus.rejected
        return

    if all(s.state == StepState.approved for s in steps):
        document.status = DocumentStatus.approved
        return

    document.status = DocumentStatus.in_review

