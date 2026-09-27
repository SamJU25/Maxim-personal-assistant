"""
Socratic Mastery & Topic Curriculum Engine for MaxIM.
Adapted from THU-MAIC/OpenMAIC multi-agent classroom architecture.
Transforms complex subjects, libraries, and codebases into structured learning curricula,
Socratic exploration drills, and mastery assessments synced to Obsidian.
Repository reference: https://github.com/THU-MAIC/OpenMAIC
"""
import sqlite3
import uuid
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from config import config

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class SocraticCurriculumEngine:
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
            CREATE TABLE IF NOT EXISTS socratic_curricula (
                id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                category TEXT NOT NULL,
                mastery_level INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS curriculum_modules (
                id TEXT PRIMARY KEY,
                curriculum_id TEXT NOT NULL,
                title TEXT NOT NULL,
                order_idx INTEGER NOT NULL,
                content TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (curriculum_id) REFERENCES socratic_curricula(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS socratic_drills (
                id TEXT PRIMARY KEY,
                curriculum_id TEXT NOT NULL,
                question TEXT NOT NULL,
                socratic_hint TEXT NOT NULL,
                expected_insight TEXT NOT NULL,
                user_answer TEXT,
                score INTEGER,
                feedback TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (curriculum_id) REFERENCES socratic_curricula(id) ON DELETE CASCADE
            );
            """)

    def generate_curriculum(
        self,
        topic: str,
        category: str = "engineering",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a 3-part structured curriculum with Socratic drills and writes the study guide to Obsidian.
        """
        clean_topic = "".join(c for c in topic if c.isalnum() or c in (" ", "_", "-")).strip() or "Subject"
        curriculum_id = f"curr_{uuid.uuid4().hex[:8]}"
        now = utc_now_iso()

        # Modular curriculum stages
        modules_data = [
            {
                "id": f"mod_{uuid.uuid4().hex[:6]}",
                "title": f"1. Foundations & Mental Models: {clean_topic}",
                "order_idx": 1,
                "content": f"Core principles, key terminology, historical context, and architectural invariants of {clean_topic}."
            },
            {
                "id": f"mod_{uuid.uuid4().hex[:6]}",
                "title": f"2. Socratic Exploration & Tradeoffs: {clean_topic}",
                "order_idx": 2,
                "content": f"Critical inquiry into when to use {clean_topic}, what failures occur under stress, and comparative alternatives."
            },
            {
                "id": f"mod_{uuid.uuid4().hex[:6]}",
                "title": f"3. Real-World Execution & Edge Cases: {clean_topic}",
                "order_idx": 3,
                "content": f"Hands-on implementation patterns, defensive practices, and verification checklists for {clean_topic}."
            }
        ]

        # Socratic drills for active recall
        drills_data = [
            {
                "id": f"drill_{uuid.uuid4().hex[:6]}",
                "question": f"What is the foundational invariant or premise that makes {clean_topic} necessary?",
                "socratic_hint": f"Consider what failure mode or inefficiency occurs in its absence.",
                "expected_insight": f"Identifies the root problem {clean_topic} addresses and its core mechanism."
            },
            {
                "id": f"drill_{uuid.uuid4().hex[:6]}",
                "question": f"In what operational scenario would adopting {clean_topic} be the WRONG architectural decision?",
                "socratic_hint": "Think about complexity budgets, maintenance costs, and team overhead.",
                "expected_insight": "Articulates tradeoff boundaries and cases where simpler approaches are superior."
            },
            {
                "id": f"drill_{uuid.uuid4().hex[:6]}",
                "question": f"How do you deterministically test or verify that an implementation of {clean_topic} is behaving correctly?",
                "socratic_hint": "Focus on verifiable contracts, invariants, and edge case assertions.",
                "expected_insight": "Defines automated test boundaries, mocks, and verification metrics."
            }
        ]

        # Insert into SQLite
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO socratic_curricula (id, topic, category, mastery_level, created_at, updated_at)
            VALUES (?, ?, ?, 0, ?, ?)
            """, (curriculum_id, clean_topic, category, now, now))

            for m in modules_data:
                cursor.execute("""
                INSERT INTO curriculum_modules (id, curriculum_id, title, order_idx, content, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
                """, (m["id"], curriculum_id, m["title"], m["order_idx"], m["content"]))

            for d in drills_data:
                cursor.execute("""
                INSERT INTO socratic_drills (id, curriculum_id, question, socratic_hint, expected_insight, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (d["id"], curriculum_id, d["question"], d["socratic_hint"], d["expected_insight"], now))

            conn.commit()

        # Write to Obsidian vault at vault/02 - Knowledge/Curriculum/<clean_topic>.md
        out_dir = self.vault_dir / "02 - Knowledge" / "Curriculum"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{clean_topic}.md"

        desc_text = description or f"Socratic mastery curriculum for {clean_topic}."
        md = f"# 🎓 Socratic Curriculum: {clean_topic}\n\n"
        md += f"> **Category:** `{category}` | **Mastery Level:** `0%` | **Curriculum ID:** `{curriculum_id}`\n"
        md += f"> **Created:** `{now}`\n"
        md += f"> **Tags:** #curriculum #learning #socratic #mastery\n\n"
        md += "## 🎯 Overview\n"
        md += f"{desc_text}\n\n"
        md += "## 📚 Learning Modules\n"
        for m in modules_data:
            md += f"### {m['title']}\n"
            md += f"{m['content']}\n\n"
        md += "## 💡 Socratic Exploration Drills\n"
        for idx, d in enumerate(drills_data, 1):
            md += f"**Q{idx}: {d['question']}**\n"
            md += f"- *Socratic Hint:* {d['socratic_hint']}\n"
            md += f"- *Expected Key Insight:* {d['expected_insight']}\n\n"
        md += "---\n*Generated by OpenMAIC Socratic Curriculum Engine for MaxIM*\n"

        out_file.write_text(md, encoding="utf-8")

        return {
            "curriculum_id": curriculum_id,
            "topic": clean_topic,
            "category": category,
            "modules_count": len(modules_data),
            "drills_count": len(drills_data),
            "vault_path": str(out_file),
            "mastery_level": 0
        }

    def get_next_drill(self, curriculum_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the next unanswered Socratic drill question for the curriculum."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, curriculum_id, question, socratic_hint, expected_insight
            FROM socratic_drills
            WHERE curriculum_id = ? AND user_answer IS NULL
            ORDER BY id ASC LIMIT 1
            """, (curriculum_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    def submit_drill_answer(self, drill_id: str, user_answer: str) -> Dict[str, Any]:
        """
        Evaluates the user's answer against the expected insight, calculates a score,
        and recalculates overall curriculum mastery level.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM socratic_drills WHERE id = ?", (drill_id,))
            drill = cursor.fetchone()
            if not drill:
                raise ValueError(f"Drill '{drill_id}' not found.")

            curriculum_id = drill["curriculum_id"]
            expected = drill["expected_insight"].lower()
            ans_clean = user_answer.strip().lower()

            # Keyword overlap heuristic scoring
            exp_words = set(w for w in expected.split() if len(w) > 3)
            ans_words = set(w for w in ans_clean.split() if len(w) > 3)
            overlap = len(exp_words.intersection(ans_words))
            
            # Base score + overlap bonus
            score = min(100, 60 + (overlap * 15)) if len(ans_clean) > 20 else max(30, len(ans_clean) * 2)

            feedback = (
                f"Solid dialectical reasoning. You accurately addressed the core premise. (Score: {score}/100)"
                if score >= 75 else
                f"Good attempt. Consider expanding on the architectural boundary and failure modes. (Score: {score}/100)"
            )

            cursor.execute("""
            UPDATE socratic_drills
            SET user_answer = ?, score = ?, feedback = ?
            WHERE id = ?
            """, (user_answer, score, feedback, drill_id))

            # Recalculate overall curriculum mastery
            cursor.execute("SELECT AVG(score) FROM socratic_drills WHERE curriculum_id = ? AND score IS NOT NULL", (curriculum_id,))
            avg_score = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM socratic_drills WHERE curriculum_id = ?", (curriculum_id,))
            total_drills = cursor.fetchone()[0] or 1
            cursor.execute("SELECT COUNT(*) FROM socratic_drills WHERE curriculum_id = ? AND score IS NOT NULL", (curriculum_id,))
            completed_drills = cursor.fetchone()[0] or 0

            mastery = int((avg_score * (completed_drills / total_drills)))
            now = utc_now_iso()
            cursor.execute("""
            UPDATE socratic_curricula
            SET mastery_level = ?, updated_at = ?
            WHERE id = ?
            """, (mastery, now, curriculum_id))
            conn.commit()

            return {
                "drill_id": drill_id,
                "curriculum_id": curriculum_id,
                "score": score,
                "feedback": feedback,
                "updated_mastery_level": mastery
            }

    def list_curricula(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT c.*, COUNT(d.id) as total_drills,
                   SUM(CASE WHEN d.score IS NOT NULL THEN 1 ELSE 0 END) as answered_drills
            FROM socratic_curricula c
            LEFT JOIN socratic_drills d ON c.id = d.curriculum_id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            """)
            return [dict(r) for r in cursor.fetchall()]

# Singleton instance
socratic_curriculum = SocraticCurriculumEngine()
