---
name: react-and-web-design
description: React 19, luxury UI design, anti-slop taste, and purposeful motion.
---

# Unified Master Design, Taste & Motion Engineering

Consolidates **React 19 architecture**, **anti-slop frontend taste**, **UI/UX Pro Max design intelligence**, **DESIGN.md design system specifications**, and **purposeful motion engineering** into a single cohesive, non-duplicative master skill.

---

## 0. When to Apply

Use this skill whenever designing, building, reviewing, or refactoring user interfaces:
- Scaffolding new landing pages, web applications, dashboards, or portfolios.
- Setting up a coherent design system, color tokens, typography scales, and spacing rhythms.
- Auditing UI against AI-slop clichés, broken viewports, or low contrast.
- Building interactive motion, scroll-driven animations, transitions, or micro-interactions.
- Optimizing React 19 component performance and canvas rendering loops.

---

## 1. Brief Inference & The Three Dials (Read the Room First)

Before writing markup or styles, **infer what the user actually needs** to avoid default LLM aesthetics (generic AI purple, Inter on slate-900, centered hero over mesh gradient, 3 identical cards).

### 1.1 The One-Line "Design Read"
State in one line before generating code:
> **"Reading this as: `<page kind>` for `<audience>`, with a `<vibe>` visual language, leaning toward `<design system or aesthetic family>`."**

### 1.2 The Three Dials Configuration
Calibrate three dials (1–10 scale) to guide layout asymmetry, animation, and spacing:
- **`DESIGN_VARIANCE`** (1 = Strict Symmetry / Corporate, 10 = Artsy Chaos / Experimental)
- **`MOTION_INTENSITY`** (1 = Static / Instant, 10 = Cinematic / Physics-driven)
- **`VISUAL_DENSITY`** (1 = Art Gallery / Airy, 10 = Cockpit / Data-dense)

| Context / Vibe | VARIANCE | MOTION | DENSITY | Primary Reference |
|---|---|---|---|---|
| B2B SaaS / Productivity (Linear-style) | 5–6 | 3–4 | 4–6 | Emil Kowalski Lens |
| Premium Consumer / Luxury (Apple-adjacent) | 7–8 | 5–7 | 3–4 | Jakub Krehel Lens |
| Creative Studio / Portfolio / Agency | 8–10 | 7–9 | 2–3 | Jhey Tompkins Lens |
| Trust-first / Public-sector / Regulated | 3–4 | 2–3 | 5–7 | System Tokens (Radix/Fluent) |
| Editorial / Publication | 6–7 | 3–4 | 3–4 | Serif/Mono Type Layouts |

---

## 2. UI/UX Pro Max Intelligence CLI (`search.py`)

Searchable local design intelligence engine backed by 79 styles, 192 product palettes, 74 font pairings, 119 UX guidelines, 105 curated icons, 17 GSAP presets, and 22 technology stacks:

```powershell
# 1. Generate full design system for a new project/page
rtk python .agents/skills/react-and-web-design/scripts/search.py "<product_type> <vibe>" --design-system -p "Project Name"

# 2. Tune design system with dials
rtk python .agents/skills/react-and-web-design/scripts/search.py "<query>" --design-system --variance <1-10> --motion <1-10> --density <1-10>

# 3. Persist as MASTER.md source of truth
rtk python .agents/skills/react-and-web-design/scripts/search.py "<query>" --design-system --persist -p "Project Name" --output-dir "."

# 4. Domain-specific queries (domains: style, color, typography, ux, icons, gsap, landing, chart, react, web)
rtk python .agents/skills/react-and-web-design/scripts/search.py "dark glassmorphism" --domain style
rtk python .agents/skills/react-and-web-design/scripts/search.py "saas high contrast" --domain color
rtk python .agents/skills/react-and-web-design/scripts/search.py "keyboard focus trap" --domain ux

# 5. Stack-specific implementation rules (react, nextjs, html-tailwind, shadcn, threejs, swiftui, etc.)
rtk python .agents/skills/react-and-web-design/scripts/search.py "memo list virtualization" --stack react
rtk python .agents/skills/react-and-web-design/scripts/search.py "server components streaming" --stack nextjs
```

---

## 3. Anti-Slop Frontend Taste & Aesthetic Directives

### 3.1 Typography Discipline
- **Default Display Headlines:** `text-4xl md:text-6xl tracking-tighter leading-none`.
- **Sans Display Default:** Reach for `Geist`, `Outfit`, `Cabinet Grotesk`, `Satoshi`, `Plus Jakarta Sans`, or `PP Neue Montreal`. Avoid defaulting to standard `Inter` unless requested.
- **Serif Restrictions:** Serif is **banned as a lazy proxy for "creative/luxury"**.
  - **Banned as defaults:** `Fraunces` and `Instrument_Serif`.
  - Use serif ONLY when the brand brief explicitly requires it or is genuinely literary/heritage.
  - When justified, rotate: `PP Editorial New`, `GT Sectra`, `Cormorant Garamond`, `Tiempos`, `Recoleta`, `EB Garamond`.
  - Never mix a serif emphasis word into a sans headline; use bold/italic of the **same font family**.
- **Italic Descender Clearance:** When using italic display text with descenders (`y, g, j, p, q`), use `leading-[1.1]` minimum and `pb-1` to prevent clipping.

### 3.2 Color Calibration & Anti-Default Guardrails
- **The Lila Rule:** Generic AI purple/cyan glowing gradient cards are prohibited. Use neutral bases (Zinc/Slate/Stone) with single high-contrast accents (Emerald, Electric Blue, Deep Rose, Burnt Orange).
- **The Premium-Consumer Anti-Beige Rule:** Banned default palette: warm cream (`#f5f1ea`) + brass/clay/oxblood (`#b08947`, `#9a2436`) + espresso text.
  - Rotate alternatives: **Cold Luxury** (silver-grey + chrome + smoke), **Forest** (deep green + bone + amber), **Black & Tan** (sharp off-black + warm tan), **Cobalt + Cream** (saturated blue on clean neutral).
- **Color Consistency Lock:** Max 1 primary accent color. Lock it across every section; never switch accent colors halfway down the page.

### 3.3 Layout Diversification & Geometry
- **Anti-Center Bias:** When `DESIGN_VARIANCE > 4`, avoid centered hero headers. Force split-screen (50/50), left-aligned copy with right asset, or asymmetric whitespace.
- **Hero Viewport Discipline:**
  - Hero **must fit in the initial viewport** (`min-h-[100dvh]`, never `h-screen`).
  - Top padding capped at `pt-24` max.
  - Headline max 2 lines desktop; subtext max 20 words / 4 lines.
  - CTAs visible above the fold without scrolling.
  - Max 4 text elements in hero: (1) Eyebrow/brand mark, (2) Headline, (3) Subtext, (4) CTAs. Trust logo walls belong in a separate section below hero.
- **Eyebrow Restraint:** Max 1 uppercase tracking eyebrow per 3 sections. Hero counts as one. Never place eyebrows on every section.
- **Section Layout Repetition Ban:** Never repeat the same layout family consecutively. Zigzag alternating image/text splits capped at 2 in a row.
- **Bento Grid Discipline:** Exactly as many cells as content items (no blank filler cells). Minimum 2–3 cells must feature real visual variation (images, tinted backgrounds, subtle patterns).
- **CTA Button Wrap Ban:** Button text must never wrap to multiple lines at desktop (max 1–3 words). No duplicate CTA intents on one page (e.g., unify "Contact us", "Get in touch", "Let's talk" to one consistent label).

### 3.4 Visual Asset Priority
1. **AI Image Tools First:** Use available image generation tools to produce section-specific hero visuals and product mockups.
2. **Real Photography Second:** Use Unsplash / Picsum descriptive seeds (`https://picsum.photos/seed/{seed}/{w}/{h}`).
3. **Real SVG Brand Logos:** Use Simple Icons (`https://cdn.simpleicons.org/{slug}/ffffff`) for trust bars.
4. **Prohibited:** Div-based fake UI screenshots and decorative hand-rolled SVG doodles.

---

## 4. The `DESIGN.md` System Specification Standard

Every production project benefits from a companion `DESIGN.md` file that bridges `AGENTS.md` and UI engineering. Follow the 9 standard sections:

1. **Visual Theme & Atmosphere**: Mood, density tier, aesthetic identity.
2. **Color Palette & Semantic Roles**: CSS variables with tokens (`--color-primary`, `--color-background`, `--color-accent`, etc.).
3. **Typography Rules**: Display, body, mono type scale and line-heights.
4. **Component Stylings**: Interactive states (default, hover, active, focus, disabled).
5. **Layout Principles**: Spacing scale, container max-widths (`max-w-7xl`), grid rules.
6. **Depth & Elevation**: Layered borders, tinted shadows, glassmorphism refraction.
7. **Do's and Don'ts**: Concrete guardrails preventing AI-slop regressions.
8. **Responsive Behavior**: Breakpoints (`sm: 640`, `md: 768`, `lg: 1024`, `xl: 1280`).
9. **Agent Prompt Guide**: Ready-to-use prompts for generating screens on-system.

*Refer to [references/design-md-spec.md](file:///f:/Maxim/.agents/skills/react-and-web-design/references/design-md-spec.md) for 68+ curated brand design system archetypes (Linear, Vercel, Stripe, Raycast, Supabase, Apple, etc.).*

---

## 5. Purposeful Motion Engineering (The Three Designers)

Motion must be motivated. Unmotivated animation is amateur clutter.

### 5.1 The Three Designers Framework
- **Emil Kowalski (Linear / Vercel):** Restraint, speed, efficiency. Durations < 300ms (180ms ideal). Best for productivity tools and B2B SaaS.
- **Jakub Krehel (jakub.kr):** Subtle production polish, smoothness (200–500ms). Best for consumer apps and mobile.
- **Jhey Tompkins (@jh3yy):** Playful delight, innovative CSS, micro-interactions. Best for landing pages and portfolios.

### 5.2 The Frequency Gate
| Frequency | Motion Rule |
|---|---|
| **Rare** (monthly / onboarding) | Expressive, delightful animations welcome |
| **Occasional** (daily interactions) | Fast, subtle, purposeful motion (150–250ms) |
| **Frequent** (100s/day: navigation, table rows) | Instant or zero animation (< 100ms) |
| **Keyboard-initiated** (shortcuts, command bar) | Never animate position; instant transition |

### 5.3 Canonical Animation Skeletons
- **Sticky-Stack (GSAP ScrollTrigger):** Pinned cards stacking on scroll with scale/opacity scrub.
- **Horizontal-Pan (GSAP):** Horizontal travel pinned to vertical scroll distance.
- **Scroll-Reveal Stagger (Motion):** `whileInView` with `staggerChildren` and `prefers-reduced-motion` check.

*See [references/taste-and-anti-slop.md](file:///f:/Maxim/.agents/skills/react-and-web-design/references/taste-and-anti-slop.md) and [references/motion/motion-cookbook.md](file:///f:/Maxim/.agents/skills/react-and-web-design/references/motion/motion-cookbook.md) for complete code implementations.*

---

## 6. React 19 Architecture & Component Performance

- **Server vs Client Boundary:** Keep layout, data-fetching, and static content in Server Components (RSC). Isolate animations, motion values, and event listeners in leaf `'use client'` components.
- **Strict Hook Discipline:**
  - **NEVER** use React `useState` for continuous values (mouse tracking, scroll progress, physics). Use Motion's `useMotionValue` / `useTransform` / `useScroll` to prevent frame-by-frame re-rendering.
  - Animate ONLY `transform` and `opacity`. Never animate `top`, `left`, `width`, or `height`.
- **High FPS Decoupling:** Decouple canvas loops from React state using refs and `requestAnimationFrame`.
- **Memory & DOM Cleanup:** Always clean up event listeners, ResizeObservers, GSAP contexts (`ctx.revert()`), and WebGL geometries/materials.

---

## 7. 3D WebGL Holographic Experiences & Reactive Canvas Waveforms

Consolidates cinematic holographic visualizers and reactive audio graphics:
- **Three.js / WebGL Holographic Core**:
  - Dynamic perspective cameras, particle point clouds, glowing geometric lattices, and custom GLSL shaders.
  - Orbital state dynamics: Morph visual states smoothly across agent modes (`idle`, `listening`, `thinking`, `speaking`, `executing`).
  - Resource lifecycle: Cache and reuse geometries and materials; dispose unused textures and call `renderer.dispose()` to eliminate WebGL context leaks.
- **Reactive 2D Canvas Waveforms**:
  - Audio telemetry: Real-time frequency bin processing, smooth interpolation, and peak detection.
  - Visual fidelity: Dual-wave orbital oscilloscopes, particle ripples, and reactive glow effects.
  - DPI scaling: Always handle high-DPI/retina displays by multiplying canvas dimensions with `window.devicePixelRatio`.

---

## 8. Generative Engine Optimization (GEO) & Technical SEO (OpenSEO Architecture)

Ensures web applications and documentation are natively discoverable by search engines and AI generative models:
- **Title Tag Calibration**: Ensure length is strictly between 30 and 65 characters; place high-priority entity keywords in the first 3 words.
- **Meta Description Health**: Maintain character count within the optimal 100–165 character range; describe unique value propositions clearly.
- **Strict Heading Hierarchy**: Enforce exactly one primary `<h1>` element per page. Structure sections sequentially using semantic `<h2>` and `<h3>` tags without skipping levels.
- **OpenGraph & Social Snippets**: Complete rich media tags (`og:title`, `og:description`, `og:image`, `og:url`, `twitter:card`) for link previews.
- **Canonicalization**: Always define `<link rel="canonical" href="...">` to prevent duplicate content indexing.
- **Accessibility & Image SEO**: Enforce meaningful, descriptive `alt` attributes on every `<img>` tag; avoid empty or purely decorative placeholders without `aria-hidden="true"`.
- **Structured Data (Schema.org / JSON-LD)**: Embed structured data (`SoftwareApplication`, `Article`, `Organization`, or `WebSite`) so LLM crawlers parse system capabilities deterministically.
- **Automated Audit Reporting**: Generate actionable SEO scorecards and export remediation notes into the Obsidian knowledge vault.

---

## 9. Pre-Delivery Quality Gate

Before declaring UI work complete, execute this verification checklist:
- [ ] **Contrast Check:** WCAG 2.2 AA compliant (4.5:1 text, 3:1 large text) for both light and dark modes.
- [ ] **Reduced Motion:** Every animation honors `prefers-reduced-motion` (instant fallback).
- [ ] **Viewport Fit:** Hero fits in desktop viewport without scrolling (`min-h-[100dvh]`).
- [ ] **Touch Targets:** Minimum 44×44px with 8px+ padding between interactive elements.
- [ ] **Keyboard Nav:** Visible focus indicators (`focus-visible:ring-2`) on all interactive controls.
- [ ] **CTA Wrap Check:** Primary button labels fit on one line at desktop.
- [ ] **Zero Emoji Icons:** All icons sourced from standard SVG libraries (Phosphor / Radix / Heroicons).
- [ ] **Copy Self-Audit:** Zero hallucinated or broken copy; register is uniform across sections.
- [ ] **Technical SEO:** Validated `<title>`, `<meta name="description">`, single `<h1>`, OpenGraph tags, and Schema.org markup.

---

## 10. Deep Reference Directory

Load specialized guides on-demand without context bloat:
- **Creative UI & Shaders (Magic UI, COBE, Paper Shaders, React Bits):** [references/creative-ui-and-shaders.md](file:///f:/MAXIM%20V2/.agents/skills/react-and-web-design/references/creative-ui-and-shaders.md)
- **Taste & Anti-Slop Guide:** [references/taste-and-anti-slop.md](file:///f:/Maxim/.agents/skills/react-and-web-design/references/taste-and-anti-slop.md)
- **UI/UX Pro Max Rules & Taxonomy:** [references/ui-ux-pro-rules.md](file:///f:/Maxim/.agents/skills/react-and-web-design/references/ui-ux-pro-rules.md) & [references/ui-ux-quick-reference.md](file:///f:/Maxim/.agents/skills/react-and-web-design/references/ui-ux-quick-reference.md)
- **DESIGN.md Specification & 68+ Systems:** [references/design-md-spec.md](file:///f:/Maxim/.agents/skills/react-and-web-design/references/design-md-spec.md)
- **Motion Principles & Cookbook:** [references/motion/motion-cookbook.md](file:///f:/Maxim/.agents/skills/react-and-web-design/references/motion/motion-cookbook.md) & [references/motion/anti-checklist.md](file:///f:/Maxim/.agents/skills/react-and-web-design/references/motion/anti-checklist.md)
- **Motion Workflows:** [references/motion/workflows/create.md](file:///f:/Maxim/.agents/skills/react-and-web-design/references/motion/workflows/create.md) & [references/motion/workflows/audit.md](file:///f:/Maxim/.agents/skills/react-and-web-design/references/motion/workflows/audit.md)
