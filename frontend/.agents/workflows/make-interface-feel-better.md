---
description: Audit and elevate UI feeling, tactile responsiveness, clean spacing, and drop-up ergonomics.
---

# `/make-interface-feel-better` — UI Tactile Quality & Ergonomics Workflow

Execute this workflow whenever auditing, refining, or elevating a frontend interface to feel cleaner, more tactile, and ergonomically sound.

---

## Step 1: Clutter & Vertical Spacing Audit
- Inspect all scrollable feeds and conversation canvas views.
- Ensure starter directives, suggestion pills, and engine status banners only appear in **empty states** (`items.length === 0`).
- Ensure no persistent suggestion cards take up space above populated message or document streams.
- Verify message media previews use compact proportional thumbnails (`w-64 h-36`) rather than full-width image blocks.

## Step 2: Combobox & Dropdown Directionality Check
- Inspect all `<select>`, combobox, and dropdown menus across the layout.
- If a combobox or select trigger is located in the **lower third** of a container or screen viewport:
  - Verify it pops **UPWARD** (`bottom-full mb-1.5` / drop-up).
  - Verify it has an upward chevron (`ChevronUp`) with a smooth 180° rotation on open.
  - Verify a click-outside dismiss handler and `Escape` key support are wired.
  - Verify a synced hidden `<select className="sr-only">` is retained for form/test compatibility.

## Step 3: Tabbed State Preservation Verification
- In multi-panel drawers or side docks (e.g. Chat, Intelligence, Activity):
  - Verify tab switching uses CSS display toggling (`hidden` vs `flex` / `block`) rather than conditional unmounting.
  - Test switching between tabs while typing a draft or viewing an attachment to guarantee zero state loss.

## Step 4: Proportional Scale & Focal Points
- Check mascot stages or hero visualizers:
  - If placed alongside active work panes, ensure dimensions are balanced (`w-56 h-32` compact) and do not crush content below them.
  - If placed in a dedicated center stage, ensure it is centered with capability tiles rather than pushed against the edges.

## Step 5: Verification & Quality Gate
- Run `npm run typecheck` to confirm 0 TypeScript errors.
- Run `npm test` to ensure all unit and integration tests remain 100% green.
- Run `npm run lint` to verify zero lint regressions.
