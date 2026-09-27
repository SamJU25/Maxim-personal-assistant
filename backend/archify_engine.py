"""
Archify Architecture & Diagram Verification Engine for MaxIM.
Adapted from tt-a1i/archify architecture.
Generates verified Mermaid system diagrams, sequence diagrams, and data flows,
validating layout and exporting self-contained visual notes to Obsidian.
Repository reference: https://github.com/tt-a1i/archify
"""
import sqlite3
import re
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from config import config

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

VALID_DIAGRAM_HEADERS = [
    "graph TD", "graph LR", "graph TB", "graph RL",
    "flowchart TD", "flowchart LR", "flowchart TB", "flowchart RL",
    "sequenceDiagram",
    "stateDiagram-v2", "stateDiagram",
    "classDiagram",
    "erDiagram"
]

class ArchifyEngine:
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
            CREATE TABLE IF NOT EXISTS architecture_diagrams (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                diagram_type TEXT NOT NULL,
                mermaid_code TEXT NOT NULL,
                description TEXT,
                node_count INTEGER DEFAULT 0,
                edge_count INTEGER DEFAULT 0,
                vault_path TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

    def validate_mermaid(self, code: str) -> Dict[str, Any]:
        """
        Validates Mermaid syntax rules, header declarations, balanced brackets,
        and extracts node/edge counts.
        """
        lines = [line.strip() for line in code.strip().splitlines() if line.strip() and not line.strip().startswith("%%")]
        if not lines:
            return {"valid": False, "error": "Diagram code is empty.", "node_count": 0, "edge_count": 0}

        header = lines[0]
        has_valid_header = any(header.startswith(h) for h in VALID_DIAGRAM_HEADERS)
        if not has_valid_header:
            return {
                "valid": False,
                "error": f"Invalid or missing diagram header: '{header}'. Must start with one of {VALID_DIAGRAM_HEADERS[:4]}...",
                "node_count": 0,
                "edge_count": 0
            }

        # Check bracket balance
        open_brackets = code.count("[") + code.count("(") + code.count("{")
        close_brackets = code.count("]") + code.count(")") + code.count("}")
        if open_brackets != close_brackets:
            return {
                "valid": False,
                "error": f"Unbalanced brackets in diagram: {open_brackets} open vs {close_brackets} closed.",
                "node_count": 0,
                "edge_count": 0
            }

        # Extract edges (--> , --- , ==> , -.-> , ->> )
        edge_pattern = re.compile(r"(-->|---|==>|-\.->|->>|--\s*[\w\s]+\s*-->)")
        edge_count = len(edge_pattern.findall(code))

        # Extract node IDs
        node_pattern = re.compile(r"([A-Za-z0-9_]+)\s*(\[|\(|\{)")
        found_nodes = set(m.group(1) for m in node_pattern.finditer(code))
        node_count = max(len(found_nodes), 2 if edge_count > 0 else 1)

        return {
            "valid": True,
            "header": header,
            "node_count": node_count,
            "edge_count": edge_count,
            "error": None
        }

    def generate_diagram(
        self,
        title: str,
        diagram_type: str = "system",
        description: Optional[str] = None,
        raw_mermaid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validates and records an architectural diagram, then exports it to Obsidian with markdown formatting.
        """
        clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip() or "Architecture_Diagram"
        
        # Default starter templates if raw_mermaid is not provided
        if not raw_mermaid:
            if diagram_type == "sequence":
                raw_mermaid = f"""sequenceDiagram
    autonumber
    actor User
    participant Frontend as MaxIM Frontend (React 19)
    participant Engine as ReAct Engine (FastAPI)
    participant Model as LLM Provider
    participant Vault as Obsidian Vault

    User->>Frontend: Submit Task
    Frontend->>Engine: POST /api/chat (SSE Stream)
    Engine->>Model: ReAct Prompt + LifeOS Context
    Model-->>Engine: Tool Calls / Receipt
    Engine->>Vault: Sync Memory & Ledger
    Engine-->>Frontend: Stream Tokens & Receipts
    Frontend-->>User: Render Interactive View
"""
            elif diagram_type == "data_flow":
                raw_mermaid = f"""flowchart LR
    A[Inbound Data / User Prompt] --> B[Security Audit & Sanitizer]
    B --> C[ReAct Orchestration Loop]
    C --> D[(SQLite WAL maxim.db)]
    C --> E[Obsidian Knowledge Synapse]
    C --> F[External Gateway / Tools]
    F --> C
    C --> G[SSE Response Stream]
"""
            elif diagram_type == "state_machine":
                raw_mermaid = f"""stateDiagram-v2
    [*] --> Idle
    Idle --> Ingesting: User Input Received
    Ingesting --> Auditing: AgentShield Inbound Scan
    Auditing --> Thinking: Verified Clean
    Auditing --> Blocked: Prompt Injection Detected
    Blocked --> Idle: Threat Logged
    Thinking --> ToolExecution: Tool Calls Emitted
    ToolExecution --> Thinking: Receipt Feedback
    Thinking --> Streaming: Final Synthesized Output
    Streaming --> Idle: Turn Complete
"""
            else:  # system architecture default
                raw_mermaid = f"""graph TD
    subgraph Client Layer [User & Remote Interfaces]
        UI[React 19 Luxury Frontend]
        TG[Telegram Bot Remote Uplink]
        CUA[Computer Use Background Driver]
    end

    subgraph Core Brain [FastAPI & ReAct Engine]
        API[FastAPI Server :8000]
        Router[Multi-Connection Router]
        Engine[ReAct Reasoning Loop]
        Governor[Hardware & Cost Governor]
    end

    subgraph Persistence [State & Knowledge]
        DB[(SQLite WAL maxim.db)]
        Vault[Obsidian Vault Markdown]
        FTS[SQLite FTS5 Full Text Search]
    end

    UI --> API
    TG --> API
    API --> Engine
    Engine --> Router
    Engine --> DB
    Engine --> Vault
    Engine --> Governor
"""

        # Validate syntax
        val = self.validate_mermaid(raw_mermaid)
        if not val["valid"]:
            raise ValueError(f"Mermaid validation failed: {val['error']}")

        now = utc_now_iso()
        diag_id = f"diag_{uuid.uuid4().hex[:8]}"

        # Write to vault/02 - Knowledge/Architecture/<clean_title>.md
        out_dir = self.vault_dir / "02 - Knowledge" / "Architecture"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{clean_title}.md"

        desc_str = description or f"Architectural specification and verifiable diagram for {clean_title}."
        md = f"# 📐 {clean_title}\n\n"
        md += f"> **Type:** `{diagram_type}` | **Nodes:** `{val['node_count']}` | **Edges:** `{val['edge_count']}`\n"
        md += f"> **Generated:** `{now}`\n"
        md += f"> **Tags:** #architecture #diagram #system-design #verified\n\n"
        md += "## 📋 Overview\n"
        md += f"{desc_str}\n\n"
        md += "## 📊 System Diagram\n\n"
        md += "```mermaid\n"
        md += raw_mermaid.strip() + "\n"
        md += "```\n\n"
        md += "---\n*Generated by Archify Engine for MaxIM*\n"

        out_file.write_text(md, encoding="utf-8")

        # Save to database
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO architecture_diagrams (id, title, diagram_type, mermaid_code, description, node_count, edge_count, vault_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                diag_id,
                clean_title,
                diagram_type,
                raw_mermaid.strip(),
                desc_str,
                val["node_count"],
                val["edge_count"],
                str(out_file),
                now,
                now
            ))
            conn.commit()

        return {
            "id": diag_id,
            "title": clean_title,
            "diagram_type": diagram_type,
            "node_count": val["node_count"],
            "edge_count": val["edge_count"],
            "vault_path": str(out_file),
            "mermaid_code": raw_mermaid.strip(),
            "created_at": now
        }

    def inspect_codebase_architecture(self, target_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Scans a Python backend directory, extracts module dependencies from import statements,
        and constructs a verifiable module dependency diagram.
        """
        root_dir = Path(target_dir).resolve() if target_dir else Path(__file__).resolve().parent
        py_files = list(root_dir.glob("*.py"))
        
        module_names = set(f.stem for f in py_files if not f.name.startswith("test_"))
        dependencies: Dict[str, set] = {m: set() for m in module_names}

        import_pattern = re.compile(r"^(?:from\s+([A-Za-z0-9_]+)\s+import|import\s+([A-Za-z0-9_]+))", re.MULTILINE)

        for py in py_files:
            mod_name = py.stem
            if mod_name.startswith("test_") or mod_name not in module_names:
                continue
            try:
                content = py.read_text(encoding="utf-8", errors="ignore")
                for match in import_pattern.finditer(content):
                    dep = match.group(1) or match.group(2)
                    if dep in module_names and dep != mod_name:
                        dependencies[mod_name].add(dep)
            except Exception:
                pass

        # Build clean Mermaid flowchart
        mermaid_lines = ["flowchart TD"]
        edge_count = 0
        
        # Group core modules vs auxiliary
        core_mods = [m for m in ("server", "engine", "router", "memory", "config") if m in module_names]
        feature_mods = [m for m in sorted(module_names) if m not in core_mods][:15]  # limit to top 15 for readability

        for src, dests in dependencies.items():
            if src in core_mods or src in feature_mods:
                for dst in dests:
                    if dst in core_mods or dst in feature_mods:
                        mermaid_lines.append(f"    {src}[{src}.py] --> {dst}[{dst}.py]")
                        edge_count += 1

        if edge_count == 0:
            # Fallback connection to keep diagram valid
            for m in list(module_names)[:5]:
                mermaid_lines.append(f"    CoreSystem --> {m}[{m}.py]")

        mermaid_code = "\n".join(mermaid_lines)
        return self.generate_diagram(
            title="MaxIM_Backend_Module_Architecture",
            diagram_type="system",
            description=f"Auto-extracted module dependency architecture across {len(module_names)} Python backend modules.",
            raw_mermaid=mermaid_code
        )

    def list_diagrams(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM architecture_diagrams ORDER BY created_at DESC")
            return [dict(r) for r in cursor.fetchall()]

# Singleton instance
archify_engine = ArchifyEngine()
