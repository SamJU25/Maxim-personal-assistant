import React from 'react';

export interface BentoGridProps {
  className?: string;
  children: React.ReactNode;
}

export const BentoGrid: React.FC<BentoGridProps> = ({ className = '', children }) => {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-3 gap-4 auto-rows-[180px] ${className}`}>
      {children}
    </div>
  );
};

export interface BentoCardProps {
  className?: string;
  children?: React.ReactNode;
  header?: React.ReactNode;
  icon?: React.ReactNode;
  title?: React.ReactNode;
  description?: React.ReactNode;
  href?: string;
  cta?: string;
  colSpan?: 1 | 2 | 3;
  rowSpan?: 1 | 2 | 3;
}

export const BentoCard: React.FC<BentoCardProps> = ({
  className = '',
  children,
  header,
  icon,
  title,
  description,
  href,
  cta,
  colSpan = 1,
  rowSpan = 1,
}) => {
  const colSpanClasses = {
    1: 'md:col-span-1',
    2: 'md:col-span-2',
    3: 'md:col-span-3',
  };

  const rowSpanClasses = {
    1: 'row-span-1',
    2: 'row-span-2',
    3: 'row-span-3',
  };

  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border border-border-subtle bg-bg-card p-5 flex flex-col justify-between transition-all duration-300 hover:border-border-hover hover:shadow-lg ${colSpanClasses[colSpan]} ${rowSpanClasses[rowSpan]} ${className}`}
    >
      {/* Background Graphic Slot */}
      {header && <div className="absolute inset-0 z-0 overflow-hidden">{header}</div>}

      {/* Ambient Gradient on Hover */}
      <div className="pointer-events-none absolute inset-0 z-0 bg-gradient-to-t from-emerald-500/5 via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

      {/* Content Top */}
      <div className="relative z-10 flex items-center justify-between">
        {icon && <div className="p-2 rounded-xl bg-bg-card-subtle border border-border-subtle text-text-primary">{icon}</div>}
      </div>

      {children}

      {/* Content Bottom */}
      <div className="relative z-10 flex flex-col gap-1 mt-auto">
        {title && <h3 className="text-base font-semibold text-text-primary tracking-tight">{title}</h3>}
        {description && <p className="text-xs text-text-muted leading-relaxed line-clamp-2">{description}</p>}
        {cta && href && (
          <a
            href={href}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-400 hover:text-emerald-300 mt-2 transition-colors"
          >
            {cta} →
          </a>
        )}
      </div>
    </div>
  );
};
