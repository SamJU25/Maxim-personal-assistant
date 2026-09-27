"""
Autonomous ReAct Agent Engine for MaxIM.
Combines Bitterbot's sarcastic personality, LifeOS TELOS accountability,
OpenHuman memory persistence, and Meta Muse evidence receipts.
"""
import time
import json
import logging
import asyncio
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from config import config
from telos import LifeOSEngine
from memory import SQLiteMemoryStore, MessageRecord
from router import model_router, ProviderType
from tools import vault_synapse, screen_tool, cua_driver
from tools.reach_tool import agent_reach
from five_layer_memory import five_layer_memory, FiveLayerMemorySystem

logger = logging.getLogger("maxim.engine")

def _run_async_safely(coro):
    """Executes a coroutine safely whether an event loop is already running or not."""
    try:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(lambda: asyncio.run(coro)).result()
    except RuntimeError:
        return asyncio.run(coro)


# Standard Tool Schemas for Model Function-Calling
MAXIM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_vault_note",
            "description": "Reads a markdown note from the user's Obsidian vault. Returns content, tags, and wikilinks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title or relative path of the note to read (e.g. 'Master MOC' or 'DeepSeek-V3 MoE Architecture').",
                    }
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_vault_note",
            "description": "Creates or updates a note in the Obsidian vault with wikilinks and tags.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The title of the note (e.g. 'DeepSeek Analysis')."},
                    "content": {"type": "string", "description": "The markdown content of the note."},
                    "folder": {
                        "type": "string",
                        "description": "Target folder (e.g. '01 - Memory', '02 - Skills', '04 - Tasks'). Default is '01 - Memory'.",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags like ['#ai', '#research'].",
                    },
                },
                "required": ["title", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_vault",
            "description": "Performs a full-text search across all notes in the Obsidian vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keyword or concept to search for."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_vault_backlinks",
            "description": "Finds all notes in the vault that link to the specified note.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The title of the note to find backlinks for."}
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remember_user_fact",
            "description": "Permanently saves a fact, preference, or rule about the user in the SQLite memory tree.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category: 'preference', 'habit', 'project', or 'rule'.",
                    },
                    "key": {"type": "string", "description": "Unique key (e.g. 'ui_theme', 'favorite_model')."},
                    "value": {"type": "string", "description": "The fact or preference to remember."},
                },
                "required": ["category", "key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_screen",
            "description": "Inspects the user's active application window and captures a real-time screenshot. Use this whenever the user asks 'what do you see?', 'look at my screen', or needs advice on what they are currently viewing.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cua_click",
            "description": "Clicks an element, link, or coordinate in the background using Cua driver without stealing the mouse cursor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_name_or_selector": {
                        "type": "string",
                        "description": "Accessible name or selector of the element to click (e.g. 'Search', 'Download ZIP').",
                    },
                    "x": {"type": "integer", "description": "Optional X coordinate on screen."},
                    "y": {"type": "integer", "description": "Optional Y coordinate on screen."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cua_type",
            "description": "Types text into an input field or active window in the background using Cua driver.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text string to type."},
                    "element_name": {
                        "type": "string",
                        "description": "Optional input field name or selector to focus and type into.",
                    },
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cua_navigate_browser",
            "description": "Navigates the browser window to a target URL in the background.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Web URL to navigate to (e.g. 'https://github.com')."}
                },
                "required": ["url"],
            },
        },
    },
]

from tools.catalog import tool_catalog
# Load full Hermes-compatible modular toolset catalog
MAXIM_TOOLS = tool_catalog.get_all_tools()

class MaxIMAgentEngine:
    def __init__(
        self,
        memory_store: Optional[SQLiteMemoryStore] = None,
        lifeos: Optional[LifeOSEngine] = None,
        five_layer: Optional[FiveLayerMemorySystem] = None,
    ):
        self.memory = memory_store or SQLiteMemoryStore()
        self.lifeos = lifeos or LifeOSEngine()
        self.five_layer = five_layer or five_layer_memory
        self.max_tool_iterations = 6

    def get_scoped_tools(
        self,
        provider: Optional[ProviderType | str] = None,
        model: Optional[str] = None,
        query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns an optimal tool payload based on model context window, provider capacity, and user intent.
        Local models (llama-server, Unsloth, Ollama) receive a high-leverage core suite plus dynamically
        mounted tool bundles matching the prompt's intent. This prevents context window saturation
        while ensuring that specialized capabilities (browser, OS automation, office, files, MCP, etc.)
        are immediately accessible when requested.
        Cloud models with massive context windows (Gemini, Claude, GPT-4o) receive the full MAXIM_TOOLS catalog.
        """
        active_prov = str(provider or model_router.active_provider).lower()
        is_local = any(loc in active_prov for loc in ("unsloth", "ollama", "local", "custom", "lmstudio"))
        if is_local:
            # Universal Foundational Core (always mounted for local execution)
            scoped_names = {
                "read_vault_note", "write_vault_note", "search_vault", "find_vault_backlinks",
                "remember_user_fact", "retain_memory", "recall_memory", "query_five_layer_memory",
                "compact_context_safeguard", "inspect_screen", "web_search", "read_web_page",
                "sandbox_run_command", "add_session_todo", "update_session_todo", "list_session_todos",
                "get_hardware_status", "adjust_master_volume", "set_screen_brightness",
                "crystallize_skill", "recall_skill", "generate_image",
                "read_document", "inspect_image"
            }

            if query:
                q = query.lower()

                # 1. Browser & Web Navigation Bundle
                if any(k in q for k in ("browser", "web", "url", "http", "site", "navigate", "page", "scrape", "dom", "click link", "open link", "tab", "chrome", "edge")):
                    scoped_names.update({
                        "browser_navigate", "browser_get_dom", "browser_click_element",
                        "browser_type_element", "browser_extract_text", "browser_manage_session"
                    })

                # 2. Desktop OS & Application Management Bundle
                if any(k in q for k in ("window", "app", "application", "desktop", "focus", "launch", "open app", "switch to", "minimize", "maximize", "close window", "process", "click", "mouse", "type", "keyboard", "hwnd")):
                    scoped_names.update({
                        "os_list_windows", "os_focus_window", "os_launch_app",
                        "os_execute_action", "os_list_processes"
                    })

                # 3. File & Directory Organization Bundle
                if any(k in q for k in ("file", "files", "folder", "directory", "organize", "downloads", "desktop files", "clean up", "move files", "sort")):
                    scoped_names.update({
                        "scan_directory", "organize_directory", "undo_organization"
                    })

                # 4. Office & Spreadsheet Data Bundle
                if any(k in q for k in ("spreadsheet", "excel", "sheet", "csv", "table", "workbook", "cell", "cells", "formula", "rows", "columns")):
                    scoped_names.update({
                        "office_create_workbook", "office_read_sheet", "office_edit_cells",
                        "office_import_csv", "office_export_markdown", "office_rollback_revision"
                    })

                # 5. Swarm & Multi-Agent Operator Bundle
                if any(k in q for k in ("agent", "agents", "specialist", "squad", "hire", "delegate", "council", "operator", "shift", "collaborate")):
                    scoped_names.update({
                        "list_agent_team", "hire_agent_teammate", "run_group_collaboration",
                        "operator_dispatch_group_task", "operator_orchestrate_objective",
                        "operator_cross_group_handoff", "schedule_agent_shift"
                    })

                # 6. Video & Meeting Intelligence Bundle
                if any(k in q for k in ("video", "meeting", "transcript", "frames", "summary of meeting", "mp4", "recording")):
                    scoped_names.update({
                        "video_inspect_file", "video_extract_frames", "video_get_transcript", "video_summarize_meeting"
                    })

                # 7. Architecture & Diagrams Bundle
                if any(k in q for k in ("diagram", "architecture", "mermaid", "flowchart", "inspect codebase", "system graph")):
                    scoped_names.update({
                        "archify_create_diagram", "archify_inspect_codebase", "archify_list_diagrams"
                    })

                # 8. Model Context Protocol (MCP) Bundle
                if any(k in q for k in ("mcp", "smithery", "glama", "install server", "mcp server", "model context protocol")):
                    scoped_names.update({
                        "call_mcp_tool", "mcp_search_registry", "mcp_inspect_server",
                        "mcp_install_server", "mcp_list_servers", "mcp_remove_server"
                    })

                # 9. Academic & Scientific Research Bundle
                if any(k in q for k in ("paper", "arxiv", "pubmed", "pubchem", "literature", "molecule", "dossier")):
                    scoped_names.update({
                        "science_search_arxiv", "science_search_pubmed", "science_lookup_compound", "science_synthesize_literature_review"
                    })

                # 10. Work Guidance & Project Planning Bundle
                if any(k in q for k in ("project", "milestone", "decompose", "work guide", "next action", "goal decomposition")):
                    scoped_names.update({
                        "work_decompose_goal", "work_get_next_action", "work_update_action_status", "work_list_projects"
                    })

                # 11. Mobile ADB Bridge Bundle
                if any(k in q for k in ("phone", "mobile", "android", "adb", "device battery", "device tap")):
                    scoped_names.update({
                        "adb_get_devices", "adb_get_battery", "adb_tap", "adb_swipe", "adb_launch_app"
                    })

            scoped_tools = [t for t in MAXIM_TOOLS if t.get("function", {}).get("name") in scoped_names]
            try:
                from extensions.extension_manager import extension_manager
                scoped_tools.extend(extension_manager.get_scoped_tools(query=query))
            except Exception as ext_err:
                logger.debug(f"Dynamic extension tool mount skipped: {ext_err}")
            return scoped_tools

        try:
            from extensions.extension_manager import extension_manager
            return MAXIM_TOOLS + extension_manager.get_all_tools()
        except Exception:
            return MAXIM_TOOLS

    def build_system_prompt(self, session_id: str = "default_session") -> str:
        """
        Constructs the system prompt.
        To maximize llama.cpp / llama-server KV-cache prefix hits across conversational turns,
        static invariant instructions (Soul, TELOS, Privacy Contract, Cognitive Personas)
        are placed at the front, while dynamic / ephemeral contexts (active window, session todos)
        are placed at the tail.
        """
        prompt_parts: List[str] = []

        # 1. Static Invariant Prefix: Personality & Soul
        soul_text = config.soul_path.read_text(encoding="utf-8") if config.soul_path.exists() else ""
        if soul_text:
            prompt_parts.append(soul_text)

        # 2. Static LifeOS Alignment Directives
        telos_text = self.lifeos.get_context_injection()
        if telos_text:
            prompt_parts.append(telos_text)

        # 3. Static Contracts & Directives
        static_injections = [
            ("privacy_guard", lambda: __import__("privacy_guard").privacy_guard.get_loyalty_and_privacy_contract()),
            ("cognitive_personas", lambda: __import__("cognitive_personas").cognitive_personas.get_directive_prompt()),
            ("mental_models", lambda: __import__("mental_models").mental_models.get_prompt_context(limit=5)),
        ]
        for name, fn in static_injections:
            try:
                txt = fn()
                if txt:
                    prompt_parts.append(txt)
            except Exception as e:
                logger.debug(f"Static prompt injection '{name}' omitted: {e}")

        # 4. Long-Term Facts (Layer 5)
        facts = self.memory.get_facts()
        if facts:
            fact_lines = [f"- {f.key}: {f.value}" for f in facts[:8]]
            prompt_parts.append("### Remembered User Facts:\n" + "\n".join(fact_lines))

        # 5. Dynamic Tail Context: Second Brain, Language Learner, Session Todos, Desktop Window
        dynamic_injections = [
            ("second_brain", lambda: __import__("second_brain").second_brain_engine.get_prompt_context_injection()),
            ("language_learner", lambda: __import__("language_learner").language_learner.get_context_injection()),
            ("session_todos", lambda: __import__("session_todos").session_todos.format_todos_context(session_id)),
        ]
        for name, fn in dynamic_injections:
            try:
                txt = fn()
                if txt:
                    prompt_parts.append(txt)
            except Exception as e:
                logger.debug(f"Dynamic prompt injection '{name}' omitted: {e}")

        # Real-time desktop perception (ephemeral - placed at tail to avoid breaking KV cache)
        active_win = screen_tool.get_active_window()
        if active_win and active_win != "Unknown":
            prompt_parts.append(f"### Real-time Desktop Context:\n- Active Application Window: `{active_win}`")

        # Native Media Tool Directives
        prompt_parts.append(
            "### Native Media & Image Generation Directives:\n"
            "- You have direct access to the `generate_image(prompt, style, width, height)` tool.\n"
            "- When Sam asks you to generate, create, draw, or make a picture, image, photo, or artwork, "
            "you MUST invoke the `generate_image` tool directly. NEVER claim that you cannot generate images directly."
        )

        return "\n\n".join(prompt_parts)

    def execute_tool(self, name: str, args: Dict[str, Any], session_id: str) -> str:
        """Executes tool and records Meta Muse evidence receipt."""
        try:
            # AgentShield Runtime Privilege & Boundary Enforcer
            from agent_shield import agent_shield
            audit = agent_shield.audit_tool_call(name, args, session_id=session_id)
            if not audit.get("allowed", True):
                block_res = json.dumps({"error": f"AgentShield Blocked: {audit.get('reason')}", "security_audit": audit})
                self.memory.log_receipt(name, args, block_res, session_id=session_id)
                return block_res

            if name == "read_vault_note":
                res = vault_synapse.read_note(args.get("title", ""))
                out = json.dumps(res)
            elif name == "write_vault_note":
                res = vault_synapse.write_note(
                    title=args.get("title", ""),
                    content=args.get("content", ""),
                    folder=args.get("folder", "01 - Memory"),
                    tags=args.get("tags"),
                )
                out = json.dumps(res)
            elif name == "search_vault":
                res = vault_synapse.search_vault(args.get("query", ""))
                out = json.dumps(res)
            elif name == "find_vault_backlinks":
                res = vault_synapse.find_backlinks(args.get("title", ""))
                out = json.dumps(res)
            elif name == "remember_user_fact":
                self.memory.remember_fact(
                    category=args.get("category", "preference"),
                    key=args.get("key", ""),
                    value=args.get("value", ""),
                    session_id=session_id,
                )
                out = json.dumps({"status": "remembered", "key": args.get("key")})
            elif name == "query_five_layer_memory":
                q = args.get("query", "")
                lim = args.get("limit", 5)
                res = self.five_layer.search_all_layers(q, limit=lim)
                out = json.dumps(res)
            elif name == "compact_context_safeguard":
                reason = args.get("reason", "Agent-requested safeguard compaction")
                res = self.five_layer.execute_safeguard_compaction(session_id, reason=reason)
                out = json.dumps(res)
            elif name == "generate_image":
                try:
                    from image_generator import image_generator
                except ImportError:
                    from backend.image_generator import image_generator
                prompt = args.get("prompt", "")
                style = args.get("style", "photorealistic")
                width = int(args.get("width", 768))
                height = int(args.get("height", 768))
                res = image_generator.generate(prompt=prompt, width=width, height=height, style=style)
                out = json.dumps(res)
            elif name == "retain_memory":
                res = self.five_layer.retain(
                    content=args.get("content", ""),
                    category=args.get("category", "observation"),
                    source=args.get("source", "user_interaction"),
                    metadata=args.get("metadata"),
                    session_id=session_id,
                )
                out = json.dumps(res)
            elif name == "recall_memory":
                res = self.five_layer.recall(
                    query=args.get("query", ""),
                    top_k=args.get("top_k", 5),
                    include_mental_models=args.get("include_mental_models", True),
                    session_id=session_id,
                )
                out = json.dumps(res)
            elif name == "reflect_mental_models":
                res = self.five_layer.reflect(
                    topic=args.get("topic", "general"),
                    session_id=session_id,
                )
                out = json.dumps(res)
            elif name == "get_mental_models":
                from mental_models import mental_models
                models = mental_models.get_all(
                    min_confidence=args.get("min_confidence", 0.0),
                    limit=args.get("limit", 10),
                )
                out = json.dumps({"status": "success", "mental_models": [m.to_dict() for m in models], "count": len(models)})
            elif name == "inspect_screen":
                res = screen_tool.inspect_screen()
                # Omit large base64 payload from raw text tool observation to preserve LLM token budget
                res_clean = {k: v for k, v in res.items() if k != "image_base64"}
                res_clean["screenshot_captured"] = res.get("screenshot_available", False)
                out = json.dumps(res_clean)
            elif name == "cua_click":
                out = json.dumps(cua_driver.click(
                    element_name_or_selector=args.get("element_name_or_selector"),
                    x=args.get("x"),
                    y=args.get("y"),
                ))
            elif name == "cua_type":
                out = json.dumps(cua_driver.type_text(
                    text=args.get("text", ""),
                    element_name=args.get("element_name"),
                ))
            elif name == "cua_navigate_browser":
                out = json.dumps(cua_driver.navigate_browser(url=args.get("url", "")))
            elif name == "read_web_page":
                res = _run_async_safely(agent_reach.read_web_page(
                    url=args.get("url", ""),
                    max_chars=args.get("max_chars", 10000),
                ))
                out = json.dumps(res)
            elif name == "web_search":
                res = _run_async_safely(agent_reach.web_search(
                    query=args.get("query", ""),
                    max_results=args.get("max_results", 6),
                ))
                out = json.dumps(res)
            elif name == "github_reach":
                res = _run_async_safely(agent_reach.github_reach(
                    repo=args.get("repo", ""),
                    action=args.get("action", "info"),
                ))
                out = json.dumps(res)
            elif name == "community_reach":
                res = _run_async_safely(agent_reach.community_reach(
                    source=args.get("source", "v2ex"),
                    limit=args.get("limit", 6),
                ))
                out = json.dumps(res)
            elif name == "reach_doctor":
                res = _run_async_safely(agent_reach.reach_doctor())
                out = json.dumps(res)
            elif name == "call_mcp_tool":
                from tools.mcp_client import mcp_client
                res = _run_async_safely(mcp_client.call_tool(
                    server_name=args.get("server_name", ""),
                    tool_name=args.get("tool_name", ""),
                    arguments=args.get("arguments", {}),
                ))
                out = json.dumps(res)
            elif name == "mcp_search_registry":
                from tools.mcp_client import mcp_client
                res = _run_async_safely(mcp_client.search_registries(
                    query=args.get("query", ""),
                    registry=args.get("registry", "all"),
                    limit=args.get("limit", 10),
                ))
                out = json.dumps(res)
            elif name == "mcp_inspect_server":
                from tools.mcp_client import mcp_client
                res = mcp_client.inspect_server(args.get("server_id", ""))
                out = json.dumps(res)
            elif name == "mcp_install_server":
                from tools.mcp_client import mcp_client
                cfg = mcp_client.register_server(
                    name=args.get("name", ""),
                    command=args.get("command"),
                    args=args.get("args"),
                    transport=args.get("transport", "stdio"),
                    env=args.get("env"),
                    description=args.get("description"),
                )
                out = json.dumps({"status": "installed", "server": cfg.model_dump()})
            elif name == "mcp_list_servers":
                from tools.mcp_client import mcp_client
                res = mcp_client.list_installed_servers()
                out = json.dumps({"status": "success", "servers": res, "count": len(res)})
            elif name == "mcp_remove_server":
                from tools.mcp_client import mcp_client
                res = mcp_client.remove_server(args.get("name", ""))
                out = json.dumps({"status": "removed" if res else "not_found", "name": args.get("name")})
            elif name == "create_subagent":
                from subagent import subagent_pool
                target_toolset = args.get("toolset", "vault")
                if target_toolset == "reach":
                    whitelist = ["read_web_page", "web_search", "github_reach", "community_reach", "reach_doctor"]
                elif target_toolset == "operator":
                    whitelist = [
                        "list_agent_team", "hire_agent_teammate", "run_group_collaboration",
                        "operator_dispatch_group_task", "operator_orchestrate_objective",
                        "operator_cross_group_handoff", "schedule_agent_shift"
                    ]
                elif target_toolset == "all":
                    whitelist = None
                else:
                    whitelist = ["read_vault_note", "search_vault", "find_vault_backlinks"]
                sub = subagent_pool.create_subagent(
                    task=args.get("task", ""),
                    role=args.get("role", "Specialist Worker"),
                    toolset_whitelist=whitelist,
                    max_iterations=args.get("max_iterations", 4),
                )
                try:
                    sub_res = _run_async_safely(sub.run())
                except Exception as sub_err:
                    sub_res = {"status": "error", "error": str(sub_err)}
                out = json.dumps(sub_res)
            elif name == "call_mcp_tool":
                from tools.mcp_client import mcp_client
                try:
                    mcp_res = _run_async_safely(mcp_client.call_tool(
                        server_name=args.get("server_name", ""),
                        tool_name=args.get("tool_name", ""),
                        arguments=args.get("arguments", {}),
                    ))
                except Exception as mcp_err:
                    mcp_res = {"status": "error", "error": str(mcp_err)}
                out = json.dumps(mcp_res)
            elif name == "list_agent_team":
                from chief_operator import agent_operator
                team = [m.model_dump() for m in agent_operator.list_team()]
                out = json.dumps({"status": "success", "team": team, "total": len(team)})
            elif name == "hire_agent_teammate":
                from chief_operator import agent_operator
                m = agent_operator.hire_agent(
                    name=args.get("name", ""),
                    role=args.get("role", ""),
                    persona=args.get("persona", ""),
                    avatar=args.get("avatar", "Sparkles"),
                    toolsets=args.get("toolsets"),
                    skills=args.get("skills"),
                    category=args.get("category"),
                )
                out = json.dumps({"status": "hired", "agent": m.model_dump()})
            elif name == "run_group_collaboration":
                from chief_operator import agent_operator
                res = _run_async_safely(agent_operator.run_group_chat(
                    group_id=args.get("group_id", "group_core_council"),
                    user_message=args.get("message", ""),
                    rounds=args.get("rounds", 1),
                ))
                out = json.dumps(res)
            elif name == "operator_dispatch_group_task":
                from chief_operator import agent_operator
                res = _run_async_safely(agent_operator.dispatch_group_task(
                    group_id=args.get("group_id", "group_core_council"),
                    task_prompt=args.get("task_prompt", ""),
                    target_agent_ids=args.get("target_agent_ids"),
                    rounds=args.get("rounds", 1),
                ))
                out = json.dumps(res)
            elif name == "operator_orchestrate_objective":
                from chief_operator import agent_operator
                res = _run_async_safely(agent_operator.orchestrate_objective(
                    objective=args.get("objective", ""),
                    preferred_category=args.get("preferred_category"),
                    rounds=args.get("rounds", 1),
                ))
                out = json.dumps(res)
            elif name == "operator_cross_group_handoff":
                from chief_operator import agent_operator
                res = _run_async_safely(agent_operator.cross_group_handoff(
                    source_group_id=args.get("source_group_id", ""),
                    target_group_id=args.get("target_group_id", ""),
                    deliverable_summary=args.get("deliverable_summary", ""),
                    next_step_instruction=args.get("next_step_instruction", ""),
                    rounds=args.get("rounds", 1),
                ))
                out = json.dumps(res)
            elif name == "schedule_agent_shift":
                from chief_operator import agent_operator
                rep = _run_async_safely(agent_operator.execute_shift(
                    agent_id=args.get("agent_id", "agent_hermes"),
                    task=args.get("task", ""),
                ))
                out = json.dumps(rep.model_dump())
            elif name == "evaluate_proactive_initiative":
                from proactive_agent import proactive_agent
                eval_res = _run_async_safely(proactive_agent.evaluate_initiative(
                    session_id=session_id,
                    force=args.get("force", False),
                ))
                out = json.dumps(eval_res)
            elif name == "trigger_idle_scout":
                from idle_scout import idle_scout
                scout_res = _run_async_safely(idle_scout.execute_scout_cycle(
                    trigger_type=args.get("trigger_type", "manual"),
                    force=args.get("force", True),
                ))
                out = json.dumps(scout_res)
            elif name == "get_overnight_intel":
                from idle_scout import idle_scout
                latest_report = idle_scout.get_latest_report()
                if latest_report:
                    out = json.dumps({"status": "found", "report": latest_report})
                else:
                    out = json.dumps({"status": "empty", "message": "No overnight intelligence report generated yet."})
            elif name == "manage_interest_topics":
                from idle_scout import idle_scout
                action = args.get("action", "list")
                if action == "add":
                    t = idle_scout.add_interest_topic(args.get("topic", ""), args.get("category", "tech"))
                    out = json.dumps({"status": "added", "topic": t.model_dump()})
                elif action == "delete":
                    succ = idle_scout.delete_interest_topic(args.get("topic_id", 0))
                    out = json.dumps({"status": "deleted" if succ else "not_found"})
                else:
                    topics = [t.model_dump() for t in idle_scout.get_interest_topics()]
                    out = json.dumps({"status": "success", "topics": topics})
            elif name == "get_privacy_status":
                from privacy_guard import privacy_guard
                summary = privacy_guard.get_status_summary()
                out = json.dumps(summary)
            elif name == "update_privacy_guard":
                from privacy_guard import privacy_guard
                kw_to_add = args.get("add_blocked_keyword")
                current_kw = list(privacy_guard.get_settings().blocked_keywords)
                if kw_to_add and kw_to_add not in current_kw:
                    current_kw.append(kw_to_add)
                updated = privacy_guard.update_settings(
                    strict_mode=args.get("strict_mode"),
                    blocked_keywords=current_kw if kw_to_add else None,
                )
                out = json.dumps({"status": "updated", "settings": updated.model_dump()})
            elif name == "learn_language_phrase":
                from language_learner import language_learner
                p = language_learner.learn_phrase(
                    word_or_phrase=args.get("word_or_phrase", ""),
                    language=args.get("language", "bangla"),
                    meaning=args.get("meaning", ""),
                    phonetic_script=args.get("phonetic_script"),
                    usage_example=args.get("usage_example"),
                    confidence=args.get("confidence", 0.85),
                    source="dialogue_learning",
                )
                language_learner.sync_to_vault()
                out = json.dumps({"status": "learned", "phrase": p.model_dump()})
            elif name == "query_learned_language":
                from language_learner import language_learner
                phrases = [p.model_dump() for p in language_learner.search_vocabulary(
                    query=args.get("query", ""),
                    limit=20,
                )] if args.get("query") else [p.model_dump() for p in language_learner.get_vocabulary(
                    language=args.get("language"),
                    limit=30,
                )]
                out = json.dumps({"status": "success", "results": phrases, "count": len(phrases)})
            elif name == "get_language_stats":
                from language_learner import language_learner
                stats = language_learner.get_learning_stats()
                out = json.dumps({"status": "success", "stats": stats})
            elif name == "get_hardware_status":
                from hardware_governor import hardware_governor
                status = hardware_governor.get_hardware_telemetry()
                out = json.dumps({"status": "success", "hardware": status.model_dump()})
            elif name == "get_cost_governor_metrics":
                from hardware_governor import hardware_governor
                metrics = hardware_governor.get_daily_cost_summary()
                out = json.dumps({"status": "success", "metrics": metrics})
            elif name == "update_cost_governor_settings":
                from hardware_governor import hardware_governor
                updated = hardware_governor.update_settings(
                    daily_budget_usd=args.get("daily_budget_usd"),
                    prefer_local_first=args.get("prefer_local_when_feasible"),
                    hard_cap_enabled=args.get("hard_cap_enforced"),
                )
                out = json.dumps({"status": "updated", "settings": updated.model_dump()})
            elif name == "adjust_master_volume":
                from hardware_governor import hardware_governor
                res = hardware_governor.adjust_master_volume(
                    action=args.get("action", "up"),
                    steps=args.get("steps", 2)
                )
                out = json.dumps(res)
            elif name == "get_screen_brightness":
                from hardware_governor import hardware_governor
                res = hardware_governor.get_screen_brightness()
                out = json.dumps(res)
            elif name == "set_screen_brightness":
                from hardware_governor import hardware_governor
                res = hardware_governor.set_screen_brightness(
                    level_percent=args.get("level_percent", 50)
                )
                out = json.dumps(res)
            elif name == "get_default_browser":
                from hardware_governor import hardware_governor
                res = hardware_governor.get_default_browser()
                out = json.dumps(res)
            elif name == "get_wifi_status":
                from hardware_governor import hardware_governor
                res = hardware_governor.get_wifi_status()
                out = json.dumps(res)
            elif name == "adb_get_devices":
                from tools.adb_tool import adb_bridge
                res = adb_bridge.get_devices()
                out = json.dumps(res)
            elif name == "adb_get_battery":
                from tools.adb_tool import adb_bridge
                res = adb_bridge.get_battery(device_id=args.get("device_id"))
                out = json.dumps(res)
            elif name == "adb_tap":
                from tools.adb_tool import adb_bridge
                res = adb_bridge.tap(x=args.get("x", 0), y=args.get("y", 0), device_id=args.get("device_id"))
                out = json.dumps(res)
            elif name == "adb_swipe":
                from tools.adb_tool import adb_bridge
                res = adb_bridge.swipe(
                    x1=args.get("x1", 0), y1=args.get("y1", 0),
                    x2=args.get("x2", 0), y2=args.get("y2", 0),
                    duration_ms=args.get("duration_ms", 300),
                    device_id=args.get("device_id")
                )
                out = json.dumps(res)
            elif name == "adb_launch_app":
                from tools.adb_tool import adb_bridge
                res = adb_bridge.launch_app(package_name=args.get("package_name", ""), device_id=args.get("device_id"))
                out = json.dumps(res)
            elif name == "os_list_windows":
                from mark_liv import mark_liv_engine
                wins = mark_liv_engine.list_windows(visible_only=args.get("visible_only", True))
                out = json.dumps({"status": "success", "windows": [w.model_dump() for w in wins], "count": len(wins)})
            elif name == "os_focus_window":
                from mark_liv import mark_liv_engine
                succ = mark_liv_engine.focus_window(args.get("target", ""))
                out = json.dumps({"status": "success" if succ else "not_found", "target": args.get("target")})
            elif name == "os_launch_app":
                from mark_liv import mark_liv_engine
                res = mark_liv_engine.launch_application(
                    command_or_path=args.get("command", ""),
                    args=args.get("args"),
                )
                out = json.dumps(res)
            elif name == "os_execute_action":
                from mark_liv import mark_liv_engine
                res = mark_liv_engine.execute_action_step(
                    action=args.get("action", ""),
                    target=args.get("target"),
                    x=args.get("x"),
                    y=args.get("y"),
                    text=args.get("text"),
                    keys=args.get("keys"),
                    session_id=session_id,
                )
                out = json.dumps(res)
            elif name == "os_list_processes":
                from mark_liv import mark_liv_engine
                procs = mark_liv_engine.list_processes(
                    filter_name=args.get("filter_name"),
                    limit=args.get("limit", 25),
                )
                out = json.dumps({"status": "success", "processes": procs, "count": len(procs)})
            elif name == "crystallize_skill":
                from second_brain import second_brain_engine
                sk = second_brain_engine.crystallize_skill(
                    name=args.get("name", ""),
                    description=args.get("description", ""),
                    steps=args.get("steps", []),
                    trigger_keywords=args.get("trigger_keywords"),
                    preconditions=args.get("preconditions"),
                    sync_vault=True,
                )
                second_brain_engine.sync_skills_moc()
                out = json.dumps({"status": "crystallized", "skill": sk.model_dump()})
            elif name == "recall_skill":
                from second_brain import second_brain_engine
                matched = second_brain_engine.recall_skill(args.get("query", ""))
                out = json.dumps({"status": "success", "skills": [s.model_dump() for s in matched], "count": len(matched)})
            elif name == "record_error_reflexion":
                from second_brain import second_brain_engine
                ref = second_brain_engine.record_error_reflexion(
                    failed_tool=args.get("failed_tool", ""),
                    error_message=args.get("error_message", ""),
                    root_cause=args.get("root_cause", ""),
                    corrective_rule=args.get("corrective_rule", ""),
                    session_id=session_id,
                )
                out = json.dumps({"status": "recorded", "reflexion": ref.model_dump()})
            elif name == "list_learned_skills":
                from second_brain import second_brain_engine
                skills = second_brain_engine.list_skills(limit=args.get("limit", 50))
                out = json.dumps({"status": "success", "skills": [s.model_dump() for s in skills], "count": len(skills)})
            elif name == "sandbox_run_command":
                from workstation_sandbox import workstation_sandbox
                res = workstation_sandbox.execute_sandboxed_command(
                    command=args.get("command", ""),
                    cwd=args.get("cwd"),
                    timeout_seconds=args.get("timeout_seconds", 15)
                )
                out = json.dumps(res.model_dump())
            elif name == "sandbox_audit_command":
                from workstation_sandbox import workstation_sandbox
                audit = workstation_sandbox.audit_command(
                    command=args.get("command", ""),
                    working_dir=args.get("cwd")
                )
                out = json.dumps(audit.model_dump())
            elif name == "workstation_scaffold_project":
                from workstation_sandbox import workstation_sandbox
                res = workstation_sandbox.scaffold_project(
                    project_type=args.get("project_type", "python_service"),
                    target_dir=args.get("target_dir", ""),
                    project_name=args.get("project_name", ""),
                    description=args.get("description", "Workstation Generated Component")
                )
                out = json.dumps(res)
            elif name == "workstation_git_status":
                from workstation_sandbox import workstation_sandbox
                status = workstation_sandbox.get_git_hygiene(
                    repo_dir=args.get("repo_dir")
                )
                out = json.dumps(status.model_dump())
            elif name == "add_session_todo":
                from session_todos import session_todos
                todo = session_todos.add_todo(
                    session_id=session_id,
                    task_description=args.get("task", ""),
                    step_order=args.get("step_order")
                )
                out = json.dumps({"status": "created", "todo": todo.model_dump()})
            elif name == "update_session_todo":
                from session_todos import session_todos
                updated = session_todos.update_todo(
                    todo_id=args.get("todo_id"),
                    status=args.get("status", "in_progress"),
                    result_summary=args.get("result_summary")
                )
                out = json.dumps({"status": "updated", "todo": updated.model_dump() if updated else None})
            elif name == "list_session_todos":
                from session_todos import session_todos
                todos = session_todos.list_todos(
                    session_id=session_id,
                    status=args.get("status")
                )
                out = json.dumps({"status": "success", "todos": [t.model_dump() for t in todos], "count": len(todos)})
            elif name == "get_token_juice_stats":
                from token_juice import token_juice
                out = json.dumps(token_juice.get_stats())
            elif name == "send_remote_message":
                from multi_channel_uplink import multi_channel_uplink
                res = _run_async_safely(multi_channel_uplink.send_remote(
                    channel=args.get("channel", "webhook"),
                    target=args.get("target", ""),
                    text=args.get("text", ""),
                    title=args.get("title")
                ))
                out = json.dumps(res)
            elif name == "broadcast_remote_message":
                from multi_channel_uplink import multi_channel_uplink
                res = _run_async_safely(multi_channel_uplink.broadcast(
                    text=args.get("text", ""),
                    title=args.get("title")
                ))
                out = json.dumps(res)
            elif name == "get_remote_channel_status":
                from multi_channel_uplink import multi_channel_uplink
                res = multi_channel_uplink.get_channel_status()
                out = json.dumps(res)
            elif name == "agentshield_scan_text":
                from agent_shield import agent_shield
                scan_res = agent_shield.scan_inbound_content(text=args.get("text", ""), source=args.get("source", "external"))
                out = json.dumps(scan_res.model_dump())
            elif name == "agentshield_get_security_status":
                from agent_shield import agent_shield
                out = json.dumps(agent_shield.get_security_metrics())
            elif name == "agentshield_audit_tool_call":
                from agent_shield import agent_shield
                audit_res = agent_shield.audit_tool_call(
                    tool_name=args.get("tool_name", ""),
                    arguments=args.get("arguments", {}),
                    session_id=session_id,
                )
                out = json.dumps(audit_res)
            elif name == "browser_navigate":
                from browser_agent import browser_agent
                nav_res = _run_async_safely(browser_agent.navigate(
                    url=args.get("url", ""),
                    session_id=session_id,
                ))
                out = json.dumps(nav_res)
            elif name == "browser_get_dom":
                from browser_agent import browser_agent
                dom_res = browser_agent.get_dom(
                    filter_interactive=args.get("filter_interactive", True),
                    max_elements=args.get("max_elements", 80),
                    session_id=session_id,
                )
                out = json.dumps(dom_res)
            elif name == "browser_click_element":
                from browser_agent import browser_agent
                click_res = _run_async_safely(browser_agent.click_element(
                    element_index=args.get("element_index", 1),
                    session_id=session_id,
                ))
                out = json.dumps(click_res)
            elif name == "browser_type_element":
                from browser_agent import browser_agent
                type_res = _run_async_safely(browser_agent.type_element(
                    element_index=args.get("element_index", 1),
                    text=args.get("text", ""),
                    submit=args.get("submit", False),
                    session_id=session_id,
                ))
                out = json.dumps(type_res)
            elif name == "browser_extract_text":
                from browser_agent import browser_agent
                text_res = browser_agent.extract_text(
                    session_id=session_id,
                    max_chars=args.get("max_chars", 5000),
                )
                out = json.dumps(text_res)
            elif name == "browser_manage_session":
                from browser_agent import browser_agent
                sess_res = browser_agent.manage_session(
                    action=args.get("action", "list_tabs"),
                    tab_id=args.get("tab_id"),
                    session_id=session_id,
                )
                out = json.dumps(sess_res)
            elif name == "laya_decide_browsing_action":
                from browser_agent import browser_agent
                action_res = browser_agent.laya_decide_action(
                    objective=args.get("objective", ""),
                    session_id=session_id,
                )
                out = json.dumps(action_res)
            elif name == "laya_verify_browsing_content":
                from browser_agent import browser_agent
                verif_res = browser_agent.laya_verify_page(
                    objective=args.get("objective", ""),
                    session_id=session_id,
                )
                out = json.dumps(verif_res)
            elif name == "scan_directory":
                from file_organizer import file_organizer
                scan_res = file_organizer.scan_directory(
                    directory_path=args.get("directory_path", ""),
                )
                out = json.dumps(scan_res.model_dump())
            elif name == "organize_directory":
                from file_organizer import file_organizer
                org_res = file_organizer.organize_directory(
                    directory_path=args.get("directory_path", ""),
                    dry_run=args.get("dry_run", False),
                )
                out = json.dumps(org_res.model_dump())
            elif name == "undo_organization":
                from file_organizer import file_organizer
                undo_res = file_organizer.undo_organization(
                    batch_id=args.get("batch_id", ""),
                )
                out = json.dumps(undo_res)
            # Office & Spreadsheet Harness
            elif name == "office_create_workbook":
                from office_harness import office_harness
                wb = office_harness.create_workbook(
                    title=args.get("title", "New Workbook"),
                    description=args.get("description"),
                    initial_sheet_names=args.get("sheet_names"),
                )
                out = json.dumps({"status": "created", "workbook": wb.model_dump()})
            elif name == "office_read_sheet":
                from office_harness import office_harness
                sheet_res = office_harness.read_sheet_grid(
                    sheet_id=args.get("sheet_id", ""),
                    range_str=args.get("range_str"),
                )
                out = json.dumps(sheet_res)
            elif name == "office_edit_cells":
                from office_harness import office_harness
                updates = args.get("cell_updates", {})
                if isinstance(updates, str):
                    try:
                        updates = json.loads(updates)
                    except Exception:
                        updates = {}
                edit_res = office_harness.update_cells(
                    sheet_id=args.get("sheet_id", ""),
                    cell_updates=updates,
                    author="assistant",
                )
                out = json.dumps(edit_res)
            elif name == "office_rollback_revision":
                from office_harness import office_harness
                rb_res = office_harness.rollback_revision(
                    sheet_id=args.get("sheet_id", ""),
                    revision_id=args.get("revision_id", ""),
                )
                out = json.dumps(rb_res)
            elif name == "office_export_markdown":
                from office_harness import office_harness
                md = office_harness.export_markdown_table(
                    sheet_id=args.get("sheet_id", ""),
                    range_str=args.get("range_str"),
                    save_to_vault=args.get("save_to_vault", False),
                    vault_note_name=args.get("vault_note_name"),
                )
                out = json.dumps({"status": "exported", "markdown_table": md})
            elif name == "office_import_csv":
                from office_harness import office_harness
                imp_res = office_harness.import_csv(
                    sheet_id=args.get("sheet_id", ""),
                    csv_text_or_path=args.get("csv_data", ""),
                )
                out = json.dumps(imp_res)
            # Executive Work Guide & Task Director
            elif name == "work_decompose_goal":
                from work_guide import work_guide
                proj = work_guide.decompose_goal(
                    goal=args.get("goal", ""),
                    category=args.get("category", "general"),
                    description=args.get("description"),
                )
                out = json.dumps({"status": "decomposed", "project": proj.model_dump()})
            elif name == "work_get_next_action":
                from work_guide import work_guide
                next_act = work_guide.get_next_recommended_action()
                out = json.dumps(next_act)
            elif name == "work_update_action_status":
                from work_guide import work_guide
                upd_act = work_guide.update_action_status(
                    action_id=args.get("action_id", ""),
                    status=args.get("status", "completed"),
                    result_summary=args.get("result_summary"),
                )
                out = json.dumps(upd_act)
            elif name == "work_list_projects":
                from work_guide import work_guide
                projs = [p.model_dump() for p in work_guide.list_projects(status=args.get("status"))]
                out = json.dumps({"status": "success", "projects": projs, "total": len(projs)})
            elif name == "set_cognitive_persona":
                from cognitive_personas import cognitive_personas
                pers = cognitive_personas.set_active_persona(args.get("persona_key", "executive_assistant"))
                out = json.dumps({"status": "switched", "persona": pers.model_dump()})
            # Video & Meeting Intelligence Engine
            elif name == "video_inspect_file":
                from video_inspector import video_inspector
                res = video_inspector.inspect_video(args.get("video_path", ""))
                out = json.dumps(res)
            elif name == "video_extract_frames":
                from video_inspector import video_inspector
                res = video_inspector.extract_keyframes(
                    video_path=args.get("video_path", ""),
                    interval_seconds=float(args.get("interval_seconds", 10.0)),
                    max_frames=int(args.get("max_frames", 30))
                )
                out = json.dumps({"status": "success", "frames": res, "count": len(res)})
            elif name == "video_get_transcript":
                from video_inspector import video_inspector
                res = video_inspector.extract_audio_and_transcript(args.get("video_path", ""))
                out = json.dumps(res)
            elif name == "video_summarize_meeting":
                from video_inspector import video_inspector
                res = video_inspector.synthesize_meeting_summary(
                    video_path=args.get("video_path", ""),
                    title=args.get("title"),
                    interval_seconds=float(args.get("interval_seconds", 15.0))
                )
                out = json.dumps(res)
            # Conversation Tree & Presets Engine
            elif name == "tree_fork_branch":
                from conversation_tree import conversation_tree
                res = conversation_tree.fork_branch(
                    session_id=session_id,
                    fork_message_id=int(args.get("fork_message_id", 1)),
                    new_branch_name=args.get("new_branch_name", "Alternative Branch")
                )
                out = json.dumps(res)
            elif name == "tree_list_branches":
                from conversation_tree import conversation_tree
                res = conversation_tree.list_branches(session_id=session_id)
                out = json.dumps({"status": "success", "branches": res, "count": len(res)})
            elif name == "tree_switch_branch":
                from conversation_tree import conversation_tree
                success = conversation_tree.switch_branch(
                    session_id=session_id,
                    branch_id=args.get("branch_id", "")
                )
                out = json.dumps({"status": "switched" if success else "failed", "branch_id": args.get("branch_id")})
            elif name == "tree_save_preset":
                from conversation_tree import conversation_tree
                res = conversation_tree.save_preset(
                    preset_id=args.get("preset_id", ""),
                    name=args.get("name", ""),
                    model_alias=args.get("model_alias", "primary"),
                    temperature=float(args.get("temperature", 0.7)),
                    system_prompt=args.get("system_prompt"),
                    toolsets=args.get("toolsets"),
                    description=args.get("description")
                )
                out = json.dumps(res)
            elif name == "tree_load_preset":
                from conversation_tree import conversation_tree
                preset = conversation_tree.get_preset(args.get("preset_id", ""))
                out = json.dumps({"status": "success", "preset": preset} if preset else {"status": "not_found"})
            elif name == "tree_save_artifact":
                from conversation_tree import conversation_tree
                art = conversation_tree.save_artifact(
                    session_id=session_id,
                    branch_id=args.get("branch_id", ""),
                    title=args.get("title", "Artifact"),
                    artifact_type=args.get("artifact_type", "markdown"),
                    content=args.get("content", "")
                )
                out = json.dumps(art)
            # Archify Architecture & Verification Engine
            elif name == "archify_create_diagram":
                from archify_engine import archify_engine
                diag = archify_engine.generate_diagram(
                    title=args.get("title", "Architecture_Diagram"),
                    diagram_type=args.get("diagram_type", "system"),
                    description=args.get("description"),
                    raw_mermaid=args.get("mermaid_code"),
                )
                out = json.dumps({"status": "created", "diagram": diag})
            elif name == "archify_inspect_codebase":
                from archify_engine import archify_engine
                diag = archify_engine.inspect_codebase_architecture(
                    target_dir=args.get("target_dir"),
                )
                out = json.dumps({"status": "inspected", "diagram": diag})
            elif name == "archify_list_diagrams":
                from archify_engine import archify_engine
                diags = archify_engine.list_diagrams()
                out = json.dumps({"status": "success", "diagrams": diags, "count": len(diags)})
            # OpenMAIC Socratic Curriculum Engine
            elif name == "curriculum_create_topic":
                from socratic_curriculum import socratic_curriculum
                curr = socratic_curriculum.generate_curriculum(
                    topic=args.get("topic", ""),
                    category=args.get("category", "engineering"),
                    description=args.get("description"),
                )
                out = json.dumps({"status": "created", "curriculum": curr})
            elif name == "curriculum_get_drill":
                from socratic_curriculum import socratic_curriculum
                drill = socratic_curriculum.get_next_drill(curriculum_id=args.get("curriculum_id", ""))
                out = json.dumps({"status": "success", "drill": drill} if drill else {"status": "all_drills_completed"})
            elif name == "curriculum_submit_answer":
                from socratic_curriculum import socratic_curriculum
                res = socratic_curriculum.submit_drill_answer(
                    drill_id=args.get("drill_id", ""),
                    user_answer=args.get("answer", ""),
                )
                out = json.dumps(res)
            elif name == "curriculum_list_topics":
                from socratic_curriculum import socratic_curriculum
                topics = socratic_curriculum.list_curricula()
                out = json.dumps({"status": "success", "topics": topics, "count": len(topics)})
            # Voice Studio Engine
            elif name == "voice_studio_render_note":
                from voice_studio import voice_studio
                prod = voice_studio.synthesize_note_to_audio(
                    note_title_or_path=args.get("note_title", ""),
                    profile_id=args.get("profile_id", "host_maxim"),
                )
                out = json.dumps({"status": "rendered", "production": prod})
            elif name == "voice_studio_render_dialogue":
                from voice_studio import voice_studio
                prod = voice_studio.synthesize_dialogue(
                    script=args.get("script", []),
                    title=args.get("title", "Dialogue_Podcast"),
                )
                out = json.dumps({"status": "rendered", "production": prod})
            elif name == "voice_studio_list_profiles":
                from voice_studio import voice_studio
                profs = voice_studio.list_profiles()
                out = json.dumps({"status": "success", "profiles": profs, "count": len(profs)})
            # Scientific Research & Discovery Engine
            elif name == "science_search_arxiv":
                from scientific_skills import scientific_skills
                papers = scientific_skills.search_arxiv(
                    query=args.get("query", ""),
                    max_results=int(args.get("max_results", 5))
                )
                out = json.dumps({"status": "success", "papers": papers, "count": len(papers)})
            elif name == "science_search_pubmed":
                from scientific_skills import scientific_skills
                papers = scientific_skills.search_pubmed(
                    query=args.get("query", ""),
                    max_results=int(args.get("max_results", 5))
                )
                out = json.dumps({"status": "success", "papers": papers, "count": len(papers)})
            elif name == "science_lookup_compound":
                from scientific_skills import scientific_skills
                compound = scientific_skills.lookup_pubchem_compound(
                    compound_name=args.get("compound_name", "")
                )
                out = json.dumps({"status": "success", "compound": compound})
            elif name == "science_synthesize_literature_review":
                from scientific_skills import scientific_skills
                dossier = scientific_skills.synthesize_literature_review(
                    topic=args.get("topic", "")
                )
                out = json.dumps({"status": "synthesized", "dossier": dossier})
            # BrowserSkill CLI & Real-Session Browser Bridge
            elif name == "browserskill_get_active_tab":
                from browser_skill_bridge import browser_skill_bridge
                tab = browser_skill_bridge.get_active_browser_tab(test_mode=bool(args.get("test_mode", False)))
                out = json.dumps({"status": "success", "tab": tab})
            elif name == "browserskill_evaluate_script":
                from browser_skill_bridge import browser_skill_bridge
                res = browser_skill_bridge.evaluate_script(
                    script=args.get("script", ""),
                    tab_id=args.get("tab_id"),
                    test_mode=bool(args.get("test_mode", False))
                )
                out = json.dumps(res)
            elif name == "browserskill_execute_command":
                from browser_skill_bridge import browser_skill_bridge
                res = browser_skill_bridge.execute_browser_command(
                    action=args.get("action", "click"),
                    target=args.get("target", ""),
                    value=args.get("value"),
                    test_mode=bool(args.get("test_mode", False))
                )
                out = json.dumps(res)
            # Magnitude Hardware Profiler & Local Model Recommender
            elif name == "magnitude_profile_hardware":
                from magnitude_engine import magnitude_engine
                prof = magnitude_engine.profile_hardware()
                out = json.dumps({"status": "success", "profile": prof})
            elif name == "magnitude_benchmark_throughput":
                from magnitude_engine import magnitude_engine
                bench = magnitude_engine.benchmark_throughput(test_tokens=int(args.get("test_tokens", 100)))
                out = json.dumps(bench)
            elif name == "magnitude_get_profile":
                from magnitude_engine import magnitude_engine
                prof = magnitude_engine.get_latest_profile()
                out = json.dumps({"status": "success", "profile": prof})
            # Cursor Plugin Ecosystem
            elif name == "cursor_import_plugin":
                from cursor_plugins import cursor_plugins
                p_data = args.get("manifest_path_or_dict")
                if isinstance(p_data, str) and (p_data.strip().startswith("{") or p_data.strip().startswith("[")):
                    try:
                        p_data = json.loads(p_data)
                    except Exception:
                        pass
                res = cursor_plugins.import_plugin(p_data)
                out = json.dumps(res)
            elif name == "cursor_list_plugins":
                from cursor_plugins import cursor_plugins
                plugs = cursor_plugins.list_installed_plugins()
                out = json.dumps({"status": "success", "plugins": plugs, "count": len(plugs)})
            elif name == "cursor_toggle_plugin":
                from cursor_plugins import cursor_plugins
                ok = cursor_plugins.toggle_plugin(
                    plugin_id=args.get("plugin_id", ""),
                    enabled=bool(args.get("enabled", True))
                )
                out = json.dumps({"status": "success" if ok else "failed", "plugin_id": args.get("plugin_id"), "enabled": bool(args.get("enabled", True))})
            # OpenSEO Technical Visibility Engine
            elif name == "seo_audit_url":
                from open_seo import open_seo
                if args.get("html"):
                    res = open_seo.audit_html(args["html"], url=args.get("url", "https://example.com"))
                else:
                    res = open_seo.audit_url(args.get("url", "https://example.com"), test_mode=bool(args.get("test_mode", False)))
                out = json.dumps(res)
            elif name == "seo_analyze_keyword_density":
                from open_seo import open_seo
                res = open_seo.analyze_keyword_density(
                    text=args.get("text", ""),
                    target_keywords=args.get("target_keywords")
                )
                out = json.dumps(res)
            elif name == "seo_list_audits":
                from open_seo import open_seo
                audits = open_seo.list_audits()
                out = json.dumps({"status": "success", "audits": audits, "count": len(audits)})
            # Chief Agent Operator & Dynamic Group Orchestration
            elif name == "operator_assemble_dynamic_group":
                from chief_operator import agent_operator
                res = _run_async_safely(agent_operator.assemble_dynamic_group(
                    topic=args.get("topic", ""),
                    group_name=args.get("group_name"),
                    skills_requested=args.get("skills_requested"),
                    desktop_context=args.get("desktop_context"),
                    use_active_window=bool(args.get("use_active_window", False)),
                ))
                out = json.dumps(res)
            elif name == "operator_delete_group":
                from chief_operator import agent_operator
                succ = agent_operator.delete_group(args.get("group_id", ""))
                out = json.dumps({"status": "deleted" if succ else "not_found", "group_id": args.get("group_id")})
            elif name == "operator_dispatch_group_task":
                from chief_operator import agent_operator
                res = _run_async_safely(agent_operator.dispatch_group_task(
                    group_id=args.get("group_id", ""),
                    task_prompt=args.get("task_prompt", ""),
                    target_agent_ids=args.get("target_agent_ids"),
                    rounds=int(args.get("rounds", 1)),
                ))
                out = json.dumps(res)
            elif name == "operator_orchestrate_objective":
                from chief_operator import agent_operator
                res = _run_async_safely(agent_operator.orchestrate_objective(
                    objective=args.get("objective", ""),
                    preferred_category=args.get("preferred_category"),
                    rounds=int(args.get("rounds", 1)),
                    save_to_vault=bool(args.get("save_to_vault", True)),
                ))
                out = json.dumps(res)
            elif name == "operator_cross_group_handoff":
                from chief_operator import agent_operator
                res = _run_async_safely(agent_operator.cross_group_handoff(
                    source_group_id=args.get("source_group_id", ""),
                    target_group_id=args.get("target_group_id", ""),
                    deliverable_summary=args.get("deliverable_summary", ""),
                    next_step_instruction=args.get("next_step_instruction", ""),
                    rounds=int(args.get("rounds", 1)),
                ))
                out = json.dumps(res)
            elif name == "hire_operator_agent":
                from chief_operator import agent_operator
                m = agent_operator.hire_agent(
                    name=args.get("name", "Specialist"),
                    role=args.get("role", "Specialist"),
                    persona=args.get("persona", ""),
                    avatar=args.get("avatar", "Sparkles"),
                    toolsets=args.get("toolsets", ["vault"]),
                    skills=args.get("skills", []),
                    category=args.get("category"),
                )
                out = json.dumps({"status": "hired", "agent": m.model_dump()})
            elif name == "run_group_collaboration":
                from chief_operator import agent_operator
                res = _run_async_safely(agent_operator.run_group_chat(
                    group_id=args.get("group_id", ""),
                    user_message=args.get("message", ""),
                    rounds=int(args.get("rounds", 1)),
                ))
                out = json.dumps(res)
            elif name == "schedule_agent_shift":
                from chief_operator import agent_operator
                rep = _run_async_safely(agent_operator.execute_shift(
                    agent_id=args.get("agent_id", ""),
                    task=args.get("task", ""),
                    save_to_vault=True,
                ))
            elif name == "read_document":
                from document_reader import document_reader
                res = document_reader.read_document(
                    file_path_str=args.get("file_path", ""),
                    max_chars=int(args.get("max_chars", 15000)),
                )
                out = json.dumps(res)
            elif name == "inspect_image":
                from document_reader import document_reader
                res = _run_async_safely(document_reader.inspect_image(
                    image_path_str=args.get("image_path", ""),
                    prompt=args.get("prompt"),
                    auto_boot_local=True,
                ))
                out = json.dumps(res)
            else:
                is_ext_tool = False
                try:
                    from extensions.extension_manager import extension_manager
                    if extension_manager.has_tool(name):
                        res = extension_manager.execute_extension_tool(name, args, session_id=session_id)
                        out = json.dumps(res) if not isinstance(res, str) else res
                        is_ext_tool = True
                except Exception as ext_err:
                    out = json.dumps({"error": f"Extension tool '{name}' failed: {ext_err}"})
                    is_ext_tool = True

                if not is_ext_tool:
                    out = json.dumps({"error": f"Unknown tool: {name}"})

            # Record Meta Muse receipt with raw output
            self.memory.log_receipt(name, args, out, session_id=session_id)

            # TokenJuice Compression: compress tool output before passing to model context
            from token_juice import token_juice
            return token_juice.compress(out, tool_name=name)
        except Exception as e:
            err = json.dumps({"error": str(e)})
            self.memory.log_receipt(name, args, err, session_id=session_id)
            return err

    async def run_turn(
        self,
        user_message: str,
        session_id: str = "default_session",
        provider: Optional[ProviderType | str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a complete agentic conversational turn:
        1. Stores user turn.
        2. ReAct tool-execution loop.
        3. Stores assistant reply.
        4. Returns answer + receipts.
        """
        # Save user message
        self.memory.add_message(
            MessageRecord(session_id=session_id, role="user", content=user_message)
        )
        try:
            from idle_scout import idle_scout
            idle_scout.record_user_activity(user_message)
        except Exception:
            pass

        try:
            from language_learner import language_learner
            language_learner.ingest_spoken_utterance(user_message, source="chat_or_voice")
        except Exception:
            pass

        receipts_generated = []

        # Zylos 75% Context Safeguard Check
        safeguard_info = self.five_layer.check_context_safeguard(session_id)
        if safeguard_info.get("triggered", False):
            compaction_res = self.five_layer.execute_safeguard_compaction(
                session_id=session_id,
                reason=f"Auto-triggered: context capacity at {safeguard_info.get('capacity_percent')}%",
            )
            receipts_generated.append({
                "tool": "compact_context_safeguard",
                "args": {"trigger": "75%_threshold", "capacity_percent": safeguard_info.get("capacity_percent")},
                "output": json.dumps(compaction_res),
            })

        # Build prompt and history
        system_prompt = self.build_system_prompt(session_id=session_id)
        history = self.memory.get_messages(session_id, limit=30)

        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        for m in history:
            role = m.role
            content = m.content or ""
            # Guard against obsolete historical capability refusals acting as negative few-shot examples
            if role == "assistant" and any(ref in content.lower() for ref in ("can't generate image", "cannot generate image", "can’t generate image", "can't generate a pic", "cannot generate a pic", "can’t generate a pic")):
                continue
            if role == "system":
                role = "user"
                content = f"[System Context] {content}"
            msg_dict: Dict[str, Any] = {"role": role, "content": content}
            if m.tool_calls:
                try:
                    msg_dict["tool_calls"] = json.loads(m.tool_calls)
                except Exception:
                    pass
            messages.append(msg_dict)

        # Guarantee that the current user message is at the end of the context payload
        if not messages or messages[-1].get("role") != "user" or messages[-1].get("content") != user_message:
            messages.append({"role": "user", "content": user_message})

        q_lower = user_message.lower()
        is_image_intent = any(
            k in q_lower for k in (
                "generate image", "generating image", "create image", "creating image",
                "draw a", "draw ", "render image", "generate a picture", "create a picture",
                "make a picture", "make an image", "picture of a", "picture of", "photo of a",
                "photo of", "illustration of", "generate a pic", "create a pic", "make a pic", "paint a"
            )
        )

        iteration = 0
        active_tools = self.get_scoped_tools(provider=provider, model=model, query=user_message)

        while iteration < self.max_tool_iterations:
            iteration += 1
            if is_image_intent and iteration == 1 and any(t.get("function", {}).get("name") == "generate_image" for t in active_tools):
                current_tools = [t for t in active_tools if t.get("function", {}).get("name") == "generate_image"]
                tool_choice = "required"
            else:
                current_tools = active_tools
                tool_choice = "auto"

            response = await model_router.chat_completion(
                messages=messages,
                tools=current_tools,
                provider=provider,
                model=model,
                tool_choice=tool_choice,
            )

            # Record token usage in cost governor if available
            if hasattr(response, "usage") and response.usage:
                try:
                    from hardware_governor import hardware_governor
                    hardware_governor.record_usage(
                        provider=str(provider or model_router.active_provider),
                        model=str(model or getattr(response, "model", "default")),
                        input_tokens=getattr(response.usage, "prompt_tokens", 0),
                        output_tokens=getattr(response.usage, "completion_tokens", 0),
                        session_id=session_id,
                    )
                except Exception:
                    pass

            choice = response.choices[0]
            message_obj = choice.message

            # Check if model wants to call tools
            if message_obj.tool_calls:
                # Append assistant tool call message to turn history
                tool_calls_json = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message_obj.tool_calls
                ]
                messages.append({
                    "role": "assistant",
                    "content": message_obj.content or "",
                    "tool_calls": tool_calls_json,
                })

                # Execute each tool
                for tc in message_obj.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except Exception:
                        fn_args = {}

                    tool_output = self.execute_tool(fn_name, fn_args, session_id)
                    receipts_generated.append({"tool": fn_name, "args": fn_args, "output": tool_output})

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fn_name,
                        "content": tool_output,
                    })
            else:
                # Final response generated
                final_text = message_obj.content or getattr(message_obj, "reasoning_content", None) or ""
                self.memory.add_message(
                    MessageRecord(session_id=session_id, role="assistant", content=final_text)
                )
                return {
                    "session_id": session_id,
                    "response": final_text,
                    "receipts": receipts_generated,
                    "iterations": iteration,
                }

        fallback_text = "I executed the requested tools, but reached the maximum execution budget for this turn."
        self.memory.add_message(
            MessageRecord(session_id=session_id, role="assistant", content=fallback_text)
        )
        return {
            "session_id": session_id,
            "response": fallback_text,
            "receipts": receipts_generated,
            "iterations": iteration,
        }

    async def run(
        self,
        prompt: str,
        session_id: str = "default_session",
        provider: Optional[ProviderType | str] = None,
        model: Optional[str] = None,
    ) -> str:
        """Convenience execution method returning text answer."""
        res = await self.run_turn(
            user_message=prompt,
            session_id=session_id,
            provider=provider,
            model=model,
        )
        return res["response"]

    async def run_turn_stream(
        self,
        user_message: str,
        session_id: str = "default_session",
        provider: Optional[ProviderType | str] = None,
        model: Optional[str] = None,
    ):
        """
        Executes turn and yields SSE event dictionaries.
        """
        # Save user message
        self.memory.add_message(
            MessageRecord(session_id=session_id, role="user", content=user_message)
        )
        try:
            from idle_scout import idle_scout
            idle_scout.record_user_activity(user_message)
        except Exception:
            pass

        try:
            from language_learner import language_learner
            language_learner.ingest_spoken_utterance(user_message, source="chat_or_voice")
        except Exception:
            pass
        yield {"type": "session", "session_id": session_id}

        # Zylos 75% Context Safeguard Check
        safeguard_info = self.five_layer.check_context_safeguard(session_id)
        if safeguard_info.get("triggered", False):
            compaction_res = self.five_layer.execute_safeguard_compaction(
                session_id=session_id,
                reason=f"Auto-triggered: context capacity at {safeguard_info.get('capacity_percent')}%",
            )
            yield {
                "type": "receipt",
                "tool": "compact_context_safeguard",
                "args": {"trigger": "75%_threshold", "capacity_percent": safeguard_info.get("capacity_percent")},
                "output": json.dumps(compaction_res),
            }

        # Build prompt and history
        system_prompt = self.build_system_prompt(session_id=session_id)
        history = self.memory.get_messages(session_id, limit=30)

        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        for m in history:
            role = m.role
            content = m.content or ""
            # Guard against obsolete historical capability refusals acting as negative few-shot examples
            if role == "assistant" and any(ref in content.lower() for ref in ("can't generate image", "cannot generate image", "can’t generate image", "can't generate a pic", "cannot generate a pic", "can’t generate a pic")):
                continue
            if role == "system":
                role = "user"
                content = f"[System Context] {content}"
            msg_dict: Dict[str, Any] = {"role": role, "content": content}
            if m.tool_calls:
                try:
                    msg_dict["tool_calls"] = json.loads(m.tool_calls)
                except Exception:
                    pass
            messages.append(msg_dict)

        # Guarantee that the current user message is at the end of the context payload
        if not messages or messages[-1].get("role") != "user" or messages[-1].get("content") != user_message:
            messages.append({"role": "user", "content": user_message})

        q_lower = user_message.lower()
        is_image_intent = any(
            k in q_lower for k in (
                "generate image", "generating image", "create image", "creating image",
                "draw a", "draw ", "render image", "generate a picture", "create a picture",
                "make a picture", "make an image", "picture of a", "picture of", "photo of a",
                "photo of", "illustration of", "generate a pic", "create a pic", "make a pic", "paint a"
            )
        )

        iteration = 0
        active_tools = self.get_scoped_tools(provider=provider, model=model, query=user_message)

        while iteration < self.max_tool_iterations:
            iteration += 1
            yield {"type": "status", "message": f"Reasoning cycle {iteration}..."}

            accumulated_content = ""
            tool_calls_dict = {}

            if is_image_intent and iteration == 1 and any(t.get("function", {}).get("name") == "generate_image" for t in active_tools):
                current_tools = [t for t in active_tools if t.get("function", {}).get("name") == "generate_image"]
                tool_choice = "required"
            else:
                current_tools = active_tools
                tool_choice = "auto"

            async for chunk in model_router.stream_chat_completion(
                messages=messages,
                tools=current_tools,
                provider=provider,
                model=model,
                tool_choice=tool_choice,
            ):
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta.content:
                    accumulated_content += delta.content
                    yield {"type": "content", "content": delta.content}

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index if tc.index is not None else 0
                        if idx not in tool_calls_dict:
                            tool_calls_dict[idx] = {
                                "id": tc.id or f"call_{idx}_{int(time.time()*1000)}",
                                "name": "",
                                "arguments": "",
                            }
                        if tc.id:
                            tool_calls_dict[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_dict[idx]["name"] += tc.function.name
                            if tc.function.arguments:
                                tool_calls_dict[idx]["arguments"] += tc.function.arguments

            if tool_calls_dict:
                tool_calls_list = list(tool_calls_dict.values())
                tool_calls_json = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments"],
                        },
                    }
                    for tc in tool_calls_list
                ]
                messages.append({
                    "role": "assistant",
                    "content": accumulated_content or None,
                    "tool_calls": tool_calls_json,
                })

                for tc in tool_calls_list:
                    fn_name = tc["name"]
                    try:
                        fn_args = json.loads(tc["arguments"])
                    except Exception:
                        fn_args = {}

                    yield {"type": "tool_call", "tool": fn_name, "args": fn_args}
                    tool_output = self.execute_tool(fn_name, fn_args, session_id)
                    yield {"type": "tool_result", "tool": fn_name, "output": tool_output}

                    if fn_name == "generate_image":
                        try:
                            parsed_img = json.loads(tool_output)
                            img_url = parsed_img.get("image_url") or parsed_img.get("direct_url")
                            if img_url:
                                yield {"type": "image", "url": img_url, "prompt": fn_args.get("prompt", "")}
                        except Exception:
                            pass

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": fn_name,
                        "content": tool_output,
                    })
            else:
                self.memory.add_message(
                    MessageRecord(session_id=session_id, role="assistant", content=accumulated_content)
                )
                yield {"type": "done", "session_id": session_id, "iterations": iteration}
                return

        fallback_text = "I executed the requested tools, but reached the maximum execution budget for this turn."
        self.memory.add_message(
            MessageRecord(session_id=session_id, role="assistant", content=fallback_text)
        )
        yield {"type": "content", "content": fallback_text}
        yield {"type": "done", "session_id": session_id, "iterations": iteration}

# Aliases and singleton
AutonomousReActEngine = MaxIMAgentEngine
agent_engine = MaxIMAgentEngine()

