---
name: creative-ui-and-shaders
description: Professional creative engineering integrating Magic UI animated components, COBE WebGL globe, Paper Design GPU shaders, and React Bits sensory micro-interactions.
---

# Creative UI, Shader Engineering & Micro-Interactions

Consolidates the design systems, mathematical models, and implementation patterns of four state-of-the-art frontend creative engineering frameworks:

1. **Magic UI (`magicuidesign/magicui`)**: High-impact animated component primitives (Bento Grids, Border Beams, Shimmer Buttons, Meteors, Orbiting Badges).
2. **COBE (`shuding/cobe`)**: Ultra-lightweight (5kB) WebGL procedural dot-sphere globe with spring-physics inertia and marker routing.
3. **Paper Design Shaders (`@paper-design/shaders-react`)**: Zero-boilerplate WebGL2 fragment shaders (organic mesh gradients, fluid domain warping, liquid metal, and dithering).
4. **React Bits (`davidhdev/react-bits`)**: Sensory-rich tactile components (DecryptedText matrix decoding, SpotlightCard radial light tracking, Magnet pull, TrueFocus).

---

## 1. When to Apply

Use this skill whenever:
- Upgrading standard flat dashboards or interfaces into high-end, tactile, and cinematic applications.
- Adding planetary connection topology, multi-channel uplinks, or agent telemetry maps (`COBE`).
- Creating dynamic cockpit atmospheric backgrounds, organic color flows, or audio-reactive liquid states (`Paper Shaders`).
- Adding luminous borders, bento card highlights, and polished shimmer CTAs (`Magic UI`).
- Implementing futuristic terminal typography reveals, spotlight cards, and magnetic controls (`React Bits`).

---

## 2. The Four Pillars & Architectural Patterns

### 2.1 Magic UI: Layout Geometry & Border Glow
- **Border Beam**: Uses CSS `offset-path` and conic gradients or SVG stroke offsets to route a glowing beam around arbitrary card geometry.
- **Bento Grid**: Asymmetric CSS Grid (`grid-cols-1 md:grid-cols-3`) providing structured visual hierarchy without boring uniform cards.
- **Shimmer Button**: Uses rotating conic gradient masks behind frosted glass backgrounds for high-converting, premium CTAs.

### 2.2 COBE: Lightweight WebGL Planetary Visualization
- **Zero Heavy Textures**: Renders an interactive Fibonacci sphere directly on the GPU via custom raymarching fragment shaders.
- **Retina Scaling**: Caps `devicePixelRatio` at `min(window.devicePixelRatio, 2)` to guarantee crisp rendering on high-DPI displays without GPU memory strain.
- **Spring Damping**: Smooth drag physics using pointer interaction delta decay (`delta * 0.95`).
- **Resource Discipline**: Enforce strict lifecycle cleanup via `globe.destroy()` on component unmount.

### 2.3 Paper Design Shaders: GPU-Accelerated Atmosphere
- **Component Primitives**: `@paper-design/shaders-react` delivers zero-dependency WebGL2 shaders:
  - `<MeshGradient colors={[...]} distortion={0.8} swirl={0.6} speed={0.15} />`
  - `<LiquidMetal color="#10b981" roughness={0.2} speed={0.2} />`
  - `<Waves color="#3b82f6" amplitude={0.5} frequency={1.2} />`
  - `<Dithering color1="#09090b" color2="#10b981" gridSize={4} />`
- **Domain Warping**: Procedural noise octaves ($fBm$) create organic fluid swirls without video assets or 3D scene graphs.
- **Canvas Stacking**: Position shaders with `pointer-events-none absolute inset-0 opacity-30` behind content for ambient mood without obstructing interaction.

### 2.4 React Bits: Sensory Richness & Tactile Typography
- **DecryptedText**: Character-by-character cyberpunk unscramble animation with configurable glyph sets and iteration speeds.
- **SpotlightCard**: Tracks mouse coordinates within card bounds and renders a dynamic `radial-gradient` highlight across borders and surfaces.
- **Magnet**: Pulls interactive elements toward the cursor on proximity, adding delightful micro-interactions.
- **TrueFocus**: Enhances text readability by magnifying or focusing hovered words while softly blurring background text.

---

## 3. Best Practices & Performance Guardrails

1. **Layer Isolation**: Always isolate continuous animations (canvas, WebGL, RAF loops) in leaf `'use client'` components to prevent parent React re-rendering.
2. **GPU Acceleration**: Animate strictly `transform`, `opacity`, and CSS variables; never animate layout-triggering properties like `width`, `height`, `top`, or `left`.
3. **Accessibility & Reduced Motion**: Check `@media (prefers-reduced-motion: reduce)` and provide instant transitions or static fallbacks.
4. **Contrast & Anti-Slop**: Maintain WCAG 2.2 AA contrast. Use muted dark/light bases (`#09090b` / `#f8fafc`) with a single high-contrast primary accent (Emerald, Blue, or Warm Tan).

---

## 4. Deep Reference Cookbook
For complete TypeScript implementations, mathematical equations, and GLSL code blocks, see:
[`references/creative-ui-and-shaders.md`](file:///f:/MAXIM%20V2/.agents/skills/react-and-web-design/references/creative-ui-and-shaders.md)
