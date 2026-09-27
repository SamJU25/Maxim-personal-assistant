---
name: code-quality-guardian
description: Defensive coding, Karpathy guidelines, Ponytail lazy senior dev ladder, Pocock engineering flows, and zero-hallucination verification.
---

# Code Quality Guardian & Senior Engineering Craftsmanship

Unifies defensive programming, zero-hallucination execution, Andrej Karpathy's coding guidelines, Dietrich Gebert's Ponytail lazy-senior-dev ladder, and Matt Pocock's TypeScript & context engineering disciplines into a single consolidated, high-density standard.

---

## 1. Karpathy's Core Guidelines
Derived from Andrej Karpathy's observations on LLM coding pitfalls:
1. **Think Before Coding**:
   - Don't assume. Don't hide confusion. Surface tradeoffs explicitly.
   - If multiple interpretations exist, present them—don't silently choose one.
   - If a simpler approach exists, say so. Push back when warranted.
   - If something is unclear, stop. Name what is confusing and ask.
2. **Simplicity First**:
   - Minimum code that solves the problem. Nothing speculative.
   - No features beyond what was asked. No abstractions for single-use code.
   - No unrequested "configurability" or error handling for impossible scenarios.
   - If 200 lines could be 50, rewrite it.
3. **Surgical Changes**:
   - Touch only what you must. Clean up only your own mess.
   - Do not "improve" adjacent code, comments, or formatting unprompted.
   - Match existing style. Every changed line must trace directly to user intent.
   - If your changes orphan imports or helpers, remove them immediately.
4. **Goal-Driven Execution**:
   - Define concrete, verifiable success criteria before editing. Loop until verified.
   - "Fix bug" → Write reproduction test → Make test pass.
   - "Refactor" → Verify tests pass before and after.

---

## 2. Ponytail's Ladder of Efficient Laziness
The best code is the code never written. Before writing new code, climb the ladder from the bottom:
1. **Rung 1 (YAGNI)**: Does this actually need to be built at all?
2. **Rung 2 (Reuse)**: Does a helper, utility, or pattern already exist in this codebase? Reuse it.
3. **Rung 3 (Stdlib)**: Does the standard library already provide this? Use it.
4. **Rung 4 (Native Platform)**: Does a native platform/browser/OS feature cover it? Use it.
5. **Rung 5 (Installed Dependencies)**: Does an already-installed package solve it? Use it.
6. **Rung 6 (One-Liner)**: Can this be expressed cleanly in one line? Make it one line.
7. **Rung 7 (Minimum Working Code)**: Only then write the absolute minimum code that works.

**Root Cause over Symptom Patching**:
- A bug report names a surface symptom. Grep all callers of the touched function and fix the root cause once. One guard at the source is cleaner than patching multiple callers.
- **Shortest working diff wins**, but only once the full flow is understood. Deletion over addition. Boring over clever. Fewest files possible.

---

## 3. Pocock's Engineering Flows & Context Hygiene
Derived from Matt Pocock's TypeScript & agentic engineering standards:
1. **The Idea-to-Ship Flow**:
   - **Upfront Grilling (`/grill-me`, `/grill-with-docs`)**: Clarify fuzzy requirements through structured questions *before* writing code. Facts are the agent's job; decisions are the user's.
   - **Prototype Detour**: If a question requires a runnable answer (UI feel, state model), create a throwaway prototype to test the hypothesis, then fold the learnings into the real code.
   - **To-Spec & To-Tickets**: Decompose multi-session builds into tracer-bullet tickets with explicit blocking edges.
   - **Two-Axis Code Review**: Review every diff on two independent axes: **Standards** (lint, types, style, security) and **Spec** (did we build what was asked without scope creep?).
2. **Deep Module Design**:
   - A deep module has a lot of functionality behind a small, simple interface at a clean seam.
   - High leverage: caller does very little work to get significant value.
   - Locality: keep related domain logic together. Avoid shallow pass-through abstractions.
3. **Smart Zone Context Management**:
   - Reason within the "smart zone" (<150k tokens) where LLM intelligence is sharpest.
   - Keep idea formulation and spec in one unbroken window.
   - At phase boundaries, choose deliberately: **Continue** (in-flight), **Handoff** (portable checkpoint), **Subagent** (isolated worker), or **Compact** (milestone preservation).

---

## 4. Fullstack Type Safety & Zero Runtime Drift
- **Strict Boundary Contracts**: Enforce shared schemas between client and server (FastAPI Pydantic v2 ↔ TypeScript interfaces).
- **Zero Runtime Drift**: Ensure API request/response payloads match transport types verbatim.
- **No Any Escapes**: Avoid `any`, non-null assertions (`!`), or silent fallback degradation.
