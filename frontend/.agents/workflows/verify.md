---
description: Deterministic 6-phase verification pipeline (Build to Diff).
---

# `/verify` — MaxIM 6-Phase Verification Pipeline

Inspired by `WorldFlowAI/everything-claude-code`, this workflow runs a deterministic 6-phase quality gate before declaring any task, phase, or PR complete.

## Execution Sequence

### Phase 1: Build Verification (Fail Fast)
Ensure the full client and server bundles build without errors:
```powershell
rtk npm run build
```
> [!IMPORTANT]
> If the build fails, **STOP immediately**. Fix the build errors before proceeding to subsequent phases.

### Phase 2: Typecheck Verification
Validate full TypeScript strict typing across both client and server:
```powershell
rtk npm run typecheck
```
Verify 0 errors across `tsconfig.json` and `tsconfig.server.json`.

### Phase 3: Lint & Code Style
Check for lint errors, unused imports, or code smell:
```powershell
rtk npm run lint
```
Must pass with 0 errors and 0 warnings.

### Phase 4: Automated Test Suite & Coverage
Run the Vitest test suite:
```powershell
rtk npm test
```
Verify that all test files pass (baseline: 60/60 passing tests).

### Phase 5: Security & Secret Scan
Scan modified files for exposed API keys, credentials, or stray debug logs:
```powershell
# Check for stray secrets / tokens
rtk git diff --staged | Select-String -Pattern "sk-", "api_key", "password", "token"
# Check for stray console.logs in production code
rtk git diff --staged | Select-String -Pattern "console\.log"
```

### Phase 6: Git Diff Review
Inspect exact changes to prevent unintended modifications or scope creep:
```powershell
rtk git diff --stat
rtk git status --short
```

---

## Output Report Format

Produce a standardized verification summary:

```markdown
### Verification Gate Summary
- **Build**: [PASS / FAIL]
- **TypeScript**: [PASS / FAIL] (0 errors)
- **Lint**: [PASS / FAIL] (0 warnings)
- **Tests**: [PASS / FAIL] (60/60 passing)
- **Security & Secrets**: [PASS / FAIL] (0 leaks)
- **Diff Hygiene**: [PASS / FAIL] (Files reviewed, zero collateral churn)
```
