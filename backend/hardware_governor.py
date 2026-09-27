"""
OpenJarvis Local-First Hardware & Cost Governor for MaxIM.
Repository reference: https://github.com/open-jarvis/OpenJarvis

Features:
1. Real-time Hardware Telemetry (CPU, RAM, GPU VRAM via nvidia-smi/WMI/psutil).
2. Local LLM Service Discovery (Ollama port 11434 ping and model tag extraction).
3. Cost Governor & Daily Budget Hard Cap (live token expenditure and cost tracking in SQLite).
4. Dynamic Task-Complexity Router (routes routine tasks to free local models when VRAM permits;
   preserves cloud budget for deep reasoning/multimodal work).
"""
import os
import time
import json
import shutil
import sqlite3
import logging
import platform
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from pydantic import BaseModel, Field

import psutil
from config import config

logger = logging.getLogger("maxim.hardware_governor")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def utc_today_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

# =============================================================================
# SUB-CENT COST PRECISION ENGINE (HERMES-STYLE USAGE PRICING)
# =============================================================================
_ZERO = Decimal("0")
_SUBCENT_THRESHOLD = Decimal("0.01")

def format_cost_label(amount: float | Decimal) -> str:
    """
    Cost display label:
    - zero -> "$0.00"
    - sub-cent (< $0.01) -> "~$0.0046" (4 decimal places)
    - sub-cent underflow -> "~$<0.0001" (if rounds to 0.0000 at 4 dp)
    - standard (>= $0.01) -> "~$1.23" (2 decimal places)
    
    Prevents sub-cent expenditures on high-efficiency models (DeepSeek, Groq, Gemini Flash, etc.)
    from misleadingly displaying as $0.00.
    """
    if isinstance(amount, (int, float)):
        dec = Decimal(str(round(amount, 6)))
    else:
        dec = amount

    if dec == _ZERO or dec == Decimal("0.00"):
        return "$0.00"
    if dec < _SUBCENT_THRESHOLD:
        label = f"~${dec:.4f}"
        return label if label != "~$0.0000" else "~$<0.0001"
    return f"~${dec:.2f}"

# =============================================================================
# PRICING TABLE (USD per 1,000,000 tokens)
# =============================================================================
PROVIDER_PRICING: Dict[str, Dict[str, Tuple[float, float]]] = {
    # provider: { model_prefix: (input_per_million, output_per_million) }
    "google": {
        "gemini-2.0-flash": (0.10, 0.40),
        "gemini-2.0-flash-lite": (0.075, 0.30),
        "gemini-1.5-pro": (1.25, 5.00),
        "gemini-2.5-pro": (1.25, 5.00),
        "default": (0.10, 0.40),
    },
    "openai": {
        "gpt-4o": (2.50, 10.00),
        "gpt-4o-mini": (0.15, 0.60),
        "o1": (15.00, 60.00),
        "o3-mini": (1.10, 4.40),
        "default": (2.50, 10.00),
    },
    "deepseek": {
        "deepseek-chat": (0.14, 0.28),
        "deepseek-reasoner": (0.55, 2.19),
        "deepseek-v3": (0.14, 0.28),
        "deepseek-r1": (0.55, 2.19),
        "default": (0.14, 0.28),
    },
    "openrouter": {
        "claude-3.5-sonnet": (3.00, 15.00),
        "llama-3.3-70b": (0.12, 0.30),
        "deepseek-r1": (0.55, 2.19),
        "default": (0.50, 1.50),
    },
    "nous": {
        "hermes-3-llama-3.1-405b": (2.00, 5.00),
        "hermes-3-llama-3.1-70b": (0.60, 1.20),
        "hermes-3-llama-3.1-8b": (0.10, 0.20),
        "default": (0.60, 1.20),
    },
    "anthropic": {
        "claude-3-5-sonnet": (3.00, 15.00),
        "claude-3-5-haiku": (0.80, 4.00),
        "claude-3-opus": (15.00, 75.00),
        "claude-3-7-sonnet": (3.00, 15.00),
        "default": (3.00, 15.00),
    },
    "groq": {
        "llama-3.3-70b": (0.59, 0.79),
        "llama-3.1-8b": (0.05, 0.08),
        "mixtral-8x7b": (0.24, 0.24),
        "gemma2-9b": (0.20, 0.20),
        "default": (0.50, 0.80),
    },
    "mistral": {
        "mistral-large": (2.00, 6.00),
        "mistral-small": (0.20, 0.60),
        "codestral": (0.30, 0.90),
        "ministral-8b": (0.10, 0.10),
        "default": (1.00, 3.00),
    },
    "xai": {
        "grok-2": (2.00, 10.00),
        "grok-beta": (5.00, 15.00),
        "default": (2.00, 10.00),
    },
    "together": {
        "meta-llama-3.1-70b": (0.88, 0.88),
        "meta-llama-3.1-8b": (0.18, 0.18),
        "qwen-2.5-72b": (0.90, 0.90),
        "default": (0.80, 0.80),
    },
    "fireworks": {
        "llama-v3p1-70b": (0.90, 0.90),
        "llama-v3p1-8b": (0.20, 0.20),
        "deepseek-r1": (0.55, 2.19),
        "default": (0.90, 0.90),
    },
    "cerebras": {
        "llama3.1-70b": (0.60, 0.60),
        "llama3.1-8b": (0.10, 0.10),
        "llama3.3-70b": (0.60, 0.60),
        "default": (0.60, 0.60),
    },
    "perplexity": {
        "sonar-pro": (3.00, 15.00),
        "sonar": (1.00, 1.00),
        "default": (1.00, 5.00),
    },
    "cohere": {
        "command-r-plus": (2.50, 10.00),
        "command-r": (0.15, 0.60),
        "default": (0.50, 2.00),
    },
    "sambanova": {
        "meta-llama-3.1-70b": (0.60, 0.60),
        "meta-llama-3.1-8b": (0.10, 0.10),
        "meta-llama-3.3-70b": (0.60, 0.60),
        "default": (0.60, 0.60),
    },
    "azure": {
        "gpt-4o": (2.50, 10.00),
        "gpt-4o-mini": (0.15, 0.60),
        "default": (2.50, 10.00),
    },
    "omniroute": {
        "default": (0.50, 1.50),
    },
    "ollama": {
        "default": (0.00, 0.00),
    },
    "unsloth": {
        "default": (0.00, 0.00),
    },
    "custom": {
        "default": (0.10, 0.40),
    },
}

class HardwareTelemetry(BaseModel):
    timestamp: str = Field(default_factory=utc_now_iso)
    # CPU
    cpu_percent: float = 0.0
    cpu_cores: int = 1
    # System RAM
    ram_total_gb: float = 0.0
    ram_used_gb: float = 0.0
    ram_free_gb: float = 0.0
    ram_percent: float = 0.0
    # GPU / VRAM
    gpu_available: bool = False
    gpu_name: Optional[str] = None
    vram_total_mb: float = 0.0
    vram_used_mb: float = 0.0
    vram_free_mb: float = 0.0
    vram_percent: float = 0.0
    gpu_temperature_c: Optional[int] = None
    gpu_utilization_percent: Optional[int] = None
    # Local LLM Service (Ollama)
    ollama_online: bool = False
    ollama_models: List[str] = Field(default_factory=list)

class CostGovernorSettings(BaseModel):
    daily_budget_usd: float = 1.00
    hard_cap_enabled: bool = True
    auto_downgrade_to_local: bool = True
    prefer_local_first: bool = False
    vram_headroom_threshold_percent: float = 85.0
    updated_at: str = Field(default_factory=utc_now_iso)

class CostLedgerRecord(BaseModel):
    id: Optional[int] = None
    timestamp: str = Field(default_factory=utc_now_iso)
    date_str: str = Field(default_factory=utc_today_date)
    session_id: str = "default_session"
    provider: str = "unknown"
    model: str = "unknown"
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    estimated_savings_usd: float = 0.0
    cost_label: str = "$0.00"
    task_complexity: str = "routine"  # "routine", "complex", "vision", "reasoning"
    routing_decision: str = "cloud_direct"  # "cloud_direct", "local_routed", "budget_downgraded"

class HardwareGovernorEngine:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager to ensure safe SQLite connection release on Windows."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initializes tables for hardware telemetry and cost governance."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cost_governor_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    daily_budget_usd REAL DEFAULT 1.00,
                    hard_cap_enabled INTEGER DEFAULT 1,
                    auto_downgrade_to_local INTEGER DEFAULT 1,
                    prefer_local_first INTEGER DEFAULT 0,
                    vram_headroom_threshold_percent REAL DEFAULT 85.0,
                    updated_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cost_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    date_str TEXT,
                    session_id TEXT,
                    provider TEXT,
                    model TEXT,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    estimated_cost_usd REAL DEFAULT 0.0,
                    estimated_savings_usd REAL DEFAULT 0.0,
                    task_complexity TEXT DEFAULT 'routine',
                    routing_decision TEXT DEFAULT 'cloud_direct'
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cost_ledger_date ON cost_ledger (date_str)")

            # Seed default settings if empty
            cursor.execute("SELECT COUNT(*) FROM cost_governor_settings WHERE id = 1")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO cost_governor_settings (
                        id, daily_budget_usd, hard_cap_enabled, auto_downgrade_to_local,
                        prefer_local_first, vram_headroom_threshold_percent, updated_at
                    ) VALUES (1, 1.00, 1, 1, 0, 85.0, ?)
                """, (utc_now_iso(),))
            conn.commit()

    # =========================================================================
    # 1. HARDWARE TELEMETRY INSPECTION
    # =========================================================================
    def inspect_hardware(self, ping_ollama: bool = True) -> HardwareTelemetry:
        """Collects real-time CPU, RAM, GPU/VRAM, and local Ollama server telemetry."""
        # 1. CPU Telemetry
        cpu_pct = psutil.cpu_percent(interval=None)
        cpu_cores = psutil.cpu_count(logical=True) or 1

        # 2. RAM Telemetry
        vm = psutil.virtual_memory()
        ram_total = round(vm.total / (1024 ** 3), 2)
        ram_used = round(vm.used / (1024 ** 3), 2)
        ram_free = round(vm.available / (1024 ** 3), 2)
        ram_pct = round(vm.percent, 1)

        # 3. GPU & VRAM Telemetry
        gpu_avail = False
        gpu_name = None
        vram_total = 0.0
        vram_used = 0.0
        vram_free = 0.0
        vram_pct = 0.0
        gpu_temp = None
        gpu_util = None

        if shutil.which("nvidia-smi"):
            try:
                cmd = [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu",
                    "--format=csv,noheader,nounits"
                ]
                output = subprocess.check_output(cmd, text=True, timeout=2).strip()
                if output:
                    parts = [p.strip() for p in output.split(",")]
                    if len(parts) >= 6:
                        gpu_avail = True
                        gpu_name = parts[0]
                        vram_total = float(parts[1])
                        vram_used = float(parts[2])
                        vram_free = float(parts[3])
                        gpu_util = int(parts[4]) if parts[4].isdigit() else 0
                        gpu_temp = int(parts[5]) if parts[5].isdigit() else 0
                        if vram_total > 0:
                            vram_pct = round((vram_used / vram_total) * 100, 1)
            except Exception as e:
                logger.debug(f"nvidia-smi telemetry query failed: {e}")

        # 4. Ollama Local Host Inspection
        ollama_online = False
        ollama_models = []
        if ping_ollama:
            try:
                req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "MaxIM-Governor/2.0"})
                with urllib.request.urlopen(req, timeout=0.8) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode())
                        ollama_online = True
                        for m in data.get("models", []):
                            m_name = m.get("name", "")
                            if m_name:
                                ollama_models.append(m_name)
            except Exception:
                ollama_online = False

        return HardwareTelemetry(
            timestamp=utc_now_iso(),
            cpu_percent=cpu_pct,
            cpu_cores=cpu_cores,
            ram_total_gb=ram_total,
            ram_used_gb=ram_used,
            ram_free_gb=ram_free,
            ram_percent=ram_pct,
            gpu_available=gpu_avail,
            gpu_name=gpu_name,
            vram_total_mb=vram_total,
            vram_used_mb=vram_used,
            vram_free_mb=vram_free,
            vram_percent=vram_pct,
            gpu_temperature_c=gpu_temp,
            gpu_utilization_percent=gpu_util,
            ollama_online=ollama_online,
            ollama_models=ollama_models,
        )

    def get_hardware_telemetry(self, ping_ollama: bool = True) -> HardwareTelemetry:
        """Alias for inspect_hardware."""
        return self.inspect_hardware(ping_ollama=ping_ollama)

    def get_daily_cost_summary(self) -> Dict[str, Any]:
        """Alias for get_spend_summary_today."""
        return self.get_spend_summary_today()

    # =========================================================================
    # 2. PRICING & COST COMPUTATION
    # =========================================================================
    @staticmethod
    def calculate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> Tuple[float, float]:
        """
        Calculates estimated cost for the query in USD.
        Also calculates savings compared to baseline GPT-4o pricing.
        Returns (cost_usd, savings_usd).
        """
        p_clean = provider.lower()
        m_clean = model.lower()

        # Provider aliases mapping
        alias_map = {
            "chatgpt": "openai",
            "gemini": "google",
            "claude": "anthropic",
            "grok": "xai",
            "nous-portal": "nous",
            "together-ai": "together",
            "fireworks-ai": "fireworks",
            "cerebras-ai": "cerebras",
            "azure-openai": "azure",
            "azure-foundry": "azure",
        }
        p_clean = alias_map.get(p_clean, p_clean)

        # Local Ollama is always $0.00
        if p_clean == "ollama":
            # Savings compared to baseline GPT-4o ($2.50 / $10.00 per 1M)
            baseline_cost = ((input_tokens / 1_000_000) * 2.50) + ((output_tokens / 1_000_000) * 10.00)
            return (0.00, round(baseline_cost, 6))

        prov_table = PROVIDER_PRICING.get(p_clean, PROVIDER_PRICING["google"])
        rates = prov_table.get("default", (0.10, 0.40))
        for k, r in prov_table.items():
            if k in m_clean:
                rates = r
                break

        in_rate, out_rate = rates
        cost = ((input_tokens / 1_000_000) * in_rate) + ((output_tokens / 1_000_000) * out_rate)
        
        # Calculate savings against GPT-4o flagship
        gpt4o_cost = ((input_tokens / 1_000_000) * 2.50) + ((output_tokens / 1_000_000) * 10.00)
        savings = max(0.0, gpt4o_cost - cost)

        return (round(cost, 6), round(savings, 6))

    @classmethod
    def get_pricing_catalog(cls) -> Dict[str, Any]:
        """Returns full provider pricing catalog and sub-cent precision rules."""
        catalog = {}
        for prov, models in PROVIDER_PRICING.items():
            catalog[prov] = {
                m: {
                    "input_per_million_usd": rates[0],
                    "output_per_million_usd": rates[1],
                    "subcent_supported": True,
                }
                for m, rates in models.items()
            }
        return {
            "subcent_threshold_usd": float(_SUBCENT_THRESHOLD),
            "subcent_precision_decimals": 4,
            "providers": catalog,
        }

    # =========================================================================
    # 3. SETTINGS & BUDGET ENFORCEMENT
    # =========================================================================
    def get_settings(self) -> CostGovernorSettings:
        """Retrieves active cost governor configuration."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cost_governor_settings WHERE id = 1")
            row = cursor.fetchone()
            if not row:
                return CostGovernorSettings()
            return CostGovernorSettings(
                daily_budget_usd=row["daily_budget_usd"],
                hard_cap_enabled=bool(row["hard_cap_enabled"]),
                auto_downgrade_to_local=bool(row["auto_downgrade_to_local"]),
                prefer_local_first=bool(row["prefer_local_first"]),
                vram_headroom_threshold_percent=row["vram_headroom_threshold_percent"],
                updated_at=row["updated_at"] or utc_now_iso(),
            )

    def update_settings(
        self,
        daily_budget_usd: Optional[float] = None,
        hard_cap_enabled: Optional[bool] = None,
        auto_downgrade_to_local: Optional[bool] = None,
        prefer_local_first: Optional[bool] = None,
        vram_headroom_threshold_percent: Optional[float] = None,
    ) -> CostGovernorSettings:
        """Updates governor settings."""
        curr = self.get_settings()
        now = utc_now_iso()

        new_budget = daily_budget_usd if daily_budget_usd is not None else curr.daily_budget_usd
        new_hard_cap = 1 if (hard_cap_enabled if hard_cap_enabled is not None else curr.hard_cap_enabled) else 0
        new_auto_down = 1 if (auto_downgrade_to_local if auto_downgrade_to_local is not None else curr.auto_downgrade_to_local) else 0
        new_local_first = 1 if (prefer_local_first if prefer_local_first is not None else curr.prefer_local_first) else 0
        new_vram_thresh = vram_headroom_threshold_percent if vram_headroom_threshold_percent is not None else curr.vram_headroom_threshold_percent

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE cost_governor_settings SET
                    daily_budget_usd = ?,
                    hard_cap_enabled = ?,
                    auto_downgrade_to_local = ?,
                    prefer_local_first = ?,
                    vram_headroom_threshold_percent = ?,
                    updated_at = ?
                WHERE id = 1
            """, (new_budget, new_hard_cap, new_auto_down, new_local_first, new_vram_thresh, now))
            conn.commit()

        return self.get_settings()

    # =========================================================================
    # 4. COST LEDGER & USAGE TRACKING
    # =========================================================================
    def record_usage(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        session_id: str = "default_session",
        task_complexity: str = "routine",
        routing_decision: str = "cloud_direct",
    ) -> CostLedgerRecord:
        """Records an execution turn in the cost ledger and calculates fees."""
        cost, savings = self.calculate_cost(provider, model, input_tokens, output_tokens)
        total_tokens = input_tokens + output_tokens
        now = utc_now_iso()
        today = utc_today_date()
        label = format_cost_label(cost)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cost_ledger (
                    timestamp, date_str, session_id, provider, model,
                    input_tokens, output_tokens, total_tokens,
                    estimated_cost_usd, estimated_savings_usd,
                    task_complexity, routing_decision
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now, today, session_id, provider.lower(), model,
                input_tokens, output_tokens, total_tokens,
                cost, savings, task_complexity, routing_decision,
            ))
            conn.commit()
            rec_id = cursor.lastrowid

        return CostLedgerRecord(
            id=rec_id,
            timestamp=now,
            date_str=today,
            session_id=session_id,
            provider=provider.lower(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
            estimated_savings_usd=savings,
            cost_label=label,
            task_complexity=task_complexity,
            routing_decision=routing_decision,
        )

    def get_spend_summary_today(self) -> Dict[str, Any]:
        """Calculates today's cumulative spend, tokens, savings, and budget health."""
        today = utc_today_date()
        settings = self.get_settings()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*),
                    COALESCE(SUM(input_tokens), 0),
                    COALESCE(SUM(output_tokens), 0),
                    COALESCE(SUM(total_tokens), 0),
                    COALESCE(SUM(estimated_cost_usd), 0.0),
                    COALESCE(SUM(estimated_savings_usd), 0.0)
                FROM cost_ledger
                WHERE date_str = ?
            """, (today,))
            turns, in_tok, out_tok, tot_tok, cost_sum, sav_sum = cursor.fetchone()

            # Breakdown by provider
            cursor.execute("""
                SELECT provider, COUNT(*), COALESCE(SUM(total_tokens), 0), COALESCE(SUM(estimated_cost_usd), 0.0)
                FROM cost_ledger
                WHERE date_str = ?
                GROUP BY provider
            """, (today,))
            by_prov = [
                {
                    "provider": r[0],
                    "turns": r[1],
                    "tokens": r[2],
                    "cost_usd": round(r[3], 4),
                    "cost_label": format_cost_label(r[3]),
                }
                for r in cursor.fetchall()
            ]

        budget = settings.daily_budget_usd
        used_pct = round((cost_sum / budget) * 100, 1) if budget > 0 else 0.0
        remaining_usd = max(0.0, round(budget - cost_sum, 4))
        cap_exceeded = (cost_sum >= budget) and settings.hard_cap_enabled

        return {
            "date": today,
            "total_turns": turns,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "total_tokens": tot_tok,
            "spend_today_usd": round(cost_sum, 4),
            "spend_today_label": format_cost_label(cost_sum),
            "savings_today_usd": round(sav_sum, 4),
            "savings_today_label": format_cost_label(sav_sum),
            "daily_budget_usd": budget,
            "remaining_budget_usd": remaining_usd,
            "budget_used_percent": used_pct,
            "hard_cap_exceeded": cap_exceeded,
            "auto_downgrade_active": cap_exceeded and settings.auto_downgrade_to_local,
            "by_provider": by_prov,
        }

    def get_recent_ledger(self, limit: int = 30) -> List[CostLedgerRecord]:
        """Retrieves recent cost ledger entries."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cost_ledger ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            records = []
            for r in rows:
                d = dict(r)
                d["cost_label"] = format_cost_label(d.get("estimated_cost_usd", 0.0))
                records.append(CostLedgerRecord(**d))
            return records

    # =========================================================================
    # 5. DYNAMIC LOCAL-FIRST TASK ROUTER
    # =========================================================================
    def evaluate_routing(
        self,
        task_complexity: str = "routine",  # "routine", "complex", "vision", "reasoning"
        prompt_length: int = 100,
        requested_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        OpenJarvis Smart Routing Decision:
        - If budget hard cap is hit -> Auto-downgrade to local Ollama if online.
        - If prefer_local_first and task is routine and VRAM has headroom -> route to Ollama ($0.00).
        - If task is complex/reasoning/vision -> route to best cloud model.
        """
        settings = self.get_settings()
        spend = self.get_spend_summary_today()
        telemetry = self.inspect_hardware(ping_ollama=True)

        vram_ok = (not telemetry.gpu_available) or (telemetry.vram_percent < settings.vram_headroom_threshold_percent)
        local_viable = telemetry.ollama_online and vram_ok

        # 1. Budget Hard Cap Exceeded
        if spend["hard_cap_exceeded"]:
            if local_viable and settings.auto_downgrade_to_local:
                return {
                    "decision": "budget_downgraded",
                    "target_provider": "ollama",
                    "target_model": telemetry.ollama_models[0] if telemetry.ollama_models else "llama3.2",
                    "reason": f"Daily budget of ${settings.daily_budget_usd:.2f} reached. Auto-downgrading to local Ollama ($0.00) to protect your wallet.",
                    "hardware_vram_percent": telemetry.vram_percent,
                    "ollama_online": True,
                }
            elif not local_viable and settings.hard_cap_enabled:
                return {
                    "decision": "budget_halted",
                    "target_provider": requested_provider or "google",
                    "target_model": "gemini-2.0-flash",
                    "reason": f"Budget limit of ${settings.daily_budget_usd:.2f} reached and local Ollama is unavailable. Please approve extra budget.",
                    "hardware_vram_percent": telemetry.vram_percent,
                    "ollama_online": False,
                }

        # 2. Prefer Local-First or Routine Task
        is_routine = task_complexity == "routine" and prompt_length < 800
        if (settings.prefer_local_first or is_routine) and local_viable:
            return {
                "decision": "local_routed",
                "target_provider": "ollama",
                "target_model": telemetry.ollama_models[0] if telemetry.ollama_models else "llama3.2",
                "reason": f"Routing routine task to local Ollama GPU ({telemetry.gpu_name or 'Local CPU'}) at $0.00 cost.",
                "hardware_vram_percent": telemetry.vram_percent,
                "ollama_online": True,
            }

        # 3. Cloud Direct Execution
        return {
            "decision": "cloud_direct",
            "target_provider": requested_provider or "google",
            "target_model": "gemini-2.0-flash",
            "reason": "Routing to cloud provider for high-speed multi-modal / complex reasoning.",
            "hardware_vram_percent": telemetry.vram_percent,
            "ollama_online": telemetry.ollama_online,
        }

    # =========================================================================
    # 5. OS HARDWARE DISPATCHERS (VOLUME, BRIGHTNESS, BROWSER, WI-FI)
    # =========================================================================

    def adjust_master_volume(self, action: str = "up", steps: int = 1) -> Dict[str, Any]:
        """
        Nudges or mutes master system audio volume.
        action: 'up', 'down', or 'mute'
        Uses direct Windows keybd_event API for 0ms latency.
        """
        if platform.system() != "Windows":
            return {"status": "unsupported", "platform": platform.system()}

        import ctypes
        user32 = ctypes.windll.user32
        VK_VOLUME_MUTE = 0xAD
        VK_VOLUME_DOWN = 0xAE
        VK_VOLUME_UP = 0xAF
        KEYEVENTF_KEYUP = 0x0002

        act = action.lower().strip()
        if act in ["up", "volume_up", "raise"]:
            vk = VK_VOLUME_UP
        elif act in ["down", "volume_down", "lower"]:
            vk = VK_VOLUME_DOWN
        elif act in ["mute", "toggle_mute", "unmute"]:
            vk = VK_VOLUME_MUTE
            steps = 1
        else:
            return {"status": "error", "message": f"Unsupported volume action: {action}. Use 'up', 'down', or 'mute'."}

        clamped_steps = max(1, min(50, int(steps)))
        for _ in range(clamped_steps):
            user32.keybd_event(vk, 0, 0, 0)
            time.sleep(0.01)
            user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.02)

        return {"status": "success", "action": act, "steps": clamped_steps}

    def get_screen_brightness(self) -> Dict[str, Any]:
        """Reads primary display brightness percentage via Windows WMI."""
        if platform.system() != "Windows":
            return {"status": "unsupported", "platform": platform.system()}

        try:
            cmd = [
                "powershell", "-NoProfile", "-Command",
                "(Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightness -ErrorAction SilentlyContinue).CurrentBrightness"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            val = res.stdout.strip()
            if val.isdigit():
                return {"status": "success", "brightness_percent": int(val)}
            return {"status": "unavailable", "message": "WmiMonitorBrightness not supported (e.g. desktop monitor or external display)."}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def set_screen_brightness(self, level_percent: int) -> Dict[str, Any]:
        """Sets display brightness (0-100) via Windows WMI."""
        if platform.system() != "Windows":
            return {"status": "unsupported", "platform": platform.system()}

        level = max(0, min(100, int(level_percent)))
        try:
            cmd = [
                "powershell", "-NoProfile", "-Command",
                f"(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods -ErrorAction SilentlyContinue).WmiSetBrightness(1, {level})"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                return {"status": "success", "target_brightness_percent": level}
            return {"status": "error", "message": res.stderr.strip() or "Failed to set brightness via WMI"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_default_browser(self) -> Dict[str, Any]:
        """Detects user's primary default browser via Windows UserChoice ProgId registry key."""
        if platform.system() != "Windows":
            return {"status": "unsupported", "platform": platform.system()}

        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice",
            )
            prog_id, _ = winreg.QueryValueEx(key, "ProgId")
            winreg.CloseKey(key)

            name = "Unknown"
            prog_lower = prog_id.lower()
            if "chrome" in prog_lower:
                name = "Google Chrome"
            elif "edge" in prog_lower:
                name = "Microsoft Edge"
            elif "brave" in prog_lower:
                name = "Brave Browser"
            elif "firefox" in prog_lower:
                name = "Mozilla Firefox"
            elif "opera" in prog_lower:
                name = "Opera"

            return {"status": "success", "prog_id": prog_id, "browser_name": name}
        except Exception as e:
            return {"status": "error", "error": str(e), "browser_name": "Unknown"}

    def get_wifi_status(self) -> Dict[str, Any]:
        """Retrieves active Wi-Fi adapter connection state and telemetry via netsh."""
        if platform.system() != "Windows":
            return {"status": "unsupported", "platform": platform.system()}

        try:
            res = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=5)
            lines = res.stdout.splitlines()
            info = {}
            for line in lines:
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip()
                    if k in ["Name", "State", "SSID", "Signal", "Radio type", "Description"]:
                        info[k.lower().replace(" ", "_")] = v
            return {"status": "success", "wifi": info}
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Singleton instance
hardware_governor = HardwareGovernorEngine()
