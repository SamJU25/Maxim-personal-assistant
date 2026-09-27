"""
Unit & Integration Tests for Phase 9:
- Zylos Five-Layer Inside-Out Memory System.
- SQLite FTS5 BM25 Ranked Full-Text Search.
- Zylos 75% Context Safeguard Compaction Engine.
- Engine Tool Integration (query_five_layer_memory, compact_context_safeguard).
- FastAPI Phase 9 API Endpoints.
"""
import pytest
import json
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from server import app
from memory import memory_store, MessageRecord
from tools.vault_tool import vault_synapse
from five_layer_memory import five_layer_memory
from engine import agent_engine

client = TestClient(app)

def test_layer_1_identity():
    l1 = five_layer_memory.get_layer_1_identity()
    assert l1["layer"] == 1
    assert l1["name"] == "Identity & Persona"
    assert l1["soul_contract_loaded"] is True
    assert len(l1["telos_targets"]) > 0

def test_layer_2_state():
    l2 = five_layer_memory.get_layer_2_state("test_sess_p9")
    assert l2["layer"] == 2
    assert l2["name"] == "State & Perception"
    assert "active_window" in l2
    assert "resolution" in l2
    assert l2["session_id"] == "test_sess_p9"

def test_layer_3_references():
    l3 = five_layer_memory.get_layer_3_references(limit=5)
    assert l3["layer"] == 3
    assert l3["name"] == "References & Obsidian Graph"
    assert l3["vault_note_count"] > 0
    assert len(l3["references"]) > 0

def test_layer_4_sessions():
    sess_id = "test_l4_sess"
    memory_store.add_message(MessageRecord(session_id=sess_id, role="user", content="Turn 1"))
    memory_store.add_message(MessageRecord(session_id=sess_id, role="assistant", content="Turn 2"))

    l4 = five_layer_memory.get_layer_4_sessions(sess_id)
    assert l4["layer"] == 4
    assert l4["name"] == "Sessions & Episodic Dialogue"
    assert l4["turn_count"] >= 2
    assert l4["estimated_tokens"] > 0

def test_layer_5_archive():
    memory_store.remember_fact("test_cat", "p9_test_key", "p9_test_value")
    l5 = five_layer_memory.get_layer_5_archive()
    assert l5["layer"] == 5
    assert l5["name"] == "Long-term Semantic Archive"
    assert l5["fact_count"] > 0
    assert any(f["key"] == "p9_test_key" for f in l5["facts"])

def test_all_layers_unified():
    layers = five_layer_memory.get_all_layers("unified_test_sess")
    assert "layer_1_identity" in layers
    assert "layer_2_state" in layers
    assert "layer_3_references" in layers
    assert "layer_4_sessions" in layers
    assert "layer_5_archive" in layers
    assert "safeguard_status" in layers

def test_fts5_indexing_and_bm25_search():
    # Index a unique fact
    memory_store.remember_fact("preference", "quantum_hyperdrive", "Ultra-efficient warp reactor")
    
    # Search via SQLite FTS5
    fts_results = memory_store.search_fts("quantum_hyperdrive", limit=5)
    assert len(fts_results) > 0
    assert "quantum_hyperdrive" in fts_results[0]["title"] or "warp" in fts_results[0]["content"]

    # Search via unified five_layer_memory
    unified_results = five_layer_memory.search_all_layers("quantum_hyperdrive", limit=5)
    assert len(unified_results) > 0
    assert any("warp" in r["content"].lower() or "quantum" in r["title"].lower() for r in unified_results)

def test_safeguard_threshold_detection():
    sess_id = "test_safeguard_eval"
    # Under low load
    status_low = five_layer_memory.check_context_safeguard(sess_id, max_tokens=100000, threshold=0.75)
    assert status_low["triggered"] is False
    assert status_low["status"] == "healthy"

    # Under strict budget threshold
    status_high = five_layer_memory.check_context_safeguard(sess_id, max_tokens=100, threshold=0.5)
    assert status_high["triggered"] is True
    assert status_high["status"] == "warning_critical_compaction_required"

def test_safeguard_compaction_execution():
    sess_id = f"compaction_test_{uuid.uuid4().hex[:8]}"
    for i in range(8):
        memory_store.add_message(MessageRecord(session_id=sess_id, role="user", content=f"User goal {i}"))
        memory_store.add_message(MessageRecord(session_id=sess_id, role="assistant", content=f"Assistant answer {i}"))

    msgs_before = memory_store.get_messages(sess_id)
    assert len(msgs_before) == 16

    # Execute compaction
    res = five_layer_memory.execute_safeguard_compaction(sess_id, reason="Unit test compaction")
    assert res["status"] == "compacted"
    assert res["pruned_turns"] > 0
    assert res["checkpoint_title"].startswith("Checkpoint_")

    # Verify messages in session pruned to keep_last (4) + anchor note
    msgs_after = memory_store.get_messages(sess_id)
    assert len(msgs_after) <= 6
    assert any("[Zylos Context Safeguard:" in m.content for m in msgs_after)

    # Verify note exists in Obsidian vault
    note_data = vault_synapse.read_note(res["checkpoint_title"])
    assert note_data["found"] is True
    assert "## 1. Dialogue Trajectory" in note_data["content"]
    assert "#checkpoint" in note_data["tags"]

def test_engine_query_five_layer_tool():
    res_str = agent_engine.execute_tool(
        "query_five_layer_memory",
        {"query": "LifeOS", "limit": 3},
        session_id="test_sess"
    )
    res_data = json.loads(res_str)
    assert isinstance(res_data, list)

def test_engine_compact_safeguard_tool():
    sess_id = "engine_compact_sess"
    memory_store.add_message(MessageRecord(session_id=sess_id, role="user", content="Session data to compact"))
    res_str = agent_engine.execute_tool(
        "compact_context_safeguard",
        {"reason": "Testing tool execution"},
        session_id=sess_id
    )
    res_data = json.loads(res_str)
    assert res_data["status"] == "compacted"

def test_server_phase9_endpoints():
    sess_id = "server_p9_test_sess"
    memory_store.add_message(MessageRecord(session_id=sess_id, role="user", content="Hello server"))

    # 1. Five layers endpoint
    res_layers = client.get(f"/api/memory/five-layers?session_id={sess_id}")
    assert res_layers.status_code == 200
    ldata = res_layers.json()
    assert "layer_1_identity" in ldata
    assert "layer_2_state" in ldata

    # 2. Safeguard status endpoint
    res_stat = client.get(f"/api/memory/safeguard/status?session_id={sess_id}")
    assert res_stat.status_code == 200
    assert "capacity_percent" in res_stat.json()

    # 3. Memory search endpoint
    res_srch = client.post("/api/memory/search", json={"query": "TELOS", "limit": 3})
    assert res_srch.status_code == 200
    assert "results" in res_srch.json()

    # 4. Memory compact endpoint
    res_comp = client.post("/api/memory/compact", json={"session_id": sess_id, "reason": "API test"})
    assert res_comp.status_code == 200
    assert res_comp.json()["status"] == "compacted"
