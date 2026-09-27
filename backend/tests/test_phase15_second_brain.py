"""
Unit and integration tests for Phase 15: ZhiGui UI Second Brain & Autonomous Learning Loop.
Verifies skill crystallization, Obsidian vault synchronization, and error reflexion loops.
"""
import pytest
from pathlib import Path
from second_brain import SecondBrainEngine, LearnedSkill, ErrorReflexion

@pytest.fixture
def temp_brain(tmp_path: Path):
    db_file = tmp_path / "test_brain.db"
    skills_folder = tmp_path / "vault_skills"
    return SecondBrainEngine(db_path=db_file, vault_skills_dir=skills_folder)

def test_second_brain_init_and_seeding(temp_brain):
    """Verify tables are created and foundational skills are seeded."""
    skills = temp_brain.list_skills()
    assert len(skills) >= 3
    names = [s.name for s in skills]
    assert "sqlite_wal_checkpoint" in names
    assert "active_window_context_audit" in names

def test_crystallize_skill_and_vault_sync(temp_brain):
    """Verify crystallizing a skill writes to SQLite and creates an Obsidian note."""
    skill = temp_brain.crystallize_skill(
        name="git_push_workflow",
        description="Stages, commits with conventional prefix, and pushes branch.",
        trigger_keywords=["git push", "commit code", "push branch"],
        preconditions="Git repository clean",
        steps=[
            {"tool": "run_command", "args": {"CommandLine": "git status"}, "description": "Check status"},
            {"tool": "run_command", "args": {"CommandLine": "git push"}, "description": "Push commits"}
        ],
        sync_vault=True,
    )

    assert skill.name == "git_push_workflow"
    assert len(skill.steps) == 2
    assert skill.vault_path is not None

    note_path = Path(skill.vault_path)
    assert note_path.exists()
    content = note_path.read_text(encoding="utf-8")
    assert "Git Push Workflow" in content
    assert "git status" in content
    assert "[[Skills MOC]]" in content

def test_recall_skill_matching(temp_brain):
    """Verify searching for skills by trigger keyword or description."""
    matched = temp_brain.recall_skill("wal")
    assert len(matched) >= 1
    assert any(s.name == "sqlite_wal_checkpoint" for s in matched)

    matched_desc = temp_brain.recall_skill("intelligence scout")
    assert len(matched_desc) >= 1
    assert any(s.name == "daily_intel_synthesis" for s in matched_desc)

def test_record_error_reflexion_and_prompt_injection(temp_brain):
    """Verify error reflexion recording and prompt injection synthesis."""
    ref = temp_brain.record_error_reflexion(
        failed_tool="os_launch_app",
        error_message="Executable not found in system PATH",
        root_cause="Caller provided bare binary name without full path",
        corrective_rule="Always resolve binary location or use shutil.which before launching",
        session_id="session_test",
    )
    assert ref.id is not None
    assert ref.failed_tool == "os_launch_app"

    history = temp_brain.list_reflexions()
    assert len(history) == 1

    prompt_inj = temp_brain.get_prompt_context_injection()
    assert "ZhiGui Reflexion" in prompt_inj
    assert "os_launch_app" in prompt_inj
    assert "Always resolve binary location" in prompt_inj

def test_sync_skills_moc(temp_brain):
    """Verify Skills MOC note creation and wikilinks."""
    moc_path = temp_brain.sync_skills_moc()
    assert moc_path.exists()
    content = moc_path.read_text(encoding="utf-8")
    assert "Skills Map of Content" in content
    assert "[[Sqlite Wal Checkpoint]]" in content

def test_skills_tool_catalog():
    """Verify skills tools are registered in catalog."""
    from tools.catalog import tool_catalog, ToolsetName
    tools = tool_catalog.get_toolset(ToolsetName.SKILLS)
    assert len(tools) >= 4
    tool_names = [t["function"]["name"] for t in tools]
    assert "crystallize_skill" in tool_names
    assert "recall_skill" in tool_names
    assert "record_error_reflexion" in tool_names
    assert "list_learned_skills" in tool_names

def test_engine_skills_tools():
    """Verify engine.execute_tool runs second brain tools cleanly."""
    import json
    from engine import MaxIMAgentEngine
    eng = MaxIMAgentEngine()

    # 1. list_learned_skills
    r1 = eng.execute_tool("list_learned_skills", {"limit": 5}, session_id="test_skill")
    d1 = json.loads(r1)
    assert d1["status"] == "success"
    assert "skills" in d1

    # 2. recall_skill
    r2 = eng.execute_tool("recall_skill", {"query": "wal"}, session_id="test_skill")
    d2 = json.loads(r2)
    assert d2["status"] == "success"
    assert len(d2["skills"]) >= 1

    # 3. record_error_reflexion
    r3 = eng.execute_tool("record_error_reflexion", {
        "failed_tool": "test_dummy",
        "error_message": "Test timeout",
        "root_cause": "Network latency",
        "corrective_rule": "Increase timeout to 10s",
    }, session_id="test_skill")
    d3 = json.loads(r3)
    assert d3["status"] == "recorded"

def test_server_skills_endpoints():
    """Verify FastAPI server exposes the ZhiGui Second Brain endpoints."""
    from fastapi.testclient import TestClient
    from server import app
    client = TestClient(app)

    # 1. GET /api/skills
    r1 = client.get("/api/skills")
    assert r1.status_code == 200
    d1 = r1.json()
    assert "skills" in d1
    assert "count" in d1

    # 2. GET /api/skills/reflexions
    r2 = client.get("/api/skills/reflexions?limit=10")
    assert r2.status_code == 200
    d2 = r2.json()
    assert "reflexions" in d2

    # 3. POST /api/skills/sync-vault
    r3 = client.post("/api/skills/sync-vault")
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["status"] == "synced"

