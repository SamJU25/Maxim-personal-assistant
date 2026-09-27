import React from 'react';
import { motion, useReducedMotion } from 'motion/react';

export type JarvisCoreState =
  | 'idle'
  | 'listening'
  | 'thinking'
  | 'searching'
  | 'talking'
  | 'executing'
  | 'success'
  | 'error';

interface StateMotionConfig {
  speed: number;
  reverse: number;
  scale: number;
  glow: number;
}

const stateMotion: Record<JarvisCoreState, StateMotionConfig> = {
  idle: { speed: 48, reverse: 64, scale: 1, glow: 0.32 },
  listening: { speed: 18, reverse: 26, scale: 1.035, glow: 0.58 },
  thinking: { speed: 10, reverse: 14, scale: 1.02, glow: 0.5 },
  searching: { speed: 12, reverse: 16, scale: 1.02, glow: 0.52 },
  talking: { speed: 16, reverse: 22, scale: 1.045, glow: 0.56 },
  executing: { speed: 7, reverse: 18, scale: 1.025, glow: 0.62 },
  success: { speed: 30, reverse: 40, scale: 1.02, glow: 0.45 },
  error: { speed: 90, reverse: 100, scale: 0.985, glow: 0.38 },
};

const ticks = Array.from({ length: 48 }, (_, index) => index);
const waveform = Array.from({ length: 32 }, (_, index) => index);

export interface JarvisCoreProps {
  state?: JarvisCoreState;
  className?: string;
  accentColor?: string;
}

export const JarvisCore: React.FC<JarvisCoreProps> = ({
  state = 'idle',
  className = '',
  accentColor,
}) => {
  const reduceMotion = useReducedMotion();
  const config = stateMotion[state] || stateMotion.idle;

  const accent =
    accentColor ||
    (state === 'error'
      ? 'var(--color-agents, #f59e0b)'
      : state === 'success'
      ? 'var(--accent, #00d992)'
      : 'var(--accent, #00d992)');

  const rotate = reduceMotion ? 0 : 360;

  return (
    <div
      data-testid="jarvis-core"
      className={`core-wrap ${className}`}
      data-state={state}
      style={{ '--core-accent': accent } as React.CSSProperties}
    >
      {/* Ambient Atmosphere Glow */}
      <motion.div
        className="core-atmosphere"
        animate={{
          opacity: config.glow,
          scale: reduceMotion ? 1 : [0.96, config.scale, 0.96],
        }}
        transition={{
          duration: state === 'talking' ? 2.2 : 5.6,
          repeat: reduceMotion ? 0 : Infinity,
          ease: 'easeInOut',
        }}
      />

      {/* Outer Rotating HUD Geometry */}
      <motion.svg
        className="core-geometry core-outer"
        viewBox="0 0 500 500"
        animate={{ rotate }}
        transition={{
          duration: config.speed,
          repeat: reduceMotion ? 0 : Infinity,
          ease: 'linear',
        }}
        aria-hidden="true"
      >
        <circle cx="250" cy="250" r="220" className="ring ring-faint" />
        <circle cx="250" cy="250" r="205" className="ring ring-dashed" />
        <path d="M250 20a230 230 0 0 1 200 115" className="arc arc-bright" />
        <path d="M50 365a230 230 0 0 1 15-250" className="arc" />
        <circle cx="250" cy="30" r="3" className="orbit-node" />
        <circle cx="435" cy="365" r="2.5" className="orbit-node dim" />
      </motion.svg>

      {/* Mid Counter-Rotating Ring with 48 Radial Ticks */}
      <motion.svg
        className="core-geometry core-mid"
        viewBox="0 0 500 500"
        animate={{ rotate: -rotate }}
        transition={{
          duration: config.reverse,
          repeat: reduceMotion ? 0 : Infinity,
          ease: 'linear',
        }}
        aria-hidden="true"
      >
        <circle cx="250" cy="250" r="167" className="ring ring-faint" />
        <path d="M250 83a167 167 0 0 1 145 84" className="arc arc-bright" />
        <path d="M105 334a167 167 0 0 1 0-168" className="arc" />
        {ticks.map((tick) => (
          <line
            key={tick}
            x1="250"
            y1="92"
            x2="250"
            y2={tick % 4 === 0 ? '106' : '100'}
            className="tick"
            transform={`rotate(${tick * 7.5} 250 250)`}
          />
        ))}
      </motion.svg>

      {/* Inner Waveform Frequency Ring */}
      <motion.svg
        className="core-geometry core-wave"
        viewBox="0 0 500 500"
        animate={{
          rotate: state === 'thinking' || state === 'executing' ? rotate : 0,
          scale: config.scale,
        }}
        transition={{
          rotate: {
            duration: config.speed * 1.6,
            repeat: reduceMotion ? 0 : Infinity,
            ease: 'linear',
          },
          scale: { duration: 1.8 },
        }}
        aria-hidden="true"
      >
        <circle cx="250" cy="250" r="118" className="ring ring-faint" />
        {waveform.map((bar) => {
          const length = 7 + ((bar * 7) % 15);
          return (
            <line
              key={bar}
              x1="250"
              y1="120"
              x2="250"
              y2={120 + length}
              className="wave-bar"
              transform={`rotate(${bar * 11.25} 250 250)`}
            />
          );
        })}
      </motion.svg>

      {/* Central Radiant Aperture & Arc Light */}
      <div className="core-aperture" aria-hidden="true">
        <span className="aperture-ring" />
        <motion.span
          className="aperture-light"
          animate={{
            opacity: reduceMotion ? 0.74 : [0.52, 0.9, 0.52],
            scale: reduceMotion ? 1 : [0.96, 1.05, 0.96],
          }}
          transition={{
            duration: state === 'talking' ? 1.1 : 3.8,
            repeat: reduceMotion ? 0 : Infinity,
            ease: 'easeInOut',
          }}
        />
        <span className="aperture-center" />
      </div>

      {/* Hairline Crosshair Reticle Axes */}
      <div className="core-axis axis-horizontal" aria-hidden="true" />
      <div className="core-axis axis-vertical" aria-hidden="true" />
      <span className="sr-only">JARVIS holographic core state: {state}</span>
    </div>
  );
};
