import { useState, useEffect } from 'react';
import { Sparkles, Calendar, Target, ChevronRight } from 'lucide-react';
import { TopNav } from './components/TopNav';
import { DateTimeWidget } from './components/DateTimeWidget';
import { VisualUplink } from './components/VisualUplink';
import { SystemTelemetry } from './components/SystemTelemetry';
import { MascotStage } from './components/MascotStage';
import { IntelligenceDrawer } from './components/IntelligenceDrawer';
import { MemoryView } from './components/MemoryView';
import { GraphView } from './components/GraphView';
import { AgentsView } from './components/AgentsView';
import { SkillsView } from './components/SkillsView';
import { ConnectionsView } from './components/ConnectionsView';
import { SettingsView } from './components/SettingsView';
import { TabType, ThemeMode } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabType>('home');
  const [theme, setTheme] = useState<ThemeMode>(() => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const saved = window.localStorage.getItem('maxim_theme');
        return (saved === 'light' || saved === 'dark') ? saved : 'dark';
      }
    } catch {
      // fallback
    }
    return 'dark';
  });

  const [isBackendHealthy, setIsBackendHealthy] = useState(true);
  const [latencyMs, setLatencyMs] = useState(14);

  // Synchronize theme with HTML document attribute
  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', theme);
    }
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem('maxim_theme', theme);
      }
    } catch {
      // fallback
    }
  }, [theme]);

  // Check backend health
  useEffect(() => {
    const checkHealth = async () => {
      const startTime = performance.now();
      try {
        const res = await fetch('/api/health');
        if (res.ok) {
          const latency = Math.round(performance.now() - startTime);
          setLatencyMs(latency || 12);
          setIsBackendHealthy(true);
        } else {
          setIsBackendHealthy(false);
        }
      } catch {
        setIsBackendHealthy(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleTriggerMorningBriefing = () => {
    window.dispatchEvent(
      new CustomEvent('maxim:open-drawer-tab', { detail: { tab: 'chat' } })
    );
    window.dispatchEvent(
      new CustomEvent('maxim:send-prompt', {
        detail: { prompt: '🌅 Deliver my executive morning briefing for today.' },
      })
    );
  };

  const handleTriggerCheckTelos = () => {
    window.dispatchEvent(
      new CustomEvent('maxim:open-drawer-tab', { detail: { tab: 'chat' } })
    );
    window.dispatchEvent(
      new CustomEvent('maxim:send-prompt', {
        detail: { prompt: '🎯 Inspect my active TELOS profile in the Obsidian vault and summarize my top priorities and sprint goals.' },
      })
    );
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-bg-main text-text-primary overflow-hidden font-sans transition-colors duration-200">
      {/* TOP NAVIGATION BAR */}
      <TopNav
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        theme={theme}
        toggleTheme={toggleTheme}
        latencyMs={latencyMs}
        isBackendHealthy={isBackendHealthy}
      />

      {/* MAIN WORKSPACE BODY */}
      <main className="flex-1 flex overflow-hidden">
        {activeTab === 'home' && (
          <div className="flex-1 flex overflow-hidden">
            {/* LEFT COLUMN: DATE/TIME, PERCEPTION, TELEMETRY */}
            <aside className="w-80 flex-shrink-0 flex flex-col gap-3.5 p-3.5 border-r border-border-subtle overflow-y-auto bg-bg-card/40">
              {/* 1. Real-time Date and Time HUD (Topmost Left) */}
              <DateTimeWidget />

              {/* 2. Executive Daily Directives */}
              <div className="rounded-xl border border-border-subtle bg-bg-card p-3.5 transition-all shadow-xs flex flex-col gap-2.5">
                <div className="flex items-center gap-1.5 px-0.5 text-[11px] font-mono uppercase tracking-wider text-text-muted">
                  <Sparkles className="w-3.5 h-3.5 text-accent" />
                  <span className="font-semibold text-text-secondary">Daily Directives</span>
                </div>
                <div className="grid gap-1.5">
                  <button
                    type="button"
                    onClick={handleTriggerMorningBriefing}
                    className="w-full text-left p-2.5 rounded-lg border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover hover:border-accent/40 text-xs text-text-primary transition-all flex items-center justify-between group btn-press cursor-pointer"
                  >
                    <div className="flex items-center gap-2">
                      <Calendar className="w-3.5 h-3.5 text-accent" />
                      <span className="font-medium">Morning Briefing</span>
                    </div>
                    <ChevronRight className="w-3.5 h-3.5 text-text-muted group-hover:text-accent transition-transform group-hover:translate-x-0.5" />
                  </button>

                  <button
                    type="button"
                    onClick={handleTriggerCheckTelos}
                    className="w-full text-left p-2.5 rounded-lg border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover hover:border-accent/40 text-xs text-text-primary transition-all flex items-center justify-between group btn-press cursor-pointer"
                  >
                    <div className="flex items-center gap-2">
                      <Target className="w-3.5 h-3.5 text-amber" />
                      <span className="font-medium">Check TELOS Goals</span>
                    </div>
                    <ChevronRight className="w-3.5 h-3.5 text-text-muted group-hover:text-amber transition-transform group-hover:translate-x-0.5" />
                  </button>
                </div>
              </div>

              {/* 3. Visual Uplink (Standby, Click Modal for Camera/Screen) */}
              <VisualUplink />

              {/* 4. System Telemetry (RAM, CPU, Latency) */}
              <SystemTelemetry />
            </aside>


            {/* CENTER COLUMN: MASCOT COMPANION & OPERATIONAL STAGE */}
            <div className="flex-1 min-w-0 flex flex-col h-full overflow-hidden bg-bg-main relative">
              <MascotStage isCompact={false} />
            </div>

            {/* RIGHT COLUMN: WORKSPACE HUB (COMPACT TABS: CHAT, INTELLIGENCE, ACTIVITY) */}
            <IntelligenceDrawer />
          </div>
        )}

        {/* DEDICATED VIEW: MEMORY */}
        {activeTab === 'memory' && <MemoryView />}

        {/* DEDICATED VIEW: GRAPH */}
        {activeTab === 'graph' && <GraphView theme={theme} />}

        {/* DEDICATED VIEW: AGENTS */}
        {activeTab === 'agents' && <AgentsView />}

        {/* DEDICATED VIEW: SKILLS */}
        {activeTab === 'skills' && <SkillsView />}

        {/* DEDICATED VIEW: CONNECTIONS */}
        {activeTab === 'connections' && <ConnectionsView />}

        {/* DEDICATED VIEW: SETTINGS */}
        {activeTab === 'settings' && <SettingsView theme={theme} toggleTheme={toggleTheme} />}
      </main>
    </div>
  );
}
