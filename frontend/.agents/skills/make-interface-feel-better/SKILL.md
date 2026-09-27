---
name: make-interface-feel-better
description: Systematic tactile UI/UX polish, micro-interaction ergonomics, viewport-aware combobox directionality, uncluttered content hierarchy, and state-preserving tabbed layouts.
---

# Make Interface Feel Better — UI/UX Ergonomics & Tactile Polish

A consolidated craftsmanship skill derived from user experience realities, micro-interaction ergonomics, and design system disciplines. Ensures AI-generated interfaces feel premium, tactile, intuitive, and uncluttered.

---

## 1. Anti-Clutter & Content-First Breathing Room

AI tools frequently over-decorate interfaces with persistent helper cards and prompt suggestions. Always enforce:

1. **Empty-State Scoping**:
   - Starter prompts, quick suggestions, and "online" engine badges belong **strictly** in empty states (`items.length === 0`).
   - The moment content exists (messages, files, cards), remove auxiliary banners from the scroll pane. Never permanently pin suggestions above an active feed.
2. **Protect Vertical Real Estate**:
   - Users interact vertically. Limit sticky headers to compact dimensions (~44px–52px).
   - Use proportional media thumbnails (e.g. `w-64 h-36`) rather than full-width image previews that push content out of view.
   - Always ensure scroll containers have `min-h-0` and proper flex constraints so messages never overflow behind fixed input docks.

---

## 2. Viewport-Aware Combobox & Drop-Up Ergonomics

Dropdowns located at the bottom of the viewport create severe usability friction when they open downward.

1. **The Bottom-Dock Invariant**:
   - Any selector, combobox, or menu triggered in the lower third of the viewport (such as input bars, status docks, or bottom command rails) **must open upward** (`bottom-full mb-1.5` / drop-up).
   - Never rely on native `<select>` alone for bottom docks—browsers often default to opening downward and clip against viewport edges or OS taskbars.
2. **Directional Visual Cues**:
   - Use an upward-pointing indicator (`ChevronUp`) for drop-up controls.
   - Rotate the chevron 180° on toggle to provide immediate tactile feedback.
3. **Robust Interaction Contracts**:
   - Always attach a click-outside dismiss listener.
   - Support `Escape` key dismissal.
   - Retain a visually hidden, synchronized `<select className="sr-only">` so automated tests, form submissions, and screen readers continue functioning without disruption.

---

## 3. State-Preserving Workspace Tabs

When consolidating complex toolsets into compact side drawers or split panels:

1. **Zero-Unmount State Preservation**:
   - Never conditionally unmount active working components:
     ```tsx
     // BAD: Destroys scroll position, draft text, and uploaded attachments
     {activeTab === 'chat' && <TelegramChat />}

     // GOOD: Keeps component permanently mounted with zero state loss
     <div className={`flex-1 min-h-0 flex flex-col ${activeTab === 'chat' ? 'flex' : 'hidden'}`}>
       <TelegramChat />
     </div>
     ```
2. **Compact Segmented Switchers**:
   - Group related tools (e.g. Chat, Intelligence, Activity) into single-row segmented buttons (`p-0.5 rounded-xl border border-border-subtle bg-bg-card-subtle`).
   - Highlight active tabs with high-contrast accent backgrounds (`bg-accent text-accent-contrast shadow-xs`) and clear iconography.

---

## 4. Proportional Geometry & Hero Focal Points

Avoid extreme swings in visual scale:

1. **Avoid the Monolith**:
   - Do not let mascot stages, hero banners, or visualizers consume more than 35% of vertical screen height unless they are the sole purpose of the page.
2. **Avoid the Sliver**:
   - Do not shrink character-rich mascots or central focal points into tiny 48px icons where personality and visual detail are destroyed.
3. **Balanced Companion Standard**:
   - Compact Mode: `w-56 h-32` (head) with `w-44 h-22` (visor), saving vertical room while keeping expressive OLED eyes and reactive soundwaves prominent.
   - Centerpiece Mode: `w-80 h-52` (head) with `w-64 h-36` (visor), surrounded by balanced capability telemetry tiles.

---

## 5. Sensory & Micro-Interaction Details

Make elements feel responsive and physical:
- **Button Press Feedback**: Add tactile active states (`active:scale-95`, `transition-all duration-150`).
- **Glow & Highlights**: Use subtle metallic bevel highlights (`bg-gradient-to-r from-transparent via-white/20 to-transparent`) and soft ambient neon blurs rather than harsh saturated dropshadows.
- **Text & Tag Hygiene**: Use `truncate` with informative tooltips or responsive grids to prevent text wrapping from breaking layout alignment.
