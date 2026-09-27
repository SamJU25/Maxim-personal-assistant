# Development Context Posture

**Mode**: Active implementation & coding  
**Focus**: Feature building, test writing, refactoring

## Operating Principles
1. **Action-First**: Implement code changes directly, verify with tests, then report.
2. **Implementation Hierarchy**:
   - Step 1: Get it working (functional proof).
   - Step 2: Get it right (contracts, edge cases, error handling).
   - Step 3: Get it clean (readability, zero duplication, minimal churn).
3. **Atomic Changes**: Keep edits scoped to the specific task; avoid collateral file changes.
4. **Tool Priority**: Edit/Write for targeted changes, Bash with `rtk` for rapid verification loops.
