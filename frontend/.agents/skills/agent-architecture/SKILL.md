---
name: agent-architecture
description: Agent loops, memory tiers, parallel worker pools, and OS containment.
---

# Agent Architecture & Multi-Agent Systems

Covers autonomous tool loops, multi-tiered memory systems, parallel execution pools, and safe computer use:

## 1. Autonomous Agent Loops & Safety Gates
- **Tool Execution Cycle**: Step formulation -> tool invocation -> observation parse -> state evaluation -> next step.
- **Human-in-the-Loop Gates**: Mandatory safety approval before executing destructive file commands, database drops, or external API mutations.
- **Error Recovery**: Catch tool exceptions gracefully, synthesize error messages, and pivot without terminating the turn.

## 2. Multi-Tiered Memory Architecture
- **Working Memory**: In-context task state, active slots, and immediate scratchpads.
- **Session Memory**: Persistent session ledger (`handoff.md`), status, and active objectives.
- **Episodic & Semantic Memory**: Long-term Obsidian knowledge notes and SQLite vector embeddings.
- **Forgetting Policy**: Prune stale ephemeral context; prevent prompt memory bloat.

## 3. Parallel Worker Pools & Orchestration
- **Task Decomposition**: Split complex epics into DAGs of independent, isolated worker subtasks.
- **Barrier Synchronization**: Wait for parallel subagent completion before aggregating results.
- **Subagent-Driven Development**: Fresh subagent per task + 2-stage spec and quality review.

## 4. Real-Session Browser Bridging (BrowserSkill Architecture)
- **Active Session Attachment**: Connect directly to existing user browser sessions via Chrome DevTools Protocol (CDP port 9222) or simulated tab adapters without launching blank headless windows.
- **Zero-Disruption Invariants**: Execute automated interactions without stealing operating system mouse focus or clearing logged-in authentication cookies (Google, GitHub, SSO).
- **Non-Disruptive DOM Actions**: Dispatch safe JavaScript evaluation and structured DOM commands (`click`, `type`, `scroll`, `extract`).
- **Audit Logging**: Persist action histories into SQLite (`browser_skill_actions`) for traceability and verification receipts.

## 5. Plugin Ecosystem & Manifest Ingestion (Cursor Plugins Architecture)
- **Manifest Standardization**: Ingest and validate standard `plugin.json` manifests declaring craft rules, portable skills, and Model Context Protocol (MCP) server configurations.
- **Dynamic Adapter Pipeline**: Map external plugin rules into agent system prompts, mount skill directories on demand, and bridge MCP tool schemas.
- **Lifecycle Management**: Store installed plugin metadata in SQLite (`cursor_plugins`), supporting runtime enabling, disabling, and version tracking without restarting the agent host.
