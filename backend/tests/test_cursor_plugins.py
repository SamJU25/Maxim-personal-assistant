"""
Unit and integration tests for Cursor Plugin Ecosystem Adapter.
"""
import pytest
import tempfile
import shutil
import json
from pathlib import Path
from cursor_plugins import CursorPluginEngine

@pytest.fixture
def temp_plugins():
    tmp_dir = Path(tempfile.mkdtemp())
    db_path = tmp_dir / "test_cursor_plugins.db"
    engine = CursorPluginEngine(db_path=db_path, plugins_dir=tmp_dir)
    yield engine, tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_initial_seed_plugins(temp_plugins):
    engine, _ = temp_plugins
    plugins = engine.list_installed_plugins()
    assert len(plugins) >= 1
    default_plug = plugins[0]
    assert default_plug["id"] == "plugin_cursor_devtools"
    assert default_plug["is_enabled"] is True
    assert "rules" in default_plug["manifest"]

def test_validate_manifest(temp_plugins):
    engine, _ = temp_plugins
    
    valid_man = {
        "name": "Security Scanner",
        "version": "1.0.0",
        "rules": ["Check auth boundaries"],
        "skills": ["security-audit"],
        "mcpServers": {"trivy": {"command": "trivy"}}
    }
    res = engine.validate_manifest(valid_man)
    assert res["valid"] is True
    assert res["rules_count"] == 1
    assert res["skills_count"] == 1
    assert res["mcp_count"] == 1

    invalid_man = {"description": "no name or version"}
    res_bad = engine.validate_manifest(invalid_man)
    assert res_bad["valid"] is False
    assert len(res_bad["errors"]) >= 2

def test_import_plugin_dict_and_file(temp_plugins):
    engine, tmp_dir = temp_plugins
    
    # 1. Import dict
    dict_man = {
        "id": "plugin_test_01",
        "name": "Test Plugin",
        "version": "0.1.0",
        "description": "A test plugin for testing",
        "rules": ["rule 1", "rule 2"],
        "skills": ["skill-a"]
    }
    imported = engine.import_plugin(dict_man)
    assert imported["id"] == "plugin_test_01"
    assert imported["status"] == "imported"
    assert imported["rules_count"] == 2

    # 2. Import file
    f_path = tmp_dir / "plugin.json"
    file_man = {
        "id": "plugin_file_02",
        "name": "File Plugin",
        "version": "2.0.0",
        "author": "Antigravity",
        "rules": ["Rule X"],
        "skills": [],
        "mcpServers": {}
    }
    f_path.write_text(json.dumps(file_man), encoding="utf-8")
    imported_f = engine.import_plugin(str(f_path))
    assert imported_f["id"] == "plugin_file_02"
    assert imported_f["name"] == "File Plugin"

    all_plugs = engine.list_installed_plugins()
    assert len(all_plugs) == 3

def test_toggle_plugin(temp_plugins):
    engine, _ = temp_plugins
    assert engine.toggle_plugin("plugin_cursor_devtools", False) is True
    plugs = engine.list_installed_plugins()
    p = [x for x in plugs if x["id"] == "plugin_cursor_devtools"][0]
    assert p["is_enabled"] is False

    assert engine.toggle_plugin("plugin_cursor_devtools", True) is True
    plugs2 = engine.list_installed_plugins()
    p2 = [x for x in plugs2 if x["id"] == "plugin_cursor_devtools"][0]
    assert p2["is_enabled"] is True

def test_engine_tool_dispatch():
    from engine import agent_engine

    # Test cursor_list_plugins
    res_raw = agent_engine.execute_tool(
        name="cursor_list_plugins",
        args={},
        session_id="test_session"
    )
    res = json.loads(res_raw)
    assert res["status"] == "success"
    assert len(res["plugins"]) >= 1

    # Test cursor_import_plugin with JSON string
    manifest = {
        "id": "plugin_runtime_tool_test",
        "name": "Runtime Test Plugin",
        "version": "1.0.0",
        "rules": ["Be concise"]
    }
    res_raw2 = agent_engine.execute_tool(
        name="cursor_import_plugin",
        args={"manifest_path_or_dict": json.dumps(manifest)},
        session_id="test_session"
    )
    res2 = json.loads(res_raw2)
    assert res2["id"] == "plugin_runtime_tool_test"
    assert res2["status"] == "imported"

    # Test cursor_toggle_plugin
    res_raw3 = agent_engine.execute_tool(
        name="cursor_toggle_plugin",
        args={"plugin_id": "plugin_runtime_tool_test", "enabled": False},
        session_id="test_session"
    )
    res3 = json.loads(res_raw3)
    assert res3["status"] == "success"
    assert res3["enabled"] is False
