"""
Conversation Tree & Presets Engine for MaxIM (Adapted from LibreChat architecture).
Provides DAG message branching, branch forking, session presets, and versioned artifacts.
Repository reference: https://github.com/LibreChat-AI/LibreChat
"""
import sqlite3
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from config import config

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

DEFAULT_PRESETS = [
    {
        "id": "preset_executive_assistant",
        "name": "Executive Personal Assistant",
        "description": "General daily executive guidance, task breakdown, memory indexing, and calendar/work tracking.",
        "model_alias": "primary",
        "temperature": 0.7,
        "system_prompt": "You are MaxIM, an executive personal assistant and intellectual partner. Guide work strategically with concrete next steps.",
        "toolsets": ["vault", "memory", "work_guide", "office", "todos"]
    },
    {
        "id": "preset_code_architect",
        "name": "Defensive Code Architect",
        "description": "Strict software engineering, zero speculative abstractions, rigorous test loops, and surgical refactorings.",
        "model_alias": "reasoning",
        "temperature": 0.2,
        "system_prompt": "You are a senior software architect. Implement robust, defensive, minimal solutions backed by verifiable tests.",
        "toolsets": ["vault", "memory", "os", "skills", "sandbox"]
    },
    {
        "id": "preset_video_analyst",
        "name": "Multimodal Video Analyst",
        "description": "Video frame extraction, timestamped meeting synthesis, on-screen slide/code parsing, and action item logs.",
        "model_alias": "primary",
        "temperature": 0.4,
        "system_prompt": "You are a video analysis specialist. Inspect recordings, extract visual keyframes, analyze audio/captions, and create actionable meeting notes.",
        "toolsets": ["vault", "memory", "video", "reach"]
    },
    {
        "id": "preset_financial_auditor",
        "name": "Office & Financial Auditor",
        "description": "Spreadsheet cell operations, formula verification, CSV ledger tracking, and Git-style revisions.",
        "model_alias": "fast",
        "temperature": 0.1,
        "system_prompt": "You are a precise data and financial auditor. Verify spreadsheet cells, calculate formulas with zero error, and validate balances.",
        "toolsets": ["vault", "office", "work_guide", "files"]
    }
]

class ConversationTreeEngine:
    def __init__(self, db_path: Optional[Path] = None, vault_dir: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self.vault_dir = vault_dir or config.vault_dir
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversation_branches (
                branch_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                name TEXT NOT NULL,
                parent_branch_id TEXT,
                fork_message_id INTEGER,
                is_active INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS message_tree_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                branch_id TEXT NOT NULL,
                parent_message_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                model TEXT,
                tool_calls TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (branch_id) REFERENCES conversation_branches(branch_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS conversation_presets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                model_alias TEXT NOT NULL,
                temperature REAL DEFAULT 0.7,
                system_prompt TEXT,
                toolsets TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS conversation_artifacts (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                branch_id TEXT NOT NULL,
                title TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                content TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            );
            """)

            # Seed default presets if empty
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM conversation_presets")
            if cursor.fetchone()[0] == 0:
                now = utc_now_iso()
                for p in DEFAULT_PRESETS:
                    cursor.execute("""
                    INSERT INTO conversation_presets (id, name, description, model_alias, temperature, system_prompt, toolsets, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        p["id"],
                        p["name"],
                        p["description"],
                        p["model_alias"],
                        p["temperature"],
                        p["system_prompt"],
                        json.dumps(p["toolsets"]),
                        now,
                        now
                    ))
                conn.commit()

    def get_or_create_main_branch(self, session_id: str) -> str:
        """Ensures a session has at least one active main branch."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT branch_id FROM conversation_branches WHERE session_id = ? AND is_active = 1", (session_id,))
            row = cursor.fetchone()
            if row:
                return row["branch_id"]
            
            # Check if any branch exists
            cursor.execute("SELECT branch_id FROM conversation_branches WHERE session_id = ?", (session_id,))
            any_row = cursor.fetchone()
            if any_row:
                b_id = any_row["branch_id"]
                cursor.execute("UPDATE conversation_branches SET is_active = 1 WHERE branch_id = ?", (b_id,))
                conn.commit()
                return b_id

            # Create default main branch
            branch_id = f"branch_main_{uuid.uuid4().hex[:8]}"
            cursor.execute("""
            INSERT INTO conversation_branches (branch_id, session_id, name, parent_branch_id, fork_message_id, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (branch_id, session_id, "Main Branch", None, None, utc_now_iso()))
            conn.commit()
            return branch_id

    def add_node(
        self,
        session_id: str,
        role: str,
        content: str,
        branch_id: Optional[str] = None,
        parent_message_id: Optional[int] = None,
        model: Optional[str] = None,
        tool_calls: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Appends a new turn node to the specified or active branch."""
        active_branch_id = branch_id or self.get_or_create_main_branch(session_id)
        
        # If parent_message_id is not explicitly provided, find the latest message in this branch
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if parent_message_id is None:
                cursor.execute(
                    "SELECT id FROM message_tree_nodes WHERE branch_id = ? ORDER BY id DESC LIMIT 1",
                    (active_branch_id,)
                )
                last_node = cursor.fetchone()
                if last_node:
                    parent_message_id = last_node["id"]
                else:
                    # Check if this branch is forked from another branch
                    cursor.execute("SELECT fork_message_id FROM conversation_branches WHERE branch_id = ?", (active_branch_id,))
                    fork_row = cursor.fetchone()
                    if fork_row and fork_row["fork_message_id"]:
                        parent_message_id = fork_row["fork_message_id"]

            tc_str = json.dumps(tool_calls) if tool_calls and not isinstance(tool_calls, str) else tool_calls
            now = utc_now_iso()

            cursor.execute("""
            INSERT INTO message_tree_nodes (session_id, branch_id, parent_message_id, role, content, model, tool_calls, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, active_branch_id, parent_message_id, role, content, model, tc_str, now))
            node_id = cursor.lastrowid
            conn.commit()

            return {
                "id": node_id,
                "session_id": session_id,
                "branch_id": active_branch_id,
                "parent_message_id": parent_message_id,
                "role": role,
                "content": content,
                "model": model,
                "tool_calls": tool_calls,
                "created_at": now
            }

    def fork_branch(self, session_id: str, fork_message_id: int, new_branch_name: str) -> Dict[str, Any]:
        """Forks a conversation from an existing message node into a new branch and activates it."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT branch_id FROM message_tree_nodes WHERE id = ?", (fork_message_id,))
            parent_node = cursor.fetchone()
            if not parent_node:
                raise ValueError(f"Message ID {fork_message_id} does not exist.")
            parent_branch_id = parent_node["branch_id"]

            # Deactivate current branches for this session
            cursor.execute("UPDATE conversation_branches SET is_active = 0 WHERE session_id = ?", (session_id,))

            new_branch_id = f"branch_{uuid.uuid4().hex[:8]}"
            now = utc_now_iso()
            cursor.execute("""
            INSERT INTO conversation_branches (branch_id, session_id, name, parent_branch_id, fork_message_id, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (new_branch_id, session_id, new_branch_name, parent_branch_id, fork_message_id, now))
            conn.commit()

            return {
                "branch_id": new_branch_id,
                "session_id": session_id,
                "name": new_branch_name,
                "parent_branch_id": parent_branch_id,
                "fork_message_id": fork_message_id,
                "is_active": True,
                "created_at": now
            }

    def switch_branch(self, session_id: str, branch_id: str) -> bool:
        """Sets the active branch for a conversation session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT branch_id FROM conversation_branches WHERE branch_id = ? AND session_id = ?", (branch_id, session_id))
            if not cursor.fetchone():
                return False
            cursor.execute("UPDATE conversation_branches SET is_active = 0 WHERE session_id = ?", (session_id,))
            cursor.execute("UPDATE conversation_branches SET is_active = 1 WHERE branch_id = ?", (branch_id,))
            conn.commit()
            return True

    def list_branches(self, session_id: str) -> List[Dict[str, Any]]:
        """Lists all branches in a session with metadata and message counts."""
        self.get_or_create_main_branch(session_id)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT b.branch_id, b.session_id, b.name, b.parent_branch_id, b.fork_message_id, b.is_active, b.created_at,
                   COUNT(m.id) as node_count
            FROM conversation_branches b
            LEFT JOIN message_tree_nodes m ON b.branch_id = m.branch_id
            WHERE b.session_id = ?
            GROUP BY b.branch_id
            ORDER BY b.created_at ASC
            """, (session_id,))
            rows = cursor.fetchall()
            return [
                {
                    "branch_id": r["branch_id"],
                    "session_id": r["session_id"],
                    "name": r["name"],
                    "parent_branch_id": r["parent_branch_id"],
                    "fork_message_id": r["fork_message_id"],
                    "is_active": bool(r["is_active"]),
                    "node_count": r["node_count"],
                    "created_at": r["created_at"]
                }
                for r in rows
            ]

    def get_branch_history(self, session_id: str, branch_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Reconstructs the full linear history from root up to the latest leaf in the specified branch.
        Walks backward through parent_message_id pointers or ancestor branches.
        """
        target_branch = branch_id or self.get_or_create_main_branch(session_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Fetch all nodes in this session to build an in-memory parent map
            cursor.execute("""
            SELECT id, session_id, branch_id, parent_message_id, role, content, model, tool_calls, created_at
            FROM message_tree_nodes
            WHERE session_id = ?
            ORDER BY id ASC
            """, (session_id,))
            all_nodes = {row["id"]: dict(row) for row in cursor.fetchall()}

            # Find the leaf node of target_branch
            cursor.execute("""
            SELECT id FROM message_tree_nodes
            WHERE branch_id = ?
            ORDER BY id DESC LIMIT 1
            """, (target_branch,))
            leaf_row = cursor.fetchone()
            
            if not leaf_row:
                # If target branch has no direct nodes yet, check if it's forked from a parent
                cursor.execute("SELECT fork_message_id FROM conversation_branches WHERE branch_id = ?", (target_branch,))
                fork_row = cursor.fetchone()
                if not fork_row or not fork_row["fork_message_id"]:
                    return []
                current_id = fork_row["fork_message_id"]
            else:
                current_id = leaf_row["id"]

            # Trace backwards to root
            lineage = []
            visited = set()
            while current_id and current_id in all_nodes and current_id not in visited:
                visited.add(current_id)
                node = all_nodes[current_id]
                lineage.append(node)
                current_id = node["parent_message_id"]

            lineage.reverse()
            return lineage

    def save_preset(
        self,
        preset_id: str,
        name: str,
        model_alias: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        toolsets: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates or updates a reusable operational preset."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = utc_now_iso()
            ts_str = json.dumps(toolsets or ["vault", "memory"])
            cursor.execute("""
            INSERT INTO conversation_presets (id, name, description, model_alias, temperature, system_prompt, toolsets, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                model_alias = excluded.model_alias,
                temperature = excluded.temperature,
                system_prompt = excluded.system_prompt,
                toolsets = excluded.toolsets,
                updated_at = excluded.updated_at
            """, (preset_id, name, description, model_alias, temperature, system_prompt, ts_str, now, now))
            conn.commit()
            return {
                "id": preset_id,
                "name": name,
                "description": description,
                "model_alias": model_alias,
                "temperature": temperature,
                "system_prompt": system_prompt,
                "toolsets": toolsets or ["vault", "memory"],
                "updated_at": now
            }

    def get_preset(self, preset_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversation_presets WHERE id = ?", (preset_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "model_alias": row["model_alias"],
                "temperature": row["temperature"],
                "system_prompt": row["system_prompt"],
                "toolsets": json.loads(row["toolsets"]) if row["toolsets"] else [],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }

    def list_presets(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversation_presets ORDER BY id ASC")
            return [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "description": r["description"],
                    "model_alias": r["model_alias"],
                    "temperature": r["temperature"],
                    "system_prompt": r["system_prompt"],
                    "toolsets": json.loads(r["toolsets"]) if r["toolsets"] else [],
                    "updated_at": r["updated_at"]
                }
                for r in cursor.fetchall()
            ]

    def save_artifact(
        self,
        session_id: str,
        branch_id: str,
        title: str,
        artifact_type: str,
        content: str
    ) -> Dict[str, Any]:
        """Saves a versioned code or document artifact tied to the conversation branch and syncs to vault."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Calculate next version
            cursor.execute("""
            SELECT MAX(version) FROM conversation_artifacts
            WHERE session_id = ? AND title = ?
            """, (session_id, title))
            max_v = cursor.fetchone()[0]
            version = (max_v or 0) + 1
            
            artifact_id = f"art_{uuid.uuid4().hex[:8]}"
            now = utc_now_iso()
            cursor.execute("""
            INSERT INTO conversation_artifacts (id, session_id, branch_id, title, artifact_type, content, version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (artifact_id, session_id, branch_id, title, artifact_type, content, version, now))
            conn.commit()

            # Sync to vault/02 - Knowledge/Artifacts/
            try:
                art_dir = self.vault_dir / "02 - Knowledge" / "Artifacts"
                art_dir.mkdir(parents=True, exist_ok=True)
                clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip()
                art_path = art_dir / f"{clean_title}_v{version}.md"
                md_content = f"# {title} (Version {version})\n\n"
                md_content += f"> **Session:** `{session_id}` | **Branch:** `{branch_id}` | **Type:** `{artifact_type}`\n"
                md_content += f"> **Generated:** `{now}`\n\n"
                if artifact_type == "code":
                    md_content += f"```python\n{content}\n```\n"
                else:
                    md_content += f"{content}\n"
                art_path.write_text(md_content, encoding="utf-8")
            except Exception:
                pass

            return {
                "id": artifact_id,
                "session_id": session_id,
                "branch_id": branch_id,
                "title": title,
                "artifact_type": artifact_type,
                "version": version,
                "created_at": now
            }

    def list_artifacts(self, session_id: str, branch_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if branch_id:
                cursor.execute("""
                SELECT * FROM conversation_artifacts
                WHERE session_id = ? AND branch_id = ?
                ORDER BY version DESC, created_at DESC
                """, (session_id, branch_id))
            else:
                cursor.execute("""
                SELECT * FROM conversation_artifacts
                WHERE session_id = ?
                ORDER BY title ASC, version DESC
                """, (session_id,))
            return [dict(r) for r in cursor.fetchall()]

# Singleton instance
conversation_tree = ConversationTreeEngine()
