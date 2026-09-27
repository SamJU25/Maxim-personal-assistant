"""
Hermes & Nanobot-Inspired Sub-Agent Creation & Delegation Engine for MaxIM.
Enables the primary cognitive agent to dynamically spawn isolated child agents
with dedicated tasks, custom roles, tool whitelists, and independent model connections.
"""
import asyncio
import concurrent.futures
import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from config import config
from memory import memory_store, MessageRecord, SQLiteMemoryStore
from router import model_router, ProviderType
from telos import telos_engine
from tools.vault_tool import vault_synapse
from tools.screen_tool import screen_tool
from tools.cua_tool import cua_driver
from tools.reach_tool import agent_reach

logger = logging.getLogger("maxim.subagent")

def _run_async_safely(coro):
    """Executes a coroutine safely whether an event loop is already running or not."""
    try:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(lambda: asyncio.run(coro)).result()
    except RuntimeError:
        return asyncio.run(coro)


class SubAgentConfig(BaseModel):
    subagent_id: str = Field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:8]}")
    task: str = Field(..., description="The objective or prompt for this subagent")
    role: str = Field(default="Specialist Worker", description="Domain persona or specialty")
    provider: Optional[str] = Field(default=None, description="Model provider override")
    model: Optional[str] = Field(default=None, description="Model name override")
    toolset_whitelist: Optional[List[str]] = Field(default=None, description="Allowed tool names")
    max_iterations: int = Field(default=4, description="Maximum execution step budget")

class SubAgent:
    def __init__(
        self,
        config_obj: SubAgentConfig,
        memory: Optional[SQLiteMemoryStore] = None,
    ):
        self.cfg = config_obj
        self.memory = memory or memory_store
        # Resolve connection role if not explicitly specified
        if not self.cfg.provider:
            prov, mod = model_router.get_connection_for_role("subagents")
            self.provider = prov
            self.model = self.cfg.model or mod
        else:
            self.provider = self.cfg.provider
            self.model = self.cfg.model

    def build_subagent_system_prompt(self) -> str:
        """Constructs focused, non-bloated sub-agent prompt."""
        telos_summary = telos_engine.get_context_injection()
        prompt = (
            f"You are a specialized MaxIM Sub-Agent with role: '{self.cfg.role}'.\n"
            f"Your specific mission is: {self.cfg.task}\n\n"
            f"Grounding context:\n{telos_summary}\n\n"
            "Rules:\n"
            "1. Focus strictly on completing your assigned task efficiently.\n"
            "2. Use available tools decisively to gather evidence and produce verifiable results.\n"
            "3. Write like a thoughtful human: direct verbs, natural rhythm, zero AI clichés (never say 'serves as', 'pivotal', 'in today's world', 'furthermore').\n"
            "4. Never use artificial chatbot filler ('Certainly!', 'I hope this helps'). State your findings directly and stop when finished.\n"
        )
        return prompt

    def get_allowed_tools(self, all_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filters the tool catalog against the subagent's allowed whitelist."""
        if not self.cfg.toolset_whitelist:
            return all_tools
        return [
            t for t in all_tools
            if t.get("function", {}).get("name") in self.cfg.toolset_whitelist
        ]

    def execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Executes tool and records receipt."""
        if self.cfg.toolset_whitelist and name not in self.cfg.toolset_whitelist:
            return json.dumps({"error": f"Tool '{name}' is not authorized for subagent '{self.cfg.subagent_id}'."})

        try:
            from engine import agent_engine
            return agent_engine.execute_tool(name, args, session_id=f"subagent_{self.cfg.subagent_id}")
        except Exception as e:
            err = json.dumps({"error": str(e)})
            self.memory.log_receipt(name, args, err, session_id=f"subagent_{self.cfg.subagent_id}")
            return err

    async def run(self, all_tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Runs the subagent ReAct execution loop."""
        from engine import MAXIM_TOOLS

        tools_catalog = self.get_allowed_tools(all_tools or MAXIM_TOOLS)
        # Avoid recursion: subagents cannot spawn more subagents unless whitelisted
        tools_catalog = [t for t in tools_catalog if t.get("function", {}).get("name") != "create_subagent"]

        system_prompt = self.build_subagent_system_prompt()
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self.cfg.task},
        ]

        receipts_generated = []
        iteration = 0

        while iteration < self.cfg.max_iterations:
            iteration += 1
            response = await model_router.chat_completion(
                messages=messages,
                tools=tools_catalog if tools_catalog else None,
                provider=self.provider,
                model=self.model,
            )

            choice = response.choices[0]
            message_obj = choice.message

            if message_obj.tool_calls:
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

                for tc in message_obj.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except Exception:
                        fn_args = {}

                    tool_output = self.execute_tool(fn_name, fn_args)
                    receipts_generated.append({"tool": fn_name, "args": fn_args, "output": tool_output})

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fn_name,
                        "content": tool_output,
                    })
            else:
                final_text = message_obj.content or ""
                return {
                    "subagent_id": self.cfg.subagent_id,
                    "task": self.cfg.task,
                    "role": self.cfg.role,
                    "status": "completed",
                    "result": final_text,
                    "receipts": receipts_generated,
                    "iterations": iteration,
                }

        fallback = f"Sub-agent '{self.cfg.subagent_id}' completed execution budget ({self.cfg.max_iterations} steps)."
        return {
            "subagent_id": self.cfg.subagent_id,
            "task": self.cfg.task,
            "role": self.cfg.role,
            "status": "budget_reached",
            "result": fallback,
            "receipts": receipts_generated,
            "iterations": iteration,
        }

class SubAgentPool:
    def __init__(self):
        self.active_subagents: Dict[str, SubAgent] = {}

    def create_subagent(
        self,
        task: str,
        role: str = "Specialist Worker",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        toolset_whitelist: Optional[List[str]] = None,
        max_iterations: int = 4,
    ) -> SubAgent:
        cfg = SubAgentConfig(
            task=task,
            role=role,
            provider=provider,
            model=model,
            toolset_whitelist=toolset_whitelist,
            max_iterations=max_iterations,
        )
        sub = SubAgent(cfg)
        self.active_subagents[cfg.subagent_id] = sub
        return sub

    async def run_parallel(self, subagents: List[SubAgent]) -> List[Dict[str, Any]]:
        """Executes multiple subagents concurrently."""
        tasks = [sub.run() for sub in subagents]
        return await asyncio.gather(*tasks)

# Global pool singleton
subagent_pool = SubAgentPool()
