"""
Unit & Integration Tests for Phase 12:
- Proactive Situational Initiative & Real-Time Hands-Free Voice Agent.
- Situational Snapshot (Foreground Window, LifeOS TELOS, Shift Findings, Cadence).
- Dynamic Evaluation (Non-Robotic, Situation-Grounded Questions vs. [NO_INTERVENTION]).
- Sensitivity Modes (Gentle, Balanced, Proactive, Muted) & Cooldown Enforcement.
- ReAct Engine tool integration (evaluate_proactive_initiative).
- FastAPI Phase 12 REST Endpoints.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from server import app
from proactive_agent import proactive_agent, ProactiveIntervention
from tools.catalog import tool_catalog, ToolsetName
from engine import agent_engine

client = TestClient(app)

# =============================================================================
# 1. PROACTIVE SETTINGS & SNAPSHOT
# =============================================================================

def test_proactive_settings_lifecycle():
    """Verifies retrieval and update of proactive settings in SQLite."""
    settings = proactive_agent.get_settings()
    assert settings.mode in ["gentle", "balanced", "proactive", "muted"]
    assert settings.cooldown_minutes >= 1

    # Update settings
    updated = proactive_agent.update_settings(mode="proactive", auto_speak=True, cooldown_minutes=5)
    assert updated.mode == "proactive"
    assert updated.cooldown_minutes == 5
    assert updated.auto_speak is True

    # Restore balanced
    restored = proactive_agent.update_settings(mode="balanced", auto_speak=True, cooldown_minutes=8)
    assert restored.mode == "balanced"

def test_situation_snapshot_gathering():
    """Verifies situational context gathers active window, TELOS targets, and recent turns."""
    snapshot = proactive_agent.get_situation_snapshot("default_session")
    assert "active_window" in snapshot
    assert "primary_target" in snapshot
    assert "all_targets" in snapshot
    assert "latest_shift_report" in snapshot
    assert "last_user_turn" in snapshot
    assert "timestamp" in snapshot


# =============================================================================
# 2. DYNAMIC COGNITIVE EVALUATION (PROACTIVE INITIATIVE)
# =============================================================================

@pytest.mark.asyncio
async def test_evaluate_initiative_no_intervention():
    """Verifies that when LLM assesses user is focused, no intervention is triggered."""
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "[NO_INTERVENTION]"
    mock_choice.message = mock_message
    mock_resp.choices = [mock_choice]

    with patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_resp

        res = await proactive_agent.evaluate_initiative(session_id="default_session", force=True)
        assert res["should_intervene"] is False
        assert "no intervention needed" in res["reason"]

@pytest.mark.asyncio
async def test_evaluate_initiative_triggers_situational_question():
    """Verifies that strategic situational opportunity triggers a dynamic question."""
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "I noticed you're finalizing the proactive initiative engine. Want me to run the test suite and verify the voice listener integration next?"
    mock_choice.message = mock_message
    mock_resp.choices = [mock_choice]

    with patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_resp

        res = await proactive_agent.evaluate_initiative(session_id="default_session", force=True)
        assert res["should_intervene"] is True
        assert "proactive initiative engine" in res["intervention"]["message"]
        assert res["intervention"]["active_window"] is not None

        # Verify recorded in SQLite history
        history = proactive_agent.list_interventions(limit=5)
        assert len(history) >= 1
        assert any(i.id == res["intervention"]["id"] for i in history)

@pytest.mark.asyncio
async def test_evaluate_initiative_cooldown_and_muted():
    """Verifies cooldown prevents rapid re-prompting and mute suppresses non-forced runs."""
    # 1. Cooldown suppression
    res = await proactive_agent.evaluate_initiative(session_id="default_session", force=False)
    assert res["should_intervene"] is False
    assert "Cooldown active" in res["reason"]

    # 2. Muted suppression
    proactive_agent.update_settings(mode="muted")
    res_muted = await proactive_agent.evaluate_initiative(session_id="default_session", force=False)
    assert res_muted["should_intervene"] is False
    assert "muted" in res_muted["reason"]

    # Restore balanced
    proactive_agent.update_settings(mode="balanced")


# =============================================================================
# 3. REACT ENGINE TOOL INTEGRATION
# =============================================================================

def test_evaluate_proactive_initiative_tool_in_catalog():
    """Verifies evaluate_proactive_initiative is registered in operator tools."""
    tools = tool_catalog.get_toolset(ToolsetName.OPERATOR)
    names = [t["function"]["name"] for t in tools]
    assert "evaluate_proactive_initiative" in names

def test_engine_executes_proactive_tool():
    """Verifies engine executes evaluate_proactive_initiative synchronously."""
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "[NO_INTERVENTION]"
    mock_choice.message = mock_message
    mock_resp.choices = [mock_choice]

    with patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_resp

        res_str = agent_engine.execute_tool("evaluate_proactive_initiative", {"force": True}, "default_session")
        res = json.loads(res_str)
        assert "should_intervene" in res


# =============================================================================
# 4. FASTAPI REST ENDPOINTS
# =============================================================================

def test_api_proactive_snapshot_endpoint():
    """Verifies GET /api/proactive/snapshot."""
    resp = client.get("/api/proactive/snapshot?session_id=default_session")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_window" in data
    assert "primary_target" in data

def test_api_proactive_settings_endpoints():
    """Verifies GET and POST /api/proactive/settings."""
    # GET
    get_resp = client.get("/api/proactive/settings")
    assert get_resp.status_code == 200
    assert "mode" in get_resp.json()

    # POST
    post_payload = {"mode": "proactive", "auto_speak": True, "cooldown_minutes": 6}
    post_resp = client.post("/api/proactive/settings", json=post_payload)
    assert post_resp.status_code == 200
    updated = post_resp.json()
    assert updated["mode"] == "proactive"
    assert updated["cooldown_minutes"] == 6

    # Restore balanced
    client.post("/api/proactive/settings", json={"mode": "balanced", "auto_speak": True, "cooldown_minutes": 8})

def test_api_proactive_evaluate_and_history_endpoints():
    """Verifies POST /api/proactive/evaluate and GET /api/proactive/history."""
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "API Proactive Question: Should we review the latest security rules?"
    mock_choice.message = mock_message
    mock_resp.choices = [mock_choice]

    with patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_resp

        eval_resp = client.post("/api/proactive/evaluate", json={"session_id": "default_session", "force": True})
        assert eval_resp.status_code == 200
        eval_data = eval_resp.json()
        assert eval_data["should_intervene"] is True
        assert "API Proactive Question" in eval_data["intervention"]["message"]

    # History
    hist_resp = client.get("/api/proactive/history?limit=10")
    assert hist_resp.status_code == 200
    assert "interventions" in hist_resp.json()
    assert len(hist_resp.json()["interventions"]) >= 1
