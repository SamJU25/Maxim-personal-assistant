import React, { Component, ErrorInfo, ReactNode, useState, useEffect } from 'react';
import {
  MeshGradient,
  LiquidMetal,
  Waves,
  Dithering,
  DotOrbit,
  GrainGradient,
} from '@paper-design/shaders-react';

export type PaperShaderMode =
  | 'mesh'
  | 'liquid'
  | 'waves'
  | 'dither'
  | 'dotOrbit'
  | 'grain';

export interface PaperShaderProps {
  mode?: PaperShaderMode;
  className?: string;
  colors?: string[];
  distortion?: number;
  swirl?: number;
  speed?: number;
  opacity?: number;
}

function hasFullWebGLSupport(): boolean {
  if (typeof window === 'undefined' || typeof document === 'undefined') return false;
  try {
    const canvas = document.createElement('canvas');
    const gl = (canvas.getContext('webgl2') || canvas.getContext('webgl')) as WebGLRenderingContext | null;
    return !!(gl && typeof gl.getShaderPrecisionFormat === 'function');
  } catch {
    return false;
  }
}

// Error boundary to prevent WebGL context initialization failures from breaking the app
class ShaderErrorBoundary extends Component<{ children: ReactNode; fallback?: ReactNode }, { hasError: boolean }> {
  constructor(props: { children: ReactNode; fallback?: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.warn('PaperShader WebGL notice:', error.message, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || null;
    }
    return this.props.children;
  }
}

export const PaperShader: React.FC<PaperShaderProps> = ({
  mode = 'mesh',
  className = '',
  colors = ['#09090b', '#10b981', '#18181b', '#3b82f6'],
  distortion = 0.8,
  swirl = 0.6,
  speed = 0.15,
  opacity = 0.45,
}) => {
  const [webglSupported, setWebglSupported] = useState<boolean>(false);

  useEffect(() => {
    setWebglSupported(hasFullWebGLSupport());
  }, []);

  const fallback = (
    <div
      data-testid="paper-shader-fallback"
      className="w-full h-full bg-gradient-to-tr from-emerald-950/20 via-transparent to-blue-950/20 animate-pulse"
      style={{ animationDuration: '6s' }}
    />
  );

  return (
    <div
      data-testid="paper-shader-container"
      className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}
      style={{ opacity }}
    >
      <ShaderErrorBoundary fallback={fallback}>
        {!webglSupported ? (
          fallback
        ) : (
          <>
            {mode === 'mesh' && (
              <MeshGradient
                colors={colors}
                distortion={distortion}
                swirl={swirl}
                speed={speed}
                style={{ width: '100%', height: '100%' }}
              />
            )}
            {mode === 'liquid' && (
              <LiquidMetal
                colorBack={colors[0] || '#09090b'}
                colorTint={colors[1] || '#10b981'}
                distortion={distortion}
                speed={speed * 1.5}
                style={{ width: '100%', height: '100%' }}
              />
            )}
            {mode === 'waves' && (
              <Waves
                colorBack={colors[0] || '#09090b'}
                colorFront={colors[3] || '#3b82f6'}
                amplitude={0.5}
                frequency={1.2}
                style={{ width: '100%', height: '100%' }}
              />
            )}
            {mode === 'dither' && (
              <Dithering
                colorBack={colors[0] || '#09090b'}
                colorFront={colors[1] || '#10b981'}
                size={4}
                speed={speed}
                style={{ width: '100%', height: '100%' }}
              />
            )}
            {mode === 'dotOrbit' && (
              <DotOrbit
                colors={colors}
                speed={speed}
                style={{ width: '100%', height: '100%' }}
              />
            )}
            {mode === 'grain' && (
              <GrainGradient
                colors={colors}
                noise={0.3}
                speed={speed}
                style={{ width: '100%', height: '100%' }}
              />
            )}
          </>
        )}
      </ShaderErrorBoundary>
    </div>
  );
};
