---
description: Extract patterns and solutions into reusable skills or memory.
---

# `/learn` — Continuous Learning & Pattern Extraction Workflow

Inspired by `WorldFlowAI/everything-claude-code`, this workflow extracts battle-tested solutions, environment workarounds, and user corrections from the current session into persistent assets.

## When to Run `/learn`
- After resolving a complex bug or cryptic build error.
- When discovering a non-obvious framework quirk or workaround.
- After receiving a specific architectural correction from the user.
- Before ending a major session or milestone.

## Extraction Protocol

### 1. Pattern Identification
Review the recent session trajectory for extractable patterns:
- **Error Resolutions**: Root cause diagnosis, exact fix, and verification steps.
- **User Corrections**: Explicit user guidance that should become durable project policy.
- **Architectural Patterns**: Reusable component or adapter designs that worked cleanly.
- **Environment Workarounds**: Windows powershell quirks, native binary paths, or junction behaviors.

### 2. Delegation to Specialist Agents
- Delegate skill authoring to [`.agents/agents/skill-extractor.md`](file:///f:/Maxim/.agents/agents/skill-extractor.md).
- Delegate memory architecture and durability audits to [`.agents/agents/agent-memory-engineer.md`](file:///f:/Maxim/.agents/agents/agent-memory-engineer.md).

### 3. Output Placement
- **Project-Specific Knowledge**: Append to Obsidian vault (`vault/`) or `RULES.md`.
- **Reusable Skills**: Mint a new skill in `.agents/skills/<skill-name>/SKILL.md` (validated via `skill-doctor`).
- **Operational Ledger**: Record key findings in [`handoff.md`](file:///f:/Maxim/handoff.md).
