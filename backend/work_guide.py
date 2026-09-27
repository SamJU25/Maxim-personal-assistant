"""
Executive Work Guidance & Task Director for MaxIM.
Provides proactive goal decomposition, next-action guidance, and LifeOS milestone execution.

Features:
1. Work Projects, Milestones, and Action Checklist stored in SQLite WAL.
2. Intelligent Goal Decomposer (breaks objectives into sequential, actionable steps).
3. Context-Aware Next Action Advisor (coordinates foreground tasks with active goals).
4. Automated Progress Progression & Completion Tracking.
5. Executive Work Briefs & Obsidian Vault Sync (Work_Tracker.md).
"""
import uuid
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field

from config import config

logger = logging.getLogger("maxim.work_guide")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# =============================================================================
# DATA MODELS
# =============================================================================

class WorkAction(BaseModel):
    id: str
    milestone_id: str
    action_text: str
    status: str = "pending"  # "pending", "in_progress", "completed", "skipped"
    suggested_tool: Optional[str] = None
    result_summary: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)

class WorkMilestone(BaseModel):
    id: str
    project_id: str
    title: str
    description: Optional[str] = None
    status: str = "pending"  # "pending", "in_progress", "completed"
    order_idx: int = 0
    actions: List[WorkAction] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)

class WorkProject(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    category: str = "general"  # "coding", "research", "finance", "organization", "general"
    status: str = "active"  # "active", "completed", "paused"
    milestones: List[WorkMilestone] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)

# =============================================================================
# WORK GUIDE ENGINE
# =============================================================================

class WorkGuideEngine:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Creates SQLite WAL tables for projects, milestones, and actions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS work_projects (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT DEFAULT 'general',
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS work_milestones (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    order_idx INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES work_projects(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS work_actions (
                    id TEXT PRIMARY KEY,
                    milestone_id TEXT NOT NULL,
                    action_text TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    suggested_tool TEXT,
                    result_summary TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (milestone_id) REFERENCES work_milestones(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_work_milestones_proj ON work_milestones(project_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_work_actions_ms ON work_actions(milestone_id)")
            conn.commit()

    # -------------------------------------------------------------------------
    # GOAL DECOMPOSITION
    # -------------------------------------------------------------------------

    def decompose_goal(
        self,
        goal: str,
        category: str = "general",
        description: Optional[str] = None,
    ) -> WorkProject:
        """
        Decomposes a broad user work goal into a structured project with sequential milestones and actions.
        """
        proj_id = f"proj_{uuid.uuid4().hex[:8]}"
        now = utc_now_iso()

        # Heuristic / deterministic decomposition logic
        milestone_specs = self._generate_milestones_for_goal(goal, category)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO work_projects (id, title, description, category, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'active', ?, ?)
            """, (proj_id, goal, description or f"Work project for: {goal}", category, now, now))

            project_milestones: List[WorkMilestone] = []
            for m_idx, m_spec in enumerate(milestone_specs):
                m_id = f"ms_{uuid.uuid4().hex[:8]}"
                cursor.execute("""
                    INSERT INTO work_milestones (id, project_id, title, description, status, order_idx, created_at)
                    VALUES (?, ?, ?, ?, 'pending', ?, ?)
                """, (m_id, proj_id, m_spec["title"], m_spec.get("description", ""), m_idx, now))

                ms_actions: List[WorkAction] = []
                for a_spec in m_spec.get("actions", []):
                    a_id = f"act_{uuid.uuid4().hex[:8]}"
                    cursor.execute("""
                        INSERT INTO work_actions (id, milestone_id, action_text, status, suggested_tool, created_at, updated_at)
                        VALUES (?, ?, ?, 'pending', ?, ?, ?)
                    """, (a_id, m_id, a_spec["text"], a_spec.get("tool"), now, now))

                    ms_actions.append(WorkAction(
                        id=a_id,
                        milestone_id=m_id,
                        action_text=a_spec["text"],
                        status="pending",
                        suggested_tool=a_spec.get("tool"),
                        created_at=now,
                        updated_at=now,
                    ))

                project_milestones.append(WorkMilestone(
                    id=m_id,
                    project_id=proj_id,
                    title=m_spec["title"],
                    description=m_spec.get("description"),
                    status="pending",
                    order_idx=m_idx,
                    actions=ms_actions,
                    created_at=now,
                ))

            conn.commit()

        return WorkProject(
            id=proj_id,
            title=goal,
            description=description,
            category=category,
            status="active",
            milestones=project_milestones,
            created_at=now,
            updated_at=now,
        )

    def _generate_milestones_for_goal(self, goal: str, category: str) -> List[Dict[str, Any]]:
        """Synthesizes structured milestones and action items tailored to the objective."""
        g_lower = goal.lower()

        # 1. Organization & Files
        if any(k in g_lower for k in ["download", "organize", "file", "folder", "sort", "cleanup"]):
            return [
                {
                    "title": "Directory Discovery & Analysis",
                    "description": "Scan target workspace or downloads to identify clutter and categories",
                    "actions": [
                        {"text": "Scan directory and categorize files", "tool": "scan_directory"},
                        {"text": "Preview organization changes without touching disk", "tool": "organize_directory"},
                    ]
                },
                {
                    "title": "Execution & Verification",
                    "description": "Move files into structured directories and verify integrity",
                    "actions": [
                        {"text": "Execute organization into structured folders", "tool": "organize_directory"},
                        {"text": "Verify clean state and record receipts", "tool": "read_vault_note"},
                    ]
                }
            ]

        # 2. Spreadsheet / Finance / Data
        if any(k in g_lower for k in ["sheet", "excel", "csv", "finance", "budget", "data", "report", "table"]):
            return [
                {
                    "title": "Data Setup & Ingestion",
                    "description": "Initialize workbook and import tabular records",
                    "actions": [
                        {"text": "Create structured spreadsheet workbook", "tool": "office_create_workbook"},
                        {"text": "Populate rows or import CSV data", "tool": "office_edit_cells"},
                    ]
                },
                {
                    "title": "Computation & Metrics",
                    "description": "Apply analytical formulas and calculate totals",
                    "actions": [
                        {"text": "Calculate totals and averages via formulas", "tool": "office_edit_cells"},
                        {"text": "Verify computed values and preview changes", "tool": "office_read_sheet"},
                    ]
                },
                {
                    "title": "Summary & Reporting",
                    "description": "Export structured Markdown table to Obsidian vault",
                    "actions": [
                        {"text": "Export Markdown table to Obsidian vault note", "tool": "office_export_markdown"},
                    ]
                }
            ]

        # 3. Research & Internet
        if any(k in g_lower for k in ["research", "investigate", "web", "github", "look into", "competitor"]):
            return [
                {
                    "title": "Information Gathering",
                    "description": "Query online sources and inspect documentation",
                    "actions": [
                        {"text": "Execute multi-engine web search", "tool": "web_search"},
                        {"text": "Extract Markdown summaries from relevant pages", "tool": "read_web_page"},
                    ]
                },
                {
                    "title": "Synthesis & Archival",
                    "description": "Condense findings into permanent knowledge notes",
                    "actions": [
                        {"text": "Synthesize key insights and record in Obsidian vault", "tool": "write_vault_note"},
                    ]
                }
            ]

        # Default multi-stage plan
        return [
            {
                "title": "Scoping & Context Review",
                "description": "Assess requirements, constraints, and resources",
                "actions": [
                    {"text": "Review project context and LifeOS TELOS targets", "tool": "get_telos_profile"},
                    {"text": "Inspect desktop environment and relevant files", "tool": "inspect_screen"},
                ]
            },
            {
                "title": "Implementation & Action",
                "description": "Execute core tasks and milestones",
                "actions": [
                    {"text": "Execute primary task actions", "tool": "create_subagent"},
                ]
            },
            {
                "title": "Review & Verification",
                "description": "Audit outputs and document outcomes",
                "actions": [
                    {"text": "Verify results and record completion report", "tool": "write_vault_note"},
                ]
            }
        ]

    # -------------------------------------------------------------------------
    # NEXT-ACTION RECOMMENDATION
    # -------------------------------------------------------------------------

    def get_next_recommended_action(self) -> Dict[str, Any]:
        """
        Retrieves the single highest-priority pending action across active projects.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    a.id as action_id,
                    a.action_text,
                    a.suggested_tool,
                    a.status as action_status,
                    m.id as milestone_id,
                    m.title as milestone_title,
                    p.id as project_id,
                    p.title as project_title,
                    p.category
                FROM work_actions a
                JOIN work_milestones m ON a.milestone_id = m.id
                JOIN work_projects p ON m.project_id = p.id
                WHERE p.status = 'active' AND a.status IN ('pending', 'in_progress')
                ORDER BY m.order_idx ASC, a.rowid ASC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if not row:
                return {
                    "has_action": False,
                    "message": "All current project actions are completed. Ready for your next objective.",
                }

            return {
                "has_action": True,
                "project_id": row["project_id"],
                "project_title": row["project_title"],
                "category": row["category"],
                "milestone_id": row["milestone_id"],
                "milestone_title": row["milestone_title"],
                "action_id": row["action_id"],
                "action_text": row["action_text"],
                "suggested_tool": row["suggested_tool"],
                "status": row["action_status"],
            }

    # -------------------------------------------------------------------------
    # STATUS & COMPLETION MANAGEMENT
    # -------------------------------------------------------------------------

    def update_action_status(
        self,
        action_id: str,
        status: str,  # "completed", "in_progress", "pending", "skipped"
        result_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Updates an action's status. Automatically cascades completion up to milestones and projects.
        """
        now = utc_now_iso()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE work_actions SET status = ?, result_summary = ?, updated_at = ?
                WHERE id = ?
            """, (status, result_summary, now, action_id))

            # Find milestone
            cursor.execute("SELECT milestone_id FROM work_actions WHERE id = ?", (action_id,))
            m_row = cursor.fetchone()
            if not m_row:
                return {"status": "not_found", "action_id": action_id}
            m_id = m_row["milestone_id"]

            # Check if all actions in this milestone are done
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status IN ('completed', 'skipped') THEN 1 ELSE 0 END) as done
                FROM work_actions WHERE milestone_id = ?
            """, (m_id,))
            stat = cursor.fetchone()
            ms_completed = stat["total"] > 0 and stat["total"] == stat["done"]
            if ms_completed:
                cursor.execute("UPDATE work_milestones SET status = 'completed' WHERE id = ?", (m_id,))
            elif status == "in_progress":
                cursor.execute("UPDATE work_milestones SET status = 'in_progress' WHERE id = ?", (m_id,))

            # Find project
            cursor.execute("SELECT project_id FROM work_milestones WHERE id = ?", (m_id,))
            p_row = cursor.fetchone()
            p_id = p_row["project_id"] if p_row else None
            proj_completed = False

            if p_id:
                cursor.execute("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as done
                    FROM work_milestones WHERE project_id = ?
                """, (p_id,))
                p_stat = cursor.fetchone()
                proj_completed = p_stat["total"] > 0 and p_stat["total"] == p_stat["done"]
                if proj_completed:
                    cursor.execute("UPDATE work_projects SET status = 'completed', updated_at = ? WHERE id = ?", (now, p_id))
                else:
                    cursor.execute("UPDATE work_projects SET updated_at = ? WHERE id = ?", (now, p_id))

            conn.commit()

        return {
            "status": "updated",
            "action_id": action_id,
            "action_status": status,
            "milestone_completed": ms_completed,
            "project_completed": proj_completed,
        }

    def list_projects(self, status: Optional[str] = None) -> List[WorkProject]:
        """Lists projects with their nested milestones and actions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM work_projects WHERE status = ? ORDER BY updated_at DESC", (status,))
            else:
                cursor.execute("SELECT * FROM work_projects ORDER BY updated_at DESC")
            p_rows = cursor.fetchall()

            projects = []
            for p_row in p_rows:
                p_id = p_row["id"]
                cursor.execute("SELECT * FROM work_milestones WHERE project_id = ? ORDER BY order_idx ASC", (p_id,))
                m_rows = cursor.fetchall()

                milestones = []
                for m_row in m_rows:
                    m_id = m_row["id"]
                    cursor.execute("SELECT * FROM work_actions WHERE milestone_id = ? ORDER BY rowid ASC", (m_id,))
                    a_rows = cursor.fetchall()
                    actions = [WorkAction(**dict(a)) for a in a_rows]
                    milestones.append(WorkMilestone(**dict(m_row), actions=actions))

                projects.append(WorkProject(**dict(p_row), milestones=milestones))
            return projects

    def sync_work_to_vault(self) -> Path:
        """Exports active projects and next actions to Obsidian vault."""
        projects = self.list_projects(status="active")
        now = utc_now_iso()

        lines = [
            "# MaxIM Executive Work Tracker",
            f"*Updated automatically at {now}*",
            "",
            "## Active Projects",
        ]

        if not projects:
            lines.append("No active projects. All tasks completed.")
        else:
            for p in projects:
                lines.append(f"### 🎯 {p.title} (`{p.category}`)")
                if p.description:
                    lines.append(f"> {p.description}")
                lines.append("")
                for m in p.milestones:
                    m_icon = "✅" if m.status == "completed" else ("🔄" if m.status == "in_progress" else "⏳")
                    lines.append(f"#### {m_icon} Milestone: {m.title}")
                    for a in m.actions:
                        check = "[x]" if a.status in ("completed", "skipped") else "[ ]"
                        tool_hint = f" *(tool: `{a.suggested_tool}`)*" if a.suggested_tool else ""
                        lines.append(f"- {check} {a.action_text}{tool_hint}")
                    lines.append("")

        note_path = config.vault_dir / "00 - LifeOS" / "Work_Tracker.md"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Synchronized Work Tracker to vault: {note_path}")
        return note_path

# Global singleton
work_guide = WorkGuideEngine()
