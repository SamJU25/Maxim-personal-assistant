## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## RTK - Rust Token Killer

Always prefix terminal and CLI commands with `rtk` (e.g. `rtk git status`, `rtk npm test`, `rtk vitest`, `rtk cargo test`, `rtk ls`, etc.) to compress output and conserve LLM tokens by up to 90%.
- Use `rtk gain` to review token savings.
- Use `rtk proxy <cmd>` only when raw uncompressed output is strictly necessary.

## Installed Specialized Skills & Agents (from aitmpl.com & claude-code-templates)

### Master Orchestrator
- `project-orchestrator`: Master project orchestrator for task decomposition, dynamic agent routing, and skill mounting.

### Consolidated Master Skills (`.agents/skills/`)
1. `agency-agents`:  Master Agency persona dispatcher (279 specialists), reality checking, and minimal change.
2. `claude-skills`:  Master catalog router for 731+ skills and agents on demand across the AgenticSkills.io 16-category taxonomy with integrated skill doctor.
3. `code-quality-guardian`:  Defensive coding, zero-hallucination verification, fullstack contracts, and debugging.
4. `react-and-web-design`:  React 19 architecture, luxury web design, 3D WebGL holographic canvas, UI/UX Pro Max intelligence, OpenSEO technical SEO, and purposeful motion.
5. `test-engineering`:  TDD red-green-refactor loop, automated Vitest suites, and Playwright E2E automation.
6. `agent-architecture`:  Agent execution loops, memory tiers, parallel worker pools, BrowserSkill session bridging, and Cursor plugin manifest ingestion.
7. `llm-and-rag-engineering`:  Production RAG pipelines, token budgeting, prompt caching, MCP servers, and Magnitude hardware/model quantization sizing.
8. `voice-agents`:  Speech-to-text, audio visualization, and conversational turn-taking interaction.
9. `graphify`:  Codebase knowledge graph navigation, query, and architecture extraction.
10. `make-interface-feel-better`:  Systematic tactile UI/UX polish, micro-interaction ergonomics, viewport-aware combobox directionality, uncluttered content hierarchy, and state-preserving tabbed layouts.

### Specialized Agents (`.agents/agents/`)
- **Orchestration & Planning**:
  - `project-orchestrator`: Central project supervisor and dynamic agent/skill router.
  - `multi-agent-coordinator`: Inter-agent messaging, synchronization points, distributed execution.
  - `workflow-orchestrator`: DAG execution, saga patterns, business process workflows.
  - `task-decomposition-expert`: Work breakdown structure (WBS), dependency mapping.
  - `agent-organizer`: Team assembly, agent capability matching, roster management.
  - `planner`: Tactical implementation planning and sprint milestones.
  - `error-coordinator`: Cascade failure detection, error recovery strategies.
  - `agency-agents-orchestrator`: Autonomous pipeline manager orchestrating full dev workflows.
  - `agency-senior-project-manager`: Scope control, task breakdown, memory across sprints.
  - `agency-project-shepherd`: Cross-functional delivery and blocker removal.
- **Architecture & System Design**:
  - `code-architect`: Boundary and contract enforcement, anti-duplication rules (R01–R40).
  - `se-system-architecture-reviewer`: Deep architecture audits, system invariants.
  - `microservices-architect`: Component boundary decoupling, protocol contracts.
  - `llm-architect`: LLM serving, local/cloud routing, RAG pipeline, context caching.
  - `api-architect`: REST, WebSocket, JSON-RPC, schema versioning, error contracts.
  - `database-architect`: Schema design, SQLite, indexing, data migrations.
  - `agency-codebase-archaeologist`: Decodes legacy patterns, maps undocumented dependencies.
  - `agency-database-optimizer`: SQLite indexing, query profiling, lock minimization.
  - `agency-database-reliability-engineer`: Crash resilience, transactions, WAL integrity.
- **Frontend & UI Engineering**:
  - `expert-react-frontend-engineer`: React 19 concurrent mode, streaming hooks, canvas lifecycle.
  - `frontend-developer`: Complete UI development across components and views.
  - `ui-ux-designer`: Layout composition, visual hierarchy, user experience refinement.
  - `agency-frontend-developer`: Precision UI implementation with responsive geometry.
  - `agency-3d-scene-developer`: Three.js / WebGL holographic visualization specialist.
  - `agency-whimsy-injector`: Micro-interactions, delight triggers, tactile feedback.
  - `agency-brand-guardian`: Aesthetic consistency, typography, color harmony.
- **Backend & Development Tools**:
  - `backend-architect`: Express server endpoints, SSE streaming, Hermes adapter integration.
  - `agency-backend-architect`: Production server topology, resilient endpoints.
  - `agency-api-platform-engineer`: API design, SSE/WebSocket contracts.
  - `agency-minimal-change-engineer`: Surgical refactoring with minimal diffs.
  - `agency-devops-automator`: CI/CD automation, build optimization.
  - `agency-codebase-onboarding-engineer`: Fast architectural ramp-up and documentation.
  - `agency-ai-engineer`: LLM tool wiring, agent prompting, model integration.
  - `agent-memory-engineer`: Multi-tiered agent memory architectures, store indexing, retrieval optimization.
  - `skill-extractor`: Transforms proven patterns and solutions into portable standalone skills.
  - `mcp-expert`: Model Context Protocol servers, tool schemas, lazy loading.
  - `context-manager`: Token budgeting, memory pruning, context serialization.
  - `dependency-manager`: Dependency graphs, lockfile integrity, audit.
  - `git-workflow-manager`: Atomic commits, branch isolation, release hygiene.
- **Obsidian Knowledge Vault**:
  - `obsidian-connection-agent`: Manages Obsidian links and backlinks.
  - `obsidian-moc-agent`: Builds Maps of Content for Obsidian knowledge graphs.
  - `obsidian-vault-optimizer`: Cleans and organizes Obsidian vault structures.
  - `obsidian-metadata-agent`: Standardizes note metadata, frontmatter, and tags.
  - `agency-knowledge-graph-engineer`: Graph topologies, knowledge extraction, taxonomy.
- **Quality, Security & Reality Check**:
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

### Installed Plugins (`.agents/plugins/`)
- `maxim-core`: MaxIM core plugin bundling Obsidian knowledge operations, frontend design systems, canvas visualizers, and graphify knowledge extraction.
- `agency-agents`: Complete 279+ specialist agent roster and JSON catalog from msitarzewski/agency-agents.
- `claude-skills`: Complete 731-item indexed dynamic catalog (`catalog.json`, `query_catalog.py`, `library/`) integrating the AgenticSkills.io 16-category taxonomy (193 skills), Alireza Rezvani, and Jeff Allan skill ecosystems without workspace bloat.

### Hermes Lazy Router Plugin
- `agency-agents-router`: Deployed to `C:\Users\Sam\AppData\Local\hermes\plugins\agency-agents-router` with tools `agency_agents_search`, `agency_agents_inspect`, `agency_agents_load`, and `agency_agents_delegate`. Exposes all 279 Agency Agents dynamically to Hermes without startup catalog bloat.

### Workflows & Slash Commands (`.agents/workflows/`)
- `/orchestrate`: Master multi-agent orchestration workflow across planning, implementation, and review.
- `/verify`: Deterministic 6-phase verification pipeline (Build, Types, Lint, Tests, Security, Diff Review).
- `/learn`: Continuous learning loop extracting patterns into learned skills or memory notes.
- `/generate-tests`: Generate unit and integration tests.
- `/test-coverage`: Run test coverage audits.
- `/web-design-reviewer`: Audit UI against modern visual guidelines.
- `/optimize-bundle-size`: Audit bundle weight and chunking.
- `/performance-audit`: Comprehensive performance and frame rate audit.
- `/make-interface-feel-better`: Systematic UI tactile ergonomics, drop-up directionality, and zero-clutter layout audit.

## Workspace Organization & Cleanliness Protocol

Always maintain an organized workspace:
1. **Reports Directory**: All phase completion reports MUST be written to `reports/COMPLETION_REPORT_PHASE_XX.md`. Never place completion reports in the root directory.
2. **Instructions Directory**: `Instructions/` is strictly for phase prompts (`PHASE_01.md` through `PHASE_15.md`), templates, and reference notes. Never duplicate root documentation files here.
3. **Root Cleanliness**: The root directory is strictly for configuration (`package.json`, tsconfigs, build configs), core canonical documentation (`README.md`, `START_HERE.md`, `RULES.md`, `ARCHITECTURE.md`, `CAPABILITY_MATRIX.md`, `VERIFIED_RUNTIME.md`, `TASKS.md`), and the active operational ledger (`handoff.md`). Never leave temporary, scratch, or backup files in root.
4. **Handoff Continuity**: Keep `handoff.md` at root updated after each phase to guarantee seamless session resumes.
5. **Quality Gates**: Every change must pass `rtk npm test` (30/30 baseline), `rtk npm run typecheck`, and `rtk npm run lint` before completing a phase.

## Senior Engineering Craftsmanship (Karpathy, Pocock, Ponytail)

Always adhere to the consolidated craftsmanship guidelines:
1. **Karpathy Guidelines**: Think before coding (surface tradeoffs & assumptions), simplicity first (zero speculative abstractions), surgical changes (clean your own mess), goal-driven execution (loop against verifiable tests).
2. **Ponytail Ladder of Laziness**: YAGNI -> Existing codebase util -> Stdlib -> Native platform -> Dependency -> One-liner -> Minimum working code. Root-cause over symptom patching; shortest working diff wins.
3. **Pocock Flows & Context Hygiene**: Upfront grilling to clarify requirements, deep module design (high leverage, clean seam), two-axis code review (Standards + Spec), and smart zone context budgeting (<150k tokens).

## Permanent Natural-Human Writing Rules

Write like a thoughtful human who understands the subject and communicates naturally:
1. **Ban Generic AI Rhetoric**: Avoid phrases like "It is important to note", "serves as", "plays a pivotal role", "evolving landscape", "in today's world", "furthermore", "overall", "in conclusion".
2. **No Inflated Facts or Automatic Praise**: Never describe ordinary facts as "groundbreaking", "pivotal", or "transformative". Eliminate promotional adjectives like "vibrant", "breathtaking", "renowned", "sophisticated".
3. **Direct Verbs & Simple Vocabulary**: Prefer "wrote" over "served as the author", "help" over "facilitate", "use" over "utilize", "show" over "demonstrate".
4. **Natural Rhythm & Organic Structure**: Vary sentence length naturally. Avoid mechanical formulaic paragraph sequences (claim → explanation → significance).
5. **No Forced Triads or Contrasts**: Reject automatic rule-of-three groupings and unneeded "not only X, but also Y" constructions.
6. **No Vague Authority**: Never cite "experts say" or "critics argue" without naming sources.
7. **No Chatbot Filler**: Never use "Certainly!", "I hope this helps", "Let me know if you need anything else", or meta-commentary about the writing process.
8. **Stop When Complete**: State what happened directly and concisely. Stop when the thought is finished.

## Ruflo Governance & Anti-Drift Protocol (ruvnet/ruflo)

You MUST follow these rules before doing anything:
1. **Behavioral Invariants (Always Enforced)**:
   - Do what has been asked; nothing more, nothing less.
   - NEVER create files unless they are absolutely necessary for achieving the user's explicit goal.
   - ALWAYS prefer editing an existing file to creating a new one.
   - NEVER proactively create documentation files (*.md) or README files unless explicitly requested.
   - NEVER save working files, text/mds, or tests to the root folder.
   - ALWAYS read a file before editing it.
   - NEVER commit secrets, credentials, or .env files.
2. **Governed Step-by-Step Loop**:
   - `recall → inspect → route → plan → execute → test → validate → benchmark → optimize → receipt → handoff`
   - Execute strictly ONE step at a time.
   - After completing each step: test, validate, and report the exact diff to the user for explicit approval before proceeding to the next step.
   - Never batch multiple unrelated changes across files without checking in.
3. **Architecture & Engineering Discipline**:
   - Follow Domain-Driven Design with clean bounded contexts.
   - Keep files under 500 lines.
   - Use typed interfaces for all public APIs.
   - TDD verification: tests must pass 100% green before marking any step complete.




