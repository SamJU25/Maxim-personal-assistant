---
name: graphify
description: Codebase knowledge graph navigation, query, and architecture extraction.
---

# Graphify Knowledge Graph

Rules:
- For codebase or architecture questions, when `graphify-out/graph.json` exists, first run `graphify query "<question>"`.
- Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts.
- If `graphify-out/wiki/index.md` exists, navigate it instead of reading raw files.
- After modifying code files in this session, run `graphify update .` (AST-only, zero API cost).
