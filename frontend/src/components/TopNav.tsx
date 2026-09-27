import React from 'react';
import {
  LayoutDashboard,
  Database,
  Network,
  Users,
  Zap,
  Radio,
  Settings,
  Sun,
  Moon,
  Activity,
} from 'lucide-react';
import { TabType, ThemeMode } from '../types';

interface TopNavProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  theme: ThemeMode;
  toggleTheme: () => void;
  latencyMs?: number;
  isBackendHealthy?: boolean;
}

export const TopNav: React.FC<TopNavProps> = ({
  activeTab,
  setActiveTab,
  theme,
  toggleTheme,
  latencyMs = 12,
  isBackendHealthy = true,
}) => {
  const navItems: { id: TabType; label: string; icon: React.ReactNode }[] = [
    { id: 'home', label: 'Home', icon: <LayoutDashboard className="w-3.5 h-3.5" /> },
    { id: 'memory', label: 'Memory', icon: <Database className="w-3.5 h-3.5" /> },
    { id: 'graph', label: 'Graph', icon: <Network className="w-3.5 h-3.5" /> },
    { id: 'agents', label: 'Agents', icon: <Users className="w-3.5 h-3.5" /> },
    { id: 'skills', label: 'Skills', icon: <Zap className="w-3.5 h-3.5" /> },
    { id: 'connections', label: 'Connections', icon: <Radio className="w-3.5 h-3.5" /> },
    { id: 'settings', label: 'Settings', icon: <Settings className="w-3.5 h-3.5" /> },
  ];

  return (
    <header className="h-14 border-b border-border-subtle bg-bg-card/95 backdrop-blur-md px-5 flex items-center justify-between select-none z-30 transition-colors duration-150">
      {/* Brand & System Status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2.5">
          <div className="relative w-7 h-7 rounded-md border border-border-subtle bg-bg-card-subtle flex items-center justify-center font-bold text-xs tracking-wider text-text-primary shadow-xs transition-transform active:scale-95 group">
            <span className="font-mono text-xs font-semibold">M</span>
            <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-accent ring-2 ring-bg-card" />
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm tracking-tight text-text-primary font-sans">MaxIM</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-medium border border-border-subtle text-text-secondary bg-bg-card-subtle">
              v2.0 Native
            </span>
          </div>
        </div>

        <div className="h-3.5 w-px bg-border-subtle mx-0.5" />

        {/* Backend Heartbeat */}
        <div className="flex items-center gap-1.5 text-xs text-text-muted px-2 py-0.5 rounded-full bg-bg-card-subtle border border-border-subtle">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isBackendHealthy ? 'bg-accent shadow-sm shadow-accent/50 animate-pulse' : 'bg-rose-500'
            }`}
          />
          <span className="font-mono text-[10px] uppercase tracking-wider font-semibold text-text-secondary">
            {isBackendHealthy ? 'ONLINE' : 'OFFLINE'}
          </span>
        </div>
      </div>

      {/* Center Segmented Navigation Capsule */}
      <nav className="flex items-center gap-1 bg-bg-card-subtle p-1 rounded-full border border-border-subtle shadow-xs">
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all duration-150 cursor-pointer ${
                isActive
                  ? 'bg-accent text-accent-contrast shadow-sm font-semibold'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-card-hover'
              }`}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Right Controls: Latency Telemetry & Black/White Mode Switch */}
      <div className="flex items-center gap-2.5">
        <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-mono text-text-muted px-2.5 py-1 rounded-md bg-bg-card-subtle border border-border-subtle">
          <Activity className="w-3 h-3 text-accent" />
          <span className="text-text-primary font-medium">{latencyMs}ms</span>
        </div>

        {/* Minimalist Black & White Mode Switcher */}
        <div className="flex items-center p-0.5 rounded-md border border-border-subtle bg-bg-card-subtle">
          <button
            onClick={() => {
              if (theme !== 'light') toggleTheme();
            }}
            aria-label="Switch to Light mode"
            title="Light Mode"
            className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium transition-all cursor-pointer ${
              theme === 'light'
                ? 'bg-accent text-accent-contrast shadow-xs font-semibold'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            <Sun className="w-3 h-3" />
            <span>LIGHT</span>
          </button>

          <button
            onClick={() => {
              if (theme !== 'dark') toggleTheme();
            }}
            aria-label="Switch to Dark mode"
            title="Dark Mode"
            className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium transition-all cursor-pointer ${
              theme === 'dark'
                ? 'bg-accent text-accent-contrast shadow-xs font-semibold'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            <Moon className="w-3 h-3" />
            <span>DARK</span>
          </button>
        </div>
      </div>
    </header>
  );
};
