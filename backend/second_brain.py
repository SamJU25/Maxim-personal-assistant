"""
ZhiGui UI Second Brain & Autonomous Learning Loop Engine for MaxIM.
Repository reference: https://github.com/CarlWangChina/zhigui-openclaw-ui-second-brain-skill

Functional Core:
1. Autonomous Skill Crystallization: Extracts reusable multi-step recipes from successful workflows.
2. Obsidian Vault Synchronization: Generates clean markdown notes in `vault/02 - Skills/` with MOC links.
3. Reflexion & Anti-Pattern Defense: Ingests errors, logs root causes, and creates corrective memory rules so MaxIM never repeats mistakes.
4. Dynamic Skill Recaller & Step Dispatcher: Matches user goals to crystallized skills and executes sequenced steps.
5. Persistent SQLite WAL Tables: `learned_skills` and `error_reflexions`.
"""
import re
import json
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from pydantic import BaseModel, Field

from config import config

logger = logging.getLogger("maxim.second_brain")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SkillStep(BaseModel):
    tool: str
    args: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None
    expected_output_contains: Optional[str] = None


class LearnedSkill(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    trigger_keywords: List[str] = Field(default_factory=list)
    preconditions: Optional[str] = None
    steps: List[SkillStep] = Field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    vault_path: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class ErrorReflexion(BaseModel):
    id: Optional[int] = None
    timestamp: str = Field(default_factory=utc_now_iso)
    session_id: str = "default_session"
    failed_tool: str
    error_message: str
    root_cause: str
    corrective_rule: str


FOUNDATIONAL_SKILLS: List[Dict[str, Any]] = [
    {
        "name": "sqlite_wal_checkpoint",
        "description": "Performs an explicit PRAGMA wal_checkpoint(TRUNCATE) on the local SQLite database to prevent WAL file bloat.",
        "trigger_keywords": ["checkpoint", "wal", "truncate wal", "vacuum db"],
        "preconditions": "maxim.db exists and is not locked",
        "steps": [
            {
                "tool": "get_hardware_status",
                "args": {},
                "description": "Verify host system resources prior to checkpoint",
            }
        ],
    },
    {
        "name": "active_window_context_audit",
        "description": "Performs a full perception audit combining active window title, process name, and hardware load.",
        "trigger_keywords": ["window audit", "active app", "screen context", "check app"],
        "preconditions": "Desktop session active",
        "steps": [
            {
                "tool": "os_list_windows",
                "args": {"visible_only": True},
                "description": "Inspect open top-level windows",
            },
            {
                "tool": "get_hardware_status",
                "args": {},
                "description": "Capture hardware telemetry during inspection",
            }
        ],
    },
    {
        "name": "daily_intel_synthesis",
        "description": "Coordinates overnight intelligence scout with active TELOS objectives to generate daily briefing.",
        "trigger_keywords": ["daily briefing", "morning intel", "synthesize scout", "scout summary"],
        "preconditions": "Network access available",
        "steps": [
            {
                "tool": "get_overnight_intel",
                "args": {},
                "description": "Fetch latest overnight intelligence report",
            },
            {
                "tool": "read_vault_note",
                "args": {"title": "00 - LifeOS/TELOS"},
                "description": "Check current TELOS targets for alignment",
            }
        ],
    },
]


class SecondBrainEngine:
    """Manages skill crystallization, Obsidian vault notes, and error reflexion loops."""

    def __init__(self, db_path: Optional[Path] = None, vault_skills_dir: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self.skills_dir = vault_skills_dir or (config.vault_dir / "02 - Skills")
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._seed_foundational_skills()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initializes SQLite WAL tables for skills and reflexions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learned_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    trigger_keywords TEXT,
                    preconditions TEXT,
                    steps_json TEXT NOT NULL,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    vault_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_reflexions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    failed_tool TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    root_cause TEXT NOT NULL,
                    corrective_rule TEXT NOT NULL
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_learned_skills_name ON learned_skills(name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_reflexions_time ON error_reflexions(timestamp);")
            conn.commit()

    def _seed_foundational_skills(self):
        """Seeds default multi-step action recipes if not already present."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for s in FOUNDATIONAL_SKILLS:
                cursor.execute("SELECT id FROM learned_skills WHERE name = ?", (s["name"],))
                if not cursor.fetchone():
                    now = utc_now_iso()
                    kw_str = json.dumps(s.get("trigger_keywords", []))
                    steps_str = json.dumps(s.get("steps", []))
                    cursor.execute("""
                        INSERT INTO learned_skills (
                            name, description, trigger_keywords, preconditions, steps_json,
                            success_count, failure_count, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 1, 0, ?, ?)
                    """, (s["name"], s["description"], kw_str, s.get("preconditions", ""), steps_str, now, now))
            conn.commit()

    # =========================================================================
    # 1. SKILL CRYSTALLIZATION & RECALL
    # =========================================================================

    def crystallize_skill(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        trigger_keywords: Optional[List[str]] = None,
        preconditions: Optional[str] = None,
        sync_vault: bool = True,
    ) -> LearnedSkill:
        """
        Crystallizes a validated workflow into a reusable skill.
        Persists to SQLite and writes a structured Markdown note to Obsidian vault.
        """
        clean_name = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_").lower()
        now = utc_now_iso()
        kw_list = trigger_keywords or [clean_name]
        steps_objs = [SkillStep(**st) if isinstance(st, dict) else st for st in steps]
        steps_json = json.dumps([s.model_dump() for s in steps_objs])
        kw_json = json.dumps(kw_list)

        vault_file_path = None
        if sync_vault:
            vault_file_path = self._write_skill_to_vault(
                name=clean_name,
                description=description,
                trigger_keywords=kw_list,
                preconditions=preconditions or "",
                steps=steps_objs,
            )

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO learned_skills (
                    name, description, trigger_keywords, preconditions, steps_json,
                    success_count, failure_count, vault_path, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 1, 0, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    description = excluded.description,
                    trigger_keywords = excluded.trigger_keywords,
                    preconditions = excluded.preconditions,
                    steps_json = excluded.steps_json,
                    vault_path = excluded.vault_path,
                    updated_at = excluded.updated_at
            """, (clean_name, description, kw_json, preconditions, steps_json, str(vault_file_path) if vault_file_path else None, now, now))
            conn.commit()

        return self.get_skill(clean_name)

    def get_skill(self, name_or_id: Any) -> Optional[LearnedSkill]:
        """Retrieves skill by name or primary ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if isinstance(name_or_id, int) or (isinstance(name_or_id, str) and name_or_id.isdigit()):
                cursor.execute("SELECT * FROM learned_skills WHERE id = ?", (int(name_or_id),))
            else:
                cursor.execute("SELECT * FROM learned_skills WHERE name = ?", (str(name_or_id).lower().strip(),))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_skill(row)

    def list_skills(self, limit: int = 50) -> List[LearnedSkill]:
        """Returns all registered skills sorted by success count."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM learned_skills ORDER BY success_count DESC, id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [self._row_to_skill(r) for r in rows]

    def recall_skill(self, query: str) -> List[LearnedSkill]:
        """Searches learned skills by query against name, description, and trigger keywords."""
        q = query.lower().strip()
        all_skills = self.list_skills(limit=100)
        matched = []
        for s in all_skills:
            if q in s.name.lower() or q in s.description.lower():
                matched.append(s)
                continue
            for kw in s.trigger_keywords:
                if q in kw.lower() or kw.lower() in q:
                    matched.append(s)
                    break
        return matched

    def record_skill_execution(self, name: str, success: bool):
        """Updates success/failure counter for a skill."""
        now = utc_now_iso()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if success:
                cursor.execute("""
                    UPDATE learned_skills SET success_count = success_count + 1, updated_at = ? WHERE name = ?
                """, (now, name))
            else:
                cursor.execute("""
                    UPDATE learned_skills SET failure_count = failure_count + 1, updated_at = ? WHERE name = ?
                """, (now, name))
            conn.commit()

    def _row_to_skill(self, row: sqlite3.Row) -> LearnedSkill:
        steps_raw = json.loads(row["steps_json"]) if row["steps_json"] else []
        steps = [SkillStep(**st) for st in steps_raw]
        kw_raw = json.loads(row["trigger_keywords"]) if row["trigger_keywords"] else []
        return LearnedSkill(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            trigger_keywords=kw_raw,
            preconditions=row["preconditions"],
            steps=steps,
            success_count=row["success_count"],
            failure_count=row["failure_count"],
            vault_path=row["vault_path"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # =========================================================================
    # 2. OBSIDIAN VAULT SYNCHRONIZATION
    # =========================================================================

    def _write_skill_to_vault(
        self,
        name: str,
        description: str,
        trigger_keywords: List[str],
        preconditions: str,
        steps: List[SkillStep],
    ) -> Path:
        """Writes or updates skill markdown note in vault/02 - Skills/."""
        title_case = " ".join(word.capitalize() for word in name.replace("_", " ").split())
        file_path = self.skills_dir / f"{title_case}.md"

        steps_lines = []
        for i, st in enumerate(steps, start=1):
            desc = f" — {st.description}" if st.description else ""
            args_formatted = json.dumps(st.args)
            steps_lines.append(f"{i}. **`{st.tool}`**{desc}\n   - Parameters: `{args_formatted}`")

        content = f"""---
title: "{title_case}"
type: skill
category: second-brain
tags:
  - "#skill"
  - "#second-brain"
  - "#automation"
triggers: {json.dumps(trigger_keywords)}
updated_at: "{utc_now_iso()}"
---

# {title_case}

> **Description:** {description}  
> **Source:** MaxIM ZhiGui Autonomous Learning Loop  
> **Preconditions:** {preconditions or 'None'}  
> **Index Link:** [[Skills MOC]]

---

## Operational Steps

{"\n".join(steps_lines)}

---

## Trigger Keywords
{", ".join(f"`{k}`" for k in trigger_keywords)}

## Context Notes
- Auto-crystallized by MaxIM Second Brain Engine.
- Call via tool `execute_learned_skill(skill_name="{name}")`.
"""
        file_path.write_text(content.strip(), encoding="utf-8")
        return file_path

    def sync_skills_moc(self) -> Path:
        """Generates or updates the Master Map of Content [[Skills MOC]] in vault/02 - Skills/."""
        skills = self.list_skills(limit=100)
        moc_path = self.skills_dir / "Skills MOC.md"

        items = []
        for s in skills:
            title_case = " ".join(word.capitalize() for word in s.name.replace("_", " ").split())
            items.append(f"- [[{title_case}]] — *{s.description}* (Success: {s.success_count}x)")

        content = f"""---
title: "Skills Map of Content"
type: moc
tags:
  - "#moc"
  - "#skills"
  - "#second-brain"
updated_at: "{utc_now_iso()}"
---

# MaxIM Skills Map of Content (MOC)

> Autonomous skill registry and execution recipes crystallized by MaxIM Second Brain.

---

## Active Learned Skills ({len(skills)})

{"\n".join(items) if items else "- No skills crystallized yet."}

---
*Maintained automatically by `backend/second_brain.py`.*
"""
        moc_path.write_text(content.strip(), encoding="utf-8")
        return moc_path

    # =========================================================================
    # 3. REFLEXION & ANTI-PATTERN DEFENSE
    # =========================================================================

    def record_error_reflexion(
        self,
        failed_tool: str,
        error_message: str,
        root_cause: str,
        corrective_rule: str,
        session_id: str = "default_session",
    ) -> ErrorReflexion:
        """
        Registers an execution failure and creates a persistent corrective rule
        so MaxIM does not repeat the mistake.
        """
        now = utc_now_iso()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO error_reflexions (
                    timestamp, session_id, failed_tool, error_message, root_cause, corrective_rule
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (now, session_id, failed_tool, error_message, root_cause, corrective_rule))
            conn.commit()
            row_id = cursor.lastrowid

        return ErrorReflexion(
            id=row_id,
            timestamp=now,
            session_id=session_id,
            failed_tool=failed_tool,
            error_message=error_message,
            root_cause=root_cause,
            corrective_rule=corrective_rule,
        )

    def list_reflexions(self, limit: int = 30) -> List[ErrorReflexion]:
        """Retrieves recent error reflexion corrective rules."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM error_reflexions ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [
                ErrorReflexion(
                    id=r["id"],
                    timestamp=r["timestamp"],
                    session_id=r["session_id"],
                    failed_tool=r["failed_tool"],
                    error_message=r["error_message"],
                    root_cause=r["root_cause"],
                    corrective_rule=r["corrective_rule"],
                )
                for r in rows
            ]

    def get_prompt_context_injection(self, limit: int = 5) -> str:
        """
        Returns active anti-pattern corrective rules to inject into the system prompt.
        """
        rules = self.list_reflexions(limit=limit)
        if not rules:
            return ""

        rule_bullets = [
            f"- **Rule when calling `{r.failed_tool}`**: {r.corrective_rule} *(avoid: {r.error_message[:60]})*"
            for r in rules
        ]
        return (
            "### ZhiGui Reflexion & Anti-Pattern Defense (Never Repeat These Mistakes):\n"
            + "\n".join(rule_bullets)
        )


# Global singleton
second_brain_engine = SecondBrainEngine()
