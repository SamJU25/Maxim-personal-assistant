"""
Unit and integration tests for Voice Studio Engine (VoiceStudio adaptation).
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from voice_studio import VoiceStudioEngine, clean_markdown_for_speech

@pytest.fixture
def temp_studio():
    tmp_dir = Path(tempfile.mkdtemp())
    db_path = tmp_dir / "test_studio.db"
    vault_dir = tmp_dir / "vault"
    vault_dir.mkdir(parents=True)
    engine = VoiceStudioEngine(db_path=db_path, vault_dir=vault_dir)
    yield engine, tmp_dir, vault_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_clean_markdown_for_speech():
    raw_md = """# Meeting Notes & Briefing
> **Date:** 2026-09-25

Here is the plan for [[Phase 23|The Architecture]]:
- Review code in `server.py`
- Check table: | Name | Score |
- Visit [OpenAI](https://openai.com) for specs.
```python
def test(): pass
```
The architecture is **solid** and *verified*.
"""
    clean = clean_markdown_for_speech(raw_md)
    assert "Meeting Notes & Briefing" in clean
    assert "def test" not in clean  # code block stripped
    assert "https://" not in clean  # url stripped
    assert "The Architecture" in clean  # wikilink simplified
    assert "solid and verified" in clean  # asterisks stripped

def test_default_voice_profiles(temp_studio):
    engine, _, _ = temp_studio
    profs = engine.list_profiles()
    assert len(profs) >= 4
    prof_ids = [p["id"] for p in profs]
    assert "host_maxim" in prof_ids
    assert "analyst_jenny" in prof_ids
    assert "critic_eric" in prof_ids
    assert "bilingual_pradeep" in prof_ids

def test_synthesize_note_to_audio(temp_studio):
    engine, _, vault_dir = temp_studio
    
    # Create sample note in vault
    note_dir = vault_dir / "00 - LifeOS"
    note_dir.mkdir(parents=True)
    sample_note = note_dir / "Executive_Morning_Brief.md"
    sample_note.write_text("""# Executive Morning Brief
Today we focus on high-leverage architectural refactorings and deterministic test verification.
All milestones are tracking according to plan.
""", encoding="utf-8")

    prod = engine.synthesize_note_to_audio(str(sample_note), profile_id="host_maxim")
    assert prod["production_id"] is not None
    assert prod["title"] == "Executive_Morning_Brief"
    assert Path(prod["audio_path"]).exists()
    assert Path(prod["audio_path"]).stat().st_size > 0

    # Verify record in DB
    prods = engine.list_productions()
    assert len(prods) == 1
    assert prods[0]["title"] == "Executive_Morning_Brief"

def test_synthesize_dialogue(temp_studio):
    engine, _, vault_dir = temp_studio
    script = [
        {"speaker": "host_maxim", "text": "Welcome everyone to today's technical architecture sync."},
        {"speaker": "analyst_jenny", "text": "The test coverage is currently at one hundred percent with zero warnings."},
        {"speaker": "critic_eric", "text": "Let us make sure we keep simplicity first and avoid speculative bloat."}
    ]

    res = engine.synthesize_dialogue(script=script, title="Sprint_Sync_Podcast")
    assert res["production_id"] is not None
    assert res["turns_count"] == 3
    assert Path(res["audio_path"]).exists()
    assert Path(res["audio_path"]).stat().st_size > 0
