---
trigger: always_on
description: Performance optimization, context window management, strategic compaction, and documentation hygiene guidelines.
---

# Performance, Context & Compaction Protocol

Inspired by the battle-tested engineering practices of `WorldFlowAI/everything-claude-code`:

## 1. Context Window Management & The 80/20 Rule

Large language models experience degradation and context compression issues near the end of their context window.
- **The 80% Reserve**: Conduct complex architectural changes, multi-file features, and heavy refactorings strictly within the first 80% of the context window.
- **The 20% Cliff**: If context utilization reaches the final 20%:
  - Limit work to single-file fixes, small unit tests, or documentation updates.
  - Snapshot the current state into [`handoff.md`](file:///f:/Maxim/handoff.md) and perform strategic compaction (`/compact`) or start a fresh turn.

## 2. Strategic Compaction vs. Arbitrary Compaction

Never rely on accidental auto-compaction mid-task:
- **Pre-Execution Checkpoint**: Compact after deep research and plan approval, immediately before writing code.
- **Milestone Checkpoint**: Compact immediately after completing a milestone and passing verification, before starting the next phase.
- **Pre-Compact Preservation**: Always write active files, test status, and next steps into [`handoff.md`](file:///f:/Maxim/handoff.md) before compacting.

## 3. Documentation Anti-Pollution Guardrail

Prevent workspace pollution and markdown scattering:
- **Master Documentation**: Root is strictly for canonical documentation (`README.md`, `START_HERE.md`, `RULES.md`, `ARCHITECTURE.md`, `CAPABILITY_MATRIX.md`, `VERIFIED_RUNTIME.md`, `handoff.md`, `TASKS.md`).
- **Reports**: All phase completion summaries MUST go into `reports/COMPLETION_REPORT_PHASE_XX.md`.
- **Architectural Docs & Guides**: Must go into `docs/` (e.g. `docs/SKILLS_AND_AGENTS_ORGANIZATION.md`).
- **Phase Instructions**: Strictly in `Instructions/` (`PHASE_01.md` through `PHASE_15.md`).
- **Strictly Prohibited**: Never drop scratch markdown files, `.tmp` files, or temporary documentation in the project root or source directories.

## 4. Token Efficiency with RTK
- Prefix all shell operations with `rtk` (e.g. `rtk npm test`, `rtk git status`, `rtk vitest`, `rtk cargo test`) to compress outputs by up to 90% and save tokens.
