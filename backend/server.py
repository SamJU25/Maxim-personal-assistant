"""
MaxIM Native Backend - Production FastAPI Server
Provides high-performance SSE streaming, multi-provider model routing,
TELOS intent engineering, native Obsidian vault synapse, CUA execution,
and Bitterbot Dream Engine & Voice synthesis.
"""
import io
import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any, Union

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field

from config import config, utc_now_iso
from telos import telos_engine
from memory import memory_store
from router import model_router, ProviderType, ProviderConfig
from engine import agent_engine
from tools.screen_tool import screen_tool
from tools.cua_tool import cua_driver
from dream_engine import BitterbotDreamEngine
from voice import voice_synthesizer
from telegram_bot import telegram_uplink
from five_layer_memory import five_layer_memory
from tools.vault_tool import vault_synapse

# Configure server logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("maxim.server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown routines."""
    logger.info("Initializing MaxIM Native Cognitive Engine...")
    logger.info(f"Active Provider: {config.active_provider}")
    logger.info(f"Obsidian Vault: {config.vault_dir}")
    logger.info(f"TELOS Grounding: {config.telos_path.exists()}")

    # Initialize Telegram Remote Uplink if configured
    if telegram_uplink.is_configured:
        telegram_uplink.start()
        logger.info("Telegram Remote Uplink active.")
    else:
        logger.info("Telegram Remote Uplink idling (token not configured).")

    # Start Autonomous Watchdog & Cron Scheduler
    from cron_engine import watchdog_scheduler
    watchdog_scheduler.start()
    logger.info("Autonomous Watchdog & Cron Scheduler active.")

    yield

    logger.info("Shutting down MaxIM Native Cognitive Engine...")
    await telegram_uplink.stop()
    await watchdog_scheduler.stop()

app = FastAPI(
    title="MaxIM Cognitive System",
    description="Native autonomous AI operating system bridging LifeOS TELOS, Obsidian Memory, and Background CUA",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend applications (Vite dev server, local origins)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== REQUEST / RESPONSE MODELS ====================

class ChatRequest(BaseModel):
    message: str = Field(..., description="User query or command")
    session_id: Optional[str] = Field(default="default_session", description="Session identifier")
    stream: bool = Field(default=True, description="Enable SSE event stream")
    provider: Optional[str] = Field(default=None, description="Optional override provider")
    model: Optional[str] = Field(default=None, description="Optional override model name")
    has_image: Optional[bool] = Field(default=False, description="Whether prompt contains an image attachment")
    attachments: Optional[List[Dict[str, Any]]] = Field(default=None, description="Attached documents or images")

class ProviderSelectRequest(BaseModel):
    provider: str = Field(..., description="Provider identifier (google, chatgpt, deepseek, omniroute, custom, ollama)")
    model: Optional[str] = Field(default=None, description="Model identifier")

class CustomProviderRequest(BaseModel):
    name: str = Field(..., description="Custom provider identifier")
    base_url: str = Field(..., description="OpenAI-compatible base URL")
    api_key: str = Field(default="dummy-key", description="API key")
    model_name: str = Field(..., description="Model identifier")

class CuaActionRequest(BaseModel):
    action: str = Field(..., description="Action type: click, type, navigate, hotkey")
    element_name_or_selector: Optional[str] = None
    text: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    key: Optional[str] = None
    url: Optional[str] = None

class DreamTriggerRequest(BaseModel):
    session_id: Optional[str] = Field(default="default_session")

class VoiceSynthesizeRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize to speech")
    voice: Optional[str] = Field(default=None, description="Neural voice identifier")
    engine: Optional[str] = Field(default=None, description="Preferred engine: 'edge', 'local_fast', 'qwen3'")
    model: Optional[str] = Field(default=None, description="Optional local TTS model name")

class SubAgentCreateRequest(BaseModel):
    task: str = Field(..., description="Task for sub-agent")
    role: Optional[str] = "Specialist Worker"
    toolset: Optional[str] = "all"
    provider: Optional[str] = None
    model: Optional[str] = None
    max_iterations: Optional[int] = 4

class ConnectionRoleRequest(BaseModel):
    role: str = Field(..., description="Connection role (primary, subagents, fast, reasoning)")
    provider: str = Field(..., description="Target provider")
    model: Optional[str] = None

class MCPRegisterRequest(BaseModel):
    name: str = Field(..., description="MCP server name")
    transport: str = Field(default="stdio")
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    source_registry: Optional[str] = "custom"

class MCPCallRequest(BaseModel):
    server_name: str = Field(..., description="Target MCP server name")
    tool_name: str = Field(..., description="Target tool name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments payload matching tool schema")

class WatchdogTriggerRequest(BaseModel):
    job_name: str = Field(..., description="Scheduled job identifier")

class MemorySearchRequest(BaseModel):
    query: str = Field(..., description="Search keyword or concept")
    limit: Optional[int] = Field(default=10, description="Max search results")

class MemoryCompactRequest(BaseModel):
    session_id: str = Field(default="default_session", description="Session to compact")
    reason: Optional[str] = Field(default="Manual user compaction", description="Compaction trigger rationale")

class ReachReadRequest(BaseModel):
    url: str = Field(..., description="Target webpage URL to read")
    max_chars: Optional[int] = Field(default=10000, description="Max characters to extract")

class ReachSearchRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    max_results: Optional[int] = Field(default=6, description="Max search result items")

class ReachGitHubRequest(BaseModel):
    repo: str = Field(..., description="Repository in 'owner/repo' format")
    action: Optional[str] = Field(default="info", description="Inspection action: 'info', 'readme', or 'releases'")

class HireAgentRequest(BaseModel):
    name: str = Field(..., description="Display name of the agent")
    role: str = Field(..., description="Specialty role or function")
    persona: str = Field(..., description="Operating directives and personality")
    avatar: Optional[str] = Field(default="Sparkles", description="Avatar icon name")
    toolsets: Optional[List[str]] = Field(default_factory=lambda: ["vault"], description="Assigned toolsets")
    skills: Optional[List[str]] = Field(default_factory=list, description="Assigned specialized skills")
    category: Optional[str] = Field(default=None, description="Primary domain category")
    provider: Optional[str] = None
    model: Optional[str] = None

class CreateGroupRequest(BaseModel):
    name: str = Field(..., description="Group name")
    description: str = Field(..., description="Objective or charter of the group")
    member_ids: List[str] = Field(..., description="IDs of member agents")
    category: Optional[str] = Field(default=None, description="Domain category")
    topic: Optional[str] = None

class AssembleDynamicGroupRequest(BaseModel):
    topic: str = Field(default="", description="Objective or project topic for the ad-hoc group")
    group_name: Optional[str] = Field(default=None, description="Optional custom name for the group")
    skills_requested: Optional[List[str]] = Field(default=None, description="Optional list of specific skill IDs requested")
    desktop_context: Optional[str] = Field(default=None, description="Optional manual desktop context string")
    use_active_window: bool = Field(default=False, description="Whether to inspect current active foreground window")

class GroupChatRequest(BaseModel):
    message: str = Field(..., description="User prompt or task for the agent team")
    rounds: Optional[int] = Field(default=1, description="Number of turn rounds per member")

class DispatchGroupTaskRequest(BaseModel):
    task_prompt: str = Field(..., description="Directive or task brief from MaxIM")
    target_agent_ids: Optional[List[str]] = Field(default=None, description="Optional target agent IDs")
    rounds: Optional[int] = Field(default=1, description="Number of discussion rounds")

class OrchestrateObjectiveRequest(BaseModel):
    objective: str = Field(..., description="High-level goal or mission for MaxIM to orchestrate")
    preferred_category: Optional[str] = Field(default=None, description="Optional category hint")
    rounds: Optional[int] = Field(default=1, description="Number of discussion rounds")
    save_to_vault: Optional[bool] = Field(default=True, description="Save report to Obsidian vault")

class CrossGroupHandoffRequest(BaseModel):
    source_group_id: str = Field(..., description="Source group ID")
    target_group_id: str = Field(..., description="Target group ID")
    deliverable_summary: str = Field(..., description="Summary of deliverable")
    next_step_instruction: str = Field(..., description="Instruction for receiving group")
    rounds: Optional[int] = Field(default=1, description="Number of discussion rounds")

class ExecuteShiftRequest(BaseModel):
    agent_id: str = Field(..., description="Agent to execute shift")
    task: str = Field(..., description="Shift assignment or mission")
    save_to_vault: Optional[bool] = Field(default=True, description="Save executive summary to Obsidian vault")

class ProactiveEvaluateRequest(BaseModel):
    session_id: Optional[str] = Field(default="default_session", description="Session identifier")
    force: Optional[bool] = Field(default=False, description="Whether to bypass cooldown")

class ProactiveSettingsRequest(BaseModel):
    mode: Optional[str] = Field(default=None, description="gentle, balanced, proactive, muted")
    auto_speak: Optional[bool] = Field(default=None, description="Whether to auto-speak interventions")
    cooldown_minutes: Optional[int] = Field(default=None, description="Minimum cooldown minutes")

class ScoutTriggerRequest(BaseModel):
    trigger_type: Optional[str] = Field(default="manual", description="sleep, idle, manual")
    force: Optional[bool] = Field(default=True, description="Whether to bypass idle check")

class ScoutSettingsRequest(BaseModel):
    enabled: Optional[bool] = None
    idle_threshold_minutes: Optional[int] = None
    night_start_hour: Optional[int] = None
    night_end_hour: Optional[int] = None
    auto_generate_audio: Optional[bool] = None

class AddInterestTopicRequest(BaseModel):
    topic: str = Field(..., description="Topic name to track")
    category: Optional[str] = Field(default="tech", description="Category: tech, project, ai, general")

class RetainMemoryRequest(BaseModel):
    content: str = Field(..., description="Fact, rule, observation, or preference content")
    category: Optional[str] = Field(default="observation", description="world, experience, opinion, observation, preference")
    source: Optional[str] = Field(default="api", description="Origin of the memory")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata dictionary")
    session_id: Optional[str] = Field(default="default_session", description="Session identifier")

class RecallMemoryRequest(BaseModel):
    query: str = Field(..., description="Query string for semantic/lexical memory search")
    top_k: Optional[int] = Field(default=5, description="Number of results to retrieve per network")
    include_mental_models: Optional[bool] = Field(default=True, description="Whether to include synthesized mental models")
    session_id: Optional[str] = Field(default="default_session", description="Session identifier")

class ReflectMemoryRequest(BaseModel):
    topic: Optional[str] = Field(default="general", description="Topic focus for reflection")
    session_id: Optional[str] = Field(default="default_session", description="Session identifier to pull recent observations from")

class MentalModelPatchRequest(BaseModel):
    confidence: Optional[float] = Field(default=None, description="Updated confidence score (0.0 to 1.0)")
    disposition: Optional[str] = Field(default=None, description="Updated disposition text")
    status: Optional[str] = Field(default=None, description="active, superseded, disproven")

class InboundWebhookRequest(BaseModel):
    channel: Optional[str] = Field(default="webhook", description="Channel identifier: webhook, discord, slack, etc.")
    sender_id: str = Field(..., description="Unique ID of external user/system")
    sender_name: Optional[str] = Field(default="External User", description="Display name of sender")
    content: str = Field(..., description="User message or prompt")
    session_id: Optional[str] = Field(default=None, description="Optional custom session ID")
    reply_target: Optional[str] = Field(default=None, description="Optional webhook or chat ID to receive the response")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional client payload metadata")

class ChannelConfigRequest(BaseModel):
    channel: str = Field(..., description="Channel name: discord, slack, telegram, webhook")
    enabled: Optional[bool] = Field(default=True, description="Whether channel is active")
    bot_token: Optional[str] = Field(default=None, description="Bot token or API key")
    webhook_url: Optional[str] = Field(default=None, description="Incoming/outgoing webhook URL")
    allowed_ids: Optional[List[str]] = Field(default=None, description="List of authorized sender IDs")
    extra_config: Optional[Dict[str, Any]] = Field(default=None, description="Optional extra settings")

class RemoteSendRequest(BaseModel):
    channel: str = Field(..., description="Target channel: discord, slack, telegram, webhook")
    target: str = Field(..., description="Target webhook URL, channel ID, or chat ID")
    text: str = Field(..., description="Message body to send")
    title: Optional[str] = Field(default=None, description="Optional message title")

class RemoteBroadcastRequest(BaseModel):
    text: str = Field(..., description="Message text to broadcast")
    title: Optional[str] = Field(default=None, description="Optional message title")
    channels: Optional[List[str]] = Field(default=None, description="Optional subset of channels to broadcast to")

class SecurityScanRequest(BaseModel):
    text: str = Field(..., description="Payload or prompt content to inspect for threats")
    source: Optional[str] = Field(default="api", description="Origin source: web, webhook, user, file")

class SecuritySettingsRequest(BaseModel):
    mode: Optional[str] = Field(default=None, description="strict, balanced, permissive")
    block_injections: Optional[bool] = Field(default=None, description="Whether to actively defang/block prompt injections")
    quarantine_untrusted: Optional[bool] = Field(default=None, description="Whether to isolate untrusted text in XML tags")
    restrict_remote_tier4: Optional[bool] = Field(default=None, description="Whether to block remote sessions from invoking Tier 4 OS tools")

class ToolAuditRequest(BaseModel):
    tool_name: str = Field(..., description="Target tool name to audit")
    arguments: Optional[Dict[str, Any]] = Field(default=None, description="Arguments dictionary")
    session_id: Optional[str] = Field(default="default_session", description="Caller session ID")

class EmbedRequest(BaseModel):
    text: Optional[str] = Field(default=None, description="Single text string to embed")
    texts: Optional[List[str]] = Field(default=None, description="Batch of text strings to embed")
    auto_boot: Optional[bool] = Field(default=False, description="Whether to auto-start embedding server if offline")

class RerankRequest(BaseModel):
    query: str = Field(..., description="Query string to rank documents against")
    documents: List[str] = Field(..., description="Candidate document passages")
    top_k: Optional[int] = Field(default=5, description="Number of top results to return")
    auto_boot: Optional[bool] = Field(default=False, description="Whether to auto-start reranker server if offline")

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., description="Query to search across Obsidian vault notes")
    max_results: Optional[int] = Field(default=10, description="Max results to return")
    auto_boot: Optional[bool] = Field(default=False, description="Whether to auto-start retrieval server if offline")

# ==================== API ENDPOINTS ====================

@app.get("/health")
@app.get("/api/status")
@app.get("/api/health")
async def health_check():
    """Returns runtime health status and active provider."""
    cfg = model_router.get_provider_config()
    return {
        "status": "healthy",
        "system": "MaxIM Native Backend v2.0",
        "active_provider": config.active_provider,
        "active_model": cfg.default_model if cfg else "",
        "vault_path": str(config.vault_dir),
        "vault_exists": config.vault_dir.exists(),
        "telos_exists": config.telos_path.exists(),
        "database": str(config.db_path),
        "telegram_uplink_active": telegram_uplink.is_running,
    }

@app.get("/api/telos")
async def get_telos():
    """Returns the parsed LifeOS TELOS framework and markdown content."""
    telos_data = telos_engine.load_telos()
    return {
        "profile": telos_data,
        "formatted_context": telos_engine.get_context_injection(),
        "path": str(config.telos_path),
    }

@app.get("/api/vault/notes")
async def get_vault_notes(folder: Optional[str] = None, query: Optional[str] = None):
    """Returns list of real Obsidian vault notes with metadata and snippets."""
    import re
    from datetime import datetime

    vault_root = config.vault_dir
    if not vault_root.exists():
        return []

    notes = []
    base_dir = (vault_root / folder).resolve() if folder else vault_root.resolve()
    try:
        base_dir.relative_to(vault_root.resolve())
    except ValueError:
        return []

    if not base_dir.exists():
        return []

    for path in base_dir.rglob("*.md"):
        try:
            content = path.read_text(encoding="utf-8")
            if query and query.lower() not in content.lower() and query.lower() not in path.stem.lower():
                continue

            tags = re.findall(r"(?:^|\s)#([A-Za-z0-9_/-]+)", content)
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            snippet = ""
            for line in content.splitlines():
                clean_l = line.strip()
                if clean_l and not clean_l.startswith("#"):
                    snippet = clean_l
                    break
            if not snippet:
                snippet = content[:120].strip()

            notes.append({
                "id": path.stem,
                "title": path.stem,
                "path": path.relative_to(vault_root).as_posix(),
                "folder": path.parent.name,
                "tags": [f"#{t}" for t in tags[:4]],
                "updatedAt": mtime.strftime("%b %d, %H:%M"),
                "snippet": snippet[:140],
            })
        except Exception:
            continue
    return notes

@app.get("/api/vault/folders")
async def get_vault_folders():
    """Returns list of top-level vault folders and their note counts."""
    vault_root = config.vault_dir
    if not vault_root.exists():
        return []

    folders = []
    for item in sorted(vault_root.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            count = len(list(item.rglob("*.md")))
            folders.append({"name": item.name, "count": count})
    return folders

@app.get("/api/vault/note")
async def get_vault_note(title: str = Query(...)):
    """Reads full content and wikilinks of an Obsidian note."""
    return vault_synapse.read_note(title)

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """
    Cognitive ReAct execution endpoint.
    Supports SSE streaming or standard JSON response.
    """
    # Automatic Vision Model Routing: detect image attachments or visual creation/viewing queries
    has_img = bool(req.has_image) or (
        bool(req.attachments) and any(
            (a.get("type") or "").startswith("image/") or str(a.get("name") or "").lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"))
            for a in req.attachments
        )
    )
    q_clean = (req.message or "").lower()

    # Image GENERATION intent is a tool call (generate_image) for standard LLMs, NOT a vision model task!
    is_image_generation = any(
        k in q_clean for k in (
            "generate image", "generating image", "create image", "creating image",
            "draw a", "draw ", "render image", "generate a picture", "create a picture",
            "make a picture", "make an image", "picture of a", "photo of a", "illustration of"
        )
    )

    # Visual INSPECTION intent: user wants to inspect/see an attached image or screen
    is_visual_inspection = has_img or (not is_image_generation and any(
        k in q_clean for k in (
            "ocr", "visual inspection", "look at this", "look at the image",
            "what does the picture look like", "what is in this photo",
            "what do you see", "describe the image", "see image", "screenshot analysis", "inspect image"
        )
    ))

    # Process and save any attachments locally so tools can access them
    processed_message = req.message
    if req.attachments:
        from document_reader import document_reader
        attachment_notes = []
        for att in req.attachments:
            att_name = att.get("name", "attachment")
            data_url = att.get("dataUrl")
            content = att.get("content")
            if data_url:
                try:
                    saved_path = document_reader.save_attachment_base64(att_name, data_url)
                    attachment_notes.append(f"[Attached Image saved to: {saved_path}]")
                except Exception as ex:
                    logger.debug(f"Could not save base64 attachment: {ex}")
            elif content:
                try:
                    saved_path = document_reader.save_attachment_bytes(att_name, content.encode("utf-8"))
                    attachment_notes.append(f"[Attached Document saved to: {saved_path}]")
                except Exception as ex:
                    logger.debug(f"Could not save text attachment: {ex}")
            else:
                attachment_notes.append(f"[Attached File: {att_name}]")
        if attachment_notes:
            processed_message = f"{processed_message}\n\n" + "\n".join(attachment_notes)

    # Parse explicit cloud model selector format: cloud:<provider>:<model>
    if req.model and req.model.startswith("cloud:"):
        parts = req.model.split(":", 2)
        if len(parts) >= 2:
            req.provider = parts[1]
            req.model = parts[2] if len(parts) > 2 else None

    # Auto-boot native llama-server for Method B local models or autonomous auto-selection
    if req.provider == "local" or (req.model and ("auto" in req.model.lower() or "local" in req.model.lower())) or is_visual_inspection:
        from local_model_manager import local_model_manager
        try:
            chosen = None
            if not req.model or req.model in ("auto", "local:auto") or is_visual_inspection:
                task = "vision" if is_visual_inspection else "auto"
                chosen = local_model_manager.select_best_model(
                    task_type=task,
                    has_image=has_img,
                    query=req.message,
                )
                if chosen:
                    if chosen.get("is_cloud"):
                        req.provider = chosen.get("provider", "openai")
                        req.model = chosen.get("file_name")
                    else:
                        req.model = chosen["file_name"]
                        req.provider = "local"
            if req.provider == "local":
                local_model_manager.ensure_model_running(chosen["path"] if chosen else req.model)
        except Exception as e:
            logger.warning(f"Could not auto-start local model: {e}")
            # Automatic Cloud Failover: if local model fails to start, check if any cloud provider is connected
            try:
                from router import model_router
                cloud_provs = model_router.get_connected_cloud_providers()
                if cloud_provs:
                    fallback_p = cloud_provs[0]
                    logger.info(f"Failing over to connected cloud provider '{fallback_p['provider']}' ({fallback_p['model_name']})")
                    req.provider = fallback_p["provider"]
                    req.model = fallback_p["model_name"]
            except Exception as fe:
                logger.warning(f"Cloud failover error: {fe}")

    if req.stream:
        async def event_generator():
            try:
                async for event in agent_engine.run_turn_stream(
                    user_message=processed_message,
                    session_id=req.session_id or "default_session",
                    provider=req.provider,
                    model=req.model,
                ):
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as e:
                logger.error(f"Error during streaming turn: {e}")
                err_msg = str(e)
                if "Connection error" in err_msg or "ConnectError" in err_msg or "timed out" in err_msg:
                    current_prov = req.provider or model_router.active_provider
                    err_msg = f"LLM Connection Error: Could not connect to '{current_prov}'. If using a local model server (Ollama, Unsloth, LM Studio), please check that it is running on the configured host/port, or switch providers in the Settings tab."
                err_event = {"type": "error", "error": err_msg}
                yield f"data: {json.dumps(err_event)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    else:
        result = await agent_engine.run_turn(
            user_message=processed_message,
            session_id=req.session_id or "default_session",
            provider=req.provider,
            model=req.model,
        )
        return result

@app.get("/api/session")
async def get_session(session_id: str = Query(default="default_session")):
    """Retrieves session messages, remembered facts, and execution receipts."""
    messages = memory_store.get_messages(session_id, limit=50)
    facts = memory_store.get_facts()
    receipts = memory_store.get_receipts(session_id, limit=30)
    return {
        "session_id": session_id,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at,
            }
            for m in messages
        ],
        "facts": [
            {
                "id": f.id,
                "category": f.category,
                "key": f.key,
                "value": f.value,
                "created_at": f.updated_at,
            }
            for f in facts
        ],
        "receipts": [
            {
                "id": r.get("id"),
                "tool_name": r.get("tool_name"),
                "input_parameters": r.get("arguments"),
                "output_result": r.get("result"),
                "created_at": r.get("timestamp"),
            }
            for r in receipts
        ],
    }

@app.post("/api/session/new")
async def create_new_session():
    """Generates a fresh session ID."""
    new_id = f"session_{uuid.uuid4().hex[:12]}"
    memory_store.create_session(new_id)
    return {"session_id": new_id}

@app.get("/api/directives/frequent")
async def get_frequent_directives(limit: int = 4):
    """Returns frequent and recent user directives based on actual daily usage."""
    directives = memory_store.get_frequent_user_directives(limit=limit)
    return {"directives": directives}

@app.get("/api/providers")
async def list_providers():
    """Returns all registered LLM providers and the active provider."""
    providers = model_router.list_providers()
    return {
        "active_provider": config.active_provider,
        "providers": providers,
        "connected_cloud_providers": model_router.get_connected_cloud_providers(),
    }

@app.post("/api/providers/select")
async def select_provider(req: ProviderSelectRequest):
    """Switches the active LLM provider."""
    prov_name = req.provider.lower()
    if prov_name not in model_router.providers:
        raise HTTPException(status_code=400, detail=f"Provider '{req.provider}' is not registered.")
    
    config.active_provider = prov_name
    model_router.active_provider = prov_name
    if req.model:
        model_router.providers[prov_name].model_name = req.model

    return {
        "status": "success",
        "active_provider": config.active_provider,
        "active_model": model_router.providers[prov_name].model_name,
    }

@app.post("/api/providers/custom")
async def register_custom_provider(req: CustomProviderRequest):
    """Registers a new OpenAI-compatible custom provider."""
    model_router.register_custom_provider(
        name=req.name,
        base_url=req.base_url,
        api_key=req.api_key,
        model_name=req.model_name,
    )
    return {
        "status": "registered",
        "name": req.name,
        "base_url": req.base_url,
        "model_name": req.model_name,
    }

@app.get("/api/screen")
def get_screen():
    """Captures desktop screen state and foreground window."""
    info = screen_tool.inspect_screen()
    return info

@app.post("/api/cua/act")
def execute_cua(req: CuaActionRequest):
    """Dispatches low-level CUA actions without mouse cursor theft."""
    act = req.action.lower()
    if act == "click":
        res = cua_driver.click(element_name_or_selector=req.element_name_or_selector, x=req.x, y=req.y)
    elif act == "type":
        res = cua_driver.type_text(text=req.text or "", element_name=req.element_name_or_selector)
    elif act == "navigate":
        res = cua_driver.navigate_browser(url=req.url or "")
    elif act == "hotkey":
        res = cua_driver.hotkey(key_combination=req.key or "")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {req.action}")
    
    if isinstance(res, dict) and "status" not in res:
        res["status"] = "success" if res.get("success", True) else "failed"
    return res

@app.post("/api/dream/trigger")
async def trigger_dream(req: DreamTriggerRequest):
    """Triggers the Bitterbot offline reflection cycle."""
    dreamer = BitterbotDreamEngine(memory_store=memory_store)
    thought = dreamer.run_dream_cycle(session_id=req.session_id or "default_session")
    return {
        "status": "completed",
        "session_id": req.session_id,
        "synthesis": thought,
    }

@app.get("/api/morning-greeting")
async def get_morning_greeting():
    """Generates the sarcastic Bitterbot morning wake-up brief."""
    dreamer = BitterbotDreamEngine(memory_store=memory_store)
    greeting = dreamer.get_morning_greeting()
    return {"greeting": greeting}

@app.post("/api/voice/synthesize")
async def synthesize_voice(req: VoiceSynthesizeRequest):
    """Synthesizes text to speech returning streaming audio/mpeg."""
    try:
        spoken_text = voice_synthesizer.format_text_for_speech(req.text)
        audio_bytes = await voice_synthesizer.speak_to_bytes(
            text=spoken_text or req.text,
            voice=req.voice,
            engine=req.engine,
            preferred_model=req.model,
        )
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Voice synthesis error: {e}")
        raise HTTPException(status_code=500, detail=f"Voice synthesis failed: {e}")

@app.post("/api/voice/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
    model: Optional[str] = None,
):
    """Transcribes uploaded microphone audio using the local ASR engine (Qwen3-ASR on CUDA / Faster-Whisper)."""
    try:
        from pathlib import Path
        from local_asr import local_asr
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio payload")
        suffix = Path(file.filename or "recording.webm").suffix or ".webm"
        text = local_asr.transcribe_bytes(audio_bytes, suffix=suffix, preferred_model=model)
        return {"status": "success", "text": text}
    except Exception as e:
        logger.error(f"Local ASR transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

@app.get("/api/audio/status")
async def get_audio_status():
    """Returns operational status, model discovery, and acceleration metrics for local ASR & TTS pipelines."""
    try:
        from local_asr import local_asr
        from voice import voice_engine
        return {
            "status": "ready",
            "asr": local_asr.get_status(),
            "tts": voice_engine.get_status(),
        }
    except Exception as e:
        logger.error(f"Audio status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to inspect audio status: {e}")


@app.post("/api/subagent/create")
async def create_subagent_endpoint(req: SubAgentCreateRequest):
    """Spawns an isolated Hermes/Nanobot sub-agent worker."""
    from subagent import subagent_pool
    whitelist = None if req.toolset == "all" else ["read_vault_note", "search_vault", "find_vault_backlinks"]
    sub = subagent_pool.create_subagent(
        task=req.task,
        role=req.role or "Specialist Worker",
        provider=req.provider,
        model=req.model,
        toolset_whitelist=whitelist,
        max_iterations=req.max_iterations or 4,
    )
    result = await sub.run()
    return result

@app.get("/api/connections")
async def get_connections_endpoint():
    """Returns Hermes multi-connection roles and fallback provider."""
    return {
        "active_provider": config.active_provider,
        "fallback_provider": model_router.fallback_provider,
        "roles": model_router.connection_roles,
    }

@app.post("/api/connections/role")
async def set_connection_role_endpoint(req: ConnectionRoleRequest):
    """Configures connection role mapping (primary, subagents, fast, reasoning)."""
    model_router.set_connection_role(req.role, req.provider, req.model)
    return {
        "status": "updated",
        "role": req.role,
        "provider": req.provider,
        "model": req.model,
    }

@app.get("/api/tools")
def get_tools_catalog_endpoint():
    """Returns all active tools categorized by toolset with parameter schemas."""
    from tools.catalog import TOOLSET_REGISTRY
    tool_list = []
    for ts_enum, tools in TOOLSET_REGISTRY.items():
        ts_name = ts_enum.value if hasattr(ts_enum, "value") else str(ts_enum)
        category_name = ts_name.replace("_", " ").title()
        for tool in tools:
            fn = tool.get("function", {})
            name = fn.get("name", "")
            desc = fn.get("description", "")
            params = fn.get("parameters", {}).get("properties", {})
            param_names = list(params.keys())
            sample_args = ", ".join([f'{k}="..."' for k in param_names[:2]])
            tool_list.append({
                "id": f"tool_{name}",
                "name": name,
                "category": category_name,
                "toolset": ts_name,
                "description": desc,
                "status": "active",
                "parametersCount": len(params),
                "sampleCall": f"{name}({sample_args})",
                "parameters": params,
            })

    # Include dynamic Extension Capsule tools
    try:
        from extensions.extension_manager import extension_manager
        for ext in extension_manager._extensions.values():
            if not ext.enabled:
                continue
            cat_name = f"Extension: {ext.name}"
            for tool in ext.tools:
                fn = tool.get("function", {})
                name = fn.get("name", "")
                desc = fn.get("description", "")
                params = fn.get("parameters", {}).get("properties", {})
                param_names = list(params.keys())
                sample_args = ", ".join([f'{k}="..."' for k in param_names[:2]])
                tool_list.append({
                    "id": f"ext_tool_{name}",
                    "name": name,
                    "category": cat_name,
                    "toolset": f"ext_{ext.id}",
                    "description": desc,
                    "status": "active",
                    "parametersCount": len(params),
                    "sampleCall": f"{name}({sample_args})",
                    "parameters": params,
                })
    except Exception as ext_err:
        logger.debug(f"Extension tools in catalog omitted: {ext_err}")

    return {"tools": tool_list, "total": len(tool_list)}

@app.get("/api/extensions")
def get_extensions_endpoint():
    """Returns all discovered extension capsules, their metadata, intent triggers, and tools."""
    from extensions.extension_manager import extension_manager
    exts = extension_manager.list_extensions()
    return {"status": "success", "count": len(exts), "extensions": exts}

@app.get("/api/mcp/search")
async def search_mcp_registries_endpoint(
    query: str = Query(default="", description="Search query keyword or capability"),
    registry: str = Query(default="all", description="Registry filter: all, official, smithery, glama"),
    limit: int = Query(default=10, description="Max results to return"),
):
    """Searches Smithery, Glama, and official MCP registries for community and standard servers."""
    from tools.mcp_client import mcp_client
    return await mcp_client.search_registries(query=query, registry=registry, limit=limit)

@app.get("/api/mcp/inspect")
async def inspect_mcp_server_endpoint(
    server_id: str = Query(..., description="MCP server ID or package name to inspect"),
):
    """Retrieves full manifest, required environment variables, and install commands for an MCP server."""
    from tools.mcp_client import mcp_client
    return mcp_client.inspect_server(server_id)

@app.get("/api/mcp/servers")
async def list_mcp_servers_endpoint():
    """Lists all mounted and active MCP servers in MaxIM."""
    from tools.mcp_client import mcp_client
    servers = mcp_client.list_installed_servers()
    return {"status": "success", "servers": servers, "count": len(servers)}

@app.post("/api/mcp/install")
async def install_mcp_server_endpoint(req: MCPRegisterRequest):
    """Mounts and registers an MCP server with SQLite persistence."""
    from tools.mcp_client import mcp_client
    cfg = mcp_client.register_server(
        name=req.name,
        transport=req.transport,
        command=req.command,
        args=req.args,
        url=req.url,
        env=req.env,
        description=req.description,
        source_registry=req.source_registry or "custom",
    )
    return {"status": "mounted", "server": cfg.model_dump()}

@app.post("/api/mcp/register")
async def register_mcp_endpoint(req: MCPRegisterRequest):
    """Registers an external MCP server."""
    from tools.mcp_client import mcp_client
    cfg = mcp_client.register_server(
        name=req.name,
        transport=req.transport,
        command=req.command,
        args=req.args,
        url=req.url,
        env=req.env,
        description=req.description,
        source_registry=req.source_registry or "custom",
    )
    return {"status": "registered", "server": req.name, "config": cfg.model_dump()}

@app.delete("/api/mcp/servers/{server_name}")
async def remove_mcp_server_endpoint(server_name: str):
    """Unmounts and removes a registered MCP server."""
    from tools.mcp_client import mcp_client
    success = mcp_client.remove_server(server_name)
    return {"status": "removed" if success else "not_found", "server_name": server_name}

@app.post("/api/mcp/call")
async def call_mcp_tool_endpoint(req: MCPCallRequest):
    """Executes a tool on a connected MCP server."""
    from tools.mcp_client import mcp_client
    return await mcp_client.call_tool(
        server_name=req.server_name,
        tool_name=req.tool_name,
        arguments=req.arguments,
    )

@app.get("/api/watchdog/jobs")
async def get_watchdog_jobs_endpoint():
    """Lists registered autonomous watchdog heartbeat routines."""
    from cron_engine import watchdog_scheduler
    return {"jobs": list(watchdog_scheduler.jobs.values())}

@app.post("/api/watchdog/trigger")
async def trigger_watchdog_endpoint(req: WatchdogTriggerRequest):
    """Manually triggers a watchdog scheduled routine."""
    from cron_engine import watchdog_scheduler
    res = await watchdog_scheduler.execute_job(req.job_name)
    return res

# =============================================================================
# PHASE 9: ZYLOS FIVE-LAYER MEMORY & CONTEXT SAFEGUARD ENDPOINTS
# =============================================================================

@app.get("/api/memory/five-layers")
async def get_five_layers_endpoint(session_id: str = "default_session", query: Optional[str] = None):
    """Returns real-time diagnostic snapshot of all 5 Zylos memory layers."""
    from five_layer_memory import five_layer_memory
    return five_layer_memory.get_all_layers(session_id=session_id, query=query)

@app.post("/api/memory/search")
async def search_memory_endpoint(req: MemorySearchRequest):
    """Executes BM25 ranked full-text search across SQLite FTS5 and Obsidian vault."""
    from five_layer_memory import five_layer_memory
    results = five_layer_memory.search_all_layers(query=req.query, limit=req.limit or 10)
    return {"query": req.query, "results": results}

@app.post("/api/memory/compact")
async def compact_memory_endpoint(req: MemoryCompactRequest):
    """Triggers Zylos 75% Context Safeguard compaction to prevent context degradation."""
    from five_layer_memory import five_layer_memory
    res = five_layer_memory.execute_safeguard_compaction(session_id=req.session_id, reason=req.reason or "Manual compaction")
    return res

@app.get("/api/memory/safeguard/status")
async def get_safeguard_status_endpoint(session_id: str = "default_session"):
    """Returns token capacity ratio, threshold, and safeguard status."""
    from five_layer_memory import five_layer_memory
    return five_layer_memory.check_context_safeguard(session_id=session_id)

# =============================================================================
# PHASE 10: AGENT REACH NATIVE INTERNET GATEWAY ENDPOINTS
# =============================================================================

@app.get("/api/reach/doctor")
async def reach_doctor_endpoint():
    """Runs automated health check and latency diagnostics across all reach channels."""
    from tools.reach_tool import agent_reach
    return await agent_reach.reach_doctor()

@app.post("/api/reach/read")
async def reach_read_endpoint(req: ReachReadRequest):
    """Fetches clean Markdown from any public URL using Jina Reader or direct fallback."""
    from tools.reach_tool import agent_reach
    res = await agent_reach.read_web_page(url=req.url, max_chars=req.max_chars or 10000)
    return res

@app.post("/api/reach/search")
async def reach_search_endpoint(req: ReachSearchRequest):
    """Performs multi-engine web search via DuckDuckGo without requiring API keys."""
    from tools.reach_tool import agent_reach
    res = await agent_reach.web_search(query=req.query, max_results=req.max_results or 6)
    return res

@app.post("/api/reach/github")
async def reach_github_endpoint(req: ReachGitHubRequest):
    """Inspects GitHub repository metadata, stars, activity, or full README."""
    from tools.reach_tool import agent_reach
    res = await agent_reach.github_reach(repo=req.repo, action=req.action or "info")
    return res

@app.get("/api/reach/community")
async def reach_community_endpoint(source: str = Query("v2ex", description="Source: 'v2ex' or 'hackernews'"), limit: int = Query(6, description="Max discussions")):
    """Fetches trending developer discussions and hot topics."""
    from tools.reach_tool import agent_reach
    res = await agent_reach.community_reach(source=source, limit=limit)
    return res

# =============================================================================
# PHASE 11: LOBEHUB CHIEF AGENT OPERATOR & MULTI-AGENT COLLABORATION ENDPOINTS
# =============================================================================

@app.get("/api/operator/team")
async def get_operator_team_endpoint():
    """Lists all hired agent teammates in the Chief Agent Operator's team roster."""
    from chief_operator import agent_operator
    members = agent_operator.list_team()
    return {"team": [m.model_dump() for m in members], "total": len(members)}

@app.post("/api/operator/hire")
async def hire_operator_agent_endpoint(req: HireAgentRequest):
    """Hires a new specialized agent teammate into the persistent team roster."""
    from chief_operator import agent_operator
    m = agent_operator.hire_agent(
        name=req.name,
        role=req.role,
        persona=req.persona,
        avatar=req.avatar or "Sparkles",
        toolsets=req.toolsets or ["vault"],
        skills=req.skills,
        category=req.category,
        provider=req.provider,
        model=req.model,
    )
    return m.model_dump()

@app.delete("/api/operator/team/{agent_id}")
async def fire_operator_agent_endpoint(agent_id: str):
    """Removes an agent from the active team roster."""
    from chief_operator import agent_operator
    success = agent_operator.fire_agent(agent_id)
    return {"status": "success" if success else "not_found", "agent_id": agent_id}

@app.get("/api/operator/groups")
async def get_operator_groups_endpoint():
    """Lists all multi-agent collaboration groups."""
    from chief_operator import agent_operator
    groups = agent_operator.list_groups()
    return {"groups": [g.model_dump() for g in groups]}

@app.get("/api/operator/groups/{group_id}")
async def get_single_operator_group_endpoint(group_id: str):
    """Retrieves metadata and member roster for a specific collaboration group."""
    from chief_operator import agent_operator
    group = agent_operator.get_group(group_id)
    if not group:
        return {"error": f"Group '{group_id}' not found."}
    members = [agent_operator.get_agent(m_id).model_dump() for m_id in group.member_ids if agent_operator.get_agent(m_id)]
    res = group.model_dump()
    res["members"] = members
    return res

@app.post("/api/operator/groups")
async def create_operator_group_endpoint(req: CreateGroupRequest):
    """Creates a new multi-agent collaboration group."""
    from chief_operator import agent_operator
    g = agent_operator.create_group(
        name=req.name,
        description=req.description,
        member_ids=req.member_ids,
        category=req.category,
        topic=req.topic,
    )
    return g.model_dump()

@app.post("/api/operator/groups/assemble")
async def assemble_operator_group_endpoint(req: AssembleDynamicGroupRequest):
    """Dynamically assembles an ad-hoc collaboration group on demand based on topic or desktop window context."""
    from chief_operator import agent_operator
    res = await agent_operator.assemble_dynamic_group(
        topic=req.topic,
        group_name=req.group_name,
        skills_requested=req.skills_requested,
        desktop_context=req.desktop_context,
        use_active_window=req.use_active_window,
    )
    return res

@app.delete("/api/operator/groups/{group_id}")
async def delete_operator_group_endpoint(group_id: str):
    """Deletes an ad-hoc collaboration group and its message history."""
    from chief_operator import agent_operator
    success = agent_operator.delete_group(group_id)
    return {"status": "success" if success else "not_found", "group_id": group_id}

@app.get("/api/operator/groups/{group_id}/messages")
async def get_group_messages_endpoint(group_id: str, limit: int = 50):
    """Retrieves conversation history of an agent collaboration group."""
    from chief_operator import agent_operator
    messages = agent_operator.get_group_messages(group_id=group_id, limit=limit)
    return {"group_id": group_id, "messages": messages}

@app.post("/api/operator/groups/{group_id}/chat")
async def run_group_chat_endpoint(group_id: str, req: GroupChatRequest):
    """Dispatches a user prompt to a multi-agent collaboration group for iterative turn-taking."""
    from chief_operator import agent_operator
    res = await agent_operator.run_group_chat(
        group_id=group_id,
        user_message=req.message,
        rounds=req.rounds or 1,
    )
    return res

@app.post("/api/operator/groups/{group_id}/dispatch")
async def dispatch_group_task_endpoint(group_id: str, req: DispatchGroupTaskRequest):
    """MaxIM Chief Conductor enters group, posts directive brief, runs turns, and delivers sign-off."""
    from chief_operator import agent_operator
    res = await agent_operator.dispatch_group_task(
        group_id=group_id,
        task_prompt=req.task_prompt,
        target_agent_ids=req.target_agent_ids,
        rounds=req.rounds or 1,
    )
    return res

@app.post("/api/operator/orchestrate")
async def orchestrate_objective_endpoint(req: OrchestrateObjectiveRequest):
    """Autonomous MaxIM Conductor: selects category group, dispatches mission, and archives to vault."""
    from chief_operator import agent_operator
    res = await agent_operator.orchestrate_objective(
        objective=req.objective,
        preferred_category=req.preferred_category,
        rounds=req.rounds or 1,
        save_to_vault=req.save_to_vault if req.save_to_vault is not None else True,
    )
    return res

@app.post("/api/operator/cross-group-handoff")
async def cross_group_handoff_endpoint(req: CrossGroupHandoffRequest):
    """MaxIM bridges work from one specialized group channel to another."""
    from chief_operator import agent_operator
    res = await agent_operator.cross_group_handoff(
        source_group_id=req.source_group_id,
        target_group_id=req.target_group_id,
        deliverable_summary=req.deliverable_summary,
        next_step_instruction=req.next_step_instruction,
        rounds=req.rounds or 1,
    )
    return res

@app.post("/api/operator/shifts/execute")
async def execute_shift_endpoint(req: ExecuteShiftRequest):
    """Executes an autonomous background shift for a specialized agent and writes to vault."""
    from chief_operator import agent_operator
    report = await agent_operator.execute_shift(
        agent_id=req.agent_id,
        task=req.task,
        save_to_vault=req.save_to_vault if req.save_to_vault is not None else True,
    )
    return report.model_dump()

@app.get("/api/operator/reports")
async def get_operator_reports_endpoint(limit: int = 20):
    """Lists recent autonomous shift reports from the team."""
    from chief_operator import agent_operator
    reports = agent_operator.list_reports(limit=limit)
    return {"reports": [r.model_dump() for r in reports]}

# =============================================================================
# PHASE 12: PROACTIVE SITUATIONAL INITIATIVE & REAL-TIME VOICE ENDPOINTS
# =============================================================================

@app.get("/api/proactive/snapshot")
async def get_proactive_snapshot_endpoint(session_id: str = "default_session"):
    """Returns real-time situational snapshot of active window, TELOS, and cadence."""
    from proactive_agent import proactive_agent
    return proactive_agent.get_situation_snapshot(session_id=session_id)

@app.post("/api/proactive/evaluate")
async def evaluate_proactive_endpoint(req: ProactiveEvaluateRequest):
    """Evaluates whether to proactively interject with a non-robotic thought or question."""
    from proactive_agent import proactive_agent
    res = await proactive_agent.evaluate_initiative(
        session_id=req.session_id or "default_session",
        force=req.force or False,
    )
    return res

@app.get("/api/proactive/settings")
async def get_proactive_settings_endpoint():
    """Retrieves current proactive initiative sensitivity, auto-speak, and cooldown."""
    from proactive_agent import proactive_agent
    return proactive_agent.get_settings().model_dump()

@app.post("/api/proactive/settings")
async def update_proactive_settings_endpoint(req: ProactiveSettingsRequest):
    """Updates proactive sensitivity mode, auto-speak behavior, or cooldown."""
    from proactive_agent import proactive_agent
    updated = proactive_agent.update_settings(
        mode=req.mode,
        auto_speak=req.auto_speak,
        cooldown_minutes=req.cooldown_minutes,
    )
    return updated.model_dump()

@app.get("/api/proactive/history")
async def get_proactive_history_endpoint(limit: int = 20):
    """Retrieves recent proactive interventions and contextual check-ins."""
    from proactive_agent import proactive_agent
    interventions = proactive_agent.list_interventions(limit=limit)
    return {"interventions": [i.model_dump() for i in interventions]}

# =============================================================================
# AUTONOMOUS OVERNIGHT & IDLE INTELLIGENCE SCOUT ENDPOINTS
# =============================================================================

@app.get("/api/scout/status")
async def get_scout_status_endpoint():
    """Checks idle state, nighttime sleep window, and scout readiness."""
    from idle_scout import idle_scout
    return idle_scout.check_idle_or_sleep_status()

@app.post("/api/scout/trigger")
async def trigger_scout_cycle_endpoint(req: ScoutTriggerRequest):
    """Triggers an autonomous overnight or idle scouting cycle."""
    from idle_scout import idle_scout
    res = await idle_scout.execute_scout_cycle(
        trigger_type=req.trigger_type or "manual",
        force=req.force if req.force is not None else True,
    )
    return res

@app.get("/api/scout/latest")
async def get_latest_scout_report_endpoint():
    """Retrieves the latest overnight intelligence briefing."""
    from idle_scout import idle_scout
    rep = idle_scout.get_latest_report()
    if not rep:
        return {"status": "empty", "message": "No intelligence reports scouted yet."}
    return {"status": "found", "report": rep}

@app.get("/api/scout/reports")
async def list_scout_reports_endpoint(limit: int = 20):
    """Lists historical overnight and idle intelligence briefings."""
    from idle_scout import idle_scout
    reports = idle_scout.list_reports(limit=limit)
    return {"reports": reports}

@app.post("/api/scout/reports/{report_id}/review")
async def review_scout_report_endpoint(report_id: str):
    """Marks a scout briefing as reviewed by the user."""
    from idle_scout import idle_scout
    succ = idle_scout.mark_report_reviewed(report_id)
    return {"status": "success" if succ else "not_found", "report_id": report_id}

@app.get("/api/scout/interests")
async def get_scout_interests_endpoint(limit: int = 20):
    """Lists dynamically tracked user interest topics."""
    from idle_scout import idle_scout
    topics = idle_scout.get_interest_topics(limit=limit)
    return {"topics": [t.model_dump() for t in topics]}

@app.post("/api/scout/interests")
async def add_scout_interest_endpoint(req: AddInterestTopicRequest):
    """Adds or boosts a tracked user interest topic."""
    from idle_scout import idle_scout
    t = idle_scout.add_interest_topic(topic=req.topic, category=req.category or "tech")
    return {"status": "success", "topic": t.model_dump()}

@app.delete("/api/scout/interests/{topic_id}")
async def delete_scout_interest_endpoint(topic_id: int):
    """Removes a topic from interest tracking."""
    from idle_scout import idle_scout
    succ = idle_scout.delete_interest_topic(topic_id)
    return {"status": "success" if succ else "not_found", "topic_id": topic_id}

@app.get("/api/scout/settings")
async def get_scout_settings_endpoint():
    """Retrieves current idle scout configuration."""
    from idle_scout import idle_scout
    return idle_scout.get_settings().model_dump()

@app.post("/api/scout/settings")
async def update_scout_settings_endpoint(req: ScoutSettingsRequest):
    """Updates idle scout schedule and thresholds."""
    from idle_scout import idle_scout
    updated = idle_scout.update_settings(
        enabled=req.enabled,
        idle_threshold_minutes=req.idle_threshold_minutes,
        night_start_hour=req.night_start_hour,
        night_end_hour=req.night_end_hour,
        auto_generate_audio=req.auto_generate_audio,
    )
    return updated.model_dump()

# =============================================================================
# Privacy Guard & Owner Loyalty Protection Endpoints
# =============================================================================

class PrivacySettingsRequest(BaseModel):
    owner_name: Optional[str] = None
    strict_mode: Optional[bool] = None
    redact_file_paths: Optional[bool] = None
    redact_credentials: Optional[bool] = None
    redact_pii: Optional[bool] = None
    block_all_egress_leaks: Optional[bool] = None
    blocked_keywords: Optional[List[str]] = None

class PrivacyCheckRequest(BaseModel):
    query: str
    channel: Optional[str] = "test_check"

@app.get("/api/privacy/status")
async def get_privacy_status_endpoint():
    """Retrieves privacy guard summary, leak protection status, and owner loyalty state."""
    from privacy_guard import privacy_guard
    return privacy_guard.get_status_summary()

@app.get("/api/privacy/settings")
async def get_privacy_settings_endpoint():
    """Retrieves current privacy guard configuration."""
    from privacy_guard import privacy_guard
    return privacy_guard.get_settings().model_dump()

@app.post("/api/privacy/settings")
async def update_privacy_settings_endpoint(req: PrivacySettingsRequest):
    """Updates privacy guard policies, toggles, or blocked keywords."""
    from privacy_guard import privacy_guard
    updated = privacy_guard.update_settings(
        owner_name=req.owner_name,
        strict_mode=req.strict_mode,
        redact_file_paths=req.redact_file_paths,
        redact_credentials=req.redact_credentials,
        redact_pii=req.redact_pii,
        block_all_egress_leaks=req.block_all_egress_leaks,
        blocked_keywords=req.blocked_keywords,
    )
    return updated.model_dump()

@app.get("/api/privacy/audit")
async def get_privacy_audit_endpoint(limit: int = 50):
    """Retrieves recent privacy audit log entries."""
    from privacy_guard import privacy_guard
    logs = privacy_guard.get_audit_logs(limit=limit)
    return {"audit_logs": [l.model_dump() for l in logs]}

@app.post("/api/privacy/check")
async def check_privacy_sanitize_endpoint(req: PrivacyCheckRequest):
    """Dry-run test to check how text is sanitized or if it gets blocked."""
    from privacy_guard import privacy_guard
    res = privacy_guard.sanitize_outgoing_query(query=req.query, channel=req.channel or "test_check")
    return res

# =============================================================================
# Language Acquisition & Dialect Learning Endpoints (Bangla, Chakma, etc.)
# =============================================================================

class LearnPhraseRequest(BaseModel):
    word_or_phrase: str
    language: str = "bangla"
    meaning: str
    phonetic_script: Optional[str] = None
    usage_example: Optional[str] = None
    confidence: Optional[float] = 0.85
    source: Optional[str] = "user_taught"

@app.get("/api/languages/vocabulary")
async def get_language_vocabulary_endpoint(language: Optional[str] = None, limit: int = 100):
    """Retrieves learned vocabulary optionally filtered by language (bangla, chakma, etc.)."""
    from language_learner import language_learner
    vocab = language_learner.get_vocabulary(language=language, limit=limit)
    stats = language_learner.get_learning_stats()
    return {
        "vocabulary": [v.model_dump() for v in vocab],
        "stats": stats,
    }

@app.post("/api/languages/learn")
async def learn_language_phrase_endpoint(req: LearnPhraseRequest):
    """Explicitly teaches or updates a local language phrase or greeting."""
    from language_learner import language_learner
    phrase = language_learner.learn_phrase(
        word_or_phrase=req.word_or_phrase,
        language=req.language,
        meaning=req.meaning,
        phonetic_script=req.phonetic_script,
        usage_example=req.usage_example,
        confidence=req.confidence or 0.85,
        source=req.source or "user_taught",
    )
    language_learner.sync_to_vault()
    return {"status": "learned", "phrase": phrase.model_dump()}

@app.get("/api/languages/stats")
async def get_language_stats_endpoint():
    """Retrieves language acquisition progress metrics."""
    from language_learner import language_learner
    return language_learner.get_learning_stats()

@app.post("/api/languages/sync-vault")
async def sync_languages_to_vault_endpoint():
    """Exports learned language knowledge to Obsidian vault note."""
    from language_learner import language_learner
    note = language_learner.sync_to_vault()
    return {"status": "synced", "path": str(note) if note else None}

# =============================================================================
# OpenJarvis Hardware Telemetry & Cost Governor Endpoints
# =============================================================================

class UpdateGovernorSettingsRequest(BaseModel):
    daily_budget_usd: Optional[float] = None
    hard_cap_enabled: Optional[bool] = None
    auto_downgrade_to_local: Optional[bool] = None
    prefer_local_first: Optional[bool] = None
    vram_headroom_threshold_percent: Optional[float] = None

@app.get("/api/hardware/telemetry")
async def get_hardware_telemetry_endpoint():
    """Returns real-time host hardware telemetry (CPU, RAM, GPU/VRAM, temperatures, Ollama models)."""
    from hardware_governor import hardware_governor
    telemetry = hardware_governor.get_hardware_telemetry()
    return telemetry.model_dump()

@app.get("/api/hardware/governor")
async def get_cost_governor_summary_endpoint():
    """Returns current daily token spend, budget status, cost savings, and governor configuration."""
    from hardware_governor import hardware_governor
    summary = hardware_governor.get_daily_cost_summary()
    settings = hardware_governor.get_settings()
    return {
        "summary": summary,
        "settings": settings.model_dump(),
    }

@app.post("/api/hardware/governor/settings")
async def update_cost_governor_settings_endpoint(req: UpdateGovernorSettingsRequest):
    """Updates budget hard caps and local-first routing preferences."""
    from hardware_governor import hardware_governor
    updated = hardware_governor.update_settings(
        daily_budget_usd=req.daily_budget_usd,
        hard_cap_enabled=req.hard_cap_enabled,
        auto_downgrade_to_local=req.auto_downgrade_to_local,
        prefer_local_first=req.prefer_local_first,
        vram_headroom_threshold_percent=req.vram_headroom_threshold_percent,
    )
    return {"status": "updated", "settings": updated.model_dump()}

@app.get("/api/hardware/cost-ledger")
async def get_cost_ledger_endpoint(limit: int = 50):
    """Retrieves recent cost ledger execution logs."""
    from hardware_governor import hardware_governor
    records = hardware_governor.get_recent_ledger(limit=limit)
    return {"ledger": [r.model_dump() for r in records]}

@app.get("/api/hardware/pricing")
async def get_hardware_pricing_catalog_endpoint():
    """Returns the comprehensive provider pricing catalog, per-token rates, and sub-cent precision rules."""
    from hardware_governor import HardwareGovernorEngine
    return HardwareGovernorEngine.get_pricing_catalog()

# =============================================================================
# Phase 14: Mark-LIV Functional OS Automation & Action Loop Endpoints
# =============================================================================

class OSActionRequest(BaseModel):
    action: str
    target: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    text: Optional[str] = None
    keys: Optional[List[str]] = None
    session_id: Optional[str] = "default_session"

class OSLaunchRequest(BaseModel):
    command: str
    args: Optional[List[str]] = None
    working_dir: Optional[str] = None

@app.get("/api/os/windows")
async def list_windows_endpoint(visible_only: bool = True):
    """Enumerates open application windows with geometry and HWNDs."""
    from mark_liv import mark_liv_engine
    windows = mark_liv_engine.list_windows(visible_only=visible_only)
    active = mark_liv_engine.get_active_window()
    return {
        "windows": [w.model_dump() for w in windows],
        "active_window": active.model_dump() if active else None,
        "count": len(windows),
    }

@app.post("/api/os/action")
async def execute_os_action_endpoint(req: OSActionRequest):
    """Executes a direct OS automation action (click, type, hotkey, window lifecycle)."""
    from mark_liv import mark_liv_engine
    res = mark_liv_engine.execute_action_step(
        action=req.action,
        target=req.target,
        x=req.x,
        y=req.y,
        text=req.text,
        keys=req.keys,
        session_id=req.session_id or "default_session",
    )
    return res

@app.post("/api/os/launch")
async def launch_os_app_endpoint(req: OSLaunchRequest):
    """Launches an application or executable in the background."""
    from mark_liv import mark_liv_engine
    res = mark_liv_engine.launch_application(
        command_or_path=req.command,
        args=req.args,
        working_dir=req.working_dir,
    )
    return res

@app.get("/api/os/processes")
async def list_processes_endpoint(filter_name: Optional[str] = None, limit: int = 30):
    """Lists running system processes with memory footprint."""
    from mark_liv import mark_liv_engine
    procs = mark_liv_engine.list_processes(filter_name=filter_name, limit=limit)
    return {"processes": procs, "count": len(procs)}

@app.get("/api/os/history")
async def get_os_action_history_endpoint(limit: int = 50):
    """Retrieves recent OS automation execution receipts."""
    from mark_liv import mark_liv_engine
    actions = mark_liv_engine.get_recent_actions(limit=limit)
    return {"actions": [a.model_dump() for a in actions]}

# =============================================================================
# Phase 15: ZhiGui UI Second Brain & Autonomous Learning Loop Endpoints
# =============================================================================

class CrystallizeSkillRequest(BaseModel):
    name: str
    description: str
    steps: List[Dict[str, Any]]
    trigger_keywords: Optional[List[str]] = None
    preconditions: Optional[str] = None
    sync_vault: Optional[bool] = True

class ErrorReflexionRequest(BaseModel):
    failed_tool: str
    error_message: str
    root_cause: str
    corrective_rule: str
    session_id: Optional[str] = "default_session"

@app.get("/api/skills")
async def list_skills_endpoint(limit: int = 50):
    """Lists all crystallized skills with execution counters and steps."""
    from second_brain import second_brain_engine
    skills = second_brain_engine.list_skills(limit=limit)
    return {"skills": [s.model_dump() for s in skills], "count": len(skills)}

@app.post("/api/skills/crystallize")
async def crystallize_skill_endpoint(req: CrystallizeSkillRequest):
    """Crystallizes a validated multi-step action pattern into the Second Brain and Obsidian vault."""
    from second_brain import second_brain_engine
    skill = second_brain_engine.crystallize_skill(
        name=req.name,
        description=req.description,
        steps=req.steps,
        trigger_keywords=req.trigger_keywords,
        preconditions=req.preconditions,
        sync_vault=req.sync_vault if req.sync_vault is not None else True,
    )
    second_brain_engine.sync_skills_moc()
    return {"status": "crystallized", "skill": skill.model_dump()}

@app.get("/api/skills/reflexions")
async def list_reflexions_endpoint(limit: int = 30):
    """Lists recent error reflexion corrective rules."""
    from second_brain import second_brain_engine
    reflexions = second_brain_engine.list_reflexions(limit=limit)
    return {"reflexions": [r.model_dump() for r in reflexions], "count": len(reflexions)}

@app.post("/api/skills/reflexions")
async def record_reflexion_endpoint(req: ErrorReflexionRequest):
    """Registers an execution pitfall and corrective rule."""
    from second_brain import second_brain_engine
    ref = second_brain_engine.record_error_reflexion(
        failed_tool=req.failed_tool,
        error_message=req.error_message,
        root_cause=req.root_cause,
        corrective_rule=req.corrective_rule,
        session_id=req.session_id or "default_session",
    )
    return {"status": "recorded", "reflexion": ref.model_dump()}

@app.post("/api/skills/sync-vault")
async def sync_skills_vault_endpoint():
    """Generates and updates Master Skills Map of Content in Obsidian."""
    from second_brain import second_brain_engine
    moc = second_brain_engine.sync_skills_moc()
    return {"status": "synced", "moc_path": str(moc)}

# =============================================================================
# Phase 16: 10xProductivity Workstation & QwenPaw Sandboxed Guard Endpoints
# =============================================================================

class SandboxRunRequest(BaseModel):
    command: str
    cwd: Optional[str] = None
    timeout_seconds: Optional[int] = 15

class SandboxAuditRequest(BaseModel):
    command: str
    cwd: Optional[str] = None

class WorkstationScaffoldRequest(BaseModel):
    project_type: str
    target_dir: str
    project_name: str
    description: Optional[str] = "MaxIM Workstation Generated Component"

class WorkstationCommitRequest(BaseModel):
    message: str
    files: Optional[List[str]] = None
    repo_dir: Optional[str] = None

class WorkstationSnippetRequest(BaseModel):
    title: str
    language: str
    code: str
    tags: Optional[List[str]] = None
    description: Optional[str] = None

@app.post("/api/sandbox/run")
async def run_sandboxed_command_endpoint(req: SandboxRunRequest):
    """Executes a shell command inside the QwenPaw pre-audited secure sandbox."""
    from workstation_sandbox import workstation_sandbox
    res = workstation_sandbox.execute_sandboxed_command(
        command=req.command,
        cwd=req.cwd,
        timeout_seconds=req.timeout_seconds or 15
    )
    return res.model_dump()

@app.post("/api/sandbox/audit")
async def audit_command_endpoint(req: SandboxAuditRequest):
    """Audits a command for safety risks without executing it."""
    from workstation_sandbox import workstation_sandbox
    audit = workstation_sandbox.audit_command(command=req.command, working_dir=req.cwd)
    return audit.model_dump()

@app.get("/api/sandbox/audit-logs")
async def list_sandbox_audit_logs_endpoint(limit: int = 25):
    """Retrieves recent sandbox execution audits and blocked attempts."""
    from workstation_sandbox import workstation_sandbox
    logs = workstation_sandbox.list_audit_logs(limit=limit)
    return {"logs": logs, "count": len(logs)}

@app.post("/api/workstation/scaffold")
async def scaffold_project_endpoint(req: WorkstationScaffoldRequest):
    """Generates project scaffold boilerplate for developer productivity."""
    from workstation_sandbox import workstation_sandbox
    res = workstation_sandbox.scaffold_project(
        project_type=req.project_type,
        target_dir=req.target_dir,
        project_name=req.project_name,
        description=req.description or "MaxIM Workstation Generated Component"
    )
    return res

@app.get("/api/workstation/git-status")
async def get_git_status_endpoint(repo_dir: Optional[str] = None):
    """Inspects Git working tree hygiene, untracked files, and conventional readiness."""
    from workstation_sandbox import workstation_sandbox
    status = workstation_sandbox.get_git_hygiene(repo_dir=repo_dir)
    return status.model_dump()

@app.post("/api/workstation/commit")
async def create_atomic_commit_endpoint(req: WorkstationCommitRequest):
    """Creates a conventional atomic commit after staging changes."""
    from workstation_sandbox import workstation_sandbox
    res = workstation_sandbox.create_atomic_commit(
        message=req.message,
        files=req.files,
        repo_dir=req.repo_dir
    )
    return res

@app.get("/api/workstation/snippets")
async def list_snippets_endpoint(language: Optional[str] = None, tag: Optional[str] = None):
    """Lists verified developer snippets and recipes."""
    from workstation_sandbox import workstation_sandbox
    snippets = workstation_sandbox.list_snippets(language=language, tag=tag)
    return {"snippets": [s.model_dump() for s in snippets], "count": len(snippets)}

@app.post("/api/workstation/snippets")
async def save_snippet_endpoint(req: WorkstationSnippetRequest):
    """Saves a code snippet or recipe to the Workstation registry."""
    from workstation_sandbox import workstation_sandbox
    snippet = workstation_sandbox.save_snippet(
        title=req.title,
        language=req.language,
        code=req.code,
        tags=req.tags,
        description=req.description
    )
    return snippet.model_dump()

# =============================================================================
# OpenHuman Innovations: Session Todos & TokenJuice Compression Endpoints
# =============================================================================

class CreateTodoRequest(BaseModel):
    session_id: Optional[str] = "default_session"
    task_description: str
    step_order: Optional[int] = None

class UpdateTodoRequest(BaseModel):
    status: str
    result_summary: Optional[str] = None

@app.get("/api/todos")
async def list_session_todos_endpoint(session_id: str = "default_session", status: Optional[str] = None):
    """Lists persistent goals and todo items for the specified session."""
    from session_todos import session_todos
    todos = session_todos.list_todos(session_id=session_id, status=status)
    return {"todos": [t.model_dump() for t in todos], "count": len(todos)}

@app.post("/api/todos")
async def create_session_todo_endpoint(req: CreateTodoRequest):
    """Creates a new actionable sub-goal in the session todo ledger."""
    from session_todos import session_todos
    todo = session_todos.add_todo(
        session_id=req.session_id or "default_session",
        task_description=req.task_description,
        step_order=req.step_order
    )
    return todo.model_dump()

@app.patch("/api/todos/{todo_id}")
async def update_session_todo_endpoint(todo_id: int, req: UpdateTodoRequest):
    """Updates the status and result of a session todo item."""
    from session_todos import session_todos
    updated = session_todos.update_todo(
        todo_id=todo_id,
        status=req.status,
        result_summary=req.result_summary
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Todo not found")
    return updated.model_dump()

@app.delete("/api/todos/{todo_id}")
async def delete_session_todo_endpoint(todo_id: int):
    """Deletes a session todo item."""
    from session_todos import session_todos
    succ = session_todos.delete_todo(todo_id=todo_id)
    return {"success": succ}

@app.get("/api/tokenjuice/stats")
async def get_token_juice_stats_endpoint():
    """Retrieves real-time token savings and compression ratio metrics from TokenJuice."""
    from token_juice import token_juice
    return token_juice.get_stats()

# =============================================================================
# PHASE 18: HIGH-DPI HARDWARE DISPATCHERS & MOBILE TELEKINESIS (ADB BRIDGE)
# =============================================================================

class VolumeAdjustRequest(BaseModel):
    action: str = Field("up", description="'up', 'down', or 'mute'")
    steps: int = Field(2, ge=1, le=50)

class BrightnessSetRequest(BaseModel):
    level_percent: int = Field(50, ge=0, le=100)

class MobileTapRequest(BaseModel):
    x: int
    y: int
    device_id: Optional[str] = None

class MobileLaunchRequest(BaseModel):
    package_name: str
    device_id: Optional[str] = None

@app.post("/api/hardware/volume")
async def adjust_volume_endpoint(req: VolumeAdjustRequest):
    """Nudges or mutes master system audio volume."""
    from hardware_governor import hardware_governor
    return hardware_governor.adjust_master_volume(action=req.action, steps=req.steps)

@app.get("/api/hardware/brightness")
async def get_brightness_endpoint():
    """Reads primary display brightness percentage via Windows WMI."""
    from hardware_governor import hardware_governor
    return hardware_governor.get_screen_brightness()

@app.post("/api/hardware/brightness")
async def set_brightness_endpoint(req: BrightnessSetRequest):
    """Sets display brightness (0-100) via Windows WMI."""
    from hardware_governor import hardware_governor
    return hardware_governor.set_screen_brightness(level_percent=req.level_percent)

@app.get("/api/hardware/default-browser")
async def get_default_browser_endpoint():
    """Resolves the user's primary default browser via Windows UserChoice registry keys."""
    from hardware_governor import hardware_governor
    return hardware_governor.get_default_browser()

@app.get("/api/hardware/wifi-status")
async def get_wifi_status_endpoint():
    """Retrieves active Wi-Fi adapter connection state and telemetry."""
    from hardware_governor import hardware_governor
    return hardware_governor.get_wifi_status()

@app.get("/api/mobile/devices")
async def get_mobile_devices_endpoint():
    """Lists connected Android mobile devices or emulators via ADB."""
    from tools.adb_tool import adb_bridge
    return adb_bridge.get_devices()

@app.get("/api/mobile/battery")
async def get_mobile_battery_endpoint(device_id: Optional[str] = None):
    """Reads mobile device battery percentage and health."""
    from tools.adb_tool import adb_bridge
    return adb_bridge.get_battery(device_id=device_id)

@app.post("/api/mobile/tap")
async def mobile_tap_endpoint(req: MobileTapRequest):
    """Injects coordinate tap on connected mobile screen."""
    from tools.adb_tool import adb_bridge
    return adb_bridge.tap(x=req.x, y=req.y, device_id=req.device_id)

@app.post("/api/mobile/launch")
async def mobile_launch_endpoint(req: MobileLaunchRequest):
    """Launches an application package on connected mobile device."""
    from tools.adb_tool import adb_bridge
    return adb_bridge.launch_app(package_name=req.package_name, device_id=req.device_id)

# ==================== HINDSIGHT EPISTEMIC MEMORY ENDPOINTS ====================

@app.post("/api/memory/retain")
async def retain_memory_endpoint(req: RetainMemoryRequest):
    """
    Hindsight Retain Primitive: Stores observation/fact/preference with epistemic provenance.
    """
    res = five_layer_memory.retain(
        content=req.content,
        category=req.category or "observation",
        source=req.source or "api",
        metadata=req.metadata,
        session_id=req.session_id or "default_session",
    )
    return res

@app.post("/api/memory/recall")
async def recall_memory_endpoint(req: RecallMemoryRequest):
    """
    Hindsight Recall Primitive: Hybrid search across mental models, observations, and vault notes.
    """
    res = five_layer_memory.recall(
        query=req.query,
        top_k=req.top_k or 5,
        include_mental_models=req.include_mental_models if req.include_mental_models is not None else True,
        session_id=req.session_id or "default_session",
    )
    return res

@app.post("/api/memory/reflect")
async def reflect_memory_endpoint(req: ReflectMemoryRequest):
    """
    Hindsight Reflect Primitive: Runs epistemic reflection pass to synthesize mental models.
    """
    res = five_layer_memory.reflect(
        topic=req.topic or "general",
        session_id=req.session_id or "default_session",
    )
    return res

@app.get("/api/memory/mental-models")
async def get_mental_models_endpoint(min_confidence: float = 0.0, limit: int = 50):
    """
    Retrieves active synthesized mental models and user behavioral dispositions.
    """
    from mental_models import mental_models
    models = mental_models.get_all(min_confidence=min_confidence, limit=limit)
    return {
        "status": "success",
        "mental_models": [m.to_dict() for m in models],
        "count": len(models),
    }

@app.patch("/api/memory/mental-models/{model_id}")
async def patch_mental_model_endpoint(model_id: str, req: MentalModelPatchRequest):
    """
    Updates disposition, confidence, or status for an existing mental model.
    """
    from mental_models import mental_models
    updated = mental_models.update_model(
        name_or_id=int(model_id) if model_id.isdigit() else model_id,
        disposition=req.disposition,
        confidence=req.confidence,
        status=req.status,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Mental model '{model_id}' not found.")
    return {
        "status": "updated",
        "mental_model": updated.to_dict(),
    }

# ==================== OPENCLAW MULTI-CHANNEL REMOTE UPLINK ENDPOINTS ====================

@app.post("/api/uplink/webhook")
async def inbound_webhook_endpoint(req: InboundWebhookRequest):
    """
    Ingests inbound message from any external service (Shortcuts, Home Assistant, Termux, Webhook),
    routes through ReAct engine, and optionally delivers the response back.
    """
    from multi_channel_uplink import multi_channel_uplink, InboundMessage, ChannelType
    try:
        ch_enum = ChannelType(req.channel.lower())
    except Exception:
        ch_enum = ChannelType.WEBHOOK

    inbound = InboundMessage(
        channel=ch_enum,
        sender_id=req.sender_id,
        sender_name=req.sender_name or "External Sender",
        content=req.content,
        session_id=req.session_id,
        reply_target=req.reply_target,
        raw_metadata=req.metadata or {},
    )
    res = await multi_channel_uplink.process_inbound(inbound)
    return res

@app.get("/api/uplink/channels")
async def get_channels_endpoint():
    """Returns configuration and traffic telemetry for all communication channels."""
    from multi_channel_uplink import multi_channel_uplink
    return multi_channel_uplink.get_channel_status()

@app.post("/api/uplink/channels")
async def configure_channel_endpoint(req: ChannelConfigRequest):
    """Configures credentials, webhooks, and allowed IDs for a communication channel."""
    from multi_channel_uplink import multi_channel_uplink
    cfg = multi_channel_uplink.configure_channel(
        channel=req.channel,
        enabled=req.enabled if req.enabled is not None else True,
        bot_token=req.bot_token,
        webhook_url=req.webhook_url,
        allowed_ids=req.allowed_ids,
        extra_config=req.extra_config,
    )
    return {"status": "configured", "channel": cfg.model_dump()}

@app.post("/api/uplink/send")
async def send_remote_message_endpoint(req: RemoteSendRequest):
    """Dispatches an outbound notification to a specific channel target."""
    from multi_channel_uplink import multi_channel_uplink
    res = await multi_channel_uplink.send_remote(
        channel=req.channel,
        target=req.target,
        text=req.text,
        title=req.title,
    )
    return res

@app.post("/api/uplink/broadcast")
async def broadcast_remote_message_endpoint(req: RemoteBroadcastRequest):
    """Broadcasts message to all enabled channels."""
    from multi_channel_uplink import multi_channel_uplink
    res = await multi_channel_uplink.broadcast(
        text=req.text,
        title=req.title,
        channels=req.channels,
    )
    return res

@app.get("/api/uplink/inbox")
async def get_uplink_inbox_endpoint(limit: int = 50, channel: Optional[str] = None):
    """Retrieves recent multi-channel conversation logs."""
    from multi_channel_uplink import multi_channel_uplink
    logs = multi_channel_uplink.get_inbox(limit=limit, channel=channel)
    return {"status": "success", "count": len(logs), "inbox": logs}

# ==================== AGENTSHIELD ADVERSARIAL SECURITY ENDPOINTS ====================

@app.post("/api/security/scan")
async def security_scan_endpoint(req: SecurityScanRequest):
    """
    AgentShield Indirect Prompt Injection & Adversarial Payload Scanner.
    Inspects text for role hijacking, instruction overrides, and exfiltration beacons.
    """
    from agent_shield import agent_shield
    report = agent_shield.scan_inbound_content(text=req.text, source=req.source or "api")
    return report.model_dump()

@app.get("/api/security/status")
async def get_security_status_endpoint():
    """Returns AgentShield runtime metrics, threat totals, and quarantine statistics."""
    from agent_shield import agent_shield
    return agent_shield.get_security_metrics()

@app.get("/api/security/settings")
async def get_security_settings_endpoint():
    """Returns AgentShield firewall settings."""
    from agent_shield import agent_shield
    return agent_shield.get_settings()

@app.post("/api/security/settings")
async def update_security_settings_endpoint(req: SecuritySettingsRequest):
    """Updates AgentShield firewall sensitivity mode and tier lockdown toggles."""
    from agent_shield import agent_shield
    updated = agent_shield.update_settings(
        mode=req.mode,
        block_injections=req.block_injections,
        quarantine_untrusted=req.quarantine_untrusted,
        restrict_remote_tier4=req.restrict_remote_tier4,
    )
    return {"status": "updated", "settings": updated}

@app.get("/api/security/audit")
async def get_security_audit_endpoint(limit: int = 50):
    """Retrieves recent threat audit entries from SQLite WAL."""
    from agent_shield import agent_shield
    logs = agent_shield.get_audit_log(limit=limit)
    return {"status": "success", "count": len(logs), "audit_log": logs}

@app.post("/api/security/audit-tool")
async def audit_tool_call_endpoint(req: ToolAuditRequest):
    """Pre-execution validation testing tool permissions and path traversal."""
    from agent_shield import agent_shield
    res = agent_shield.audit_tool_call(
        tool_name=req.tool_name,
        arguments=req.arguments or {},
        session_id=req.session_id or "default_session",
    )
    return res

# =========================================================================
# Browser Agent & Interactive DOM Endpoints (Phase 22 - browser-use)
# =========================================================================

class BrowserNavigateRequest(BaseModel):
    url: str
    session_id: str = "default_session"
    tab_id: Optional[str] = None
    custom_html: Optional[str] = None

class BrowserClickRequest(BaseModel):
    element_index: int
    session_id: str = "default_session"

class BrowserTypeRequest(BaseModel):
    element_index: int
    text: str
    submit: bool = False
    session_id: str = "default_session"

class BrowserSessionActionRequest(BaseModel):
    action: str
    tab_id: Optional[str] = None
    session_id: str = "default_session"

@app.post("/api/browser/navigate")
async def browser_navigate_endpoint(req: BrowserNavigateRequest):
    """Navigates to a URL and returns indexed interactive DOM tree."""
    from browser_agent import browser_agent
    return await browser_agent.navigate(
        url=req.url,
        session_id=req.session_id,
        tab_id=req.tab_id,
        custom_html=req.custom_html,
    )

@app.get("/api/browser/dom")
async def browser_dom_endpoint(
    filter_interactive: bool = True,
    max_elements: int = 80,
    session_id: str = "default_session",
):
    """Retrieves the indexed interactive DOM element tree of the active page."""
    from browser_agent import browser_agent
    return browser_agent.get_dom(
        filter_interactive=filter_interactive,
        max_elements=max_elements,
        session_id=session_id,
    )

@app.post("/api/browser/click")
async def browser_click_endpoint(req: BrowserClickRequest):
    """Clicks an interactive element by its 1-based index from the active DOM tree."""
    from browser_agent import browser_agent
    return await browser_agent.click_element(
        element_index=req.element_index,
        session_id=req.session_id,
    )

@app.post("/api/browser/type")
async def browser_type_endpoint(req: BrowserTypeRequest):
    """Types text into an indexed input or textarea element."""
    from browser_agent import browser_agent
    return await browser_agent.type_element(
        element_index=req.element_index,
        text=req.text,
        submit=req.submit,
        session_id=req.session_id,
    )

@app.get("/api/browser/text")
async def browser_text_endpoint(
    session_id: str = "default_session",
    max_chars: int = 5000,
):
    """Extracts clean readable body text from the active webpage."""
    from browser_agent import browser_agent
    return browser_agent.extract_text(session_id=session_id, max_chars=max_chars)

@app.get("/api/browser/session")
async def browser_session_endpoint(session_id: str = "default_session"):
    """Returns active browser session status and open tabs."""
    from browser_agent import browser_agent
    return browser_agent.manage_session(action="list_tabs", session_id=session_id)

@app.post("/api/browser/tabs")
async def browser_tabs_action_endpoint(req: BrowserSessionActionRequest):
    """Executes tab and history lifecycle actions (new_tab, close_tab, switch_tab, history_back, history_forward)."""
    from browser_agent import browser_agent
    return browser_agent.manage_session(
        action=req.action,
        tab_id=req.tab_id,
        session_id=req.session_id,
    )

@app.get("/api/browser/cdp-status")
async def browser_cdp_status_endpoint():
    """Checks if a local Chrome or Edge browser is attached via CDP port 9222."""
    from browser_agent import browser_agent
    return await browser_agent.check_cdp_status()

# =========================================================================
# File & Directory Organizer Endpoints
# =========================================================================

class DirectoryScanRequest(BaseModel):
    directory_path: str

class DirectoryOrganizeRequest(BaseModel):
    directory_path: str
    dry_run: bool = False

class UndoOrganizationRequest(BaseModel):
    batch_id: str

@app.post("/api/files/scan")
def scan_directory_endpoint(req: DirectoryScanRequest):
    """Scans a directory and returns file counts and planned category moves."""
    from file_organizer import file_organizer
    return file_organizer.scan_directory(directory_path=req.directory_path)

@app.post("/api/files/organize")
def organize_directory_endpoint(req: DirectoryOrganizeRequest):
    """Organizes files into category folders with collision protection and dry-run preview."""
    from file_organizer import file_organizer
    return file_organizer.organize_directory(
        directory_path=req.directory_path,
        dry_run=req.dry_run,
    )

@app.post("/api/files/undo")
def undo_organization_endpoint(req: UndoOrganizationRequest):
    """Reverts an organization batch, restoring moved files to original paths."""
    from file_organizer import file_organizer
    return file_organizer.undo_organization(batch_id=req.batch_id)

@app.get("/api/files/history")
def get_organization_history_endpoint(limit: int = 50):
    """Retrieves file organization transaction batches from SQLite WAL."""
    from file_organizer import file_organizer
    return {"status": "success", "history": file_organizer.get_history(limit=limit)}

# =============================================================================
# OFFICE & SPREADSHEET HARNESS ENDPOINTS (Univer Adaptation)
# =============================================================================

class CreateWorkbookRequest(BaseModel):
    title: str = Field(..., description="Workbook title")
    description: Optional[str] = None
    sheet_names: Optional[List[str]] = None

class EditCellsRequest(BaseModel):
    updates: Dict[str, Any] = Field(..., description="Cell coordinates to values or formulas, e.g. {'A1': 100, 'B1': '=A1*2'}")
    author: Optional[str] = "user"

class RollbackRevisionRequest(BaseModel):
    revision_id: str = Field(..., description="Revision ID to rollback")

class ExportMarkdownRequest(BaseModel):
    range_str: Optional[str] = None
    save_to_vault: Optional[bool] = False
    vault_note_name: Optional[str] = None

class ImportCsvRequest(BaseModel):
    sheet_id: str
    csv_data: str

@app.post("/api/office/workbook")
async def create_workbook_endpoint(req: CreateWorkbookRequest):
    """Creates a new structured spreadsheet workbook."""
    from office_harness import office_harness
    wb = office_harness.create_workbook(
        title=req.title,
        description=req.description,
        initial_sheet_names=req.sheet_names,
    )
    return {"status": "created", "workbook": wb.model_dump()}

@app.get("/api/office/workbooks")
async def list_workbooks_endpoint():
    """Lists all spreadsheet workbooks."""
    from office_harness import office_harness
    wbs = office_harness.list_workbooks()
    return {"status": "success", "workbooks": [wb.model_dump() for wb in wbs]}

@app.get("/api/office/sheet/{sheet_id}")
async def read_sheet_endpoint(sheet_id: str, range_str: Optional[str] = None):
    """Reads spreadsheet cells, formulas, and 2D matrix."""
    from office_harness import office_harness
    return office_harness.read_sheet_grid(sheet_id=sheet_id, range_str=range_str)

@app.post("/api/office/sheet/{sheet_id}/cells")
async def update_cells_endpoint(sheet_id: str, req: EditCellsRequest):
    """Updates cells with Git-style revision tracking and formula evaluation."""
    from office_harness import office_harness
    return office_harness.update_cells(sheet_id=sheet_id, cell_updates=req.updates, author=req.author or "user")

@app.post("/api/office/sheet/{sheet_id}/rollback")
async def rollback_sheet_revision_endpoint(sheet_id: str, req: RollbackRevisionRequest):
    """Rolls back all cell mutations from a specific revision."""
    from office_harness import office_harness
    return office_harness.rollback_revision(sheet_id=sheet_id, revision_id=req.revision_id)

@app.post("/api/office/sheet/{sheet_id}/export-markdown")
async def export_markdown_table_endpoint(sheet_id: str, req: ExportMarkdownRequest):
    """Exports sheet cells to GitHub/Obsidian-compatible Markdown table format."""
    from office_harness import office_harness
    md = office_harness.export_markdown_table(
        sheet_id=sheet_id,
        range_str=req.range_str,
        save_to_vault=req.save_to_vault or False,
        vault_note_name=req.vault_note_name,
    )
    return {"status": "exported", "markdown_table": md}

@app.post("/api/office/import-csv")
async def import_csv_endpoint(req: ImportCsvRequest):
    """Imports tabular CSV data into a sheet."""
    from office_harness import office_harness
    return office_harness.import_csv(sheet_id=req.sheet_id, csv_text_or_path=req.csv_data)

# =============================================================================
# EXECUTIVE WORK GUIDANCE & TASK DIRECTOR ENDPOINTS
# =============================================================================

class DecomposeGoalRequest(BaseModel):
    goal: str = Field(..., description="High-level work objective")
    category: Optional[str] = "general"
    description: Optional[str] = None

class UpdateActionStatusRequest(BaseModel):
    status: str = Field(..., description="completed, in_progress, pending, skipped")
    result_summary: Optional[str] = None

@app.post("/api/work/decompose")
async def decompose_goal_endpoint(req: DecomposeGoalRequest):
    """Decomposes a broad goal into sequential milestones and action checklists."""
    from work_guide import work_guide
    proj = work_guide.decompose_goal(goal=req.goal, category=req.category or "general", description=req.description)
    return {"status": "decomposed", "project": proj.model_dump()}

@app.get("/api/work/next-action")
async def get_next_work_action_endpoint():
    """Retrieves the highest-priority pending task action across active projects."""
    from work_guide import work_guide
    return work_guide.get_next_recommended_action()

@app.get("/api/work/projects")
async def list_work_projects_endpoint(status: Optional[str] = None):
    """Lists active work projects and milestones."""
    from work_guide import work_guide
    projects = work_guide.list_projects(status=status)
    return {"status": "success", "projects": [p.model_dump() for p in projects], "total": len(projects)}

@app.post("/api/work/actions/{action_id}/status")
async def update_action_status_endpoint(action_id: str, req: UpdateActionStatusRequest):
    """Updates action status and automatically cascades progress to milestones."""
    from work_guide import work_guide
    return work_guide.update_action_status(action_id=action_id, status=req.status, result_summary=req.result_summary)

@app.post("/api/work/sync-vault")
async def sync_work_to_vault_endpoint():
    """Exports active work progress tracker to Obsidian vault."""
    from work_guide import work_guide
    path = work_guide.sync_work_to_vault()
    return {"status": "synced", "path": str(path)}

# =============================================================================
# COGNITIVE THINKING MODES & PERSONA ENDPOINTS (Octop Adaptation)
# =============================================================================

class SelectPersonaRequest(BaseModel):
    persona: str = Field(..., description="Persona key or name to activate")

@app.get("/api/personas")
async def list_personas_endpoint():
    """Lists all 16 MBTI cognitive thinking modes and the active persona."""
    from cognitive_personas import cognitive_personas
    return {
        "status": "success",
        "active_persona": cognitive_personas.get_active_persona().model_dump(),
        "personas": cognitive_personas.list_personas(),
    }

@app.post("/api/personas/select")
async def select_persona_endpoint(req: SelectPersonaRequest):
    """Switches the assistant's active thinking mode / cognitive archetype."""
    from cognitive_personas import cognitive_personas
    selected = cognitive_personas.set_active_persona(req.persona)
    return {"status": "switched", "active_persona": selected.model_dump()}

# =============================================================================
# VIDEO & MEETING INTELLIGENCE ENDPOINTS (claude-video Adaptation)
# =============================================================================

class InspectVideoRequest(BaseModel):
    video_path: str = Field(..., description="Local path to video file")

class ExtractFramesRequest(BaseModel):
    video_path: str = Field(..., description="Local path to video file")
    interval_seconds: float = Field(10.0, description="Sampling interval in seconds")
    max_frames: int = Field(30, description="Maximum frames to sample")

class VideoTranscriptRequest(BaseModel):
    video_path: str = Field(..., description="Local path to video file")

class SummarizeMeetingRequest(BaseModel):
    video_path: str = Field(..., description="Local path to video file")
    title: Optional[str] = Field(None, description="Custom title for the briefing")
    interval_seconds: float = Field(15.0, description="Frame sampling interval in seconds")

@app.post("/api/video/inspect")
async def inspect_video_endpoint(req: InspectVideoRequest):
    """Inspects video stream format, codecs, duration, and dimensions."""
    from video_inspector import video_inspector
    return video_inspector.inspect_video(req.video_path)

@app.post("/api/video/frames")
async def extract_frames_endpoint(req: ExtractFramesRequest):
    """Extracts visual keyframes at regular intervals using FFmpeg into vault cache."""
    from video_inspector import video_inspector
    frames = video_inspector.extract_keyframes(
        video_path=req.video_path,
        interval_seconds=req.interval_seconds,
        max_frames=req.max_frames,
    )
    return {"status": "success", "frames": frames, "count": len(frames)}

@app.post("/api/video/transcript")
async def extract_video_transcript_endpoint(req: VideoTranscriptRequest):
    """Extracts subtitle segments or audio speech activity windows."""
    from video_inspector import video_inspector
    return video_inspector.extract_audio_and_transcript(req.video_path)

@app.post("/api/video/summarize")
async def summarize_meeting_endpoint(req: SummarizeMeetingRequest):
    """Generates an executive meeting or tutorial briefing with timestamps and action items."""
    from video_inspector import video_inspector
    return video_inspector.synthesize_meeting_summary(
        video_path=req.video_path,
        title=req.title,
        interval_seconds=req.interval_seconds,
    )

# =============================================================================
# CONVERSATION TREE & PRESET ENDPOINTS (LibreChat Adaptation)
# =============================================================================

class ForkBranchRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    fork_message_id: int = Field(..., description="Message ID to fork from")
    new_branch_name: str = Field("Alternative Branch", description="Name for the new branch")

class SwitchBranchRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    branch_id: str = Field(..., description="Branch identifier to activate")

class SavePresetRequest(BaseModel):
    preset_id: str = Field(..., description="Preset identifier")
    name: str = Field(..., description="Display name")
    model_alias: str = Field("primary", description="Model alias")
    temperature: float = Field(0.7, description="Model temperature")
    system_prompt: Optional[str] = Field(None, description="System role prompt")
    toolsets: Optional[List[str]] = Field(None, description="Enabled toolsets")
    description: Optional[str] = Field(None, description="Preset description")

class SaveArtifactRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    branch_id: str = Field(..., description="Branch identifier")
    title: str = Field(..., description="Artifact title")
    artifact_type: str = Field("markdown", description="Artifact type ('code', 'markdown', 'plan', 'data')")
    content: str = Field(..., description="Artifact body content")

@app.get("/api/tree/branches/{session_id}")
async def list_branches_endpoint(session_id: str):
    """Lists all branches in the conversation tree for a session."""
    from conversation_tree import conversation_tree
    branches = conversation_tree.list_branches(session_id)
    return {"status": "success", "branches": branches, "count": len(branches)}

@app.post("/api/tree/branches/fork")
async def fork_branch_endpoint(req: ForkBranchRequest):
    """Forks a conversation from a specific message node into an exploratory branch."""
    from conversation_tree import conversation_tree
    return conversation_tree.fork_branch(
        session_id=req.session_id,
        fork_message_id=req.fork_message_id,
        new_branch_name=req.new_branch_name,
    )

@app.post("/api/tree/branches/switch")
async def switch_branch_endpoint(req: SwitchBranchRequest):
    """Switches the active branch in the conversation session."""
    from conversation_tree import conversation_tree
    success = conversation_tree.switch_branch(session_id=req.session_id, branch_id=req.branch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Branch not found in session")
    return {"status": "switched", "branch_id": req.branch_id}

@app.get("/api/tree/history/{session_id}")
async def get_branch_history_endpoint(session_id: str, branch_id: Optional[str] = None):
    """Returns the reconstructed linear history from root to leaf for the active or specified branch."""
    from conversation_tree import conversation_tree
    history = conversation_tree.get_branch_history(session_id=session_id, branch_id=branch_id)
    return {"status": "success", "history": history, "count": len(history)}

@app.get("/api/tree/presets")
async def list_presets_endpoint():
    """Lists all operational presets."""
    from conversation_tree import conversation_tree
    presets = conversation_tree.list_presets()
    return {"status": "success", "presets": presets, "count": len(presets)}

@app.get("/api/tree/presets/{preset_id}")
async def get_preset_endpoint(preset_id: str):
    """Retrieves a specific operational preset."""
    from conversation_tree import conversation_tree
    preset = conversation_tree.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    return {"status": "success", "preset": preset}

@app.post("/api/tree/presets")
async def save_preset_endpoint(req: SavePresetRequest):
    """Saves or updates an operational preset."""
    from conversation_tree import conversation_tree
    saved = conversation_tree.save_preset(
        preset_id=req.preset_id,
        name=req.name,
        model_alias=req.model_alias,
        temperature=req.temperature,
        system_prompt=req.system_prompt,
        toolsets=req.toolsets,
        description=req.description,
    )
    return {"status": "saved", "preset": saved}

@app.post("/api/tree/artifacts")
async def save_artifact_endpoint(req: SaveArtifactRequest):
    """Saves a versioned artifact tied to a branch and syncs it to the Obsidian vault."""
    from conversation_tree import conversation_tree
    art = conversation_tree.save_artifact(
        session_id=req.session_id,
        branch_id=req.branch_id,
        title=req.title,
        artifact_type=req.artifact_type,
        content=req.content,
    )
    return {"status": "saved", "artifact": art}

@app.get("/api/tree/artifacts/{session_id}")
async def list_artifacts_endpoint(session_id: str, branch_id: Optional[str] = None):
    """Lists artifacts generated in the conversation tree."""
    from conversation_tree import conversation_tree
    artifacts = conversation_tree.list_artifacts(session_id=session_id, branch_id=branch_id)
    return {"status": "success", "artifacts": artifacts, "count": len(artifacts)}

# =============================================================================
# ARCHIFY ARCHITECTURE & VERIFIED DIAGRAMS (Archify Adaptation)
# =============================================================================

class CreateDiagramRequest(BaseModel):
    title: str = Field(..., description="Diagram title")
    diagram_type: str = Field("system", description="Diagram type: 'system', 'sequence', 'data_flow', 'state_machine'")
    description: Optional[str] = Field(None, description="Architecture description")
    mermaid_code: Optional[str] = Field(None, description="Raw Mermaid code")

class InspectCodebaseRequest(BaseModel):
    target_dir: Optional[str] = Field(None, description="Target backend directory path")

@app.post("/api/archify/diagrams")
async def create_diagram_endpoint(req: CreateDiagramRequest):
    """Generates a verified Mermaid diagram and exports an architectural note to Obsidian."""
    from archify_engine import archify_engine
    return archify_engine.generate_diagram(
        title=req.title,
        diagram_type=req.diagram_type,
        description=req.description,
        raw_mermaid=req.mermaid_code,
    )

@app.post("/api/archify/inspect")
async def inspect_codebase_endpoint(req: InspectCodebaseRequest):
    """Scans Python modules and generates a verifiable architecture diagram."""
    from archify_engine import archify_engine
    return archify_engine.inspect_codebase_architecture(target_dir=req.target_dir)

@app.get("/api/archify/diagrams")
async def list_diagrams_endpoint():
    """Lists all stored architecture diagrams."""
    from archify_engine import archify_engine
    diags = archify_engine.list_diagrams()
    return {"status": "success", "diagrams": diags, "count": len(diags)}

# =============================================================================
# SOCRATIC MASTERY & TECHNICAL CURRICULUM (OpenMAIC Adaptation)
# =============================================================================

class CreateCurriculumRequest(BaseModel):
    topic: str = Field(..., description="Topic or technology to master")
    category: str = Field("engineering", description="Curriculum category")
    description: Optional[str] = Field(None, description="Learning goals")

class SubmitDrillAnswerRequest(BaseModel):
    drill_id: str = Field(..., description="Drill identifier")
    answer: str = Field(..., description="Learner's reasoning or answer")

@app.post("/api/curriculum/create")
async def create_curriculum_endpoint(req: CreateCurriculumRequest):
    """Generates a multi-stage curriculum with Socratic drills in the Obsidian vault."""
    from socratic_curriculum import socratic_curriculum
    return socratic_curriculum.generate_curriculum(
        topic=req.topic,
        category=req.category,
        description=req.description,
    )

@app.get("/api/curriculum/drills/{curriculum_id}/next")
async def get_next_drill_endpoint(curriculum_id: str):
    """Retrieves the next unanswered Socratic exploration drill."""
    from socratic_curriculum import socratic_curriculum
    drill = socratic_curriculum.get_next_drill(curriculum_id)
    if not drill:
        return {"status": "completed", "message": "All drills answered for this curriculum."}
    return {"status": "success", "drill": drill}

@app.post("/api/curriculum/drills/submit")
async def submit_drill_endpoint(req: SubmitDrillAnswerRequest):
    """Evaluates drill response and recalculates topic mastery level."""
    from socratic_curriculum import socratic_curriculum
    return socratic_curriculum.submit_drill_answer(drill_id=req.drill_id, user_answer=req.answer)

@app.get("/api/curriculum/topics")
async def list_curricula_endpoint():
    """Lists all active curricula with progress metrics."""
    from socratic_curriculum import socratic_curriculum
    topics = socratic_curriculum.list_curricula()
    return {"status": "success", "topics": topics, "count": len(topics)}

# =============================================================================
# VOICE STUDIO & AUDIO BRIEFINGS (VoiceStudio Adaptation)
# =============================================================================

class RenderNoteAudioRequest(BaseModel):
    note_title: str = Field(..., description="Obsidian note title or path")
    profile_id: str = Field("host_maxim", description="Voice profile ID")

class RenderDialogueAudioRequest(BaseModel):
    title: str = Field("Dialogue_Podcast", description="Dialogue podcast title")
    script: List[Dict[str, str]] = Field(..., description="List of turns: [{'speaker': 'host_maxim', 'text': '...'}]")

@app.post("/api/voice-studio/render-note")
async def render_note_audio_endpoint(req: RenderNoteAudioRequest):
    """Converts an Obsidian vault note into a clean spoken MP3 podcast briefing."""
    from voice_studio import voice_studio
    return voice_studio.synthesize_note_to_audio(
        note_title_or_path=req.note_title,
        profile_id=req.profile_id,
    )

@app.post("/api/voice-studio/render-dialogue")
async def render_dialogue_audio_endpoint(req: RenderDialogueAudioRequest):
    """Renders a multi-speaker scripted dialogue into a master MP3 audio briefing."""
    from voice_studio import voice_studio
    return voice_studio.synthesize_dialogue(
        script=req.script,
        title=req.title,
    )

@app.get("/api/voice-studio/profiles")
async def list_voice_profiles_endpoint():
    """Lists available voice profiles."""
    from voice_studio import voice_studio
    profiles = voice_studio.list_profiles()
    return {"status": "success", "profiles": profiles, "count": len(profiles)}

@app.get("/api/voice-studio/productions")
async def list_voice_productions_endpoint():
    """Lists all rendered audio productions."""
    from voice_studio import voice_studio
    productions = voice_studio.list_productions()
    return {"status": "success", "productions": productions, "count": len(productions)}

# =============================================================================
# SCIENTIFIC RESEARCH & LITERATURE DISCOVERY (K-Dense Adaptation)
# =============================================================================

class SearchArxivRequest(BaseModel):
    query: str = Field(..., description="Academic query or topic")
    max_results: int = Field(5, description="Maximum papers to return")

class SearchPubmedRequest(BaseModel):
    query: str = Field(..., description="Biomedical query or disease/drug name")
    max_results: int = Field(5, description="Maximum papers to return")

class LookupCompoundRequest(BaseModel):
    compound_name: str = Field(..., description="Chemical compound name")

class SynthesizeReviewRequest(BaseModel):
    topic: str = Field(..., description="Topic for academic literature review")

@app.post("/api/science/arxiv")
async def search_arxiv_endpoint(req: SearchArxivRequest):
    """Searches arXiv academic repository for peer-reviewed papers and abstracts."""
    from scientific_skills import scientific_skills
    papers = scientific_skills.search_arxiv(query=req.query, max_results=req.max_results)
    return {"status": "success", "papers": papers, "count": len(papers)}

@app.post("/api/science/pubmed")
async def search_pubmed_endpoint(req: SearchPubmedRequest):
    """Searches NCBI PubMed biomedical database."""
    from scientific_skills import scientific_skills
    papers = scientific_skills.search_pubmed(query=req.query, max_results=req.max_results)
    return {"status": "success", "papers": papers, "count": len(papers)}

@app.post("/api/science/pubchem")
async def lookup_compound_endpoint(req: LookupCompoundRequest):
    """Retrieves chemical formula, molecular weight, IUPAC name, and SMILES via PubChem."""
    from scientific_skills import scientific_skills
    compound = scientific_skills.lookup_pubchem_compound(compound_name=req.compound_name)
    return {"status": "success", "compound": compound}

@app.post("/api/science/review")
async def synthesize_review_endpoint(req: SynthesizeReviewRequest):
    """Synthesizes a structured academic literature review in the Obsidian vault."""
    from scientific_skills import scientific_skills
    dossier = scientific_skills.synthesize_literature_review(topic=req.topic)
    return {"status": "synthesized", "dossier": dossier}

@app.get("/api/science/papers")
async def list_saved_papers_endpoint(limit: int = 50):
    """Lists saved scientific papers and bibliography entries."""
    from scientific_skills import scientific_skills
    papers = scientific_skills.list_saved_papers(limit=limit)
    return {"status": "success", "papers": papers, "count": len(papers)}

# =============================================================================
# BROWSERSKILL REAL-SESSION BRIDGE (Tencent Adaptation)
# =============================================================================

class BrowserEvalRequest(BaseModel):
    script: str = Field(..., description="JavaScript expression to evaluate")
    tab_id: Optional[str] = Field(None, description="Target browser tab ID")
    test_mode: bool = Field(False, description="Run in simulated test mode")

class BrowserCommandRequest(BaseModel):
    action: str = Field(..., description="Action: click, type, scroll, extract")
    target: str = Field(..., description="CSS selector or element target")
    value: Optional[str] = Field(None, description="Optional text value")
    test_mode: bool = Field(False, description="Run in simulated test mode")

@app.get("/api/browserskill/active-tab")
async def get_browser_active_tab_endpoint(test_mode: bool = False):
    """Retrieves active logged-in browser tab info via BrowserSkill bridge."""
    from browser_skill_bridge import browser_skill_bridge
    tab = browser_skill_bridge.get_active_browser_tab(test_mode=test_mode)
    return {"status": "success", "tab": tab}

@app.post("/api/browserskill/evaluate")
async def evaluate_browser_script_endpoint(req: BrowserEvalRequest):
    """Safely evaluates JavaScript in active tab without stealing window focus."""
    from browser_skill_bridge import browser_skill_bridge
    return browser_skill_bridge.evaluate_script(script=req.script, tab_id=req.tab_id, test_mode=req.test_mode)

@app.post("/api/browserskill/execute")
async def execute_browser_command_endpoint(req: BrowserCommandRequest):
    """Executes click, type, scroll, or extract in the active tab."""
    from browser_skill_bridge import browser_skill_bridge
    return browser_skill_bridge.execute_browser_command(
        action=req.action, target=req.target, value=req.value, test_mode=req.test_mode
    )

@app.get("/api/browserskill/actions")
async def list_browser_actions_endpoint(limit: int = 20):
    """Lists logged browser actions."""
    from browser_skill_bridge import browser_skill_bridge
    actions = browser_skill_bridge.list_recent_actions(limit=limit)
    return {"status": "success", "actions": actions, "count": len(actions)}

# =============================================================================
# MAGNITUDE HARDWARE PROFILER & MODEL RECOMMENDER (Magnitude Adaptation)
# =============================================================================

class BenchmarkThroughputRequest(BaseModel):
    test_tokens: int = Field(100, description="Tokens to simulate in benchmark")

@app.post("/api/magnitude/profile")
async def profile_hardware_endpoint():
    """Probes system CPU, RAM, and GPU VRAM to recommend local open-source models."""
    from magnitude_engine import magnitude_engine
    return magnitude_engine.profile_hardware()

@app.post("/api/magnitude/benchmark")
async def benchmark_throughput_endpoint(req: BenchmarkThroughputRequest):
    """Executes a local inference throughput benchmark."""
    from magnitude_engine import magnitude_engine
    return magnitude_engine.benchmark_throughput(test_tokens=req.test_tokens)

@app.get("/api/magnitude/latest")
async def get_latest_hardware_profile_endpoint():
    """Retrieves the latest hardware profile and recommendations."""
    from magnitude_engine import magnitude_engine
    profile = magnitude_engine.get_latest_profile()
    return {"status": "success", "profile": profile}

# =============================================================================
# CURSOR PLUGIN ECOSYSTEM (Cursor Adaptation)
# =============================================================================

class ImportCursorPluginRequest(BaseModel):
    manifest: Any = Field(..., description="Manifest dict or path to plugin.json")

class ToggleCursorPluginRequest(BaseModel):
    plugin_id: str = Field(..., description="Plugin ID")
    enabled: bool = Field(..., description="True to enable, False to disable")

@app.post("/api/cursor-plugins/import")
async def import_cursor_plugin_endpoint(req: ImportCursorPluginRequest):
    """Imports and registers a Cursor plugin manifest."""
    from cursor_plugins import cursor_plugins
    return cursor_plugins.import_plugin(req.manifest)

@app.get("/api/cursor-plugins/list")
async def list_cursor_plugins_endpoint():
    """Lists all installed Cursor plugins."""
    from cursor_plugins import cursor_plugins
    plugins = cursor_plugins.list_installed_plugins()
    return {"status": "success", "plugins": plugins, "count": len(plugins)}

@app.post("/api/cursor-plugins/toggle")
async def toggle_cursor_plugin_endpoint(req: ToggleCursorPluginRequest):
    """Enables or disables an installed Cursor plugin."""
    from cursor_plugins import cursor_plugins
    ok = cursor_plugins.toggle_plugin(req.plugin_id, req.enabled)
    return {"status": "success" if ok else "failed", "plugin_id": req.plugin_id, "enabled": req.enabled}

# =============================================================================
# OPENSEO VISIBILITY & AUDITOR ENGINE (OpenSEO Adaptation)
# =============================================================================

class AuditUrlRequest(BaseModel):
    url: str = Field(..., description="Webpage URL to audit")
    test_mode: bool = Field(False, description="Use mock HTML test fixture")

class AuditHtmlRequest(BaseModel):
    html: str = Field(..., description="Raw HTML markup to audit")
    url: Optional[str] = Field("https://example.com", description="Associated URL")

class KeywordDensityRequest(BaseModel):
    text: str = Field(..., description="Article or page text to analyze")
    target_keywords: Optional[List[str]] = Field(None, description="Target keywords")

@app.post("/api/seo/audit-url")
async def audit_seo_url_endpoint(req: AuditUrlRequest):
    """Performs full technical SEO audit and saves scorecard to Obsidian."""
    from open_seo import open_seo
    return open_seo.audit_url(req.url, test_mode=req.test_mode)

@app.post("/api/seo/audit-html")
async def audit_seo_html_endpoint(req: AuditHtmlRequest):
    """Performs static SEO audit on provided HTML source."""
    from open_seo import open_seo
    return open_seo.audit_html(req.html, url=req.url or "https://example.com")

@app.post("/api/seo/keyword-density")
async def analyze_keyword_density_endpoint(req: KeywordDensityRequest):
    """Analyzes keyword frequency and density distribution."""
    from open_seo import open_seo
    return open_seo.analyze_keyword_density(req.text, target_keywords=req.target_keywords)

@app.get("/api/seo/audits")
async def list_seo_audits_endpoint():
    """Lists recent SEO audits."""
    from open_seo import open_seo
    audits = open_seo.list_audits()
    return {"status": "success", "audits": audits, "count": len(audits)}

# =============================================================================
# STANDALONE LOCAL MODEL DISCOVERY & NATIVE LLAMA-SERVER
# =============================================================================

class LocalModelLoadRequest(BaseModel):
    model_path_or_id: str = Field(..., description="Local model file path or HuggingFace repo ID")
    port: int = Field(8080, description="Port for standalone llama-server")
    context_length: int = Field(16384, description="Context window tokens")
    n_gpu_layers: int = Field(99, description="GPU offload layers")

@app.get("/api/local/models")
async def get_local_models_endpoint():
    """Scans local models/ directory and returns all detected GGUF models."""
    from local_model_manager import local_model_manager
    models = local_model_manager.scan_models()
    status = local_model_manager.get_status()
    return {"status": "success", "models": models, "count": len(models), "telemetry": status}

@app.post("/api/local/start")
async def start_local_model_endpoint(req: LocalModelLoadRequest):
    """Starts standalone native llama-server with CUDA acceleration."""
    from local_model_manager import local_model_manager
    try:
        res = local_model_manager.start_server(
            model_path_or_id=req.model_path_or_id,
            port=req.port,
            context_length=req.context_length,
            n_gpu_layers=req.n_gpu_layers,
        )
        return {"status": "success", "server": res}
    except Exception as e:
        logger.error(f"Error starting local llama-server: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/local/stop")
async def stop_local_model_endpoint():
    """Stops the active standalone native llama-server."""
    from local_model_manager import local_model_manager
    stopped = local_model_manager.stop_server()
    return {"status": "success", "stopped": stopped}

@app.post("/api/local/open-folder")
async def open_local_models_folder_endpoint():
    """Opens project models/ folder in native Windows Explorer / file manager."""
    from local_model_manager import local_model_manager
    return local_model_manager.open_models_directory()

@app.post("/api/local/ensure")
async def ensure_local_model_endpoint(req: LocalModelLoadRequest):
    """Ensures llama-server is online with the requested model."""
    from local_model_manager import local_model_manager
    try:
        res = local_model_manager.ensure_model_running(req.model_path_or_id)
        return {"status": "success", "server": res}
    except Exception as e:
        logger.error(f"Error ensuring local llama-server: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/local/status")
async def get_local_status_endpoint():
    """Returns status and health of the standalone native llama-server."""
    from local_model_manager import local_model_manager
    return local_model_manager.get_status()

class ModelSelectBestRequest(BaseModel):
    task_type: Optional[str] = Field("auto", description="Capability category or 'auto'")
    has_image: Optional[bool] = Field(False, description="Whether prompt includes image attachment")
    has_audio: Optional[bool] = Field(False, description="Whether prompt includes audio attachment")
    query: Optional[str] = Field("", description="User prompt or intent directive")

@app.post("/api/local/select-best")
async def select_best_local_model_endpoint(req: ModelSelectBestRequest):
    """
    Autonomously selects the best local GGUF model based on capability demand:
    - All-Rounder LLM (models/llm/)
    - Vision & Multimodal (models/vision/)
    - Voice-to-Text ASR (models/asr/)
    - Text-to-Voice TTS (models/tts/)
    """
    from local_model_manager import local_model_manager
    selected = local_model_manager.select_best_model(
        task_type=req.task_type or "auto",
        has_image=bool(req.has_image),
        has_audio=bool(req.has_audio),
        query=req.query or "",
    )
    if not selected:
        raise HTTPException(status_code=404, detail="No matching local model found")
    return {
        "status": "success",
        "selected_model": selected,
        "routed_category": selected.get("routed_category"),
        "selection_reason": selected.get("selection_reason"),
    }

# ---------------------------------------------------------
# Laya System 1 Decision Engine Endpoints
# ---------------------------------------------------------

class DecisionRouteRequest(BaseModel):
    query: str
    has_image: bool = False
    has_audio: bool = False

class DecisionVerifyRequest(BaseModel):
    user_query: str
    assistant_reply: str
    threshold: float = 0.20

class DecisionSafetyRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class DecisionPredictRequest(BaseModel):
    state: Union[str, Dict[str, Any]]
    questions: Dict[str, Any]
    model: Optional[str] = None

class DecisionModelSelectRequest(BaseModel):
    query: str
    task_type: str = "auto"
    has_image: bool = False
    has_audio: bool = False
    prefer_local: bool = True

class DecisionBrowsingRequest(BaseModel):
    query: Optional[str] = None
    action: str = "evaluate_need"  # "evaluate_need", "decide_action", "verify_content"
    objective: Optional[str] = None
    url: Optional[str] = None
    content: Optional[str] = None
    elements: Optional[List[Dict[str, Any]]] = None
    session_id: str = "default_session"

@app.post("/api/decision/route")
async def decision_route_endpoint(req: DecisionRouteRequest):
    try:
        from decision_engine import decision_engine
        decision = decision_engine.classify_intent(
            query=req.query,
            has_image=req.has_image,
            has_audio=req.has_audio
        )
        return {
            "status": "success",
            "modality": decision.modality,
            "target_category": decision.target_category,
            "language": decision.language,
            "confidence": decision.confidence,
            "probabilities": decision.probabilities,
            "is_neural": decision.is_neural,
            "reason": decision.reason,
        }
    except Exception as e:
        logger.error("Error in decision_route_endpoint: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/decision/verify")
async def decision_verify_endpoint(req: DecisionVerifyRequest):
    try:
        from decision_engine import decision_engine
        verif = decision_engine.verify_response(
            user_query=req.user_query,
            assistant_reply=req.assistant_reply,
            threshold=req.threshold
        )
        return {
            "status": "success",
            "is_valid": verif.is_valid,
            "addresses_query": verif.addresses_query,
            "confidence": verif.confidence,
            "drift_detected": verif.drift_detected,
            "addresses_prob": verif.addresses_prob,
            "reason": verif.reason,
            "is_neural": verif.is_neural,
        }
    except Exception as e:
        logger.error("Error in decision_verify_endpoint: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/decision/safety")
async def decision_safety_endpoint(req: DecisionSafetyRequest):
    try:
        from decision_engine import decision_engine
        safety = decision_engine.evaluate_tool_safety(
            tool_name=req.tool_name,
            arguments=req.arguments
        )
        return {
            "status": "success",
            "is_allowed": safety.is_allowed,
            "risk_level": safety.risk_level,
            "confidence": safety.confidence,
            "reason": safety.reason,
            "is_neural": safety.is_neural,
        }
    except Exception as e:
        logger.error("Error in decision_safety_endpoint: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/decision/predict")
async def decision_predict_endpoint(req: DecisionPredictRequest):
    try:
        from decision_engine import decision_engine
        res = decision_engine.predict(
            state=req.state,
            questions=req.questions,
            model=req.model
        )
        return {
            "status": "success",
            "result": res
        }
    except Exception as e:
        logger.error("Error in decision_predict_endpoint: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/decision/select-model")
async def decision_select_model_endpoint(req: DecisionModelSelectRequest):
    try:
        from decision_engine import decision_engine
        from local_model_manager import local_model_manager
        from router import model_router
        all_models = local_model_manager.scan_models()
        runnable = [m for m in all_models if m.get("category") != "diffusion"]
        connected = model_router.get_connected_cloud_providers()

        running_path = None
        if local_model_manager.is_server_ready(local_model_manager._active_port):
            r_info = local_model_manager.get_running_model_info(local_model_manager._active_port)
            if r_info and r_info.get("id"):
                running_path = r_info["id"]

        decision = decision_engine.select_suitable_model(
            query=req.query,
            task_type=req.task_type,
            has_image=req.has_image,
            has_audio=req.has_audio,
            candidates=runnable,
            cloud_providers=connected,
            running_model_path=running_path,
        )
        return {
            "status": "success",
            "chosen_model": decision.chosen_model,
            "provider": decision.provider,
            "is_cloud": decision.is_cloud,
            "task_domain": decision.task_domain,
            "complexity": decision.complexity,
            "capability_score": decision.capability_score,
            "capabilities": decision.model_capabilities,
            "reason": decision.reason,
            "is_neural": decision.is_neural,
        }
    except Exception as e:
        logger.error("Error in decision_select_model_endpoint: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/decision/browsing")
async def decision_browsing_endpoint(req: DecisionBrowsingRequest):
    try:
        from decision_engine import decision_engine
        from browser_agent import browser_agent
        if req.action == "decide_action":
            obj = req.objective or req.query or ""
            res = browser_agent.laya_decide_action(objective=obj, session_id=req.session_id)
            return {"status": "success", "result": res}
        elif req.action == "verify_content":
            obj = req.objective or req.query or ""
            res = browser_agent.laya_verify_page(objective=obj, session_id=req.session_id)
            return {"status": "success", "result": res}
        else:
            q = req.query or req.objective or ""
            decision = decision_engine.evaluate_browsing_need(q)
            return {
                "status": "success",
                "needs_browsing": decision.needs_browsing,
                "search_query": decision.search_query,
                "confidence": decision.confidence,
                "reason": decision.reason,
                "is_neural": decision.is_neural,
            }
    except Exception as e:
        logger.error("Error in decision_browsing_endpoint: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# Neural Image Generation Endpoints
# ---------------------------------------------------------

class ImageGenerateRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024
    style: Optional[str] = "photorealistic"
    seed: Optional[int] = None

@app.get("/api/images/{filename}")
async def get_generated_image_endpoint(filename: str):
    """Serves generated images from the Obsidian vault cache."""
    try:
        from image_generator import image_generator
        img_path = image_generator.get_image_path(filename)
        if not img_path or not img_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        return FileResponse(img_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error serving image %s: %s", filename, e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/image/generate")
async def generate_image_endpoint(req: ImageGenerateRequest):
    """Generates an image via neural diffusion and persists to vault."""
    try:
        from image_generator import image_generator
        res = image_generator.generate(
            prompt=req.prompt,
            width=req.width,
            height=req.height,
            style=req.style,
            seed=req.seed
        )
        return res
    except Exception as e:
        logger.error("Error in generate_image_endpoint: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# Document & Image Reading Endpoints
# ---------------------------------------------------------

class ReadDocumentRequest(BaseModel):
    file_path: str = Field(..., description="Path to file (PDF, DOCX, CSV, TXT, etc.)")
    max_chars: Optional[int] = Field(default=15000, description="Max characters to extract")

class InspectImageRequest(BaseModel):
    image_path: str = Field(..., description="Path to image file")
    prompt: Optional[str] = Field(default=None, description="Inspection prompt or question")

@app.post("/api/document/read")
async def read_document_endpoint(req: ReadDocumentRequest):
    """Reads and extracts text from local document (PDF, Word, CSV, JSON, code)."""
    try:
        from document_reader import document_reader
        return document_reader.read_document(req.file_path, max_chars=req.max_chars or 15000)
    except Exception as e:
        logger.error("Error in read_document_endpoint: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/image/inspect")
async def inspect_image_endpoint(req: InspectImageRequest):
    """Inspects and describes an image file using PIL and multimodal vision."""
    try:
        from document_reader import document_reader
        return await document_reader.inspect_image(
            req.image_path,
            prompt=req.prompt,
            auto_boot_local=True,
        )
    except Exception as e:
        logger.error("Error in inspect_image_endpoint: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/retrieval/status")
async def retrieval_status_endpoint():
    """Returns local embedding and reranker model status and readiness."""
    from retrieval_engine import retrieval_engine
    return retrieval_engine.get_status()

@app.post("/api/retrieval/embed")
async def embed_endpoint(req: EmbedRequest):
    """Generates 1024-dim dense vector embedding(s) using Qwen3-Embedding."""
    from retrieval_engine import retrieval_engine
    if req.texts:
        vectors = retrieval_engine.get_embeddings_batch(req.texts, auto_boot=bool(req.auto_boot))
        return {"status": "success", "embeddings": vectors, "count": len(vectors)}
    elif req.text:
        vec = retrieval_engine.get_embedding(req.text, auto_boot=bool(req.auto_boot))
        return {"status": "success", "embedding": vec, "dimensions": len(vec) if vec else 0}
    raise HTTPException(status_code=400, detail="Either 'text' or 'texts' must be provided.")

@app.post("/api/retrieval/rerank")
async def rerank_endpoint(req: RerankRequest):
    """Reranks documents against query using Qwen3-Reranker."""
    from retrieval_engine import retrieval_engine
    ranked = retrieval_engine.rerank(
        query=req.query,
        documents=req.documents,
        top_k=req.top_k,
        auto_boot=bool(req.auto_boot),
    )
    return {"status": "success", "query": req.query, "results": ranked}

@app.post("/api/vault/semantic-search")
async def vault_semantic_search_endpoint(req: SemanticSearchRequest):
    """Hybrid semantic vector + reranker search across Obsidian vault notes."""
    from tools.vault_tool import vault_synapse
    results = vault_synapse.semantic_search_vault(
        query=req.query,
        max_results=req.max_results or 10,
        auto_boot=bool(req.auto_boot),
    )
    return {"status": "success", "query": req.query, "count": len(results), "results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=config.host, port=config.port, reload=True)





