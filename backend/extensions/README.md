# MaxIM Extension Capsules (`backend/extensions/`)

The **Extension Capsule Architecture** allows any external GitHub repository, specialized tool suite, or community agent to be integrated directly into MaxIM without touching core system files (`server.py`, `engine.py`, `catalog.py`).

---

## How to Add Any GitHub Repository as an Extension

1. **Create a folder for the capsule:**
   ```
   backend/extensions/<capsule_name>/
   ```
2. **Place the repository files inside the folder:**
   Copy or clone the repository code into `backend/extensions/<capsule_name>/`.
3. **Add `manifest.json`:**
   ```json
   {
     "id": "my_capsule",
     "name": "My Custom Capsule",
     "version": "1.0.0",
     "description": "Integrates external GitHub capability X into MaxIM.",
     "author": "Your Name / GitHub Author",
     "homepage": "https://github.com/...",
     "intent_triggers": ["keyword1", "keyword2", "keyword3"],
     "enabled": true
   }
   ```
4. **Add `tools.py`:**
   Expose standard OpenAI-compatible tool definitions and an execution handler:
   ```python
   def get_tools() -> list[dict]:
       return [
           {
               "type": "function",
               "function": {
                   "name": "my_custom_tool",
                   "description": "Performs capability X from external repo",
                   "parameters": {
                       "type": "object",
                       "properties": {
                           "param1": {"type": "string", "description": "..."}
                       },
                       "required": ["param1"]
                   }
               }
           }
       ]

   def execute_tool(name: str, args: dict, **kwargs) -> dict:
       if name == "my_custom_tool":
           # Call the repository functions
           return {"status": "success", "result": "..."}
       raise ValueError(f"Unknown tool: {name}")
   ```

---

## Automatic Lifecycle & Capabilities

- **Zero-Config Discovery:** `ExtensionManager` automatically discovers all folders with a valid `manifest.json` on startup or via `extension_manager.discover_extensions()`.
- **Dynamic Intent Scoping:** MaxIM's tool engine matches user prompts against `intent_triggers`. When the user asks for something matching the extension, its tools are dynamically mounted into local/cloud models.
- **REST Telemetry:** The REST API exposes `GET /api/extensions` to inspect all active capsules, status, and exposed tools.
