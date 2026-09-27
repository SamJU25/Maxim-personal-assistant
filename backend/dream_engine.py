"""
Bitterbot-Inspired Dream & Reflection Engine for MaxIM.
Performs offline memory consolidation, synthesizes daily thoughts into Obsidian vault notes,
and generates sarcastic morning wake-up greetings tied to LifeOS TELOS goals.
Repository reference: https://github.com/Bitterbot-AI/bitterbot-desktop
"""
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from config import config
from memory import SQLiteMemoryStore, MessageRecord
from telos import LifeOSEngine
from tools.vault_tool import vault_synapse

class BitterbotDreamEngine:
    def __init__(
        self,
        memory_store: Optional[SQLiteMemoryStore] = None,
        lifeos: Optional[LifeOSEngine] = None,
    ):
        self.memory = memory_store or SQLiteMemoryStore()
        self.lifeos = lifeos or LifeOSEngine()

    def run_dream_cycle(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a background dream & reflection cycle:
        1. Reads recent messages and facts.
        2. Synthesizes key takeaways and concepts.
        3. Writes a reflection note in vault/01 - Memory/.
        """
        # Get recent messages
        if session_id:
            messages = self.memory.get_messages(session_id, limit=30)
        else:
            # Get latest session messages
            sessions = self.memory.list_sessions()
            if sessions:
                messages = self.memory.get_messages(sessions[0]["id"], limit=30)
            else:
                messages = []

        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

        if not messages:
            return {
                "status": "skipped",
                "reason": "No recent session messages to reflect on.",
                "timestamp": now.isoformat(),
            }

        # Extract topics, wikilink candidates, and key thoughts
        topics = set()
        user_thoughts = []
        for m in messages:
            if m.role == "user":
                user_thoughts.append(m.content)
                # Extract potential topics (capitalized phrases or words)
                found = re.findall(r"\b[A-Z][a-zA-Z0-9_-]+\b", m.content)
                topics.update(found)

        # Synthesize dream reflection markdown
        telos_profile = self.lifeos.load()
        active_target = telos_profile.targets[0] if telos_profile.targets else "Master Project Milestone"

        # Query idle scout for fresh overnight intelligence
        overnight_section = ""
        news_mention = ""
        try:
            from idle_scout import idle_scout
            latest_intel = idle_scout.get_latest_intel()
            if latest_intel and latest_intel.get("status") == "success":
                brief = latest_intel.get("briefing", {})
                headline = brief.get("headline", "")
                findings = brief.get("findings", [])
                if headline or findings:
                    findings_md = "\n".join(f"- {f.get('title', '')} ({f.get('source', '')})" for f in findings[:3])
                    overnight_section = f"\n## 📡 Overnight Curated Intel\n**{headline}**\n{findings_md}\n"
                    news_mention = f" Overnight radar caught: '{headline}'."
        except Exception:
            pass

        dream_note_content = f"""# Dream Reflection — {date_str}
Synthesized by **MaxIM Dream Engine** during background reflection.

## 🌙 Core Takeaways
- User engaged in {len(user_thoughts)} conversation turns.
- Active target alignment: [[{active_target}]]
- Discovered concepts: {", ".join(f"[[{t}]]" for t in list(topics)[:6])}
{overnight_section}
## 💡 Synthesized Insights
{self._summarize_thoughts(user_thoughts)}

## 🎯 Next Steps
- Verify execution receipts against [[TELOS]].
- Continue progress on active execution projects.

#dream #reflection #memory #bitterbot #scout
"""

        note_title = f"Dream Reflection - {date_str}"
        write_res = vault_synapse.write_note(
            title=note_title,
            content=dream_note_content,
            folder="01 - Memory",
            tags=["#dream", "#reflection"],
        )

        # Also store reflection fact in SQLite memory
        self.memory.remember_fact(
            category="reflection",
            key=f"last_dream_{date_str}",
            value=f"Consolidated {len(user_thoughts)} thoughts; linked {len(topics)} topics.{news_mention}",
            session_id=session_id,
        )

        return {
            "status": "completed",
            "note_path": write_res.get("path"),
            "date": date_str,
            "thoughts_processed": len(user_thoughts),
            "topics_linked": list(topics)[:6],
            "overnight_intel": bool(overnight_section),
        }

    def _summarize_thoughts(self, thoughts: List[str]) -> str:
        if not thoughts:
            return "Quiet day with minimal conversational drift."
        snippets = [f"- {t[:100]}..." if len(t) > 100 else f"- {t}" for t in thoughts[:5]]
        return "\n".join(snippets)

    def get_morning_greeting(self) -> str:
        """
        Generates a witty, sarcastic morning wake-up greeting
        combining dream cycle results and active TELOS milestones.
        """
        profile = self.lifeos.load()
        target = profile.targets[0] if profile.targets else "your pending tasks"

        # Check for latest dream reflection fact
        facts = self.memory.get_facts("reflection")
        recent_reflection = facts[0].value if facts else "Consolidated your notes and pruned the graph."

        greeting = (
            f"I'm awake. While you were sleeping, I ran the dream cycle: {recent_reflection} "
            f"Your #1 target right now is '{target}'. Ready to actually do some work today, "
            f"or are we going to spend 2 hours rearranging window layouts?"
        )
        return greeting

    def generate_morning_greeting(self) -> str:
        """Alias for get_morning_greeting."""
        return self.get_morning_greeting()

# Singleton instance
dream_engine = BitterbotDreamEngine()

