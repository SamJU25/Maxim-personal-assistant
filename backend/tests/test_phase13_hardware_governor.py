"""
Unit tests for Phase 13: OpenJarvis Local-First Hardware & Cost Governor.
Defensive verification of hardware telemetry, pricing models, budget caps, and dynamic routing.
"""
import pytest
from pathlib import Path
from hardware_governor import (
    HardwareGovernorEngine,
    HardwareTelemetry,
    CostGovernorSettings,
    CostLedgerRecord,
)

@pytest.fixture
def temp_governor(tmp_path: Path):
    db_file = tmp_path / "test_governor.db"
    return HardwareGovernorEngine(db_path=db_file)

def test_hardware_telemetry_gathering(temp_governor):
    """Verify hardware telemetry gathers real CPU, RAM, and GPU stats without crashing."""
    telemetry = temp_governor.inspect_hardware(ping_ollama=False)
    assert isinstance(telemetry, HardwareTelemetry)
    assert telemetry.cpu_cores >= 1
    assert telemetry.ram_total_gb > 0
    assert 0.0 <= telemetry.ram_percent <= 100.0

    # If GPU is detected (like RTX 4050 on host), verify fields
    if telemetry.gpu_available:
        assert telemetry.gpu_name is not None
        assert telemetry.vram_total_mb > 0
        assert telemetry.vram_free_mb >= 0

def test_calculate_cost_and_savings():
    """Verify cost calculation across cloud providers and zero cost for local Ollama."""
    # Ollama is always $0.00 and generates savings
    cost, savings = HardwareGovernorEngine.calculate_cost("ollama", "llama3.2", 1000, 500)
    assert cost == 0.0
    assert savings > 0.0

    # Google Gemini 2.0 Flash ($0.10 in, $0.40 out per 1M)
    cost_gemini, savings_gemini = HardwareGovernorEngine.calculate_cost("google", "gemini-2.0-flash", 1_000_000, 1_000_000)
    assert round(cost_gemini, 2) == 0.50
    assert savings_gemini > 0.0

    # DeepSeek Chat ($0.14 in, $0.28 out per 1M)
    cost_ds, _ = HardwareGovernorEngine.calculate_cost("deepseek", "deepseek-chat", 1_000_000, 1_000_000)
    assert round(cost_ds, 2) == 0.42

def test_cost_governor_settings_lifecycle(temp_governor):
    """Verify settings can be queried and updated."""
    initial = temp_governor.get_settings()
    assert initial.daily_budget_usd == 1.00
    assert initial.hard_cap_enabled is True

    updated = temp_governor.update_settings(
        daily_budget_usd=2.50,
        prefer_local_first=True,
        vram_headroom_threshold_percent=90.0,
    )
    assert updated.daily_budget_usd == 2.50
    assert updated.prefer_local_first is True
    assert updated.vram_headroom_threshold_percent == 90.0

    retrieved = temp_governor.get_settings()
    assert retrieved.daily_budget_usd == 2.50
    assert retrieved.prefer_local_first is True

def test_cost_ledger_recording_and_summary(temp_governor):
    """Verify logging turns into cost ledger and computing daily spend summaries."""
    # Record cloud turn
    temp_governor.record_usage(
        provider="google",
        model="gemini-2.0-flash",
        input_tokens=10000,
        output_tokens=2000,
        session_id="session_test",
        task_complexity="routine",
    )

    # Record free local turn
    temp_governor.record_usage(
        provider="ollama",
        model="llama3.2",
        input_tokens=5000,
        output_tokens=1000,
        session_id="session_test",
        task_complexity="routine",
        routing_decision="local_routed",
    )

    summary = temp_governor.get_spend_summary_today()
    assert summary["total_turns"] == 2
    assert summary["total_tokens"] == 18000
    assert summary["spend_today_usd"] > 0
    assert summary["savings_today_usd"] > 0
    assert summary["hard_cap_exceeded"] is False

    recent = temp_governor.get_recent_ledger(limit=5)
    assert len(recent) == 2
    assert recent[0].provider == "ollama"
    assert recent[1].provider == "google"

def test_budget_hard_cap_enforcement(temp_governor):
    """Verify hard cap triggers when spend exceeds budget."""
    temp_governor.update_settings(daily_budget_usd=0.001, hard_cap_enabled=True, auto_downgrade_to_local=True)

    # Incur spend above $0.001
    temp_governor.record_usage(
        provider="openai",
        model="gpt-4o",
        input_tokens=5000,
        output_tokens=2000,
    )

    summary = temp_governor.get_spend_summary_today()
    assert summary["hard_cap_exceeded"] is True

    routing = temp_governor.evaluate_routing(task_complexity="complex")
    # Because Ollama is offline or online, decision must be budget-aware
    assert routing["decision"] in ["budget_downgraded", "budget_halted"]

def test_governor_tools_registered_in_catalog():
    """Verify governor tools are present in catalog."""
    from tools.catalog import tool_catalog, ToolsetName
    tools = tool_catalog.get_toolset(ToolsetName.GOVERNOR)
    assert len(tools) >= 3
    tool_names = [t["function"]["name"] for t in tools]
    assert "get_hardware_status" in tool_names
    assert "get_cost_governor_metrics" in tool_names
    assert "update_cost_governor_settings" in tool_names

def test_engine_governor_tools_execution():
    """Verify engine.execute_tool executes governor tools and returns valid json."""
    import json
    from engine import MaxIMAgentEngine
    engine = MaxIMAgentEngine()

    # 1. get_hardware_status
    res_raw = engine.execute_tool("get_hardware_status", {}, session_id="test_sess")
    res = json.loads(res_raw)
    assert res["status"] == "success"
    assert "hardware" in res

    # 2. get_cost_governor_metrics
    res_m_raw = engine.execute_tool("get_cost_governor_metrics", {}, session_id="test_sess")
    res_m = json.loads(res_m_raw)
    assert res_m["status"] == "success"
    assert "metrics" in res_m

    # 3. update_cost_governor_settings
    res_u_raw = engine.execute_tool("update_cost_governor_settings", {"daily_budget_usd": 3.0}, session_id="test_sess")
    res_u = json.loads(res_u_raw)
    assert res_u["status"] == "updated"
    assert res_u["settings"]["daily_budget_usd"] == 3.0

def test_server_governor_endpoints():
    """Verify FastAPI server exposes the hardware governor endpoints."""
    from fastapi.testclient import TestClient
    from server import app
    client = TestClient(app)

    # 1. GET /api/hardware/telemetry
    r1 = client.get("/api/hardware/telemetry")
    assert r1.status_code == 200
    d1 = r1.json()
    assert "cpu_cores" in d1
    assert "ram_total_gb" in d1

    # 2. GET /api/hardware/governor
    r2 = client.get("/api/hardware/governor")
    assert r2.status_code == 200
    d2 = r2.json()
    assert "summary" in d2
    assert "settings" in d2

    # 3. POST /api/hardware/governor/settings
    r3 = client.post("/api/hardware/governor/settings", json={"daily_budget_usd": 1.50, "prefer_local_first": True})
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["status"] == "updated"
    assert d3["settings"]["daily_budget_usd"] == 1.50
    assert d3["settings"]["prefer_local_first"] is True

    # 4. GET /api/hardware/cost-ledger
    r4 = client.get("/api/hardware/cost-ledger?limit=10")
    assert r4.status_code == 200
    d4 = r4.json()
    assert "ledger" in d4
