"""
Unit and integration tests for Phase 14: Mark-LIV Functional OS Automation & Vision-Action Loop.
Verifies window perception, process controls, action simulation, and execution receipts.
"""
import pytest
from pathlib import Path
from mark_liv import MarkLivEngine, WindowInfo, OSActionRecord

@pytest.fixture
def temp_mark_liv(tmp_path: Path):
    db_file = tmp_path / "test_mark_liv.db"
    return MarkLivEngine(db_path=db_file)

def test_mark_liv_db_init(temp_mark_liv):
    """Verify SQLite WAL tables are initialized properly."""
    assert temp_mark_liv.db_path.exists()
    actions = temp_mark_liv.get_recent_actions()
    assert len(actions) == 0

def test_list_windows(temp_mark_liv):
    """Verify window enumeration returns real desktop windows with geometry."""
    windows = temp_mark_liv.list_windows(visible_only=True)
    assert isinstance(windows, list)
    if windows:
        w = windows[0]
        assert isinstance(w, WindowInfo)
        assert w.hwnd > 0
        assert w.rect.width >= 0
        assert w.rect.height >= 0

def test_find_window_and_active(temp_mark_liv):
    """Verify looking up active window or searching by query."""
    active = temp_mark_liv.get_active_window()
    # In interactive Windows sessions, there is almost always an active window
    if active:
        assert isinstance(active, WindowInfo)
        assert active.is_active is True

    # Search for common processes if present (e.g. explorer, code, python)
    win = temp_mark_liv.find_window("explorer")
    if win:
        assert "explorer" in win.process_name.lower() or "explorer" in win.title.lower()

def test_log_action_and_receipts(temp_mark_liv):
    """Verify logging actions and retrieving receipts from SQLite WAL."""
    rec = temp_mark_liv.log_action(
        action_type="send_keys",
        target="ActiveWindow",
        parameters={"keys": ["ctrl", "c"]},
        success=True,
        duration_ms=45.2,
    )
    assert rec.id is not None
    assert rec.action_type == "send_keys"
    assert rec.success is True

    recent = temp_mark_liv.get_recent_actions(limit=10)
    assert len(recent) == 1
    assert recent[0].action_type == "send_keys"
    assert recent[0].parameters.get("keys") == ["ctrl", "c"]

def test_execute_action_step_validation(temp_mark_liv):
    """Verify execute_action_step validates parameters defensive and returns structured status."""
    # Invalid action
    res_inv = temp_mark_liv.execute_action_step(action="unsupported_dummy")
    assert res_inv["status"] == "error"

    # Click without coordinates or target
    res_click_fail = temp_mark_liv.execute_action_step(action="click")
    assert res_click_fail["status"] == "error"

    # Type without text
    res_type_fail = temp_mark_liv.execute_action_step(action="type")
    assert res_type_fail["status"] == "error"

    # Send keys without keys
    res_keys_fail = temp_mark_liv.execute_action_step(action="send_keys")
    assert res_keys_fail["status"] == "error"

def test_process_listing(temp_mark_liv):
    """Verify listing system processes with memory footprint."""
    procs = temp_mark_liv.list_processes(limit=15)
    assert isinstance(procs, list)
    assert len(procs) > 0
    p = procs[0]
    assert "pid" in p
    assert "name" in p
    assert "memory_mb" in p
    assert p["memory_mb"] >= 0.0

def test_screen_snapshot_geometry(temp_mark_liv):
    """Verify screen snapshot capture returns dimensions and status."""
    snap = temp_mark_liv.capture_screen_snapshot()
    assert snap["status"] == "success"
    assert snap["width"] > 0
    assert snap["height"] > 0

def test_os_tools_catalog():
    """Verify OS tools are registered in catalog."""
    from tools.catalog import tool_catalog, ToolsetName
    tools = tool_catalog.get_toolset(ToolsetName.OS)
    assert len(tools) >= 5
    tool_names = [t["function"]["name"] for t in tools]
    assert "os_list_windows" in tool_names
    assert "os_focus_window" in tool_names
    assert "os_launch_app" in tool_names
    assert "os_execute_action" in tool_names
    assert "os_list_processes" in tool_names

def test_engine_os_tools():
    """Verify engine.execute_tool runs OS tools cleanly."""
    import json
    from engine import MaxIMAgentEngine
    eng = MaxIMAgentEngine()

    # 1. os_list_windows
    r1 = eng.execute_tool("os_list_windows", {"visible_only": True}, session_id="test_os")
    d1 = json.loads(r1)
    assert d1["status"] == "success"
    assert "windows" in d1

    # 2. os_list_processes
    r2 = eng.execute_tool("os_list_processes", {"limit": 10}, session_id="test_os")
    d2 = json.loads(r2)
    assert d2["status"] == "success"
    assert len(d2["processes"]) > 0

    # 3. os_execute_action validation
    r3 = eng.execute_tool("os_execute_action", {"action": "invalid_op"}, session_id="test_os")
    d3 = json.loads(r3)
    assert d3["status"] == "error"

def test_server_os_endpoints():
    """Verify FastAPI server exposes the Mark-LIV OS endpoints."""
    from fastapi.testclient import TestClient
    from server import app
    client = TestClient(app)

    # 1. GET /api/os/windows
    r1 = client.get("/api/os/windows")
    assert r1.status_code == 200
    d1 = r1.json()
    assert "windows" in d1
    assert "count" in d1

    # 2. GET /api/os/processes
    r2 = client.get("/api/os/processes?limit=10")
    assert r2.status_code == 200
    d2 = r2.json()
    assert "processes" in d2

    # 3. POST /api/os/action
    r3 = client.post("/api/os/action", json={"action": "focus", "target": "NonExistentDummyWindowXYZ"})
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["action"] == "focus"

    # 4. GET /api/os/history
    r4 = client.get("/api/os/history?limit=10")
    assert r4.status_code == 200
    d4 = r4.json()
    assert "actions" in d4

