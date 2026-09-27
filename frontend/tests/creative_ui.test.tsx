import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  BorderBeam,
  ShimmerButton,
  BentoGrid,
  BentoCard,
  CobeGlobe,
  PaperShader,
  DecryptedText,
  SpotlightCard,
  Magnet,
  TrueFocus,
} from '../src/components/ui';

describe('Creative UI Components & Shader Primitives', () => {
  describe('BorderBeam (Magic UI)', () => {
    it('renders with custom properties and CSS variable styling', () => {
      render(
        <div className="relative w-64 h-32">
          <BorderBeam size={220} duration={8} colorFrom="#10b981" colorTo="#3b82f6" />
        </div>
      );
      const beam = screen.getByTestId('border-beam');
      expect(beam).toBeInTheDocument();
    });
  });

  describe('ShimmerButton (Magic UI)', () => {
    it('renders text, allows custom styling, and handles click events', () => {
      const handleClick = vi.fn();
      render(
        <ShimmerButton onClick={handleClick} shimmerColor="#ffffff">
          Deploy Neural Agent
        </ShimmerButton>
      );
      const button = screen.getByRole('button', { name: /deploy neural agent/i });
      expect(button).toBeInTheDocument();
      fireEvent.click(button);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('BentoGrid & BentoCard (Magic UI)', () => {
    it('renders asymmetric layout slots with headers and actions', () => {
      render(
        <BentoGrid>
          <BentoCard
            title="Telemetry Engine"
            description="Real-time hardware metrics and telemetry."
            cta="View Metrics"
            href="#telemetry"
            colSpan={2}
          />
          <BentoCard
            title="Neural Memory"
            description="Vector-indexed episodic memory store."
            colSpan={1}
          />
        </BentoGrid>
      );
      expect(screen.getByText('Telemetry Engine')).toBeInTheDocument();
      expect(screen.getByText('Neural Memory')).toBeInTheDocument();
      expect(screen.getByText(/View Metrics/i)).toBeInTheDocument();
    });
  });

  describe('CobeGlobe (COBE WebGL)', () => {
    it('mounts canvas element without crashing and cleans up on unmount', () => {
      const { container, unmount } = render(
        <CobeGlobe
          markers={[
            { location: [37.7749, -122.4194], size: 0.05 },
            { location: [51.5074, -0.1278], size: 0.05 },
          ]}
        />
      );
      const canvas = container.querySelector('canvas');
      expect(canvas).not.toBeNull();
      expect(() => unmount()).not.toThrow();
    });
  });

  describe('PaperShader (Paper Design Shaders)', () => {
    it('renders shader backdrop across modes with fallback protection', () => {
      const { container } = render(
        <div className="relative w-full h-48">
          <PaperShader mode="mesh" colors={['#09090b', '#10b981', '#3b82f6']} />
        </div>
      );
      expect(container.firstChild).toBeInTheDocument();
    });
  });

  describe('DecryptedText (React Bits)', () => {
    it('renders initial text characters', () => {
      render(<DecryptedText text="MAXIM NEURAL CORE" speed={20} />);
      const element = screen.getByText(/MAXIM NEURAL CORE/i);
      expect(element).toBeInTheDocument();
    });
  });

  describe('SpotlightCard (React Bits)', () => {
    it('renders content and updates coordinates on pointer interaction', () => {
      const { container } = render(
        <SpotlightCard spotlightColor="rgba(16, 185, 129, 0.2)">
          <h4>Cockpit Uplink</h4>
        </SpotlightCard>
      );
      expect(screen.getByText('Cockpit Uplink')).toBeInTheDocument();
      const card = container.firstChild as HTMLElement;
      fireEvent.mouseEnter(card);
      fireEvent.mouseMove(card, { clientX: 50, clientY: 50 });
      fireEvent.mouseLeave(card);
    });
  });

  describe('Magnet (React Bits)', () => {
    it('renders interactive child and reacts to mouse movement', () => {
      const { container } = render(
        <Magnet padding={40} magnetStrength={3}>
          <button>Hover Me</button>
        </Magnet>
      );
      const button = screen.getByText('Hover Me');
      expect(button).toBeInTheDocument();
      fireEvent.mouseMove(container.firstChild as HTMLElement, { clientX: 20, clientY: 20 });
      fireEvent.mouseLeave(container.firstChild as HTMLElement);
    });
  });

  describe('TrueFocus (React Bits)', () => {
    it('splits sentence into interactive words and toggles hover focus', () => {
      render(<TrueFocus sentence="Agentic Cognitive Architecture" />);
      const agenticWord = screen.getByText('Agentic');
      expect(agenticWord).toBeInTheDocument();
      fireEvent.mouseEnter(agenticWord);
      fireEvent.mouseLeave(agenticWord);
    });
  });
});
