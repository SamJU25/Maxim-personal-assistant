"""
Unit and integration tests for Conversation Tree & Presets Engine (LibreChat adaptation).
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from conversation_tree import ConversationTreeEngine

@pytest.fixture
def temp_tree():
    tmp_dir = Path(tempfile.mkdtemp())
    db_path = tmp_dir / "test_tree.db"
    vault_dir = tmp_dir / "vault"
    vault_dir.mkdir(parents=True)
    engine = ConversationTreeEngine(db_path=db_path, vault_dir=vault_dir)
    yield engine, tmp_dir, vault_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_default_presets_seeded(temp_tree):
    engine, _, _ = temp_tree
    presets = engine.list_presets()
    preset_ids = [p["id"] for p in presets]
    assert "preset_executive_assistant" in preset_ids
    assert "preset_code_architect" in preset_ids
    assert "preset_video_analyst" in preset_ids
    assert "preset_financial_auditor" in preset_ids

def test_main_branch_creation_and_node_chain(temp_tree):
    engine, _, _ = temp_tree
    session_id = "sess_001"
    
    # 1. First user message
    n1 = engine.add_node(session_id=session_id, role="user", content="Plan project alpha architecture.")
    assert n1["parent_message_id"] is None
    assert n1["role"] == "user"
    
    # 2. Assistant response
    n2 = engine.add_node(session_id=session_id, role="assistant", content="Here is the modular blueprint.")
    assert n2["parent_message_id"] == n1["id"]
    
    # 3. Verify history
    history = engine.get_branch_history(session_id=session_id)
    assert len(history) == 2
    assert history[0]["content"] == "Plan project alpha architecture."
    assert history[1]["content"] == "Here is the modular blueprint."

def test_branch_forking_and_divergence(temp_tree):
    engine, _, _ = temp_tree
    session_id = "sess_002"
    
    n1 = engine.add_node(session_id=session_id, role="user", content="Step 1: Setup database schema.")
    n2 = engine.add_node(session_id=session_id, role="assistant", content="Schema defined with SQLite WAL.")
    
    # Fork branch from n2 to explore NoSQL alternative
    fork_res = engine.fork_branch(
        session_id=session_id,
        fork_message_id=n2["id"],
        new_branch_name="NoSQL Exploration"
    )
    assert fork_res["branch_id"] is not None
    assert fork_res["fork_message_id"] == n2["id"]
    
    # Add new turn in the forked branch
    n3_fork = engine.add_node(
        session_id=session_id,
        branch_id=fork_res["branch_id"],
        role="user",
        content="What if we used MongoDB instead?"
    )
    n4_fork = engine.add_node(
        session_id=session_id,
        branch_id=fork_res["branch_id"],
        role="assistant",
        content="MongoDB introduces operational overhead compared to embedded SQLite."
    )
    
    # Verify forked branch lineage contains n1, n2, n3_fork, n4_fork
    fork_history = engine.get_branch_history(session_id=session_id, branch_id=fork_res["branch_id"])
    assert len(fork_history) == 4
    assert fork_history[0]["content"] == "Step 1: Setup database schema."
    assert fork_history[1]["content"] == "Schema defined with SQLite WAL."
    assert fork_history[2]["content"] == "What if we used MongoDB instead?"
    assert fork_history[3]["content"] == "MongoDB introduces operational overhead compared to embedded SQLite."

    # Verify main branch only contains n1, n2
    main_branches = [b for b in engine.list_branches(session_id=session_id) if b["name"] == "Main Branch"]
    assert len(main_branches) == 1
    main_history = engine.get_branch_history(session_id=session_id, branch_id=main_branches[0]["branch_id"])
    assert len(main_history) == 2

def test_switch_branch(temp_tree):
    engine, _, _ = temp_tree
    session_id = "sess_003"
    
    n1 = engine.add_node(session_id=session_id, role="user", content="Init")
    fork = engine.fork_branch(session_id=session_id, fork_message_id=n1["id"], new_branch_name="Branch B")
    
    branches = engine.list_branches(session_id=session_id)
    active_b = next(b for b in branches if b["is_active"])
    assert active_b["branch_id"] == fork["branch_id"]

    # Switch back to main
    main_b = next(b for b in branches if b["name"] == "Main Branch")
    switched = engine.switch_branch(session_id=session_id, branch_id=main_b["branch_id"])
    assert switched is True

    branches_after = engine.list_branches(session_id=session_id)
    active_after = next(b for b in branches_after if b["is_active"])
    assert active_after["branch_id"] == main_b["branch_id"]

def test_save_and_get_preset(temp_tree):
    engine, _, _ = temp_tree
    custom = engine.save_preset(
        preset_id="preset_researcher",
        name="Deep Research Specialist",
        model_alias="reasoning",
        temperature=0.3,
        system_prompt="Execute systematic research with source verification.",
        toolsets=["reach", "vault", "memory"],
        description="Focused on web intelligence and note synthesis."
    )
    assert custom["id"] == "preset_researcher"
    
    fetched = engine.get_preset("preset_researcher")
    assert fetched is not None
    assert fetched["name"] == "Deep Research Specialist"
    assert fetched["temperature"] == 0.3
    assert "reach" in fetched["toolsets"]

def test_save_artifact_and_vault_sync(temp_tree):
    engine, _, vault_dir = temp_tree
    session_id = "sess_art"
    branch_id = engine.get_or_create_main_branch(session_id)
    
    # Save version 1
    art_v1 = engine.save_artifact(
        session_id=session_id,
        branch_id=branch_id,
        title="Payment_Module",
        artifact_type="code",
        content="def process_payment(amount):\n    return True"
    )
    assert art_v1["version"] == 1
    
    # Save version 2 with updated code
    art_v2 = engine.save_artifact(
        session_id=session_id,
        branch_id=branch_id,
        title="Payment_Module",
        artifact_type="code",
        content="def process_payment(amount):\n    assert amount > 0\n    return True"
    )
    assert art_v2["version"] == 2
    
    # Check vault files created
    art_dir = vault_dir / "02 - Knowledge" / "Artifacts"
    assert (art_dir / "Payment_Module_v1.md").exists()
    assert (art_dir / "Payment_Module_v2.md").exists()
    
    v2_text = (art_dir / "Payment_Module_v2.md").read_text(encoding="utf-8")
    assert "assert amount > 0" in v2_text

    # List artifacts
    all_arts = engine.list_artifacts(session_id=session_id)
    assert len(all_arts) == 2
