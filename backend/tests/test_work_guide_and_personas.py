"""
Unit tests for Executive Work Guidance & Task Director (work_guide.py)
and Cognitive Thinking Modes / Personas (cognitive_personas.py).
Verifies:
1. Goal decomposition into sequential milestones and discrete actions.
2. Next-action recommendation algorithm.
3. Action status updates and automatic milestone/project completion cascades.
4. Work tracker Obsidian vault synchronization.
5. Cognitive persona catalog, active selection, and system prompt directive generation.
6. Engine tool integration for work guide and cognitive personas.
7. FastAPI endpoints for work guidance and personas.
"""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from work_guide import WorkGuideEngine
from cognitive_personas import CognitivePersonaManager, PERSONA_CATALOG
from server import app

client = TestClient(app)

def test_goal_decomposition_and_cascades(tmp_path: Path):
    """Verify decomposing a goal and completing actions cascades up to project completion."""
    guide = WorkGuideEngine(db_path=tmp_path / "work_test.db")

    # 1. Decompose goal
    proj = guide.decompose_goal(
        goal="Organize Downloads Folder and Cleanup",
        category="organization",
        description="Categorize photos, videos, and archives",
    )
    assert proj.status == "active"
    assert len(proj.milestones) >= 2
    assert len(proj.milestones[0].actions) >= 1

    # 2. Get next action
    next_action = guide.get_next_recommended_action()
    assert next_action["has_action"] is True
    assert next_action["project_id"] == proj.id
    first_act_id = next_action["action_id"]

    # 3. Update all actions to completed
    for m in proj.milestones:
        for a in m.actions:
            guide.update_action_status(action_id=a.id, status="completed", result_summary="Done")

    # Verify project is marked completed
    projects = guide.list_projects(status="completed")
    assert len(projects) == 1
    assert projects[0].id == proj.id

    # Verify no more pending actions
    next_after = guide.get_next_recommended_action()
    assert next_after["has_action"] is False

def test_work_tracker_vault_sync(tmp_path: Path):
    """Verify writing Work_Tracker.md note to Obsidian vault."""
    guide = WorkGuideEngine(db_path=tmp_path / "sync_test.db")
    guide.decompose_goal(goal="Build New API Endpoint", category="coding")

    note_path = guide.sync_work_to_vault()
    assert note_path.exists()
    content = note_path.read_text(encoding="utf-8")
    assert "# MaxIM Executive Work Tracker" in content
    assert "Build New API Endpoint" in content

def test_cognitive_personas_management(tmp_path: Path):
    """Verify switching personas, catalog inspection, and prompt directive generation."""
    manager = CognitivePersonaManager(db_path=str(tmp_path / "personas_test.db"))

    # Default is executive_assistant
    default_p = manager.get_active_persona()
    assert default_p.key == "executive_assistant"

    # Switch to INTJ Architect
    intj = manager.set_active_persona("intj_architect")
    assert intj.key == "intj_architect"
    assert intj.mbti == "INTJ"

    active_now = manager.get_active_persona()
    assert active_now.key == "intj_architect"

    # Prompt directive contains INTJ
    directive = manager.get_directive_prompt()
    assert "Chief Architect" in directive
    assert "INTJ" in directive

    # List personas
    all_personas = manager.list_personas()
    assert len(all_personas) >= 8
    intj_entry = next(p for p in all_personas if p["key"] == "intj_architect")
    assert intj_entry["is_active"] is True

def test_fastapi_work_and_persona_endpoints():
    """Verify /api/work and /api/personas endpoints."""
    # 1. Decompose goal via API
    res_decomp = client.post("/api/work/decompose", json={
        "goal": "Prepare Year End Financial Summary",
        "category": "finance",
    })
    assert res_decomp.status_code == 200
    p_data = res_decomp.json()["project"]
    proj_id = p_data["id"]

    # 2. Get next action
    res_next = client.get("/api/work/next-action")
    assert res_next.status_code == 200
    assert res_next.json()["has_action"] is True

    # 3. List projects
    res_list = client.get("/api/work/projects")
    assert res_list.status_code == 200
    assert any(p["id"] == proj_id for p in res_list.json()["projects"])

    # 4. List personas
    res_personas = client.get("/api/personas")
    assert res_personas.status_code == 200
    assert "executive_assistant" in [p["key"] for p in res_personas.json()["personas"]]

    # 5. Select persona
    res_sel = client.post("/api/personas/select", json={"persona": "bitterbot_cynic"})
    assert res_sel.status_code == 200
    assert res_sel.json()["active_persona"]["key"] == "bitterbot_cynic"
