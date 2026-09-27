# 🌌 MaxIM V2 — Sovereign Personal AI Executive Assistant & Cognitive Operating System

[![Backend Verification](https://img.shields.io/badge/Backend%20Tests-394%2F394%20Passing%20(100%25)-success?style=flat-square&logo=pytest)](file:///f:/MAXIM%20V2/backend/tests)
[![Frontend Verification](https://img.shields.io/badge/Frontend%20Tests-24%2F24%20Passing%20(100%25)-success?style=flat-square&logo=vitest)](file:///f:/MAXIM%20V2/frontend/tests)
[![Typecheck](https://img.shields.io/badge/TypeScript%20%26%20Python-Type%20Clean-blue?style=flat-square)](file:///f:/MAXIM%20V2/frontend)
[![Local GPU Acceleration](https://img.shields.io/badge/CUDA%20Acceleration-RTX%204050%20(6GB)-purple?style=flat-square&logo=nvidia)](file:///f:/MAXIM%20V2/backend)
[![Knowledge Engine](https://img.shields.io/badge/Obsidian-Bi--directional%20Vault-7c3aed?style=flat-square&logo=obsidian)](file:///f:/MAXIM%20V2/vault)

> **"Built for Sam. Sovereign, local-first, fiercely loyal, sarcastic, and ruthlessly accountable."**

---

## 🧭 Purpose & Vision

Modern commercial AI assistants suffer from three fatal flaws:
1. **Cloud Lock-in & Amnesia:** They reside in someone else's data center, read none of your personal notes, forget you the moment a session closes, and log your private thoughts.
2. **Corporate Sycophancy ("Slop"):** They act like bland, corporate customer-service bots that shower you with generic praise and flatter your bad habits instead of holding you accountable.
3. **Zero Native Action:** They are isolated in browser tabs, completely blind to your desktop windows, files, and background workflows.

**MaxIM V2** is built from the ground up as a **sovereign, local-first executive partner and cognitive Life Operating System (LifeOS)**. It runs directly on your personal hardware, integrates natively with an Obsidian markdown vault, speaks with an authentic personality, automates your desktop, and remembers everything across a 5-layer inside-out memory hierarchy.

---

## ⚡ Core Pillars

### 1. 🛡️ Unshakable Owner Loyalty & Zero-Egress Privacy Guard
- Permanently bound to **Sam**. MaxIM never feels defensive or resentful; critiques are treated as sovereign guidance.
- Outbound queries pass through a runtime privacy firewall that sanitizes file paths, PII, and blocks live API keys before any request touches an external network.

### 2. 🧠 Daniel Miessler's TELOS Framework & Obsidian Synapse
- Grounded in **TELOS** (*Targets, Execution, Lore, Operations, Stack*) defined in [`vault/00 - LifeOS/TELOS.md`](vault/00%20-%20LifeOS/TELOS.md).
- Bi-directional link parsing for `[[wikilinks]]`, tags, and maps of content (MOCs).
- Every insight, research session, skill recipe, and reflection is preserved as plain, portable Markdown.

### 3. 🎯 5-Layer Inside-Out Memory & 75% Safeguard
- **Layer 1 (Working):** Active context and immediate scratchpad.
- **Layer 2 (State & Perception):** Active windows, screen telemetry, and camera feed.
- **Layer 3 (Episodic):** Full turn history stored in SQLite WAL (`maxim.db`).
- **Layer 4 (Semantic):** Hybrid BM25 (FTS5) + 1024-dim dense vector embeddings with neural cross-encoder reranking.
- **Layer 5 (Procedural & Telos):** Crystallized operational skills and life goals.
- Automated 75% context cliff compaction saves dialogue checkpoints to vault notes before token limits degrade model output.

### 4. 🚀 Local-First Multi-Model Orchestration (NVIDIA RTX 4050 6GB)
Custom "Hot-Seat" GPU VRAM governor dynamically calculates context limits and offload layers to ensure models fit within laptop VRAM without triggering Windows PCIe paging:
- **Reasoning LLMs:** `Qwen3.5-9B`, `Qwen3.5-4B`, and `Gemma-4-E4B` managed via `llama-server.exe` on CUDA.
- **Vision Multimodal:** `Qwen3VL-4B-Instruct` paired with `mmproj-Qwen3VL-4B-Instruct-F16.gguf` for visual inspection and screen analysis.
- **Semantic Retrieval & Reranker:** Dedicated `Qwen3-Embedding-0.6B` and `Qwen3-Reranker-0.6B` for dense vault search.
- **Local Audio (audio.cpp CUDA):**
  - **ASR:** `Qwen3-ASR-0.6B` transcribing in **603ms (12.3x realtime)**.
  - **TTS:** `Qwen3-TTS-0.6B` synthesizing cloned studio audio in **3.2s**.

### 5. 🤖 Autonomous Subsystems
- **LobeHub Chief Agent Operator:** Coordinates multi-agent collaboration councils (`agent_chief`, `agent_hermes`, `agent_reach`, `agent_bitterbot`, `agent_zylos`) with automated shift handoff logs.
- **Idle Intelligence Scout:** Detects inactivity or sleep periods (23:00–07:00), curates high-signal tech intel from Hacker News and DuckDuckGo, and writes briefings.
- **Bitterbot Dream Engine:** Sarcastic morning wake-up briefings and offline thought consolidation.
- **Mark-LIV & TryCua OS Driver:** Win32 HWND desktop perception, window management, and background clicks/keystrokes without stealing mouse focus.
- **Adaptive Language Learner:** Real-time linguistic acquisition of local dialects (Bangla, Chakma, Chatgaya) with phonetic substitution.
- **Dynamic Extension Capsules (`backend/extensions/`):** Zero-config drop-in architecture for external tools and agents.

---

## 🏗️ Architecture

```
MAXIM V2/
├── backend/                        # Python 3.14 Native Backend
│   ├── .venv/                      # Isolated virtual environment
│   ├── config.py                   # Strict Pydantic configuration & zero-hallucination paths
│   ├── server.py                   # FastAPI production server with SSE streaming & REST API
│   ├── engine.py                   # Autonomous ReAct execution loop & dynamic intent scoping
│   ├── router.py                   # Multi-provider model gateway (Local CUDA, Ollama, Cloud)
│   ├── local_model_manager.py      # Hot-Seat VRAM governor & llama-server process manager
│   ├── retrieval_engine.py         # Semantic dense embeddings & neural reranker pipeline
│   ├── local_asr.py                # Ultra-fast Qwen3-ASR (audio.cpp CUDA) + Faster-Whisper
│   ├── voice.py                    # Voice cloning TTS (audio.cpp CUDA) + Edge-TTS + pyttsx3
│   ├── five_layer_memory.py        # 5-Layer inside-out memory & FTS5 BM25 search
│   ├── chief_operator.py           # Multi-agent collaboration councils & 24/7 shift logging
│   ├── idle_scout.py               # Sleep detector & overnight intelligence curator
│   ├── dream_engine.py             # Bitterbot reflection cycles & morning greeting generator
│   ├── mark_liv.py                 # Windows desktop window perception & action loop
│   ├── privacy_guard.py            # Outbound redaction & owner loyalty engine
│   ├── language_learner.py         # Adaptive local language & dialect acquisition
│   ├── workstation_sandbox.py      # QwenPaw command safety guard & project scaffolder
│   ├── extensions/                 # Dynamic GitHub repository capsules
│   └── tests/                      # 394 unit & integration tests (100% green)
│
├── frontend/                       # React 19 + TypeScript Luxury Interface
│   ├── src/
│   │   ├── App.tsx                 # Core application shell & navigation
│   │   ├── components/
│   │   │   ├── TelegramChat.tsx    # Streaming chat with collapsible receipts & audio feedback
│   │   │   ├── VisualUplink.tsx    # Live camera/screen HUD with "Snap to Chat" frame attach
│   │   │   ├── AgentsView.tsx      # Multi-agent roster & operator shift dispatch
│   │   │   ├── SkillsView.tsx      # Tool marketplace & dynamic extension capsules
│   │   │   └── SettingsView.tsx    # Provider gateways, privacy controls, hardware gauges
│   │   └── index.css               # Luxury dark aesthetic & fluid motion design
│   └── tests/                      # 24 Vitest UI tests (100% green)
│
├── models/                         # Local GGUF Model Inventory (Ignored in Git)
│   ├── llm/                        # General reasoning models (Qwen3.5-9B, 4B, Gemma)
│   ├── vision/                     # Multimodal models (Qwen3VL-4B + mmproj projector)
│   ├── embedding/                  # Dense vector models (Qwen3-Embedding, Qwen3-Reranker)
│   ├── asr/                        # Speech recognition models (Qwen3-ASR-0.6B/1.7B)
│   ├── tts/                        # Voice synthesis models (Qwen3-TTS-0.6B + voice reference)
│   └── reasoning/                  # Dedicated deep chain-of-thought models
│
└── vault/                          # Obsidian Markdown Vault
    ├── 00 - LifeOS/                # TELOS profile & master directives
    ├── 01 - Memory/                # Dialogue checkpoints & episodic reflections
    ├── 02 - Knowledge/             # Synthesized research & curated briefings
    ├── 02 - Skills/                # Crystallized action recipes & MOCs
    └── 03 - Agents/                # Operator team shift logs
```

---

## 🚦 Current Status & Unfinished Work

> **Notice:** MaxIM is an active, evolving personal engineering project. The core foundation, memory layers, multi-model execution, and frontend hookups are verified and fully operational. Several advanced frontiers are actively under construction:

| Subsystem | Status | Description |
|---|---|---|
| **Multi-Model Orchestration** | ✅ Operational | Qwen3.5 LLMs, Qwen3VL Vision, Qwen3 Embeddings/Reranker, Qwen3 ASR/TTS. |
| **Obsidian Vault & TELOS** | ✅ Operational | Bi-directional links, FTS5 BM25 search, reflection notes, memory checkpoints. |
| **Autonomous Operator & Scout**| ✅ Operational | Council chats, shift reports, idle habit tracking, and overnight briefings. |
| **Privacy & Desktop Control** | ✅ Operational | Outbound secret scrubbing, Win32 HWND automation, QwenPaw command sandbox. |
| **Continuous Wake-Word Loop** | 🟡 In Progress | Hands-free Web Speech is live; local offline zero-latency wake-word ("Hey MaxIM") is being wired directly to audio.cpp. |
| **Continuous Video Stream Vision**| 🟡 In Progress | "Snap to Chat" frame capture is live; real-time 30 FPS continuous visual attention loop is planned. |
| **DeepSeek-R1 Hot Seat Swapping**| 🟡 In Progress | Dynamic hot-swapping between fast tool-calling models (Qwen3.5) and deep thinking models (DeepSeek-R1). |
| **Encrypted Mobile Sync Bridge** | ⚪ Planned | P2P encrypted sync between laptop vault and mobile client over Tailscale/WebRTC. |

---

## 🛠️ Getting Started

### Prerequisites
- **OS:** Windows 11 (64-bit).
- **GPU:** NVIDIA GPU with CUDA 12+ (tested on RTX 4050 6GB Laptop GPU).
- **Python:** Python 3.11+ (Python 3.14 used in development).
- **Node.js:** Node.js 20+ with npm.
- **System Tools:** `ffmpeg` installed and available on system `PATH`.
- **audio.cpp binary:** `audiocpp_cli.exe` located at `~/.unsloth/audio.cpp/bin/audiocpp_cli.exe`.

---

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/SamJU25/Maxim-personal-assistant.git
cd Maxim-personal-assistant
```

#### 2. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
```

#### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

#### 4. Model Weights Setup
Drop your `.gguf` weights into the `models/` directory:
- `models/llm/`: `Qwen3.5-9B-abliterated-Q4_K_M.gguf` or `Qwen3.5-4B-Q6_K.gguf`
- `models/vision/`: `Qwen3VL-4B-Instruct-Q4_K_M.gguf` and `mmproj-Qwen3VL-4B-Instruct-F16.gguf`
- `models/embedding/`: `Qwen3-Embedding-0.6B-Q8_0.gguf` and `Qwen3-Reranker-0.6B-q8_0.gguf`
- `models/asr/`: `qwen3-asr-0.6b-q8_0.gguf`
- `models/tts/`: `qwen3-tts-12hz-0.6b-base-q8_0.gguf` and reference WAV file `voice_ref_16k.wav`

---

### Running MaxIM

#### ⚡ Option A: One-Click Launcher (Recommended)
Simply double-click either:
- **`start_maxim.bat`** (Batch launcher with visual colored terminal)
- **`start_maxim.exe`** (Native standalone Windows launcher)

The launcher automatically:
1. Validates Python virtualenv and Node dependencies (auto-installs if missing).
2. Boots the Backend FastAPI server on `http://127.0.0.1:8000`.
3. Boots the React 19 Frontend on `http://localhost:5173`.
4. Performs a health check ping to ensure all services are ready.
5. Automatically opens your default web browser directly to `http://localhost:5173`.
6. To stop all services, press `[ENTER]` / `[Q]` in the launcher or run `stop_maxim.bat`.

---

#### 🛠️ Option B: Manual Command-Line Launch
```bash
# Terminal 1 - Backend:
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 - Frontend:
cd frontend
npm run dev
```

---

## 🧪 Verification & Test Suites

MaxIM enforces strict test-driven reliability. All changes must pass 100% green before being committed.

```bash
# Run backend test suite (394 tests)
cd backend
pytest

# Run frontend test suite (24 tests)
cd frontend
npm test

# Run frontend typecheck
npm run typecheck

# Run production build
npm run build
```

---

## 🔒 Security & Privacy Notice

- **Local Execution:** All reasoning, embeddings, speech recognition, and audio synthesis run locally on your GPU by default.
- **Zero Telemetry:** MaxIM contains no tracking pixels, analytics, or third-party phone-home code.
- **Sanitization:** Live credentials, API keys, and sensitive local filesystem paths are blocked and stripped by `backend/privacy_guard.py` before external tool execution.

---

## 📄 License

This repository is maintained for personal use and research by **Sam**. Licensed under the [MIT License](LICENSE).
