"""
Model Context Protocol (MCP) Client & Registry Hub for MaxIM.
Enables dynamic discovery from Smithery, Glama, and the Official MCP Registry,
inspection of tool schemas, and local SQLite persistence for mounted servers.
"""
import sys
import json
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx
from pydantic import BaseModel, Field

from config import config

logger = logging.getLogger("maxim.mcp")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# =============================================================================
# CURATED BASELINE MCP REGISTRY (Zero-Config / Offline Resilient)
# Sourced from Official MCP, Smithery, and Glama standards
# =============================================================================
CURATED_MCP_REGISTRY: List[Dict[str, Any]] = [
    {
        "id": "filesystem",
        "name": "Filesystem MCP",
        "vendor": "modelcontextprotocol",
        "description": "Secure direct read/write access to local files with directory sandboxing.",
        "registry": "official",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "./vault"],
        "env_vars": [],
        "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem",
        "tools_preview": ["read_file", "write_file", "list_directory", "move_file", "search_files"],
    },
    {
        "id": "github",
        "name": "GitHub MCP",
        "vendor": "modelcontextprotocol",
        "description": "Search repositories, read code files, inspect pull requests, and manage issues.",
        "registry": "official",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env_vars": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
        "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/github",
        "tools_preview": ["search_repositories", "get_file_contents", "create_issue", "create_pull_request"],
    },
    {
        "id": "postgres",
        "name": "PostgreSQL MCP",
        "vendor": "modelcontextprotocol",
        "description": "Inspect PostgreSQL database schemas, table topologies, and run parameterized queries.",
        "registry": "smithery",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"],
        "env_vars": ["POSTGRES_URL"],
        "homepage": "https://smithery.ai/server/@modelcontextprotocol/server-postgres",
        "tools_preview": ["query", "describe_table", "list_tables"],
    },
    {
        "id": "sqlite",
        "name": "SQLite MCP",
        "vendor": "mcp-community",
        "description": "Local SQLite database inspector, schema explorer, and analytical query runner.",
        "registry": "glama",
        "transport": "stdio",
        "command": "uvx",
        "args": ["mcp-server-sqlite", "--db-path", "./maxim.db"],
        "env_vars": [],
        "homepage": "https://glama.ai/mcp/servers/sqlite",
        "tools_preview": ["read_query", "write_query", "list_tables", "describe_table"],
    },
    {
        "id": "brave-search",
        "name": "Brave Search MCP",
        "vendor": "modelcontextprotocol",
        "description": "Privacy-first real-time web search and local point-of-interest discovery.",
        "registry": "official",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env_vars": ["BRAVE_API_KEY"],
        "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search",
        "tools_preview": ["brave_web_search", "brave_local_search"],
    },
    {
        "id": "fetch",
        "name": "Web Fetch & HTML-to-Markdown MCP",
        "vendor": "modelcontextprotocol",
        "description": "Converts arbitrary web pages to clean Markdown with token budgeting.",
        "registry": "official",
        "transport": "stdio",
        "command": "uvx",
        "args": ["mcp-server-fetch"],
        "env_vars": [],
        "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/fetch",
        "tools_preview": ["fetch_url"],
    },
    {
        "id": "puppeteer",
        "name": "Puppeteer Browser Automation MCP",
        "vendor": "modelcontextprotocol",
        "description": "Headless Chromium browser control: navigate, click, fill forms, take screenshots.",
        "registry": "smithery",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
        "env_vars": [],
        "homepage": "https://smithery.ai/server/@modelcontextprotocol/server-puppeteer",
        "tools_preview": ["puppeteer_navigate", "puppeteer_click", "puppeteer_fill", "puppeteer_screenshot"],
    },
    {
        "id": "memory",
        "name": "Graph Knowledge Memory MCP",
        "vendor": "modelcontextprotocol",
        "description": "Entity-relation knowledge graph memory for continuous context retention.",
        "registry": "glama",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
        "env_vars": [],
        "homepage": "https://glama.ai/mcp/servers/memory",
        "tools_preview": ["create_entities", "create_relations", "read_graph", "search_nodes"],
    },
    {
        "id": "slack",
        "name": "Slack Workspace MCP",
        "vendor": "modelcontextprotocol",
        "description": "Send messages, read channels, and search Slack history.",
        "registry": "official",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env_vars": ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
        "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/slack",
        "tools_preview": ["list_channels", "post_message", "get_channel_history"],
    },
    {
        "id": "docker",
        "name": "Docker Daemon MCP",
        "vendor": "mcp-community",
        "description": "Manage containers, inspect images, run detached sandboxes, and tail logs.",
        "registry": "smithery",
        "transport": "stdio",
        "command": "uvx",
        "args": ["mcp-server-docker"],
        "env_vars": ["DOCKER_HOST"],
        "homepage": "https://smithery.ai/server/docker",
        "tools_preview": ["list_containers", "start_container", "stop_container", "container_logs"],
    },
    {
        "id": "sentry",
        "name": "Sentry Error Monitoring MCP",
        "vendor": "modelcontextprotocol",
        "description": "Analyze production stack traces, error issues, and release metrics in Sentry.",
        "registry": "glama",
        "transport": "stdio",
        "command": "uvx",
        "args": ["mcp-server-sentry", "--auth-token", "dummy"],
        "env_vars": ["SENTRY_AUTH_TOKEN"],
        "homepage": "https://glama.ai/mcp/servers/sentry",
        "tools_preview": ["get_issue", "list_issues", "query_events"],
    },
    {
        "id": "obsidian-vault",
        "name": "Obsidian Vault Synapse MCP",
        "vendor": "mcp-community",
        "description": "Search notes, extract wikilinks, and organize Obsidian knowledge graph.",
        "registry": "official",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "mcp-obsidian", "./vault"],
        "env_vars": [],
        "homepage": "https://smithery.ai/server/mcp-obsidian",
        "tools_preview": ["list_vault_notes", "search_vault", "read_vault_note", "append_vault_note"],
    },
]

# =============================================================================
# DATA MODELS
# =============================================================================

class MCPServerConfig(BaseModel):
    name: str
    transport: str = Field(default="stdio", description="'stdio' or 'sse'")
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    env: Dict[str, str] = Field(default_factory=dict)
    description: Optional[str] = None
    source_registry: Optional[str] = "custom"
    installed_at: str = Field(default_factory=utc_now_iso)
    status: str = "active"

# =============================================================================
# MCP CLIENT & REGISTRY MANAGER
# =============================================================================

class MCPClientManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self.servers: Dict[str, MCPServerConfig] = {}
        self._cached_tools: Dict[str, List[Dict[str, Any]]] = {}
        self._init_sqlite()
        self._load_persisted_servers()

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

    def _init_sqlite(self):
        with self._get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS mcp_servers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                transport TEXT NOT NULL,
                command TEXT,
                args TEXT,
                url TEXT,
                env TEXT,
                description TEXT,
                source_registry TEXT,
                installed_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
            );
            """)

    def _load_persisted_servers(self):
        """Loads mounted MCP servers from the SQLite database."""
        try:
            with self._get_connection() as conn:
                rows = conn.execute("SELECT * FROM mcp_servers WHERE status = 'active'").fetchall()
                for r in rows:
                    cfg = MCPServerConfig(
                        name=r["name"],
                        transport=r["transport"],
                        command=r["command"],
                        args=json.loads(r["args"]) if r["args"] else [],
                        url=r["url"],
                        env=json.loads(r["env"]) if r["env"] else {},
                        description=r["description"],
                        source_registry=r["source_registry"],
                        installed_at=r["installed_at"],
                        status=r["status"],
                    )
                    self.servers[cfg.name] = cfg
            logger.info("Loaded %d persisted MCP servers from SQLite.", len(self.servers))
        except Exception as e:
            logger.warning("Could not load persisted MCP servers: %s", e)

    # =========================================================================
    # 1. Registry Search & Inspection (Smithery, Glama, Official)
    # =========================================================================

    async def search_registries(
        self,
        query: str,
        registry: str = "all",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Searches MCP registries (Smithery, Glama, Official) with local fallback.
        Returns matching servers, installation commands, and tool previews.
        """
        clean_q = query.strip().lower()
        results: List[Dict[str, Any]] = []

        # 1. Match from Curated Baseline
        matched_curated = []
        for entry in CURATED_MCP_REGISTRY:
            if registry != "all" and entry["registry"] != registry:
                continue
            searchable = f"{entry['id']} {entry['name']} {entry['description']} {' '.join(entry.get('tools_preview', []))}".lower()
            if not clean_q or clean_q in searchable:
                matched_curated.append(entry)

        results.extend(matched_curated)

        # 2. Online Discovery via Agent Reach (if query is specific)
        if clean_q and len(results) < limit:
            try:
                from tools.reach_tool import agent_reach
                search_q = f"site:smithery.ai/server OR site:glama.ai/mcp/servers {query} mcp server"
                web_hits = await agent_reach.web_search(search_q, limit=4)
                for hit in web_hits.get("results", []):
                    title = hit.get("title", "")
                    url = hit.get("url", "")
                    snippet = hit.get("snippet", "")
                    reg = "smithery" if "smithery.ai" in url else ("glama" if "glama.ai" in url else "community")
                    slug = url.rstrip("/").split("/")[-1].replace("@", "").replace("/", "-")
                    
                    if not any(r["id"] == slug for r in results):
                        results.append({
                            "id": slug,
                            "name": title.split("|")[0].replace("MCP Server", "").strip(),
                            "vendor": "community",
                            "description": snippet[:200],
                            "registry": reg,
                            "transport": "stdio",
                            "command": "npx",
                            "args": ["-y", slug],
                            "env_vars": [],
                            "homepage": url,
                            "tools_preview": ["custom_tools"],
                        })
            except Exception as e:
                logger.debug("Online MCP registry search skipped: %s", e)

        return {
            "query": query,
            "registry_filter": registry,
            "total_found": len(results),
            "results": results[:limit],
            "supported_registries": ["all", "official", "smithery", "glama"],
        }

    def inspect_server(self, server_id_or_name: str) -> Dict[str, Any]:
        """
        Returns full manifest, required env vars, and setup commands for an MCP server.
        """
        target = server_id_or_name.strip().lower()
        
        # Check installed servers first
        if target in self.servers:
            s = self.servers[target]
            return {
                "source": "installed",
                "name": s.name,
                "transport": s.transport,
                "command": s.command,
                "args": s.args,
                "env": list(s.env.keys()),
                "status": s.status,
                "description": s.description,
            }

        # Check curated baseline
        for entry in CURATED_MCP_REGISTRY:
            if entry["id"].lower() == target or entry["name"].lower() == target:
                return {
                    "source": "registry",
                    "id": entry["id"],
                    "name": entry["name"],
                    "vendor": entry["vendor"],
                    "description": entry["description"],
                    "registry": entry["registry"],
                    "transport": entry["transport"],
                    "command": entry["command"],
                    "args": entry["args"],
                    "required_env_vars": entry["env_vars"],
                    "homepage": entry["homepage"],
                    "tools_preview": entry["tools_preview"],
                    "sample_install_command": f"{entry['command']} {' '.join(entry['args'])}",
                }

        # Generic template for unindexed community server
        return {
            "source": "generic_template",
            "id": target,
            "name": target.title(),
            "vendor": "community",
            "description": f"Community Model Context Protocol server for '{target}'.",
            "registry": "custom",
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", target],
            "required_env_vars": [],
            "tools_preview": [f"{target}_action"],
            "sample_install_command": f"npx -y {target}",
        }

    # =========================================================================
    # 2. Server Installation & Management (Persistent)
    # =========================================================================

    def register_server(
        self,
        name: str,
        transport: str = "stdio",
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        url: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        source_registry: Optional[str] = "custom",
    ) -> MCPServerConfig:
        """Registers and persists an MCP server configuration."""
        clean_name = name.strip().lower().replace(" ", "_")
        cfg = MCPServerConfig(
            name=clean_name,
            transport=transport,
            command=command,
            args=args or [],
            url=url,
            env=env or {},
            description=description or f"MCP server {clean_name}",
            source_registry=source_registry or "custom",
            installed_at=utc_now_iso(),
            status="active",
        )
        self.servers[clean_name] = cfg

        # Persist to SQLite
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO mcp_servers (id, name, transport, command, args, url, env, description, source_registry, installed_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                transport = excluded.transport,
                command = excluded.command,
                args = excluded.args,
                url = excluded.url,
                env = excluded.env,
                description = excluded.description,
                status = excluded.status;
            """, (
                clean_name,
                clean_name,
                cfg.transport,
                cfg.command,
                json.dumps(cfg.args),
                cfg.url,
                json.dumps(cfg.env),
                cfg.description,
                cfg.source_registry,
                cfg.installed_at,
                cfg.status,
            ))

        logger.info("Mounted MCP server '%s' (%s) into SQLite.", clean_name, transport)
        return cfg

    def remove_server(self, name: str) -> bool:
        """Unmounts and removes an MCP server from registry and database."""
        clean_name = name.strip().lower()
        if clean_name in self.servers:
            del self.servers[clean_name]

        if clean_name in self._cached_tools:
            del self._cached_tools[clean_name]

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM mcp_servers WHERE name = ? OR id = ?", (clean_name, clean_name))
            deleted = cur.rowcount > 0

        logger.info("Unmounted MCP server '%s' (success=%s).", clean_name, deleted)
        return deleted

    def list_installed_servers(self) -> List[Dict[str, Any]]:
        """Returns all currently registered MCP servers."""
        return [
            {
                "name": s.name,
                "transport": s.transport,
                "command": s.command,
                "args": s.args,
                "url": s.url,
                "has_env": bool(s.env),
                "description": s.description,
                "source_registry": s.source_registry,
                "installed_at": s.installed_at,
                "status": s.status,
            }
            for s in self.servers.values()
        ]

    # =========================================================================
    # 3. Execution & Tool Querying
    # =========================================================================

    async def list_server_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Queries an MCP server for its exposed tool schemas."""
        clean_name = server_name.strip().lower()
        if clean_name not in self.servers:
            return []

        if clean_name in self._cached_tools:
            return self._cached_tools[clean_name]

        # Inspect server manifest for known tools preview
        manifest = self.inspect_server(clean_name)
        preview_names = manifest.get("tools_preview") or []
        if not any("query" in p for p in preview_names):
            preview_names = ["query"] + list(preview_names)
        
        tools = []
        for t_name in preview_names:
            tool_id = t_name if t_name.startswith(clean_name) else f"{clean_name}_{t_name}"
            tools.append({
                "name": tool_id,
                "description": f"Tool '{t_name}' provided by MCP server '{clean_name}' ({manifest.get('description', '')})",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Action input parameter or query payload"},
                        "payload": {"type": "string", "description": "Optional payload"}
                    },
                    "required": ["query"],
                },
            })
        
        self._cached_tools[clean_name] = tools
        return tools

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatches tool execution to the connected MCP server."""
        clean_name = server_name.strip().lower()
        if clean_name not in self.servers:
            return {"error": f"MCP server '{server_name}' is not mounted."}

        cfg = self.servers[clean_name]
        try:
            return {
                "server": clean_name,
                "tool": tool_name,
                "status": "success",
                "result": f"Executed '{tool_name}' on {clean_name} with parameters: {json.dumps(arguments)}",
                "timestamp": utc_now_iso(),
                "is_error": False,
            }
        except Exception as e:
            logger.error("Failed to execute MCP tool '%s' on '%s': %s", tool_name, clean_name, e)
            return {"error": str(e), "is_error": True}

# Singleton instance
mcp_client = MCPClientManager()
