---
trigger: always_on
description: Guidance on using installed specialized skills, agents, and tools for MaxIM.
---

# MaxIM Customizations, Skills & Specialized Agents

This workspace is enhanced with specialized skills, agents, workflows, and plugins from `rtk`, `graphify`, and `claude-code-templates`:

## 1. RTK (Rust Token Killer) - Token Compression
- **Rule**: Always prefix shell commands with `rtk` (e.g. `rtk git status`, `rtk vitest run`, `rtk npm test`, `rtk cargo test`, `rtk ls`) to cut output volume by up to 90%.
- Use `rtk gain` to review accumulated savings.

## 2. Graphify Knowledge Graph
- **Rule**: For codebase architecture questions, query `graphify-out/graph.json` via `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"`.
- Rebuild/update the graph after significant file changes using `graphify update .` (AST-only, zero API cost).

## 3. Consolidated Master Skills (`.agents/skills/`)
1. `agency-agents`:  Master Agency persona dispatcher (279 specialists), reality checking, and minimal change.
2. `claude-skills`:  Master catalog router for 731+ skills and agents on demand across the AgenticSkills.io 16-category taxonomy with integrated skill doctor.
3. `code-quality-guardian`:  Defensive coding, zero-hallucination verification, fullstack contracts, and debugging.
4. `react-and-web-design`:  React 19 architecture, luxury web design, 3D WebGL holographic canvas, UI/UX Pro Max intelligence, OpenSEO technical SEO, and purposeful motion.
5. `test-engineering`:  TDD red-green-refactor loop, automated Vitest suites, and Playwright E2E automation.
6. `agent-architecture`:  Agent execution loops, memory tiers, parallel worker pools, BrowserSkill session bridging, and Cursor plugin manifest ingestion.
7. `llm-and-rag-engineering`:  Production RAG pipelines, token budgeting, prompt caching, MCP servers, and Magnitude hardware/model quantization sizing.
8. `voice-agents`:  Speech-to-text, audio visualization, and conversational turn-taking interaction.
9. `graphify`:  Codebase knowledge graph navigation, query, and architecture extraction.

## 4. Specialized Agents (`.agents/agents/`)
- **Master Orchestrator**:
  - `project-orchestrator`: Central project supervisor and dynamic agent/skill router.
- **Multi-Agent Coordination & Planning**:
  - `multi-agent-coordinator`: Inter-agent messaging, synchronization points, distributed execution.
  - `workflow-orchestrator`: DAG execution, saga patterns, business process workflows.
  - `task-decomposition-expert`: Work breakdown structure (WBS), dependency mapping.
  - `agent-organizer`: Team assembly, agent capability matching, roster management.
  - `planner`: Tactical implementation planning and sprint milestones.
  - `error-coordinator`: Cascade failure detection, error recovery strategies.
- **Architecture & System Design**:
  - `code-architect`: Boundary and contract enforcement between MaxIM, Hermes, and Obsidian.
  - `se-system-architecture-reviewer`: Deep architecture audits, system invariants.
  - `microservices-architect`: Component boundary decoupling, protocol contracts.
  - `llm-architect`: LLM serving, local/cloud routing, RAG pipeline, context caching.
  - `api-architect`: REST, WebSocket, JSON-RPC, schema versioning, error contracts.
  - `database-architect`: Schema design, SQLite, indexing, data migrations.
- **Frontend & UI Engineering**:
  - `expert-react-frontend-engineer`: React 19 concurrent mode, streaming hooks, canvas lifecycle.
  - `frontend-developer`: Complete UI development across components, hooks, and views.
  - `ui-ux-designer`: Layout composition, visual hierarchy, user experience refinement.
  - `agency-frontend-developer`: Precision UI implementation with responsive geometry.
  - `agency-3d-scene-developer`: Three.js / WebGL holographic visualization specialist.
  - `agency-whimsy-injector`: Micro-interactions, delight triggers, tactile feedback.
- **Backend & Development Tools**:
  - `backend-architect`: Express server endpoints, SSE streaming, Hermes adapter integration.
  - `agency-backend-architect`: Production server topology, resilient endpoints.
  - `agency-api-platform-engineer`: API design, SSE/WebSocket contracts.
  - `agency-database-optimizer`: SQLite indexing, query optimization, lock avoidance.
  - `agency-database-reliability-engineer`: Database transactions, crash recovery.
  - `agency-minimal-change-engineer`: Surgical refactoring with minimal diffs.
  - `agency-codebase-archaeologist`: Legacy pattern analysis, undocumented dependencies.
  - `agent-memory-engineer`: Multi-tiered agent memory architectures, store indexing, retrieval optimization.
  - `skill-extractor`: Transforms proven patterns and solutions into portable standalone skills.
  - `mcp-expert`: Model Context Protocol servers, tool schemas, lazy loading.
  - `context-manager`: Token budgeting, memory pruning, context serialization.
  - `dependency-manager`: Dependency graphs, lockfile integrity, audit.
  - `git-workflow-manager`: Atomic commits, branch isolation, release hygiene.
- **Obsidian Operations**:
  - `obsidian-connection-agent`: Manages links, backlinks, and graph connectivity in Obsidian.
  - `obsidian-moc-agent`: Generates Maps of Content (MOCs) across the vault.
  - `obsidian-vault-optimizer`: Cleans up orphaned notes and optimizes vault structures.
  - `obsidian-metadata-agent`: Standardizes note metadata, frontmatter, and tags.
  - `agency-knowledge-graph-engineer`: Graph topologies, knowledge extraction, taxonomy.
- **Quality, Security & Research**:
  - `agency-reality-checker`: Demand receipts, stop fantasy approvals, evidence-based sign-off.
  - `agency-evidence-collector`: Screenshot, log, and test proof collector.
  - `agency-ui-finish-gate-reviewer`: UI finish gate, aesthetic excellence, zero placeholders.
  - `code-reviewer`: Deep code inspection, anti-pattern detection, code quality gate.
  - `test-generator`: Automated Vitest test suite generation.
  - `agency-test-automation-engineer`: Full-suite automated test coverage.
  - `agency-performance-benchmarker`: High FPS, frame time, bundle size benchmarking.
  - `accessibility-tester`: WCAG 2.2 AA compliance, ARIA keyboard navigation, contrast audits.
  - `agency-accessibility-auditor`: Deep accessibility audits against screen readers.
  - `se-security-reviewer`: Security vulnerability analysis, auth boundaries, input sanitization.
  - `agency-application-security-engineer`: AppSec, threat boundaries, dependency audit.
  - `agency-ai-generated-code-security-auditor`: Review for hallucinations, security leaks.
  - `agency-secrets-credential-hygiene-engineer`: Secret leaks, token sanitation.
  - `prompt-engineer`: LLM prompt optimization, XML tagging, anti-hallucination.
  - `search-specialist`: Multi-source web research, fact-checking, authoritative synthesis.

## 5. Dynamic Plugins (`.agents/plugins/`)
- `maxim-core`: MaxIM core plugin bundling Obsidian knowledge operations, frontend design systems, canvas visualizers, and graphify knowledge extraction.
- `agency-agents`: Complete 279+ specialist agent roster and JSON catalog from msitarzewski/agency-agents.
- `claude-skills`: Complete 731-item indexed dynamic catalog (`catalog.json`, `query_catalog.py`, `library/`) integrating the AgenticSkills.io 16-category taxonomy (193 skills), Alireza Rezvani, and Jeff Allan skill ecosystems without workspace bloat.

## 6. Hermes Agency Agents Lazy-Router Plugin
- **Location**: `C:\Users\Sam\AppData\Local\hermes\plugins\agency-agents-router`
- **Enabled in**: `C:\Users\Sam\AppData\Local\hermes\config.yaml` (`plugins.enabled: [agency-agents-router]`)
- **Tools**:
  - `agency_agents_search(query, division)`
  - `agency_agents_inspect(agent)`
  - `agency_agents_load(agent)`
  - `agency_agents_delegate(agent, task)`
- Exposes all 279 Agency Agents dynamically to Hermes without catalog bloat.

## 7. Workflows & Slash Commands (`.agents/workflows/`)
- `/orchestrate`: Master multi-agent orchestration workflow across planning, implementation, and review.
- `/verify`: Deterministic 6-phase verification pipeline (Build, Types, Lint, Tests, Security, Diff Review).
- `/learn`: Continuous learning loop extracting patterns into learned skills or memory notes.
- `/generate-tests`: Generate unit and integration tests.
- `/test-coverage`: Run test coverage audits.
- `/web-design-reviewer`: Audit UI against modern visual guidelines.
- `/optimize-bundle-size`: Audit bundle weight and chunking.
- `/performance-audit`: Comprehensive performance and frame rate audit.

## 8. Workspace Organization & Cleanliness Protocol
- **Reports Directory**: All phase completion reports live in `reports/COMPLETION_REPORT_PHASE_XX.md`.
- **Instructions Directory**: `Instructions/` is strictly for phase prompts (`PHASE_01.md` through `PHASE_15.md`), prompt templates, and reference notes.
- **Root Cleanliness**: Root is reserved for configuration and master documentation (`START_HERE.md`, `RULES.md`, `ARCHITECTURE.md`, `handoff.md`, `TASKS.md`). No temporary files.
- **Handoff Continuity**: Update `handoff.md` after every phase.
- **Quality Gates**: All tests (`rtk npm test`), typechecking, and linting must pass with zero errors.


