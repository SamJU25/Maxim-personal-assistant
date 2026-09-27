# Master Reference: Creative UI Engineering & Shader Architecture
## Magic UI • COBE WebGL Globe • Paper Shaders • React Bits

This manual documents the architectural paradigms, mathematical models, GLSL shader techniques, and React 19 implementation standards for four premier modern creative engineering libraries:

1. **Magic UI (`magicuidesign/magicui`)** — Modern animated component primitives, bento grids, border beams, shimmer interactions.
2. **COBE (`shuding/cobe`)** — 5kB WebGL procedural dot-sphere globe with spring-damped rotation, markers, and arcs.
3. **Paper Design Shaders (`paper-design/shaders` / `shaders.paper.design`)** — WebGL2 GPU fragment shaders: mesh gradients, fluid domain warping, liquid metal, and dithering.
4. **React Bits (`DavidHDev/react-bits` / `reactbits.dev`)** — Sensory-rich interactive React components: decrypted cipher typography, spotlight radial glow, magnetic physics, and canvas backgrounds.

---

## 1. Magic UI (`magicuidesign/magicui`)

### 1.1 Philosophy & Design Engineering Principles
- **Copy-Paste Ownership**: Zero bloated third-party abstractions; components are direct, self-contained primitives adhering to the shadcn archetype.
- **Micro-Interaction Hierarchy**: Layered visual depth using subtle borders, ambient perimeter glow, and physics-driven spring easing.
- **Tailwind CSS + Pure CSS/Motion**: Animations are powered by hardware-accelerated CSS transforms (`transform`, `opacity`, `filter`) and conic/radial gradients.

### 1.2 Core Component Blueprints

#### A. Border Beam
The Border Beam creates an animated radiant comet tracing the boundary of a container or card without altering box model dimensions.

```tsx
import React from 'react';

interface BorderBeamProps {
  className?: string;
  size?: number;
  duration?: number;
  borderWidth?: number;
  anchor?: number;
  colorFrom?: string;
  colorTo?: string;
  delay?: number;
}

export const BorderBeam: React.FC<BorderBeamProps> = ({
  className = '',
  size = 200,
  duration = 12,
  anchor = 90,
  borderWidth = 1.5,
  colorFrom = '#10b981',
  colorTo = '#3b82f6',
  delay = 0,
}) => {
  return (
    <div
      style={
        {
          '--size': `${size}px`,
          '--duration': `${duration}s`,
          '--anchor': `${anchor}%`,
          '--border-width': `${borderWidth}px`,
          '--color-from': colorFrom,
          '--color-to': colorTo,
          '--delay': `-${delay}s`,
        } as React.CSSProperties
      }
      className={`pointer-events-none absolute inset-0 rounded-[inherit] [border:calc(var(--border-width))_solid_transparent] 
      ![mask-clip:padding-box,border-box] ![mask-composite:intersect] 
      [mask:linear-gradient(transparent,transparent),linear-gradient(white,white)] 
      after:absolute after:aspect-square after:w-[calc(var(--size))] 
      after:animate-border-beam after:[animation-delay:var(--delay)] 
      after:[background:linear-gradient(to_left,var(--color-from),var(--color-to),transparent)] 
      after:[offset-anchor:calc(var(--anchor))_50%] after:[offset-path:rect(0_auto_auto_0_round_calc(var(--size)))] ${className}`}
    />
  );
};
```

#### B. Shimmer Button
A tactile button incorporating a sweeping conic gradient reflection behind a translucent surface, giving an illuminated glass/metallic luster.

```tsx
import React from 'react';

interface ShimmerButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  shimmerColor?: string;
  shimmerSize?: string;
  borderRadius?: string;
  shimmerDuration?: string;
  background?: string;
  children?: React.ReactNode;
}

export const ShimmerButton: React.FC<ShimmerButtonProps> = ({
  shimmerColor = '#ffffff',
  shimmerSize = '0.1em',
  shimmerDuration = '2.5s',
  borderRadius = '100px',
  background = 'rgba(18, 18, 21, 0.95)',
  children,
  className = '',
  ...props
}) => {
  return (
    <button
      style={
        {
          '--spread': '90deg',
          '--shimmer-color': shimmerColor,
          '--radius': borderRadius,
          '--speed': shimmerDuration,
          '--cut': shimmerSize,
          '--bg': background,
        } as React.CSSProperties
      }
      className={`group relative z-0 flex cursor-pointer items-center justify-center overflow-hidden whitespace-nowrap border border-white/10 px-6 py-2.5 text-white [background:var(--bg)] [border-radius:var(--radius)] active:scale-95 transition-transform duration-150 ${className}`}
      {...props}
    >
      {/* Conic Glow Spark */}
      <div className="absolute inset-0 -z-30 overflow-visible [container-type:size]">
        <div className="absolute inset-0 h-[100cqh] animate-shimmer-slide [aspect-ratio:1] [border-radius:0] [mask:none]">
          <div className="animate-spin-around absolute -inset-full w-auto rotate-0 [background:conic-gradient(from_calc(270deg-(var(--spread)*0.5)),transparent_0,var(--shimmer-color)_var(--spread),transparent_var(--spread))] [translate:0_0]" />
        </div>
      </div>
      {children}
      {/* Highlight Backdrop */}
      <div className="absolute [background:var(--bg)] [border-radius:var(--radius)] [inset:var(--cut)] -z-20" />
    </button>
  );
};
```

#### C. Bento Grid Architecture
- Asymmetric CSS Grid: `grid grid-cols-1 md:grid-cols-3 gap-4`.
- Standard cell distribution:
  - Hero span: `col-span-2 row-span-2`
  - Stat cards: `col-span-1 row-span-1`
  - Wide telemetry bar: `col-span-3 row-span-1`
- Subtle inner gradient hover: `group-hover:opacity-100 transition-opacity bg-gradient-to-t from-emerald-500/10 via-transparent to-transparent`.

---

## 2. COBE (`shuding/cobe`)

### 2.1 Technical Architecture
- **5kB Footprint**: Procedural raymarched WebGL sphere. Renders thousands of sampled points distributed across a Fibonacci sphere.
- **Texture-Free**: Eliminates heavy 2048x1024 landmass PNG/JPG maps by encoding world geography mathematically into vertex/fragment computations.
- **Retina Precision**: Renders at `canvas.width = size * window.devicePixelRatio` while styling canvas CSS dimensions to `100%`, preventing blurred pixels on High-DPI screens.

### 2.2 Mathematical Model
- **Spherical Coordinate Mapping**:
  $$\phi \in [0, 2\pi], \quad \theta \in [-\frac{\pi}{2}, \frac{\pi}{2}]$$
  $$\mathbf{P} = \begin{bmatrix} \cos(\theta) \sin(\phi) \\ \sin(\theta) \\ \cos(\theta) \cos(\phi) \end{bmatrix}$$
- **Spring Rotation & Velocity Damping**:
  $$\phi_{t+1} = \phi_t + v_\phi$$
  $$v_{\phi, t+1} = v_{\phi, t} \times \mu \quad (\mu \approx 0.95)$$

### 2.3 Production React 19 Component

```tsx
import React, { useEffect, useRef } from 'react';
import createGlobe from 'cobe';

interface CobeGlobeProps {
  className?: string;
  markers?: Array<{ location: [number, number]; size: number }>;
  baseColor?: [number, number, number];
  markerColor?: [number, number, number];
  glowColor?: [number, number, number];
  diffuse?: number;
  mapSamples?: number;
  mapBrightness?: number;
  dark?: number;
}

export const CobeGlobe: React.FC<CobeGlobeProps> = ({
  className = '',
  markers = [
    { location: [37.7749, -122.4194], size: 0.05 }, // SF
    { location: [51.5074, -0.1278], size: 0.05 },  // London
    { location: [35.6762, 139.6503], size: 0.06 }, // Tokyo
  ],
  baseColor = [0.1, 0.1, 0.14],
  markerColor = [0.06, 0.72, 0.51], // Emerald
  glowColor = [0.15, 0.2, 0.3],
  diffuse = 1.2,
  mapSamples = 16000,
  mapBrightness = 6,
  dark = 1,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const pointerInteracting = useRef<number | null>(null);
  const pointerInteractionMovement = useRef<number>(0);
  const phiRef = useRef<number>(0);

  useEffect(() => {
    let width = 0;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const onResize = () => {
      if (canvas) {
        width = canvas.offsetWidth;
      }
    };
    window.addEventListener('resize', onResize);
    onResize();

    const globe = createGlobe(canvas, {
      devicePixelRatio: Math.min(window.devicePixelRatio || 1, 2),
      width: width * 2,
      height: width * 2,
      phi: 0,
      theta: 0.25,
      dark,
      diffuse,
      mapSamples,
      mapBrightness,
      baseColor,
      markerColor,
      glowColor,
      markers,
      onRender: (state) => {
        if (!pointerInteracting.current) {
          phiRef.current += 0.003;
        }
        state.phi = phiRef.current + pointerInteractionMovement.current;
        state.width = width * 2;
        state.height = width * 2;
      },
    });

    return () => {
      globe.destroy();
      window.removeEventListener('resize', onResize);
    };
  }, [baseColor, dark, diffuse, glowColor, mapBrightness, mapSamples, markerColor, markers]);

  return (
    <div className={`relative aspect-square w-full max-w-[500px] flex items-center justify-center ${className}`}>
      <canvas
        ref={canvasRef}
        className="w-full h-full cursor-grab active:cursor-grabbing"
        onPointerDown={(e) => {
          pointerInteracting.current = e.clientX - pointerInteractionMovement.current;
        }}
        onPointerUp={() => {
          pointerInteracting.current = null;
        }}
        onPointerOut={() => {
          pointerInteracting.current = null;
        }}
        onMouseMove={(e) => {
          if (pointerInteracting.current !== null) {
            const delta = e.clientX - pointerInteracting.current;
            pointerInteractionMovement.current = delta * 0.005;
          }
        }}
        onTouchMove={(e) => {
          if (pointerInteracting.current !== null && e.touches[0]) {
            const delta = e.touches[0].clientX - pointerInteracting.current;
            pointerInteractionMovement.current = delta * 0.005;
          }
        }}
      />
    </div>
  );
};
```

---

## 3. Paper Design Shaders (`paper-design/shaders`)

### 3.1 Architectural Structure
- **Zero Three.js Overhead**: Directly compiles GLSL fragment shaders on an isolated WebGL2 canvas context via `ShaderMount`.
- **Procedural Organic Motion**: Employs continuous mathematical noise functions (Simplex, Voronoi, Curl Noise, fBm) instead of heavy pre-rendered video loops.
- **Full Spectrum of Presets**:
  - `MeshGradient`: Multi-point color distortion with swirling vectors.
  - `LiquidMetal`: Chromatic reflection with specular highlights and normal vectors.
  - `Waves`: Undulating wave harmonics for audio and telemetry visualization.
  - `Dithering`: 4x4 / 8x8 Bayer matrix quantization eliminating color banding on OLED and LCD displays.

### 3.2 GLSL Fragment Shader Mechanics

#### Domain Warping Equation
$$f(\mathbf{p}) = \text{fBm}(\mathbf{p} + \alpha \cdot \text{fBm}(\mathbf{p} + \beta \cdot \text{fBm}(\mathbf{p})))$$
This nested evaluation creates complex, non-repeating marble swirls and fluid eddies with minimal GPU cycles.

#### Normal Calculation & Specular Lighting
To render liquid chrome or water ripples from procedural height fields:
$$\mathbf{n} = \text{normalize}\left(\begin{bmatrix} h(x+\epsilon, y) - h(x-\epsilon, y) \\ h(x, y+\epsilon) - h(x, y-\epsilon) \\ 2\epsilon \end{bmatrix}\right)$$
$$I_{\text{spec}} = (\mathbf{n} \cdot \mathbf{h})^{\gamma} \quad (\gamma \approx 32.0)$$

### 3.3 React Integration via `@paper-design/shaders-react`

```tsx
import React from 'react';
import { MeshGradient, LiquidMetal, Waves, Dithering } from '@paper-design/shaders-react';

interface ShaderBackdropProps {
  mode?: 'mesh' | 'liquid' | 'waves' | 'dither';
  className?: string;
  colors?: string[];
}

export const ShaderBackdrop: React.FC<ShaderBackdropProps> = ({
  mode = 'mesh',
  className = '',
  colors = ['#09090b', '#10b981', '#18181b', '#3b82f6'],
}) => {
  return (
    <div className={`absolute inset-0 pointer-events-none overflow-hidden opacity-40 ${className}`}>
      {mode === 'mesh' && (
        <MeshGradient
          colors={colors}
          distortion={0.8}
          swirl={0.6}
          speed={0.15}
          style={{ width: '100%', height: '100%' }}
        />
      )}
      {mode === 'liquid' && (
        <LiquidMetal
          color="#10b981"
          roughness={0.2}
          speed={0.2}
          style={{ width: '100%', height: '100%' }}
        />
      )}
      {mode === 'waves' && (
        <Waves
          color="#3b82f6"
          amplitude={0.5}
          frequency={1.2}
          speed={0.25}
          style={{ width: '100%', height: '100%' }}
        />
      )}
      {mode === 'dither' && (
        <Dithering
          color1="#09090b"
          color2="#10b981"
          gridSize={4}
          style={{ width: '100%', height: '100%' }}
        />
      )}
    </div>
  );
};
```

---

## 4. React Bits (`davidhdev/react-bits`)

### 4.1 Component Archetypes & sensory Interactions

#### A. DecryptedText (Cyberpunk Hacker Unscramble)
Reveals text character-by-character while cycling surrounding glyphs through a randomized glyph pool, creating a futuristic terminal decoding aesthetic.

```tsx
import React, { useEffect, useState } from 'react';

interface DecryptedTextProps {
  text: string;
  speed?: number;
  maxIterations?: number;
  characters?: string;
  className?: string;
  revealDirection?: 'start' | 'end' | 'center';
  useOriginalCharsOnly?: boolean;
}

export const DecryptedText: React.FC<DecryptedTextProps> = ({
  text,
  speed = 50,
  maxIterations = 10,
  characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+',
  className = '',
}) => {
  const [displayText, setDisplayText] = useState<string>(text);

  useEffect(() => {
    let iteration = 0;
    const interval = setInterval(() => {
      setDisplayText(
        text
          .split('')
          .map((char, index) => {
            if (char === ' ') return ' ';
            if (index < iteration) {
              return text[index];
            }
            return characters[Math.floor(Math.random() * characters.length)];
          })
          .join('')
      );

      if (iteration >= text.length) {
        clearInterval(interval);
      }
      iteration += 1 / (maxIterations / text.length || 1);
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed, maxIterations, characters]);

  return <span className={className}>{displayText}</span>;
};
```

#### B. SpotlightCard (Radial Cursor Tracking Glow)
Tracks the user's cursor within card bounds, setting dynamic CSS coordinates to project a subtle, focused halo across borders and surfaces.

```tsx
import React, { useRef, useState } from 'react';

interface SpotlightCardProps extends React.HTMLAttributes<HTMLDivElement> {
  spotlightColor?: string;
  children: React.ReactNode;
}

export const SpotlightCard: React.FC<SpotlightCardProps> = ({
  spotlightColor = 'rgba(16, 185, 129, 0.12)', // Emerald glow
  children,
  className = '',
  ...props
}) => {
  const divRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [opacity, setOpacity] = useState<number>(0);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!divRef.current) return;
    const rect = divRef.current.getBoundingClientRect();
    setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  const handleMouseEnter = () => setOpacity(1);
  const handleMouseLeave = () => setOpacity(0);

  return (
    <div
      ref={divRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`relative overflow-hidden rounded-2xl border border-border-subtle bg-bg-card p-6 transition-all duration-300 ${className}`}
      {...props}
    >
      {/* Radial Hover Spotlight */}
      <div
        className="pointer-events-none absolute -inset-px opacity-0 transition-opacity duration-300"
        style={{
          opacity,
          background: `radial-gradient(500px circle at ${position.x}px ${position.y}px, ${spotlightColor}, transparent 70%)`,
        }}
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
};
```

#### C. Magnet Pull Component
Bridges DOM events with spring displacement, gently pulling an interactive element toward the cursor within a defined proximity radius.

```tsx
import React, { useRef, useState } from 'react';

interface MagnetProps {
  children: React.ReactNode;
  padding?: number;
  disabled?: boolean;
  magnetStrength?: number;
}

export const Magnet: React.FC<MagnetProps> = ({
  children,
  padding = 40,
  disabled = false,
  magnetStrength = 2.5,
}) => {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const ref = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (disabled || !ref.current) return;
    const { left, top, width, height } = ref.current.getBoundingClientRect();
    const centerX = left + width / 2;
    const centerY = top + height / 2;
    const distX = Math.abs(centerX - e.clientX);
    const distY = Math.abs(centerY - e.clientY);

    if (distX < width / 2 + padding && distY < height / 2 + padding) {
      setPosition({
        x: (e.clientX - centerX) / magnetStrength,
        y: (e.clientY - centerY) / magnetStrength,
      });
    } else {
      setPosition({ x: 0, y: 0 });
    }
  };

  const handleMouseLeave = () => {
    setPosition({ x: 0, y: 0 });
  };

  return (
    <div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        transform: `translate3d(${position.x}px, ${position.y}px, 0)`,
        transition: 'transform 0.2s cubic-bezier(0.25, 1, 0.5, 1)',
      }}
      className="inline-block"
    >
      {children}
    </div>
  );
};
```

---

## 5. Architectural Synthesis Matrix

| Library | Primary Responsibility | Best Applied To | Computational Cost |
|---|---|---|---|
| **Magic UI** | CSS/SVG Border & Grid Primitives | Bento grids, feature cards, primary CTAs, HUD borders | Ultra-light (CSS GPU layers) |
| **COBE** | High-performance 3D Planetary Visualization | Global telemetry, connection routing, agent uplink maps | Low (~5kB gzipped, ~60 FPS) |
| **Paper Shaders** | Procedural WebGL2 Surface Canvas | Dynamic cockpit backdrops, liquid status states, organic mesh backgrounds | Low to Moderate (Shader fragment bound) |
| **React Bits** | Sensory Micro-interactions & Motion | Cyberpunk decrypted text, radial card spotlights, cursor magnetism | Negligible (RAF & pointer event throttling) |

---

## 6. Implementation Checklist for Production UIs

1. **Retina Display Protection**: Always verify canvas shaders apply `window.devicePixelRatio` capped at 2.0 to prevent memory blowups on 4K screens.
2. **Context Cleanup**: Always invoke `globe.destroy()` or clean up WebGL animation frames in `useEffect` cleanup returns to prevent WebGL context leaks.
3. **Motion Sensitivity**: Honor `prefers-reduced-motion` across border beams, shimmers, and continuous rotations.
4. **Theme Tokens**: Keep base shader and spotlight colors mapped to CSS variables (`--bg-card`, `--border-subtle`, `--color-active`).
