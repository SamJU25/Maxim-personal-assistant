"""
Hermes-Inspired Modular Toolset Catalog for MaxIM.
Organizes built-in tools, MCP bridges, and subagent delegation into toggleable bundles.
Repository reference: https://github.com/NousResearch/hermes-agent
"""
from enum import Enum
from typing import Dict, List, Any, Optional

class ToolsetName(str, Enum):
    VAULT = "vault"
    PERCEPTION = "perception"
    CUA = "cua"
    MEMORY = "memory"
    DELEGATION = "delegation"
    MCP = "mcp"
    REACH = "reach"
    OPERATOR = "operator"
    SCOUT = "scout"
    SECURITY = "security"
    LANGUAGE = "language"
    GOVERNOR = "governor"
    OS = "os"
    SKILLS = "skills"
    SANDBOX = "sandbox"
    TODOS = "todos"
    MOBILE_ADB = "mobile_adb"
    UPLINK = "uplink"
    BROWSER = "browser"
    FILES = "files"
    OFFICE = "office"
    WORK_GUIDE = "work_guide"
    VIDEO = "video"
    CONVERSATION_TREE = "conversation_tree"
    ARCHIFY = "archify"
    CURRICULUM = "curriculum"
    VOICE_STUDIO = "voice_studio"
    SCIENCE = "science"
    BROWSER_SKILL = "browser_skill"
    MAGNITUDE = "magnitude"
    CURSOR_PLUGINS = "cursor_plugins"
    SEO = "seo"
    MEDIA = "media"

# Individual Tool Definitions
VAULT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_vault_note",
            "description": "Reads the markdown contents and frontmatter of a note from the Obsidian vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The title or relative path of the note."}
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_vault_note",
            "description": "Creates or updates a note in the Obsidian vault with tags and wikilinks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the note."},
                    "content": {"type": "string", "description": "Markdown body content."},
                    "folder": {"type": "string", "description": "Target folder in vault, default '01 - Memory'."},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tags (e.g. ['#lifeos', '#project']).",
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
]

PERCEPTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "inspect_screen",
            "description": "Inspects the user's active application window and captures a real-time screenshot.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

CUA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "cua_click",
            "description": "Clicks an element, link, or coordinate in the background using Cua driver without stealing mouse cursor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_name_or_selector": {"type": "string", "description": "Accessible name or selector to click."},
                    "x": {"type": "integer", "description": "Optional X coordinate."},
                    "y": {"type": "integer", "description": "Optional Y coordinate."},
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
                    "element_name": {"type": "string", "description": "Optional target input element name."},
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
                    "url": {"type": "string", "description": "Web URL to navigate to."}
                },
                "required": ["url"],
            },
        },
    },
]

MEMORY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "remember_user_fact",
            "description": "Permanently saves a fact, preference, or rule about the user in the SQLite memory tree.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Category: 'preference', 'habit', 'project', or 'rule'."},
                    "key": {"type": "string", "description": "Unique key (e.g. 'ui_theme')."},
                    "value": {"type": "string", "description": "The fact or preference to remember."},
                },
                "required": ["category", "key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_five_layer_memory",
            "description": "Performs integrated BM25 search across all 5 Zylos memory layers (Identity, State, Obsidian References, Session History, and Long-term Archive).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keyword, phrase, or topic to search across memory layers."},
                    "limit": {"type": "integer", "description": "Maximum number of results to return (default 5)."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compact_context_safeguard",
            "description": "Triggers Zylos 75% Context Safeguard compaction to synthesize active session turns into an episodic checkpoint note in vault/01 - Memory/ and stabilize working context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Reason for triggering compaction (default 'Manual or agent-requested compaction')."}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retain_memory",
            "description": "Retains an observation, fact, rule, or preference in MaxIM's Hindsight memory engine with epistemic category (world, experience, opinion, observation) and provenance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "The information, observation, rule, or preference to retain."},
                    "category": {"type": "string", "description": "Epistemic category: 'observation', 'experience', 'opinion', 'preference', or 'world'."},
                    "source": {"type": "string", "description": "Source or origin of this memory (e.g. 'user_interaction', 'tool_output')."},
                    "metadata": {"type": "object", "description": "Optional metadata dictionary (e.g. {'name': 'custom_key', 'confidence': 0.8})."},
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memory",
            "description": "Performs unified Hindsight epistemic retrieval across mental models, observations, session history, and Obsidian vault notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Topic, question, or keyword to retrieve memory for."},
                    "top_k": {"type": "integer", "description": "Maximum number of results per category to return (default 5)."},
                    "include_mental_models": {"type": "boolean", "description": "Whether to include high-level synthesized mental models (default true)."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reflect_mental_models",
            "description": "Triggers reflective synthesis over observations and experiences to form or update high-level mental models and user heuristics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Focus topic or theme for reflection (default 'general')."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_mental_models",
            "description": "Retrieves active synthesized mental models and user behavioral dispositions filtered by minimum confidence threshold.",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_confidence": {"type": "number", "description": "Minimum confidence filter between 0.0 and 1.0 (default 0.0)."},
                    "limit": {"type": "integer", "description": "Maximum number of mental models to return (default 10)."},
                },
            },
        },
    },
]

DELEGATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_subagent",
            "description": "Spawns an isolated sub-agent child worker with a specific role, task, and tool whitelist. Returns structured synthesis and execution receipts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The dedicated goal or task for the sub-agent to execute."},
                    "role": {"type": "string", "description": "Specialist persona (e.g., 'Vault Researcher', 'Code Auditor', 'Screen Analyst')."},
                    "toolset": {"type": "string", "description": "Allowed toolset: 'vault', 'perception', 'cua', or 'all' (default 'vault')."},
                    "max_iterations": {"type": "integer", "description": "Maximum execution budget steps (default 4)."}
                },
                "required": ["task"],
            },
        },
    },
]

MCP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "call_mcp_tool",
            "description": "Executes a tool on a connected Model Context Protocol (MCP) server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_name": {"type": "string", "description": "Name of the registered MCP server."},
                    "tool_name": {"type": "string", "description": "Name of the tool to execute."},
                    "arguments": {"type": "object", "description": "JSON arguments matching tool schema."}
                },
                "required": ["server_name", "tool_name", "arguments"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp_search_registry",
            "description": "Searches Smithery, Glama, and official MCP registries for Model Context Protocol servers by keyword or category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword or capability (e.g., 'postgres', 'docker', 'browser', 'github')."},
                    "registry": {"type": "string", "description": "Target registry filter: 'all', 'official', 'smithery', or 'glama' (default 'all')."},
                    "limit": {"type": "integer", "description": "Maximum number of results to return (default 10)."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp_inspect_server",
            "description": "Retrieves the full manifest, required environment variables, and installation commands for an MCP server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "ID, name, or package identifier of the MCP server (e.g. 'postgres', 'github', 'filesystem')."}
                },
                "required": ["server_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp_install_server",
            "description": "Mounts and registers an MCP server into MaxIM's persistent SQLite registry so its tools become available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Unique identifier for this server mount."},
                    "command": {"type": "string", "description": "Executable command (e.g. 'npx', 'uvx', 'docker')."},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Command line arguments."},
                    "transport": {"type": "string", "description": "'stdio' or 'sse' (default 'stdio')."},
                    "env": {"type": "object", "description": "Optional environment variables dictionary."},
                    "description": {"type": "string", "description": "Brief description of this server's capabilities."}
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp_list_servers",
            "description": "Lists all currently mounted and active MCP servers in MaxIM.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp_remove_server",
            "description": "Unmounts and removes a registered MCP server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the MCP server to remove."}
                },
                "required": ["name"],
            },
        },
    },
]

REACH_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_web_page",
            "description": "Reads and extracts clean, LLM-ready markdown from any public web page URL using Jina Reader.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The web URL to fetch and convert to markdown (e.g. 'https://en.wikipedia.org/wiki/Artificial_intelligence')."},
                    "max_chars": {"type": "integer", "description": "Maximum character budget (default 10000)."}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Searches the live internet for up-to-date facts, documentation, news, or articles using DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query keywords or phrase."},
                    "limit": {"type": "integer", "description": "Number of results to return (default 5)."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_reach",
            "description": "Inspects a public GitHub repository, fetching stars, description, latest activity, or README markdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository in 'owner/name' format (e.g. 'Panniantong/Agent-Reach')."},
                    "action": {"type": "string", "description": "'summary' (default) or 'readme'."}
                },
                "required": ["repo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "community_reach",
            "description": "Inspects trending developer and tech discussions from V2EX or Hacker News.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Community source: 'v2ex' (default) or 'hackernews'."},
                    "limit": {"type": "integer", "description": "Number of topics to retrieve (default 5)."}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reach_doctor",
            "description": "Runs connectivity diagnostics across all Agent Reach internet access channels (Jina, Web Search, GitHub, Community).",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

OPERATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_agent_team",
            "description": "Lists all hired agent teammates in the Chief Agent Operator's AI team, including their roles, personas, assigned toolsets, and status.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hire_agent_teammate",
            "description": "Hires a new specialized agent teammate with a custom role, persona, avatar, and assigned toolsets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Display name of the new agent."},
                    "role": {"type": "string", "description": "Domain specialty role (e.g. 'Security Auditor')."},
                    "persona": {"type": "string", "description": "Core operating directives and personality."},
                    "avatar": {"type": "string", "description": "Avatar icon name (default 'Sparkles')."},
                    "toolsets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Assigned toolset bundles: 'vault', 'reach', 'memory', 'perception', 'cua'."
                    },
                    "skills": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Assigned specialized skills from catalog (e.g. ['copywriting', 'claude-seo'])."
                    },
                    "category": {
                        "type": "string",
                        "description": "Primary domain category (e.g. 'marketing', 'web-development', 'testing', 'security')."
                    }
                },
                "required": ["name", "role", "persona"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_group_collaboration",
            "description": "Orchestrates multi-agent collaborative turn-taking discussion in an agent group.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_id": {"type": "string", "description": "Target collaboration group ID (e.g. 'group_marketing', 'group_core_council')."},
                    "message": {"type": "string", "description": "Discussion prompt or task for the agent team."},
                    "rounds": {"type": "integer", "description": "Number of discussion rounds (default 1)."}
                },
                "required": ["group_id", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "operator_dispatch_group_task",
            "description": "MaxIM administrative directive dispatch: MaxIM issues a task brief into a specific group channel, moderates specialist turn-taking, and provides executive sign-off.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_id": {"type": "string", "description": "Target group ID (e.g. 'group_marketing', 'group_web_dev', 'group_qa_testing')."},
                    "task_prompt": {"type": "string", "description": "Administrative directive or task description."},
                    "target_agent_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional subset of specific agent IDs to invoke."
                    },
                    "rounds": {"type": "integer", "description": "Number of collaboration rounds (default 1)."}
                },
                "required": ["group_id", "task_prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "operator_orchestrate_objective",
            "description": "Autonomous MaxIM Master Conductor: analyzes high-level objective, selects the optimal categorized channel, dispatches the task, and logs an executive report to the Obsidian vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "objective": {"type": "string", "description": "High-level goal or mission to orchestrate."},
                    "preferred_category": {"type": "string", "description": "Optional category hint ('marketing', 'web-development', 'testing', 'backend', 'security', 'agents')."},
                    "rounds": {"type": "integer", "description": "Number of discussion rounds (default 1)."}
                },
                "required": ["objective"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "operator_cross_group_handoff",
            "description": "MaxIM bridges work from one specialized group channel to another, transferring deliverables and next-step instructions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_group_id": {"type": "string", "description": "Source group ID where work originated."},
                    "target_group_id": {"type": "string", "description": "Target group ID to receive the handoff."},
                    "deliverable_summary": {"type": "string", "description": "Summary of completed deliverable."},
                    "next_step_instruction": {"type": "string", "description": "Instruction for the receiving team."}
                },
                "required": ["source_group_id", "target_group_id", "deliverable_summary", "next_step_instruction"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_agent_shift",
            "description": "Dispatches an autonomous background shift mission for an agent and logs an executive summary to the vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Target agent ID (e.g. 'agent_hermes')."},
                    "task": {"type": "string", "description": "Shift objective or mission."}
                },
                "required": ["agent_id", "task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "operator_assemble_dynamic_group",
            "description": "Dynamically assembles an ad-hoc collaboration group on demand based on the user's project objective, requested skills, or active desktop window context without using preselected dummy groups.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Project objective or topic for the ad-hoc group (e.g. 'YouTube scriptwriting', 'FastAPI security audit')."},
                    "group_name": {"type": "string", "description": "Optional custom display name for the group."},
                    "skills_requested": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of specialized skills from the catalog (e.g. ['copywriting', 'claude-seo'])."
                    },
                    "desktop_context": {"type": "string", "description": "Optional active application or desktop context description."},
                    "use_active_window": {"type": "boolean", "description": "If true, automatically inspects the currently focused foreground window on the desktop to guide agent selection."}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "operator_delete_group",
            "description": "Deletes an ad-hoc collaboration group and removes its message history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_id": {"type": "string", "description": "Group ID to delete."}
                },
                "required": ["group_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_proactive_initiative",
            "description": "Evaluates user's foreground window, TELOS targets, and focus rhythm to formulate a non-robotic proactive question or thought.",
            "parameters": {
                "type": "object",
                "properties": {
                    "force": {"type": "boolean", "description": "Whether to bypass cooldown and force evaluation."}
                },
                "required": [],
            },
        },
    },
]

SCOUT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "trigger_idle_scout",
            "description": "Triggers an autonomous overnight & idle intelligence scout cycle to collect news, breakthroughs, and project ideas based on user interests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "trigger_type": {"type": "string", "enum": ["manual", "idle", "sleep"], "description": "Trigger category."},
                    "force": {"type": "boolean", "description": "Whether to bypass idle threshold/cooldown checks."}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_overnight_intel",
            "description": "Retrieves the latest overnight/idle intelligence briefing and curated news discovered while the user was asleep or idle.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "manage_interest_topics",
            "description": "Manages user interest tracking topics for the overnight scout.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "add", "delete"], "description": "Action to perform."},
                    "topic": {"type": "string", "description": "Topic name (required for add)."},
                    "category": {"type": "string", "description": "Category name (optional for add)."},
                    "topic_id": {"type": "integer", "description": "Topic ID (required for delete)."}
                },
                "required": ["action"],
            },
        },
    },
]

SECURITY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_privacy_status",
            "description": "Inspects the Privacy Guard protection status, blocked leak counters, and active Owner Loyalty contract.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_privacy_guard",
            "description": "Updates the Privacy Guard configuration, toggle strict mode, or adds blocked confidential keywords.",
            "parameters": {
                "type": "object",
                "properties": {
                    "strict_mode": {"type": "boolean", "description": "Enable or disable strict leak prevention."},
                    "add_blocked_keyword": {"type": "string", "description": "Specific confidential keyword to block from egress."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "agentshield_scan_text",
            "description": "Scans arbitrary text or external untrusted payloads for indirect prompt injection, role hijacking, instruction overrides, and exfiltration beacons.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Content or payload to inspect for adversarial patterns."},
                    "source": {"type": "string", "description": "Source origin of the content (e.g. 'web', 'file', 'webhook')."},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "agentshield_get_security_status",
            "description": "Retrieves AgentShield runtime firewall metrics, active threat counts, quarantined payloads, and Tier 4 OS lockdown status.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "agentshield_audit_tool_call",
            "description": "Pre-execution security audit validating a proposed tool call against privilege boundary tiers and argument traversal patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string", "description": "Name of the tool to audit."},
                    "arguments": {"type": "object", "description": "Proposed tool call arguments."},
                },
                "required": ["tool_name"],
            },
        },
    },
]

LANGUAGE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "learn_language_phrase",
            "description": "Records or updates a learned word, idiom, greeting, or expression in local languages (Bangla, Chakma, etc.) with its meaning and usage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "word_or_phrase": {"type": "string", "description": "The word or phrase (e.g. 'ki khobor', 'doi bhalo', 'thik ache')."},
                    "language": {"type": "string", "description": "Language or dialect (e.g. 'bangla', 'chakma', 'chatgaya', 'sylheti')."},
                    "meaning": {"type": "string", "description": "English meaning, intent, or cultural explanation."},
                    "usage_example": {"type": "string", "description": "Example of how to use it naturally in banter or response."},
                    "phonetic_script": {"type": "string", "description": "Original script or phonetic spelling if known."},
                },
                "required": ["word_or_phrase", "language", "meaning"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_learned_language",
            "description": "Searches or lists words, expressions, and idioms learned so far in local languages (Bangla, Chakma, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Optional search term or keyword to filter by."},
                    "language": {"type": "string", "description": "Optional language filter ('bangla', 'chakma')."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_language_stats",
            "description": "Returns progress metrics on acquired local languages and dialects (total vocabulary, heard counts, top phrases).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

GOVERNOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_hardware_status",
            "description": "Inspects host hardware telemetry in real-time (CPU usage %, RAM GB used/free, GPU name, VRAM used/free, temperature, and local Ollama model availability).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cost_governor_metrics",
            "description": "Returns today's LLM token spend, daily budget cap status, total cost in USD, and estimated savings compared to GPT-4o.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_cost_governor_settings",
            "description": "Updates cost governor preferences such as daily budget hard cap (USD), prefer_local_when_feasible flag, or hard_cap_enforced flag.",
            "parameters": {
                "type": "object",
                "properties": {
                    "daily_budget_usd": {"type": "number", "description": "Maximum allowed daily spending in USD (e.g. 1.0, 5.0)."},
                    "prefer_local_when_feasible": {"type": "boolean", "description": "If true, routes routine non-reasoning tasks to local models when VRAM is available."},
                    "hard_cap_enforced": {"type": "boolean", "description": "If true, blocks cloud LLM requests once the daily budget is reached and downgrades to local models."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "adjust_master_volume",
            "description": "Nudges or mutes system master volume ('up', 'down', 'mute') with step count.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Volume action: 'up', 'down', or 'mute'."},
                    "steps": {"type": "integer", "description": "Number of volume adjustment steps (1-50, default 2)."},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_screen_brightness",
            "description": "Reads display brightness percentage via Windows WMI telemetry.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_screen_brightness",
            "description": "Sets the Windows display brightness (0-100%).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level_percent": {"type": "integer", "description": "Target brightness level between 0 and 100."}
                },
                "required": ["level_percent"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_default_browser",
            "description": "Detects the user's registered default web browser via Windows UserChoice registry keys.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_wifi_status",
            "description": "Inspects active Wi-Fi adapter connection, SSID, signal strength, and network status via netsh.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

OS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "os_list_windows",
            "description": "Enumerates all active desktop application windows, including window titles, HWNDs, process names, and geometry coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "visible_only": {"type": "boolean", "description": "If true, only returns visible foreground windows (default true)."}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "os_focus_window",
            "description": "Brings a target application window to the foreground by title substring or HWND.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Title substring (e.g. 'Notepad', 'Visual Studio Code', 'Chrome') or numeric HWND."}
                },
                "required": ["target"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "os_launch_app",
            "description": "Launches an application executable or command line in the background.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Application executable path or command (e.g. 'notepad.exe', 'calc.exe')."},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Command line arguments list."}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "os_execute_action",
            "description": "Executes a direct OS automation action: click, double_click, right_click, type, send_keys, minimize, maximize, or close.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action type: 'click', 'double_click', 'right_click', 'type', 'send_keys', 'focus', 'minimize', 'maximize', 'close'."},
                    "target": {"type": "string", "description": "Target window title or element descriptor."},
                    "x": {"type": "integer", "description": "Horizontal desktop pixel coordinate for mouse clicks."},
                    "y": {"type": "integer", "description": "Vertical desktop pixel coordinate for mouse clicks."},
                    "text": {"type": "string", "description": "Text to type when action is 'type'."},
                    "keys": {"type": "array", "items": {"type": "string"}, "description": "List of keys for hotkeys (e.g. ['ctrl', 's'], ['alt', 'tab'], ['enter'])."}
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "os_list_processes",
            "description": "Lists running system processes with PID, name, and memory consumption (MB).",
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_name": {"type": "string", "description": "Optional process name filter (e.g. 'python', 'code')."},
                    "limit": {"type": "integer", "description": "Maximum number of processes to return (default 25)."}
                },
                "required": [],
            },
        },
    },
]

SKILLS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "crystallize_skill",
            "description": "Saves a multi-step task execution pattern or solution into the Second Brain as a reusable skill in Obsidian vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Unique identifier for the skill (e.g. 'sqlite_backup_sync')."},
                    "description": {"type": "string", "description": "Clear explanation of what the skill achieves."},
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "args": {"type": "object"},
                                "description": {"type": "string"},
                            },
                            "required": ["tool"],
                        },
                        "description": "Sequential tool invocation steps.",
                    },
                    "trigger_keywords": {"type": "array", "items": {"type": "string"}, "description": "Phrases that trigger this skill."},
                    "preconditions": {"type": "string", "description": "Required state before execution."},
                },
                "required": ["name", "description", "steps"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_skill",
            "description": "Searches crystallized skills in the Second Brain by keyword, trigger, or task description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keyword or goal to search (e.g. 'backup', 'window audit')."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_error_reflexion",
            "description": "Registers an execution failure and creates a persistent corrective rule so MaxIM does not repeat the mistake.",
            "parameters": {
                "type": "object",
                "properties": {
                    "failed_tool": {"type": "string", "description": "Tool name that failed."},
                    "error_message": {"type": "string", "description": "Error string or exception received."},
                    "root_cause": {"type": "string", "description": "Why the failure occurred."},
                    "corrective_rule": {"type": "string", "description": "Rule to follow next time to avoid this failure."},
                },
                "required": ["failed_tool", "error_message", "root_cause", "corrective_rule"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_learned_skills",
            "description": "Lists all crystallized skills with execution stats and Obsidian vault paths.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum number of skills to return (default 50)."}
                },
                "required": [],
            },
        },
    },
]

SANDBOX_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "sandbox_run_command",
            "description": "Executes a shell command inside the QwenPaw pre-audited secure sandbox with execution timeout and output clipping.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to audit and execute."},
                    "cwd": {"type": "string", "description": "Optional working directory. Defaults to workspace root."},
                    "timeout_seconds": {"type": "integer", "description": "Execution timeout in seconds (default 15, max 60)."}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sandbox_audit_command",
            "description": "Performs a QwenPaw pre-execution safety check on a command without executing it, checking for destructive patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to audit for safety risks."}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "workstation_scaffold_project",
            "description": "Scaffolds a new production-ready project template (e.g. python_service, fastapi, cli_tool).",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_type": {"type": "string", "description": "Type of project: 'python_service', 'fastapi', 'cli_tool'."},
                    "target_dir": {"type": "string", "description": "Directory to generate project in."},
                    "project_name": {"type": "string", "description": "Name of the new project module."},
                    "description": {"type": "string", "description": "Brief description of the project."}
                },
                "required": ["project_type", "target_dir", "project_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "workstation_git_status",
            "description": "Checks the working tree cleanliness, untracked files, branch status, and Git hygiene score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_dir": {"type": "string", "description": "Optional directory of repository. Defaults to workspace root."}
                },
                "required": [],
            },
        },
    },
]

TODOS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_session_todo",
            "description": "Appends a structured sub-goal or actionable task to the active session checklist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Description of the task to track."},
                    "step_order": {"type": "integer", "description": "Optional step sequence order number."}
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_session_todo",
            "description": "Updates the status of a session task (pending, in_progress, completed, failed) with an optional outcome summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {"type": "integer", "description": "ID of the todo item."},
                    "status": {"type": "string", "description": "Status: 'pending', 'in_progress', 'completed', 'failed'."},
                    "result_summary": {"type": "string", "description": "Brief outcome description."}
                },
                "required": ["todo_id", "status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_session_todos",
            "description": "Lists the active goals and todo items for the current session.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Optional filter: 'pending', 'in_progress', 'completed', 'failed'."}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_token_juice_stats",
            "description": "Retrieves real-time token savings and compression ratio metrics from the TokenJuice engine.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

MOBILE_ADB_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "adb_get_devices",
            "description": "Lists attached Android mobile devices, emulators, and their connection states via ADB.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "adb_get_battery",
            "description": "Retrieves real-time mobile battery level, voltage, temperature, and charging health.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string", "description": "Optional Android device serial/id."}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "adb_tap",
            "description": "Injects a coordinate tap at (x, y) on the connected mobile device screen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate on mobile display."},
                    "y": {"type": "integer", "description": "Y coordinate on mobile display."},
                    "device_id": {"type": "string", "description": "Optional Android device serial/id."}
                },
                "required": ["x", "y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "adb_swipe",
            "description": "Executes a coordinate touch swipe from (x1, y1) to (x2, y2) on mobile display.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x1": {"type": "integer", "description": "Start X coordinate."},
                    "y1": {"type": "integer", "description": "Start Y coordinate."},
                    "x2": {"type": "integer", "description": "End X coordinate."},
                    "y2": {"type": "integer", "description": "End Y coordinate."},
                    "duration_ms": {"type": "integer", "description": "Swipe duration in milliseconds (default 300)."},
                    "device_id": {"type": "string", "description": "Optional Android device serial/id."}
                },
                "required": ["x1", "y1", "x2", "y2"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "adb_launch_app",
            "description": "Launches an application package on the connected mobile device.",
            "parameters": {
                "type": "object",
                "properties": {
                    "package_name": {"type": "string", "description": "Target Android package name (e.g. com.slack, com.google.android.apps.maps)."},
                    "device_id": {"type": "string", "description": "Optional Android device serial/id."}
                },
                "required": ["package_name"],
            },
        },
    },
]

UPLINK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_remote_message",
            "description": "Dispatches a remote message, report, or alert to an external communication channel (Discord, Slack, Telegram, or Webhook).",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "Target channel: 'discord', 'slack', 'telegram', or 'webhook'."},
                    "target": {"type": "string", "description": "Destination address (webhook URL, Discord/Slack channel ID, or Telegram chat ID)."},
                    "text": {"type": "string", "description": "Text body of the message."},
                    "title": {"type": "string", "description": "Optional title or header for the message."},
                },
                "required": ["channel", "target", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "broadcast_remote_message",
            "description": "Broadcasts an alert, shift summary, or briefing across all configured and enabled communication channels simultaneously.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Message text to broadcast."},
                    "title": {"type": "string", "description": "Optional header or subject."},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_remote_channel_status",
            "description": "Retrieves real-time status, configuration, and traffic telemetry for all connected external channels (Discord, Slack, Telegram, Webhook).",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

BROWSER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "browser_navigate",
            "description": "Navigates to a web URL, parses the HTML, and returns an indexed interactive DOM element tree ([1] Link, [2] Button, [3] Input).",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The destination URL (e.g. 'https://news.ycombinator.com' or 'https://github.com')."},
                    "session_id": {"type": "string", "description": "Optional session identifier, defaults to 'default_session'."},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_get_dom",
            "description": "Retrieves the indexed interactive DOM element tree of the active webpage without re-fetching.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_interactive": {"type": "boolean", "description": "Whether to return only actionable elements. Defaults to true."},
                    "max_elements": {"type": "integer", "description": "Maximum number of interactive elements to return. Defaults to 80."},
                    "session_id": {"type": "string", "description": "Optional session ID."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click_element",
            "description": "Clicks an indexed interactive element by its 1-based index ([1], [2], etc.) from the active DOM tree. Navigates links or submits forms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_index": {"type": "integer", "description": "The 1-based element index shown in the DOM tree."},
                    "session_id": {"type": "string", "description": "Optional session ID."},
                },
                "required": ["element_index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_type_element",
            "description": "Types text into an indexed input field or textarea ([1], [2], etc.). Optionally submits the form immediately.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_index": {"type": "integer", "description": "The 1-based element index of the target input field."},
                    "text": {"type": "string", "description": "The text to input."},
                    "submit": {"type": "boolean", "description": "If true, submits the form after typing. Defaults to false."},
                    "session_id": {"type": "string", "description": "Optional session ID."},
                },
                "required": ["element_index", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_extract_text",
            "description": "Extracts clean readable body text from the active webpage, stripped of HTML markup and scripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_chars": {"type": "integer", "description": "Maximum characters to return. Defaults to 5000."},
                    "session_id": {"type": "string", "description": "Optional session ID."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_manage_session",
            "description": "Manages browser multi-tab lifecycle and navigation history (new_tab, close_tab, switch_tab, history_back, history_forward, list_tabs).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["new_tab", "close_tab", "switch_tab", "history_back", "history_forward", "list_tabs"],
                        "description": "The session action to perform.",
                    },
                    "tab_id": {"type": "string", "description": "Target tab ID for switch_tab or close_tab."},
                    "session_id": {"type": "string", "description": "Optional session ID."},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "laya_decide_browsing_action",
            "description": "Uses Laya System 1 neural decision engine to analyze the current webpage's interactive elements and select the optimal link, button, or search box to act on for a given objective.",
            "parameters": {
                "type": "object",
                "properties": {
                    "objective": {"type": "string", "description": "The research or browsing objective to fulfill."},
                    "session_id": {"type": "string", "description": "Optional session ID."},
                },
                "required": ["objective"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "laya_verify_browsing_content",
            "description": "Uses Laya System 1 neural decision engine to verify whether the active webpage's text content satisfies the research objective and extract key findings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "objective": {"type": "string", "description": "The research or browsing objective to verify."},
                    "session_id": {"type": "string", "description": "Optional session ID."},
                },
                "required": ["objective"],
            },
        },
    },
]

FILE_ORGANIZER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "scan_directory",
            "description": "Scans a directory (e.g. 'C:/Users/Sam/Downloads') and returns a breakdown of file counts, sizes, and proposed category moves without modifying disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {"type": "string", "description": "Absolute or relative path to the folder to scan."},
                },
                "required": ["directory_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "organize_directory",
            "description": "Organizes files in a directory into category folders (Photos, Documents, Videos, Audio, Archives, Installers, Code). Supports dry_run preview and collision protection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {"type": "string", "description": "Path to the folder to organize."},
                    "dry_run": {"type": "boolean", "description": "If true, simulates organization without moving files. Defaults to false."},
                },
                "required": ["directory_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "undo_organization",
            "description": "Rolls back an organization batch, moving all relocated files back to their original paths.",
            "parameters": {
                "type": "object",
                "properties": {
                    "batch_id": {"type": "string", "description": "The batch identifier returned from organize_directory."},
                },
                "required": ["batch_id"],
            },
        },
    },
]

OFFICE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "office_create_workbook",
            "description": "Creates a new structured spreadsheet workbook with multiple sheets for tabular data management.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the workbook (e.g. 'Project Budget', 'Quarterly Revenue')."},
                    "description": {"type": "string", "description": "Optional description of the workbook purpose."},
                    "sheet_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Initial sheet names, defaults to ['Sheet1'].",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "office_read_sheet",
            "description": "Reads spreadsheet cells and computed formulas from a sheet or designated coordinate range (e.g. 'A1:C10').",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_id": {"type": "string", "description": "Identifier of the sheet to inspect."},
                    "range_str": {"type": "string", "description": "Optional range string (e.g. 'A1:E20'). Defaults to all populated cells."},
                },
                "required": ["sheet_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "office_edit_cells",
            "description": "Updates cells with raw values or formulas (e.g. {'A1': 'Revenue', 'B1': 5000, 'C1': '=B1*1.15'}). Commits Git-style revision.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_id": {"type": "string", "description": "Target sheet identifier."},
                    "cell_updates": {
                        "type": "object",
                        "description": "Key-value dictionary of cell coordinates to values or formulas (e.g. {'A1': 'Total', 'B1': '=SUM(B2:B10)'}).",
                    },
                },
                "required": ["sheet_id", "cell_updates"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "office_rollback_revision",
            "description": "Rolls back all cell mutations committed in a specific spreadsheet revision.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_id": {"type": "string", "description": "Target sheet identifier."},
                    "revision_id": {"type": "string", "description": "Revision ID to undo (e.g. 'rev_20260925_103000')."},
                },
                "required": ["sheet_id", "revision_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "office_export_markdown",
            "description": "Exports spreadsheet cells to clean GitHub/Obsidian-compatible Markdown table format. Optionally writes to vault note.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_id": {"type": "string", "description": "Sheet identifier to export."},
                    "range_str": {"type": "string", "description": "Optional coordinate range."},
                    "save_to_vault": {"type": "boolean", "description": "Whether to write table to an Obsidian vault note."},
                    "vault_note_name": {"type": "string", "description": "Optional note title if saving to vault."},
                },
                "required": ["sheet_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "office_import_csv",
            "description": "Imports tabular CSV text into a spreadsheet sheet with row/col coordinate mapping.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_id": {"type": "string", "description": "Target sheet identifier."},
                    "csv_data": {"type": "string", "description": "Raw CSV text or local file path."},
                },
                "required": ["sheet_id", "csv_data"],
            },
        },
    },
]

WORK_GUIDE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "work_decompose_goal",
            "description": "Decomposes a broad user work goal or project into sequential milestones and discrete action checklists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "The high-level work goal or project objective."},
                    "category": {"type": "string", "description": "Category: 'coding', 'research', 'finance', 'organization', 'general'."},
                    "description": {"type": "string", "description": "Optional background context."},
                },
                "required": ["goal"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "work_get_next_action",
            "description": "Retrieves the single highest-priority pending action across active work projects to guide the user's focus.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "work_update_action_status",
            "description": "Updates progress on a work task (e.g. 'completed', 'in_progress', 'skipped'). Automatically updates milestone progress.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_id": {"type": "string", "description": "Action item identifier."},
                    "status": {"type": "string", "description": "New status: 'completed', 'in_progress', 'pending', 'skipped'."},
                    "result_summary": {"type": "string", "description": "Summary of findings or completed work output."},
                },
                "required": ["action_id", "status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "work_list_projects",
            "description": "Lists all active work projects with their milestones, tasks, and completion percentages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status: 'active', 'completed', or leave empty for all."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_cognitive_persona",
            "description": "Switches the assistant's cognitive thinking mode (e.g. 'executive_assistant', 'intj_architect', 'istj_auditor', 'entp_visionary', 'entj_commander', 'intp_logician', 'bitterbot_cynic').",
            "parameters": {
                "type": "object",
                "properties": {
                    "persona_key": {"type": "string", "description": "Key or name of the cognitive persona to activate."},
                },
                "required": ["persona_key"],
            },
        },
    },
]

VIDEO_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "video_inspect_file",
            "description": "Inspects video file metadata, stream formats, duration, resolution, codecs, and framerate using FFprobe.",
            "parameters": {
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "Local path to the video file."},
                },
                "required": ["video_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "video_extract_frames",
            "description": "Samples and extracts visual keyframes at regular intervals using FFmpeg, saving them to the Obsidian vault frame cache.",
            "parameters": {
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "Local path to the video file."},
                    "interval_seconds": {"type": "number", "description": "Sampling interval in seconds (default 10.0)."},
                    "max_frames": {"type": "integer", "description": "Maximum number of frames to extract (default 30)."},
                },
                "required": ["video_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "video_get_transcript",
            "description": "Extracts subtitles (SRT/VTT) or speech activity segments from the video file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "Local path to the video file."},
                },
                "required": ["video_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "video_summarize_meeting",
            "description": "Generates an executive video meeting or tutorial dossier with timestamped frames, dialogue segments, and action items saved to the Obsidian vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "Local path to the video file."},
                    "title": {"type": "string", "description": "Custom title for the meeting or tutorial briefing."},
                    "interval_seconds": {"type": "number", "description": "Frame sampling interval in seconds (default 15.0)."},
                },
                "required": ["video_path"],
            },
        },
    },
]

CONVERSATION_TREE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tree_fork_branch",
            "description": "Forks the conversation history from a specific message ID into an alternative branch (LibreChat-style message tree).",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Active session identifier."},
                    "fork_message_id": {"type": "integer", "description": "Message ID where the conversation branches off."},
                    "new_branch_name": {"type": "string", "description": "Name for the new exploratory branch."},
                },
                "required": ["session_id", "fork_message_id", "new_branch_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tree_list_branches",
            "description": "Lists all conversation branches for a session, indicating active branch and message counts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session identifier."},
                },
                "required": ["session_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tree_switch_branch",
            "description": "Switches the active conversation branch in the message tree.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session identifier."},
                    "branch_id": {"type": "string", "description": "Branch identifier to activate."},
                },
                "required": ["session_id", "branch_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tree_save_preset",
            "description": "Saves a reusable operational preset with model alias, temperature, system prompt, and allowed toolsets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "preset_id": {"type": "string", "description": "Unique identifier for the preset."},
                    "name": {"type": "string", "description": "Human-readable preset name."},
                    "model_alias": {"type": "string", "description": "Model alias (e.g. 'primary', 'fast', 'reasoning')."},
                    "temperature": {"type": "number", "description": "Model temperature (0.0 to 1.0)."},
                    "system_prompt": {"type": "string", "description": "System role directive."},
                    "toolsets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of allowed toolsets (e.g. ['vault', 'office', 'video']).",
                    },
                    "description": {"type": "string", "description": "Brief description of the preset."},
                },
                "required": ["preset_id", "name", "model_alias"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tree_load_preset",
            "description": "Loads an operational preset configuration by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "preset_id": {"type": "string", "description": "Unique identifier of the preset to load."},
                },
                "required": ["preset_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tree_save_artifact",
            "description": "Saves a versioned code or document artifact tied to the conversation branch and syncs it to the Obsidian vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session identifier."},
                    "branch_id": {"type": "string", "description": "Branch identifier."},
                    "title": {"type": "string", "description": "Title or filename of the artifact."},
                    "artifact_type": {"type": "string", "description": "Type: 'code', 'markdown', 'plan', 'data'."},
                    "content": {"type": "string", "description": "Raw content of the artifact."},
                },
                "required": ["session_id", "branch_id", "title", "artifact_type", "content"],
            },
        },
    },
]

ARCHIFY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "archify_create_diagram",
            "description": "Creates or updates an architectural diagram (system, sequence, data_flow, state_machine), validates Mermaid syntax, and syncs an interactive note to Obsidian.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the diagram."},
                    "diagram_type": {"type": "string", "description": "Type: 'system', 'sequence', 'data_flow', 'state_machine'."},
                    "description": {"type": "string", "description": "Detailed explanation of the architecture."},
                    "mermaid_code": {"type": "string", "description": "Raw Mermaid diagram code (or omit to use template)."},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "archify_inspect_codebase",
            "description": "Scans the Python backend codebase, maps module import relationships, and generates an automated architecture diagram.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_dir": {"type": "string", "description": "Optional directory path to scan. Defaults to backend."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "archify_list_diagrams",
            "description": "Lists all stored architecture and system design diagrams.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

CURRICULUM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "curriculum_create_topic",
            "description": "Decomposes any technical subject, library, or codebase into a multi-stage Socratic learning curriculum and drill questions in the Obsidian vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Subject, skill, or library to learn."},
                    "category": {"type": "string", "description": "Category: 'engineering', 'architecture', 'theory', 'business', 'tools'."},
                    "description": {"type": "string", "description": "Optional background or target learning goals."},
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "curriculum_get_drill",
            "description": "Retrieves the next unanswered Socratic exploration question for a topic curriculum.",
            "parameters": {
                "type": "object",
                "properties": {
                    "curriculum_id": {"type": "string", "description": "Curriculum identifier."},
                },
                "required": ["curriculum_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "curriculum_submit_answer",
            "description": "Submits a learner's answer to a Socratic drill question, evaluates dialectical accuracy, and updates topic mastery level.",
            "parameters": {
                "type": "object",
                "properties": {
                    "drill_id": {"type": "string", "description": "Drill identifier."},
                    "answer": {"type": "string", "description": "Learner's response or reasoning."},
                },
                "required": ["drill_id", "answer"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "curriculum_list_topics",
            "description": "Lists all active Socratic learning curricula and mastery levels.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

VOICE_STUDIO_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "voice_studio_render_note",
            "description": "Converts an Obsidian vault note, report, or briefing into a spoken audio podcast MP3 file using Edge-TTS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_title": {"type": "string", "description": "Name or path of the Obsidian note to speak."},
                    "profile_id": {"type": "string", "description": "Voice profile: 'host_maxim', 'analyst_jenny', 'critic_eric', 'bilingual_pradeep'."},
                },
                "required": ["note_title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "voice_studio_render_dialogue",
            "description": "Renders a multi-speaker conversation script into a unified audio briefing file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the dialogue podcast."},
                    "script": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "speaker": {"type": "string", "description": "Voice profile ID (e.g. 'host_maxim', 'analyst_jenny')."},
                                "text": {"type": "string", "description": "Spoken turn dialogue."},
                            },
                            "required": ["speaker", "text"],
                        },
                        "description": "Sequence of dialogue turns.",
                    },
                },
                "required": ["title", "script"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "voice_studio_list_profiles",
            "description": "Lists available voice profiles, pitches, and rates.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

SCIENCE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "science_search_arxiv",
            "description": "Searches arXiv for academic and machine learning research papers, returning titles, abstracts, authors, and PDF links.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query or topic."},
                    "max_results": {"type": "integer", "description": "Maximum number of papers to retrieve (default 5)."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "science_search_pubmed",
            "description": "Searches NCBI PubMed biomedical literature, returning titles, journals, authors, and abstracts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Biomedical or scientific query."},
                    "max_results": {"type": "integer", "description": "Maximum number of articles to retrieve (default 5)."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "science_lookup_compound",
            "description": "Retrieves chemical compound information from PubChem including IUPAC name, molecular formula, weight, and canonical SMILES.",
            "parameters": {
                "type": "object",
                "properties": {
                    "compound_name": {"type": "string", "description": "Common or scientific compound name (e.g. 'caffeine', 'aspirin')."},
                },
                "required": ["compound_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "science_synthesize_literature_review",
            "description": "Compiles a systematic academic literature review with BibTeX citations and syncs it to the Obsidian vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Research topic or problem to synthesize."},
                },
                "required": ["topic"],
            },
        },
    },
]

BROWSER_SKILL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "browserskill_get_active_tab",
            "description": "Queries the connected logged-in browser session for the active tab title, URL, and session details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_mode": {"type": "boolean", "description": "Set to true to return verified test session data."}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browserskill_evaluate_script",
            "description": "Safely evaluates JavaScript in the active user browser tab without stealing window focus.",
            "parameters": {
                "type": "object",
                "properties": {
                    "script": {"type": "string", "description": "JavaScript code or expression to evaluate."},
                    "tab_id": {"type": "string", "description": "Optional tab ID to target."},
                    "test_mode": {"type": "boolean", "description": "Set to true to run in simulated mode."},
                },
                "required": ["script"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browserskill_execute_command",
            "description": "Executes real browser actions ('click', 'type', 'scroll', 'extract') in the active tab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["click", "type", "scroll", "extract"], "description": "Action type to perform."},
                    "target": {"type": "string", "description": "CSS selector or element identifier."},
                    "value": {"type": "string", "description": "Optional text value for typing."},
                    "test_mode": {"type": "boolean", "description": "Set to true to run in simulated mode."},
                },
                "required": ["action", "target"],
            },
        },
    },
]

MAGNITUDE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "magnitude_profile_hardware",
            "description": "Probes system CPU, RAM, and GPU VRAM to recommend optimal quantized open-source local LLMs.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "magnitude_benchmark_throughput",
            "description": "Executes a rapid token generation throughput benchmark on the local machine.",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_tokens": {"type": "integer", "description": "Number of synthetic benchmark tokens (default 100)."}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "magnitude_get_profile",
            "description": "Retrieves the latest hardware profile, VRAM limits, and model suitability recommendations.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

CURSOR_PLUGINS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "cursor_import_plugin",
            "description": "Imports and validates a Cursor plugin manifest (plugin.json) with rules, skills, and MCP servers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "manifest_path_or_dict": {"type": "string", "description": "File path to plugin.json or JSON string of manifest."}
                },
                "required": ["manifest_path_or_dict"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cursor_list_plugins",
            "description": "Lists all installed Cursor plugins, showing versions, rules count, skills count, and active status.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cursor_toggle_plugin",
            "description": "Enables or disables an installed Cursor plugin by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plugin_id": {"type": "string", "description": "The unique ID of the plugin."},
                    "enabled": {"type": "boolean", "description": "True to enable, False to disable."}
                },
                "required": ["plugin_id", "enabled"],
            },
        },
    },
]

SEO_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "seo_audit_url",
            "description": "Audits a website or HTML string for technical SEO, OpenGraph tags, heading hierarchy, and saves a scorecard to Obsidian.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Webpage URL to fetch and audit."},
                    "html": {"type": "string", "description": "Optional raw HTML source to audit directly."},
                    "test_mode": {"type": "boolean", "description": "Set to true to run against simulated markup."}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "seo_analyze_keyword_density",
            "description": "Calculates total word count and keyword frequency distribution for text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text or article content to analyze."},
                    "target_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of target keywords to check density percentages for."
                    }
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "seo_list_audits",
            "description": "Lists previous SEO technical audits and scores recorded in MaxIM.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

MEDIA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generates a high-quality visual image, picture, photo, artwork, or illustration from a detailed visual prompt using neural diffusion (FLUX / SDXL / DALL-E).",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The visual prompt describing what should be depicted in detail (subjects, scene, style, lighting)."
                    },
                    "style": {
                        "type": "string",
                        "description": "Artistic style: 'photorealistic', 'anime', 'cyberpunk', 'cinematic', 'digital art', 'watercolor', or 'pixel art'. Default is 'photorealistic'.",
                        "default": "photorealistic"
                    },
                    "width": {
                        "type": "integer",
                        "description": "Width of the image in pixels (e.g. 512, 768, 1024). Default is 768.",
                        "default": 768
                    },
                    "height": {
                        "type": "integer",
                        "description": "Height of the image in pixels (e.g. 512, 768, 1024). Default is 768.",
                        "default": 768
                    }
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": "Reads and extracts clean plain text from any local document, report, or code file (PDF, Word .docx, CSV, JSON, Markdown, Python, TXT, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the document file (absolute path, relative path, or filename)."
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum number of characters to extract (default 15000).",
                        "default": 15000
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_image",
            "description": "Inspects and describes any local image file (PNG, JPG, JPEG, WEBP, BMP, GIF), extracting dimensions, visual contents, and layout details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Path to the image file (absolute path, vault relative path, or attachment filename)."
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Specific question or inspection instruction regarding the image (e.g. 'What does this picture look like?', 'Read the text in this diagram')."
                    }
                },
                "required": ["image_path"]
            }
        }
    }
]

TOOLSET_REGISTRY: Dict[ToolsetName, List[Dict[str, Any]]] = {
    ToolsetName.VAULT: VAULT_TOOLS,
    ToolsetName.PERCEPTION: PERCEPTION_TOOLS,
    ToolsetName.CUA: CUA_TOOLS,
    ToolsetName.MEMORY: MEMORY_TOOLS,
    ToolsetName.DELEGATION: DELEGATION_TOOLS,
    ToolsetName.MCP: MCP_TOOLS,
    ToolsetName.REACH: REACH_TOOLS,
    ToolsetName.OPERATOR: OPERATOR_TOOLS,
    ToolsetName.SCOUT: SCOUT_TOOLS,
    ToolsetName.SECURITY: SECURITY_TOOLS,
    ToolsetName.LANGUAGE: LANGUAGE_TOOLS,
    ToolsetName.GOVERNOR: GOVERNOR_TOOLS,
    ToolsetName.OS: OS_TOOLS,
    ToolsetName.SKILLS: SKILLS_TOOLS,
    ToolsetName.SANDBOX: SANDBOX_TOOLS,
    ToolsetName.TODOS: TODOS_TOOLS,
    ToolsetName.MOBILE_ADB: MOBILE_ADB_TOOLS,
    ToolsetName.UPLINK: UPLINK_TOOLS,
    ToolsetName.BROWSER: BROWSER_TOOLS,
    ToolsetName.FILES: FILE_ORGANIZER_TOOLS,
    ToolsetName.OFFICE: OFFICE_TOOLS,
    ToolsetName.WORK_GUIDE: WORK_GUIDE_TOOLS,
    ToolsetName.VIDEO: VIDEO_TOOLS,
    ToolsetName.CONVERSATION_TREE: CONVERSATION_TREE_TOOLS,
    ToolsetName.ARCHIFY: ARCHIFY_TOOLS,
    ToolsetName.CURRICULUM: CURRICULUM_TOOLS,
    ToolsetName.VOICE_STUDIO: VOICE_STUDIO_TOOLS,
    ToolsetName.SCIENCE: SCIENCE_TOOLS,
    ToolsetName.BROWSER_SKILL: BROWSER_SKILL_TOOLS,
    ToolsetName.MAGNITUDE: MAGNITUDE_TOOLS,
    ToolsetName.CURSOR_PLUGINS: CURSOR_PLUGINS_TOOLS,
    ToolsetName.SEO: SEO_TOOLS,
    ToolsetName.MEDIA: MEDIA_TOOLS,
}

class ToolCatalogManager:
    @staticmethod
    def get_toolset(name: ToolsetName | str) -> List[Dict[str, Any]]:
        try:
            key = ToolsetName(name.lower())
            return TOOLSET_REGISTRY.get(key, [])
        except ValueError:
            return []

    @staticmethod
    def get_all_tools() -> List[Dict[str, Any]]:
        all_t = []
        for tools in TOOLSET_REGISTRY.values():
            all_t.extend(tools)
        return all_t

    @staticmethod
    def filter_by_toolsets(enabled_toolsets: List[str]) -> List[Dict[str, Any]]:
        res = []
        for ts_name in enabled_toolsets:
            res.extend(ToolCatalogManager.get_toolset(ts_name))
        return res

tool_catalog = ToolCatalogManager()
