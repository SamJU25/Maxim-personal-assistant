"""
Unit & Integration Tests for MaxIM V2 Smithery & Glama MCP Registry Hub.
Tests registry search, manifest inspection, persistent SQLite mounting,
ReAct engine tool routing, and FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from tools.mcp_client import mcp_client, CURATED_MCP_REGISTRY
from engine import agent_engine
from server import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# =============================================================================
# 1. REGISTRY SEARCH TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_mcp_search_curated_baseline():
    """Verifies that search returns curated baseline servers matching keywords."""
    res = await mcp_client.search_registries(query="postgres", registry="all")
    assert res["total_found"] >= 1
    names = [r["id"] for r in res["results"]]
    assert "postgres" in names

@pytest.mark.asyncio
async def test_mcp_search_registry_filtering():
    """Verifies filtering by official, smithery, or glama registries."""
    res_smithery = await mcp_client.search_registries(query="", registry="smithery")
    for r in res_smithery["results"]:
        assert r["registry"] == "smithery"

    res_official = await mcp_client.search_registries(query="", registry="official")
    for r in res_official["results"]:
        assert r["registry"] == "official"


# =============================================================================
# 2. SERVER MANIFEST INSPECTION TESTS
# =============================================================================

def test_mcp_inspect_curated_server():
    """Verifies detailed inspection of known curated MCP servers."""
    manifest = mcp_client.inspect_server("github")
    assert manifest["source"] == "registry"
    assert manifest["id"] == "github"
    assert "GITHUB_PERSONAL_ACCESS_TOKEN" in manifest["required_env_vars"]
    assert "search_repositories" in manifest["tools_preview"]
    assert manifest["sample_install_command"].startswith("npx")

def test_mcp_inspect_unknown_community_server():
    """Verifies fallback manifest generation for unindexed servers."""
    manifest = mcp_client.inspect_server("some-custom-tool")
    assert manifest["source"] == "generic_template"
    assert manifest["id"] == "some-custom-tool"
    assert "npx" in manifest["sample_install_command"]


# =============================================================================
# 3. MOUNTING, PERSISTENCE & EXECUTION TESTS
# =============================================================================

def test_mcp_mount_persist_and_remove():
    """Tests mounting an MCP server, verifying SQLite persistence, and unmounting."""
    server_name = "test_analytics_server"
    
    # Mount
    cfg = mcp_client.register_server(
        name=server_name,
        transport="stdio",
        command="npx",
        args=["-y", "@test/analytics"],
        env={"API_KEY": "secret"},
        description="Test Analytics Server",
        source_registry="smithery",
    )
    assert cfg.name == server_name
    assert server_name in mcp_client.servers

    # List
    installed = mcp_client.list_installed_servers()
    names = [s["name"] for s in installed]
    assert server_name in names

    # Remove
    removed = mcp_client.remove_server(server_name)
    assert removed is True
    assert server_name not in mcp_client.servers

@pytest.mark.asyncio
async def test_mcp_call_tool():
    """Tests invoking an MCP tool through the client manager."""
    server_name = "test_calc_server"
    mcp_client.register_server(
        name=server_name,
        transport="stdio",
        command="uvx",
        args=["calc-mcp"],
    )

    res = await mcp_client.call_tool(
        server_name=server_name,
        tool_name="add",
        arguments={"a": 5, "b": 10},
    )
    assert res["status"] == "success"
    assert res["server"] == server_name
    assert res["is_error"] is False

    # Cleanup
    mcp_client.remove_server(server_name)


# =============================================================================
# 4. REACT ENGINE TOOL INTEGRATION TESTS
# =============================================================================

def test_react_engine_mcp_search():
    """Tests execution of mcp_search_registry from ReAct engine."""
    import json
    raw = agent_engine.execute_tool("mcp_search_registry", {"query": "sqlite"}, session_id="test_mcp")
    parsed = json.loads(raw)
    assert parsed.get("total_found", 0) >= 1
    ids = [r["id"] for r in parsed.get("results", [])]
    assert "sqlite" in ids

def test_react_engine_mcp_inspect():
    """Tests execution of mcp_inspect_server from ReAct engine."""
    import json
    raw = agent_engine.execute_tool("mcp_inspect_server", {"server_id": "filesystem"}, session_id="test_mcp")
    parsed = json.loads(raw)
    assert parsed.get("id") == "filesystem"
    assert "read_file" in parsed.get("tools_preview", [])


# =============================================================================
# 5. FASTAPI REST ENDPOINTS TESTS
# =============================================================================

def test_api_mcp_search(client):
    """GET /api/mcp/search returns matching registry entries."""
    resp = client.get("/api/mcp/search?query=browser")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert any("puppeteer" in r["id"] for r in data["results"])

def test_api_mcp_inspect(client):
    """GET /api/mcp/inspect returns server manifest."""
    resp = client.get("/api/mcp/inspect?server_id=brave-search")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "brave-search"
    assert "BRAVE_API_KEY" in data["required_env_vars"]

def test_api_mcp_lifecycle(client):
    """Tests install, list, call, and delete endpoints via REST."""
    # 1. Install
    payload = {
        "name": "api_test_mcp",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "dummy-mcp"],
        "description": "API lifecycle test",
    }
    resp_install = client.post("/api/mcp/install", json=payload)
    assert resp_install.status_code == 200
    assert resp_install.json()["status"] == "mounted"

    # 2. List
    resp_list = client.get("/api/mcp/servers")
    assert resp_list.status_code == 200
    servers = resp_list.json()["servers"]
    assert any(s["name"] == "api_test_mcp" for s in servers)

    # 3. Call
    call_payload = {
        "server_name": "api_test_mcp",
        "tool_name": "ping",
        "arguments": {"hello": "world"},
    }
    resp_call = client.post("/api/mcp/call", json=call_payload)
    assert resp_call.status_code == 200
    assert resp_call.json()["status"] == "success"

    # 4. Delete
    resp_del = client.delete("/api/mcp/servers/api_test_mcp")
    assert resp_del.status_code == 200
    assert resp_del.json()["status"] == "removed"
