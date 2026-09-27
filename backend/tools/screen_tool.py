"""
Real-Time Screen & Window Perception for MaxIM.
Detects active application windows on Windows and captures token-budgeted screen snapshots.
Enables 'What do you see?' vision queries.
"""
import io
import base64
import platform
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from PIL import Image, ImageGrab
from config import config

# Windows-specific window inspection via ctypes
def get_active_window_info() -> Dict[str, str]:
    """Retrieves the title and process of the currently focused foreground window on Windows."""
    try:
        from mark_liv import mark_liv_service
        win = mark_liv_service.get_active_window()
        if win:
            return {
                "title": win.title or "Untitled Window",
                "hwnd": str(win.hwnd),
                "process_name": win.process_name,
                "pid": str(win.pid),
            }
    except Exception:
        pass

    if platform.system() != "Windows":
        return {"title": "Non-Windows Host", "platform": platform.system()}

    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return {"title": "Unknown (Desktop/No Focus)", "hwnd": "0"}

        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return {"title": buff.value or "Untitled Window", "hwnd": str(hwnd)}
    except Exception as e:
        return {"title": "Detection Error", "error": str(e)}

class ScreenPerceptionTool:
    def __init__(self, max_dimension: int = 1280):
        self.max_dimension = max_dimension

    def capture_screenshot(self, as_base64: bool = True) -> Dict[str, Any]:
        """
        Captures the primary monitor screenshot, scales down to max_dimension
        for token budgeting, and returns base64 JPEG.
        """
        try:
            try:
                img = ImageGrab.grab()
                capture_mode = "live"
            except Exception:
                # Defensive fallback for non-interactive/virtual sessions
                img = Image.new("RGB", (1280, 720), color=(3, 7, 18))
                capture_mode = "fallback_canvas"

            orig_w, orig_h = img.size

            # Downscale proportionally if larger than max_dimension
            if max(orig_w, orig_h) > self.max_dimension:
                scale = self.max_dimension / max(orig_w, orig_h)
                new_size = (int(orig_w * scale), int(orig_h * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            else:
                new_size = (orig_w, orig_h)

            # Convert to RGB (in case of RGBA) and save as compressed JPEG buffer
            if img.mode != "RGB":
                img = img.convert("RGB")

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            jpeg_bytes = buffer.getvalue()

            b64_str = base64.b64encode(jpeg_bytes).decode("utf-8") if as_base64 else ""

            return {
                "success": True,
                "mode": capture_mode,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "original_dimensions": [orig_w, orig_h],
                "scaled_dimensions": list(new_size),
                "image_base64": b64_str,
                "bytes_size": len(jpeg_bytes),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def capture_screen(self) -> Image.Image:
        """Captures screen as PIL Image instance."""
        try:
            return ImageGrab.grab()
        except Exception:
            return Image.new("RGB", (1280, 720), color=(3, 7, 18))

    def inspect_screen(self) -> Dict[str, Any]:
        """
        Returns active window metadata and a compressed screenshot
        ready for multimodal LLM vision queries.
        """
        window_info = get_active_window_info()
        shot = self.capture_screenshot(as_base64=True)

        return {
            "active_window": window_info.get("title", "Unknown"),
            "active_window_info": window_info,
            "timestamp": shot.get("timestamp"),
            "screenshot_available": shot.get("success", False),
            "dimensions": shot.get("scaled_dimensions", []),
            "resolution": shot.get("scaled_dimensions", [1280, 720]),
            "image_base64": shot.get("image_base64", ""),
        }

    def get_active_window(self) -> str:
        """Convenience method returning currently focused window title."""
        return get_active_window_info().get("title", "Unknown")

    def get_screen_resolution(self) -> list:
        """Returns resolution dimensions."""
        shot = self.capture_screenshot(as_base64=False)
        return shot.get("scaled_dimensions", [1280, 720])

# Singleton instance
screen_tool = ScreenPerceptionTool()

