"""
Unit & Integration Tests for Phase 11:
- LobeHub Chief Agent Operator & Multi-Agent Collaboration Engine.
- Team Roster Management (hire, fire, list, update).
- Collaboration Groups ("Agent Groups") & Multi-Agent Iterative Turn-Taking.
- 7x24 Autonomous Shifts & Executive Shift Reporting into Obsidian Vault.
- MaxIM ReAct Engine tool integration (list_agent_team, hire_agent_teammate, run_group_collaboration, schedule_agent_shift).
- Sub-Agent delegation with operator toolset.
- FastAPI Phase 11 REST endpoints.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from server import app
from chief_operator import agent_operator, AgentMember, AgentCollaborationGroup
from tools.catalog import ToolsetName, tool_catalog
from engine import agent_engine
from subagent import subagent_pool

client = TestClient(app)

# =============================================================================
# 1. TEAM ROSTER MANAGEMENT
# =============================================================================

def test_team_roster_defaults_and_listing():
    """Verifies default seeded team members exist."""
    team = agent_operator.list_team()
    assert len(team) >= 5
    ids = [m.id for m in team]
    assert "agent_chief" in ids
    assert "agent_hermes" in ids
    assert "agent_reach" in ids
    assert "agent_bitterbot" in ids
    assert "agent_zylos" in ids

def test_hire_and_fire_agent():
    """Verifies hiring a new agent teammate and subsequent firing."""
    new_agent = agent_operator.hire_agent(
        name="Test Refactoring Specialist",
        role="Code Optimizer",
        persona="Applies surgical minimal diffs and Karpathy simplicity.",
        avatar="Code",
        toolsets=["vault", "perception"],
    )
    assert new_agent.id.startswith("agent_")
    assert new_agent.name == "Test Refactoring Specialist"
    assert new_agent.status == "idle"

    # Verify retrieval
    retrieved = agent_operator.get_agent(new_agent.id)
    assert retrieved is not None
    assert retrieved.role == "Code Optimizer"
    assert "vault" in retrieved.toolsets

    # Fire agent
    fired = agent_operator.fire_agent(new_agent.id)
    assert fired is True
    assert agent_operator.get_agent(new_agent.id) is None


# =============================================================================
# 2. COLLABORATION GROUPS & MESSAGES
# =============================================================================

def test_group_defaults_and_creation():
    """Verifies default group exists and custom group creation works."""
    groups = agent_operator.list_groups()
    assert len(groups) >= 1
    council = next((g for g in groups if g.id == "group_core_council"), None)
    assert council is not None
    assert "agent_chief" in council.member_ids

    # Create new group
    custom_group = agent_operator.create_group(
        name="Security & Performance Review",
        description="Cross-auditing code boundaries, threat models, and memory leaks.",
        member_ids=["agent_chief", "agent_bitterbot"],
        topic="Pre-production Audit",
    )
    assert custom_group.id.startswith("group_")
    assert len(custom_group.member_ids) == 2

    # Fetch group
    g = agent_operator.get_group(custom_group.id)
    assert g is not None
    assert g.name == "Security & Performance Review"

def test_group_messages_logging_and_history():
    """Verifies group message logging and retrieval."""
    test_group = agent_operator.create_group(
        name="History Test Group",
        description="Testing message persistence.",
        member_ids=["agent_chief"],
    )
    agent_operator.log_group_message(
        group_id=test_group.id,
        sender_id="test_sender",
        sender_name="Test Operator",
        role="Supervisor",
        content="Testing team collaboration channel message.",
    )
    messages = agent_operator.get_group_messages(test_group.id, limit=10)
    assert len(messages) == 1
    assert messages[0]["sender_id"] == "test_sender"
    assert messages[0]["content"] == "Testing team collaboration channel message."


# =============================================================================
# 3. MULTI-AGENT GROUP CHAT (TURN-TAKING COLLABORATION)
# =============================================================================

@pytest.mark.asyncio
async def test_run_group_chat_collaboration():
    """Verifies multi-agent collaborative turn-taking execution."""
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "I have analyzed the proposition from my domain perspective and approve."
    mock_choice.message = mock_message
    mock_resp.choices = [mock_choice]

    with patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_resp

        result = await agent_operator.run_group_chat(
            group_id="group_core_council",
            user_message="Evaluate Phase 11 multi-agent architecture readiness.",
            rounds=1,
        )

        assert result["status"] == "success"
        assert result["group_id"] == "group_core_council"
        assert len(result["turns"]) == 3  # agent_chief, agent_hermes, agent_bitterbot
        assert result["total_turns"] == 3

        # Verify turns contains agent names and valid content
        first_turn = result["turns"][0]
        assert first_turn["agent_id"] in ["agent_chief", "agent_hermes", "agent_bitterbot"]
        assert "I have analyzed" in first_turn["content"]


# =============================================================================
# 4. AUTONOMOUS SHIFTS & EXECUTIVE REPORTING
# =============================================================================

@pytest.mark.asyncio
async def test_execute_shift_and_reporting():
    """Verifies autonomous shift execution and SQLite/vault persistence."""
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Autonomous shift completed: 4 files reviewed, zero regressions found."
    mock_choice.message = mock_message
    mock_resp.choices = [mock_choice]

    with patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat, \
         patch("tools.vault_tool.vault_synapse.write_note", return_value={"status": "created", "path": "vault/test.md"}):
        mock_chat.return_value = mock_resp

        report = await agent_operator.execute_shift(
            agent_id="agent_reach",
            task="Monitor tech community feeds for emerging agent patterns.",
            save_to_vault=True,
        )

        assert report.id.startswith("shift_")
        assert report.agent_id == "agent_reach"
        assert report.status == "completed"
        assert "Autonomous shift completed" in report.summary

        # Check list_reports contains this report
        reports = agent_operator.list_reports(limit=5)
        assert len(reports) >= 1
        assert any(r.id == report.id for r in reports)


# =============================================================================
# 5. MAXIM REACT ENGINE TOOL INTEGRATION & SUBAGENTS
# =============================================================================

def test_operator_tools_registered_in_catalog():
    """Verifies that operator tools are registered in catalog."""
    assert ToolsetName.OPERATOR == "operator"
    tools = tool_catalog.get_toolset(ToolsetName.OPERATOR)
    tool_names = [t["function"]["name"] for t in tools]
    assert "list_agent_team" in tool_names
    assert "hire_agent_teammate" in tool_names
    assert "run_group_collaboration" in tool_names
    assert "schedule_agent_shift" in tool_names
    assert len(tool_catalog.get_all_tools()) >= 22

def test_engine_executes_operator_tools():
    """Verifies ReAct engine execution of operator tools."""
    # 1. list_agent_team
    res_str = agent_engine.execute_tool("list_agent_team", {}, "default_session")
    res = json.loads(res_str)
    assert res["status"] == "success"
    assert res["total"] >= 5

    # 2. hire_agent_teammate
    hire_res_str = agent_engine.execute_tool("hire_agent_teammate", {
        "name": "Engine Test Bot",
        "role": "QA Bot",
        "persona": "Automates all verifications.",
    }, "default_session")
    hire_res = json.loads(hire_res_str)
    assert hire_res["status"] == "hired"
    assert hire_res["agent"]["name"] == "Engine Test Bot"

    # Clean up hired test bot
    agent_operator.fire_agent(hire_res["agent"]["id"])

def test_subagent_with_operator_toolset():
    """Verifies SubAgent worker pool accepts operator toolset."""
    sub = subagent_pool.create_subagent(
        task="Coordinate with Chief Operator on active roster.",
        role="Staff Coordinator",
        toolset_whitelist=["list_agent_team", "hire_agent_teammate"],
        max_iterations=2,
    )
    assert sub.cfg.role == "Staff Coordinator"
    assert len(sub.cfg.toolset_whitelist) == 2
    assert "list_agent_team" in sub.cfg.toolset_whitelist


# =============================================================================
# 6. FASTAPI REST ENDPOINTS
# =============================================================================

def test_api_operator_team_endpoints():
    """Verifies GET /api/operator/team, POST /api/operator/hire, and DELETE /api/operator/team/{id}."""
    # List team
    resp = client.get("/api/operator/team")
    assert resp.status_code == 200
    data = resp.json()
    assert "team" in data
    assert data["total"] >= 5

    # Hire agent
    hire_payload = {
        "name": "API Hired Specialist",
        "role": "API Tester",
        "persona": "Validates HTTP routes.",
        "avatar": "Globe",
        "toolsets": ["reach", "vault"],
    }
    hire_resp = client.post("/api/operator/hire", json=hire_payload)
    assert hire_resp.status_code == 200
    hired_agent = hire_resp.json()
    assert hired_agent["name"] == "API Hired Specialist"
    agent_id = hired_agent["id"]

    # Fire agent
    del_resp = client.delete(f"/api/operator/team/{agent_id}")
    assert del_resp.status_code == 200
    del_data = del_resp.json()
    assert del_data["status"] == "success"

def test_api_operator_groups_and_messages_endpoints():
    """Verifies GET/POST /api/operator/groups and GET messages."""
    # List groups
    resp = client.get("/api/operator/groups")
    assert resp.status_code == 200
    groups = resp.json()["groups"]
    assert len(groups) >= 1

    # Create group
    create_payload = {
        "name": "API Collaboration Circle",
        "description": "Cross-domain discussion via REST.",
        "member_ids": ["agent_chief", "agent_hermes"],
        "topic": "Knowledge Syntheses",
    }
    post_resp = client.post("/api/operator/groups", json=create_payload)
    assert post_resp.status_code == 200
    created = post_resp.json()
    assert created["name"] == "API Collaboration Circle"
    group_id = created["id"]

    # Get messages
    msg_resp = client.get(f"/api/operator/groups/{group_id}/messages")
    assert msg_resp.status_code == 200
    assert "messages" in msg_resp.json()

def test_api_operator_shifts_and_reports_endpoints():
    """Verifies POST /api/operator/shifts/execute and GET /api/operator/reports."""
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "API shift executed cleanly."
    mock_choice.message = mock_message
    mock_resp.choices = [mock_choice]

    with patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat, \
         patch("tools.vault_tool.vault_synapse.write_note", return_value={"status": "created"}):
        mock_chat.return_value = mock_resp

        shift_payload = {
            "agent_id": "agent_chief",
            "task": "Review operator system status.",
            "save_to_vault": False,
        }
        shift_resp = client.post("/api/operator/shifts/execute", json=shift_payload)
        assert shift_resp.status_code == 200
        shift_data = shift_resp.json()
        assert shift_data["agent_id"] == "agent_chief"
        assert shift_data["status"] == "completed"

    # Get reports
    rep_resp = client.get("/api/operator/reports")
    assert rep_resp.status_code == 200
    assert "reports" in rep_resp.json()
    assert len(rep_resp.json()["reports"]) >= 1
