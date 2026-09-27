"""
Autonomous Overnight & Idle Intelligence Scout for MaxIM.
Continuously monitors user interests, search history, and LifeOS TELOS targets.
When the user goes to sleep or remains idle for an extended period, it awakens
to scour the live internet (via Agent Reach: DuckDuckGo, Hacker News, GitHub)
for relevant news, breakthrough developments, and actionable project ideas.
Saves briefings to SQLite and the Obsidian vault (vault/02 - Knowledge/).
"""
import sqlite3
import json
import re
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from config import config
from telos import telos_engine
from tools.vault_tool import vault_synapse
from tools.reach_tool import agent_reach
from router import model_router

logger = logging.getLogger("maxim.idle_scout")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class UserInterestTopic(BaseModel):
    id: Optional[int] = None
    topic: str
    category: str = "tech"
    weight: int = 1
    source: str = "auto"
    last_seen: str = Field(default_factory=utc_now_iso)

class ScoutReport(BaseModel):
    id: str = Field(default_factory=lambda: f"scout_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}")
    created_at: str = Field(default_factory=utc_now_iso)
    trigger_type: str = "manual"  # sleep, idle, manual
    topics: List[str] = Field(default_factory=list)
    title: str
    summary: str
    briefing_markdown: str
    audio_brief: str
    raw_sources: List[Dict[str, Any]] = Field(default_factory=list)
    vault_path: Optional[str] = None
    is_reviewed: bool = False

class ScoutSettings(BaseModel):
    enabled: bool = True
    idle_threshold_minutes: int = 45
    night_start_hour: int = 23
    night_end_hour: int = 7
    last_user_activity: str = Field(default_factory=utc_now_iso)
    last_scout_time: Optional[str] = None
    auto_generate_audio: bool = True

class IdleIntelligenceScout:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self._init_tables()
        self._seed_default_interests_if_empty()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_tables(self):
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS scout_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                enabled INTEGER NOT NULL DEFAULT 1,
                idle_threshold_minutes INTEGER NOT NULL DEFAULT 45,
                night_start_hour INTEGER NOT NULL DEFAULT 23,
                night_end_hour INTEGER NOT NULL DEFAULT 7,
                last_user_activity TEXT NOT NULL,
                last_scout_time TEXT,
                auto_generate_audio INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS user_interest_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL DEFAULT 'tech',
                weight INTEGER NOT NULL DEFAULT 1,
                source TEXT NOT NULL DEFAULT 'auto',
                last_seen TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS idle_scout_reports (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                topics TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                briefing_markdown TEXT NOT NULL,
                audio_brief TEXT NOT NULL,
                raw_sources TEXT,
                vault_path TEXT,
                is_reviewed INTEGER NOT NULL DEFAULT 0
            );
            """)

            # Ensure singleton settings row exists
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM scout_settings WHERE id = 1;")
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO scout_settings (
                    id, enabled, idle_threshold_minutes, night_start_hour,
                    night_end_hour, last_user_activity, last_scout_time, auto_generate_audio
                ) VALUES (1, 1, 45, 23, 7, ?, NULL, 1);
                """, (utc_now_iso(),))
            conn.commit()

    def _seed_default_interests_if_empty(self):
        """Seeds initial topics from LifeOS TELOS and core tech stack if table is empty."""
        try:
            with self._get_connection() as conn:
                count = conn.execute("SELECT COUNT(*) FROM user_interest_topics;").fetchone()[0]
                if count == 0:
                    now = utc_now_iso()
                    telos = telos_engine.load()
                    seed_topics = [
                        ("React 19 & Modern Web Architecture", "tech", 5),
                        ("Local LLM & Autonomous AI Agents", "ai", 5),
                        ("Fullstack TypeScript & FastAPI Systems", "tech", 4),
                        ("Obsidian Personal Knowledge Management", "productivity", 3),
                    ]
                    for t in telos.targets:
                        clean_t = t.strip()
                        if clean_t and len(clean_t) > 3:
                            seed_topics.append((clean_t, "project", 6))

                    for topic, cat, weight in seed_topics:
                        conn.execute("""
                        INSERT OR IGNORE INTO user_interest_topics (topic, category, weight, source, last_seen)
                        VALUES (?, ?, ?, 'auto', ?);
                        """, (topic, cat, weight, now))
                    conn.commit()
        except Exception as e:
            logger.warning(f"Failed to seed default interest topics: {e}")

    # =========================================================================
    # 1. User Activity & Interest Profiling
    # =========================================================================

    def record_user_activity(self, text: str = ""):
        """Records user activity timestamp and extracts potential interest keywords."""
        now = utc_now_iso()
        with self._get_connection() as conn:
            conn.execute("UPDATE scout_settings SET last_user_activity = ? WHERE id = 1;", (now,))

            if text and len(text.strip()) > 3:
                # Extract potential tech, tools, and topics (e.g. PascalCase, capital phrases, tech terms)
                extracted_topics = self._extract_topics_from_text(text)
                for topic, category in extracted_topics:
                    # Filter through Privacy Guard to ensure no file paths, usernames, or secrets become topics
                    try:
                        from privacy_guard import privacy_guard
                        if not privacy_guard.is_safe_topic(topic):
                            continue
                    except Exception:
                        pass

                    conn.execute("""
                    INSERT INTO user_interest_topics (topic, category, weight, source, last_seen)
                    VALUES (?, ?, 1, 'auto', ?)
                    ON CONFLICT(topic) DO UPDATE SET
                        weight = weight + 1,
                        last_seen = excluded.last_seen;
                    """, (topic, category, now))
            conn.commit()

    def _extract_topics_from_text(self, text: str) -> List[tuple]:
        """Heuristically extracts interest topics, technology names, and project keywords."""
        results = []
        # Match common tech buzzwords or concepts
        tech_keywords = [
            "React", "Next.js", "TypeScript", "Python", "FastAPI", "SQLite",
            "Tailwind", "Ollama", "DeepSeek", "OpenAI", "Claude", "Gemini",
            "LobeHub", "OpenJarvis", "Agent Reach", "Three.js", "WebGL",
            "Obsidian", "RAG", "Subagent", "Vector DB", "Docker", "Pytest"
        ]
        text_lower = text.lower()
        for kw in tech_keywords:
            if kw.lower() in text_lower:
                results.append((kw, "tech"))

        # Look for multi-word capitalized topics (e.g. "Quantum Computing", "Local Inference")
        capitalized = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", text)
        for cap in capitalized:
            if len(cap) > 4 and cap not in [t[0] for t in results]:
                results.append((cap, "general"))

        return results[:5]

    def get_interest_topics(self, limit: int = 15) -> List[UserInterestTopic]:
        """Returns active interest topics sorted by weight and recency."""
        with self._get_connection() as conn:
            rows = conn.execute("""
            SELECT id, topic, category, weight, source, last_seen
            FROM user_interest_topics
            ORDER BY weight DESC, last_seen DESC
            LIMIT ?;
            """, (limit,)).fetchall()
            return [UserInterestTopic(**dict(r)) for r in rows]

    def add_interest_topic(self, topic: str, category: str = "custom") -> UserInterestTopic:
        """Manually registers an interest topic with boosted initial weight."""
        now = utc_now_iso()
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO user_interest_topics (topic, category, weight, source, last_seen)
            VALUES (?, ?, 10, 'manual', ?)
            ON CONFLICT(topic) DO UPDATE SET
                weight = weight + 5,
                source = 'manual',
                last_seen = excluded.last_seen;
            """, (topic.strip(), category, now))
            conn.commit()
            row = conn.execute("SELECT * FROM user_interest_topics WHERE topic = ?;", (topic.strip(),)).fetchone()
            return UserInterestTopic(**dict(row))

    def delete_interest_topic(self, topic_id: int) -> bool:
        """Removes a topic from interest tracking."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_interest_topics WHERE id = ?;", (topic_id,))
            conn.commit()
            return cursor.rowcount > 0

    # =========================================================================
    # 2. Idle & Sleep State Detection
    # =========================================================================

    def get_settings(self) -> ScoutSettings:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM scout_settings WHERE id = 1;").fetchone()
            if row:
                return ScoutSettings(**dict(row))
            return ScoutSettings()

    def update_settings(
        self,
        enabled: Optional[bool] = None,
        idle_threshold_minutes: Optional[int] = None,
        night_start_hour: Optional[int] = None,
        night_end_hour: Optional[int] = None,
        auto_generate_audio: Optional[bool] = None,
    ) -> ScoutSettings:
        current = self.get_settings()
        new_enabled = current.enabled if enabled is None else enabled
        new_idle_thresh = current.idle_threshold_minutes if idle_threshold_minutes is None else idle_threshold_minutes
        new_start = current.night_start_hour if night_start_hour is None else night_start_hour
        new_end = current.night_end_hour if night_end_hour is None else night_end_hour
        new_audio = current.auto_generate_audio if auto_generate_audio is None else auto_generate_audio

        with self._get_connection() as conn:
            conn.execute("""
            UPDATE scout_settings SET
                enabled = ?,
                idle_threshold_minutes = ?,
                night_start_hour = ?,
                night_end_hour = ?,
                auto_generate_audio = ?
            WHERE id = 1;
            """, (int(new_enabled), new_idle_thresh, new_start, new_end, int(new_audio)))
            conn.commit()
        return self.get_settings()

    def check_idle_or_sleep_status(self) -> Dict[str, Any]:
        """
        Evaluates whether the user is currently asleep or idle for an extended period:
        - Checks elapsed minutes since last_user_activity.
        - Checks if current local hour falls within nighttime sleep window (e.g. 23:00 - 07:00).
        """
        settings = self.get_settings()
        now_dt = datetime.now()
        current_hour = now_dt.hour

        # Check nighttime
        is_night = False
        if settings.night_start_hour > settings.night_end_hour:
            # Over midnight (e.g. 23 to 7)
            is_night = current_hour >= settings.night_start_hour or current_hour < settings.night_end_hour
        else:
            is_night = settings.night_start_hour <= current_hour < settings.night_end_hour

        # Check idle duration
        try:
            last_dt = datetime.fromisoformat(settings.last_user_activity.replace("Z", "+00:00"))
            minutes_idle = (datetime.now(timezone.utc) - last_dt).total_seconds() / 60.0
        except Exception:
            minutes_idle = 999.0

        is_idle = minutes_idle >= settings.idle_threshold_minutes

        # Minimum 3 hours between automatic scout cycles
        cooldown_ok = True
        if settings.last_scout_time:
            try:
                last_scout_dt = datetime.fromisoformat(settings.last_scout_time.replace("Z", "+00:00"))
                hours_since_scout = (datetime.now(timezone.utc) - last_scout_dt).total_seconds() / 3600.0
                if hours_since_scout < 3.0:
                    cooldown_ok = False
            except Exception:
                pass

        should_auto_scout = settings.enabled and cooldown_ok and (is_night or is_idle)

        return {
            "enabled": settings.enabled,
            "is_night": is_night,
            "is_idle": is_idle,
            "minutes_idle": round(minutes_idle, 1),
            "current_hour": current_hour,
            "cooldown_ok": cooldown_ok,
            "should_auto_scout": should_auto_scout,
            "last_scout_time": settings.last_scout_time,
        }

    # =========================================================================
    # 3. Autonomous Overnight Deep Scout Cycle
    # =========================================================================

    async def execute_scout_cycle(
        self,
        trigger_type: str = "manual",
        max_topics: int = 3,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes a complete overnight / idle intelligence scout cycle:
        1. Selects highest-weighted active interest topics.
        2. Queries DuckDuckGo for latest breakthrough news on each topic.
        3. Fetches trending Hacker News stories to spot emerging tech discussions.
        4. Synthesizes a high-signal Executive Intelligence Briefing + spoken Audio Brief.
        5. Saves to SQLite and Obsidian vault (vault/02 - Knowledge/).
        """
        status = self.check_idle_or_sleep_status()
        if not force and not status["should_auto_scout"] and trigger_type == "auto":
            return {
                "status": "skipped",
                "reason": "Scout cycle conditions not met (active or in cooldown).",
                "idle_status": status,
            }

        topics_records = self.get_interest_topics(limit=max_topics)
        if not topics_records:
            selected_topics = ["Artificial Intelligence Agents", "React 19 & Web Architecture"]
        else:
            selected_topics = [t.topic for t in topics_records]

        logger.info(f"Launching Idle Scout Cycle for topics: {selected_topics} (trigger: {trigger_type})")

        # Multi-Source Gathering
        collected_sources: List[Dict[str, Any]] = []

        # A. Query DuckDuckGo for each topic
        for topic in selected_topics:
            try:
                search_res = await agent_reach.web_search(
                    query=f"{topic} latest news developments",
                    limit=3,
                )
                results = search_res.get("results", [])
                for item in results:
                    collected_sources.append({
                        "topic": topic,
                        "source_type": "web_search",
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("snippet", ""),
                    })
            except Exception as e:
                logger.warning(f"Error web searching for topic '{topic}': {e}")

        # B. Query Hacker News tech feed
        try:
            hn_res = await agent_reach.community_reach(source="hackernews", limit=12)
            hn_items = hn_res.get("discussions", [])
            for item in hn_items[:6]:
                collected_sources.append({
                    "topic": "Tech Community",
                    "source_type": "hackernews",
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": f"Score: {item.get('score', 0)} | Comments: {item.get('comments', 0)}",
                })
        except Exception as e:
            logger.warning(f"Error fetching community tech feed: {e}")

        # C. LLM Synthesis & Idea Generation
        telos_profile = telos_engine.load()
        user_targets = ", ".join(telos_profile.targets[:3]) if telos_profile.targets else "MaxIM Architecture & Cognitive Systems"

        sources_summary = "\n".join([
            f"- [{s['topic']}] {s['title']}: {s['snippet']} (URL: {s.get('url', '')})"
            for s in collected_sources[:12]
        ])

        system_prompt = (
            "You are the MaxIM Autonomous Intelligence Scout. While the user was asleep or idle, "
            "you searched the internet and community feeds for updates on their active interests and projects.\n"
            "Synthesize an Executive Morning Intelligence Briefing that is high-signal and zero-fluff.\n\n"
            "Natural-Human Writing Invariants:\n"
            "- Write like a thoughtful human who understands the subject: direct verbs, natural rhythm, concrete details.\n"
            "- Ban all generic AI rhetoric: do not use 'evolving landscape', 'in today's world', 'plays a pivotal role', 'serves as', 'furthermore'.\n"
            "- No automatic praise or advertising adjectives ('vibrant', 'breathtaking', 'exciting', 'sophisticated'). State what happened plainly.\n"
            "- The audio brief must sound like a real person talking naturally, without canned openings or fake enthusiasm.\n\n"
            "Format your response as a valid JSON object with the following exact keys:\n"
            "{\n"
            '  "title": "A sharp, direct executive briefing title",\n'
            '  "summary": "2-sentence direct summary of the main discoveries",\n'
            '  "news_items": [\n'
            '     {"headline": "...", "detail": "...", "source_url": "..."}\n'
            "  ],\n"
            '  "project_ideas": [\n'
            '     {"idea": "Actionable experiment or feature the user can build", "relevance": "Tied to their active target"}\n'
            "  ],\n"
            '  "audio_brief": "A direct, natural spoken paragraph designed for voice readout (speak like a real person, state what happened directly)"\n'
            "}"
        )

        user_content = (
            f"User's Active TELOS Targets: {user_targets}\n"
            f"Scouted Topics: {', '.join(selected_topics)}\n\n"
            f"Raw Discovered Intelligence Feed:\n{sources_summary}\n\n"
            "Generate the JSON briefing now."
        )

        try:
            res = await model_router.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
            raw_text = (res.choices[0].message.content or "").strip()
            # Clean markdown codeblocks if model wrapped in ```json
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
                raw_text = re.sub(r"\n?```$", "", raw_text).strip()
            data = json.loads(raw_text)
        except Exception as err:
            logger.warning(f"LLM JSON parsing fallback: {err}")
            data = {
                "title": f"Overnight Intelligence Briefing: {', '.join(selected_topics[:2])}",
                "summary": f"Scouted {len(collected_sources)} updates across {', '.join(selected_topics)} while you were away.",
                "news_items": [
                    {"headline": s["title"], "detail": s["snippet"], "source_url": s.get("url", "")}
                    for s in collected_sources[:4]
                ],
                "project_ideas": [
                    {"idea": f"Incorporate latest {selected_topics[0]} patterns into active workflow", "relevance": user_targets}
                ],
                "audio_brief": f"Good morning! While you were resting, I scouted updates on {', '.join(selected_topics)}. Here is what is happening.",
            }

        # Build Full Markdown Briefing for Vault
        now_str = datetime.now().strftime("%Y-%m-%d")
        markdown_content = f"""# {data.get('title', 'Overnight Intelligence Briefing')}
*Synthesized autonomously by **MaxIM Idle Scout** on {now_str} (Trigger: {trigger_type})*

## ☀️ Executive Summary
{data.get('summary', '')}

## 📰 High-Signal News & Breakthroughs
"""
        for item in data.get("news_items", []):
            url_part = f" ([Source]({item.get('source_url')}))" if item.get("source_url") else ""
            markdown_content += f"- **{item.get('headline')}**{url_part}\n  {item.get('detail')}\n\n"

        markdown_content += f"""## 💡 Actionable Project Ideas & Experiments
*Aligned with your LifeOS priorities: [[TELOS]]*
"""
        for idea in data.get("project_ideas", []):
            markdown_content += f"- **{idea.get('idea')}**\n  *Strategic Relevance:* {idea.get('relevance')}\n\n"

        markdown_content += f"""## 🎙️ Spoken Morning Audio Brief
> "{data.get('audio_brief', '')}"

---
#intel #scout #overnight #news #ideas [[TELOS]] [[Master MOC]]
"""

        # Save to Obsidian Vault under 02 - Knowledge/
        vault_note_title = f"Overnight Intel - {now_str} - {uuid.uuid4().hex[:4]}"
        try:
            vault_synapse.write_note(
                title=vault_note_title,
                content=markdown_content,
                folder="02 - Knowledge",
                tags=["#intel", "#scout", "#overnight"],
            )
            saved_vault_path = f"02 - Knowledge/{vault_note_title}.md"
        except Exception as ve:
            logger.warning(f"Could not write scout note to vault: {ve}")
            saved_vault_path = None

        # Persist to SQLite
        report = ScoutReport(
            trigger_type=trigger_type,
            topics=selected_topics,
            title=data.get("title", "Overnight Intelligence Briefing"),
            summary=data.get("summary", ""),
            briefing_markdown=markdown_content,
            audio_brief=data.get("audio_brief", ""),
            raw_sources=collected_sources[:15],
            vault_path=saved_vault_path,
            is_reviewed=False,
        )

        now_iso = utc_now_iso()
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO idle_scout_reports (
                id, created_at, trigger_type, topics, title, summary,
                briefing_markdown, audio_brief, raw_sources, vault_path, is_reviewed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
            """, (
                report.id,
                report.created_at,
                report.trigger_type,
                json.dumps(report.topics),
                report.title,
                report.summary,
                report.briefing_markdown,
                report.audio_brief,
                json.dumps(report.raw_sources),
                report.vault_path,
            ))
            conn.execute("UPDATE scout_settings SET last_scout_time = ? WHERE id = 1;", (now_iso,))
            conn.commit()

        logger.info(f"Idle Scout Cycle successfully completed: {report.id} ({report.title})")
        return report.model_dump()

    # =========================================================================
    # 4. Report Retrieval & Review
    # =========================================================================

    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        """Returns the most recent scout briefing."""
        with self._get_connection() as conn:
            row = conn.execute("""
            SELECT * FROM idle_scout_reports
            ORDER BY created_at DESC
            LIMIT 1;
            """).fetchone()
            if row:
                d = dict(row)
                d["topics"] = json.loads(d.get("topics") or "[]")
                d["raw_sources"] = json.loads(d.get("raw_sources") or "[]")
                d["is_reviewed"] = bool(d.get("is_reviewed", 0))
                return d
            return None

    def list_reports(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Returns historical scout briefings."""
        with self._get_connection() as conn:
            rows = conn.execute("""
            SELECT * FROM idle_scout_reports
            ORDER BY created_at DESC
            LIMIT ?;
            """, (limit,)).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["topics"] = json.loads(d.get("topics") or "[]")
                d["raw_sources"] = json.loads(d.get("raw_sources") or "[]")
                d["is_reviewed"] = bool(d.get("is_reviewed", 0))
                results.append(d)
            return results

    def mark_report_reviewed(self, report_id: str) -> bool:
        """Marks a briefing as reviewed by user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE idle_scout_reports SET is_reviewed = 1 WHERE id = ?;", (report_id,))
            conn.commit()
            return cursor.rowcount > 0

# Singleton instance
idle_scout = IdleIntelligenceScout()
