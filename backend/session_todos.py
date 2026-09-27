"""
Durable Session Goals & Todo Ledger Engine for MaxIM.
Inspired by OpenHuman (tinyhumansai/openhuman).

Maintains a structured, persistent state machine of sub-goals and todo checklist items
per conversational session. Injects live progress into ReAct system prompts to prevent
context drift during complex multi-step reasoning.
"""

import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from pydantic import BaseModel, Field

from config import config

logger = logging.getLogger("maxim.session_todos")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionTodo(BaseModel):
    id: Optional[int] = None
    session_id: str
    task_description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    step_order: int = 1
    result_summary: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class SessionTodoManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    task_description TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    step_order INTEGER NOT NULL DEFAULT 1,
                    result_summary TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_todos_session ON session_todos(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_todos_status ON session_todos(status)")

    def add_todo(self, session_id: str, task_description: str, step_order: Optional[int] = None) -> SessionTodo:
        now = utc_now_iso()
        with self._get_connection() as conn:
            if step_order is None:
                cursor = conn.execute("SELECT MAX(step_order) as max_ord FROM session_todos WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                step_order = (row["max_ord"] + 1) if row and row["max_ord"] is not None else 1

            cursor = conn.execute("""
                INSERT INTO session_todos (session_id, task_description, status, step_order, created_at, updated_at)
                VALUES (?, ?, 'pending', ?, ?, ?)
            """, (session_id, task_description.strip(), step_order, now, now))
            todo_id = cursor.lastrowid

        return SessionTodo(
            id=todo_id,
            session_id=session_id,
            task_description=task_description.strip(),
            status="pending",
            step_order=step_order,
            created_at=now,
            updated_at=now,
        )

    def update_todo(self, todo_id: int, status: str, result_summary: Optional[str] = None) -> Optional[SessionTodo]:
        valid_statuses = ["pending", "in_progress", "completed", "failed"]
        clean_status = status.lower().strip()
        if clean_status not in valid_statuses:
            clean_status = "in_progress"

        now = utc_now_iso()
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE session_todos
                SET status = ?, result_summary = COALESCE(?, result_summary), updated_at = ?
                WHERE id = ?
            """, (clean_status, result_summary, now, todo_id))

            cursor = conn.execute("SELECT * FROM session_todos WHERE id = ?", (todo_id,))
            row = cursor.fetchone()
            if row:
                return SessionTodo(**dict(row))
        return None

    def list_todos(self, session_id: str, status: Optional[str] = None) -> List[SessionTodo]:
        with self._get_connection() as conn:
            query = "SELECT * FROM session_todos WHERE session_id = ?"
            params: List[Any] = [session_id]
            if status:
                query += " AND status = ?"
                params.append(status.lower().strip())
            query += " ORDER BY step_order ASC, id ASC"

            cursor = conn.execute(query, params)
            return [SessionTodo(**dict(r)) for r in cursor.fetchall()]

    def delete_todo(self, todo_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM session_todos WHERE id = ?", (todo_id,))
            return cursor.rowcount > 0

    def clear_session_todos(self, session_id: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM session_todos WHERE session_id = ?", (session_id,))
            return cursor.rowcount

    def format_todos_context(self, session_id: str) -> str:
        """Renders session goals and todos into a concise checklist for ReAct prompt injection."""
        todos = self.list_todos(session_id)
        if not todos:
            return ""

        status_symbols = {
            "completed": "[x]",
            "in_progress": "[/]",
            "pending": "[ ]",
            "failed": "[!]",
        }

        lines = ["### Active Session Goals & Task Checklist:"]
        for t in todos:
            sym = status_symbols.get(t.status, "[ ]")
            summary_part = f" — {t.result_summary}" if t.result_summary else ""
            lines.append(f"{sym} {t.step_order}. {t.task_description} ({t.status}){summary_part}")

        return "\n".join(lines)


# Singleton instance
session_todos = SessionTodoManager()
