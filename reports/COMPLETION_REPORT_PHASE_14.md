# Phase 14 Completion Report: Mark-LIV Functional OS Automation & Vision-Action Loop

**Date**: 2026-09-25  
**Component**: MaxIM v2.0 - Phase 14 (Mark-LIV Functional OS Automation)  
**Status**: COMPLETE (100% Verified, 139/139 Backend Tests Green, Pure Backend Implementation)  

---

## 1. Executive Summary

Phase 14 implements **Mark-LIV Functional OS Automation & Vision-Action Loop** for MaxIM, based on [FatihMakes/Mark-LIV](https://github.com/FatihMakes/Mark-LIV):
1. **Strictly Functional Backend Scope**: 100% OS-level system automation and vision-action loop. Zero frontend or 3D visual overhead in strict accordance with the owner's directive.
2. **Desktop Window Perception & Topology**: Enumerates all top-level application windows on Windows, capturing Window Handles (HWNDs), window titles, process names, PIDs, geometry bounding boxes `(left, top, right, bottom)`, visibility, and active focus.
3. **Window Lifecycle Management**: Brings any window to the foreground (`focus_window`), restores minimized windows (`ShowWindow` SW_RESTORE), minimizes, maximizes, and cleanly terminates windows via WM_CLOSE.
4. **Application & Process Control**: Background application launcher (`launch_application`) with arguments and working directory, active process listing with memory footprints (MB), and process termination.
5. **Hardware-Level Input Simulation**: Direct Windows input synthesis via `ctypes.windll.user32`:
   - Keystrokes and hotkey combinations (`send_keys`: `ctrl+s`, `alt+tab`, `win+r`, `enter`, etc.).
   - Unicode text typing (`type_text`) with per-character typing delay.
   - Mouse positioning and clicking (`mouse_click`: left, right, middle, double-click).
   - Mouse wheel vertical scrolling (`mouse_scroll`).
6. **Vision-Action Mapping Loop**: Captures desktop or target window bounding boxes with fallback handling, executes multi-step action sequences (`execute_action_step`), and verifies action execution.
7. **Persistent SQLite WAL Action Ledger**: Logs every action, parameters, duration (ms), success status, and error into table `mark_liv_actions` in `maxim.db`.
8. **Hermes Modular Toolset & REST API**: Registers `ToolsetName.OS` in `backend/tools/catalog.py` (`os_list_windows`, `os_focus_window`, `os_launch_app`, `os_execute_action`, `os_list_processes`), wires into `backend/engine.py`, and exposes 5 FastAPI REST endpoints in `backend/server.py`.

---

## 2. Implemented Architecture & Seams

### 2.1 OS Automation Engine (`backend/mark_liv.py`)
- **Native ctypes Windows APIs**:
  - `user32.EnumWindows` & `user32.GetWindowRect` for window topology.
  - `user32.SetForegroundWindow` & `user32.ShowWindow` for window focus and state transitions.
  - `user32.keybd_event` with virtual key code translation (`VK_MAP`) for hardware keystrokes.
  - `user32.mouse_event` & `user32.SetCursorPos` for mouse clicks and scrolling.
- **Defensive Screen Capture**:
  - `ImageGrab.grab(bbox)` with programmatic `Image.new` canvas fallback when desktop display context is temporarily detached in non-interactive sessions.
- **SQLite WAL Persistence**:
  - `mark_liv_actions`: Records `timestamp`, `session_id`, `action_type`, `target`, `parameters`, `success`, `duration_ms`, and `error`.

### 2.2 Hermes Toolset Catalog (`backend/tools/catalog.py`)
- Added `ToolsetName.OS = "os"`.
- Registered `OS_TOOLS`:
  - `os_list_windows`: Lists open windows, HWNDs, process names, and bounding boxes.
  - `os_focus_window`: Brings targeted window to the foreground.
  - `os_launch_app`: Launches application or command line in the background.
  - `os_execute_action`: Executes direct mouse click, double click, right click, keystroke hotkey, text typing, or window minimize/maximize/close.
  - `os_list_processes`: Lists running processes with memory usage.

### 2.3 ReAct Engine Integration (`backend/engine.py`)
- `execute_tool`: Handled autonomous ReAct tool calls for all `os_*` tools, returning structured JSON receipts with execution status.

### 2.4 FastAPI REST Endpoints (`backend/server.py`)
| Endpoint | Method | Description |
|---|---|---|
| `/api/os/windows` | `GET` | Enumerates open application windows with geometry and HWNDs |
| `/api/os/action` | `POST` | Executes a direct OS automation action (click, type, hotkey, window lifecycle) |
| `/api/os/launch` | `POST` | Launches an application or executable in the background |
| `/api/os/processes` | `GET` | Lists running system processes with memory footprint |
| `/api/os/history` | `GET` | Retrieves recent OS automation execution receipts |

---

## 3. Verification Receipts

- `tests/test_phase14_mark_liv.py`: 10/10 unit and integration tests passing.
- Total backend test suite: **139/139 passed (100% Green)**.
