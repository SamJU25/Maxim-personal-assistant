import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Brain,
  Activity,
  FileText,
  CheckCircle2,
  ExternalLink,
  Clock,
  Tag,
  ChevronRight,
  Folder,
  X,
} from 'lucide-react';
import { TelegramChat } from './TelegramChat';
import { ChatAttachment } from '../types';

export type DrawerTab = 'chat' | 'intelligence' | 'activity';
export type IntelligenceSubTab = 'notes' | 'vault';

export interface ActivityItem {
  id: string;
  title: string;
  category: 'tool' | 'memory' | 'voice' | 'routine';
  timestamp: string;
  status: 'completed' | 'in_progress' | 'failed';
  summary?: string;
}

export interface NotePreview {
  id: string;
  title: string;
  tags: string[];
  updatedAt: string;
  snippet: string;
}

export interface IntelligenceDrawerProps {
  onSelectNote?: (noteTitle: string) => void;
  onOpenVaultNote?: (path: string) => void;
  onTriggerPrompt?: (prompt: string) => void;
  onSendMessage?: (content: string, model: string, attachments: ChatAttachment[]) => void;
  defaultTab?: DrawerTab;
}

const DEFAULT_NOTES: NotePreview[] = [
  {
    id: 'note-1',
    title: 'Executive Daily Briefing',
    tags: ['#daily', '#priorities'],
    updatedAt: '08:15 AM',
    snippet: 'Key priorities for today: Review system architecture, test local speech pipelines, update TELOS milestones.',
  },
  {
    id: 'note-2',
    title: 'TELOS Master Objectives',
    tags: ['#telos', '#roadmap'],
    updatedAt: 'Yesterday',
    snippet: 'Primary objective: Zero-cloud personal AI assistant running seamlessly on local workstation hardware.',
  },
  {
    id: 'note-3',
    title: 'Obsidian Memory Structure',
    tags: ['#architecture', '#vault'],
    updatedAt: '2 days ago',
    snippet: '5-Layer memory topology: Ephemeral cache, working memory, episodic log, semantic index, and MOC links.',
  },
];

const DEFAULT_ACTIVITIES: ActivityItem[] = [
  {
    id: 'act-1',
    title: 'Obsidian Note Captured',
    category: 'memory',
    timestamp: '2m ago',
    status: 'completed',
    summary: 'Saved note [[Personal Goals 2026]] with tag #priorities',
  },
  {
    id: 'act-2',
    title: 'TELOS Target Audit',
    category: 'routine',
    timestamp: '15m ago',
    status: 'completed',
    summary: 'Scanned 12 active sprint milestones across vault',
  },
];

export const IntelligenceDrawer: React.FC<IntelligenceDrawerProps> = ({
  onSelectNote,
  onOpenVaultNote,
  onTriggerPrompt,
  onSendMessage,
  defaultTab = 'chat',
}) => {
  const [activeTab, setActiveTab] = useState<DrawerTab>(defaultTab);
  const [intelSubTab, setIntelSubTab] = useState<IntelligenceSubTab>('notes');

  const [activities, setActivities] = useState<ActivityItem[]>(DEFAULT_ACTIVITIES);
  const [notes, setNotes] = useState<NotePreview[]>(DEFAULT_NOTES);
  const [vaultFolders, setVaultFolders] = useState<{ name: string; count: number }[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [selectedNoteContent, setSelectedNoteContent] = useState<{ title: string; content: string; path?: string } | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Listen for navigation events to switch tabs programmatically
  useEffect(() => {
    const handleDrawerEvent = (e: Event) => {
      const detail = (e as CustomEvent<{ tab: DrawerTab; subTab?: IntelligenceSubTab }>).detail;
      if (detail?.tab) {
        setActiveTab(detail.tab);
        if (detail.subTab) {
          setIntelSubTab(detail.subTab);
        }
      }
    };
    window.addEventListener('maxim:open-drawer-tab', handleDrawerEvent);
    return () => window.removeEventListener('maxim:open-drawer-tab', handleDrawerEvent);
  }, []);

  useEffect(() => {
    let isMounted = true;
    const loadVault = async () => {
      setIsLoading(true);
      try {
        const folderParam = selectedFolder ? `?folder=${encodeURIComponent(selectedFolder)}` : '';
        const [notesRes, foldersRes, sessionRes] = await Promise.allSettled([
          fetch(`/api/vault/notes${folderParam}`),
          fetch('/api/vault/folders'),
          fetch('/api/session?session_id=default_session'),
        ]);

        if (!isMounted) return;

        if (notesRes.status === 'fulfilled' && notesRes.value.ok) {
          const notesData = await notesRes.value.json();
          if (Array.isArray(notesData)) setNotes(notesData);
        }

        if (foldersRes.status === 'fulfilled' && foldersRes.value.ok) {
          const foldersData = await foldersRes.value.json();
          if (Array.isArray(foldersData)) setVaultFolders(foldersData);
        }

        if (sessionRes.status === 'fulfilled' && sessionRes.value.ok) {
          const sessionData = await sessionRes.value.json();
          if (Array.isArray(sessionData.receipts) && sessionData.receipts.length > 0) {
            setActivities(
              sessionData.receipts.map((r: any) => ({
                id: r.id || String(Math.random()),
                title: r.tool_name ? `Tool: ${r.tool_name}` : 'System Action',
                category: 'tool',
                timestamp: r.created_at ? new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recent',
                status: 'completed',
                summary: r.output_result ? String(r.output_result).slice(0, 140) : undefined,
              }))
            );
          }
        }
      } catch (err) {
        console.error('Failed to load vault data:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    loadVault();
    return () => {
      isMounted = false;
    };
  }, [selectedFolder]);

  const handleOpenNote = async (title: string) => {
    onSelectNote?.(title);
    try {
      const res = await fetch(`/api/vault/note?title=${encodeURIComponent(title)}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedNoteContent({
          title: data.title || title,
          content: data.content || 'No content found.',
          path: data.path,
        });
      }
    } catch {
      // Fallback
    }
  };

  return (
    <aside
      className="w-96 lg:w-[420px] xl:w-[450px] flex-shrink-0 flex flex-col border-l border-border-subtle bg-bg-card/40 backdrop-blur-md select-none h-full overflow-hidden"
      aria-label="Assistant Workspace Drawer"
    >
      {/* 1. Header with Compact Tab Switcher */}
      <div className="p-2 border-b border-border-subtle bg-bg-card/60 shrink-0">

        {/* Tab Controls: Chat | Intelligence | Activity */}
        <div className="flex items-center p-0.5 rounded-xl border border-border-subtle bg-bg-card-subtle text-xs">
          <button
            type="button"
            onClick={() => setActiveTab('chat')}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer btn-press ${
              activeTab === 'chat'
                ? 'bg-accent text-accent-contrast shadow-xs'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Chat</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('intelligence')}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer btn-press ${
              activeTab === 'intelligence'
                ? 'bg-accent text-accent-contrast shadow-xs'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            <span>Intelligence</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('activity')}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer btn-press ${
              activeTab === 'activity'
                ? 'bg-accent text-accent-contrast shadow-xs'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Activity</span>
          </button>
        </div>
      </div>

      {/* 2. TAB 1: Chat Stream */}
      <div className={`flex-1 min-h-0 flex flex-col overflow-hidden ${activeTab === 'chat' ? 'flex' : 'hidden'}`}>
        <TelegramChat onSendMessage={onSendMessage} />
      </div>

      {/* 3. TAB 2: Intelligence (Captured Notes & Vault) */}
      <div className={`flex-1 min-h-0 overflow-y-auto p-3 flex flex-col gap-3 ${activeTab === 'intelligence' ? 'flex' : 'hidden'}`}>
        {/* Sub-tab Switcher: Notes vs Vault */}
        <div className="flex items-center p-0.5 rounded-lg border border-border-subtle bg-bg-card-subtle text-xs shrink-0">
          <button
            type="button"
            onClick={() => setIntelSubTab('notes')}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1 rounded text-[11px] font-medium transition-all cursor-pointer ${
              intelSubTab === 'notes'
                ? 'bg-accent text-accent-contrast shadow-xs font-semibold'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            <FileText className="w-3 h-3" />
            <span>Notes ({notes.length})</span>
          </button>
          <button
            type="button"
            onClick={() => setIntelSubTab('vault')}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1 rounded text-[11px] font-medium transition-all cursor-pointer ${
              intelSubTab === 'vault'
                ? 'bg-accent text-accent-contrast shadow-xs font-semibold'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            <Folder className="w-3 h-3" />
            <span>Vault Folders ({vaultFolders.length})</span>
          </button>
        </div>

        {/* Sub-view: Captured Notes */}
        {intelSubTab === 'notes' && (
          <div className="flex flex-col gap-2">
            {selectedFolder && (
              <div className="flex items-center justify-between text-[11px] font-mono px-2 py-1 rounded bg-bg-card-subtle border border-border-subtle">
                <span className="text-text-muted">
                  Folder: <strong className="text-text-primary">{selectedFolder}</strong>
                </span>
                <button
                  type="button"
                  onClick={() => setSelectedFolder(null)}
                  className="text-accent hover:underline cursor-pointer"
                >
                  Show All
                </button>
              </div>
            )}

            {isLoading && notes.length === 0 && (
              <div className="text-center py-6 text-xs text-text-muted font-mono animate-pulse">
                Scanning Obsidian vault notes...
              </div>
            )}

            {!isLoading && notes.length === 0 && (
              <div className="text-center py-6 text-xs text-text-muted font-mono">
                No notes found in {selectedFolder || 'vault'}.
              </div>
            )}

            {notes.map((note) => (
              <div
                key={note.id}
                onClick={() => handleOpenNote(note.title)}
                className="glass-panel rounded-xl p-3 border border-border-subtle hover:border-accent/40 flex flex-col gap-2 cursor-pointer transition-all btn-press group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-text-primary group-hover:text-accent transition-colors line-clamp-1">
                    {note.title}
                  </span>
                  <div className="flex items-center gap-1 text-[10px] font-mono text-text-muted shrink-0 ml-1">
                    <Clock className="w-3 h-3" />
                    <span>{note.updatedAt}</span>
                  </div>
                </div>

                <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed font-mono">
                  {note.snippet}
                </p>

                {note.tags && note.tags.length > 0 && (
                  <div className="flex items-center gap-1.5 pt-1 border-t border-border-subtle/50">
                    {note.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-[10px] font-mono text-accent bg-accent/10 px-1.5 py-0.5 rounded-sm flex items-center gap-0.5"
                      >
                        <Tag className="w-2.5 h-2.5" />
                        <span>{tag}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Sub-view: Vault Folders */}
        {intelSubTab === 'vault' && (
          <div className="flex flex-col gap-2">
            <div className="px-1 text-[11px] font-mono uppercase tracking-wider text-text-muted flex items-center justify-between">
              <span>Obsidian Knowledge Folders</span>
              <ExternalLink className="w-3 h-3 text-text-muted" />
            </div>

            <div className="flex flex-col gap-1.5">
              {vaultFolders.map((folder) => (
                <div
                  key={folder.name}
                  onClick={() => {
                    onOpenVaultNote?.(folder.name);
                    setSelectedFolder(folder.name);
                    setIntelSubTab('notes');
                  }}
                  className="p-2.5 rounded-xl border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover hover:border-accent/40 flex items-center justify-between text-xs text-text-primary transition-all cursor-pointer btn-press group"
                >
                  <div className="flex items-center gap-2">
                    <Folder className="w-3.5 h-3.5 text-accent" />
                    <span className="font-medium">{folder.name}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-mono text-text-muted">
                      {folder.count} files
                    </span>
                    <ChevronRight className="w-3 h-3 text-text-muted group-hover:text-accent transition-transform group-hover:translate-x-0.5" />
                  </div>
                </div>
              ))}
            </div>

            {onTriggerPrompt && (
              <button
                type="button"
                onClick={() => onTriggerPrompt('📖 Search and inspect recent Obsidian vault markdown files for active notes.')}
                className="mt-2 w-full p-2.5 rounded-xl border border-dashed border-accent/40 bg-accent/5 hover:bg-accent/10 text-xs font-medium text-accent transition-all flex items-center justify-center gap-1.5 cursor-pointer btn-press"
              >
                <span>Full Vault Deep-Search</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* 4. TAB 3: Activity Stream */}
      <div className={`flex-1 min-h-0 overflow-y-auto p-3 flex flex-col gap-2.5 ${activeTab === 'activity' ? 'flex' : 'hidden'}`}>
        <div className="px-1 text-[11px] font-mono uppercase tracking-wider text-text-muted flex items-center justify-between">
          <span>Recent System Executions</span>
          <span className="text-[10px] font-mono text-accent">Active</span>
        </div>

        {activities.length === 0 ? (
          <div className="text-center py-8 text-xs text-text-muted font-mono">
            No system receipts recorded yet. Execute tools or send directives to generate receipts.
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {activities.map((act) => (
              <div
                key={act.id}
                className="glass-panel rounded-xl p-2.5 border border-border-subtle flex flex-col gap-1.5 hover:border-accent/40 transition-colors"
              >
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-accent" />
                    <span className="font-semibold text-text-primary">{act.title}</span>
                  </div>
                  <span className="text-[10px] font-mono text-text-muted">{act.timestamp}</span>
                </div>
                {act.summary && (
                  <p className="text-xs text-text-secondary leading-relaxed pl-5.5 font-mono">
                    {act.summary}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Obsidian Note Reader Modal */}
      {selectedNoteContent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="w-full max-w-xl max-h-[80vh] flex flex-col rounded-xl border border-border-subtle bg-bg-card shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between p-3.5 border-b border-border-subtle bg-bg-card-subtle">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-accent" />
                <span className="font-semibold text-xs text-text-primary">{selectedNoteContent.title}</span>
                {selectedNoteContent.path && (
                  <span className="text-[10px] font-mono text-text-muted">({selectedNoteContent.path})</span>
                )}
              </div>
              <button
                type="button"
                onClick={() => setSelectedNoteContent(null)}
                className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-bg-card-hover cursor-pointer"
                title="Close Note"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto text-xs text-text-secondary whitespace-pre-wrap font-mono leading-relaxed max-h-[60vh] select-text">
              {selectedNoteContent.content}
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};
