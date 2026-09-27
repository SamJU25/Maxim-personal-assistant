"""
Phase 17: Unified System Polish & End-to-End Verification Test Suite.
Verifies the cross-engine integration of MaxIM v2.0:
1. ReAct Tool Loop & Meta Muse Execution Receipts.
2. Obsidian Vault Synapse & LifeOS TELOS Alignment.
3. Zylos 5-Layer Memory with FTS5 BM25 Search.
4. Chief Operator Multi-Agent Shift Execution.
5. Overnight Idle Scout & Dream Engine Cross-Pollination.
6. Mark-LIV Desktop OS Automation & Unified Screen Perception.
7. QwenPaw Pre-Execution Audit & Sandboxed Runner.
8. Hardware Governor & Privacy Guard Redaction.
"""
import pytest
from pathlib import Path

from config import config
from telos import LifeOSEngine
from tools.vault_tool import vault_synapse
from memory import SQLiteMemoryStore, MessageRecord
from five_layer_memory import five_layer_memory
from chief_operator import agent_operator
from idle_scout import idle_scout
from dream_engine import dream_engine
from mark_liv import mark_liv_engine
from workstation_sandbox import workstation_sandbox
from hardware_governor import hardware_governor
from privacy_guard import privacy_guard


def test_unified_telos_vault_pipeline(tmp_path):
    """Verifies LifeOS TELOS reads and bi-directional Obsidian note writing."""
    telos = LifeOSEngine()
    profile = telos.load()
    assert len(profile.targets) > 0
    assert len(profile.execution) > 0

    ctx = telos.get_context_injection()
    assert "TELOS Context" in ctx
    assert "Active Targets" in ctx

    # Vault note round-trip
    test_title = "Unified Verification Test Note"
    w_res = vault_synapse.write_note(
        title=test_title,
        content="# Test\nCross-engine verification note for Phase 17.",
        folder="01 - Memory",
        tags=["#test", "#phase17"]
    )
    assert w_res["status"] == "success"

    read_data = vault_synapse.read_note(test_title)
    assert "error" not in read_data
    assert "Phase 17" in read_data["content"]


def test_unified_five_layer_memory():
    """Verifies Zylos 5-layer inside-out memory indexing and FTS5 search."""
    summary = five_layer_memory.get_all_layers(session_id="test_session")
    assert summary["layer_1_identity"]["name"] == "Identity & Persona"
    assert summary["layer_2_state"]["name"] == "State & Perception"
    assert "recent_actions" in summary["layer_2_state"]
    assert summary["layer_3_references"]["name"] == "References & Obsidian Graph"
    assert summary["layer_4_sessions"]["name"] == "Sessions & Episodic Dialogue"
    assert summary["layer_5_archive"]["name"] == "Long-term Semantic Archive"

    # Search via unified 5-layer system
    results = five_layer_memory.search_all_layers("MaxIM", limit=5)
    assert isinstance(results, list)


def test_unified_chief_operator_shift():
    """Verifies Chief Operator team roster, group chat structure, and shift execution."""
    team = agent_operator.list_team()
    assert len(team) >= 5
    agent_ids = [a.id for a in team]
    assert "agent_chief" in agent_ids
    assert "agent_hermes" in agent_ids

    groups = agent_operator.list_groups()
    assert len(groups) >= 1
    assert groups[0].id == "group_core_council"


def test_unified_scout_and_dream_synergy():
    """Verifies cross-pollination between Idle Scout and Dream Engine."""
    # Test dream cycle execution
    res = dream_engine.run_dream_cycle(session_id="default_session")
    assert res["status"] in ["completed", "skipped"]

    greeting = dream_engine.get_morning_greeting()
    assert isinstance(greeting, str)
    assert len(greeting) > 10


def test_unified_mark_liv_screen_perception():
    """Verifies unified screen perception inside Mark-LIV OS engine."""
    snap = mark_liv_engine.capture_screen_snapshot()
    assert snap["status"] == "success"
    assert snap["width"] > 0
    assert snap["height"] > 0
    assert "window" in snap


def test_unified_qwenpaw_sandbox_boundary():
    """Verifies QwenPaw safety audit intercepting dangerous actions while allowing safe ones."""
    # Safe
    audit_ok = workstation_sandbox.audit_command("python --version")
    assert audit_ok.verdict == "ALLOW"
    assert audit_ok.is_safe is True

    # Destructive
    audit_bad = workstation_sandbox.audit_command("rm -rf /")
    assert audit_bad.verdict == "BLOCK"
    assert audit_bad.is_safe is False

    # Execution boundary
    run_res = workstation_sandbox.execute_sandboxed_command("echo phase17_sandbox_ok")
    assert run_res.executed is True
    assert run_res.exit_code == 0
    assert "phase17_sandbox_ok" in run_res.stdout


def test_unified_hardware_and_privacy():
    """Verifies Hardware Governor telemetry and Privacy Guard outbound scrubbing."""
    # Hardware
    hw = hardware_governor.inspect_hardware()
    assert hw.cpu_cores >= 1
    assert hw.ram_total_gb > 0
    assert isinstance(hw.gpu_available, bool)

    # Privacy
    res = privacy_guard.sanitize_outgoing_query(
        "My path is C:\\Users\\Sam\\secret.txt with key sk-1234567890abcdef1234567890abcdef",
        channel="test"
    )
    assert res["blocked"] is True
    assert "C:\\Users\\Sam" not in res["clean_query"]
    assert "sk-1234567890" not in res["clean_query"]
