"""
Hindsight Mental Models & Epistemic Reflection Engine for MaxIM.
Repository Reference: https://github.com/vectorize-io/hindsight
Paper: 'Hindsight is 20/20: Building Agent Memory that Retains, Recalls, and Reflects' (arXiv:2512.12818)

Functional Core:
1. Four-Network Epistemic Separation:
   - World: Objective facts, system parameters, tools.
   - Experience: Chronological logs, command execution receipts.
   - Opinion / Mental Models: High-order synthesized dispositions, behavioral heuristics, preferences.
   - Observation: Raw sensory buffers before consolidation.
2. Mental Models with Dynamic Confidence & Evidence Tracking:
   - Incremental confidence reinforcement (+0.1) on supporting evidence.
   - Confidence decay/contradiction (-0.15) on contrary feedback.
3. Vault Synchronization:
   - Automatically renders human-readable Markdown notes in 'vault/01 - Memory/Mental Models/'.
   - Maintains '_Mental Models MOC.md' with [[wikilinks]].
4. Knowledge Pages Synthesis:
   - Consolidates scattered facts into unified reference docs in 'vault/02 - Knowledge/'.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from contextlib import contextmanager
from pydantic import BaseModel, Field

from config import config

logger = logging.getLogger("maxim.mental_models")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MentalModelRecord(BaseModel):
    """Structured representation of an agent's synthesized belief/disposition."""
    id: Optional[int] = None
    name: str
    category: str = "preference"  # preference, heuristic, constraint, workflow
    disposition: str
    confidence: float = 0.5  # 0.0 to 1.0
    evidence_count: int = 1
    source_observations: List[str] = Field(default_factory=list)
    status: str = "active"  # active, superseded, disproven
    created_at: str = Field(default_factory=utc_now_iso)
    last_refined_iso: str = Field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class MentalModelEngine:
    """Manages Hindsight epistemic mental models and reflection cycles."""

    def __init__(self, db_path: Optional[Path] = None, vault_dir: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self.vault_dir = vault_dir or config.vault_dir
        self.models_dir = self.vault_dir / "01 - Memory" / "Mental Models"
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
        """Initializes SQLite WAL table for Hindsight mental models."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hindsight_mental_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    disposition TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0.5,
                    evidence_count INTEGER NOT NULL DEFAULT 1,
                    source_observations TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    last_refined_iso TEXT NOT NULL
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mm_status ON hindsight_mental_models(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mm_category ON hindsight_mental_models(category);")
            conn.commit()

    # =========================================================================
    # 1. CORE DISPOSITION & MENTAL MODEL CRUD
    # =========================================================================

    def upsert_mental_model(
        self,
        name: str,
        disposition: str,
        category: str = "preference",
        confidence: float = 0.5,
        observation: Optional[str] = None,
        sync_vault: bool = True,
    ) -> MentalModelRecord:
        """Creates or refines a mental model disposition with supporting evidence."""
        clean_name = name.lower().strip().replace(" ", "_")
        now = utc_now_iso()
        bounded_conf = max(0.0, min(1.0, float(confidence)))

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM hindsight_mental_models WHERE name = ?", (clean_name,))
            existing = cursor.fetchone()

            if existing:
                obs_list = json.loads(existing["source_observations"] or "[]")
                if observation and observation not in obs_list:
                    obs_list.append(observation)

                new_count = existing["evidence_count"] + (1 if observation else 0)
                # Incremental bayesian-style confidence reinforcement
                new_conf = min(1.0, existing["confidence"] + 0.05) if observation else bounded_conf

                cursor.execute("""
                    UPDATE hindsight_mental_models
                    SET disposition = ?, category = ?, confidence = ?, evidence_count = ?,
                        source_observations = ?, status = 'active', last_refined_iso = ?
                    WHERE name = ?
                """, (disposition, category, new_conf, new_count, json.dumps(obs_list), now, clean_name))
                conn.commit()

                rec = MentalModelRecord(
                    id=existing["id"],
                    name=clean_name,
                    category=category,
                    disposition=disposition,
                    confidence=new_conf,
                    evidence_count=new_count,
                    source_observations=obs_list,
                    status="active",
                    created_at=existing["created_at"],
                    last_refined_iso=now,
                )
            else:
                obs_list = [observation] if observation else []
                cursor.execute("""
                    INSERT INTO hindsight_mental_models (
                        name, category, disposition, confidence, evidence_count,
                        source_observations, status, created_at, last_refined_iso
                    ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
                """, (clean_name, category, disposition, bounded_conf, 1, json.dumps(obs_list), now, now))
                conn.commit()
                row_id = cursor.lastrowid

                rec = MentalModelRecord(
                    id=row_id,
                    name=clean_name,
                    category=category,
                    disposition=disposition,
                    confidence=bounded_conf,
                    evidence_count=1,
                    source_observations=obs_list,
                    status="active",
                    created_at=now,
                    last_refined_iso=now,
                )

        if sync_vault:
            self.sync_model_to_vault(rec)
            self.sync_moc()

        return rec

    def reinforce(
        self,
        name_or_id: Union[str, int],
        delta: float = 0.1,
        observation: Optional[str] = None,
        sync_vault: bool = True,
    ) -> Optional[MentalModelRecord]:
        """Strengthens confidence in an existing mental model when verified."""
        now = utc_now_iso()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if isinstance(name_or_id, int) or (isinstance(name_or_id, str) and name_or_id.isdigit()):
                cursor.execute("SELECT * FROM hindsight_mental_models WHERE id = ?", (int(name_or_id),))
            else:
                cursor.execute("SELECT * FROM hindsight_mental_models WHERE name = ?", (str(name_or_id).lower().strip(),))
            row = cursor.fetchone()
            if not row:
                return None

            new_conf = min(1.0, row["confidence"] + delta)
            new_count = row["evidence_count"] + 1
            obs_list = json.loads(row["source_observations"] or "[]")
            if observation and observation not in obs_list:
                obs_list.append(observation)

            cursor.execute("""
                UPDATE hindsight_mental_models
                SET confidence = ?, evidence_count = ?, source_observations = ?, last_refined_iso = ?
                WHERE id = ?
            """, (new_conf, new_count, json.dumps(obs_list), now, row["id"]))
            conn.commit()

            rec = MentalModelRecord(
                id=row["id"],
                name=row["name"],
                category=row["category"],
                disposition=row["disposition"],
                confidence=new_conf,
                evidence_count=new_count,
                source_observations=obs_list,
                status=row["status"],
                created_at=row["created_at"],
                last_refined_iso=now,
            )

        if sync_vault:
            self.sync_model_to_vault(rec)
            self.sync_moc()

        return rec

    def contradict(
        self,
        name_or_id: Union[str, int],
        delta: float = 0.15,
        reason: Optional[str] = None,
        sync_vault: bool = True,
    ) -> Optional[MentalModelRecord]:
        """Weakens confidence or marks a mental model as disproven upon contrary feedback."""
        now = utc_now_iso()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if isinstance(name_or_id, int) or (isinstance(name_or_id, str) and name_or_id.isdigit()):
                cursor.execute("SELECT * FROM hindsight_mental_models WHERE id = ?", (int(name_or_id),))
            else:
                cursor.execute("SELECT * FROM hindsight_mental_models WHERE name = ?", (str(name_or_id).lower().strip(),))
            row = cursor.fetchone()
            if not row:
                return None

            new_conf = max(0.0, row["confidence"] - delta)
            new_status = "disproven" if new_conf <= 0.15 else "active"
            obs_list = json.loads(row["source_observations"] or "[]")
            if reason:
                obs_list.append(f"[Contradiction]: {reason}")

            cursor.execute("""
                UPDATE hindsight_mental_models
                SET confidence = ?, status = ?, source_observations = ?, last_refined_iso = ?
                WHERE id = ?
            """, (new_conf, new_status, json.dumps(obs_list), now, row["id"]))
            conn.commit()

            rec = MentalModelRecord(
                id=row["id"],
                name=row["name"],
                category=row["category"],
                disposition=row["disposition"],
                confidence=new_conf,
                evidence_count=row["evidence_count"],
                source_observations=obs_list,
                status=new_status,
                created_at=row["created_at"],
                last_refined_iso=now,
            )

        if sync_vault:
            self.sync_model_to_vault(rec)
            self.sync_moc()

        return rec

    def get_active_models(self, min_confidence: float = 0.3, limit: int = 25) -> List[MentalModelRecord]:
        """Returns all active, high-confidence mental models ordered by confidence."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM hindsight_mental_models
                WHERE status = 'active' AND confidence >= ?
                ORDER BY confidence DESC, evidence_count DESC
                LIMIT ?
            """, (min_confidence, limit))
            rows = cursor.fetchall()
            return [
                MentalModelRecord(
                    id=r["id"],
                    name=r["name"],
                    category=r["category"],
                    disposition=r["disposition"],
                    confidence=r["confidence"],
                    evidence_count=r["evidence_count"],
                    source_observations=json.loads(r["source_observations"] or "[]"),
                    status=r["status"],
                    created_at=r["created_at"],
                    last_refined_iso=r["last_refined_iso"],
                )
                for r in rows
            ]

    def search_models(self, query: str, limit: int = 10) -> List[MentalModelRecord]:
        """Searches mental models across name, disposition, and category."""
        q = f"%{query.lower().strip()}%"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM hindsight_mental_models
                WHERE status = 'active' AND (
                    LOWER(name) LIKE ? OR LOWER(disposition) LIKE ? OR LOWER(category) LIKE ?
                )
                ORDER BY confidence DESC
                LIMIT ?
            """, (q, q, q, limit))
            rows = cursor.fetchall()
            return [
                MentalModelRecord(
                    id=r["id"],
                    name=r["name"],
                    category=r["category"],
                    disposition=r["disposition"],
                    confidence=r["confidence"],
                    evidence_count=r["evidence_count"],
                    source_observations=json.loads(r["source_observations"] or "[]"),
                    status=r["status"],
                    created_at=r["created_at"],
                    last_refined_iso=r["last_refined_iso"],
                )
                for r in rows
            ]

    def get_all(self, min_confidence: float = 0.0, limit: int = 50) -> List[MentalModelRecord]:
        """Alias to retrieve models with minimum confidence filter."""
        return self.get_active_models(min_confidence=min_confidence, limit=limit)

    def get_model(self, name_or_id: Union[str, int]) -> Optional[MentalModelRecord]:
        """Retrieves a single mental model record by numeric ID or slug name."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if isinstance(name_or_id, int) or (isinstance(name_or_id, str) and name_or_id.isdigit()):
                cursor.execute("SELECT * FROM hindsight_mental_models WHERE id = ?", (int(name_or_id),))
            else:
                cursor.execute("SELECT * FROM hindsight_mental_models WHERE name = ?", (str(name_or_id).lower().strip(),))
            r = cursor.fetchone()
            if not r:
                return None
            return MentalModelRecord(
                id=r["id"],
                name=r["name"],
                category=r["category"],
                disposition=r["disposition"],
                confidence=r["confidence"],
                evidence_count=r["evidence_count"],
                source_observations=json.loads(r["source_observations"] or "[]"),
                status=r["status"],
                created_at=r["created_at"],
                last_refined_iso=r["last_refined_iso"],
            )

    def update_model(
        self,
        name_or_id: Union[str, int],
        disposition: Optional[str] = None,
        confidence: Optional[float] = None,
        status: Optional[str] = None,
        sync_vault: bool = True,
    ) -> Optional[MentalModelRecord]:
        """Explicitly updates disposition, confidence, or status of a mental model."""
        now = utc_now_iso()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if isinstance(name_or_id, int) or (isinstance(name_or_id, str) and name_or_id.isdigit()):
                cursor.execute("SELECT * FROM hindsight_mental_models WHERE id = ?", (int(name_or_id),))
            else:
                cursor.execute("SELECT * FROM hindsight_mental_models WHERE name = ?", (str(name_or_id).lower().strip(),))
            existing = cursor.fetchone()
            if not existing:
                return None

            new_disp = disposition if disposition is not None else existing["disposition"]
            new_conf = max(0.0, min(1.0, float(confidence))) if confidence is not None else existing["confidence"]
            new_stat = status if status is not None else existing["status"]

            cursor.execute("""
                UPDATE hindsight_mental_models
                SET disposition = ?, confidence = ?, status = ?, last_refined_iso = ?
                WHERE id = ?
            """, (new_disp, new_conf, new_stat, now, existing["id"]))
            conn.commit()

            rec = MentalModelRecord(
                id=existing["id"],
                name=existing["name"],
                category=existing["category"],
                disposition=new_disp,
                confidence=new_conf,
                evidence_count=existing["evidence_count"],
                source_observations=json.loads(existing["source_observations"] or "[]"),
                status=new_stat,
                created_at=existing["created_at"],
                last_refined_iso=now,
            )

        if sync_vault:
            self.sync_model_to_vault(rec)
            self.sync_moc()

        return rec

    # =========================================================================
    # 2. REFLECTIVE SYNTHESIS (THE REFLECT PRIMITIVE)
    # =========================================================================

    def reflect(
        self,
        topic: Optional[str] = None,
        observations: Optional[List[str]] = None,
        sync_vault: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes an epistemic reflection pass.
        Clusters raw observations, detects patterns, and crystallizes or updates Mental Models.
        """
        obs = observations or []
        created_models: List[str] = []
        reinforced_models: List[str] = []

        # Heuristic pattern detection across observations
        for item in obs:
            item_lower = item.lower()
            if "minimal diff" in item_lower or "replace_file_content" in item_lower or "don't rewrite" in item_lower:
                m = self.upsert_mental_model(
                    name="surgical_code_editing",
                    disposition="Always use minimal, surgical unified diffs. Never rewrite entire files.",
                    category="heuristic",
                    confidence=0.85,
                    observation=item,
                    sync_vault=False,
                )
                reinforced_models.append(m.name)

            elif "powershell" in item_lower and ("quote" in item_lower or "escaping" in item_lower):
                m = self.upsert_mental_model(
                    name="windows_powershell_quoting",
                    disposition="Escape quotes carefully in PowerShell scripts; prefer single quotes for raw commands.",
                    category="constraint",
                    confidence=0.8,
                    observation=item,
                    sync_vault=False,
                )
                reinforced_models.append(m.name)

            elif "token" in item_lower and ("compress" in item_lower or "save" in item_lower):
                m = self.upsert_mental_model(
                    name="token_budget_conservation",
                    disposition="Minify and distill tool outputs with TokenJuice to save context window tokens.",
                    category="heuristic",
                    confidence=0.75,
                    observation=item,
                    sync_vault=False,
                )
                reinforced_models.append(m.name)

        if sync_vault:
            self.sync_all_models_to_vault()
            self.sync_moc()

        return {
            "status": "reflected",
            "topic": topic or "general_session",
            "observations_processed": len(obs),
            "created_count": len(created_models),
            "reinforced_count": len(reinforced_models),
            "models_touched": list(set(created_models + reinforced_models)),
        }

    # =========================================================================
    # 3. OBSIDIAN VAULT SYNCHRONIZATION
    # =========================================================================

    def sync_model_to_vault(self, model: MentalModelRecord) -> Path:
        """Writes or updates an individual Mental Model note in the Obsidian vault."""
        self.models_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.models_dir / f"{model.name}.md"

        obs_rendered = "\n".join(f"- {o}" for o in model.source_observations[-10:]) if model.source_observations else "- None recorded yet."

        content = (
            f"---\n"
            f"name: \"{model.name}\"\n"
            f"category: \"{model.category}\"\n"
            f"confidence: {model.confidence:.2f}\n"
            f"evidence_count: {model.evidence_count}\n"
            f"status: \"{model.status}\"\n"
            f"last_refined: \"{model.last_refined_iso}\"\n"
            f"tags:\n"
            f"  - mental-model\n"
            f"  - hindsight\n"
            f"  - {model.category}\n"
            f"---\n\n"
            f"# Mental Model: {model.name}\n\n"
            f"> **Category:** `{model.category}` | **Confidence:** `{model.confidence * 100:.1f}%`  \n"
            f"> **Status:** `{model.status}` | **Evidence Receipts:** `{model.evidence_count}`  \n"
            f"> **Last Refined:** `{model.last_refined_iso}`  \n\n"
            f"## 1. Synthesized Working Disposition\n"
            f"**{model.disposition}**\n\n"
            f"## 2. Supporting Observations & Receipts\n"
            f"{obs_rendered}\n\n"
            f"## 3. Epistemic Grounding\n"
            f"- [[00 - LifeOS/TELOS]]\n"
            f"- [[01 - Memory/Mental Models/_Mental Models MOC]]\n"
            f"- `#hindsight` `#mental-model` `#{model.category}`\n"
        )

        file_path.write_text(content, encoding="utf-8")
        return file_path

    def sync_all_models_to_vault(self) -> int:
        """Syncs all active mental models into Obsidian."""
        models = self.get_active_models(min_confidence=0.0, limit=100)
        for m in models:
            self.sync_model_to_vault(m)
        return len(models)

    def sync_moc(self) -> Path:
        """Generates or updates the Mental Models Map of Content in Obsidian."""
        self.models_dir.mkdir(parents=True, exist_ok=True)
        moc_path = self.models_dir / "_Mental Models MOC.md"
        models = self.get_active_models(min_confidence=0.0, limit=100)

        lines = [
            f"# Hindsight Mental Models MOC\n",
            f"> **Epistemic Substrate:** Opinions, Dispositions & Learned Heuristics  \n",
            f"> **Updated at:** `{utc_now_iso()}` | **Total Models:** `{len(models)}`  \n\n",
            f"## Active Working Dispositions\n",
        ]

        if not models:
            lines.append("- *No mental models consolidated yet.*\n")
        else:
            for m in models:
                pct = int(m.confidence * 100)
                status_icon = "🟢" if m.status == "active" else "🔴"
                lines.append(f"- {status_icon} **[[{m.name}]]** (`{m.category}` | {pct}% confidence | {m.evidence_count} evidence): {m.disposition}")

        lines.extend([
            f"\n## Epistemic Architecture\n",
            f"- [[00 - LifeOS/TELOS]]\n",
            f"- [[01 - Memory/Skills MOC]]\n",
            f"- [[Master MOC]]\n",
            f"- `#hindsight` `#epistemic-memory` `#mental-models`\n",
        ])

        moc_path.write_text("\n".join(lines), encoding="utf-8")
        return moc_path

    def get_prompt_context(self, limit: int = 6) -> str:
        """Formats active mental models for direct injection into the agent's system prompt."""
        models = self.get_active_models(min_confidence=0.4, limit=limit)
        if not models:
            return ""

        dispositions = [f"- [{m.category.upper()} | {int(m.confidence * 100)}% conf] {m.disposition}" for m in models]
        return (
            "### HINDSIGHT MENTAL MODELS & LEARNED DISPOSITIONS\n"
            "Apply these learned heuristics and working principles consistently:\n"
            + "\n".join(dispositions)
            + "\n"
        )


# Singleton instance
mental_models = MentalModelEngine()
mental_model_engine = mental_models
