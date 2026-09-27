# Ruflo Governance & Anti-Drift Protocol (ruvnet/ruflo)

You MUST follow these rules before doing anything:

## 1. Behavioral Invariants (Always Enforced)
- Do what has been asked; nothing more, nothing less.
- NEVER create files unless they're absolutely necessary for achieving the user's explicit goal.
- ALWAYS prefer editing an existing file to creating a new one.
- NEVER proactively create documentation files (*.md) or README files unless explicitly requested.
- NEVER save working files, text/mds, or tests to the root folder.
- ALWAYS read a file before editing it.
- NEVER commit secrets, credentials, or .env files.

## 2. Governed Step-by-Step Loop
- `recall → inspect → route → plan → execute → test → validate → benchmark → optimize → receipt → handoff`
- Execute strictly ONE step at a time.
- After completing each step: test, validate, and report the exact diff to the user for explicit approval before proceeding to the next step.
- Never batch multiple unrelated changes across files without checking in.

## 3. Architecture & Engineering Discipline
- Follow Domain-Driven Design with clean bounded contexts.
- Keep files under 500 lines.
- Use typed interfaces for all public APIs.
- TDD verification: tests must pass 100% green before marking any step complete.
