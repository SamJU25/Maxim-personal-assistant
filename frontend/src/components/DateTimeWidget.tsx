import React, { useState, useEffect } from 'react';
import { Clock, Calendar, Globe2, Sun, Moon } from 'lucide-react';

export const DateTimeWidget: React.FC = () => {
  const [time, setTime] = useState<Date>(new Date());
  const [is24Hour, setIs24Hour] = useState<boolean>(() => {
    try {
      return localStorage.getItem('maxim_clock_24h') !== 'false';
    } catch {
      return true;
    }
  });

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const toggleFormat = () => {
    setIs24Hour((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('maxim_clock_24h', String(next));
      } catch {
        // ignore
      }
      return next;
    });
  };

  // Time formatting
  const hoursNum = time.getHours();
  const minutes = String(time.getMinutes()).padStart(2, '0');
  const seconds = String(time.getSeconds()).padStart(2, '0');
  const period = hoursNum >= 12 ? 'PM' : 'AM';

  const displayHours = is24Hour
    ? String(hoursNum).padStart(2, '0')
    : String(hoursNum % 12 || 12).padStart(2, '0');

  // Day & Calendar formatting
  const weekday = time.toLocaleDateString([], { weekday: 'long' });
  const dateFormatted = time.toLocaleDateString([], {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  // Timezone resolution
  const timeZoneName = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const timeZoneOffset = -time.getTimezoneOffset() / 60;
  const offsetString = `UTC${timeZoneOffset >= 0 ? `+${timeZoneOffset}` : timeZoneOffset}:00`;

  // Solar phase icon
  const isDaytime = hoursNum >= 6 && hoursNum < 18;

  return (
    <div
      onClick={toggleFormat}
      title="Click to toggle 12h / 24h clock format"
      className="rounded-xl border border-border-subtle bg-bg-card p-4 transition-all duration-150 shadow-xs hover:border-border-hover cursor-pointer group select-none relative overflow-hidden"
    >
      {/* Top Meta Bar */}
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-1.5 text-xs text-text-muted">
          <Clock className="w-3.5 h-3.5 text-text-secondary group-hover:text-text-primary transition-colors" />
          <span className="font-mono text-[11px] uppercase tracking-wider font-semibold text-text-secondary">
            System Clock
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Format Badge */}
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border border-border-subtle text-text-muted bg-bg-card-subtle group-hover:text-text-secondary transition-colors">
            {is24Hour ? '24H' : '12H'}
          </span>

          {/* Live Heartbeat */}
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-bg-card-subtle border border-border-subtle text-[10px] font-mono text-text-secondary">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>LIVE</span>
          </div>
        </div>
      </div>

      {/* Main Digital Clock Display with Seconds & Solar Glyph */}
      <div className="flex items-baseline justify-between my-1">
        <div className="flex items-baseline gap-1 font-mono tracking-tight text-text-primary font-bold">
          <span className="text-3xl font-semibold tracking-tighter">{displayHours}:{minutes}</span>
          <span className="text-base font-normal text-text-muted">:{seconds}</span>
          {!is24Hour && (
            <span className="text-xs font-semibold ml-1 text-text-secondary tracking-normal font-sans">
              {period}
            </span>
          )}
        </div>

        <div className="flex items-center text-text-muted" title={isDaytime ? 'Daytime phase' : 'Night phase'}>
          {isDaytime ? (
            <Sun className="w-4 h-4 text-amber-500/80" />
          ) : (
            <Moon className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </div>


      {/* Calendar & Timezone Footer */}
      <div className="flex items-center justify-between text-xs text-text-secondary pt-2 border-t border-border-subtle mt-1 font-sans">
        <div className="flex items-center gap-1.5">
          <Calendar className="w-3.5 h-3.5 text-text-muted" />
          <span className="font-medium text-text-primary">{weekday},</span>
          <span className="text-text-muted">{dateFormatted}</span>
        </div>

        <div
          className="flex items-center gap-1 text-[11px] font-mono text-text-muted"
          title={`${timeZoneName} (${offsetString})`}
        >
          <Globe2 className="w-3 h-3 text-text-muted" />
          <span>{offsetString}</span>
        </div>
      </div>
    </div>
  );
};
