"""
Unit and Integration Tests for MaxIM Extension Capsule Architecture.
Validates:
1. Discovery and parsing of extension capsules (manifest.json).
2. Dynamic import of capsule tools and registration of execution handlers.
3. Intent-based tool scoping for local models.
4. Execution of extension tools via ExtensionManager and MaxIMAgentEngine.
5. REST endpoints GET /api/extensions and GET /api/tools.
"""
import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient

from extensions.extension_manager import extension_manager, ExtensionManager, ExtensionManifest
from engine import agent_engine
from server import app

client = TestClient(app)

def test_extension_manager_discovery():
    """Verifies ExtensionManager discovers capsules in backend/extensions/."""
    exts = extension_manager.discover_extensions()
    assert "openjarvis_bridge" in exts
    
    jarvis_ext = exts["openjarvis_bridge"]
    assert jarvis_ext.name == "OpenJarvis Execution Bridge"
    assert jarvis_ext.enabled is True
    assert "jarvis" in jarvis_ext.intent_triggers
    assert len(jarvis_ext.tools) >= 2

def test_extension_has_tool_and_metadata():
    """Verifies that extension tools are registered in the global lookup map."""
    assert extension_manager.has_tool("openjarvis_system_diagnostic") is True
    assert extension_manager.has_tool("openjarvis_grounding_probe") is True
    assert extension_manager.has_tool("nonexistent_tool_xyz") is False

def test_extension_tool_direct_execution():
    """Verifies direct execution of an extension tool via ExtensionManager."""
    res = extension_manager.execute_extension_tool(
        "openjarvis_system_diagnostic",
        {"subsystem": "vision", "detailed": True},
        session_id="test_session"
    )
    assert res["status"] == "online"
    assert res["subsystem"] == "vision"
    assert res["metrics"] is not None
    assert res["metrics"]["grounding_confidence"] == 0.98

    res_probe = extension_manager.execute_extension_tool(
        "openjarvis_grounding_probe",
        {"target_element": "settings button"},
        session_id="test_session"
    )
    assert res_probe["status"] == "grounded"
    assert res_probe["target"] == "settings button"
    assert res_probe["coordinates"]["x"] == 512

def test_intent_based_scoping():
    """Verifies extension tools are mounted when query matches intent triggers."""
    # When query mentions 'jarvis' or 'openjarvis', tools must be scoped
    tools_jarvis = extension_manager.get_scoped_tools(query="activate jarvis protocol please")
    tool_names_jarvis = [t.get("function", {}).get("name") for t in tools_jarvis]
    assert "openjarvis_system_diagnostic" in tool_names_jarvis

    # When query is unrelated, tools with explicit intent triggers should NOT be mounted
    tools_unrelated = extension_manager.get_scoped_tools(query="calculate tax deductions for real estate")
    tool_names_unrelated = [t.get("function", {}).get("name") for t in tools_unrelated]
    assert "openjarvis_system_diagnostic" not in tool_names_unrelated

    # When query is None, universal / all tools are returned
    tools_all = extension_manager.get_scoped_tools(query=None)
    assert len(tools_all) >= 2

def test_engine_tool_dispatch_to_extension():
    """Verifies agent_engine.execute_tool() cleanly dispatches to extension capsules."""
    raw_res = agent_engine.execute_tool(
        "openjarvis_system_diagnostic",
        {"subsystem": "all", "detailed": False},
        session_id="test_ext_sess"
    )
    # TokenJuice may return compressed string or json
    assert "OpenJarvis protocol online" in raw_res or "online" in raw_res

def test_api_extensions_endpoint():
    """Verifies GET /api/extensions returns discovered capsules."""
    resp = client.get("/api/extensions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["count"] >= 1
    
    jarvis_entry = next((e for e in data["extensions"] if e["id"] == "openjarvis_bridge"), None)
    assert jarvis_entry is not None
    assert jarvis_entry["name"] == "OpenJarvis Execution Bridge"
    assert "openjarvis_system_diagnostic" in jarvis_entry["tools"]

def test_api_tools_endpoint_includes_extensions():
    """Verifies GET /api/tools includes registered extension tools."""
    resp = client.get("/api/tools")
    assert resp.status_code == 200
    data = resp.json()
    tools = data["tools"]
    
    ext_tool = next((t for t in tools if t["name"] == "openjarvis_system_diagnostic"), None)
    assert ext_tool is not None
    assert "Extension" in ext_tool["category"]
    assert ext_tool["toolset"] == "ext_openjarvis_bridge"
