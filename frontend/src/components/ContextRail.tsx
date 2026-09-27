import React from 'react';
import {
  Sparkles,
  Calendar,
  FileText,
  Target,
  Search,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';
import { DateTimeWidget } from './DateTimeWidget';

export interface ContextRailProps {
  onTriggerRoutine?: (prompt: string) => void;
  onOpenUplinkModal?: () => void;
  vaultStatus?: string;
  voiceStatus?: string;
}

export const ContextRail: React.FC<ContextRailProps> = ({
  onTriggerRoutine,
  vaultStatus = 'Synced',
  voiceStatus = 'Ready',
}) => {
  const handleRoutine = (prompt: string) => {
    if (onTriggerRoutine) {
      onTriggerRoutine(prompt);
    }
  };

  return (
    <aside
      className="w-72 flex-shrink-0 flex flex-col gap-4 p-4 border-r border-border-subtle overflow-y-auto bg-bg-card/40 backdrop-blur-md select-none"
      aria-label="Executive Context Rail"
    >
      {/* 1. Executive Real-time Clock (Contains 'System Clock') */}
      <div className="glass-panel rounded-2xl p-3.5 shadow-sm border border-border-subtle">
        <DateTimeWidget />
      </div>

      {/* 2. Personal Assistant Daily Routines */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-1.5 px-1 text-[11px] font-mono uppercase tracking-wider text-text-muted">
          <Sparkles className="w-3 h-3 text-accent" />
          <span>Daily Directives</span>
        </div>

        <div className="grid gap-1.5">
          {/* Routine 1: Morning Briefing */}
          <button
            type="button"
            onClick={() => handleRoutine('🌅 Provide my Executive Morning Briefing: review calendar, active priorities, and loose ends.')}
            className="w-full text-left p-2.5 rounded-xl border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover hover:border-accent/40 text-xs text-text-primary transition-all flex items-center justify-between group btn-press cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <Calendar className="w-3.5 h-3.5 text-accent" />
              <span className="font-medium">Morning Briefing</span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-text-muted group-hover:text-accent transition-transform group-hover:translate-x-0.5" />
          </button>

          {/* Routine 2: Quick Note Capture */}
          <button
            type="button"
            onClick={() => handleRoutine('📝 Capture a note into my Obsidian Knowledge Vault with timestamp and tags.')}
            className="w-full text-left p-2.5 rounded-xl border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover hover:border-accent/40 text-xs text-text-primary transition-all flex items-center justify-between group btn-press cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 text-text-secondary" />
              <span className="font-medium">Capture Vault Note</span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-text-muted group-hover:text-accent transition-transform group-hover:translate-x-0.5" />
          </button>

          {/* Routine 3: Today's TELOS Priorities */}
          <button
            type="button"
            onClick={() => handleRoutine('🎯 Check and report my TELOS Targets and highest leverage objectives for today.')}
            className="w-full text-left p-2.5 rounded-xl border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover hover:border-accent/40 text-xs text-text-primary transition-all flex items-center justify-between group btn-press cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <Target className="w-3.5 h-3.5 text-amber" />
              <span className="font-medium">Check TELOS Goals</span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-text-muted group-hover:text-amber transition-transform group-hover:translate-x-0.5" />
          </button>

          {/* Routine 4: Search Memory Vault */}
          <button
            type="button"
            onClick={() => handleRoutine('🔍 Search my memory vault for recent decisions, notes, and loose ends.')}
            className="w-full text-left p-2.5 rounded-xl border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover hover:border-accent/40 text-xs text-text-primary transition-all flex items-center justify-between group btn-press cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <Search className="w-3.5 h-3.5 text-text-secondary" />
              <span className="font-medium">Query Vault Memory</span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-text-muted group-hover:text-accent transition-transform group-hover:translate-x-0.5" />
          </button>
        </div>
      </div>

      {/* 3. Hardware & Vault Readiness Vitals */}
      <div className="mt-auto flex flex-col gap-2 pt-2 border-t border-border-subtle">
        <div className="flex items-center justify-between px-1 text-[11px] font-mono uppercase tracking-wider text-text-muted">
          <span>Local Hardware Vitals</span>
          <ShieldCheck className="w-3 h-3 text-accent" />
        </div>

        <div className="glass-pill rounded-xl p-2.5 flex flex-col gap-2 text-xs border border-border-subtle">
          {/* Inference Model */}
          <div className="flex items-center justify-between">
            <span className="text-text-muted text-[11px]">Neural Core</span>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
              <span className="font-mono text-[11px] text-text-primary font-medium">Llama 3.2</span>
            </div>
          </div>

          {/* Voice Engine */}
          <div className="flex items-center justify-between">
            <span className="text-text-muted text-[11px]">Speech Voice</span>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-accent" />
              <span className="font-mono text-[11px] text-text-primary">{voiceStatus} (Kokoro)</span>
            </div>
          </div>

          {/* Obsidian Vault */}
          <div className="flex items-center justify-between">
            <span className="text-text-muted text-[11px]">Knowledge Vault</span>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-accent" />
              <span className="font-mono text-[11px] text-text-primary">{vaultStatus}</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
