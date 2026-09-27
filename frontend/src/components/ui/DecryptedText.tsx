import React, { useEffect, useState, useRef } from 'react';

export interface DecryptedTextProps {
  text: string;
  speed?: number;
  maxIterations?: number;
  characters?: string;
  className?: string;
  parentClassName?: string;
  animateOnHover?: boolean;
}

export const DecryptedText: React.FC<DecryptedTextProps> = ({
  text,
  speed = 40,
  maxIterations = 10,
  characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+',
  className = '',
  parentClassName = '',
  animateOnHover = false,
}) => {
  const [displayText, setDisplayText] = useState<string>(text);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startAnimation = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    let iteration = 0;
    const totalSteps = text.length;

    intervalRef.current = setInterval(() => {
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

      if (iteration >= totalSteps) {
        if (intervalRef.current) clearInterval(intervalRef.current);
      }
      iteration += 1 / (maxIterations / totalSteps || 1);
    }, speed);
  };

  useEffect(() => {
    if (!animateOnHover) {
      startAnimation();
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [text, speed, maxIterations, characters, animateOnHover]);

  const handleMouseEnter = () => {
    if (animateOnHover) {
      startAnimation();
    }
  };

  return (
    <span
      className={`inline-block font-mono cursor-default ${parentClassName}`}
      onMouseEnter={handleMouseEnter}
    >
      <span className={className}>{displayText}</span>
    </span>
  );
};
