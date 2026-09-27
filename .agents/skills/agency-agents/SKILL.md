---
name: agency-agents
description: Master Agency persona dispatcher, reality checking, and minimal change.
---

# The Agency Agents Master Skill

Orchestrates **279+ production-grade specialist personas** across 21 divisions, integrating the core Agency quality gates:

## 1. Local Roster & Lazy Router
- **JSON Catalog**: `.agents/plugins/agency-agents/roster.json` (279 personas)
- **Hermes Lazy Router Tools**:
  - `agency_agents_search(query, division)`: Fast keyword search across 279 personas.
  - `agency_agents_inspect(agent)`: Returns full persona definition and boundaries.
  - `agency_agents_load(agent)`: Injects specialist instructions into active context.
  - `agency_agents_delegate(agent, task)`: Spawns an isolated subagent session.

## 2. Integrated Agency Protocols

### A. Reality Checking (`agency-reality-checker`)
- **Default Skepticism**: Never accept "should work" or theoretical assertions.
- **Demand Receipts**: Require verifiable test outputs, build logs, and actual screenshots.
- **Stop Fantasy Approvals**: Block signing off on milestones without concrete execution proof.

### B. Minimal Change Engineering (`agency-minimal-change`)
- **Surgical Precision**: Make the smallest possible diff that completely satisfies the requirement.
- **Zero Collateral Damage**: Never refactor unrelated code, reformat styles, or rename untouched symbols.
- **Anti-Churn**: Keep diffs tight, focused, and easily reviewable.

### C. UI Finish Gate (`agency-ui-finish-gate`)
- **Visual Polish**: Audit typography hierarchy, micro-interactions, responsive geometry, and glassmorphism.
- **Accessibility & Contrast**: Verify WCAG 2.2 AA compliance, keyboard navigation, and focus rings.
- **Zero Placeholders**: Never leave placeholder images or mock data in production surfaces.
