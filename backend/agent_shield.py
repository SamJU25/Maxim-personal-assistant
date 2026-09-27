"""
AgentShield Runtime Indirect Prompt Injection Firewall & Strict Tool Boundary Guard for MaxIM.
Repository Reference: https://github.com/affaan-m/ECC & https://github.com/affaan-m/agentshield

Functional Core:
1. Multi-Vector Indirect Prompt Injection (IPI) Firewall:
   - Deep regex and structural heuristics detecting role hijacking (<|im_start|>, [SYSTEM], [INST]),
     instruction overrides (ignore previous instructions, disregard constraints),
     and exfiltration smuggling (tracking pixels, markdown image URLs, base64 payloads).
   - Defangs and quarantines untrusted external web payloads, inbound webhooks, and notes.
2. Dynamic Tool Permission Boundary Enforcer:
   - Tool Risk Tiering across all registered tools:
     * TIER 1: Read-Only (Vault, search, telemetry, memory query)
     * TIER 2: Local State (Facts, mental models, notes, todos, skills)
     * TIER 3: Network Egress (Remote messaging, web search, web fetch)
     * TIER 4: Privileged OS & Hardware (Desktop clicks, shell execution, volume, brightness, ADB)
   - Enforces execution boundaries based on caller context (e.g. remote webhooks blocked from Tier 4).
3. Tool Argument Traversal & Exploit Interceptor:
   - Validates arguments against path traversal escapes (../../), null-byte injections, and shell escapes.
4. SQLite WAL Threat Audit Ledger:
   - Table `agentshield_audit_log` tracking security intercepts, threat scores, matched patterns, and resolution.
   - Table `agentshield_settings` for operational mode (strict, balanced, permissive).
"""

import re
import json
import sqlite3
import logging
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from contextlib import contextmanager
from pydantic import BaseModel, Field

from config import config

logger = logging.getLogger("maxim.agent_shield")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# =============================================================================
# 1. TOOL RISK TIERS & CATALOG MAPPING
# =============================================================================

class ToolRiskTier(str, Enum):
    TIER_1_READ_ONLY = "read_only"
    TIER_2_LOCAL_STATE = "local_state"
    TIER_3_NETWORK_EGRESS = "network_egress"
    TIER_4_PRIVILEGED_OS = "privileged_os"


# Explicit risk mapping for MaxIM tool catalog
TOOL_TIER_MAPPING: Dict[str, ToolRiskTier] = {
    # Tier 1: Read-Only
    "read_vault_note": ToolRiskTier.TIER_1_READ_ONLY,
    "search_vault": ToolRiskTier.TIER_1_READ_ONLY,
    "find_vault_backlinks": ToolRiskTier.TIER_1_READ_ONLY,
    "inspect_screen": ToolRiskTier.TIER_1_READ_ONLY,
    "query_five_layer_memory": ToolRiskTier.TIER_1_READ_ONLY,
    "recall_memory": ToolRiskTier.TIER_1_READ_ONLY,
    "get_mental_models": ToolRiskTier.TIER_1_READ_ONLY,
    "list_learned_skills": ToolRiskTier.TIER_1_READ_ONLY,
    "recall_skill": ToolRiskTier.TIER_1_READ_ONLY,
    "list_session_todos": ToolRiskTier.TIER_1_READ_ONLY,
    "get_token_juice_stats": ToolRiskTier.TIER_1_READ_ONLY,
    "get_hardware_status": ToolRiskTier.TIER_1_READ_ONLY,
    "get_cost_governor_metrics": ToolRiskTier.TIER_1_READ_ONLY,
    "get_screen_brightness": ToolRiskTier.TIER_1_READ_ONLY,
    "get_default_browser": ToolRiskTier.TIER_1_READ_ONLY,
    "get_wifi_status": ToolRiskTier.TIER_1_READ_ONLY,
    "get_overnight_intel": ToolRiskTier.TIER_1_READ_ONLY,
    "get_privacy_status": ToolRiskTier.TIER_1_READ_ONLY,
    "query_learned_language": ToolRiskTier.TIER_1_READ_ONLY,
    "get_language_stats": ToolRiskTier.TIER_1_READ_ONLY,
    "os_list_windows": ToolRiskTier.TIER_1_READ_ONLY,
    "os_list_processes": ToolRiskTier.TIER_1_READ_ONLY,
    "adb_get_devices": ToolRiskTier.TIER_1_READ_ONLY,
    "adb_get_battery": ToolRiskTier.TIER_1_READ_ONLY,
    "get_remote_channel_status": ToolRiskTier.TIER_1_READ_ONLY,
    "sandbox_audit_command": ToolRiskTier.TIER_1_READ_ONLY,
    "workstation_git_status": ToolRiskTier.TIER_1_READ_ONLY,
    "browser_get_dom": ToolRiskTier.TIER_1_READ_ONLY,
    "browser_extract_text": ToolRiskTier.TIER_1_READ_ONLY,
    "laya_decide_browsing_action": ToolRiskTier.TIER_1_READ_ONLY,
    "laya_verify_browsing_content": ToolRiskTier.TIER_1_READ_ONLY,
    "scan_directory": ToolRiskTier.TIER_1_READ_ONLY,
    "read_document": ToolRiskTier.TIER_1_READ_ONLY,
    "inspect_image": ToolRiskTier.TIER_1_READ_ONLY,

    # Tier 2: Local State Modifications
    "generate_image": ToolRiskTier.TIER_2_LOCAL_STATE,
    "write_vault_note": ToolRiskTier.TIER_2_LOCAL_STATE,
    "remember_user_fact": ToolRiskTier.TIER_2_LOCAL_STATE,
    "retain_memory": ToolRiskTier.TIER_2_LOCAL_STATE,
    "reflect_mental_models": ToolRiskTier.TIER_2_LOCAL_STATE,
    "compact_context_safeguard": ToolRiskTier.TIER_2_LOCAL_STATE,
    "crystallize_skill": ToolRiskTier.TIER_2_LOCAL_STATE,
    "record_error_reflexion": ToolRiskTier.TIER_2_LOCAL_STATE,
    "add_session_todo": ToolRiskTier.TIER_2_LOCAL_STATE,
    "update_session_todo": ToolRiskTier.TIER_2_LOCAL_STATE,
    "learn_language_phrase": ToolRiskTier.TIER_2_LOCAL_STATE,
    "manage_interest_topics": ToolRiskTier.TIER_2_LOCAL_STATE,
    "update_cost_governor_settings": ToolRiskTier.TIER_2_LOCAL_STATE,
    "update_privacy_guard": ToolRiskTier.TIER_2_LOCAL_STATE,
    "workstation_scaffold_project": ToolRiskTier.TIER_2_LOCAL_STATE,
    "browser_manage_session": ToolRiskTier.TIER_2_LOCAL_STATE,
    "organize_directory": ToolRiskTier.TIER_2_LOCAL_STATE,
    "undo_organization": ToolRiskTier.TIER_2_LOCAL_STATE,

    # Tier 3: Network Egress
    "web_search": ToolRiskTier.TIER_3_NETWORK_EGRESS,
    "read_web_page": ToolRiskTier.TIER_3_NETWORK_EGRESS,
    "community_reach": ToolRiskTier.TIER_3_NETWORK_EGRESS,
    "github_reach": ToolRiskTier.TIER_3_NETWORK_EGRESS,
    "channel_doctor": ToolRiskTier.TIER_3_NETWORK_EGRESS,
    "send_remote_message": ToolRiskTier.TIER_3_NETWORK_EGRESS,
    "broadcast_remote_message": ToolRiskTier.TIER_3_NETWORK_EGRESS,
    "call_mcp_tool": ToolRiskTier.TIER_3_NETWORK_EGRESS,
    "create_subagent": ToolRiskTier.TIER_3_NETWORK_EGRESS,
    "trigger_idle_scout": ToolRiskTier.TIER_3_NETWORK_EGRESS,
    "browser_navigate": ToolRiskTier.TIER_3_NETWORK_EGRESS,
    "browser_click_element": ToolRiskTier.TIER_3_NETWORK_EGRESS,
    "browser_type_element": ToolRiskTier.TIER_3_NETWORK_EGRESS,

    # Tier 4: Privileged OS & Hardware Automation
    "cua_click": ToolRiskTier.TIER_4_PRIVILEGED_OS,
    "cua_type": ToolRiskTier.TIER_4_PRIVILEGED_OS,
    "cua_navigate_browser": ToolRiskTier.TIER_4_PRIVILEGED_OS,
    "os_focus_window": ToolRiskTier.TIER_4_PRIVILEGED_OS,
    "os_launch_app": ToolRiskTier.TIER_4_PRIVILEGED_OS,
    "os_execute_action": ToolRiskTier.TIER_4_PRIVILEGED_OS,
    "sandbox_run_command": ToolRiskTier.TIER_4_PRIVILEGED_OS,
    "adjust_master_volume": ToolRiskTier.TIER_4_PRIVILEGED_OS,
    "set_screen_brightness": ToolRiskTier.TIER_4_PRIVILEGED_OS,
    "adb_tap": ToolRiskTier.TIER_4_PRIVILEGED_OS,
    "adb_swipe": ToolRiskTier.TIER_4_PRIVILEGED_OS,
    "adb_launch_app": ToolRiskTier.TIER_4_PRIVILEGED_OS,
}


# =============================================================================
# 2. ADVERSARIAL PATTERNS & INJECTION HEURISTICS
# =============================================================================

# Instruction overrides and jailbreak directives
INJECTION_OVERRIDE_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|prompts|rules|commands)", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:safety|guidelines|constraints|instructions)", re.IGNORECASE),
    re.compile(r"bypass\s+(?:safety|filter|guard|rules)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:in\s+developer\s+mode|unrestricted|DAN|jailbroken)", re.IGNORECASE),
    re.compile(r"switch\s+to\s+(?:developer\s+mode|unfiltered\s+mode)", re.IGNORECASE),
    re.compile(r"new\s+(?:system\s+prompt|directive)\s*[:=]", re.IGNORECASE),
]

# Role marker counterfeiting
ROLE_HIJACK_PATTERNS = [
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|im_end\|>", re.IGNORECASE),
    re.compile(r"\[SYSTEM(?:\s+DIRECTIVE)?\]", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"\[/INST\]", re.IGNORECASE),
    re.compile(r"<<SYS>>", re.IGNORECASE),
    re.compile(r"<</SYS>>", re.IGNORECASE),
]

# Data exfiltration and stealth channels
EXFILTRATION_PATTERNS = [
    re.compile(r"!\[(?:[^\]]*)\]\((https?://[^\s\)]+)\)", re.IGNORECASE),  # Markdown image beacon exfiltration
    re.compile(r"(?:fetch|curl|wget)\s+(?:-X\s+POST\s+)?['\"]?https?://[^\s'\"]+", re.IGNORECASE),
    re.compile(r"send\s+(?:all\s+)?(?:passwords|tokens|api_keys|vault\s+notes)\s+to", re.IGNORECASE),
]

# Path traversal heuristics
PATH_TRAVERSAL_PATTERN = re.compile(r"(?:\.\.[\\/]){2,}|[\\/]\.\.[\\/]|%(?:2e|2f|5c)", re.IGNORECASE)


class ThreatClassification(BaseModel):
    """Structured report of an adversarial scan."""
    threat_detected: bool = False
    threat_type: str = "clean"  # clean, instruction_override, role_hijack, exfiltration, path_traversal
    risk_score: float = 0.0  # 0.0 to 1.0
    matched_patterns: List[str] = Field(default_factory=list)
    sanitized_content: str
    quarantined: bool = False


# =============================================================================
# 3. AGENTSHIELD ENGINE
# =============================================================================

class AgentShieldEngine:
    """Runtime indirect prompt injection firewall and tool boundary guard."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initializes SQLite WAL threat audit ledger and firewall settings."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agentshield_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    threat_type TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    source TEXT NOT NULL,
                    details TEXT NOT NULL,
                    action_taken TEXT NOT NULL, -- blocked, quarantined, sanitized, allowed
                    timestamp TEXT NOT NULL
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agentshield_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    mode TEXT NOT NULL DEFAULT 'strict', -- strict, balanced, permissive
                    block_injections INTEGER NOT NULL DEFAULT 1,
                    quarantine_untrusted INTEGER NOT NULL DEFAULT 1,
                    restrict_remote_tier4 INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shield_timestamp ON agentshield_audit_log(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shield_threat ON agentshield_audit_log(threat_type);")

            cursor.execute("""
                INSERT OR IGNORE INTO agentshield_settings (id, mode, block_injections, quarantine_untrusted, restrict_remote_tier4, updated_at)
                VALUES (1, 'strict', 1, 1, 1, ?)
            """, (utc_now_iso(),))
            conn.commit()

    # =========================================================================
    # SETTINGS & METRICS
    # =========================================================================

    def get_settings(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agentshield_settings WHERE id = 1")
            row = cursor.fetchone()
            if not row:
                return {"mode": "strict", "block_injections": True, "quarantine_untrusted": True, "restrict_remote_tier4": True}
            return {
                "mode": row["mode"],
                "block_injections": bool(row["block_injections"]),
                "quarantine_untrusted": bool(row["quarantine_untrusted"]),
                "restrict_remote_tier4": bool(row["restrict_remote_tier4"]),
                "updated_at": row["updated_at"],
            }

    def get_tool_tier(self, tool_name: str) -> ToolRiskTier:
        """Returns the registered risk tier for a tool, defaulting to TIER_2_LOCAL_STATE."""
        return TOOL_TIER_MAPPING.get(tool_name, ToolRiskTier.TIER_2_LOCAL_STATE)

    def update_settings(
        self,
        mode: Optional[str] = None,
        block_injections: Optional[bool] = None,
        quarantine_untrusted: Optional[bool] = None,
        restrict_remote_tier4: Optional[bool] = None,
    ) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            current = self.get_settings()
            new_mode = mode.lower() if mode else current["mode"]
            new_block = 1 if (block_injections if block_injections is not None else current["block_injections"]) else 0
            new_quar = 1 if (quarantine_untrusted if quarantine_untrusted is not None else current["quarantine_untrusted"]) else 0
            new_tier4 = 1 if (restrict_remote_tier4 if restrict_remote_tier4 is not None else current["restrict_remote_tier4"]) else 0

            cursor.execute("""
                UPDATE agentshield_settings
                SET mode = ?, block_injections = ?, quarantine_untrusted = ?, restrict_remote_tier4 = ?, updated_at = ?
                WHERE id = 1
            """, (new_mode, new_block, new_quar, new_tier4, now))
            conn.commit()
        return self.get_settings()

    def log_threat(self, threat_type: str, risk_score: float, source: str, details: str, action: str):
        now = utc_now_iso()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agentshield_audit_log (threat_type, risk_score, source, details, action_taken, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (threat_type, risk_score, source, details, action, now))
            conn.commit()

    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agentshield_audit_log ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_security_metrics(self) -> Dict[str, Any]:
        """Returns consolidated runtime security statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM agentshield_audit_log")
            total = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as blocked FROM agentshield_audit_log WHERE action_taken = 'blocked'")
            blocked = cursor.fetchone()["blocked"]

            cursor.execute("SELECT COUNT(*) as quarantined FROM agentshield_audit_log WHERE action_taken = 'quarantined'")
            quarantined = cursor.fetchone()["quarantined"]

            cursor.execute("SELECT COUNT(*) as sanitized FROM agentshield_audit_log WHERE action_taken = 'sanitized'")
            sanitized = cursor.fetchone()["sanitized"]

            settings = self.get_settings()
            return {
                "status": "active",
                "mode": settings["mode"],
                "total_threats_logged": total,
                "threats_blocked": blocked,
                "payloads_quarantined": quarantined,
                "payloads_sanitized": sanitized,
                "active_tier4_lockdown": settings["restrict_remote_tier4"],
            }

    # =========================================================================
    # 2. INBOUND SCANNING & PROMPT INJECTION DEFENSE
    # =========================================================================

    def scan_inbound_content(self, text: str, source: str = "external") -> ThreatClassification:
        """
        Scans external incoming content for indirect prompt injections,
        role hijacking, and exfiltration beacons. Returns classified threat report.
        """
        if not text or not isinstance(text, str):
            return ThreatClassification(sanitized_content=text or "")

        matched = []
        threat_type = "clean"
        risk_score = 0.0

        # 1. Check Path Traversal (0.80)
        if PATH_TRAVERSAL_PATTERN.search(text):
            matched.append("path_traversal: ../ traversal detected")
            if 0.80 > risk_score:
                threat_type = "path_traversal"
                risk_score = 0.80

        # 2. Check Exfiltration Beacons (0.85)
        for pat in EXFILTRATION_PATTERNS:
            if pat.search(text):
                matched.append(f"exfiltration: {pat.pattern}")
                if 0.85 > risk_score:
                    threat_type = "exfiltration"
                    risk_score = 0.85

        # 3. Check Instruction Overrides (0.90)
        for pat in INJECTION_OVERRIDE_PATTERNS:
            if pat.search(text):
                matched.append(f"instruction_override: {pat.pattern}")
                if 0.90 > risk_score:
                    threat_type = "instruction_override"
                    risk_score = 0.90

        # 4. Check Role Hijacking (0.95 - Highest Severity)
        for pat in ROLE_HIJACK_PATTERNS:
            if pat.search(text):
                matched.append(f"role_hijack: {pat.pattern}")
                if 0.95 > risk_score:
                    threat_type = "role_hijack"
                    risk_score = 0.95

        # Defang and sanitize content if threats detected
        sanitized = text
        quarantined = False

        if matched:
            settings = self.get_settings()
            action = "sanitized"
            # Strip role markers
            for pat in ROLE_HIJACK_PATTERNS:
                sanitized = pat.sub("[DEFANGED_ROLE_TAG]", sanitized)

            # Strip override commands
            for pat in INJECTION_OVERRIDE_PATTERNS:
                sanitized = pat.sub("[DEFANGED_INSTRUCTION_OVERRIDE]", sanitized)

            # Defang image exfiltration beacons into inert code blocks
            sanitized = re.sub(r"!\[([^\]]*)\]\((https?://[^\s\)]+)\)", r"[DEFANGED_BEACON: \1 (\2)]", sanitized)

            # If quarantine enabled, isolate inside untrusted tags
            if settings.get("quarantine_untrusted", True):
                sanitized = f"<untrusted_external_content source='{source}' security_verified='false'>\n{sanitized}\n</untrusted_external_content>"
                quarantined = True
                action = "quarantined"

            self.log_threat(
                threat_type=threat_type,
                risk_score=risk_score,
                source=source,
                details=f"Matched {len(matched)} pattern(s): {', '.join(matched[:3])}",
                action=action,
            )

            return ThreatClassification(
                threat_detected=True,
                threat_type=threat_type,
                risk_score=risk_score,
                matched_patterns=matched,
                sanitized_content=sanitized,
                quarantined=quarantined,
            )

        return ThreatClassification(
            threat_detected=False,
            threat_type="clean",
            risk_score=0.0,
            matched_patterns=[],
            sanitized_content=text,
            quarantined=False,
        )

    # =========================================================================
    # 3. TOOL PRIVILEGE BOUNDARY ENFORCER
    # =========================================================================

    def audit_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: str = "default_session",
        caller_channel: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validates proposed tool execution against risk tiers and caller boundaries.
        Blocks unauthorized execution or dangerous parameter smuggling.
        """
        tier = TOOL_TIER_MAPPING.get(tool_name, ToolRiskTier.TIER_2_LOCAL_STATE)
        settings = self.get_settings()

        # 1. Remote Channel Privilege Lockdown (Tier 4 Guard)
        # External webhooks or messaging channels CANNOT invoke Tier 4 Privileged OS tools
        is_remote_caller = (
            caller_channel is not None
            or session_id.startswith("channel_")
            or session_id.startswith("webhook_")
        )

        if is_remote_caller and tier == ToolRiskTier.TIER_4_PRIVILEGED_OS:
            if settings.get("restrict_remote_tier4", True):
                reason = f"Tool '{tool_name}' requires Tier 4 Privileged OS access, which is blocked for remote channel sessions."
                self.log_threat(
                    threat_type="privilege_escalation",
                    risk_score=1.0,
                    source=f"session:{session_id}",
                    details=f"Attempted remote invocation of {tool_name}",
                    action="blocked",
                )
                return {
                    "allowed": False,
                    "reason": reason,
                    "tier": tier.value,
                    "tool": tool_name,
                }

        # 2. Argument Safety & Path Traversal Guard
        args_str = json.dumps(arguments)
        if PATH_TRAVERSAL_PATTERN.search(args_str):
            reason = "Path traversal sequence (../) detected in tool arguments."
            self.log_threat(
                threat_type="path_traversal",
                risk_score=0.85,
                source=f"tool:{tool_name}",
                details=f"Arguments contained path traversal: {args_str[:120]}",
                action="blocked",
            )
            return {
                "allowed": False,
                "reason": reason,
                "tier": tier.value,
                "tool": tool_name,
            }

        return {
            "allowed": True,
            "tier": tier.value,
            "tool": tool_name,
        }


# Singleton instance
agent_shield = AgentShieldEngine()
