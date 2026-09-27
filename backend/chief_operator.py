"""
LobeHub-Inspired Chief Agent Operator & Multi-Agent Collaboration Engine for MaxIM.
Repository reference: https://github.com/lobehub/lobehub

Enhanced with:
- AgenticSkills.io 16-Category Dynamic Taxonomy Integration.
- Skill-to-Agent Binding: Agents equipped with specialized skills from the 731-skill catalog.
- Domain Group Channels: Specialized Messenger-style channels (Marketing, Web Dev, QA, Security, etc.).
- MaxIM Master Conductor: Autonomous dispatching, cross-group handoffs, and Obsidian vault reporting.
"""
import asyncio
import json
import logging
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from config import config
from memory import memory_store
from router import model_router
from tools.vault_tool import vault_synapse

logger = logging.getLogger("maxim.operator")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def get_skills_prompt_context(skill_ids: List[str]) -> str:
    """Loads skill descriptions and guidance from the dynamic catalog."""
    if not skill_ids:
        return ""
    
    catalog_path = Path("f:/MAXIM V2/.agents/plugins/claude-skills/catalog.json")
    if not catalog_path.exists():
        return ""
    
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except Exception:
        return ""
        
    snippets = []
    for sid in skill_ids:
        item = catalog.get(sid)
        if not item:
            for k, v in catalog.items():
                if k.lower() == sid.lower() or k.replace("-", "") == sid.replace("-", ""):
                    item = v
                    break
        if item:
            name = item.get("name", sid)
            desc = item.get("description", "")
            snippets.append(f"- Skill [{sid}] ({name}): {desc}")
    
    if snippets:
        return "Your Assigned Specialized Skills & Playbooks:\n" + "\n".join(snippets) + "\n\n"
    return ""

class AgentMember(BaseModel):
    id: str = Field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:8]}")
    name: str = Field(..., description="Display name of the agent")
    role: str = Field(..., description="Specialty role or function")
    persona: str = Field(..., description="Core personality and operating directives")
    avatar: str = Field(default="Sparkles", description="Icon or avatar identifier")
    toolsets: List[str] = Field(default_factory=lambda: ["vault"], description="Assigned toolsets: vault, reach, cua, memory, perception")
    skills: List[str] = Field(default_factory=list, description="Assigned skills from catalog (e.g. copywriting, claude-seo)")
    category: Optional[str] = Field(default=None, description="Primary domain category (e.g. marketing, web-development, etc.)")
    provider: Optional[str] = Field(default=None, description="Dedicated model provider override")
    model: Optional[str] = Field(default=None, description="Dedicated model name override")
    status: str = Field(default="idle", description="Current status: idle, active, scheduled")
    hired_at: str = Field(default_factory=utc_now_iso)
    total_tasks: int = Field(default=0)

class AgentCollaborationGroup(BaseModel):
    id: str = Field(default_factory=lambda: f"group_{uuid.uuid4().hex[:8]}")
    name: str = Field(..., description="Group name")
    description: str = Field(..., description="Objective or charter of the group")
    member_ids: List[str] = Field(default_factory=list, description="IDs of member agents")
    category: Optional[str] = Field(default=None, description="Domain category matching the 16 AgenticSkills categories")
    topic: Optional[str] = Field(default=None, description="Current discussion topic")
    created_at: str = Field(default_factory=utc_now_iso)

class ShiftReport(BaseModel):
    id: str = Field(default_factory=lambda: f"shift_{uuid.uuid4().hex[:8]}")
    agent_id: str
    agent_name: str
    task: str
    status: str = "completed"
    summary: str
    timestamp: str = Field(default_factory=utc_now_iso)
    evidence_receipts: List[Dict[str, Any]] = Field(default_factory=list)

class ChiefAgentOperator:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self._init_tables()
        self._seed_default_team()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_tables(self):
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS operator_team (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                persona TEXT NOT NULL,
                avatar TEXT NOT NULL,
                toolsets TEXT NOT NULL,
                skills TEXT DEFAULT '[]',
                category TEXT,
                provider TEXT,
                model TEXT,
                status TEXT NOT NULL,
                hired_at TEXT NOT NULL,
                total_tasks INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS operator_groups (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                member_ids TEXT NOT NULL,
                category TEXT,
                topic TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS operator_group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                sender_id TEXT NOT NULL,
                sender_name TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (group_id) REFERENCES operator_groups(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS operator_reports (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                task TEXT NOT NULL,
                status TEXT NOT NULL,
                summary TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                evidence_receipts TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_group_messages_gid ON operator_group_messages(group_id, id);
            CREATE INDEX IF NOT EXISTS idx_operator_reports_agent ON operator_reports(agent_id);
            CREATE INDEX IF NOT EXISTS idx_operator_reports_time ON operator_reports(timestamp DESC);
            """)

            # Safe migrations for existing SQLite databases
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(operator_team)")
            team_cols = [r["name"] for r in cur.fetchall()]
            if "skills" not in team_cols:
                conn.execute("ALTER TABLE operator_team ADD COLUMN skills TEXT DEFAULT '[]';")
            if "category" not in team_cols:
                conn.execute("ALTER TABLE operator_team ADD COLUMN category TEXT;")

            cur.execute("PRAGMA table_info(operator_groups)")
            group_cols = [r["name"] for r in cur.fetchall()]
            if "category" not in group_cols:
                conn.execute("ALTER TABLE operator_groups ADD COLUMN category TEXT;")

    def _seed_default_team(self):
        """Seeds default high-synergy agent roster and categorized domain channels if empty."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM operator_team")
            count = cur.fetchone()[0]
            
            defaults = [
                AgentMember(
                    id="agent_chief",
                    name="MaxIM Chief Operator",
                    role="Chief Agent Operator & Executive Conductor",
                    persona="Master coordinator, team supervisor, intent engineer, and system orchestrator.",
                    avatar="Sparkles",
                    toolsets=["all"],
                    skills=["project-orchestrator", "executing-plans"],
                    category="agents",
                ),
                AgentMember(
                    id="agent_hermes",
                    name="Hermes Archaeologist",
                    role="Obsidian Vault & Knowledge Specialist",
                    persona="Obsidian vault synapse navigator, wikilink connector, and deep knowledge graph specialist.",
                    avatar="BookOpen",
                    toolsets=["vault"],
                    skills=["notion-knowledge-capture", "doc-coauthoring"],
                    category="documents",
                ),
                AgentMember(
                    id="agent_reach",
                    name="Agent Reach Navigator",
                    role="Universal Web & Internet Gateway",
                    persona="Internet scout specializing in Jina Reader clean markdown extraction, DuckDuckGo web search, and GitHub inspection.",
                    avatar="Globe",
                    toolsets=["reach"],
                    skills=["deep-research", "firecrawl-cli"],
                    category="productivity",
                ),
                AgentMember(
                    id="agent_bitterbot",
                    name="Bitterbot Critic",
                    role="Sarcastic Code Reviewer & Auditor",
                    persona="Relentless pragmatist, reality checker, demand receipts, zero-hallucination code reviewer.",
                    avatar="Zap",
                    toolsets=["vault", "perception"],
                    skills=["systematic-debugging", "code-review"],
                    category="testing",
                ),
                AgentMember(
                    id="agent_zylos",
                    name="Zylos Memory Curator",
                    role="Memory Architect & Context Safeguard",
                    persona="Five-layer inside-out memory curator, SQLite FTS5 indexer, and 75% safeguard compaction engine.",
                    avatar="Database",
                    toolsets=["memory", "vault"],
                    skills=["planning-with-files", "using-superpowers"],
                    category="agents",
                ),
                AgentMember(
                    id="agent_copywriter",
                    name="Conversion Copywriter",
                    role="High-Impact Copywriting & Editorial Specialist",
                    persona="Audience-first copywriter, craft compelling hooks, sales narrative, anti-slop humanized messaging.",
                    avatar="Feather",
                    toolsets=["vault"],
                    skills=["copywriting", "humanizer", "beautiful-prose"],
                    category="marketing",
                ),
                AgentMember(
                    id="agent_growth",
                    name="Growth & SEO Specialist",
                    role="Search Engine & Conversion Rate Optimizer",
                    persona="Data-backed SEO strategist, keyword density auditor, CRO specialist, and GEO/AEO researcher.",
                    avatar="TrendingUp",
                    toolsets=["reach"],
                    skills=["claude-seo", "page-cro", "marketing-skills"],
                    category="seo",
                ),
                AgentMember(
                    id="agent_social",
                    name="Social Media Strategist",
                    role="Content Distribution & Viral Campaign Architect",
                    persona="Campaign launch designer, short-form viral hook specialist, multi-platform audience engagement lead.",
                    avatar="Share2",
                    toolsets=["vault"],
                    skills=["social-media-skills", "launch-strategy"],
                    category="marketing",
                ),
                AgentMember(
                    id="agent_react_architect",
                    name="React 19 Architect",
                    role="Frontend Architecture & Component Engineer",
                    persona="Senior React engineer, server components, composition patterns, performance optimization.",
                    avatar="Layout",
                    toolsets=["vault", "perception"],
                    skills=["react-best-practices", "composition-patterns"],
                    category="web-development",
                ),
                AgentMember(
                    id="agent_ui_designer",
                    name="UI/UX & Aesthetics Designer",
                    role="Design Systems & Anti-Slop Visual Specialist",
                    persona="Tailored luxury color palettes, typography hierarchy, micro-interactions, responsive geometry.",
                    avatar="Palette",
                    toolsets=["vault"],
                    skills=["taste-skill", "ui-ux-pro-max", "frontend-design"],
                    category="design",
                ),
                AgentMember(
                    id="agent_qa_tester",
                    name="Test Engineering Specialist",
                    role="TDD Automation & QA Quality Gate Engineer",
                    persona="Test-driven development, Vitest automated suites, boundary condition testing, zero regressions.",
                    avatar="CheckCircle",
                    toolsets=["vault"],
                    skills=["test-driven-development", "webapp-testing"],
                    category="testing",
                ),
                AgentMember(
                    id="agent_backend_arch",
                    name="Backend & API Platform Engineer",
                    role="Server Topology & Protocol Architect",
                    persona="FastAPI / Express resilient endpoints, authentication boundaries, schema validation.",
                    avatar="Server",
                    toolsets=["vault"],
                    skills=["better-auth", "supabase-postgres"],
                    category="backend",
                ),
                AgentMember(
                    id="agent_sec_auditor",
                    name="Security & Threat Auditor",
                    role="Application Security & Static Analysis Reviewer",
                    persona="Threat modeling, credential leak prevention, OWASP compliance, zero-trust verification.",
                    avatar="ShieldAlert",
                    toolsets=["vault", "perception"],
                    skills=["static-analysis", "security-best-practices", "audit-website"],
                    category="security",
                ),
                AgentMember(
                    id="agent_mcp_builder",
                    name="Agent & MCP Systems Architect",
                    role="Model Context Protocol & Multi-Agent Engineer",
                    persona="Multi-agent protocols, tool schemas, lazy router orchestration, autonomous execution.",
                    avatar="Cpu",
                    toolsets=["vault"],
                    skills=["mcp-builder", "agents-sdk", "loki-mode"],
                    category="agents",
                ),
            ]
            
            for m in defaults:
                if not self.get_agent(m.id):
                    self.save_agent(m)

            # Seed only the permanent Executive Council (ad-hoc domain groups created dynamically on demand)
            if not self.get_group("group_core_council"):
                self.save_group(AgentCollaborationGroup(
                    id="group_core_council",
                    name="Core Executive Council",
                    description="Strategic multi-domain orchestration between Chief Operator, Hermes Archaeologist, and Bitterbot Critic.",
                    member_ids=["agent_chief", "agent_hermes", "agent_bitterbot"],
                    category="agents",
                    topic="High-Level Architecture & Strategic Alignment",
                ))
                    
            logger.info("Seeded default Chief Operator team roster and core council.")

    # =========================================================================
    # 1. Team Management (Hire, Update, Fire, List)
    # =========================================================================
    def list_team(self) -> List[AgentMember]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM operator_team ORDER BY hired_at ASC")
            members = []
            for r in cur.fetchall():
                members.append(AgentMember(
                    id=r["id"],
                    name=r["name"],
                    role=r["role"],
                    persona=r["persona"],
                    avatar=r["avatar"],
                    toolsets=json.loads(r["toolsets"]) if r["toolsets"] else ["vault"],
                    skills=json.loads(r["skills"]) if ("skills" in r.keys() and r["skills"]) else [],
                    category=r["category"] if "category" in r.keys() else None,
                    provider=r["provider"],
                    model=r["model"],
                    status=r["status"],
                    hired_at=r["hired_at"],
                    total_tasks=r["total_tasks"],
                ))
            return members

    def get_agent(self, agent_id: str) -> Optional[AgentMember]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM operator_team WHERE id = ?", (agent_id,))
            r = cur.fetchone()
            if not r:
                return None
            return AgentMember(
                id=r["id"],
                name=r["name"],
                role=r["role"],
                persona=r["persona"],
                avatar=r["avatar"],
                toolsets=json.loads(r["toolsets"]) if r["toolsets"] else ["vault"],
                skills=json.loads(r["skills"]) if ("skills" in r.keys() and r["skills"]) else [],
                category=r["category"] if "category" in r.keys() else None,
                provider=r["provider"],
                model=r["model"],
                status=r["status"],
                hired_at=r["hired_at"],
                total_tasks=r["total_tasks"],
            )

    def save_agent(self, member: AgentMember):
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO operator_team (id, name, role, persona, avatar, toolsets, skills, category, provider, model, status, hired_at, total_tasks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                role=excluded.role,
                persona=excluded.persona,
                avatar=excluded.avatar,
                toolsets=excluded.toolsets,
                skills=excluded.skills,
                category=excluded.category,
                provider=excluded.provider,
                model=excluded.model,
                status=excluded.status,
                total_tasks=excluded.total_tasks
            """, (
                member.id,
                member.name,
                member.role,
                member.persona,
                member.avatar,
                json.dumps(member.toolsets),
                json.dumps(member.skills),
                member.category,
                member.provider,
                member.model,
                member.status,
                member.hired_at,
                member.total_tasks,
            ))

    def hire_agent(
        self,
        name: str,
        role: str,
        persona: str,
        avatar: str = "Sparkles",
        toolsets: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
        category: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AgentMember:
        member = AgentMember(
            name=name,
            role=role,
            persona=persona,
            avatar=avatar,
            toolsets=toolsets or ["vault"],
            skills=skills or [],
            category=category,
            provider=provider,
            model=model,
        )
        self.save_agent(member)
        logger.info(f"Hired new agent teammate: {member.name} ({member.role}) with {len(member.skills)} skills")
        return member

    def fire_agent(self, agent_id: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM operator_team WHERE id = ?", (agent_id,))
            return cur.rowcount > 0

    # =========================================================================
    # 2. Agent Collaboration Groups (Multi-Agent Discussions)
    # =========================================================================
    def list_groups(self) -> List[AgentCollaborationGroup]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM operator_groups ORDER BY created_at ASC")
            groups = []
            for r in cur.fetchall():
                groups.append(AgentCollaborationGroup(
                    id=r["id"],
                    name=r["name"],
                    description=r["description"],
                    member_ids=json.loads(r["member_ids"]),
                    category=r["category"] if "category" in r.keys() else None,
                    topic=r["topic"],
                    created_at=r["created_at"],
                ))
            return groups

    def get_group(self, group_id: str) -> Optional[AgentCollaborationGroup]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM operator_groups WHERE id = ?", (group_id,))
            r = cur.fetchone()
            if not r:
                return None
            return AgentCollaborationGroup(
                id=r["id"],
                name=r["name"],
                description=r["description"],
                member_ids=json.loads(r["member_ids"]),
                category=r["category"] if "category" in r.keys() else None,
                topic=r["topic"],
                created_at=r["created_at"],
            )

    def save_group(self, group: AgentCollaborationGroup):
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO operator_groups (id, name, description, member_ids, category, topic, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                member_ids=excluded.member_ids,
                category=excluded.category,
                topic=excluded.topic
            """, (
                group.id,
                group.name,
                group.description,
                json.dumps(group.member_ids),
                group.category,
                group.topic,
                group.created_at,
            ))

    def create_group(
        self,
        name: str,
        description: str,
        member_ids: List[str],
        category: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> AgentCollaborationGroup:
        # Guarantee MaxIM chief is always a member
        if "agent_chief" not in member_ids:
            member_ids = ["agent_chief"] + member_ids

        group = AgentCollaborationGroup(
            name=name,
            description=description,
            member_ids=member_ids,
            category=category,
            topic=topic,
        )
        self.save_group(group)
        logger.info(f"Created agent collaboration group: {group.name} with {len(member_ids)} agents")
        return group

    def delete_group(self, group_id: str) -> bool:
        """Deletes an ad-hoc collaboration group and its message history."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            conn.execute("DELETE FROM operator_group_messages WHERE group_id = ?", (group_id,))
            cur.execute("DELETE FROM operator_groups WHERE id = ?", (group_id,))
            deleted = cur.rowcount > 0
            if deleted:
                logger.info(f"Deleted operator collaboration group: {group_id}")
            return deleted

    def _infer_group_specifications(
        self,
        topic: str,
        desktop_context: str = "",
        skills_requested: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Infers group name, domain category, charter description, and bespoke
        specialist agents with catalog-aligned skills based on topic, desktop use, or explicit skills.
        """
        combined = f"{topic} {desktop_context}".lower()

        # If user explicitly requested skills, look them up in the catalog
        if skills_requested:
            catalog_path = Path("f:/MAXIM V2/.agents/plugins/claude-skills/catalog.json")
            cat_data = {}
            if catalog_path.exists():
                try:
                    cat_data = json.loads(catalog_path.read_text(encoding="utf-8"))
                except Exception:
                    pass

            agents = []
            for idx, sid in enumerate(skills_requested[:3]):
                info = cat_data.get(sid, {})
                s_name = info.get("name", sid.replace("-", " ").title())
                s_cat = info.get("category", "productivity")
                agents.append({
                    "name": f"{s_name} Specialist",
                    "role": f"Specialist in {s_name}",
                    "persona": f"Focuses on applying the {s_name} skill and playbook directives to accomplish project goals.",
                    "avatar": "Sparkles",
                    "skills": [sid],
                    "category": s_cat,
                })
            
            primary_cat = agents[0]["category"] if agents else "productivity"
            return {
                "group_name": f"{topic.title() if topic else 'Custom Task'} Squad",
                "category": primary_cat,
                "description": f"Dynamic collaboration team assembled with requested skills: {', '.join(skills_requested)}",
                "agents": agents,
            }

        # Rule-based contextual intent extraction from topic and desktop context
        if any(w in combined for w in ["video", "youtube", "script", "audio", "podcast", "stream", "premiere", "obs", "film", "media"]):
            return {
                "group_name": "Media & Video Production Channel",
                "category": "marketing",
                "description": "Collaborative media room for scripts, viewer retention hooks, and video pacing.",
                "agents": [
                    {
                        "name": "Video Scriptwriter",
                        "role": "Narrative & Script Specialist",
                        "persona": "Writes engaging conversational scripts, viewer retention hooks, and punchy storytelling.",
                        "avatar": "Feather",
                        "skills": ["copywriting", "humanizer", "beautiful-prose"],
                        "category": "marketing",
                    },
                    {
                        "name": "Audience & SEO Strategist",
                        "role": "Metadata & Engagement Optimizer",
                        "persona": "Optimizes titles, CTR hooks, tags, and audience discoverability.",
                        "avatar": "TrendingUp",
                        "skills": ["claude-seo", "social-media-skills"],
                        "category": "seo",
                    },
                ],
            }
        elif any(w in combined for w in ["security", "auth", "leak", "audit", "cve", "vulnerability", "threat", "penetration", "privacy"]):
            return {
                "group_name": "Security & Threat Auditing Lab",
                "category": "security",
                "description": "Collaborative room for security threat modeling, static analysis, and leak prevention.",
                "agents": [
                    {
                        "name": "Static Analysis Auditor",
                        "role": "AppSec Code Reviewer",
                        "persona": "Detects injection vulnerabilities, token leaks, and insecure configs.",
                        "avatar": "ShieldAlert",
                        "skills": ["static-analysis", "security-best-practices"],
                        "category": "security",
                    },
                    {
                        "name": "Threat Modeling Specialist",
                        "role": "Defensive Security Architect",
                        "persona": "Models threat vectors, auth boundaries, and privilege escalation.",
                        "avatar": "Zap",
                        "skills": ["security-threat-model", "audit-website"],
                        "category": "security",
                    },
                ],
            }
        elif any(w in combined for w in ["3d", "webgl", "threejs", "canvas", "shader", "blender", "hero", "three.js"]):
            return {
                "group_name": "3D WebGL & Motion Lab",
                "category": "design",
                "description": "Collaborative room for Three.js shaders, luxury canvas animation, and WebGL experiences.",
                "agents": [
                    {
                        "name": "Three.js Scene Specialist",
                        "role": "3D Canvas & WebGL Developer",
                        "persona": "Specializes in Three.js geometry, particle clouds, and holographic shaders.",
                        "avatar": "Palette",
                        "skills": ["threejs-skills", "animate"],
                        "category": "design",
                    },
                    {
                        "name": "UI/UX Aesthetic Art Director",
                        "role": "Visual Polish & Layout Architect",
                        "persona": "Anti-slop typography, dark mode glassmorphism, and responsive geometry.",
                        "avatar": "Layout",
                        "skills": ["taste-skill", "ui-ux-pro-max"],
                        "category": "design",
                    },
                ],
            }
        elif any(w in combined for w in ["react", "component", "css", "tailwind", "ui", "frontend", "figma", "web"]):
            return {
                "group_name": "Web & Frontend Engineering Channel",
                "category": "web-development",
                "description": "Collaborative room for React 19 architecture, luxury UI/UX design, and component engineering.",
                "agents": [
                    {
                        "name": "React 19 Architect",
                        "role": "Frontend Architecture & Component Engineer",
                        "persona": "Senior React engineer, server components, composition patterns, performance optimization.",
                        "avatar": "Layout",
                        "skills": ["react-best-practices", "composition-patterns"],
                        "category": "web-development",
                    },
                    {
                        "name": "UI/UX & Aesthetics Designer",
                        "role": "Design Systems & Anti-Slop Visual Specialist",
                        "persona": "Tailored luxury color palettes, typography hierarchy, micro-interactions, responsive geometry.",
                        "avatar": "Palette",
                        "skills": ["taste-skill", "ui-ux-pro-max", "frontend-design"],
                        "category": "design",
                    },
                ],
            }
        elif any(w in combined for w in ["test", "vitest", "bug", "tdd", "assert", "coverage", "debug", "qa"]):
            return {
                "group_name": "Code Quality & Testing Channel",
                "category": "testing",
                "description": "Collaborative room for TDD test generation, reality checking, and systematic bug discovery.",
                "agents": [
                    {
                        "name": "Test Engineering Specialist",
                        "role": "TDD Automation & QA Quality Gate Engineer",
                        "persona": "Test-driven development, Vitest automated suites, boundary condition testing, zero regressions.",
                        "avatar": "CheckCircle",
                        "skills": ["test-driven-development", "webapp-testing"],
                        "category": "testing",
                    },
                    {
                        "name": "Bitterbot Critic",
                        "role": "Sarcastic Code Reviewer & Auditor",
                        "persona": "Relentless pragmatist, reality checker, demand receipts, zero-hallucination code reviewer.",
                        "avatar": "Zap",
                        "skills": ["systematic-debugging", "code-review"],
                        "category": "testing",
                    },
                ],
            }
        elif any(w in combined for w in ["backend", "api", "endpoint", "database", "postgres", "sql", "fastapi", "express", "sqlite"]):
            return {
                "group_name": "Backend & APIs Channel",
                "category": "backend",
                "description": "Collaborative room for server topologies, database schemas, and robust API contracts.",
                "agents": [
                    {
                        "name": "Backend & API Platform Engineer",
                        "role": "Server Topology & Protocol Architect",
                        "persona": "FastAPI / Express resilient endpoints, authentication boundaries, schema validation.",
                        "avatar": "Server",
                        "skills": ["better-auth", "supabase-postgres"],
                        "category": "backend",
                    },
                    {
                        "name": "Database & State Specialist",
                        "role": "Schema Design & Lock Avoidance Engineer",
                        "persona": "SQLite/Postgres indexing, query optimization, data migrations, ACID transactions.",
                        "avatar": "Database",
                        "skills": ["sqlite-indexing", "backend-architecture"],
                        "category": "backend",
                    },
                ],
            }
        elif any(w in combined for w in ["marketing", "copy", "social", "campaign", "newsletter", "headline", "post", "growth", "seo"]):
            return {
                "group_name": "Marketing & Growth Channel",
                "category": "marketing",
                "description": "Collaborative marketing room for conversion copy, viral social distribution, and SEO keyword growth.",
                "agents": [
                    {
                        "name": "Conversion Copywriter",
                        "role": "High-Impact Copywriting & Editorial Specialist",
                        "persona": "Audience-first copywriter, craft compelling hooks, sales narrative, anti-slop humanized messaging.",
                        "avatar": "Feather",
                        "skills": ["copywriting", "humanizer", "beautiful-prose"],
                        "category": "marketing",
                    },
                    {
                        "name": "Growth & SEO Specialist",
                        "role": "Search Engine & Conversion Rate Optimizer",
                        "persona": "Data-backed SEO strategist, keyword density auditor, CRO specialist, and GEO/AEO researcher.",
                        "avatar": "TrendingUp",
                        "skills": ["claude-seo", "page-cro", "marketing-skills"],
                        "category": "seo",
                    },
                ],
            }
        elif any(w in combined for w in ["mcp", "subagent", "swarm", "protocol", "agents", "loop"]):
            return {
                "group_name": "Agent Architecture & MCP Channel",
                "category": "agents",
                "description": "Collaborative room for multi-agent loops, MCP server configs, and autonomous tools.",
                "agents": [
                    {
                        "name": "Agent & MCP Systems Architect",
                        "role": "Model Context Protocol & Multi-Agent Engineer",
                        "persona": "Multi-agent protocols, tool schemas, lazy router orchestration, autonomous execution.",
                        "avatar": "Cpu",
                        "skills": ["mcp-builder", "agents-sdk", "loki-mode"],
                        "category": "agents",
                    },
                    {
                        "name": "Zylos Memory Curator",
                        "role": "Memory Architect & Context Safeguard",
                        "persona": "Five-layer inside-out memory curator, SQLite FTS5 indexer, and 75% safeguard compaction engine.",
                        "avatar": "Database",
                        "skills": ["planning-with-files", "using-superpowers"],
                        "category": "agents",
                    },
                ],
            }
        else:
            clean_title = topic[:32].strip().title() if topic else "Ad-Hoc Project"
            return {
                "group_name": f"{clean_title} Squad",
                "category": "productivity",
                "description": f"Dynamic collaboration team assembled for: {topic or 'General desktop task'}",
                "agents": [
                    {
                        "name": "Domain Implementation Lead",
                        "role": "Task Execution Specialist",
                        "persona": f"Focuses on practical implementation of: {topic or 'active workflow'}.",
                        "avatar": "Sparkles",
                        "skills": ["planning-with-files", "executing-plans"],
                        "category": "productivity",
                    },
                    {
                        "name": "Quality & Verification Reviewer",
                        "role": "Validation & Regression Auditor",
                        "persona": "Demands receipts, tests assumptions, validates deliverables.",
                        "avatar": "CheckCircle",
                        "skills": ["systematic-debugging", "code-review"],
                        "category": "testing",
                    },
                ],
            }

    async def assemble_dynamic_group(
        self,
        topic: str = "",
        group_name: Optional[str] = None,
        skills_requested: Optional[List[str]] = None,
        desktop_context: Optional[str] = None,
        use_active_window: bool = False,
    ) -> Dict[str, Any]:
        """
        Dynamically assembles an ad-hoc collaboration group on demand based on:
        1. Manual user request with topic and optional requested skills.
        2. Desktop-driven context via active window title or supplied context string.
        Selects or hires bespoke specialists, registers the group, and posts an orientation brief.
        """
        detected_window = ""
        if use_active_window or (not topic and not desktop_context):
            try:
                from tools.screen_tool import get_active_window_info
                w_info = get_active_window_info()
                w_title = w_info.get("title", "")
                if w_title and w_title not in ["Non-Windows Host", "Detection Error", "Untitled Window"]:
                    detected_window = w_title
            except Exception as e:
                logger.warning(f"Could not inspect active window: {e}")

        effective_desktop = desktop_context or detected_window
        effective_topic = topic or (f"Active Workflow: {detected_window}" if detected_window else "Ad-Hoc Project")

        spec = self._infer_group_specifications(
            topic=effective_topic,
            desktop_context=effective_desktop,
            skills_requested=skills_requested,
        )

        final_group_name = group_name or spec["group_name"]
        member_ids = ["agent_chief"]

        # Ensure bespoke agents exist or hire them
        all_team = {a.name.lower(): a for a in self.list_team()}
        for a_spec in spec["agents"]:
            existing = all_team.get(a_spec["name"].lower())
            if existing:
                member_ids.append(existing.id)
            else:
                new_agent = self.hire_agent(
                    name=a_spec["name"],
                    role=a_spec["role"],
                    persona=a_spec["persona"],
                    avatar=a_spec.get("avatar", "Sparkles"),
                    skills=a_spec.get("skills", []),
                    category=a_spec.get("category"),
                )
                member_ids.append(new_agent.id)

        # Create the dynamic group
        group = self.create_group(
            name=final_group_name,
            description=spec["description"],
            member_ids=member_ids,
            category=spec["category"],
            topic=effective_topic,
        )

        # Orientation greeting from MaxIM Chief Operator
        active_agents = [self.get_agent(m_id) for m_id in member_ids if self.get_agent(m_id)]
        roster_str = ", ".join([f"{a.name} ({a.role})" for a in active_agents if a.id != "agent_chief"])
        greeting = (
            f"[DYNAMIC GROUP ASSEMBLED]: '{group.name}'\n"
            f"- Topic/Objective: {effective_topic}\n"
            f"- Category: {group.category}\n"
            f"- Context: {effective_desktop or 'Manual Operator Request'}\n"
            f"- Specialist Roster: {roster_str}\n"
            f"MaxIM Chief Operator is conducting this channel. Ready for directives."
        )
        self.log_group_message(
            group_id=group.id,
            sender_id="agent_chief",
            sender_name="MaxIM Chief Operator",
            role="Chief Conductor",
            content=greeting,
        )

        return {
            "status": "success",
            "group": group.model_dump(),
            "members": [a.model_dump() for a in active_agents],
            "topic": effective_topic,
            "detected_desktop": effective_desktop,
            "message": f"Successfully assembled dynamic group '{group.name}' with {len(member_ids)} agents.",
        }

    def get_group_messages(self, group_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM operator_group_messages WHERE group_id = ? ORDER BY id ASC LIMIT ?",
                (group_id, limit),
            )
            return [dict(r) for r in cur.fetchall()]

    def log_group_message(self, group_id: str, sender_id: str, sender_name: str, role: str, content: str):
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO operator_group_messages (group_id, sender_id, sender_name, role, content, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (group_id, sender_id, sender_name, role, content, utc_now_iso()))

    async def run_group_chat(
        self,
        group_id: str,
        user_message: str,
        rounds: int = 1,
        target_agent_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrates multi-agent collaborative turn-taking in a group channel.
        Each agent in the group reads the shared discussion history, applies its
        assigned specialized skills and persona, and contributes iteratively.
        """
        group = self.get_group(group_id)
        if not group:
            return {"error": f"Collaboration group '{group_id}' not found."}

        # Record incoming message if provided
        if user_message:
            self.log_group_message(
                group_id=group_id,
                sender_id="user",
                sender_name="Operator User",
                role="User Directive",
                content=user_message,
            )

        turns_executed = []
        all_members = [self.get_agent(m_id) for m_id in group.member_ids if self.get_agent(m_id)]
        
        # Filter target agents if specified
        if target_agent_ids:
            active_members = [m for m in all_members if m.id in target_agent_ids]
        else:
            active_members = all_members

        for r in range(rounds):
            for member in active_members:
                history = self.get_group_messages(group_id, limit=20)
                formatted_history = "\n".join([
                    f"[{msg['sender_name']} ({msg['role']})]: {msg['content']}"
                    for msg in history[-8:]
                ])

                # Load skills guidance for this agent
                skills_context = get_skills_prompt_context(member.skills)

                system_prompt = (
                    f"You are {member.name}, working as part of the '{group.name}' agent team.\n"
                    f"Your specialty role is: {member.role}.\n"
                    f"Your core persona: {member.persona}\n\n"
                    f"{skills_context}"
                    f"Group Charter: {group.description}\n"
                    f"Active Discussion Topic: {group.topic or user_message}\n\n"
                    f"Recent Channel Conversation:\n{formatted_history}\n\n"
                    "Operating Guidelines:\n"
                    "1. Respond directly to the discussion, applying your specific skills and role.\n"
                    "2. Build upon, critique, or hand off concrete deliverables to your teammates.\n"
                    "3. Format actionable findings clearly (e.g. bullet points, code, or structured copy).\n"
                    "4. Write like a thoughtful human: direct verbs, organic rhythm, zero promotional clichés.\n"
                    "5. No chatbot filler ('Certainly!', 'I hope this helps'). Deliver the solution and stop.\n"
                )

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Team collaboration turn {r+1}. Provide your expert contribution to the active discussion."},
                ]

                try:
                    response = await model_router.chat_completion(
                        messages=messages,
                        provider=member.provider,
                        model=member.model,
                    )
                    content = response.choices[0].message.content or ""
                except Exception as err:
                    content = f"[{member.name} connection error: {err}]"

                self.log_group_message(
                    group_id=group_id,
                    sender_id=member.id,
                    sender_name=member.name,
                    role=member.role,
                    content=content,
                )

                member.total_tasks += 1
                self.save_agent(member)

                turns_executed.append({
                    "round": r + 1,
                    "agent_id": member.id,
                    "agent_name": member.name,
                    "role": member.role,
                    "avatar": member.avatar,
                    "skills": member.skills,
                    "content": content,
                    "timestamp": utc_now_iso(),
                })

        return {
            "status": "success",
            "group_id": group_id,
            "group_name": group.name,
            "category": group.category,
            "turns": turns_executed,
            "total_turns": len(turns_executed),
        }

    # =========================================================================
    # 3. MaxIM Master Conductor: Task Dispatch, Routing & Cross-Group Handoff
    # =========================================================================
    async def dispatch_group_task(
        self,
        group_id: str,
        task_prompt: str,
        target_agent_ids: Optional[List[str]] = None,
        rounds: int = 1,
    ) -> Dict[str, Any]:
        """
        MaxIM (Chief Operator) enters a group, issues an administrative brief with
        explicit agent instructions, executes collaborative turns, and signs off.
        """
        group = self.get_group(group_id)
        if not group:
            return {"status": "error", "error": f"Group '{group_id}' not found."}

        chief = self.get_agent("agent_chief")
        chief_name = chief.name if chief else "MaxIM Chief Operator"

        # 1. MaxIM posts the executive brief into the group
        admin_brief = f"[EXECUTIVE DIRECTIVE from {chief_name}]: {task_prompt}"
        self.log_group_message(
            group_id=group_id,
            sender_id="agent_chief",
            sender_name=chief_name,
            role="Chief Conductor",
            content=admin_brief,
        )

        # 2. Run the group discussion among the specialists
        chat_res = await self.run_group_chat(
            group_id=group_id,
            user_message="",  # already posted by chief
            rounds=rounds,
            target_agent_ids=target_agent_ids,
        )

        # 3. MaxIM synthesizes sign-off
        signoff_prompt = (
            f"You are {chief_name}, reviewing the output of your team in '{group.name}'.\n"
            f"Original Directive: {task_prompt}\n"
            f"Team Responses: {json.dumps(chat_res.get('turns', []))}\n"
            "Produce a concise 2-3 sentence executive sign-off verifying that deliverables were met."
        )
        try:
            signoff_res = await model_router.chat_completion(
                messages=[{"role": "user", "content": signoff_prompt}]
            )
            signoff_text = signoff_res.choices[0].message.content or "Deliverables reviewed and approved."
        except Exception:
            signoff_text = "Executive review completed. Team deliverables recorded."

        self.log_group_message(
            group_id=group_id,
            sender_id="agent_chief",
            sender_name=chief_name,
            role="Chief Conductor",
            content=f"[EXECUTIVE REVIEW & SIGN-OFF]: {signoff_text}",
        )

        return {
            "status": "completed",
            "group_id": group_id,
            "group_name": group.name,
            "category": group.category,
            "task": task_prompt,
            "turns": chat_res.get("turns", []),
            "signoff": signoff_text,
            "timestamp": utc_now_iso(),
        }

    async def orchestrate_objective(
        self,
        objective: str,
        preferred_category: Optional[str] = None,
        rounds: int = 1,
        save_to_vault: bool = True,
    ) -> Dict[str, Any]:
        """
        Autonomous MaxIM Conductor:
        1. Analyzes objective and maps to the best specialized channel.
        2. Dispatches task to the group.
        3. Generates executive shift report and archives to Obsidian vault.
        """
        # Determine category and target group
        cat = (preferred_category or "").lower().strip()
        lowered = objective.lower()

        # Check existing groups first
        existing_groups = self.list_groups()
        target_group = None
        for g in existing_groups:
            if g.id == "group_core_council":
                continue
            if cat and g.category and g.category.lower() == cat:
                target_group = g
                break
            if g.category and g.category.lower() in lowered:
                target_group = g
                break

        # If no specialized group exists, dynamically assemble one on demand
        if not target_group:
            assemble_res = await self.assemble_dynamic_group(
                topic=objective,
                desktop_context=None,
                use_active_window=False,
            )
            target_group = self.get_group(assemble_res["group"]["id"])

        if not target_group:
            target_group = self.get_group("group_core_council")

        group = target_group
        group_id = target_group.id

        # Dispatch task through MaxIM
        res = await self.dispatch_group_task(
            group_id=group_id,
            task_prompt=objective,
            rounds=rounds,
        )

        # Archive to Obsidian vault
        if save_to_vault:
            clean_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            note_title = f"Team_Dispatch_{group.name.replace(' ', '_')}_{clean_time}"
            turns_md = "\n\n".join([
                f"### {t['agent_name']} ({t['role']})\n**Skills**: {', '.join(t.get('skills', [])) or 'Generalist'}\n\n{t['content']}"
                for t in res.get("turns", [])
            ])
            note_body = (
                f"# MaxIM Orchestration: {group.name}\n\n"
                f"- **Category Channel**: `{group.category or 'general'}`\n"
                f"- **Timestamp**: `{res['timestamp']}`\n"
                f"- **Group ID**: `{group_id}`\n\n"
                f"## Executive Objective\n{objective}\n\n"
                f"## Team Collaboration Thread\n{turns_md}\n\n"
                f"## Executive Sign-Off\n{res.get('signoff')}\n\n"
                f"[[00 - MOC/Master MOC]] | [[03 - Agents/Agent Registry]]\n"
            )
            vault_synapse.write_note(
                title=note_title,
                content=note_body,
                folder="03 - Agents",
                tags=["#orchestration", "#agent-team", f"#{group.category or 'general'}"]
            )

        return res

    async def cross_group_handoff(
        self,
        source_group_id: str,
        target_group_id: str,
        deliverable_summary: str,
        next_step_instruction: str,
        rounds: int = 1,
    ) -> Dict[str, Any]:
        """
        MaxIM bridges work from one specialized group channel to another.
        """
        source_group = self.get_group(source_group_id)
        target_group = self.get_group(target_group_id)

        if not source_group or not target_group:
            return {"status": "error", "error": "Source or target group not found."}

        chief_name = "MaxIM Chief Operator"
        handoff_brief = (
            f"[CROSS-GROUP HANDOFF from #{source_group.name}]:\n"
            f"Deliverable Summary: {deliverable_summary}\n\n"
            f"Directive for #{target_group.name}: {next_step_instruction}"
        )

        # Log into source group that handoff was dispatched
        self.log_group_message(
            group_id=source_group_id,
            sender_id="agent_chief",
            sender_name=chief_name,
            role="Chief Conductor",
            content=f"[CROSS-GROUP HANDOFF DISPATCHED to #{target_group.name}]: {next_step_instruction}",
        )

        # Dispatch into target group
        target_res = await self.dispatch_group_task(
            group_id=target_group_id,
            task_prompt=handoff_brief,
            rounds=rounds,
        )

        return {
            "status": "handoff_completed",
            "source_group": source_group.name,
            "target_group": target_group.name,
            "handoff_brief": handoff_brief,
            "target_execution": target_res,
        }

    # =========================================================================
    # 4. 7x24 Autonomous Shifts & Reporting
    # =========================================================================
    async def execute_shift(
        self,
        agent_id: str,
        task: str,
        save_to_vault: bool = True,
    ) -> ShiftReport:
        """
        Executes a background shift for a specialized agent and logs an executive report.
        """
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent '{agent_id}' does not exist.")

        agent.status = "active"
        self.save_agent(agent)

        skills_context = get_skills_prompt_context(agent.skills)

        system_prompt = (
            f"You are {agent.name}, operating on autonomous shift.\n"
            f"Role: {agent.role}\n"
            f"Persona: {agent.persona}\n\n"
            f"{skills_context}"
            "Produce a structured executive summary of your shift findings and recommendations."
        )

        try:
            res = await model_router.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task},
                ],
                provider=agent.provider,
                model=agent.model,
            )
            summary = res.choices[0].message.content or "Shift executed without text."
            status = "completed"
        except Exception as e:
            summary = f"Shift failed: {e}"
            status = "failed"

        agent.status = "idle"
        agent.total_tasks += 1
        self.save_agent(agent)

        report = ShiftReport(
            agent_id=agent.id,
            agent_name=agent.name,
            task=task,
            status=status,
            summary=summary,
        )

        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO operator_reports (id, agent_id, agent_name, task, status, summary, timestamp, evidence_receipts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.id,
                report.agent_id,
                report.agent_name,
                report.task,
                report.status,
                report.summary,
                report.timestamp,
                json.dumps(report.evidence_receipts),
            ))

        if save_to_vault:
            clean_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            note_title = f"{agent.name.replace(' ', '_')}_Shift_{clean_time}"
            note_body = (
                f"# Autonomous Shift Report: {agent.name}\n\n"
                f"- **Agent ID**: `{agent.id}`\n"
                f"- **Role**: {agent.role}\n"
                f"- **Assigned Skills**: {', '.join(agent.skills) or 'Generalist'}\n"
                f"- **Timestamp**: `{report.timestamp}`\n"
                f"- **Status**: `{report.status}`\n\n"
                f"## Assigned Mission\n{task}\n\n"
                f"## Executive Synthesis\n{summary}\n\n"
                f"[[00 - MOC/Master MOC]] | [[01 - Memory/Checkpoints]]\n"
            )
            vault_synapse.write_note(
                title=note_title,
                content=note_body,
                folder="03 - Agents",
                tags=["#agent-shift", "#operator", f"#{agent.name.lower().replace(' ', '-')}"]
            )

        logger.info(f"Shift completed by {agent.name}: {report.id}")
        return report

    def list_reports(self, limit: int = 20) -> List[ShiftReport]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM operator_reports ORDER BY timestamp DESC LIMIT ?", (limit,))
            reports = []
            for r in cur.fetchall():
                reports.append(ShiftReport(
                    id=r["id"],
                    agent_id=r["agent_id"],
                    agent_name=r["agent_name"],
                    task=r["task"],
                    status=r["status"],
                    summary=r["summary"],
                    timestamp=r["timestamp"],
                    evidence_receipts=json.loads(r["evidence_receipts"]) if r["evidence_receipts"] else [],
                ))
            return reports

# Global singleton
agent_operator = ChiefAgentOperator()
