"""
Unit tests for Phase 5: Bitterbot Dream Engine & Voice Engine.
Tests offline memory consolidation, wake-up greetings, and audio speech formatting.
"""
import pytest
from pathlib import Path
from dream_engine import BitterbotDreamEngine
from voice import voice_engine
from memory import SQLiteMemoryStore, MessageRecord
from telos import LifeOSEngine
from tools.vault_tool import ObsidianVaultSynapse

def test_dream_cycle_empty_session(tmp_path: Path):
    """Verify dream cycle skips cleanly when no messages exist."""
    db = SQLiteMemoryStore(db_path=tmp_path / "test.db")
    dreamer = BitterbotDreamEngine(memory_store=db)
    
    res = dreamer.run_dream_cycle(session_id="empty_sess")
    assert res["status"] == "skipped"

def test_dream_cycle_reflection_note_creation(tmp_path: Path):
    """Verify dream cycle synthesizes thoughts into an Obsidian vault note."""
    db = SQLiteMemoryStore(db_path=tmp_path / "test.db")
    db.add_message(MessageRecord(session_id="sess_01", role="user", content="Researching DeepSeek and MoE routing today."))
    db.add_message(MessageRecord(session_id="sess_01", role="assistant", content="Focus on Latent Attention cache."))
    db.add_message(MessageRecord(session_id="sess_01", role="user", content="Also need to fix Three.js Galaxy rendering."))

    dreamer = BitterbotDreamEngine(memory_store=db)
    res = dreamer.run_dream_cycle(session_id="sess_01")
    
    assert res["status"] == "completed"
    assert res["thoughts_processed"] == 2
    assert "DeepSeek" in res["topics_linked"] or "Three" in res["topics_linked"]
    assert res["note_path"] is not None

    # Verify fact stored in SQLite
    facts = db.get_facts("reflection")
    assert len(facts) > 0
    assert "Consolidated" in facts[0].value

def test_morning_greeting_sarcasm():
    """Verify morning greeting combines dream reflection, TELOS targets, and sarcasm."""
    dreamer = BitterbotDreamEngine()
    greeting = dreamer.get_morning_greeting()
    
    assert "I'm awake" in greeting
    assert "target" in greeting.lower() or "telos" in greeting.lower()
    assert len(greeting) > 50

def test_voice_text_formatting():
    """Verify long technical outputs are shortened to punchy voice replies."""
    long_text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
    formatted = voice_engine.format_text_for_speech(long_text)
    
    # Must only contain first 3 sentences
    assert "Sentence four" not in formatted
    assert "Sentence five" not in formatted
    assert "Sentence one" in formatted

@pytest.mark.asyncio
async def test_voice_speech_synthesis_test_mode():
    """Verify audio bytes synthesis in test mode."""
    audio_bytes = await voice_engine.synthesize_speech("Hello MaxIM", test_mode=True)
    assert isinstance(audio_bytes, bytes)
    assert len(audio_bytes) > 0
