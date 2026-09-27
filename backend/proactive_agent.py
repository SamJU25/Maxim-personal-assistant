"""
Proactive Situational Initiative & Real-Time Voice Agent for MaxIM.
Enables non-robotic, situation-grounded conversational initiative:
- Observes active foreground window, screen perception, LifeOS TELOS targets, and idle duration.
- Dynamically formulates context-aware questions and strategic propositions (zero canned/pre-made scripts).
- Manages intervention thresholds (gentle, balanced, proactive, muted) and adaptive cooldowns.
- Synthesizes proactive speech via Edge-TTS and maintains audit history in SQLite.
"""
import asyncio
import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from config import config
from router import model_router
from telos import telos_engine
from tools.screen_tool import get_active_window_info, screen_tool
from memory import memory_store
from chief_operator import agent_operator
from voice import voice_engine

logger = logging.getLogger("maxim.proactive")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class ProactiveSettings(BaseModel):
    mode: str = Field(default="balanced", description="Sensitivity mode: gentle, balanced, proactive, muted")
    auto_speak: bool = Field(default=True, description="Whether to automatically synthesize speech for proactive interjections")
    cooldown_minutes: int = Field(default=8, description="Minimum minutes between proactive interjections")
    last_intervention_time: Optional[str] = None

class ProactiveIntervention(BaseModel):
    id: str = Field(default_factory=lambda: f"interv_{uuid.uuid4().hex[:8]}")
    reason: str
    message: str
    active_window: str
    target_focus: Optional[str] = None
    timestamp: str = Field(default_factory=utc_now_iso)
    spoken: bool = False
    dismissed: bool = False

class ProactiveSituationalAgent:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self._init_tables()
        self._load_settings()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_tables(self):
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS proactive_settings (
                key TEXT PRIMARY KEY,
                mode TEXT NOT NULL,
                auto_speak INTEGER NOT NULL,
                cooldown_minutes INTEGER NOT NULL,
                last_intervention_time TEXT
            );

            CREATE TABLE IF NOT EXISTS proactive_interventions (
                id TEXT PRIMARY KEY,
                reason TEXT NOT NULL,
                message TEXT NOT NULL,
                active_window TEXT NOT NULL,
                target_focus TEXT,
                timestamp TEXT NOT NULL,
                spoken INTEGER DEFAULT 0,
                dismissed INTEGER DEFAULT 0
            );
            """)

    def _load_settings(self) -> ProactiveSettings:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM proactive_settings WHERE key = 'default'")
            r = cur.fetchone()
            if not r:
                s = ProactiveSettings()
                conn.execute("""
                INSERT INTO proactive_settings (key, mode, auto_speak, cooldown_minutes, last_intervention_time)
                VALUES ('default', ?, ?, ?, ?)
                """, (s.mode, 1 if s.auto_speak else 0, s.cooldown_minutes, s.last_intervention_time))
                return s
            return ProactiveSettings(
                mode=r["mode"],
                auto_speak=bool(r["auto_speak"]),
                cooldown_minutes=r["cooldown_minutes"],
                last_intervention_time=r["last_intervention_time"],
            )

    def get_settings(self) -> ProactiveSettings:
        return self._load_settings()

    def update_settings(self, mode: Optional[str] = None, auto_speak: Optional[bool] = None, cooldown_minutes: Optional[int] = None) -> ProactiveSettings:
        s = self.get_settings()
        if mode is not None:
            s.mode = mode
        if auto_speak is not None:
            s.auto_speak = auto_speak
        if cooldown_minutes is not None:
            s.cooldown_minutes = cooldown_minutes

        with self._get_connection() as conn:
            conn.execute("""
            UPDATE proactive_settings
            SET mode = ?, auto_speak = ?, cooldown_minutes = ?
            WHERE key = 'default'
            """, (s.mode, 1 if s.auto_speak else 0, s.cooldown_minutes))
        return s

    def record_intervention(self, intervention: ProactiveIntervention):
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO proactive_interventions (id, reason, message, active_window, target_focus, timestamp, spoken, dismissed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                intervention.id,
                intervention.reason,
                intervention.message,
                intervention.active_window,
                intervention.target_focus,
                intervention.timestamp,
                1 if intervention.spoken else 0,
                1 if intervention.dismissed else 0,
            ))
            conn.execute("""
            UPDATE proactive_settings SET last_intervention_time = ? WHERE key = 'default'
            """, (intervention.timestamp,))

    def list_interventions(self, limit: int = 15) -> List[ProactiveIntervention]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM proactive_interventions ORDER BY timestamp DESC LIMIT ?", (limit,))
            res = []
            for r in cur.fetchall():
                res.append(ProactiveIntervention(
                    id=r["id"],
                    reason=r["reason"],
                    message=r["message"],
                    active_window=r["active_window"],
                    target_focus=r["target_focus"],
                    timestamp=r["timestamp"],
                    spoken=bool(r["spoken"]),
                    dismissed=bool(r["dismissed"]),
                ))
            return res

    def get_situation_snapshot(self, session_id: str = "default_session") -> Dict[str, Any]:
        """Gathers real-time multi-source situational signals."""
        window_info = get_active_window_info()
        active_title = window_info.get("title", "Unknown")

        # LifeOS TELOS Profile
        telos_profile = telos_engine.load()
        primary_target = telos_profile.targets[0] if telos_profile.targets else "System Evolution"

        # Recent Operator Reports
        recent_reports = agent_operator.list_reports(limit=2)
        latest_report = recent_reports[0].summary[:200] if recent_reports else "No shifts recently."

        # Recent user message timestamp for cadence
        messages = memory_store.get_messages(session_id=session_id, limit=4)
        last_turn = messages[-1].content[:150] if messages else "No recent turn."

        return {
            "active_window": active_title,
            "primary_target": primary_target,
            "all_targets": telos_profile.targets[:3],
            "latest_shift_report": latest_report,
            "last_user_turn": last_turn,
            "timestamp": utc_now_iso(),
        }

    async def evaluate_initiative(
        self,
        session_id: str = "default_session",
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Evaluates situation and decides whether to formulate a proactive thought or question.
        Returns evaluation result with intervention details if triggered.
        """
        settings = self.get_settings()
        if settings.mode == "muted" and not force:
            return {"should_intervene": False, "reason": "Proactive mode is muted."}

        # Check Cooldown
        if not force and settings.last_intervention_time:
            try:
                last_time = datetime.fromisoformat(settings.last_intervention_time)
                elapsed_min = (datetime.now(timezone.utc) - last_time).total_seconds() / 60.0
                if elapsed_min < settings.cooldown_minutes:
                    return {
                        "should_intervene": False,
                        "reason": f"Cooldown active ({elapsed_min:.1f}/{settings.cooldown_minutes} min elapsed).",
                    }
            except Exception:
                pass

        situation = self.get_situation_snapshot(session_id=session_id)

        system_prompt = (
            "You are MaxIM, an autonomous personal AGI co-pilot with high agency.\n"
            "You are evaluating the user's current situation to determine if you should proactively speak up.\n\n"
            "Core Directives:\n"
            "1. DO NOT be robotic, canned, or generic ('How can I help you?', 'What are we working on?').\n"
            "2. DO NOT state the obvious ('I see you are on Visual Studio Code').\n"
            "3. If the user appears deeply focused on their work and does not need any interruption, respond strictly with: [NO_INTERVENTION].\n"
            "4. If there is a genuine strategic opportunity—such as challenging a potential blind spot, suggesting a high-leverage next step toward their TELOS targets, asking a sharp clarifying question, or connecting their current file to a recent shift finding—speak up decisively.\n"
            "5. Keep your spoken interjection concise (1 to 2 sharp sentences max), natural, thoughtful, and human-like.\n"
            "6. Speak like a real person: use direct verbs, natural rhythm, zero AI clichés, zero fake praise, and zero chatbot filler ('Certainly!', 'I hope this helps').\n"
        )

        user_content = (
            f"Current Situational Context:\n"
            f"- Foreground Window: {situation['active_window']}\n"
            f"- Active LifeOS TELOS Targets: {situation['all_targets']}\n"
            f"- Latest Background Shift Finding: {situation['latest_shift_report']}\n"
            f"- Last Conversation Turn: {situation['last_user_turn']}\n"
            f"- Sensitivity Mode: {settings.mode}\n\n"
            "Evaluate: Should you interject with a proactive thought/question? If no, reply [NO_INTERVENTION]. If yes, reply directly with the natural spoken message."
        )

        try:
            res = await model_router.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
            raw_reply = (res.choices[0].message.content or "").strip()
        except Exception as e:
            logger.error(f"Proactive evaluation LLM failed: {e}")
            return {"should_intervene": False, "reason": f"LLM error: {e}"}

        if "[NO_INTERVENTION]" in raw_reply or not raw_reply:
            return {
                "should_intervene": False,
                "reason": "Evaluator assessed user is focused; no intervention needed.",
                "context": situation,
            }

        # Formulate Intervention
        clean_message = raw_reply.replace("[INTERVENTION]", "").strip()
        intervention = ProactiveIntervention(
            reason=f"Situational alignment: {situation['active_window'][:50]}",
            message=clean_message,
            active_window=situation["active_window"],
            target_focus=situation["primary_target"],
            spoken=settings.auto_speak,
        )
        self.record_intervention(intervention)

        return {
            "should_intervene": True,
            "intervention": intervention.model_dump(),
            "context": situation,
            "auto_speak": settings.auto_speak,
        }

# Global singleton instance
proactive_agent = ProactiveSituationalAgent()
