"""
Unit & Integration Tests for Phase 8:
- Hermes Multi-Connection Roles & Automatic Failover.
- Sub-Agent Creation & Parallel Delegation Pool.
- Hermes Modular Toolset Catalog.
- Model Context Protocol (MCP) Client Manager.
- Autonomous Watchdog & Cron Heartbeat Scheduler.
- FastAPI Phase 8 API Endpoints.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from server import app
from router import model_router, ProviderType
from tools.catalog import tool_catalog, ToolsetName
from tools.mcp_client import mcp_client
from subagent import subagent_pool, SubAgentConfig, SubAgent
from cron_engine import watchdog_scheduler
from engine import agent_engine

client = TestClient(app)

def test_multi_connection_roles_and_routing():
    # 1. Check default roles
    prov, mod = model_router.get_connection_for_role("subagents")
    assert prov == "ollama"

    # 2. Update connection role
    model_router.set_connection_role("subagents", "deepseek", "deepseek-coder")
    prov2, mod2 = model_router.get_connection_for_role("subagents")
    assert prov2 == "deepseek"
    assert mod2 == "deepseek-coder"

    # 3. Test fallback provider configuration
    model_router.set_fallback_provider("chatgpt")
    assert model_router.fallback_provider == "chatgpt"

def test_hermes_tool_catalog():
    vault_tools = tool_catalog.get_toolset(ToolsetName.VAULT)
    assert len(vault_tools) >= 4
    assert any(t["function"]["name"] == "read_vault_note" for t in vault_tools)

    delegation_tools = tool_catalog.get_toolset(ToolsetName.DELEGATION)
    assert any(t["function"]["name"] == "create_subagent" for t in delegation_tools)

    all_tools = tool_catalog.get_all_tools()
    assert len(all_tools) >= 10

    filtered = tool_catalog.filter_by_toolsets(["vault", "perception"])
    names = [t["function"]["name"] for t in filtered]
    assert "read_vault_note" in names
    assert "inspect_screen" in names
    assert "cua_click" not in names

@pytest.mark.asyncio
async def test_mcp_client_manager():
    mcp_client.register_server(
        name="github_mcp",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"]
    )
    assert "github_mcp" in mcp_client.servers

    tools = await mcp_client.list_server_tools("github_mcp")
    assert len(tools) > 0
    assert "github_mcp_query" in tools[0]["name"]

    res = await mcp_client.call_tool("github_mcp", "github_mcp_query", {"query": "PR list"})
    assert res["is_error"] is False
    assert "Executed" in res["result"]

@pytest.mark.asyncio
async def test_subagent_creation_and_execution():
    cfg = SubAgentConfig(
        task="Investigate vault notes for TELOS milestones",
        role="Vault Archaeologist",
        toolset_whitelist=["read_vault_note", "search_vault"],
        max_iterations=3,
    )
    sub = SubAgent(cfg)
    assert sub.cfg.role == "Vault Archaeologist"

    # Verify tool whitelist filtering
    allowed = sub.get_allowed_tools(tool_catalog.get_all_tools())
    allowed_names = [t["function"]["name"] for t in allowed]
    assert "read_vault_note" in allowed_names
    assert "search_vault" in allowed_names
    assert "cua_click" not in allowed_names

    # Mock chat completion for subagent turn
    with patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_choice = MagicMock()
        mock_choice.message.content = "Vault investigation complete. Identified 3 milestones."
        mock_choice.message.tool_calls = None
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]
        mock_chat.return_value = mock_resp

        result = await sub.run()
        assert result["status"] == "completed"
        assert "Vault investigation complete" in result["result"]
        assert result["subagent_id"].startswith("sub_")

@pytest.mark.asyncio
async def test_subagent_parallel_pool():
    sub1 = subagent_pool.create_subagent(task="Task 1", role="Researcher 1")
    sub2 = subagent_pool.create_subagent(task="Task 2", role="Researcher 2")

    with patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_choice = MagicMock()
        mock_choice.message.content = "Parallel subagent done."
        mock_choice.message.tool_calls = None
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]
        mock_chat.return_value = mock_resp

        results = await subagent_pool.run_parallel([sub1, sub2])
        assert len(results) == 2
        assert all(r["status"] == "completed" for r in results)

def test_engine_create_subagent_tool():
    with patch("subagent.SubAgent.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {
            "subagent_id": "sub_test1",
            "task": "Quick search",
            "status": "completed",
            "result": "Subagent findings.",
            "receipts": [],
        }
        res_str = agent_engine.execute_tool(
            "create_subagent",
            {"task": "Quick search", "role": "Scout", "toolset": "vault"},
            session_id="test_session"
        )
        assert "sub_test1" in res_str
        assert "Subagent findings" in res_str

@pytest.mark.asyncio
async def test_autonomous_watchdog_scheduler():
    # Register test routine
    watchdog_scheduler.register_job("test_routine", interval_seconds=10)
    assert "test_routine" in watchdog_scheduler.jobs

    # Execute tick
    res = await watchdog_scheduler.execute_job("test_routine")
    assert res["status"] == "success"
    assert res["run_count"] == 1

def test_server_phase8_endpoints():
    # 1. Connections API
    res_conn = client.get("/api/connections")
    assert res_conn.status_code == 200
    cdata = res_conn.json()
    assert "roles" in cdata
    assert "active_provider" in cdata

    # Set connection role
    res_set = client.post("/api/connections/role", json={
        "role": "fast",
        "provider": "google",
        "model": "gemini-2.0-flash"
    })
    assert res_set.status_code == 200
    assert res_set.json()["status"] == "updated"

    # 2. Watchdog jobs API
    res_jobs = client.get("/api/watchdog/jobs")
    assert res_jobs.status_code == 200
    assert len(res_jobs.json()["jobs"]) >= 3

    # Trigger watchdog job
    res_trig = client.post("/api/watchdog/trigger", json={
        "job_name": "watchdog_health_ping"
    })
    assert res_trig.status_code == 200
    assert res_trig.json()["status"] == "success"

    # 3. MCP register API
    res_mcp = client.post("/api/mcp/register", json={
        "name": "sqlite_mcp",
        "transport": "stdio",
        "command": "uvx"
    })
    assert res_mcp.status_code == 200
    assert res_mcp.json()["status"] == "registered"

    # 4. Subagent create API
    with patch("subagent.SubAgent.run", new_callable=AsyncMock) as mock_sub_run:
        mock_sub_run.return_value = {
            "subagent_id": "sub_api_test",
            "task": "Test task",
            "role": "Tester",
            "status": "completed",
            "result": "API subagent completed successfully.",
            "receipts": [],
            "iterations": 1
        }
        res_sub = client.post("/api/subagent/create", json={
            "task": "Test task",
            "role": "Tester",
            "toolset": "vault"
        })
        assert res_sub.status_code == 200
        assert res_sub.json()["status"] == "completed"
        assert "API subagent completed" in res_sub.json()["result"]
