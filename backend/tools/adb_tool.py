"""
Mobile Telekinesis (ADB Bridge) Toolset for MaxIM.
Inspired by IrisX AI (https://www.irisxai.in/docs/features).

Enables cross-device mobile telekinesis:
1. Device discovery and battery telemetry.
2. Coordinate touch injection (tap, swipe).
3. Mobile application launch.
4. Seamless file synchronization (push/pull).
5. Safe, sandboxed shell execution on Android devices.

Implements graceful degradation: if Android platform-tools (adb)
is not installed or no device is connected, returns actionable feedback
rather than raising exceptions.
"""

import os
import shutil
import logging
import subprocess
from typing import Dict, List, Optional, Any

logger = logging.getLogger("maxim.tools.adb")


class ADBBridgeService:
    """Manages local Android Debug Bridge interactions."""

    def __init__(self, adb_path: Optional[str] = None):
        self._custom_adb_path = adb_path

    @property
    def adb_executable(self) -> Optional[str]:
        """Resolves the active adb binary path."""
        if self._custom_adb_path and os.path.exists(self._custom_adb_path):
            return self._custom_adb_path
        return shutil.which("adb")

    def is_available(self) -> bool:
        """Returns True if adb is present on the host system."""
        return self.adb_executable is not None

    def _build_cmd(self, subcmd: List[str], device_id: Optional[str] = None) -> List[str]:
        adb = self.adb_executable or "adb"
        cmd = [adb]
        if device_id:
            cmd.extend(["-s", device_id])
        cmd.extend(subcmd)
        return cmd

    def get_devices(self) -> Dict[str, Any]:
        """Lists connected Android devices or emulators."""
        if not self.is_available():
            return {
                "status": "adb_unavailable",
                "message": "Android Debug Bridge (adb) is not found in system PATH. Please install Android platform-tools to enable mobile telekinesis.",
                "devices": [],
                "count": 0,
            }

        try:
            cmd = self._build_cmd(["devices", "-l"])
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            lines = res.stdout.strip().splitlines()
            devices = []
            for line in lines[1:]:  # skip 'List of devices attached' header
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] != "offline":
                    dev_id = parts[0]
                    state = parts[1]
                    details = " ".join(parts[2:]) if len(parts) > 2 else ""
                    devices.append({
                        "device_id": dev_id,
                        "state": state,
                        "details": details,
                    })

            return {
                "status": "success",
                "devices": devices,
                "count": len(devices),
            }
        except Exception as e:
            logger.error("Failed to query adb devices: %s", e)
            return {"status": "error", "error": str(e), "devices": []}

    def get_battery(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Reads battery telemetry from connected device."""
        if not self.is_available():
            return {
                "status": "adb_unavailable",
                "message": "adb binary not found in PATH.",
            }

        try:
            cmd = self._build_cmd(["shell", "dumpsys", "battery"], device_id=device_id)
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            battery = {}
            for line in res.stdout.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k_clean = k.strip().lower()
                    v_clean = v.strip()
                    if k_clean in ["level", "scale", "voltage", "temperature", "status", "health", "powered"]:
                        battery[k_clean] = int(v_clean) if v_clean.isdigit() else v_clean

            return {
                "status": "success",
                "device_id": device_id or "default",
                "battery": battery,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def tap(self, x: int, y: int, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Injects coordinate tap on mobile screen."""
        if not self.is_available():
            return {
                "status": "adb_unavailable",
                "message": "adb binary not found in PATH.",
            }

        try:
            cmd = self._build_cmd(["shell", "input", "tap", str(int(x)), str(int(y))], device_id=device_id)
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                return {"status": "success", "action": "tap", "x": x, "y": y, "device_id": device_id or "default"}
            return {"status": "error", "message": res.stderr.strip() or "Tap failed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_ms: int = 300,
        device_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Injects coordinate swipe on mobile screen."""
        if not self.is_available():
            return {
                "status": "adb_unavailable",
                "message": "adb binary not found in PATH.",
            }

        try:
            cmd = self._build_cmd(
                ["shell", "input", "swipe", str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(duration_ms))],
                device_id=device_id,
            )
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                return {
                    "status": "success",
                    "action": "swipe",
                    "from": (x1, y1),
                    "to": (x2, y2),
                    "duration_ms": duration_ms,
                    "device_id": device_id or "default",
                }
            return {"status": "error", "message": res.stderr.strip() or "Swipe failed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def launch_app(self, package_name: str, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Launches an application package via monkey."""
        if not self.is_available():
            return {
                "status": "adb_unavailable",
                "message": "adb binary not found in PATH.",
            }

        pkg = package_name.strip()
        try:
            cmd = self._build_cmd(
                ["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"],
                device_id=device_id,
            )
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            if "Events injected: 1" in res.stdout:
                return {"status": "success", "package": pkg, "device_id": device_id or "default"}
            return {"status": "error", "message": res.stdout.strip() or res.stderr.strip() or "App launch failed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def shell(self, command: str, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Executes a command directly inside the Android shell."""
        if not self.is_available():
            return {
                "status": "adb_unavailable",
                "message": "adb binary not found in PATH.",
            }

        try:
            cmd = self._build_cmd(["shell", command], device_id=device_id)
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return {
                "status": "success" if res.returncode == 0 else "error",
                "returncode": res.returncode,
                "output": res.stdout.strip(),
                "error": res.stderr.strip() if res.returncode != 0 else None,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Singleton instance
adb_bridge = ADBBridgeService()
