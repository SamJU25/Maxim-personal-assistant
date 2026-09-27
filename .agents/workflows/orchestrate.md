---
description: Multi-agent orchestration workflow across planning and review.
---

# /orchestrate Workflow

Use this workflow to execute complex tasks, phase deliverables, or multi-domain refactoring using the full roster of specialized agents and skills.

## Step 1: Project & Context Analysis
- Review current phase in `handoff.md` and active tasks in `TASKS.md`.
- Inspect code dependencies and architectural boundaries across `src/`, `server/`, `vault/`, and `tests/`.

## Step 2: Task Decomposition & Work Breakdown
- Invoke `task-decomposition-expert` and `planner` to break the task into sequential or parallel milestones.
- Write/update `implementation_plan.md` with:
  - Exact components impacted
  - Assigned specialist agents
  - Mounted skills

## Step 3: Architecture & Contract Review
- Invoke `code-architect` and `api-architect` to verify:
  - Anti-duplication boundaries (R01–R40)
  - Data contracts (TypeScript interfaces, REST/SSE/WS endpoints)
  - Security and state consistency

## Step 4: Implementation (Subagent-Driven Development)
- Mount `subagent-driven-development` skill.
- For each subtask:
  1. Dispatch domain specialist (`expert-react-frontend-engineer`, `backend-architect`, or `obsidian-*`).
  2. Implement code and accompanying tests.
  3. Spec Compliance Review: Verify code matches requested specification.
  4. Code Quality Review: Verify types, styling, security, and performance.

## Step 5: Comprehensive Quality Gates
- Execute verification commands:
  ```bash
  rtk npm test
  rtk npm run typecheck
  rtk npm run lint
  rtk npm run build
  graphify update .
  ```

## Step 6: Documentation & Handoff
- Update `TASKS.md` with completed items.
- Write phase completion report to `reports/COMPLETION_REPORT_PHASE_XX.md`.
- Update `handoff.md` with the latest operational state and resume instructions.
