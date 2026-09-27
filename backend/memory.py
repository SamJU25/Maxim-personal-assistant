"""
SQLite Memory Tree for MaxIM (Inspired by OpenHuman architecture).
Provides persistent local storage for conversation sessions, turns, and learned facts.
Uses SQLite WAL mode for high concurrency and crash resilience.
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from contextlib import contextmanager
from config import config

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class MessageRecord(BaseModel):
    id: Optional[int] = None
    session_id: str
    role: str  # user, assistant, system, tool
    content: str
    tool_calls: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)

class MemoryFact(BaseModel):
    id: Optional[int] = None
    category: str  # preference, habit, project, rule
    key: str
    value: str
    source_session: Optional[str] = None
    updated_at: str = Field(default_factory=utc_now_iso)

class SQLiteMemoryStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA busy_timeout=30000;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA cache_size=-64000;")
        conn.execute("PRAGMA temp_store=MEMORY;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initializes tables for sessions, messages, and continuous memory facts."""
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS memory_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                source_session TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS execution_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                tool_name TEXT NOT NULL,
                arguments TEXT NOT NULL,
                result TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id);
            CREATE INDEX IF NOT EXISTS idx_receipts_session ON execution_receipts(session_id, id);
            CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC);

            CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                item_id UNINDEXED,
                item_type,
                title,
                content,
                tags,
                tokenize = 'porter unicode61'
            );
            """)

    # FTS5 Indexing & Search
    def index_fts(self, item_id: str, item_type: str, title: str, content: str, tags: str = "") -> None:
        """Indexes or re-indexes an item in the FTS5 virtual table."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "DELETE FROM memory_fts WHERE item_id = ? AND item_type = ?",
                    (str(item_id), item_type)
                )
                conn.execute(
                    "INSERT INTO memory_fts (item_id, item_type, title, content, tags) VALUES (?, ?, ?, ?, ?)",
                    (str(item_id), item_type, title, content, tags)
                )
        except Exception:
            pass

    def search_fts(
        self,
        query: str,
        item_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Executes a BM25 ranked full-text search across memory facts, messages, receipts, and vault notes.
        Defensively handles special characters and syntax.
        """
        if not query or not query.strip():
            return []

        # Sanitize query terms for FTS5
        clean_tokens = [w.replace('"', '').strip() for w in query.split() if w.replace('"', '').strip()]
        if not clean_tokens:
            return []

        # Formulate MATCH query with prefix matching
        match_query = " OR ".join(f'"{token}"*' for token in clean_tokens)

        with self._get_connection() as conn:
            try:
                if item_types:
                    placeholders = ",".join("?" for _ in item_types)
                    sql = f"""
                    SELECT item_id, item_type, title, content, tags, rank
                    FROM memory_fts
                    WHERE memory_fts MATCH ? AND item_type IN ({placeholders})
                    ORDER BY rank
                    LIMIT ?
                    """
                    params = [match_query] + list(item_types) + [limit]
                else:
                    sql = """
                    SELECT item_id, item_type, title, content, tags, rank
                    FROM memory_fts
                    WHERE memory_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """
                    params = [match_query, limit]

                rows = conn.execute(sql, params).fetchall()
                return [dict(r) for r in rows]
            except sqlite3.OperationalError:
                # Fallback to direct token match if complex match fails
                fallback_sql = """
                SELECT item_id, item_type, title, content, tags, 0.0 as rank
                FROM memory_fts
                WHERE content LIKE ? OR title LIKE ?
                LIMIT ?
                """
                like_term = f"%{clean_tokens[0]}%"
                rows = conn.execute(fallback_sql, (like_term, like_term, limit)).fetchall()
                return [dict(r) for r in rows]

    # Session Operations
    def create_session(self, session_id: str, title: str = "New Conversation") -> str:
        now = utc_now_iso()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, title, now, now)
            )
        return session_id

    def list_sessions(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()
            return [dict(r) for r in rows]

    # Message Turn Operations
    def add_message(self, message: MessageRecord) -> int:
        now = utc_now_iso()
        with self._get_connection() as conn:
            # Ensure session exists
            conn.execute(
                "INSERT OR IGNORE INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (message.session_id, "Active Session", now, now)
            )
            cursor = conn.execute(
                "INSERT INTO messages (session_id, role, content, tool_calls, created_at) VALUES (?, ?, ?, ?, ?)",
                (message.session_id, message.role, message.content, message.tool_calls, message.created_at)
            )
            msg_id = cursor.lastrowid
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, message.session_id))

        # Index in FTS5
        self.index_fts(
            item_id=str(msg_id),
            item_type="message",
            title=f"Session {message.session_id} [{message.role}]",
            content=message.content,
            tags=message.role,
        )
        return msg_id

    def get_messages(self, session_id: str, limit: int = 50) -> List[MessageRecord]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM (
                    SELECT * FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?
                ) ORDER BY id ASC
                """,
                (session_id, limit)
            ).fetchall()
            return [MessageRecord(**dict(r)) for r in rows]

    def prune_messages(self, session_id: str, keep_last: int = 6) -> int:
        """
        Prunes earlier conversational turns for a session to prevent context degradation,
        while preserving the most recent `keep_last` turns.
        Returns the number of pruned messages.
        """
        with self._get_connection() as conn:
            all_ids = [
                r["id"] for r in conn.execute(
                    "SELECT id FROM messages WHERE session_id = ? ORDER BY id ASC",
                    (session_id,)
                ).fetchall()
            ]
            if len(all_ids) <= keep_last:
                return 0

            prune_ids = all_ids[:-keep_last]
            placeholders = ",".join("?" for _ in prune_ids)
            conn.execute(f"DELETE FROM messages WHERE id IN ({placeholders})", prune_ids)
            return len(prune_ids)

    def get_frequent_user_directives(self, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieves user directives/prompts based on daily usage frequency and recency.
        Deduplicates prompts and ignores very short or trivial inputs.
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT trim(content) as content, COUNT(*) as usage_count, MAX(created_at) as last_used
                FROM messages
                WHERE role = 'user' AND length(trim(content)) > 3
                GROUP BY trim(content)
                ORDER BY usage_count DESC, last_used DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()
            return [
                {
                    "content": r["content"],
                    "usage_count": r["usage_count"],
                    "last_used": r["last_used"],
                }
                for r in rows
            ]

    # Continuous Learning / Fact Storage
    def remember_fact(self, category: str, key: str, value: str, session_id: Optional[str] = None) -> None:
        now = utc_now_iso()
        clean_key = key.strip().lower()
        clean_val = value.strip()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO memory_facts (category, key, value, source_session, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    category=excluded.category,
                    value=excluded.value,
                    updated_at=excluded.updated_at
                """,
                (category, clean_key, clean_val, session_id, now)
            )

        # Index in FTS5
        self.index_fts(
            item_id=clean_key,
            item_type="fact",
            title=f"Fact: {clean_key} ({category})",
            content=clean_val,
            tags=category,
        )

    def get_facts(self, category: Optional[str] = None) -> List[MemoryFact]:
        with self._get_connection() as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM memory_facts WHERE category = ? ORDER BY updated_at DESC", (category,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM memory_facts ORDER BY updated_at DESC").fetchall()
            return [MemoryFact(**dict(r)) for r in rows]

    # Execution Receipts (Meta Muse evidence pattern)
    def log_receipt(self, tool_name: str, arguments: Dict[str, Any], result: str, session_id: Optional[str] = None) -> int:
        now = utc_now_iso()
        args_str = json.dumps(arguments)
        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO execution_receipts (session_id, tool_name, arguments, result, timestamp) VALUES (?, ?, ?, ?, ?)",
                (session_id, tool_name, args_str, result, now)
            )
            receipt_id = cursor.lastrowid

        # Index in FTS5
        self.index_fts(
            item_id=str(receipt_id),
            item_type="receipt",
            title=f"Receipt: {tool_name}",
            content=f"Arguments: {args_str} | Output: {result}",
            tags=tool_name,
        )
        return receipt_id

    def get_receipts(self, session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            if session_id:
                rows = conn.execute(
                    "SELECT * FROM execution_receipts WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                    (session_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM execution_receipts ORDER BY id DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

# Singleton instance
memory_store = SQLiteMemoryStore()

