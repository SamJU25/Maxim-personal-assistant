"""
MaxIM Adaptive Language Acquisition & Dialect Learning Engine.
Enables MaxIM to gradually learn local languages (Bangla, Chakma, Sylheti, Chittagonian)
from hearing spoken utterances and conversational dialogue with Sam.
"""

import re
import json
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from config import config


logger = logging.getLogger("maxim.language_learner")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LearnedPhrase(BaseModel):
    id: Optional[int] = None
    word_or_phrase: str
    language: str = "bangla"
    meaning: str = ""
    phonetic_script: Optional[str] = None
    usage_example: Optional[str] = None
    times_heard: int = 1
    times_used: int = 0
    confidence: float = 0.6
    source: str = "hearing"
    learned_at: str = Field(default_factory=utc_now_iso)
    last_heard_at: str = Field(default_factory=utc_now_iso)


FOUNDATIONAL_VOCABULARY = [
    # Bangla (Bengali)
    LearnedPhrase(
        word_or_phrase="ki khobor",
        language="bangla",
        meaning="What's up / what's the news?",
        phonetic_script="কী খবর",
        usage_example="Ki khobor Sam, all tests green.",
        confidence=1.0,
        source="foundational",
    ),
    LearnedPhrase(
        word_or_phrase="kemon acho",
        language="bangla",
        meaning="How are you? (informal/warm)",
        phonetic_script="কেমন আছো",
        usage_example="Kemon acho Sam? Ready to build?",
        confidence=1.0,
        source="foundational",
    ),
    LearnedPhrase(
        word_or_phrase="thik ache",
        language="bangla",
        meaning="All right / okay / understood",
        phonetic_script="ঠিক আছে",
        usage_example="Thik ache, let's refactor the router.",
        confidence=1.0,
        source="foundational",
    ),
    LearnedPhrase(
        word_or_phrase="bujhlam",
        language="bangla",
        meaning="Understood / got it",
        phonetic_script="বুঝলাম",
        usage_example="Bujhlam, switching to strict mode.",
        confidence=1.0,
        source="foundational",
    ),
    LearnedPhrase(
        word_or_phrase="dhonnobad",
        language="bangla",
        meaning="Thank you",
        phonetic_script="ধন্যবাদ",
        usage_example="Dhonnobad Sam!",
        confidence=1.0,
        source="foundational",
    ),
    LearnedPhrase(
        word_or_phrase="shono",
        language="bangla",
        meaning="Listen / hear me out",
        phonetic_script="শোনো",
        usage_example="Shono, that loop might block the thread.",
        confidence=1.0,
        source="foundational",
    ),
    LearnedPhrase(
        word_or_phrase="bhalo",
        language="bangla",
        meaning="Good / well / fine",
        phonetic_script="ভালো",
        usage_example="Sob bhalo, execution finished cleanly.",
        confidence=1.0,
        source="foundational",
    ),
    LearnedPhrase(
        word_or_phrase="ghumaba na?",
        language="bangla",
        meaning="Aren't you going to sleep? (playful late-night banter)",
        phonetic_script="ঘুমাবা না?",
        usage_example="It's 3:30 AM, ghumaba na?",
        confidence=1.0,
        source="foundational",
    ),
    LearnedPhrase(
        word_or_phrase="pagol",
        language="bangla",
        meaning="Crazy / wild (playful teasing)",
        phonetic_script="পাগল",
        usage_example="Rewriting the whole kernel in a day? Pagol naki?",
        confidence=0.9,
        source="foundational",
    ),

    # Chakma (Changma Vaj)
    #
    # Do NOT seed Chakma vocabulary with guessed meanings.
    #
    # Chakma can be written using Bengali script as well as Chakma Unicode,
    # so script alone is not enough to identify the language.
    #
    # Populate verified Chakma vocabulary through:
    #   1. Explicit user teaching
    #   2. A vetted native-speaker dataset
    #
]


class LanguageLearner:
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
        """Initializes tables for learned vocabulary and heard utterances."""

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS learned_vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word_or_phrase TEXT UNIQUE NOT NULL,
                    language TEXT NOT NULL,
                    meaning TEXT,
                    phonetic_script TEXT,
                    usage_example TEXT,
                    times_heard INTEGER DEFAULT 1,
                    times_used INTEGER DEFAULT 0,
                    confidence REAL DEFAULT 0.6,
                    source TEXT DEFAULT 'hearing',
                    learned_at TEXT,
                    last_heard_at TEXT
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS language_hearing_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_text TEXT NOT NULL,
                    detected_language TEXT,
                    matched_phrases TEXT,
                    created_at TEXT
                )
                """
            )

            conn.commit()

            # Seed foundational vocabulary if table is empty.
            cursor.execute(
                "SELECT COUNT(*) FROM learned_vocabulary"
            )

            count = cursor.fetchone()[0]

            if count == 0:
                for phrase in FOUNDATIONAL_VOCABULARY:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO learned_vocabulary (
                            word_or_phrase,
                            language,
                            meaning,
                            phonetic_script,
                            usage_example,
                            times_heard,
                            times_used,
                            confidence,
                            source,
                            learned_at,
                            last_heard_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            phrase.word_or_phrase.lower().strip(),
                            phrase.language.lower(),
                            phrase.meaning,
                            phrase.phonetic_script,
                            phrase.usage_example,
                            phrase.times_heard,
                            phrase.times_used,
                            phrase.confidence,
                            phrase.source,
                            phrase.learned_at,
                            phrase.last_heard_at,
                        ),
                    )

                conn.commit()

    def learn_phrase(
        self,
        word_or_phrase: str,
        language: str,
        meaning: str,
        phonetic_script: Optional[str] = None,
        usage_example: Optional[str] = None,
        confidence: float = 0.8,
        source: str = "user_taught",
    ) -> LearnedPhrase:
        """
        Saves or updates a learned word or phrase in the vocabulary repository.
        """

        clean_phrase = word_or_phrase.strip().lower()
        clean_language = language.strip().lower()
        now = utc_now_iso()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT *
                FROM learned_vocabulary
                WHERE word_or_phrase = ?
                """,
                (clean_phrase,),
            )

            existing = cursor.fetchone()

            if existing:
                new_heard = existing["times_heard"] + 1
                new_confidence = min(
                    1.0,
                    max(existing["confidence"], confidence),
                )

                cursor.execute(
                    """
                    UPDATE learned_vocabulary
                    SET
                        language = ?,
                        meaning = COALESCE(NULLIF(?, ''), meaning),
                        phonetic_script = COALESCE(?, phonetic_script),
                        usage_example = COALESCE(?, usage_example),
                        times_heard = ?,
                        confidence = ?,
                        source = ?,
                        last_heard_at = ?
                    WHERE id = ?
                    """,
                    (
                        clean_language,
                        meaning,
                        phonetic_script,
                        usage_example,
                        new_heard,
                        new_confidence,
                        source,
                        now,
                        existing["id"],
                    ),
                )

                conn.commit()

            else:
                cursor.execute(
                    """
                    INSERT INTO learned_vocabulary (
                        word_or_phrase,
                        language,
                        meaning,
                        phonetic_script,
                        usage_example,
                        times_heard,
                        times_used,
                        confidence,
                        source,
                        learned_at,
                        last_heard_at
                    )
                    VALUES (?, ?, ?, ?, ?, 1, 0, ?, ?, ?, ?)
                    """,
                    (
                        clean_phrase,
                        clean_language,
                        meaning,
                        phonetic_script,
                        usage_example,
                        confidence,
                        source,
                        now,
                        now,
                    ),
                )

                conn.commit()

        result = self.get_phrase(clean_phrase)

        if result is None:
            raise RuntimeError(
                f"Failed to retrieve learned phrase: {clean_phrase}"
            )

        return result

    def get_phrase(
        self,
        word_or_phrase: str,
    ) -> Optional[LearnedPhrase]:
        """Retrieves a single phrase by text."""

        clean_phrase = word_or_phrase.strip().lower()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT *
                FROM learned_vocabulary
                WHERE word_or_phrase = ?
                """,
                (clean_phrase,),
            )

            row = cursor.fetchone()

            if not row:
                return None

            return LearnedPhrase(**dict(row))

    def record_usage(self, word_or_phrase: str):
        """
        Increments usage counter when MaxIM uses
        a learned phrase in dialogue.
        """

        clean_phrase = word_or_phrase.strip().lower()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE learned_vocabulary
                SET times_used = times_used + 1
                WHERE word_or_phrase = ?
                """,
                (clean_phrase,),
            )

            conn.commit()

    def ingest_spoken_utterance(
        self,
        text: str,
        source: str = "voice",
    ) -> Dict[str, Any]:
        """
        Processes heard audio transcripts or chat text from Sam.

        Behavior:
        - Matches known vocabulary.
        - Increments hearing counters.
        - Extracts explicitly taught language expressions.
        - Detects Bengali and Chakma Unicode script.
        - Never guesses that Bengali-script text is Bangla.
        - Never invents a meaning for a newly detected phrase.
        """

        if not text or not text.strip():
            return {
                "matched_phrases": [],
                "new_learned": [],
            }

        lower_text = text.lower()

        matched = []
        new_learned = []

        # ---------------------------------------------------------------
        # 1. Match against existing vocabulary
        # ---------------------------------------------------------------

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    word_or_phrase,
                    language,
                    times_heard
                FROM learned_vocabulary
                """
            )

            rows = cursor.fetchall()
            now = utc_now_iso()

            for row in rows:
                phrase = row["word_or_phrase"]

                # Match full word or exact phrase.
                pattern = r"\b" + re.escape(phrase) + r"\b"

                if re.search(pattern, lower_text):
                    matched.append(phrase)

                    cursor.execute(
                        """
                        UPDATE learned_vocabulary
                        SET
                            times_heard = times_heard + 1,
                            last_heard_at = ?
                        WHERE id = ?
                        """,
                        (
                            now,
                            row["id"],
                        ),
                    )

            conn.commit()

        # ---------------------------------------------------------------
        # 2. Extract explicitly taught expressions
        # ---------------------------------------------------------------
        #
        # Supported examples:
        #
        # "in Chakma, X means Y"
        # "X in Chakma means Y"
        # "X means Y in Chakma"
        #
        # Supports:
        # - Latin script
        # - Bengali script
        # - Chakma Unicode
        #

        teach_patterns = [
            r"in\s+(bangla|chakma|chatgaya|sylheti)[,\s]+['\"]?(.+?)['\"]?\s+means?\s+['\"]?([^.,!?;\n]+)['\"]?",

            r"['\"]?(.+?)['\"]?\s+in\s+(bangla|chakma|chatgaya|sylheti)\s+means?\s+['\"]?([^.,!?;\n]+)['\"]?",

            r"['\"]?(.+?)['\"]?\s+means?\s+['\"]?([^.,!?;\n]+)['\"]?\s+in\s+(bangla|chakma|chatgaya|sylheti)",
        ]

        for pattern in teach_patterns:
            matches = re.finditer(
                pattern,
                text,
                re.IGNORECASE,
            )

            for match in matches:
                groups = match.groups()

                if len(groups) != 3:
                    continue

                if groups[0].lower() in [
                    "bangla",
                    "chakma",
                    "chatgaya",
                    "sylheti",
                ]:
                    language = groups[0].lower()
                    phrase = groups[1].strip()
                    meaning = groups[2].strip()

                elif groups[1].lower() in [
                    "bangla",
                    "chakma",
                    "chatgaya",
                    "sylheti",
                ]:
                    phrase = groups[0].strip()
                    language = groups[1].lower()
                    meaning = groups[2].strip()

                else:
                    phrase = groups[0].strip()
                    meaning = groups[1].strip()
                    language = groups[2].lower()

                if not phrase or not meaning:
                    continue

                if len(phrase) >= 60:
                    continue

                learned = self.learn_phrase(
                    word_or_phrase=phrase,
                    language=language,
                    meaning=meaning,
                    confidence=0.9,
                    source="user_taught",
                )

                new_learned.append(
                    learned.word_or_phrase
                )

        # ---------------------------------------------------------------
        # 3. Detect local-language scripts WITHOUT guessing language
        # ---------------------------------------------------------------
        #
        # Bengali script:
        # U+0980-U+09FF
        #
        # Chakma Unicode:
        # U+11100-U+1114F
        #
        # IMPORTANT:
        # Bengali script can represent both Bangla and Chakma.
        #
        # Therefore:
        # - Bengali script != automatically Bangla
        # - Script detection does not create vocabulary
        # - Script detection does not invent meanings
        #

        bengali_script_tokens = re.findall(
            r"[\u0980-\u09FF]+",
            text,
        )

        chakma_script_tokens = re.findall(
            r"[\U00011100-\U0001114F]+",
            text,
        )

        if bengali_script_tokens:
            matched.extend(
                [
                    f"[bengali-script] {token}"
                    for token in bengali_script_tokens
                    if len(token) >= 2
                ]
            )

        if chakma_script_tokens:
            matched.extend(
                [
                    f"[chakma-script] {token}"
                    for token in chakma_script_tokens
                    if len(token) >= 2
                ]
            )

        # ---------------------------------------------------------------
        # 4. Log utterance
        # ---------------------------------------------------------------

        detected_language = (
            "local-script-or-learned-language"
            if (matched or new_learned)
            else "unknown"
        )

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO language_hearing_logs (
                    raw_text,
                    detected_language,
                    matched_phrases,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    text[:300],
                    detected_language,
                    json.dumps(
                        matched + new_learned,
                        ensure_ascii=False,
                    ),
                    utc_now_iso(),
                ),
            )

            conn.commit()

        return {
            "matched_phrases": matched,
            "new_learned": new_learned,
        }

    def get_vocabulary(
        self,
        language: Optional[str] = None,
        limit: int = 100,
    ) -> List[LearnedPhrase]:
        """Retrieves learned vocabulary optionally filtered by language."""

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if language:
                cursor.execute(
                    """
                    SELECT *
                    FROM learned_vocabulary
                    WHERE language = ?
                    ORDER BY times_heard DESC
                    LIMIT ?
                    """,
                    (
                        language.lower(),
                        limit,
                    ),
                )

            else:
                cursor.execute(
                    """
                    SELECT *
                    FROM learned_vocabulary
                    ORDER BY times_heard DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            rows = cursor.fetchall()

            return [
                LearnedPhrase(**dict(row))
                for row in rows
            ]

    def search_vocabulary(
        self,
        query: str,
        limit: int = 20,
    ) -> List[LearnedPhrase]:
        """Searches vocabulary by keyword or meaning."""

        pattern = f"%{query.strip().lower()}%"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT *
                FROM learned_vocabulary
                WHERE
                    word_or_phrase LIKE ?
                    OR meaning LIKE ?
                    OR phonetic_script LIKE ?
                ORDER BY times_heard DESC
                LIMIT ?
                """,
                (
                    pattern,
                    pattern,
                    pattern,
                    limit,
                ),
            )

            rows = cursor.fetchall()

            return [
                LearnedPhrase(**dict(row))
                for row in rows
            ]

    def get_learning_stats(self) -> Dict[str, Any]:
        """Returns vocabulary metrics and learning progress."""

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM learned_vocabulary"
            )

            total = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT language, COUNT(*)
                FROM learned_vocabulary
                GROUP BY language
                """
            )

            by_language = dict(cursor.fetchall())

            cursor.execute(
                """
                SELECT
                    SUM(times_heard),
                    SUM(times_used)
                FROM learned_vocabulary
                """
            )

            heard_sum, used_sum = cursor.fetchone()

            cursor.execute(
                """
                SELECT
                    word_or_phrase,
                    language,
                    times_heard,
                    meaning
                FROM learned_vocabulary
                ORDER BY times_heard DESC
                LIMIT 5
                """
            )

            top_heard = [
                dict(row)
                for row in cursor.fetchall()
            ]

            return {
                "total_vocabulary": total,
                "languages": by_language,
                "total_times_heard": heard_sum or 0,
                "total_times_used": used_sum or 0,
                "top_phrases": top_heard,
                "status": "actively_listening",
            }

    def get_context_injection(
        self,
        limit: int = 12,
    ) -> str:
        """
        Generates a token-compact prompt injection explaining
        MaxIM's active linguistic familiarity with local languages.
        """

        vocabulary = self.get_vocabulary(
            limit=limit
        )

        if not vocabulary:
            return ""

        bangla_items = [
            f"'{phrase.word_or_phrase}' ({phrase.meaning})"
            for phrase in vocabulary
            if phrase.language == "bangla"
        ][:6]

        chakma_items = [
            f"'{phrase.word_or_phrase}' ({phrase.meaning})"
            for phrase in vocabulary
            if phrase.language == "chakma"
        ][:5]

        lines = [
            "### Adaptive Local Language & Dialect Mastery",
            (
                "You have an active memory of Sam's local languages "
                "and dialects. Use learned expressions naturally and "
                "only when their meaning is sufficiently trusted."
            ),
        ]

        if bangla_items:
            lines.append(
                f"- **Bangla**: {', '.join(bangla_items)}"
            )

        if chakma_items:
            lines.append(
                f"- **Chakma**: {', '.join(chakma_items)}"
            )

        lines.append(
            "- **Behavioral directive:** "
            "When Sam explicitly teaches you a new word or phrase, "
            "store its language, meaning, and original form. "
            "Do not invent meanings for unfamiliar expressions."
        )

        lines.append(
            "- **Phrasing & Natural Speaking Guidelines:**\n"
            "  1. **Fluid Code-Switching:** Blend English with learned local phrases naturally as a tech peer (e.g. 'Thik ache Sam, let\\'s check the logs', 'Sob bhalo, server is up'). Avoid stiff, literal textbook translations.\n"
            "  2. **Peer Register:** Use warm, friendly informal phrasing ('tumi' / buddy banter, not stiff bureaucratic 'apni').\n"
            "  3. **Dialect Integrity:** For low-resource dialects (Chakma, etc.), use the exact phrasing taught by Sam; do not guess unvetted grammar rules. If exploring a new sentence in a dialect, you can playfully ask: 'Did I phrase that naturally?'."
        )

        return "\n".join(lines)

    def sync_to_vault(self) -> Optional[Path]:
        """
        Exports learned language knowledge to the Obsidian vault
        for persistent human review.
        """

        try:
            vault_dir = Path(
                "f:/MAXIM V2/vault/02 - Knowledge"
            )

            if not vault_dir.exists():
                vault_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

            note_path = (
                vault_dir
                / "Learned Languages & Dialects.md"
            )

            vocabulary = self.get_vocabulary(
                limit=100
            )

            bangla_vocabulary = [
                value
                for value in vocabulary
                if value.language == "bangla"
            ]

            chakma_vocabulary = [
                value
                for value in vocabulary
                if value.language == "chakma"
            ]

            other_vocabulary = [
                value
                for value in vocabulary
                if value.language
                not in [
                    "bangla",
                    "chakma",
                ]
            ]

            markdown = [
                "# 🗣️ Learned Languages & Regional Dialects",
                "",
                (
                    "MaxIM's growing repository of local languages "
                    "and phrases acquired from conversation."
                ),
                (
                    f"**Last Updated:** `{utc_now_iso()}` | "
                    f"**Total Expressions:** `{len(vocabulary)}`"
                ),
                "",
                "## 🇧🇩 Bangla (Bengali)",
                "| Phrase | Meaning | Script / Notes | Heard | Used |",
                "|---|---|---|---|---|",
            ]

            for value in bangla_vocabulary:
                markdown.append(
                    f"| **{value.word_or_phrase}** "
                    f"| {value.meaning} "
                    f"| {value.phonetic_script or '-'} "
                    f"| {value.times_heard} "
                    f"| {value.times_used} |"
                )

            markdown.extend(
                [
                    "",
                    "## 🏔️ Chakma (Changma Vaj)",
                    "| Phrase | Meaning | Script / Notes | Heard | Used |",
                    "|---|---|---|---|---|",
                ]
            )

            for value in chakma_vocabulary:
                markdown.append(
                    f"| **{value.word_or_phrase}** "
                    f"| {value.meaning} "
                    f"| {value.phonetic_script or '-'} "
                    f"| {value.times_heard} "
                    f"| {value.times_used} |"
                )

            if other_vocabulary:
                markdown.extend(
                    [
                        "",
                        "## 🗺️ Other Regional Dialects",
                        "| Phrase | Language | Meaning | Heard |",
                        "|---|---|---|---|",
                    ]
                )

                for value in other_vocabulary:
                    markdown.append(
                        f"| **{value.word_or_phrase}** "
                        f"| {value.language} "
                        f"| {value.meaning} "
                        f"| {value.times_heard} |"
                    )

            markdown.append(
                "\n#maxim/language "
                "#knowledge/linguistics "
                "#local-dialects\n"
            )

            note_path.write_text(
                "\n".join(markdown),
                encoding="utf-8",
            )

            return note_path

        except Exception as exc:
            logger.warning(
                "Failed to export language note to vault: %s",
                exc,
            )

            return None


# Singleton instance
language_learner = LanguageLearner()
