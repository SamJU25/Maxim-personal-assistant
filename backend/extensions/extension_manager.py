"""
MaxIM Dynamic Extension Manager.
Discovers, validates, and manages external repository capsules located in backend/extensions/.
Enables seamless integration of third-party tools, agents, and GitHub repositories
without mutating core system files.
"""
import os
import sys
import json
import logging
import importlib.util
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger("maxim.extensions")

DEFAULT_EXTENSIONS_DIR = Path(__file__).resolve().parent

@dataclass
class ExtensionManifest:
    id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = "Community"
    homepage: str = ""
    intent_triggers: List[str] = field(default_factory=list)
    tools: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    capsule_dir: Optional[str] = None
    entry_module: Optional[str] = None


class ExtensionManager:
    """
    MaxIM Dynamic Extension & Capsule Registry.
    Loads isolated capsules from backend/extensions/<name>/, extracting:
    1. manifest.json: Metadata, intent triggers, configuration
    2. tools.py: Standard OpenAI function definitions & execution handlers
    """
    def __init__(self, extensions_dir: Optional[Path] = None):
        self.extensions_dir = extensions_dir or DEFAULT_EXTENSIONS_DIR
        self._extensions: Dict[str, ExtensionManifest] = {}
        self._tool_handlers: Dict[str, Callable] = {}
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}
        self.discover_extensions()

    def discover_extensions(self) -> Dict[str, ExtensionManifest]:
        """
        Scans extensions_dir for subdirectories containing manifest.json.
        Loads manifests and imports tool definitions dynamically.
        """
        self._extensions.clear()
        self._tool_handlers.clear()
        self._tool_metadata.clear()

        if not self.extensions_dir.exists():
            return self._extensions

        for item in self.extensions_dir.iterdir():
            if not item.is_dir() or item.name.startswith(("_", ".")):
                continue

            manifest_path = item / "manifest.json"
            if not manifest_path.exists():
                continue

            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                ext_id = str(data.get("id", item.name)).strip()
                name = str(data.get("name", ext_id.title()))
                enabled = bool(data.get("enabled", True))

                manifest = ExtensionManifest(
                    id=ext_id,
                    name=name,
                    version=str(data.get("version", "1.0.0")),
                    description=str(data.get("description", "")),
                    author=str(data.get("author", "Community")),
                    homepage=str(data.get("homepage", "")),
                    intent_triggers=[t.lower().strip() for t in data.get("intent_triggers", [])],
                    tools=list(data.get("tools", [])),
                    enabled=enabled,
                    capsule_dir=str(item),
                )

                # Attempt dynamic loading of tools.py
                tools_file = item / "tools.py"
                if tools_file.exists() and enabled:
                    self._load_tools_module(item, tools_file, manifest)

                self._extensions[ext_id] = manifest
                logger.info(f"Loaded extension capsule: '{manifest.name}' ({ext_id}) with {len(manifest.tools)} tools.")
            except Exception as e:
                logger.error(f"Failed to load extension at {item}: {e}")

        return self._extensions

    def _load_tools_module(self, capsule_dir: Path, tools_file: Path, manifest: ExtensionManifest):
        """Dynamically imports tools.py from capsule and registers handlers."""
        module_name = f"maxim_ext_{manifest.id}"
        spec = importlib.util.spec_from_file_location(module_name, str(tools_file))
        if not spec or not spec.loader:
            return

        module = importlib.util.module_from_spec(spec)
        # Ensure capsule directory is in sys.path temporarily so internal imports work
        capsule_dir_str = str(capsule_dir)
        path_added = False
        if capsule_dir_str not in sys.path:
            sys.path.insert(0, capsule_dir_str)
            path_added = True

        try:
            spec.loader.exec_module(module)
        finally:
            if path_added and capsule_dir_str in sys.path:
                sys.path.remove(capsule_dir_str)

        # 1. Extract tool definitions
        module_tools = []
        if hasattr(module, "get_tools") and callable(module.get_tools):
            module_tools = module.get_tools()
        elif hasattr(module, "TOOLS") and isinstance(module.TOOLS, list):
            module_tools = module.TOOLS

        # Merge tools from module with manifest tools
        existing_names = {t.get("function", {}).get("name") for t in manifest.tools if "function" in t}
        for t in module_tools:
            fname = t.get("function", {}).get("name")
            if fname and fname not in existing_names:
                manifest.tools.append(t)
                existing_names.add(fname)

        # 2. Extract execution handler
        unified_executor = getattr(module, "execute_tool", None)

        for tool_def in manifest.tools:
            fn_dict = tool_def.get("function", {})
            tool_name = fn_dict.get("name")
            if not tool_name:
                continue

            self._tool_metadata[tool_name] = {
                "extension_id": manifest.id,
                "extension_name": manifest.name,
                "definition": tool_def,
            }

            # Check if module defines a specific function for this tool
            specific_fn = getattr(module, tool_name, None)
            if callable(specific_fn):
                self._tool_handlers[tool_name] = specific_fn
            elif callable(unified_executor):
                # Bind tool_name to the unified executor
                self._tool_handlers[tool_name] = lambda args, tn=tool_name, **kw: unified_executor(tn, args, **kw)
            else:
                logger.warning(f"Extension '{manifest.id}' declared tool '{tool_name}' but provided no handler in tools.py")

    def get_extension(self, extension_id: str) -> Optional[ExtensionManifest]:
        return self._extensions.get(extension_id)

    def list_extensions(self) -> List[Dict[str, Any]]:
        """Returns a serializable list of all discovered extensions."""
        out = []
        for ext in self._extensions.values():
            tool_names = [t.get("function", {}).get("name") for t in ext.tools if "function" in t]
            out.append({
                "id": ext.id,
                "name": ext.name,
                "version": ext.version,
                "description": ext.description,
                "author": ext.author,
                "homepage": ext.homepage,
                "intent_triggers": ext.intent_triggers,
                "enabled": ext.enabled,
                "tool_count": len(tool_names),
                "tools": tool_names,
                "capsule_dir": ext.capsule_dir,
            })
        return out

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tool_handlers

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Returns all tools from all enabled extensions."""
        all_tools = []
        for ext in self._extensions.values():
            if ext.enabled:
                all_tools.extend(ext.tools)
        return all_tools

    def get_scoped_tools(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Returns tools for enabled extensions.
        If query is specified, filters by extension intent triggers.
        Extensions with empty intent_triggers are universally available.
        """
        scoped = []
        q_lower = (query or "").lower().strip()

        for ext in self._extensions.values():
            if not ext.enabled:
                continue

            if not q_lower or not ext.intent_triggers:
                # Mount all if no query or if extension is universal
                scoped.extend(ext.tools)
            else:
                # Check intent triggers
                if any(trigger in q_lower for trigger in ext.intent_triggers):
                    scoped.extend(ext.tools)

        return scoped

    def execute_extension_tool(self, tool_name: str, args: Dict[str, Any], session_id: str = "default") -> Any:
        """
        Executes a registered extension tool.
        Returns the raw result (dict, string, or primitive).
        """
        handler = self._tool_handlers.get(tool_name)
        if not handler:
            raise ValueError(f"Extension tool '{tool_name}' has no registered execution handler.")

        try:
            # Call handler with args and optional session_id keyword
            try:
                return handler(args, session_id=session_id)
            except TypeError:
                return handler(args)
        except Exception as e:
            logger.error(f"Error executing extension tool '{tool_name}': {e}", exc_info=True)
            return {"status": "error", "error": f"Extension execution failed: {str(e)}", "tool": tool_name}


# Global Singleton
extension_manager = ExtensionManager()
