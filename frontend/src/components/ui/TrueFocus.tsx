import React, { useState } from 'react';

export interface TrueFocusProps {
  sentence: string;
  className?: string;
  focusClassName?: string;
  blurClassName?: string;
}

export const TrueFocus: React.FC<TrueFocusProps> = ({
  sentence,
  className = '',
  focusClassName = 'text-white scale-105 filter-none',
  blurClassName = 'text-text-muted blur-[1px] opacity-60',
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const words = sentence.split(' ');

  return (
    <span className={`inline-flex flex-wrap gap-x-1.5 ${className}`}>
      {words.map((word, idx) => {
        const isHovered = hoveredIndex === idx;
        const hasHover = hoveredIndex !== null;

        return (
          <span
            key={idx}
            onMouseEnter={() => setHoveredIndex(idx)}
            onMouseLeave={() => setHoveredIndex(null)}
            className={`inline-block transition-all duration-200 cursor-default select-none ${
              isHovered
                ? focusClassName
                : hasHover
                ? blurClassName
                : 'text-text-primary'
            }`}
          >
            {word}
          </span>
        );
      })}
    </span>
  );
};
