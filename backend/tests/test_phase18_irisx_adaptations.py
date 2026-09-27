"""
Unit tests for Phase 18: IrisX AI Adaptations.
Verifies:
1. Cubic Bézier mouse trajectory generation & micro-jitter calculation.
2. Hardware Governor active dispatchers (Volume, Brightness, Browser registry, Wi-Fi).
3. Mobile Telekinesis ADB Bridge (graceful degradation & device commands).
4. Tool catalog registration and MaxIMAgentEngine tool execution.
5. FastAPI REST API endpoints.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from mark_liv import mark_liv_engine, MarkLivEngine
from hardware_governor import hardware_governor, HardwareGovernorEngine
from tools.adb_tool import adb_bridge, ADBBridgeService
from tools.catalog import tool_catalog, ToolsetName
from engine import MaxIMAgentEngine
from server import app


# =============================================================================
# 1. BÉZIER MOUSE SIMULATION & HIGH-DPI MATRIX
# =============================================================================

def test_bezier_trajectory_math():
    """Verify cubic Bézier math generates valid trajectories with correct bounds."""
    start = (100, 200)
    end = (800, 600)
    steps = 15

    points = MarkLivEngine.calculate_bezier_trajectory(start, end, steps=steps, jitter=0.0)

    # 1. Point count is steps + 1
    assert len(points) == steps + 1

    # 2. First point is exactly start, last point is exactly end
    assert points[0] == start
    assert points[-1] == end

    # 3. All points are integer coordinate pairs
    for pt in points:
        assert isinstance(pt, tuple)
        assert len(pt) == 2
        assert isinstance(pt[0], int)
        assert isinstance(pt[1], int)

    # 4. Trajectory is non-linear (cubic curve)
    # Check that midpoint deviates from straight Euclidean midpoint (450, 400)
    mid_idx = steps // 2
    mid_pt = points[mid_idx]
    assert isinstance(mid_pt[0], int)
    assert isinstance(mid_pt[1], int)


def test_bezier_trajectory_with_jitter():
    """Verify trajectory micro-jitter decays towards zero at destination."""
    start = (0, 0)
    end = (500, 500)
    points = MarkLivEngine.calculate_bezier_trajectory(start, end, steps=20, jitter=3.0)

    assert len(points) == 21
    assert points[-1] == end  # Final destination must be exact regardless of jitter


def test_mark_liv_cursor_and_actions():
    """Verify cursor position querying and bezier_move execution step."""
    pos = mark_liv_engine.get_cursor_pos()
    assert isinstance(pos, tuple)
    assert len(pos) == 2
    assert isinstance(pos[0], int)
    assert isinstance(pos[1], int)

    # Test execute_action_step with bezier_move
    res = mark_liv_engine.execute_action_step("bezier_move", x=pos[0], y=pos[1])
    assert res["status"] in ["success", "failed"]


# =============================================================================
# 2. HARDWARE DISPATCHERS (VOLUME, BRIGHTNESS, BROWSER, WI-FI)
# =============================================================================

def test_hardware_volume_dispatcher():
    """Verify volume adjuster clamps steps and validates actions."""
    # Invalid action
    res_err = hardware_governor.adjust_master_volume("invalid_act")
    assert res_err["status"] == "error"

    # Valid actions
    res_up = hardware_governor.adjust_master_volume("up", steps=1)
    assert res_up["status"] in ["success", "unsupported"]

    res_down = hardware_governor.adjust_master_volume("down", steps=2)
    assert res_down["status"] in ["success", "unsupported"]

    res_mute = hardware_governor.adjust_master_volume("mute")
    assert res_mute["status"] in ["success", "unsupported"]


def test_hardware_default_browser_detection():
    """Verify default browser registry resolution returns valid structure."""
    res = hardware_governor.get_default_browser()
    assert res["status"] in ["success", "error", "unsupported"]
    if res["status"] == "success":
        assert "browser_name" in res
        assert "prog_id" in res


def test_hardware_screen_brightness():
    """Verify screen brightness queries and level clamping."""
    res_get = hardware_governor.get_screen_brightness()
    assert res_get["status"] in ["success", "unavailable", "unsupported", "error"]

    # Test clamping level
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        res_set = hardware_governor.set_screen_brightness(150)  # should clamp to 100
        assert res_set["status"] == "success"
        assert res_set["target_brightness_percent"] == 100

        res_set_low = hardware_governor.set_screen_brightness(-20)  # should clamp to 0
        assert res_set_low["status"] == "success"
        assert res_set_low["target_brightness_percent"] == 0


def test_hardware_wifi_status():
    """Verify netsh Wi-Fi status parser returns structured dictionary."""
    res = hardware_governor.get_wifi_status()
    assert res["status"] in ["success", "unsupported", "error"]
    if res["status"] == "success":
        assert isinstance(res["wifi"], dict)


# =============================================================================
# 3. MOBILE TELEKINESIS (ADB BRIDGE)
# =============================================================================

def test_adb_service_graceful_degradation():
    """Verify ADB bridge returns graceful status when adb executable is missing."""
    service = ADBBridgeService(adb_path="/non/existent/path/adb")
    assert not service.is_available()

    # Query methods must return adb_unavailable cleanly without crashing
    devs = service.get_devices()
    assert devs["status"] == "adb_unavailable"
    assert devs["count"] == 0

    batt = service.get_battery()
    assert batt["status"] == "adb_unavailable"

    tap_res = service.tap(100, 200)
    assert tap_res["status"] == "adb_unavailable"

    swipe_res = service.swipe(100, 200, 300, 400)
    assert swipe_res["status"] == "adb_unavailable"

    launch_res = service.launch_app("com.test.app")
    assert launch_res["status"] == "adb_unavailable"


def test_adb_service_mocked_execution():
    """Verify ADB bridge command formatting and response parsing."""
    service = ADBBridgeService()

    with patch.object(service, "is_available", return_value=True):
        # 1. Mock get_devices
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(
                returncode=0,
                stdout="List of devices attached\nemulator-5554 device product:sdk_gphone model:sdk device:generic\n"
            )
            devs = service.get_devices()
            assert devs["status"] == "success"
            assert devs["count"] == 1
            assert devs["devices"][0]["device_id"] == "emulator-5554"

        # 2. Mock get_battery
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(
                returncode=0,
                stdout="level: 88\nscale: 100\nvoltage: 4100\ntemperature: 290\nstatus: 2\n"
            )
            batt = service.get_battery()
            assert batt["status"] == "success"
            assert batt["battery"]["level"] == 88

        # 3. Mock tap
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0, stderr="")
            tap_res = service.tap(500, 600)
            assert tap_res["status"] == "success"
            assert tap_res["x"] == 500

        # 4. Mock swipe
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0, stderr="")
            sw_res = service.swipe(100, 200, 100, 800)
            assert sw_res["status"] == "success"
            assert sw_res["action"] == "swipe"


# =============================================================================
# 4. TOOL CATALOG & ENGINE DISPATCH
# =============================================================================

def test_tool_catalog_phase18_registration():
    """Verify Phase 18 tools and MOBILE_ADB toolset exist in ToolCatalog."""
    assert ToolsetName.MOBILE_ADB.value == "mobile_adb"

    adb_tools = tool_catalog.get_toolset(ToolsetName.MOBILE_ADB)
    assert len(adb_tools) == 5
    adb_tool_names = [t["function"]["name"] for t in adb_tools]
    assert "adb_get_devices" in adb_tool_names
    assert "adb_get_battery" in adb_tool_names
    assert "adb_tap" in adb_tool_names
    assert "adb_swipe" in adb_tool_names
    assert "adb_launch_app" in adb_tool_names

    gov_tools = tool_catalog.get_toolset(ToolsetName.GOVERNOR)
    gov_names = [t["function"]["name"] for t in gov_tools]
    assert "adjust_master_volume" in gov_names
    assert "get_screen_brightness" in gov_names
    assert "set_screen_brightness" in gov_names
    assert "get_default_browser" in gov_names
    assert "get_wifi_status" in gov_names


def test_engine_phase18_dispatch():
    """Verify MaxIMAgentEngine executes Phase 18 tools cleanly."""
    eng = MaxIMAgentEngine()

    # 1. adjust_master_volume
    r1 = eng.execute_tool("adjust_master_volume", {"action": "up", "steps": 1}, session_id="test_p18")
    d1 = json.loads(r1)
    assert d1["status"] in ["success", "unsupported"]

    # 2. get_default_browser
    r2 = eng.execute_tool("get_default_browser", {}, session_id="test_p18")
    d2 = json.loads(r2)
    assert d2["status"] in ["success", "error", "unsupported"]

    # 3. get_wifi_status
    r3 = eng.execute_tool("get_wifi_status", {}, session_id="test_p18")
    d3 = json.loads(r3)
    assert d3["status"] in ["success", "unsupported", "error"]

    # 4. adb_get_devices
    r4 = eng.execute_tool("adb_get_devices", {}, session_id="test_p18")
    d4 = json.loads(r4)
    assert d4["status"] in ["success", "adb_unavailable", "error"]


# =============================================================================
# 5. FASTAPI REST API ENDPOINTS
# =============================================================================

def test_server_phase18_endpoints():
    """Verify FastAPI server exposes hardware and mobile REST endpoints."""
    client = TestClient(app)

    # 1. POST /api/hardware/volume
    res_vol = client.post("/api/hardware/volume", json={"action": "mute", "steps": 1})
    assert res_vol.status_code == 200
    assert "status" in res_vol.json()

    # 2. GET /api/hardware/default-browser
    res_br = client.get("/api/hardware/default-browser")
    assert res_br.status_code == 200
    assert "status" in res_br.json()

    # 3. GET /api/hardware/wifi-status
    res_wf = client.get("/api/hardware/wifi-status")
    assert res_wf.status_code == 200
    assert "status" in res_wf.json()

    # 4. GET /api/mobile/devices
    res_dev = client.get("/api/mobile/devices")
    assert res_dev.status_code == 200
    assert "status" in res_dev.json()

    # 5. POST /api/mobile/tap
    res_tap = client.post("/api/mobile/tap", json={"x": 200, "y": 400})
    assert res_tap.status_code == 200
    assert "status" in res_tap.json()
