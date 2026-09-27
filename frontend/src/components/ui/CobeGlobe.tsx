import React, { useEffect, useRef } from 'react';
import createGlobe, { Globe } from 'cobe';

export interface GlobeMarker {
  location: [number, number]; // [lat, lon]
  size: number;
}

export interface CobeGlobeProps {
  className?: string;
  markers?: GlobeMarker[];
  baseColor?: [number, number, number];
  markerColor?: [number, number, number];
  glowColor?: [number, number, number];
  diffuse?: number;
  mapSamples?: number;
  mapBrightness?: number;
  dark?: number;
  autoRotateSpeed?: number;
}

export const CobeGlobe: React.FC<CobeGlobeProps> = ({
  className = '',
  markers = [
    { location: [37.7749, -122.4194], size: 0.05 }, // San Francisco
    { location: [51.5074, -0.1278], size: 0.05 },  // London
    { location: [35.6762, 139.6503], size: 0.06 }, // Tokyo
    { location: [1.3521, 103.8198], size: 0.04 },  // Singapore
    { location: [-33.8688, 151.2093], size: 0.04 },// Sydney
  ],
  baseColor = [0.1, 0.1, 0.14],
  markerColor = [0.06, 0.72, 0.51], // Emerald
  glowColor = [0.15, 0.22, 0.3],
  diffuse = 1.2,
  mapSamples = 16000,
  mapBrightness = 6,
  dark = 1,
  autoRotateSpeed = 0.003,
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

    const dpr = typeof window !== 'undefined' ? Math.min(window.devicePixelRatio || 1, 2) : 1;
    let globe: Globe | null = null;
    let rafId: number | null = null;

    try {
      globe = createGlobe(canvas, {
        devicePixelRatio: dpr,
        width: (width || 300) * 2,
        height: (width || 300) * 2,
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
      });

      const renderLoop = () => {
        if (!pointerInteracting.current) {
          phiRef.current += autoRotateSpeed;
        }
        if (globe) {
          globe.update({
            phi: phiRef.current + pointerInteractionMovement.current,
            width: (width || 300) * 2,
            height: (width || 300) * 2,
          });
        }
        rafId = requestAnimationFrame(renderLoop);
      };

      rafId = requestAnimationFrame(renderLoop);
    } catch {
      // In non-WebGL or test environments, gracefully degrade
    }

    return () => {
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
      }
      if (globe) {
        globe.destroy();
      }
      window.removeEventListener('resize', onResize);
    };
  }, [baseColor, dark, diffuse, glowColor, mapBrightness, mapSamples, markerColor, markers, autoRotateSpeed]);

  return (
    <div className={`relative aspect-square w-full max-w-[450px] mx-auto flex items-center justify-center select-none ${className}`}>
      <canvas
        ref={canvasRef}
        className="w-full h-full cursor-grab active:cursor-grabbing transition-opacity duration-500"
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
