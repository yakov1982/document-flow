"""Simple migrations for schema updates."""

from __future__ import annotations

from sqlalchemy import text

from lexima_dms.db.session import get_engine


def migrate() -> None:
    engine = get_engine()
    with engine.connect() as conn:
        _add_document_columns(conn)
        try:
            _add_approval_step_columns(conn)
        except Exception:
            pass
        try:
            _migrate_approval_steps_constraint(conn)
        except Exception:
            pass
        conn.commit()
    _create_new_tables(engine)


def _add_document_columns(conn) -> None:
    for col, col_type in [
        ("document_date", "DATETIME"),
        ("counterparty_from", "VARCHAR(255)"),
        ("counterparty_to", "VARCHAR(255)"),
        ("custom_attributes", "JSON"),
    ]:
        try:
            conn.execute(text(f"ALTER TABLE documents ADD COLUMN {col} {col_type}"))
        except Exception:
            pass


def _add_approval_step_columns(conn) -> None:
    for col, col_type in [
        ("delegated_to_user_id", "INTEGER"),
        ("deadline", "DATETIME"),
    ]:
        try:
            conn.execute(text(f"ALTER TABLE approval_steps ADD COLUMN {col} {col_type}"))
        except Exception:
            pass


def _migrate_approval_steps_constraint(conn) -> None:
    """Recreate approval_steps to allow parallel (multiple approvers per step_order)."""
    try:
        conn.execute(text("SELECT 1 FROM approval_steps LIMIT 1"))
    except Exception:
        return
    conn.execute(text("ALTER TABLE approval_steps RENAME TO approval_steps_old"))
    conn.execute(text("""
        CREATE TABLE approval_steps (
            id INTEGER PRIMARY KEY,
            document_id INTEGER NOT NULL,
            step_order INTEGER NOT NULL,
            approver_user_id INTEGER NOT NULL,
            delegated_to_user_id INTEGER,
            state VARCHAR(32) NOT NULL DEFAULT 'pending',
            comment TEXT,
            acted_at DATETIME,
            deadline DATETIME,
            FOREIGN KEY (document_id) REFERENCES documents(id),
            FOREIGN KEY (approver_user_id) REFERENCES users(id),
            FOREIGN KEY (delegated_to_user_id) REFERENCES users(id),
            UNIQUE (document_id, step_order, approver_user_id)
        )
    """))
    conn.execute(text("""
        INSERT INTO approval_steps (id, document_id, step_order, approver_user_id, state, comment, acted_at)
        SELECT id, document_id, step_order, approver_user_id, state, comment, acted_at FROM approval_steps_old
    """))
    conn.execute(text("DROP TABLE approval_steps_old"))


def _create_new_tables(engine) -> None:
    from lexima_dms.db.models import Base

    Base.metadata.create_all(bind=engine, checkfirst=True)
