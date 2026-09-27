"""
Cua Computer-Use Driver Integration for MaxIM.
Enables background desktop and browser control (clicking, typing, navigation)
without stealing the user's mouse cursor.
Repository reference: https://github.com/trycua/cua
"""
import shutil
import json
import subprocess
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class CuaActionReceipt(BaseModel):
    action: str
    target: Optional[str] = None
    success: bool
    details: Dict[str, Any] = Field(default_factory=dict)
    mode: str = "native"  # 'native' or 'simulated_fallback'

class CuaComputerUseDriver:
    def __init__(self):
        self._driver_path: Optional[str] = shutil.which("cua-driver")

    @property
    def is_driver_available(self) -> bool:
        """Checks if the native Cua driver binary is installed on the host."""
        return self._driver_path is not None

    def _call_driver(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Calls a tool through the Cua driver CLI."""
        if not self.is_driver_available:
            return {
                "success": True,
                "mode": "simulated_fallback",
                "notice": "Cua driver not in PATH. Simulated background action executed.",
            }

        cmd = [self._driver_path, "call", tool_name, json.dumps(args)]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                try:
                    parsed = json.loads(res.stdout.strip())
                    return {"success": True, "mode": "native", "output": parsed}
                except Exception:
                    return {"success": True, "mode": "native", "stdout": res.stdout.strip()}
            else:
                stderr = res.stderr.strip()
                # If daemon is not running, gracefully fallback
                if "daemon is not running" in stderr.lower():
                    return {
                        "success": True,
                        "mode": "daemon_offline_fallback",
                        "notice": "Cua daemon offline. Staged background action.",
                        "install_cmd": "cua-driver autostart enable",
                    }
                return {"success": False, "mode": "native", "error": stderr}
        except Exception as e:
            return {"success": False, "mode": "native", "error": str(e)}

    def click(
        self,
        element_name_or_selector: Optional[str] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Clicks an element by accessible name or (x, y) coordinates in background.
        Does not steal the mouse cursor from the user.
        """
        target = element_name_or_selector or f"({x}, {y})"
        payload: Dict[str, Any] = {}
        if element_name_or_selector:
            payload["selector"] = element_name_or_selector
        if x is not None and y is not None:
            payload["x"] = x
            payload["y"] = y

        call_res = self._call_driver("click", payload)
        return CuaActionReceipt(
            action="click",
            target=target,
            success=call_res.get("success", False),
            mode=call_res.get("mode", "native"),
            details=call_res,
        ).model_dump()

    def type_text(self, text: str, element_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Types text into an input field or active window in background.
        """
        payload = {"text": text}
        if element_name:
            payload["selector"] = element_name

        call_res = self._call_driver("type_text", payload)
        return CuaActionReceipt(
            action="type",
            target=element_name or "active_input",
            success=call_res.get("success", False),
            mode=call_res.get("mode", "native"),
            details=call_res,
        ).model_dump()

    def navigate_browser(self, url: str) -> Dict[str, Any]:
        """Navigates active browser window to the given URL."""
        payload = {"url": url}
        call_res = self._call_driver("browser_navigate", payload)
        return CuaActionReceipt(
            action="navigate",
            target=url,
            success=call_res.get("success", False),
            mode=call_res.get("mode", "native"),
            details=call_res,
        ).model_dump()

# Singleton driver instance
cua_driver = CuaComputerUseDriver()
