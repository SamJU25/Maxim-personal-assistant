---
trigger: always_on
description: Project Orchestration Rule. Guides multi-agent routing, skill mounting, and task execution workflows based on project stack.
---

# Project Agent & Skill Orchestrator Rule

When handling non-trivial engineering tasks, phase milestones, or multi-domain features in this workspace:

## 1. Dynamic Routing & Agent Selection

Evaluate the primary domain of the task and delegate according to the following roster:

| Task Domain | Primary Agent | Supporting Agents | Relevant Skills |
|---|---|---|---|
| **System Architecture & Boundaries** | `code-architect` | `se-system-architecture-reviewer`, `microservices-architect`, `agency-codebase-archaeologist` | `workspace-orchestration`, `autonomous-agent-patterns` |
| **Frontend & UI Components** | `expert-react-frontend-engineer` | `frontend-developer`, `ui-ux-designer`, `agency-frontend-developer`, `agency-3d-scene-developer` | `premium-web-design`, `react-best-practices`, `react-component-performance`, `3d-web-experience`, `canvas-design` |
| **UI Finish Gate & Aesthetics** | `agency-ui-finish-gate-reviewer` | `ui-ux-designer`, `agency-brand-guardian`, `agency-whimsy-injector` | `premium-web-design`, `agency-ui-finish-gate`, `ui-design-system` |
| **Server & Hermes Integration** | `backend-architect` | `api-architect`, `agency-backend-architect`, `agency-api-platform-engineer`, `mcp-expert` | `autonomous-agent-patterns`, `computer-use-agents`, `voice-agents` |
| **Database & State Performance** | `agency-database-optimizer` | `database-architect`, `agency-database-reliability-engineer` | `workspace-orchestration` |
| **Precision Refactoring (Zero Churn)** | `agency-minimal-change-engineer` | `code-architect`, `context-manager` | `agency-minimal-change` |
| **Multi-Agent Workflows & Plans** | `multi-agent-coordinator` | `workflow-orchestrator`, `task-decomposition-expert`, `planner`, `agency-agents-orchestrator` | `subagent-driven-development`, `dispatching-parallel-agents`, `parallel-agents`, `agent-management`, `agency-agents` |
| **Obsidian Knowledge Vault** | `obsidian-connection-agent` | `obsidian-moc-agent`, `obsidian-vault-optimizer`, `agency-knowledge-graph-engineer` | `workspace-orchestration` |
| **Testing & Quality Assurance** | `test-generator` | `code-reviewer`, `agency-test-automation-engineer`, `agency-performance-benchmarker` | `tdd-orchestrator` |
| **Reality Check & Evidence** | `agency-reality-checker` | `agency-evidence-collector`, `code-reviewer` | `agency-reality-checker` |
| **Security & Credential Hygiene** | `se-security-reviewer` | `agency-application-security-engineer`, `agency-ai-generated-code-security-auditor`, `agency-secrets-credential-hygiene-engineer` | `tdd-orchestrator` |

## 2. Multi-Stage Quality Pipeline

For any complex task:
1. **Decompose & Plan**: Split into self-contained tasks with explicit criteria (`task-decomposition-expert`, `agency-codebase-archaeologist`).
2. **Implement**: Apply Subagent-Driven Development with minimal churn (`subagent-driven-development`, `agency-minimal-change-engineer`).
3. **Four-Stage Review**:
   - **Stage 1: Spec Compliance**: Verify all user requirements and phase contracts (`se-system-architecture-reviewer`).
   - **Stage 2: Code Quality & Security**: Static analysis, boundaries, credential hygiene (`code-reviewer`, `agency-application-security-engineer`).
   - **Stage 3: UI Finish Gate**: Review visual polish, micro-interactions, responsive geometry (`agency-ui-finish-gate-reviewer`).
   - **Stage 4: Reality Check**: Verify receipts, logs, and evidence before marking complete (`agency-reality-checker`, `agency-evidence-collector`).
4. **Verify**: Run `rtk npm test`, `rtk npm run typecheck`, and `rtk npm run lint`.
5. **Ledger & Handoff**: Update `handoff.md` and save reports to `reports/COMPLETION_REPORT_PHASE_XX.md`.
