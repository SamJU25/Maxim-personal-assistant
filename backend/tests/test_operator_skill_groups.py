"""
Unit & Integration Tests for MaxIM Operator Dynamic Skill Groups & Conductor Orchestration:
- Skill-to-Agent Binding and persistence.
- Zero Preselected Groups: Only group_core_council exists by default.
- Dynamic Group Assembly:
  - Manual on-demand assembly with topic and requested catalog skills.
  - Desktop-driven assembly based on active window and desktop context.
- Group Deletion: Cleaning up ad-hoc groups and their message logs.
- MaxIM administrative dispatching (dispatch_group_task).
- Autonomous objective routing & dynamic orchestration (orchestrate_objective).
- Cross-group deliverable handoff (cross_group_handoff).
- MaxIM ReAct Engine tool integration (operator_assemble_dynamic_group, operator_delete_group, etc.).
- FastAPI REST API endpoints (POST /api/operator/groups/assemble, DELETE /api/operator/groups/{group_id}).
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from server import app
from chief_operator import agent_operator, AgentMember, AgentCollaborationGroup, get_skills_prompt_context
from engine import agent_engine

client = TestClient(app)

# =============================================================================
# 1. SKILL-TO-AGENT BINDING & PERSISTENCE
# =============================================================================

def test_agent_skills_binding_and_persistence():
    """Verifies agents can be hired with skills and retrieved with skills intact."""
    agent = agent_operator.hire_agent(
        name="Test Copywriter Specialist",
        role="Conversion Copywriter",
        persona="Writes high-converting, humanized copy.",
        avatar="Feather",
        toolsets=["vault"],
        skills=["copywriting", "humanizer"],
        category="marketing",
    )
    assert agent.id.startswith("agent_")
    assert agent.skills == ["copywriting", "humanizer"]
    assert agent.category == "marketing"

    retrieved = agent_operator.get_agent(agent.id)
    assert retrieved is not None
    assert retrieved.skills == ["copywriting", "humanizer"]
    assert retrieved.category == "marketing"

    # Cleanup
    agent_operator.fire_agent(agent.id)

def test_get_skills_prompt_context():
    """Verifies skill descriptions are loaded from the dynamic catalog."""
    ctx = get_skills_prompt_context(["copywriting", "claude-seo"])
    assert "Your Assigned Specialized Skills & Playbooks:" in ctx
    assert "copywriting" in ctx
    assert "claude-seo" in ctx

# =============================================================================
# 2. ZERO PRE-SELECTED GROUPS & DYNAMIC GROUP ASSEMBLY
# =============================================================================

def test_no_preselected_dummy_groups_by_default():
    """
    Verifies that no pre-selected domain channels exist by default.
    Only the permanent Core Executive Council exists initially.
    """
    groups = agent_operator.list_groups()
    group_ids = [g.id for g in groups]
    assert "group_core_council" in group_ids
    # Ensure dummy pre-selected groups do NOT exist
    assert "group_marketing" not in group_ids
    assert "group_web_dev" not in group_ids
    assert "group_qa_testing" not in group_ids
    assert "group_backend_api" not in group_ids
    assert "group_security" not in group_ids
    assert "group_agent_architecture" not in group_ids

@pytest.mark.asyncio
async def test_assemble_dynamic_group_manual():
    """Verifies manual dynamic group assembly for a media/scriptwriting topic."""
    res = await agent_operator.assemble_dynamic_group(
        topic="YouTube video production and scriptwriting",
        desktop_context=None,
        use_active_window=False,
    )
    assert res["status"] == "success"
    group = res["group"]
    assert "Media & Video Production" in group["name"]
    assert group["category"] == "marketing"
    assert "agent_chief" in group["member_ids"]
    assert len(group["member_ids"]) >= 2

    # Check orientation message was logged
    msgs = agent_operator.get_group_messages(group["id"], limit=5)
    assert len(msgs) >= 1
    assert "DYNAMIC GROUP ASSEMBLED" in msgs[0]["content"]

    # Cleanup
    agent_operator.delete_group(group["id"])

@pytest.mark.asyncio
async def test_assemble_dynamic_group_with_requested_skills():
    """Verifies dynamic group assembly when user explicitly specifies required skills."""
    res = await agent_operator.assemble_dynamic_group(
        topic="Custom Campaign Task",
        skills_requested=["copywriting", "claude-seo"],
        desktop_context=None,
        use_active_window=False,
    )
    assert res["status"] == "success"
    group = res["group"]
    members = res["members"]
    assert len(members) >= 2

    # Verify specialists were assigned the requested catalog skills
    all_assigned_skills = []
    for m in members:
        all_assigned_skills.extend(m.get("skills", []))
    assert "copywriting" in all_assigned_skills
    assert "claude-seo" in all_assigned_skills

    # Cleanup
    agent_operator.delete_group(group["id"])

@pytest.mark.asyncio
async def test_assemble_dynamic_group_desktop_driven():
    """Verifies dynamic group assembly triggered by desktop application context."""
    res = await agent_operator.assemble_dynamic_group(
        topic="",
        desktop_context="Visual Studio Code - FastAPI backend and database schemas",
        use_active_window=False,
    )
    assert res["status"] == "success"
    group = res["group"]
    assert group["category"] == "backend"
    assert "Backend & APIs" in group["name"]

    # Verify backend specialists in group
    members = [agent_operator.get_agent(m_id) for m_id in group["member_ids"]]
    names = [m.name for m in members if m]
    categories = [m.category for m in members if m]
    assert any("Backend" in n or "Database" in n for n in names)
    assert "backend" in categories

    # Cleanup
    agent_operator.delete_group(group["id"])

def test_delete_group_and_messages():
    """Verifies delete_group deletes the group and cascades to its messages."""
    g = agent_operator.create_group(
        name="Temporary Scratch Group",
        description="For deletion testing.",
        member_ids=["agent_chief"],
        category="productivity",
        topic="Temporary",
    )
    agent_operator.log_group_message(
        group_id=g.id,
        sender_id="agent_chief",
        sender_name="MaxIM Chief",
        role="Conductor",
        content="Test message before deletion",
    )
    assert agent_operator.get_group(g.id) is not None
    assert len(agent_operator.get_group_messages(g.id)) == 1

    deleted = agent_operator.delete_group(g.id)
    assert deleted is True
    assert agent_operator.get_group(g.id) is None
    assert len(agent_operator.get_group_messages(g.id)) == 0

# =============================================================================
# 3. MAXIM MASTER CONDUCTOR: DISPATCH & ORCHESTRATION
# =============================================================================

@pytest.mark.asyncio
async def test_dispatch_group_task_on_dynamic_group():
    """Verifies MaxIM posts executive brief, runs turns, and records sign-off on a dynamic group."""
    dyn_res = await agent_operator.assemble_dynamic_group(
        topic="Developer launch hooks",
        group_name="Launch Copy Squad",
        skills_requested=["copywriting"],
    )
    group_id = dyn_res["group"]["id"]

    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Here are 3 tested hooks for our developer launch."))
    ]

    with patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        res = await agent_operator.dispatch_group_task(
            group_id=group_id,
            task_prompt="Draft launch hooks for developers.",
            rounds=1,
        )

        assert res["status"] == "completed"
        assert res["group_id"] == group_id
        assert len(res["turns"]) >= 1
        assert "signoff" in res

        # Check messages recorded in group history
        msgs = agent_operator.get_group_messages(group_id, limit=10)
        contents = [m["content"] for m in msgs]
        assert any("EXECUTIVE DIRECTIVE from MaxIM Chief Operator" in c for c in contents)
        assert any("EXECUTIVE REVIEW & SIGN-OFF" in c for c in contents)

    # Cleanup
    agent_operator.delete_group(group_id)

@pytest.mark.asyncio
async def test_orchestrate_objective_dynamic_assembly():
    """Verifies autonomous routing creates a dynamic channel on demand and writes vault report."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Security threat model generated with zero vulnerabilities."))
    ]

    with patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        with patch("tools.vault_tool.vault_synapse.write_note") as mock_vault:
            res = await agent_operator.orchestrate_objective(
                objective="Audit authentication endpoints for privilege escalation and token leaks.",
                preferred_category="security",
                rounds=1,
                save_to_vault=True,
            )

            assert res["status"] == "completed"
            assert res["group_id"].startswith("group_")
            assert mock_vault.called
            args, kwargs = mock_vault.call_args
            assert "03 - Agents" in kwargs.get("folder", "")

    # Cleanup the created group
    agent_operator.delete_group(res["group_id"])

@pytest.mark.asyncio
async def test_cross_group_handoff_between_dynamic_groups():
    """Verifies bridging deliverables between two dynamically assembled groups."""
    g1_res = await agent_operator.assemble_dynamic_group(topic="Marketing copy and headlines")
    g2_res = await agent_operator.assemble_dynamic_group(topic="Frontend React hero section")
    g1_id = g1_res["group"]["id"]
    g2_id = g2_res["group"]["id"]

    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="React hero section built using received marketing copy."))
    ]

    with patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        res = await agent_operator.cross_group_handoff(
            source_group_id=g1_id,
            target_group_id=g2_id,
            deliverable_summary="Launch copy and hero headline ready.",
            next_step_instruction="Build responsive React hero section implementing these headlines.",
            rounds=1,
        )

        assert res["status"] == "handoff_completed"
        assert res["target_execution"]["status"] == "completed"

    # Cleanup
    agent_operator.delete_group(g1_id)
    agent_operator.delete_group(g2_id)

# =============================================================================
# 4. REACT ENGINE TOOL INTEGRATION
# =============================================================================

def test_engine_operator_dynamic_assembly_and_tools():
    """Verifies MaxIM ReAct engine can call assemble, dispatch, and delete tools."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Simulated specialist output."))
    ]

    with patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response

        # 1. operator_assemble_dynamic_group
        assemble_raw = agent_engine.execute_tool("operator_assemble_dynamic_group", {
            "topic": "Python FastAPI performance profiling",
            "skills_requested": ["better-auth"],
        }, session_id="test_session")
        assemble_res = json.loads(assemble_raw)
        assert assemble_res["status"] == "success"
        g_id = assemble_res["group"]["id"]

        # 2. operator_dispatch_group_task
        dispatch_raw = agent_engine.execute_tool("operator_dispatch_group_task", {
            "group_id": g_id,
            "task_prompt": "Profile connection pool latency.",
            "rounds": 1,
        }, session_id="test_session")
        dispatch_res = json.loads(dispatch_raw)
        assert dispatch_res["status"] == "completed"

        # 3. operator_delete_group
        delete_raw = agent_engine.execute_tool("operator_delete_group", {
            "group_id": g_id,
        }, session_id="test_session")
        delete_res = json.loads(delete_raw)
        assert delete_res["status"] == "deleted"

# =============================================================================
# 5. FASTAPI REST ENDPOINTS
# =============================================================================

def test_rest_api_dynamic_operator_endpoints():
    """Verifies HTTP endpoints for dynamic group assembly, dispatch, and deletion."""
    # 1. POST assemble dynamic group
    resp_assemble = client.post("/api/operator/groups/assemble", json={
        "topic": "YouTube scriptwriting and audience retention",
        "skills_requested": ["copywriting"],
    })
    assert resp_assemble.status_code == 200
    group_data = resp_assemble.json()
    assert group_data["status"] == "success"
    gid = group_data["group"]["id"]

    # 2. GET single group
    resp_get = client.get(f"/api/operator/groups/{gid}")
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert data["id"] == gid
    assert "members" in data
    assert len(data["members"]) >= 2

    # 3. POST dispatch to dynamic group
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="API dispatch verified."))
    ]
    with patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        resp_dispatch = client.post(f"/api/operator/groups/{gid}/dispatch", json={
            "task_prompt": "Test dispatch from REST API",
            "rounds": 1,
        })
        assert resp_dispatch.status_code == 200
        assert resp_dispatch.json()["status"] == "completed"

    # 4. DELETE group
    resp_delete = client.delete(f"/api/operator/groups/{gid}")
    assert resp_delete.status_code == 200
    assert resp_delete.json()["status"] == "success"
