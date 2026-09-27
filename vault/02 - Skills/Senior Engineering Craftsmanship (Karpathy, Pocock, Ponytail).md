---
title: Senior Engineering Craftsmanship (Karpathy, Pocock, Ponytail)
created: 2026-09-25
updated: 2026-09-25
tags:
  - skills/craftsmanship
  - code-quality
  - karpathy
  - matt-pocock
  - ponytail
  - yagni
  - tdd
---

# Senior Engineering Craftsmanship: The Consolidated Playbook

> Synthesis of **Andrej Karpathy**'s LLM coding principles, **Dietrich Gebert**'s Ponytail lazy senior dev ladder, and **Matt Pocock**'s TypeScript architecture & context hygiene flows.

Related: [[00 - MOC/Master MOC]], [[00 - LifeOS/TELOS]], [[01 - Memory/Checkpoints]]

---

## 1. Andrej Karpathy's Principles for AI Coding

*Source: [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)*

1. **Think Before Coding**:
   - Surface assumptions and ambiguities explicitly before writing code.
   - If multiple valid interpretations exist, present them rather than making silent assumptions.
   - Propose simpler alternatives when warranted; push back on unnecessary complexity.
2. **Simplicity First**:
   - Write the minimum code required to solve the problem—nothing speculative.
   - No premature abstractions or single-use helper proliferation.
   - No speculative "flexibility" or unrequested configurability.
   - If 200 lines could be 50, rewrite it.
3. **Surgical Precision**:
   - Touch only what must be touched. Match existing style and idioms.
   - Every modified line must trace directly to the user's explicit objective.
   - Clean up any orphaned imports or dead variables introduced by your edits.
4. **Goal-Driven Execution**:
   - Define concrete, verifiable success criteria before touching code.
   - Loop independently against automated checks until all conditions are green.

---

## 2. Dietrich Gebert's Ponytail: The 7-Rung Ladder of Laziness

*Source: [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)*

> *"The best code is the code never written. Lazy means efficient, not careless."*

Before writing any new logic, climb the ladder from the bottom:
- **Rung 1 (YAGNI)**: Does this actually need to be built at all?
- **Rung 2 (Reuse)**: Does a helper, utility, or pattern already exist in this codebase? Reuse it.
- **Rung 3 (Stdlib)**: Does the standard library already provide this? Use it.
- **Rung 4 (Native Platform)**: Does a native platform, browser, or OS feature cover it? Use it.
- **Rung 5 (Installed Dependencies)**: Does an already-installed package solve it? Use it.
- **Rung 6 (One-Liner)**: Can this be expressed cleanly in one line? Make it one line.
- **Rung 7 (Minimum Working Code)**: Only then write the absolute minimum code that works.

### Root Cause over Symptom Patching
- A bug report names a symptom. Grep all callers of the function you touch and fix the root cause once.
- One guard at the source is cleaner than patching multiple callers.
- **Shortest working diff wins**, but only once the full flow is understood. Deletion over addition. Boring over clever. Fewest files possible.

---

## 3. Matt Pocock's Engineering Flows & Context Hygiene

*Source: [mattpocock/skills](https://github.com/mattpocock/skills)*

1. **Upfront Grilling (`/grill-me`, `/grill-with-docs`)**:
   - Interview the problem upfront to sharpen requirements before writing code.
   - Facts are the agent's job; decisions are the user's.
2. **Deep Module Design**:
   - A deep module provides significant capability behind a small, simple interface at a clean seam.
   - High leverage: callers do minimal work to achieve complex, robust results.
   - Locality: keep related domain concepts together; eliminate pass-through wrappers.
3. **Two-Axis Code Review**:
   - **Axis 1 (Standards)**: Code style, TypeScript safety, absence of `any`, defensive bounds, test coverage.
   - **Axis 2 (Spec)**: Strict compliance with requested scope—no scope creep, no missing acceptance criteria.
4. **Smart Zone Context Management**:
   - Keep complex thinking within the "smart zone" (<150k tokens) before context degradation occurs.
   - Strategically hand off, subagent-delegate, or compact at phase boundaries.
