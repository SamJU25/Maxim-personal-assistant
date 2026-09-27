"""
Cursor & Agent Plugin Ecosystem Adapter for MaxIM.
Adapted from cursor/plugins standard architecture.
Parses, validates, imports, and registers Cursor plugins (plugin.json),
exposing their Rules, Skills, and MCP servers directly to MaxIM's tool catalog.
Repository reference: https://github.com/cursor/plugins
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

DEFAULT_CURSOR_PLUGINS = [
    {
        "id": "plugin_cursor_devtools",
        "name": "Cursor Essential DevTools",
        "version": "1.0.0",
        "description": "Standard software craftsmanship rules, git hygiene, and defensive testing contracts.",
        "author": "Cursor Community",
        "rules": [
            "Always verify with tests before marking work complete.",
            "Maintain minimal diffs; clean up temporary artifacts."
        ],
        "skills": ["git-workflow", "code-quality-guardian"],
        "mcpServers": {}
    }
]

class CursorPluginEngine:
    def __init__(self, db_path: Optional[Path] = None, plugins_dir: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self.plugins_dir = plugins_dir or (config.base_dir / ".agents" / "plugins")
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
            CREATE TABLE IF NOT EXISTS cursor_plugins (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                description TEXT,
                author TEXT,
                manifest_json TEXT NOT NULL,
                rules_count INTEGER DEFAULT 0,
                skills_count INTEGER DEFAULT 0,
                mcp_servers_count INTEGER DEFAULT 0,
                is_enabled INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cursor_plugins")
            if cursor.fetchone()[0] == 0:
                now = utc_now_iso()
                for p in DEFAULT_CURSOR_PLUGINS:
                    cursor.execute("""
                    INSERT INTO cursor_plugins (id, name, version, description, author, manifest_json, rules_count, skills_count, mcp_servers_count, is_enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    """, (
                        p["id"],
                        p["name"],
                        p["version"],
                        p["description"],
                        p["author"],
                        json.dumps(p),
                        len(p.get("rules", [])),
                        len(p.get("skills", [])),
                        len(p.get("mcpServers", {})),
                        now,
                        now
                    ))
                conn.commit()

    def validate_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Validates the structure of a Cursor plugin.json manifest."""
        errors = []
        if not manifest.get("name"):
            errors.append("Manifest is missing required field: 'name'")
        if not manifest.get("version"):
            errors.append("Manifest is missing required field: 'version'")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "name": manifest.get("name"),
            "version": manifest.get("version"),
            "rules_count": len(manifest.get("rules", [])),
            "skills_count": len(manifest.get("skills", [])),
            "mcp_count": len(manifest.get("mcpServers", {}))
        }

    def import_plugin(self, manifest_data: Any) -> Dict[str, Any]:
        """
        Imports a Cursor plugin manifest (either path string or raw dictionary),
        validates its rules/skills/mcp servers, and registers it into SQLite.
        """
        if isinstance(manifest_data, (str, Path)):
            p_path = Path(manifest_data)
            if not p_path.is_file():
                raise FileNotFoundError(f"Plugin manifest file '{manifest_data}' not found.")
            manifest = json.loads(p_path.read_text(encoding="utf-8"))
        elif isinstance(manifest_data, dict):
            manifest = manifest_data
        else:
            raise ValueError("manifest_data must be a file path or dict.")

        val = self.validate_manifest(manifest)
        if not val["valid"]:
            raise ValueError(f"Invalid plugin manifest: {', '.join(val['errors'])}")

        plugin_id = manifest.get("id") or f"plugin_{uuid.uuid4().hex[:8]}"
        now = utc_now_iso()

        rules = manifest.get("rules", [])
        skills = manifest.get("skills", [])
        mcp_servers = manifest.get("mcpServers", {})

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO cursor_plugins (id, name, version, description, author, manifest_json, rules_count, skills_count, mcp_servers_count, is_enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                version = excluded.version,
                description = excluded.description,
                manifest_json = excluded.manifest_json,
                rules_count = excluded.rules_count,
                skills_count = excluded.skills_count,
                mcp_servers_count = excluded.mcp_servers_count,
                updated_at = excluded.updated_at
            """, (
                plugin_id,
                manifest["name"],
                manifest["version"],
                manifest.get("description", ""),
                manifest.get("author", "Community"),
                json.dumps(manifest),
                len(rules),
                len(skills),
                len(mcp_servers),
                now,
                now
            ))
            conn.commit()

        return {
            "id": plugin_id,
            "name": manifest["name"],
            "version": manifest["version"],
            "rules_count": len(rules),
            "skills_count": len(skills),
            "mcp_servers_count": len(mcp_servers),
            "status": "imported",
            "created_at": now
        }

    def list_installed_plugins(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cursor_plugins ORDER BY name ASC")
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["manifest"] = json.loads(item["manifest_json"])
                item["is_enabled"] = bool(item["is_enabled"])
                del item["manifest_json"]
                results.append(item)
            return results

    def toggle_plugin(self, plugin_id: str, enabled: bool) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE cursor_plugins SET is_enabled = ?, updated_at = ? WHERE id = ?", (1 if enabled else 0, utc_now_iso(), plugin_id))
            conn.commit()
            return cursor.rowcount > 0

# Singleton instance
cursor_plugins = CursorPluginEngine()
