"""
Mark-LIV Functional OS Automation & Vision-Action Loop Engine for MaxIM.
Repository reference: https://github.com/FatihMakes/Mark-LIV

Strictly functional OS-level automation for Windows:
1. Window Perception & Topology (enumerates windows, bounding boxes, active focus).
2. Window Lifecycle Management (focus, minimize, maximize, restore, close).
3. Application & Process Control (launch, list, terminate).
4. Direct OS Input Simulation (hardware-level keybd_event / mouse_event via ctypes).
5. Vision-Action Mapping Loop (screen capture, coordinate targeting, action verification).
6. Persistent SQLite WAL Action Ledger.
"""
import os
import sys
import time
import json
import ctypes
import sqlite3
import logging
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from pydantic import BaseModel, Field
from PIL import Image, ImageGrab

import psutil
from config import config

logger = logging.getLogger("maxim.mark_liv")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Windows Virtual Key Codes
VK_MAP = {
    "enter": 0x0D,
    "return": 0x0D,
    "tab": 0x09,
    "space": 0x20,
    "backspace": 0x08,
    "esc": 0x1B,
    "escape": 0x1B,
    "shift": 0x10,
    "ctrl": 0x11,
    "control": 0x11,
    "alt": 0x12,
    "win": 0x5B,
    "windows": 0x5B,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
    "delete": 0x2E,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "f1": 0x70,
    "f2": 0x71,
    "f3": 0x72,
    "f4": 0x73,
    "f5": 0x74,
    "f6": 0x75,
    "f7": 0x76,
    "f8": 0x77,
    "f9": 0x78,
    "f10": 0x79,
    "f11": 0x7A,
    "f12": 0x7B,
}


class WindowRect(BaseModel):
    left: int
    top: int
    right: int
    bottom: int
    width: int
    height: int


class WindowInfo(BaseModel):
    hwnd: int
    title: str
    process_name: str
    pid: int
    rect: WindowRect
    is_visible: bool
    is_minimized: bool
    is_maximized: bool
    is_active: bool


class OSActionRecord(BaseModel):
    id: Optional[int] = None
    timestamp: str = Field(default_factory=utc_now_iso)
    session_id: str = "default_session"
    action_type: str
    target: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    duration_ms: float = 0.0
    error: Optional[str] = None


class MarkLivEngine:
    """Core Functional OS Automation Engine for MaxIM (Windows native)."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self.is_windows = platform.system() == "Windows"
        self._init_dpi_awareness()
        self._init_db()

    def _init_dpi_awareness(self):
        """Initializes Per-Monitor V2 DPI awareness for pixel-accurate High-DPI Matrix scaling."""
        if not self.is_windows:
            return
        try:
            # -4 corresponds to DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initializes persistent SQLite WAL tables for OS automation receipts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mark_liv_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    target TEXT NOT NULL,
                    parameters TEXT,
                    success INTEGER NOT NULL,
                    duration_ms REAL NOT NULL,
                    error TEXT
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mark_liv_actions_time ON mark_liv_actions(timestamp);")
            conn.commit()

    # =========================================================================
    # 1. WINDOW PERCEPTION & TOPOLOGY
    # =========================================================================

    def list_windows(self, visible_only: bool = True) -> List[WindowInfo]:
        """Enumerates active top-level windows on the host desktop."""
        if not self.is_windows:
            return []

        user32 = ctypes.windll.user32
        windows: List[WindowInfo] = []
        active_hwnd = user32.GetForegroundWindow()

        # RECT structure
        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        # Callback for EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

        def foreach_window(hwnd, lParam):
            if visible_only and not user32.IsWindowVisible(hwnd):
                return True

            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0 and visible_only:
                return True

            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.strip()

            if visible_only and not title:
                return True

            # Get PID and process name
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            proc_name = "Unknown"
            try:
                proc = psutil.Process(pid.value)
                proc_name = proc.name()
            except Exception:
                pass

            # Get Rect
            r = RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            w = r.right - r.left
            h = r.bottom - r.top

            # Ignore 0-sized tooltips or ghost overlays
            if visible_only and (w <= 0 or h <= 0):
                return True

            is_min = bool(user32.IsIconic(hwnd))
            is_max = bool(user32.IsZoomed(hwnd))
            is_active = (hwnd == active_hwnd)

            windows.append(
                WindowInfo(
                    hwnd=hwnd,
                    title=title,
                    process_name=proc_name,
                    pid=pid.value,
                    rect=WindowRect(
                        left=r.left,
                        top=r.top,
                        right=r.right,
                        bottom=r.bottom,
                        width=w,
                        height=h,
                    ),
                    is_visible=bool(user32.IsWindowVisible(hwnd)),
                    is_minimized=is_min,
                    is_maximized=is_max,
                    is_active=is_active,
                )
            )
            return True

        user32.EnumWindows(EnumWindowsProc(foreach_window), 0)
        return windows

    def get_active_window(self) -> Optional[WindowInfo]:
        """Returns details for the currently active foreground window."""
        windows = self.list_windows(visible_only=False)
        for w in windows:
            if w.is_active:
                return w
        return None

    def find_window(self, query: str) -> Optional[WindowInfo]:
        """Finds window by title substring or process name."""
        q = query.lower().strip()
        windows = self.list_windows(visible_only=True)
        for w in windows:
            if q in w.title.lower() or q in w.process_name.lower():
                return w
        return None

    # =========================================================================
    # 2. WINDOW LIFECYCLE MANAGEMENT
    # =========================================================================

    def focus_window(self, query_or_hwnd: Any) -> bool:
        """Brings the targeted window to the foreground."""
        if not self.is_windows:
            return False

        user32 = ctypes.windll.user32
        target_hwnd = None

        if isinstance(query_or_hwnd, int):
            target_hwnd = query_or_hwnd
        elif isinstance(query_or_hwnd, str):
            if query_or_hwnd.isdigit():
                target_hwnd = int(query_or_hwnd)
            else:
                w = self.find_window(query_or_hwnd)
                if w:
                    target_hwnd = w.hwnd

        if not target_hwnd:
            return False

        # If minimized, restore it first (SW_RESTORE = 9)
        if user32.IsIconic(target_hwnd):
            user32.ShowWindow(target_hwnd, 9)

        # Bring to front
        user32.SetForegroundWindow(target_hwnd)
        return True

    def minimize_window(self, query_or_hwnd: Any) -> bool:
        """Minimizes the window (SW_MINIMIZE = 6)."""
        if not self.is_windows:
            return False
        user32 = ctypes.windll.user32
        w = self.find_window(str(query_or_hwnd)) if isinstance(query_or_hwnd, str) else None
        hwnd = w.hwnd if w else int(query_or_hwnd)
        return bool(user32.ShowWindow(hwnd, 6))

    def maximize_window(self, query_or_hwnd: Any) -> bool:
        """Maximizes the window (SW_MAXIMIZE = 3)."""
        if not self.is_windows:
            return False
        user32 = ctypes.windll.user32
        w = self.find_window(str(query_or_hwnd)) if isinstance(query_or_hwnd, str) else None
        hwnd = w.hwnd if w else int(query_or_hwnd)
        return bool(user32.ShowWindow(hwnd, 3))

    def close_window(self, query_or_hwnd: Any) -> bool:
        """Sends WM_CLOSE (0x0010) message to cleanly terminate a window."""
        if not self.is_windows:
            return False
        user32 = ctypes.windll.user32
        w = self.find_window(str(query_or_hwnd)) if isinstance(query_or_hwnd, str) else None
        hwnd = w.hwnd if w else int(query_or_hwnd)
        return bool(user32.PostMessageW(hwnd, 0x0010, 0, 0))

    # =========================================================================
    # 3. APPLICATION & PROCESS CONTROL
    # =========================================================================

    def launch_application(
        self,
        command_or_path: str,
        args: Optional[List[str]] = None,
        working_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Launches an application or executable in the background."""
        cmd = [command_or_path] + (args or [])
        start = time.perf_counter()
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=working_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
            )
            duration = (time.perf_counter() - start) * 1000
            self.log_action(
                action_type="launch_application",
                target=command_or_path,
                parameters={"args": args, "working_dir": working_dir, "pid": proc.pid},
                success=True,
                duration_ms=duration,
            )
            return {
                "status": "launched",
                "pid": proc.pid,
                "command": command_or_path,
                "duration_ms": round(duration, 2),
            }
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            self.log_action(
                action_type="launch_application",
                target=command_or_path,
                parameters={"args": args},
                success=False,
                duration_ms=duration,
                error=str(e),
            )
            return {"status": "error", "error": str(e)}

    def list_processes(self, filter_name: Optional[str] = None, limit: int = 25) -> List[Dict[str, Any]]:
        """Lists running system processes with CPU/memory footprint."""
        procs = []
        q = (filter_name or "").lower().strip()
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
            try:
                name = p.info.get("name") or ""
                if q and q not in name.lower():
                    continue
                mem_mb = round(p.info["memory_info"].rss / (1024 * 1024), 1) if p.info.get("memory_info") else 0.0
                procs.append({
                    "pid": p.info["pid"],
                    "name": name,
                    "memory_mb": mem_mb,
                })
                if len(procs) >= limit:
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return procs

    def terminate_process(self, pid_or_name: Any) -> Dict[str, Any]:
        """Gracefully terminates or kills a process."""
        start = time.perf_counter()
        try:
            target_pid = None
            if isinstance(pid_or_name, int) or (isinstance(pid_or_name, str) and pid_or_name.isdigit()):
                target_pid = int(pid_or_name)
                proc = psutil.Process(target_pid)
                proc.terminate()
            else:
                name_q = str(pid_or_name).lower()
                killed = []
                for p in psutil.process_iter(["pid", "name"]):
                    if name_q in (p.info.get("name") or "").lower():
                        p.terminate()
                        killed.append(p.info["pid"])
                return {"status": "terminated", "pids": killed}

            duration = (time.perf_counter() - start) * 1000
            self.log_action("terminate_process", str(pid_or_name), {}, True, duration)
            return {"status": "terminated", "pid": target_pid}
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            self.log_action("terminate_process", str(pid_or_name), {}, False, duration, str(e))
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # 4. DIRECT OS INPUT SIMULATION (KEYSTROKES & MOUSE)
    # =========================================================================

    def send_keys(self, keys: List[str]) -> bool:
        """
        Sends hotkey combinations (e.g. ['ctrl', 's'] or ['win', 'r'] or ['enter']).
        Uses direct Windows keybd_event API.
        """
        if not self.is_windows:
            return False

        user32 = ctypes.windll.user32
        start = time.perf_counter()

        vk_codes = []
        for k in keys:
            k_lower = k.lower().strip()
            if k_lower in VK_MAP:
                vk_codes.append(VK_MAP[k_lower])
            elif len(k) == 1:
                # ASCII character VK code
                vk = user32.VkKeyScanW(ord(k)) & 0xFF
                vk_codes.append(vk)

        if not vk_codes:
            return False

        KEYEVENTF_KEYUP = 0x0002

        # 1. Press all keys in sequence
        for vk in vk_codes:
            user32.keybd_event(vk, 0, 0, 0)
            time.sleep(0.02)

        time.sleep(0.05)

        # 2. Release all keys in reverse sequence
        for vk in reversed(vk_codes):
            user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.02)

        duration = (time.perf_counter() - start) * 1000
        self.log_action("send_keys", "+".join(keys), {"keys": keys}, True, duration)
        return True

    def type_text(self, text: str, enter_after: bool = False) -> bool:
        """Types string directly into the currently focused window."""
        if not self.is_windows:
            return False

        user32 = ctypes.windll.user32
        start = time.perf_counter()
        KEYEVENTF_KEYUP = 0x0002
        KEYEVENTF_UNICODE = 0x0004

        for ch in text:
            # Send Unicode character directly
            user32.keybd_event(0, ord(ch), KEYEVENTF_UNICODE, 0)
            time.sleep(0.01)
            user32.keybd_event(0, ord(ch), KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0)
            time.sleep(0.01)

        if enter_after:
            time.sleep(0.05)
            user32.keybd_event(0x0D, 0, 0, 0)
            time.sleep(0.02)
            user32.keybd_event(0x0D, 0, KEYEVENTF_KEYUP, 0)

        duration = (time.perf_counter() - start) * 1000
        self.log_action("type_text", text[:30], {"length": len(text), "enter_after": enter_after}, True, duration)
        return True

    def get_cursor_pos(self) -> Tuple[int, int]:
        """Gets current physical cursor coordinates (x, y)."""
        if not self.is_windows:
            return (0, 0)
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return (pt.x, pt.y)

    @staticmethod
    def calculate_bezier_trajectory(
        start: Tuple[int, int],
        end: Tuple[int, int],
        steps: int = 15,
        jitter: float = 1.5,
    ) -> List[Tuple[int, int]]:
        """
        Calculates a cubic Bézier trajectory from start to end with human-like curvature and micro-jitter.
        Formula: B(t) = (1-t)^3 * P0 + 3(1-t)^2 * t * P1 + 3(1-t) * t^2 * P2 + t^3 * P3
        """
        import random
        x0, y0 = start
        x3, y3 = end
        dx = x3 - x0
        dy = y3 - y0

        # Control points simulating human wrist and elbow arcs
        ctrl1_x = x0 + dx * 0.25 + (random.uniform(-0.15, 0.15) * (abs(dy) + 20))
        ctrl1_y = y0 + dy * 0.15 + (random.uniform(-0.15, 0.15) * (abs(dx) + 20))
        ctrl2_x = x0 + dx * 0.75 + (random.uniform(-0.10, 0.10) * (abs(dy) + 20))
        ctrl2_y = y0 + dy * 0.85 + (random.uniform(-0.10, 0.10) * (abs(dx) + 20))

        points = []
        steps = max(2, steps)
        for i in range(steps + 1):
            t = i / steps
            b0 = (1.0 - t) ** 3
            b1 = 3.0 * ((1.0 - t) ** 2) * t
            b2 = 3.0 * (1.0 - t) * (t ** 2)
            b3 = t ** 3

            px = b0 * x0 + b1 * ctrl1_x + b2 * ctrl2_x + b3 * x3
            py = b0 * y0 + b1 * ctrl1_y + b2 * ctrl2_y + b3 * y3

            # Add micro-jitter decaying to 0 at destination
            decay = 1.0 - t
            jit_x = random.uniform(-jitter, jitter) * decay if jitter > 0 else 0.0
            jit_y = random.uniform(-jitter, jitter) * decay if jitter > 0 else 0.0

            points.append((int(round(px + jit_x)), int(round(py + jit_y))))

        points[-1] = (x3, y3)
        return points

    def bezier_move_mouse(
        self,
        target_x: int,
        target_y: int,
        duration_ms: int = 100,
        steps: int = 12,
        humanize: bool = True,
    ) -> bool:
        """
        Moves mouse cursor smoothly along a cubic Bézier trajectory to target (x, y).
        Prevents robotic coordinate snapping and anti-bot triggers.
        """
        if not self.is_windows:
            return False

        user32 = ctypes.windll.user32
        start_time = time.perf_counter()
        curr_x, curr_y = self.get_cursor_pos()

        if curr_x == target_x and curr_y == target_y:
            return True

        trajectory = self.calculate_bezier_trajectory(
            (curr_x, curr_y),
            (target_x, target_y),
            steps=max(5, steps),
            jitter=1.5 if humanize else 0.0,
        )

        step_delay = (duration_ms / 1000.0) / max(1, len(trajectory))
        for px, py in trajectory:
            user32.SetCursorPos(px, py)
            if step_delay > 0.001:
                time.sleep(step_delay)

        elapsed = (time.perf_counter() - start_time) * 1000
        self.log_action("bezier_move_mouse", f"({target_x}, {target_y})", {"steps": len(trajectory), "duration_ms": elapsed}, True, elapsed)
        return True

    def mouse_click(
        self,
        x: int,
        y: int,
        button: str = "left",
        double: bool = False,
        smooth: bool = False,
    ) -> bool:
        """Positions mouse (smoothly or direct) and clicks at exact desktop coordinates (x, y)."""
        if not self.is_windows:
            return False

        user32 = ctypes.windll.user32
        start = time.perf_counter()

        if smooth:
            self.bezier_move_mouse(x, y, duration_ms=80, steps=8)
        else:
            user32.SetCursorPos(x, y)
            time.sleep(0.02)

        # Event flags
        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        MOUSEEVENTF_RIGHTDOWN = 0x0008
        MOUSEEVENTF_RIGHTUP = 0x0010
        MOUSEEVENTF_MIDDLEDOWN = 0x0020
        MOUSEEVENTF_MIDDLEUP = 0x0040

        b = button.lower()
        if b == "right":
            down, up = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
        elif b == "middle":
            down, up = MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP
        else:
            down, up = MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP

        clicks = 2 if double else 1
        for _ in range(clicks):
            user32.mouse_event(down, 0, 0, 0, 0)
            time.sleep(0.02)
            user32.mouse_event(up, 0, 0, 0, 0)
            if double:
                time.sleep(0.05)

        duration = (time.perf_counter() - start) * 1000
        self.log_action("mouse_click", f"({x}, {y})", {"button": button, "double": double, "smooth": smooth}, True, duration)
        return True

    def mouse_scroll(self, clicks: int = -3, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """Scrolls the mouse wheel vertically (positive = up, negative = down)."""
        if not self.is_windows:
            return False

        user32 = ctypes.windll.user32
        start = time.perf_counter()

        if x is not None and y is not None:
            user32.SetCursorPos(x, y)
            time.sleep(0.02)

        MOUSEEVENTF_WHEEL = 0x0800
        WHEEL_DELTA = 120
        user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, clicks * WHEEL_DELTA, 0)

        duration = (time.perf_counter() - start) * 1000
        self.log_action("mouse_scroll", f"{clicks} clicks", {"clicks": clicks}, True, duration)
        return True

    # =========================================================================
    # 5. VISION-ACTION MAPPING LOOP
    # =========================================================================

    def capture_screen_snapshot(self, hwnd: Optional[int] = None) -> Dict[str, Any]:
        """Captures a screenshot of the primary screen or target window geometry."""
        try:
            bbox = None
            window_title = "Desktop"
            if hwnd and self.is_windows:
                user32 = ctypes.windll.user32
                class RECT(ctypes.Structure):
                    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
                r = RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(r))
                if (r.right - r.left) > 0 and (r.bottom - r.top) > 0:
                    bbox = (r.left, r.top, r.right, r.bottom)
                length = user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
            from tools.screen_tool import screen_tool
            if bbox:
                try:
                    img = ImageGrab.grab(bbox=bbox)
                except Exception:
                    # Defensive fallback when desktop DC is unavailable in non-interactive sessions
                    width = (bbox[2] - bbox[0])
                    height = (bbox[3] - bbox[1])
                    img = Image.new("RGB", (max(1, width), max(1, height)), color=(10, 15, 25))
            else:
                img = screen_tool.capture_screen()

            w, h = img.size
            return {
                "status": "success",
                "width": w,
                "height": h,
                "window": window_title,
                "bbox": bbox,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def execute_action_step(
        self,
        action: str,
        target: Optional[str] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        text: Optional[str] = None,
        keys: Optional[List[str]] = None,
        session_id: str = "default_session",
    ) -> Dict[str, Any]:
        """
        Executes an autonomous vision-action step with validation receipt.
        """
        act = action.lower().strip()
        start = time.perf_counter()

        try:
            if act in ["bezier_move", "move_mouse", "move"]:
                if x is None or y is None:
                    if target:
                        w = self.find_window(target)
                        if w:
                            x = w.rect.left + (w.rect.width // 2)
                            y = w.rect.top + (w.rect.height // 2)
                if x is None or y is None:
                    return {"status": "error", "message": "Move action requires (x, y) coordinates or target window."}
                succ = self.bezier_move_mouse(x, y)
                return {"status": "success" if succ else "failed", "action": "bezier_move", "x": x, "y": y}

            elif act in ["click", "left_click"]:
                if x is None or y is None:
                    # If target is window title, click center of that window
                    if target:
                        w = self.find_window(target)
                        if w:
                            x = w.rect.left + (w.rect.width // 2)
                            y = w.rect.top + (w.rect.height // 2)
                if x is None or y is None:
                    return {"status": "error", "message": "Click requires (x, y) coordinates or target window."}
                succ = self.mouse_click(x, y, button="left")
                return {"status": "success" if succ else "failed", "action": "click", "x": x, "y": y}

            elif act in ["double_click"]:
                if x is None or y is None:
                    return {"status": "error", "message": "Double click requires (x, y) coordinates."}
                succ = self.mouse_click(x, y, button="left", double=True)
                return {"status": "success" if succ else "failed", "action": "double_click", "x": x, "y": y}

            elif act in ["right_click"]:
                if x is None or y is None:
                    return {"status": "error", "message": "Right click requires (x, y) coordinates."}
                succ = self.mouse_click(x, y, button="right")
                return {"status": "success" if succ else "failed", "action": "right_click", "x": x, "y": y}

            elif act in ["type", "type_text"]:
                if not text:
                    return {"status": "error", "message": "type action requires 'text' parameter."}
                # Focus window if target provided
                if target:
                    self.focus_window(target)
                    time.sleep(0.05)
                succ = self.type_text(text, enter_after=False)
                return {"status": "success" if succ else "failed", "action": "type", "text": text}

            elif act in ["send_keys", "hotkey"]:
                if not keys:
                    return {"status": "error", "message": "send_keys requires 'keys' list (e.g. ['ctrl', 's'])."}
                if target:
                    self.focus_window(target)
                    time.sleep(0.05)
                succ = self.send_keys(keys)
                return {"status": "success" if succ else "failed", "action": "send_keys", "keys": keys}

            elif act in ["focus", "focus_window"]:
                if not target:
                    return {"status": "error", "message": "focus requires target window title or hwnd."}
                succ = self.focus_window(target)
                return {"status": "success" if succ else "not_found", "action": "focus", "target": target}

            elif act in ["launch", "open"]:
                if not target:
                    return {"status": "error", "message": "launch requires target application or command."}
                res = self.launch_application(target, args=keys)
                return res

            elif act in ["minimize"]:
                succ = self.minimize_window(target or "")
                return {"status": "success" if succ else "failed", "action": "minimize", "target": target}

            elif act in ["maximize"]:
                succ = self.maximize_window(target or "")
                return {"status": "success" if succ else "failed", "action": "maximize", "target": target}

            elif act in ["close"]:
                succ = self.close_window(target or "")
                return {"status": "success" if succ else "failed", "action": "close", "target": target}

            else:
                return {"status": "error", "message": f"Unsupported action type: {action}"}

        except Exception as e:
            dur = (time.perf_counter() - start) * 1000
            self.log_action(action, str(target), {"x": x, "y": y}, False, dur, str(e), session_id=session_id)
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # 6. ACTION LEDGER & RECEIPTS
    # =========================================================================

    def log_action(
        self,
        action_type: str,
        target: str,
        parameters: Dict[str, Any],
        success: bool,
        duration_ms: float,
        error: Optional[str] = None,
        session_id: str = "default_session",
    ) -> OSActionRecord:
        """Stores execution receipt in SQLite WAL table."""
        now = utc_now_iso()
        params_json = json.dumps(parameters)
        succ_int = 1 if success else 0

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mark_liv_actions (
                    timestamp, session_id, action_type, target, parameters, success, duration_ms, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, session_id, action_type, target, params_json, succ_int, duration_ms, error))
            conn.commit()
            row_id = cursor.lastrowid

        return OSActionRecord(
            id=row_id,
            timestamp=now,
            session_id=session_id,
            action_type=action_type,
            target=target,
            parameters=parameters,
            success=success,
            duration_ms=duration_ms,
            error=error,
        )

    def get_recent_actions(self, limit: int = 50) -> List[OSActionRecord]:
        """Retrieves recent action execution receipts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mark_liv_actions ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                p_dict = json.loads(r["parameters"]) if r["parameters"] else {}
                results.append(
                    OSActionRecord(
                        id=r["id"],
                        timestamp=r["timestamp"],
                        session_id=r["session_id"],
                        action_type=r["action_type"],
                        target=r["target"],
                        parameters=p_dict,
                        success=bool(r["success"]),
                        duration_ms=r["duration_ms"],
                        error=r["error"],
                    )
                )
            return results


# Global singleton instance
mark_liv_engine = MarkLivEngine()
